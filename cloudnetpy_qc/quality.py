"""Cloudnet product quality checks."""

import datetime
import json
import logging
import os
import re
from collections.abc import Iterable
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import NamedTuple, TypedDict

import netCDF4
import numpy as np
import scipy.stats
from cftime import num2pydate
from numpy import ma
from requests import RequestException

from cloudnetpy_qc.coverage import data_coverage, get_duration

from . import utils
from .variables import LEVELS, VARIABLES, Product
from .version import __version__

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

METADATA_CONFIG = utils.read_config(os.path.join(DATA_PATH, "metadata_config.ini"))
DATA_CONFIG = utils.read_config(os.path.join(DATA_PATH, "data_quality_config.ini"))
CF_AREA_TYPES_XML = os.path.join(DATA_PATH, "area-type-table.xml")
CF_STANDARD_NAMES_XML = os.path.join(DATA_PATH, "cf-standard-name-table.xml")
CF_REGION_NAMES_XML = os.path.join(DATA_PATH, "standardized-region-list.xml")

H_TO_S = 60 * 60
M_TO_MM = 1000


class ErrorLevel(Enum):
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class TestException(NamedTuple):
    result: ErrorLevel
    message: str


class TestReport(NamedTuple):
    test_id: str
    exceptions: list[TestException]


class FileReport(NamedTuple):
    timestamp: datetime.datetime
    qc_version: str
    tests: list[TestReport]
    data_coverage: float | None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "qcVersion": self.qc_version,
            "tests": [
                {
                    "testId": test.test_id,
                    "exceptions": [
                        {"result": exception.result.value, "message": exception.message}
                        for exception in test.exceptions
                    ],
                }
                for test in self.tests
            ],
        }


class SiteMeta(TypedDict):
    time: np.ndarray | None
    latitude: float | np.ndarray | None
    longitude: float | np.ndarray | None
    altitude: float | None


def run_tests(
    filename: str | PathLike,
    site_meta: SiteMeta,
    product: Product | str | None = None,
    ignore_tests: list[str] | None = None,
) -> FileReport:
    filename = Path(filename)
    coverage = None
    if isinstance(product, str):
        product = Product(product)
    with netCDF4.Dataset(filename) as nc:
        if product is None:
            try:
                product = Product(nc.cloudnet_file_type)
            except AttributeError as exc:
                raise ValueError(
                    "No 'cloudnet_file_type' global attribute found, "
                    "can not run tests. Is this a legacy file?"
                ) from exc
        logging.debug(f"Filename: {filename.stem}")
        logging.debug(f"File type: {product}")
        test_reports: list[TestReport] = []
        for cls in Test.__subclasses__():
            if ignore_tests and cls.__name__ in ignore_tests:
                continue
            test_instance = cls(nc, filename, product, site_meta)
            if product not in test_instance.products:
                continue
            try:
                test_instance.run()
            except Exception as err:
                test_instance._add_error(
                    f"Failed to run test: {err} ({type(err).__name__})"
                )
                logging.exception(f"Failed to run {cls.__name__}:")
            test_reports.append(test_instance.report)
            if test_instance.coverage is not None:
                coverage = test_instance.coverage
    return FileReport(
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        qc_version=__version__,
        tests=test_reports,
        data_coverage=coverage,
    )


