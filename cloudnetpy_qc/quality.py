"""Cloudnet product quality checks."""
import dataclasses
import datetime
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import netCDF4
import numpy as np
import scipy.stats
from numpy import ma

from . import utils
from .variables import VARIABLES, Product
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
    error_level: ErrorLevel | None = None,
    products: list[Product] | None = None,
    ignore_products: list[Product] | None = None,
):
    """Decorator for the tests."""

    def fun(cls):

        setattr(cls, "name", name)
        setattr(cls, "description", description)
        if error_level is not None:
            setattr(cls, "severity", error_level)
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
    severity = ErrorLevel.WARNING
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

    def _add_message(self, message: str | list):
        self.report.exceptions.append(
            {
                "message": utils.format_msg(message),
                "result": self.severity,
            }
        )

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
            if expected is not None:
                value = getattr(self.nc.variables[key], attribute, "")
                if value != expected:
                    msg = utils.create_expected_received_msg(key, expected, value)
                    self._add_message(msg)

    def _get_date(self):
        date_in_file = [int(getattr(self.nc, x)) for x in ("year", "month", "day")]
        return datetime.date(*date_in_file)


# --------------------#
# ------ Infos ------ #
# --------------------#


@test("Variable outliers", "Find suspicious data values.", error_level=ErrorLevel.INFO)
class FindVariableOutliers(Test):
    def run(self):
        for key, limits_str in DATA_CONFIG.items("limits"):
            limits = [float(x) for x in limits_str.split(",")]
            if key in self.nc.variables:
                data = self.nc.variables[key][:]
                if data.ndim > 0 and len(data) == 0:
                    self.severity = ErrorLevel.ERROR
                    break
                max_value = np.max(data)
                min_value = np.min(data)
                if min_value < limits[0]:
                    msg = utils.create_out_of_bounds_msg(key, *limits, min_value)
                    self._add_message(msg)
                if max_value > limits[1]:
                    msg = utils.create_out_of_bounds_msg(key, *limits, max_value)
                    self._add_message(msg)


@test(
    "Radar folding",
    "Test for radar folding.",
    products=[Product.RADAR, Product.CATEGORIZE],
    error_level=ErrorLevel.INFO,
)
class FindFolding(Test):
    def run(self):
        key = "v"
        v_threshold = 8
        try:
            data = self.nc[key][:]
        except IndexError:
            self.severity = ErrorLevel.ERROR
            self._add_message(f"Doppler velocity, '{key}', is missing.")
            return
        difference = np.abs(np.diff(data, axis=1))
        n_suspicious = ma.sum(difference > v_threshold)
        if n_suspicious > 20:
            self._add_message(f"{n_suspicious} suspicious pixels. Folding might be present.")


@test(
    "Data coverage",
    "Test that file contains enough data.",
    ignore_products=[Product.MODEL],
    error_level=ErrorLevel.INFO,
)
class TestDataCoverage(Test):
    def run(self):
        date_in_file = self._get_date()
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        current_fraction_hour = (
            now.hour + int(now.minute) / 60 if now.date() == date_in_file else 24
        )
        grid = ma.array(np.linspace(0, current_fraction_hour, int(24 * (60 / 5)) + 1))
        time = self.nc["time"][:]
        bins_with_no_data = 0
        for ind, t in enumerate(grid[:-1]):
            ind2 = np.where((time > t) & (time <= grid[ind + 1]))[0]
            if len(ind2) == 0:
                bins_with_no_data += 1
        missing = bins_with_no_data / len(grid) * 100
        if missing > 20:
            if missing > 60:
                self.severity = ErrorLevel.WARNING
            self._add_message(f"{round(missing)}% of day's data is missing.")


@test(
    "Variable names",
    "Check that variables have expected names.",
    ignore_products=[Product.MODEL],
    error_level=ErrorLevel.INFO,
)
class TestVariableNamesDefined(Test):
    def run(self):
        for key in self.nc.variables.keys():
            if key not in VARIABLES:
                self._add_message(f"'{key}' is not defined in cloudnetpy-qc.")


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
    ignore_products=[Product.MODEL],
)
class TestLongNames(Test):
    def run(self):
        self._test_variable_attribute("long_name")


