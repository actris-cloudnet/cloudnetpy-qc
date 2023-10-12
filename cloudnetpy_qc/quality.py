"""Cloudnet product quality checks."""
import dataclasses
import datetime
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import netCDF4
import numpy as np
import scipy.stats
from numpy import ma

from . import utils
from .variables import LEVELS, VARIABLES, Product
from .version import __version__

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

METADATA_CONFIG = utils.read_config(os.path.join(DATA_PATH, "metadata_config.ini"))
DATA_CONFIG = utils.read_config(os.path.join(DATA_PATH, "data_quality_config.ini"))
CF_AREA_TYPES_XML = os.path.join(DATA_PATH, "area-type-table.xml")
CF_STANDARD_NAMES_XML = os.path.join(DATA_PATH, "cf-standard-name-table.xml")
CF_REGION_NAMES_XML = os.path.join(DATA_PATH, "standardized-region-list.xml")


class ErrorLevel(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


@dataclass
class TestReport:
    testId: str
    exceptions: list[dict]

    def values(self):
        return {
            field.name: getattr(self, field.name)
            for field in dataclasses.fields(self)
            if getattr(self, field.name) is not None
        }


@dataclass
class FileReport:
    timestamp: str
    qcVersion: str
    tests: list[dict]


def run_tests(
    filename: Path | str,
    cloudnet_file_type: str | None = None,
    ignore_tests: list[str] | None = None,
) -> dict:
    if isinstance(filename, str):
        filename = Path(filename)
    with netCDF4.Dataset(filename) as nc:
        if cloudnet_file_type is None:
            try:
                cloudnet_file_type = nc.cloudnet_file_type
            except AttributeError:
                logging.error(
                    "No cloudnet_file_type global attribute found, can not run tests. "
                    "Is this a legacy file?"
                )
                return {}
        logging.debug(f"Filename: {filename.stem}")
        logging.debug(f"File type: {cloudnet_file_type}")
        test_reports: list[dict] = []
        for cls in Test.__subclasses__():
            if ignore_tests and cls.__name__ in ignore_tests:
                continue
            test_instance = cls(nc, filename, cloudnet_file_type)
            if cloudnet_file_type in test_instance.products:
                test_instance.run()
                for exception in test_instance.report.values()["exceptions"]:
                    assert exception["result"] in (
                        ErrorLevel.ERROR,
                        ErrorLevel.WARNING,
                        ErrorLevel.INFO,
                    )
                test_reports.append(test_instance.report.values())
    return FileReport(
        timestamp=f"{datetime.datetime.now().isoformat()}Z",
        qcVersion=__version__,
        tests=test_reports,
    ).__dict__


def test(
    name: str,
    description: str,
    products: list[Product] | None = None,
    ignore_products: list[Product] | None = None,
):
    """Decorator for the tests."""

    def fun(cls):
        setattr(cls, "name", name)
        setattr(cls, "description", description)
        if products is not None:
            setattr(cls, "products", [member.value for member in products])
        if ignore_products is not None:
            prods = list(set(getattr(cls, "products")) - set(ignore_products))
            setattr(cls, "products", prods)
        return cls

    return fun


class Test:
    """Test base class."""

    name: str
    description: str
    products: list[str] = Product.all()

    def __init__(self, nc: netCDF4.Dataset, filename: Path, cloudnet_file_type: str):
        self.filename = filename
        self.nc = nc
        self.cloudnet_file_type = cloudnet_file_type
        self.report = TestReport(
            testId=self.__class__.__name__,
            exceptions=[],
        )

    def run(self):
        raise NotImplementedError

    def _add_message(self, message: str | list, severity: ErrorLevel):
        self.report.exceptions.append(
            {
                "message": utils.format_msg(message),
                "result": severity,
            }
        )

    def _add_info(self, message: str | list):
        self._add_message(message, ErrorLevel.INFO)

    def _add_warning(self, message: str | list):
        self._add_message(message, ErrorLevel.WARNING)

    def _add_error(self, message: str | list):
        self._add_message(message, ErrorLevel.ERROR)

    def _read_config_keys(self, config_section: str) -> np.ndarray:
        field = "all" if "attr" in config_section else self.cloudnet_file_type
        keys = METADATA_CONFIG[config_section][field].split(",")
        return np.char.strip(keys)

    def _get_required_variables(self) -> dict:
        return {
            name: var
            for name, var in VARIABLES.items()
            if var.required is not None and self.cloudnet_file_type in var.required
        }

    def _get_required_variable_names(self) -> set:
        required_variables = self._get_required_variables()
        return set(required_variables.keys())

    def _test_variable_attribute(self, attribute: str):
        for key in self.nc.variables.keys():
            if key not in VARIABLES:
                continue
            expected = getattr(VARIABLES[key], attribute)
            if callable(expected):
                expected = expected(self.nc)
            if expected is not None:
                value = getattr(self.nc.variables[key], attribute, "")
                if value != expected:
                    msg = utils.create_expected_received_msg(
                        expected, value, variable=key
                    )
                    self._add_warning(msg)

    def _get_date(self):
        date_in_file = [int(getattr(self.nc, x)) for x in ("year", "month", "day")]
        return datetime.date(*date_in_file)


# --------------------#
# ------ Infos ------ #
# --------------------#


@test("Variable outliers", "Find suspicious data values.")
class FindVariableOutliers(Test):
    def run(self):
        for key, limits_str in DATA_CONFIG.items("limits"):
            if key == "zenith_angle" and self.cloudnet_file_type.startswith("mwr-"):
                continue
            limits = [float(x) for x in limits_str.split(",")]
            if key in self.nc.variables:
                data = self.nc.variables[key][:]
                if data.ndim > 0 and len(data) == 0:
                    break
                max_value = np.max(data)
                min_value = np.min(data)
                if min_value < limits[0]:
                    msg = utils.create_out_of_bounds_msg(key, *limits, min_value)
                    self._add_info(msg)
                if max_value > limits[1]:
                    msg = utils.create_out_of_bounds_msg(key, *limits, max_value)
                    self._add_info(msg)


@test(
    "Radar folding",
    "Test for radar folding.",
    products=[Product.RADAR, Product.CATEGORIZE],
)
class FindFolding(Test):
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


@test(
    "Data coverage",
    "Test that file contains enough data.",
)
class TestDataCoverage(Test):
    RESOLUTIONS = {
        Product.DISDROMETER: datetime.timedelta(minutes=1),
        Product.L3_CF: datetime.timedelta(hours=1),
        Product.L3_IWC: datetime.timedelta(hours=1),
        Product.L3_LWC: datetime.timedelta(hours=1),
        Product.MODEL: datetime.timedelta(hours=1),
        Product.MWR: datetime.timedelta(minutes=2),
        Product.MWR_MULTI: datetime.timedelta(minutes=20),
        Product.MWR_SINGLE: datetime.timedelta(minutes=2),
        Product.WEATHER_STATION: datetime.timedelta(minutes=1),
    }
    DEFAULT_RESOLUTION = datetime.timedelta(seconds=30)

    def run(self):
        time = np.array(self.nc["time"][:])
        time_unit = datetime.timedelta(hours=1)
        try:
            n_time = len(time)
        except (TypeError, ValueError):
            return
        if n_time < 2:
            return
        expected_res = self.RESOLUTIONS.get(
            self.cloudnet_file_type, self.DEFAULT_RESOLUTION
        )
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        if now.date() == self._get_date():
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            duration = now - midnight
        else:
            duration = datetime.timedelta(days=1)
        bins = max(1, duration // expected_res)
        hist, _bin_edges = np.histogram(
            time, bins=bins, range=(0, duration / time_unit)
        )
        missing = np.count_nonzero(hist == 0) / len(hist) * 100
        if missing > 20:
            message = f"{round(missing)}% of day's data is missing."
            if missing > 60:
                self._add_warning(message)
            else:
                self._add_info(message)

        actual_res = np.median(np.diff(time)) * time_unit
        if actual_res > expected_res * 1.05:
            self._add_warning(
                f"Expected a measurement with interval at least {expected_res},"
                f" got {actual_res} instead"
            )


@test(
    "Variable names",
    "Check that variables have expected names.",
    ignore_products=[Product.MODEL, Product.L3_CF, Product.L3_IWC, Product.L3_LWC],
)
class TestVariableNamesDefined(Test):
    def run(self):
        for key in self.nc.variables.keys():
            if key not in VARIABLES:
                self._add_info(f"'{key}' is not defined in cloudnetpy-qc.")


# ---------------------- #
# ------ Warnings ------ #
# ---------------------- #


@test("Units", "Check that variables have expected units.")
class TestUnits(Test):
    def run(self):
        self._test_variable_attribute("units")


@test(
    "Long names",
    "Check that variables have expected long names.",
    ignore_products=[Product.MODEL, Product.L3_CF, Product.L3_IWC, Product.L3_LWC],
)
class TestLongNames(Test):
    def run(self):
        self._test_variable_attribute("long_name")


@test(
    "Standard names",
    "Check that variable have expected standard names.",
    ignore_products=[Product.MODEL, Product.L3_CF, Product.L3_IWC, Product.L3_LWC],
)
class TestStandardNames(Test):
    def run(self):
        self._test_variable_attribute("standard_name")


@test("Data types", "Check that variables have expected data types.")
class TestDataTypes(Test):
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


# @test(
#     "Time data type",
#     "Check that time vector is in double precision.",
#     products=[
#         Product.RADAR,
#         Product.LIDAR,
#         Product.MWR,
#         Product.DISDROMETER,
#         Product.WEATHER_STATION,
#     ],
# )
# class TestTimeVectorDataType(Test):
#     def run(self):
#         key = "time"
#         received = self.nc.variables[key].dtype.name
#         expected = "float64"
#         if received != expected:
#             msg = utils.create_expected_received_msg(key, expected, received)
#             self._add_warning(msg)


@test("Global attributes", "Check that file contains required global attributes.")
class TestGlobalAttributes(Test):
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
        return (
            LEVELS[product] == "1b" and product != Product.MODEL
        ) or product == Product.MWR_L1C

    def _required_attrs(self, product: Product):
        attrs = set(self.REQUIRED_ATTRS)
        if product == Product.MWR_L1C:
            attrs.add("mwrpy_coefficients")
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
        required_attrs = self._required_attrs(self.cloudnet_file_type)
        missing_keys = required_attrs - nc_keys
        for key in missing_keys:
            self._add_warning(f"Attribute '{key}' is missing.")
        extra_keys = nc_keys - required_attrs
        for key in extra_keys:
            if not self._optional_attr(key, self.cloudnet_file_type):
                self._add_warning(f"Unknown attribute '{key}' found.")


@test(
    "Median LWP",
    "Test that LWP data are valid.",
    [Product.MWR, Product.CATEGORIZE],
)
class TestMedianLwp(Test):
    def run(self):
        key = "lwp"
        if key not in self.nc.variables:
            self._add_error(f"'{key}' is missing.")
            return
        data = self.nc.variables[key][:]
        mask_percentage = ma.count_masked(data) / data.size * 100
        if mask_percentage > 20:
            msg = (
                f"{round(mask_percentage,1)} % of '{key}' data points are masked "
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


@test("Attribute outliers", "Find suspicious values in global attributes.")
class FindAttributeOutliers(Test):
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


@test(
    "LDR values",
    "Test that LDR values are proper.",
    products=[Product.RADAR, Product.CATEGORIZE],
)
class TestLDR(Test):
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
            if v_count > 0 and (ldr_count / v_count * 100) < 0.1:
                self._add_warning("LDR exists in less than 0.1 % of pixels.")


@test(
    "Range correction", "Test that beta is range corrected.", products=[Product.LIDAR]
)
class TestIfRangeCorrected(Test):
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
            residuals, 25
        )  # Ad hoc outlier detection
        res = scipy.stats.pearsonr(x[~outliers], y[~outliers])
        if res.statistic < 0.75:
            self._add_warning("Data might not be range corrected.")


@test(
    "Floating-point values",
    "Test for special floating-point values which may indicate problems with the processing.",
)
class TestFloatingPointValues(Test):
    def run(self):
        for name, variable in self.nc.variables.items():
            if variable.dtype.kind != "f":
                continue
            if np.isnan(variable[:]).any():
                self._add_warning(f"Variable '{name}' contains NaN value(s).")
            if np.isinf(variable[:]).any():
                self._add_warning(f"Variable '{name}' contains infinite value(s).")


# ---------------------#
# ------ Errors ------ #
# -------------------- #


@test(
    "Beta presence",
    "Test that one beta variable exists.",
    products=[Product.LIDAR],
)
class TestLidarBeta(Test):
    def run(self):
        valid_keys = {"beta", "beta_1064", "beta_532", "beta_355"}
        for key in valid_keys:
            if key in self.nc.variables:
                return
        self._add_error("No valid beta variable found.")


@test("Time vector", "Test that time vector is continuous.")
class TestTimeVector(Test):
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


@test("Variables", "Check that file contains required variables.")
class TestVariableNames(Test):
    def run(self):
        keys_in_file = set(self.nc.variables.keys())
        required_keys = self._get_required_variable_names()
        missing_keys = list(required_keys - keys_in_file)
        for key in missing_keys:
            self._add_error(f"'{key}' is missing.")


# ------------------------------#
# ------ Error / Warning ------ #
# ----------------------------- #


@test("CF conventions", "Test compliance with the CF metadata conventions.")
class TestCFConvention(Test):
    def run(self):
        from cfchecker import cfchecks  # pylint: disable=import-outside-toplevel

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


@test(
    "Instrument PID",
    "Test that valid instrument PID exists.",
    [
        Product.MWR,
        Product.LIDAR,
        Product.RADAR,
        Product.DISDROMETER,
        Product.DOPPLER_LIDAR,
        Product.WEATHER_STATION,
    ],
)
class TestInstrumentPid(Test):
    data: dict = {}

    def run(self):
        if self._check_exists():
            self.data = utils.fetch_pid(self.nc.instrument_pid)
            self._check_serial()
            self._check_model_name()
            self._check_model_identifier()

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
                    msg = utils.create_expected_received_msg(expected, received)
                    self._add_error(msg)
                return
        self._add_warning(
            f"No serial number was defined in instrument PID but found '{received}' in the file."
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
            msg = utils.create_expected_received_msg(allowed_values, received)
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
            msg = utils.create_expected_received_msg(allowed_values, received)
            self._add_error(msg)

    SOURCE_TO_NAME = {
        "Lufft CHM15k": ["Lufft CHM 15k"],
        "Lufft CHM15kx": ["Lufft CHM 15k-x"],
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
    }

    SOURCE_TO_IDENTIFIER = {
        "BASTA": ["https://vocabulary.actris.nilu.no/actris_vocab/BASTA"],
        "METEK MIRA-35": [
            "https://vocabulary.actris.nilu.no/actris_vocab/METEKMIRA35",
            "https://vocabulary.actris.nilu.no/actris_vocab/METEKMIRA35S",
        ],
        "OTT HydroMet Parsivel2": [
            "https://vocabulary.actris.nilu.no/actris_vocab/OTTParsivel2"
        ],
        "RAL Space Copernicus": [
            "https://vocabulary.actris.nilu.no/actris_vocab/UFAMCopernicus"
        ],
        "RAL Space Galileo": [
            "https://vocabulary.actris.nilu.no/actris_vocab/UFAMGalileo"
        ],
        "RPG-Radiometer Physics HATPRO": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RPGHATPRO"
        ],
        "RPG-Radiometer Physics RPG-FMCW-35": [
            "https://vocabulary.actris.nilu.no/skosmos/actris_vocab/en/page/RPG-FMCW-35-DP"
            "https://vocabulary.actris.nilu.no/skosmos/actris_vocab/en/page/RPG-FMCW-35-SP"
            "https://vocabulary.actris.nilu.no/skosmos/actris_vocab/en/page/RPG-FMCW-35S"
        ],
        "RPG-Radiometer Physics RPG-FMCW-94": [
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94-DP",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94-SP",
            "https://vocabulary.actris.nilu.no/actris_vocab/RPG-FMCW-94S",
        ],
        "Thies Clima LNM": ["https://vocabulary.actris.nilu.no/actris_vocab/ThiesLNM"],
    }