class Test:
    """Test base class."""

    name: str
    description: str
    products: Iterable[Product] = Product.all()
    coverage: float | None = None

    def __init__(
        self, nc: netCDF4.Dataset, filename: Path, product: Product, site_meta: SiteMeta
    ):
        self.filename = filename
        self.nc = nc
        self.product = product
        self.site_meta = site_meta
        self.report = TestReport(
            test_id=self.__class__.__name__,
            exceptions=[],
        )

    def run(self):
        raise NotImplementedError

    def _add_message(self, message: str | list, severity: ErrorLevel):
        self.report.exceptions.append(
            TestException(result=severity, message=utils.format_msg(message))
        )

    def _add_info(self, message: str | list):
        self._add_message(message, ErrorLevel.INFO)

    def _add_warning(self, message: str | list):
        self._add_message(message, ErrorLevel.WARNING)

    def _add_error(self, message: str | list):
        self._add_message(message, ErrorLevel.ERROR)

    def _read_config_keys(self, config_section: str) -> np.ndarray:
        field = "all" if "attr" in config_section else self.product.value
        keys = METADATA_CONFIG[config_section][field].split(",")
        return np.char.strip(keys)

    def _get_required_variables(self) -> dict:
        return {
            name: var
            for name, var in VARIABLES.items()
            if var.required is not None and self.product in var.required
        }

    def _get_required_variable_names(self) -> set:
        required_variables = self._get_required_variables()
        return set(required_variables.keys())

    def _test_variable_attribute(self, attribute: str):
        for key, variable in self.nc.variables.items():
            if hasattr(variable, attribute):
                value = getattr(variable, attribute)
                if isinstance(value, str) and not value.strip():
                    msg = f"Empty value in variable '{key}'"
                    self._add_warning(msg)
            if key not in VARIABLES:
                continue
            expected = getattr(VARIABLES[key], attribute)
            if callable(expected):
                expected = expected(self.nc)
            if expected is not None:
                value = getattr(variable, attribute, "")
                if value != expected:
                    msg = utils.create_expected_received_msg(
                        expected, value, variable=key
                    )
                    self._add_warning(msg)


# --------------------#
# ------ Infos ------ #
# --------------------#


class FindVariableOutliers(Test):
    name = "Variable outliers"
    description = "Find suspicious data values."

    def run(self):
        for key in self.nc.variables:
            limits = self._get_limits(key)
            if limits is None:
                continue
            data = self._get_data(key)
            if data.size == 0:
                continue
            max_value = np.max(data)
            min_value = np.min(data)
            if min_value < limits[0]:
                msg = utils.create_out_of_bounds_msg(key, *limits, min_value)
                self._add_info(msg)
            if max_value > limits[1]:
                msg = utils.create_out_of_bounds_msg(key, *limits, max_value)
                self._add_info(msg)

    def _get_limits(self, key: str) -> tuple[float, float] | None:
        if key == "zenith_angle" and self.product in (
            Product.MWR_L1C,
            Product.MWR_SINGLE,
            Product.MWR_MULTI,
        ):
            return None
        if key == "height" and self.product == Product.CPR:
            return None
        if key == "air_pressure":
            pressure = utils.calc_pressure(self.nc["altitude"][:])
            max_diff = pressure * 0.05
            return (pressure - max_diff, pressure + max_diff)
        if not DATA_CONFIG.has_option("limits", key):
            return None
        limit_min, limit_max = DATA_CONFIG.get("limits", key).split(",", maxsplit=1)
        return (float(limit_min), float(limit_max))

    def _get_data(self, key: str) -> np.ndarray:
        data = self.nc[key][:]
        if self.product in (
            Product.MWR_SINGLE,
            Product.MWR_MULTI,
        ) and self.nc[key].dimensions == ("time", "height"):
            for flag_name in (f"{key}_quality_flag", "temperature_quality_flag"):
                if flag_name in self.nc.variables:
                    quality_flag = self.nc[flag_name][:]
                    data = data[quality_flag == 0]
                    break
        return data


class FindFolding(Test):
    name = "Radar folding"
    description = "Test for radar folding."
    products = [Product.RADAR, Product.CATEGORIZE]

    def run(self):
        key = "v"
        v_threshold = 8
        try:
            data = self.nc[key][:]
        except IndexError:
            self._add_error(f"Doppler velocity, '{key}', is missing.")
            return
        difference = np.abs(np.diff(data, axis=1))
        n_suspicious = ma.sum(difference > v_threshold)
        if n_suspicious > 20:
            self._add_info(
                f"{n_suspicious} suspicious pixels. Folding might be present."
            )


class TestDataCoverage(Test):
    name = "Data coverage"
    description = "Test that file contains enough data."

    def run(self):
        coverage, expected_res, actual_res = data_coverage(self.nc)
        if coverage is None:
            return
        self.coverage = coverage
        missing = (1 - coverage) * 100
        if missing > 20:
            message = f"{round(missing)}% of day's data is missing."
            if missing > 60:
                self._add_warning(message)
            else:
                self._add_info(message)

        if actual_res > expected_res * 1.05:
            self._add_warning(
                f"Expected a measurement with interval at least {expected_res},"
                f" got {actual_res} instead"
            )