@test(
    "Standard names",
    "Check that variable have expected standard names.",
    ignore_products=[Product.MODEL],
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
                msg = utils.create_expected_received_msg(key, expected, received)
                self._add_message(msg)


@test("Global attributes", "Check that file contains required global attributes.")
class TestGlobalAttributes(Test):
    def run(self):
        nc_keys = self.nc.ncattrs()
        config_keys = self._read_config_keys("required_global_attributes")
        missing_keys = list(set(config_keys) - set(nc_keys))
        for key in missing_keys:
            self._add_message(f"'{key}' is missing.")


@test(
    "Median LWP",
    "Test that median of LWP values is within a reasonable range.",
    ErrorLevel.WARNING,
    [Product.MWR, Product.CATEGORIZE],
)
class TestMedianLwp(Test):
    def run(self):
        key = "lwp"
        if key not in self.nc.variables:
            self.severity = ErrorLevel.ERROR
            self._add_message(f"'{key}' is missing.")
            return
        limits = [-0.5, 10]
        median_lwp = ma.median(self.nc.variables[key][:]) / 1000  # g -> kg
        if median_lwp < limits[0] or median_lwp > limits[1]:
            msg = utils.create_out_of_bounds_msg(key, *limits, median_lwp)
            self._add_message(msg)


@test("Attribute outliers", "Find suspicious values in global attributes.")
class FindAttributeOutliers(Test):
    def run(self):
        for key, limits_str in METADATA_CONFIG.items("attribute_limits"):
            limits = [float(x) for x in limits_str.split(",")]
            if hasattr(self.nc, key):
                value = float(self.nc.getncattr(key))
                if value < limits[0] or value > limits[1]:
                    msg = utils.create_out_of_bounds_msg(key, *limits, value)
                    self._add_message(msg)


@test(
    "LDR values", "Test that LDR values are proper.", products=[Product.RADAR, Product.CATEGORIZE]
)
class TestLDR(Test):
    def run(self):
        if "ldr" in self.nc.variables:
            ldr = self.nc["ldr"][:]
            if ldr.mask.all():
                self._add_message("LDR exists but all the values are invalid.")


@test("Range correction", "Test that beta is range corrected.", products=[Product.LIDAR])
class TestIfRangeCorrected(Test):
    def run(self):
        try:
            range_var = self.nc["range"]
            beta_raw = self.nc["beta_raw"]
        except IndexError:
            return
        n_top_ranges = 200
        x = range_var[-n_top_ranges:] ** 2
        y = np.std(beta_raw[:, -n_top_ranges:], axis=0)
        res = scipy.stats.pearsonr(x, y)
        if res.statistic < 0.75:
            self._add_message("Data might not be range corrected.")


@test(
    "Instrument PID",
    "Test that valid instrument PID exists.",
    ErrorLevel.WARNING,
    [Product.MWR, Product.LIDAR, Product.RADAR, Product.DISDROMETER],
)
class TestInstrumentPid(Test):
    def run(self):
        key = "instrument_pid"
        try:
            pid = getattr(self.nc, key)
            if pid == "":
                self._add_message("Instrument PID is empty.")
        except AttributeError:
            self._add_message("Instrument PID is missing.")


# ---------------------#
# ------ Errors ------ #
# -------------------- #


@test(
    "Beta presence",
    "Test that one beta variable exists.",
    error_level=ErrorLevel.ERROR,
    products=[Product.LIDAR],
)
class TestLidarBeta(Test):
    def run(self):
        valid_keys = {"beta", "beta_1064", "beta_532", "beta_355"}
        for key in valid_keys:
            if key in self.nc.variables:
                return
        self._add_message("No valid beta variable found.")


@test("Time vector", "Test that time vector is continuous.", ErrorLevel.ERROR)
class TestTimeVector(Test):
    def run(self):
        time = self.nc["time"][:]
        try:
            n_time = len(time)
        except (TypeError, ValueError):
            self._add_message("Time vector is empty.")
            return
        if n_time == 0:
            self._add_message("Time vector is empty.")
            return
        if n_time == 1:
            self._add_message("One time step only.")
            return
        differences = np.diff(time)
        min_difference = np.min(differences)
        max_difference = np.max(differences)
        if min_difference <= 0:
            msg = utils.create_out_of_bounds_msg("time", 0, 24, min_difference)
            self._add_message(msg)
        if max_difference >= 24:
            msg = utils.create_out_of_bounds_msg("time", 0, 24, max_difference)
            self._add_message(msg)


@test("Variables", "Check that file contains required variables.", ErrorLevel.ERROR)
class TestVariableNames(Test):
    def run(self):
        keys_in_file = set(self.nc.variables.keys())
        required_keys = self._get_required_variable_names()
        missing_keys = list(required_keys - keys_in_file)
        for key in missing_keys:
            self._add_message(f"'{key}' is missing.")


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
                    self.severity = ErrorLevel.ERROR
                elif level == "WARN":
                    self.severity = ErrorLevel.WARNING
                else:
                    continue
                msg = utils.format_msg(error_msg)
                msg = f"Variable '{key}': {msg}"
                self._add_message(msg)