class TestVariableNamesDefined(Test):
    name = "Variable names"
    description = "Check that variables have expected names."
    products = Product.all() - {
        Product.MODEL,
        Product.L3_CF,
        Product.L3_IWC,
        Product.L3_LWC,
    }

    def run(self):
        for key in self.nc.variables:
            if key not in VARIABLES:
                self._add_info(f"'{key}' is not defined in cloudnetpy-qc.")


# ---------------------- #
# ------ Warnings ------ #
# ---------------------- #


class TestUnits(Test):
    name = "Units"
    description = "Check that variables have expected units."

    def run(self):
        self._test_variable_attribute("units")


class TestLongNames(Test):
    name = "Long names"
    description = "Check that variables have expected long names."
    products = Product.all() - {
        Product.MODEL,
        Product.L3_CF,
        Product.L3_IWC,
        Product.L3_LWC,
    }

    def run(self):
        self._test_variable_attribute("long_name")


class TestStandardNames(Test):
    name = "Standard names"
    description = "Check that variable have expected standard names."
    products = Product.all() - {
        Product.MODEL,
        Product.L3_CF,
        Product.L3_IWC,
        Product.L3_LWC,
    }

    def run(self):
        self._test_variable_attribute("standard_name")


class TestComment(Test):
    name = "Comment"
    description = "Check that variables have expected comments."

    def run(self):
        self._test_variable_attribute("comment")


class TestDataTypes(Test):
    name = "Data types"
    description = "Check that variables have expected data types."

    def run(self):
        for key in self.nc.variables:
            if key not in VARIABLES:
                continue
            expected = VARIABLES[key].dtype.value
            received = self.nc.variables[key].dtype.name
            if received != expected:
                if key == "time" and received in ("float32", "float64"):
                    continue
                msg = utils.create_expected_received_msg(
                    expected, received, variable=key
                )
                self._add_warning(msg)


class TestGlobalAttributes(Test):
    name = "Global attributes"
    description = "Check that file contains required global attributes."

    REQUIRED_ATTRS = {
        "year",
        "month",
        "day",
        "file_uuid",
        "Conventions",
        "location",
        "history",
        "title",
        "cloudnet_file_type",
        "source",
    }

    def _instrument_product(self, product: Product):
        return (LEVELS[product] == "1b" and product != Product.MODEL) or product in (
            Product.MWR_L1C,
            Product.MWR_SINGLE,
            Product.MWR_MULTI,
            Product.DOPPLER_LIDAR_WIND,
            Product.EPSILON_LIDAR,
        )

    def _required_attrs(self, product: Product):
        attrs = set(self.REQUIRED_ATTRS)
        if product == Product.MWR_L1C:
            attrs.add("mwrpy_coefficients")
        if product in (Product.MWR_SINGLE, Product.MWR_MULTI, Product.EPSILON_LIDAR):
            attrs.add("source_file_uuids")
        if product != Product.MODEL:
            attrs.add(
                "instrument_pid"
                if self._instrument_product(product)
                else "source_file_uuids"
            )
        return attrs

    def _optional_attr(self, name: str, product: Product) -> bool:
        return (
            name in ("references", "pid")
            or name.endswith("_version")
            or (
                product == Product.MODEL
                and name in ("initialization_time", "institution")
            )
            or (self._instrument_product(product) and name == "serial_number")
        )

    def run(self):
        nc_keys = set(self.nc.ncattrs())
        for key in nc_keys:
            value = getattr(self.nc, key)
            if isinstance(value, str) and not value.strip():
                msg = f"Empty value in attribute '{key}'"
                self._add_warning(msg)
        required_attrs = self._required_attrs(self.product)
        missing_keys = required_attrs - nc_keys
        for key in missing_keys:
            self._add_warning(f"Attribute '{key}' is missing.")
        extra_keys = nc_keys - required_attrs
        for key in extra_keys:
            if not self._optional_attr(key, self.product):
                self._add_warning(f"Unknown attribute '{key}' found.")


class TestMedianLwp(Test):
    name = "Median LWP"
    description = "Test that LWP data are valid."
    products = [Product.MWR, Product.CATEGORIZE]

    def run(self):
        key = "lwp"
        if key not in self.nc.variables:
            self._add_warning(f"'{key}' is missing.")
            return
        data = self.nc.variables[key][:]
        mask_percentage = ma.count_masked(data) / data.size * 100
        if mask_percentage > 20:
            msg = (
                f"{round(mask_percentage, 1)} % of '{key}' data points are masked "
                f"due to low quality data."
            )
            if mask_percentage > 60:
                self._add_warning(msg)
            else:
                self._add_info(msg)
        limits = [-0.5, 10]
        median_lwp = ma.median(data) / 1000  # g -> kg
        if median_lwp < limits[0] or median_lwp > limits[1]:
            msg = utils.create_out_of_bounds_msg(key, *limits, median_lwp)
            self._add_warning(msg)


class FindAttributeOutliers(Test):
    name = "Attribute outliers"
    description = "Find suspicious values in global attributes."

    def run(self):
        try:
            year = int(self.nc.year)
            month = int(self.nc.month)
            day = int(self.nc.day)
            datetime.date(year, month, day)
        except AttributeError:
            self._add_warning("Missing some date attributes.")
        except ValueError:
            self._add_warning("Invalid date attributes.")


class TestLDR(Test):
    name = "LDR values"
    description = "Test that LDR values are proper."
    products = [Product.RADAR, Product.CATEGORIZE]

    def run(self):
        has_ldr = "ldr" in self.nc.variables or "sldr" in self.nc.variables
        has_v = "v" in self.nc.variables
        if has_v and has_ldr:
            v = self.nc["v"][:]
            ldr = (
                self.nc["ldr"][:] if "ldr" in self.nc.variables else self.nc["sldr"][:]
            )
            v_count = ma.count(v)
            ldr_count = ma.count(ldr)
            if v_count > 0 and ldr_count == 0:
                self._add_warning("All LDR are masked.")
            elif v_count > 0 and (ldr_count / v_count * 100) < 0.1:
                self._add_warning("LDR exists in less than 0.1 % of pixels.")


class TestUnexpectedMask(Test):
    name = "Unexpected mask"
    description = "Test if data contain unexpected masked values."

    def run(self):
        for key in ("range", "time", "height"):
            if key not in self.nc.variables:
                continue
            data = self.nc[key][:]
            if np.all(data.mask):
                self._add_warning(f"Variable '{key}' is completely masked.")
            elif np.any(data.mask):
                percentage = np.sum(data.mask) / data.size * 100
                self._add_warning(
                    f"Variable '{key}' contains masked values "
                    f"({percentage:.1f} % are masked)."
                )


class TestMask(Test):
    name = "Data mask"
    description = "Test that data are not completely masked."
    products = [Product.RADAR]

    def run(self):
        if not np.any(~self.nc["v"][:].mask):
            self._add_error("All data are masked.")


class TestIfRangeCorrected(Test):
    name = "Range correction"
    description = "Test that beta is range corrected."
    products = [Product.LIDAR]

    def run(self):
        try:
            range_var = self.nc["range"]
            beta_raw = self.nc["beta_raw"]
        except IndexError:
            return

        n_top_ranges = len(range_var) // 2
        x = range_var[-n_top_ranges:] ** 2
        y = np.std(beta_raw[:, -n_top_ranges:], axis=0)
        sgl_res = scipy.stats.siegelslopes(y, x)
        residuals = np.abs(y - (sgl_res.intercept + sgl_res.slope * x))
        outliers = residuals > 20 * np.percentile(
            residuals.compressed(), 25
        )  # Ad hoc outlier detection
        res = scipy.stats.pearsonr(x[~outliers], y[~outliers])
        if res.statistic < 0.75:
            self._add_warning("Data might not be range corrected.")


class TestFloatingPointValues(Test):
    name = "Floating-point values"
    description = (
        "Test for special floating-point values "
        "which may indicate problems with the processing."
    )

    def run(self):
        for name, variable in self.nc.variables.items():
            if variable.dtype.kind != "f":
                continue
            if np.isnan(variable[:]).any():
                self._add_warning(f"Variable '{name}' contains NaN value(s).")
            if np.isinf(variable[:]).any():
                self._add_warning(f"Variable '{name}' contains infinite value(s).")


class TestFillValue(Test):
    name = "Fill value"
    description = (
        "Test that fill value is explicitly set for variables with missing data."
    )

    def run(self):
        for name, variable in self.nc.variables.items():
            if variable[:].mask.any() and not hasattr(variable, "_FillValue"):
                self._add_warning(
                    f"Attribute '_FillValue' is missing from variable '{name}'."
                )


class TestRainfallConsistency(Test):
    name = "Precipitation consistency"
    description = "Test that precipitation rate and amount are consistent."
    products = [Product.WEATHER_STATION, Product.RAIN_GAUGE, Product.DISDROMETER]

    def run(self):
        for key in ("rainfall", "snowfall", "precipitation"):
            self._test_variable(key)

    def _test_variable(self, key: str) -> None:
        key_rate = f"{key}_rate"
        key_amount = f"{key}_amount"
        if key_rate not in self.nc.variables or key_amount not in self.nc.variables:
            return
        expected_amount = self.nc[key_amount][-1]  # m
        rate = self.nc[key_rate][:]  # m s-1
        interval = np.diff(self.nc["time"][:], prepend=0) * H_TO_S
        calculated_amount = np.sum(rate * interval)
        error = (expected_amount - calculated_amount) * M_TO_MM
        if np.abs(error) > 20:
            self._add_warning(
                f"Total accumulated {key} has difference of {round(error, 1)} mm"
            )


# ---------------------#
# ------ Errors ------ #
# -------------------- #


class TestDataModel(Test):
    name = "Data model"
    description = "Test netCDF data model."

    def run(self):
        expected = "NETCDF4_CLASSIC"
        received = self.nc.data_model
        if expected != received:
            self._add_error(utils.create_expected_received_msg(expected, received))


class TestBrightnessTemperature(Test):
    name = "Brightness temperature"
    description = "Test that brightness temperature data are valid."
    products = [Product.MWR_L1C]

    def run(self):
        flags = self.nc["quality_flag"][:]
        bad_percentage = ma.sum(flags != 0) / flags.size * 100
        if bad_percentage > 90:
            self._add_error("More than 90% of the data are flagged.")
        elif bad_percentage > 50:
            self._add_warning("More than 50% of the data are flagged.")


class TestMWRSingleLWP(Test):
    name = "MWR single pointing LWP"
    description = "Test that LWP data are valid."
    products = [Product.MWR_SINGLE]

    def run(self):
        flags = self.nc["lwp_quality_flag"][:]
        bad_percentage = ma.sum(flags != 0) / flags.size * 100
        if bad_percentage > 90:
            self._add_error("More than 90% of the data are flagged.")
        elif bad_percentage > 50:
            self._add_warning("More than 50% of the data are flagged.")


class TestMWRMultiTemperature(Test):
    name = "MWR multiple pointing temperature"
    description = "Test that temperature data are valid."
    products = [Product.MWR_MULTI]

    def run(self):
        flags = self.nc["temperature_quality_flag"][:]
        if not np.any(flags == 0):
            self._add_error("No valid temperature data found.")


class TestLidarBeta(Test):
    name = "Beta presence"
    description = "Test that one beta variable exists."
    products = [Product.LIDAR]

    def run(self):
        valid_keys = {"beta", "beta_1064", "beta_532", "beta_355"}
        for key in valid_keys:
            if key in self.nc.variables:
                return
        self._add_error("No valid beta variable found.")


class TestTimeVector(Test):
    name = "Time vector"
    description = "Test that time vector is continuous."

    def run(self):
        time = self.nc["time"][:]
        try:
            n_time = len(time)
        except (TypeError, ValueError):
            self._add_error("Time vector is empty.")
            return
        if n_time == 0:
            self._add_error("Time vector is empty.")
            return
        if n_time == 1:
            self._add_error("One time step only.")
            return
        differences = np.diff(time)
        min_difference = np.min(differences)
        max_difference = np.max(differences)
        if min_difference <= 0:
            msg = utils.create_out_of_bounds_msg("time", 0, 24, min_difference)
            self._add_error(msg)
        if max_difference >= 24:
            msg = utils.create_out_of_bounds_msg("time", 0, 24, max_difference)
            self._add_error(msg)


class TestVariableNames(Test):
    name = "Variables"
    description = "Check that file contains required variables."

    def run(self):
        keys_in_file = set(self.nc.variables.keys())
        required_keys = self._get_required_variable_names()
        missing_keys = list(required_keys - keys_in_file)
        for key in missing_keys:
            self._add_error(f"'{key}' is missing.")


class TestModelData(Test):
    name = "Model data"
    description = "Test that model data are valid."
    products = [Product.MODEL]

    def run(self):
        time = np.array(self.nc["time"][:])
        time_unit = datetime.timedelta(hours=1)

        try:
            n_time = len(time)
        except (TypeError, ValueError):
            return
        if n_time < 2:
            return

        duration = get_duration(self.nc)
        should_be_data_until = duration / time_unit

        for key in ("temperature", "pressure", "q"):
            if key not in self.nc.variables:
                continue
            data = self.nc[key][:]
            missing_hours = [
                int(hour)
                for ind, hour in enumerate(time)
                if hour <= should_be_data_until
                and ma.count_masked(data[ind, :]) == data.shape[1]
            ]
            if not missing_hours:
                continue
            noun, verb = ("Hour", "is") if len(missing_hours) == 1 else ("Hours", "are")
            values = utils.format_list(utils.integer_ranges(missing_hours), "and")
            self._add_error(f"{noun} {values} {verb} missing from variable '{key}'.")


class TestCoordinateVariables(Test):
    name = "Coordinate variables"
    description = "Test dimensions of coordinate variables are correct."

    def run(self):
        for key, variable in self.nc.variables.items():
            if key in self.nc.dimensions and (
                len(variable.dimensions) != 1 or key != variable.dimensions[0]
            ):
                received = "', '".join(variable.dimensions)
                self._add_error(
                    f"Expected variable '{key}' to have dimensions '{key}'"
                    f" but received '{received}'"
                )


class TestCoordinates(Test):
    name = "Coordinates"
    description = "Check that file coordinates match site coordinates."

    def run(self):
        required_vars = {"latitude", "longitude"}
        if self.nc.cloudnet_file_type != "model":
            required_vars.add("altitude")
        for key in required_vars:
            if key not in self.nc.variables:
                self._add_error(f"Variable '{key}' is missing")

        if "latitude" in self.nc.variables and "longitude" in self.nc.variables:
            site_lat = np.atleast_1d(self.site_meta["latitude"])
            site_lon = np.atleast_1d(self.site_meta["longitude"])
            file_lat = np.atleast_1d(self.nc["latitude"][:])
            file_lon = np.atleast_1d(self.nc["longitude"][:])
            file_lon[file_lon > 180] -= 360

            if (
                self.site_meta["time"] is not None
                and file_lat.size > 1
                and file_lon.size > 1
            ):
                site_time = self._read_site_time()
                file_time = self._read_file_time()
                idx = utils.find_closest(file_time, site_time)
                file_lat = file_lat[idx]
                file_lon = file_lon[idx]
            else:
                file_lat, file_lon = utils.average_coordinate(file_lat, file_lon)
                site_lat, site_lon = utils.average_coordinate(site_lat, site_lon)
                file_lat = np.atleast_1d(file_lat)
                file_lon = np.atleast_1d(file_lon)
                site_lat = np.atleast_1d(site_lat)
                site_lon = np.atleast_1d(site_lon)

            dist = utils.haversine(site_lat, site_lon, file_lat, file_lon)
            i = np.argmax(dist)
            max_dist = self._calc_max_dist(site_lat, site_lon)
            if dist[i] > max_dist:
                self._add_error(
                    f"Variables 'latitude' and 'longitude' do not match "
                    f"the site coordinates: "
                    f"expected ({site_lat[i]:.3f},\u00a0{site_lon[i]:.3f}) "
                    f"but received ({file_lat[i]:.3f},\u00a0{file_lon[i]:.3f}), "
                    f"distance {round(dist[i])}\u00a0km"
                )

        if "altitude" in self.nc.variables:
            site_alt = self.site_meta["altitude"]
            file_alt = np.atleast_1d(self.nc["altitude"][:])
            diff_alt = np.abs(site_alt - file_alt)
            i = np.argmax(diff_alt)
            if diff_alt[i] > 100:
                self._add_error(
                    f"Variable 'altitude' doesn't match the site altitude: "
                    f"expected {round(site_alt)}\u00a0m "
                    f"but received {round(file_alt[i])}\u00a0m"
                )

    def _read_site_time(self):
        for dt in self.site_meta["time"]:
            if (
                not isinstance(dt, datetime.datetime)
                or dt.tzinfo is None
                or dt.tzinfo.utcoffset(dt) is None
            ):
                raise ValueError("Naive datetimes are not supported")
        naive_dt = [
            dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            for dt in self.site_meta["time"]
        ]
        return np.array(naive_dt, dtype="datetime64[s]")

    def _read_file_time(self):
        naive_dt = num2pydate(
            self.nc["time"][:], self.nc["time"].units, self.nc["time"].calendar
        )
        return np.array(naive_dt, dtype="datetime64[s]")

    def _calc_max_dist(self, latitude, longitude):
        if self.nc.cloudnet_file_type == "model":
            mean_lat = np.mean(latitude)
            mean_lon = np.mean(longitude)
            angle = 1  # Model resolution should be at least 1 degrees.
            half_angle = angle / 2
            min_lat = np.maximum(-90, mean_lat - half_angle)
            max_lat = np.minimum(90, mean_lat + half_angle)
            min_lon = np.maximum(-180, mean_lon - half_angle)
            max_lon = np.minimum(180, mean_lon + half_angle)
            return utils.haversine(min_lat, min_lon, max_lat, max_lon)
        return 10


# ------------------------------#
# ------ Error / Warning ------ #
# ----------------------------- #


class TestCFConvention(Test):
    name = "CF conventions"
    description = "Test compliance with the CF metadata conventions."

    def run(self):
        from cfchecker import cfchecks

        cf_version = "1.8"
        inst = cfchecks.CFChecker(
            silent=True,
            version=cf_version,
            cfStandardNamesXML=CF_STANDARD_NAMES_XML,
            cfAreaTypesXML=CF_AREA_TYPES_XML,
            cfRegionNamesXML=CF_REGION_NAMES_XML,
        )
        result = inst.checker(str(self.filename))
        for key in result["variables"]:
            for level, error_msg in result["variables"][key].items():
                if not error_msg:
                    continue
                if level in ("FATAL", "ERROR"):
                    severity = ErrorLevel.ERROR
                elif level == "WARN":
                    severity = ErrorLevel.WARNING
                else:
                    continue
                msg = utils.format_msg(error_msg)
                msg = f"Variable '{key}': {msg}"
                self._add_message(msg, severity)


class TestInstrumentPid(Test):
    name = "Instrument PID"
    description = "Test that valid instrument PID exists."
    products = [
        Product.MWR,
        Product.LIDAR,
        Product.RADAR,
        Product.DISDROMETER,
        Product.DOPPLER_LIDAR,
        Product.DOPPLER_LIDAR_WIND,
        Product.WEATHER_STATION,
    ]

    data: dict = {}

    def run(self):
        if self._check_exists():
            try:
                self.data = utils.fetch_pid(self.nc.instrument_pid)
                self._check_serial()
                self._check_model_name()
                self._check_model_identifier()
            except RequestException:
                self._add_info("Failed to fetch instrument PID")

    def _check_exists(self) -> bool:
        key = "instrument_pid"
        try:
            pid = getattr(self.nc, key)
            if pid == "":
                self._add_error("Instrument PID is empty.")
                return False
            if re.fullmatch(utils.PID_FORMAT, pid) is None:
                self._add_error("Instrument PID has invalid format.")
                return False
        except AttributeError:
            self._add_warning("Instrument PID is missing.")
            return False
        return True

    def _get_value(self, kind: str) -> dict | list | None:
        try:
            item = next(item for item in self.data["values"] if item["type"] == kind)
            return json.loads(item["data"]["value"])
        except StopIteration:
            return None

    def _create_message(
        self,
        expected: str | list[str],
        received: str,
        obj: str | None = None,
    ) -> str:
        if isinstance(expected, str):
            expected = [expected]
        expected = utils.format_list([f"'{var}'" for var in expected], "or")
        msg = f"Expected {obj} to be {expected} but received '{received}'"
        return msg

    def _check_serial(self):
        key = "serial_number"
        try:
            received = str(getattr(self.nc, key))
        except AttributeError:
            return
        items = self._get_value("21.T11148/eb3c713572f681e6c4c3")
        if not isinstance(items, list):
            return
        model_name = self._get_value("21.T11148/c1a0ec5ad347427f25d6")["modelName"]
        for item in items:
            if item["alternateIdentifier"]["alternateIdentifierType"] == "SerialNumber":
                expected = item["alternateIdentifier"]["alternateIdentifierValue"]
                if "StreamLine" in model_name:
                    expected = expected.split("-")[-1]
                if received != expected:
                    msg = self._create_message(expected, received, "serial number")
                    self._add_error(msg)
                return
        self._add_warning(
            f"No serial number was defined in instrument PID "
            f"but found '{received}' in the file."
        )

    def _check_model_name(self):
        key = "source"
        try:
            source = getattr(self.nc, key)
            allowed_values = self.SOURCE_TO_NAME[source]
        except (AttributeError, KeyError):
            return
        model = self._get_value("21.T11148/c1a0ec5ad347427f25d6")
        if model is None:
            return
        received = model["modelName"]
        if received not in allowed_values:
            msg = self._create_message(allowed_values, received, "model name")
            self._add_error(msg)

    def _check_model_identifier(self):
        key = "source"
        try:
            source = getattr(self.nc, key)
            allowed_values = self.SOURCE_TO_IDENTIFIER[source]
        except (AttributeError, KeyError):
            return
        model = self._get_value("21.T11148/c1a0ec5ad347427f25d6")
        if model is None:
            return
        if "modelIdentifier" not in model:
            return
        received = model["modelIdentifier"]["modelIdentifierValue"]
        if received not in allowed_values:
            msg = self._create_message(allowed_values, received, "model identifier")
            self._add_error(msg)

    SOURCE_TO_NAME = {
        "Lufft CHM15k": ["Lufft CHM 15k", "Lufft CHM 15k-x"],
        "Lufft CHM15kx": ["Lufft CHM 15k", "Lufft CHM 15k-x"],
        "TROPOS PollyXT": ["PollyXT"],
        "Vaisala CL31": ["Vaisala CL31"],
        "Vaisala CL51": ["Vaisala CL51"],
        "Vaisala CL61d": ["Vaisala CL61"],
        "Vaisala CT25k": ["Vaisala CT25K"],
        "HALO Photonics StreamLine": [
            "StreamLine",
            "StreamLine Pro",
            "StreamLine XR",
            "StreamLine XR+",
        ],
        "Vaisala WindCube WLS200S": ["Vaisala WindCube WLS200S"],
    }

    SOURCE_TO_IDENTIFIER = {
        "BASTA": ["https://vocabulary.actris.nilu.no/actris_vocab/MeteomodemBASTA"],
        "METEK MIRA-35": [
            "https://vocabulary.actris.nilu.no/actris_vocab/MetekMIRA35",
            "https://vocabulary.actris.nilu.no/actris_vocab/MetekMIRA35S",
            "https://vocabulary.actris.nilu.no/actris_vocab/MetekMIRA35C",
        ],
        "METEK MIRA-10": ["https://vocabulary.actris.nilu.no/actris_vocab/MetekMIRA10"],
        "OTT HydroMet Parsivel2": [
            "https://vocabulary.actris.nilu.no/actris_vocab/OTTParsivel2"
        ],
        "RAL Space Copernicus": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RALCopernicus"
        ],
        "RAL Space Galileo": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RALGalileo"
        ],
        "RPG-Radiometer Physics HATPRO": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RPGHATPRO"
        ],
        "RPG-Radiometer Physics RPG-FMCW-35": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-35-DP",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-35-DP-S",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-35-SP",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-35-SP-S",
        ],
        "RPG-Radiometer Physics RPG-FMCW-94": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94-DP",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94-DP-S",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94-SP",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94-SP-S",
        ],
        "Thies Clima LNM": [
            "https://vocabulary.actris.nilu.no/actris_vocab/ThiesLNM",
            "https://vocabulary.actris.nilu.no/actris_vocab/ThiesLPM",
        ],
        "Thies Clima LPM": ["https://vocabulary.actris.nilu.no/actris_vocab/ThiesLPM"],
        "Vaisala WindCube WLS70": [
            "https://vocabulary.actris.nilu.no/actris_vocab/VaisalaWindCubeWLS70"
        ],
        "Vaisala WindCube WLS100S": [
            "https://vocabulary.actris.nilu.no/actris_vocab/VaisalaWindCube100S"
        ],
        "Vaisala WindCube WLS200S": [
            "https://vocabulary.actris.nilu.no/actris_vocab/VaisalaWindCube200S"
        ],
        "Vaisala WindCube WLS400S": [
            "https://vocabulary.actris.nilu.no/actris_vocab/VaisalaWindCube400S"
        ],
    }
