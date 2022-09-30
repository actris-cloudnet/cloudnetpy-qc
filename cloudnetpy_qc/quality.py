"""Cloudnet product quality checks."""
import dataclasses
import datetime
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

import netCDF4
import numpy as np
from cfchecker import cfchecks
from numpy import ma

from . import utils
from .utils import str2num
from .version import __version__

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

METADATA_CONFIG = utils.read_config(f"{FILE_PATH}/metadata_config.ini")
DATA_CONFIG = utils.read_config(f"{FILE_PATH}/data_quality_config.ini")


class Product(str, Enum):
    # Level 1b
    RADAR = "radar"
    LIDAR = "lidar"
    MWR = "mwr"
    DISDROMETER = "disdrometer"
    MODEL = "model"
    # Level 1c
    CATEGORIZE = "categorize"
    # Level 2
    CLASSIFICATION = "classification"
    IWC = "iwc"
    LWC = "lwc"
    DRIZZLE = "drizzle"
    # Experimental
    DER = "der"
    IER = "ier"


class ErrorLevel(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TestReport:
    testId: str
    description: str
    exceptions: List[dict]

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
    tests: List[Dict]


def run_tests(filename: Path, cloudnet_file_type: Optional[str] = None) -> dict:
    with netCDF4.Dataset(filename) as nc:
        cloudnet_file_type = (
            cloudnet_file_type if cloudnet_file_type is not None else nc.cloudnet_file_type
        )
        logging.debug(f"Filename: {filename.stem}")
        logging.debug(f"File type: {cloudnet_file_type}")
        test_reports: List[Dict] = []
        for cls in Test.__subclasses__():
            test_instance = cls(nc, filename, cloudnet_file_type)
            if cloudnet_file_type in test_instance.products:
                test_instance.run()
                for exception in test_instance.report.values()["exceptions"]:
                    assert exception["result"] in (
                        ErrorLevel.ERROR,
                        ErrorLevel.PASS,
                        ErrorLevel.WARNING,
                    )
                test_reports.append(test_instance.report.values())
    return FileReport(
        timestamp=f"{datetime.datetime.now().isoformat()}Z",
        qcVersion=__version__,
        tests=test_reports,
    ).__dict__


def test(
    description: str,
    error_level: Optional[ErrorLevel] = None,
    products: Optional[List[Product]] = None,
    ignore_products: Optional[List[Product]] = None,
):
    """Decorator for the tests."""

    def fun(cls):

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

    description: str
    severity = ErrorLevel.WARNING
    products: List[str] = [member.value for member in Product]  # All products by default

    def __init__(self, nc: netCDF4.Dataset, filename: Path, cloudnet_file_type: str):
        self.filename = filename
        self.nc = nc
        self.cloudnet_file_type = cloudnet_file_type
        self.report = TestReport(
            testId=self.__class__.__name__,
            description=self.description,
            exceptions=[],
        )

    def run(self):
        raise NotImplementedError

    def _test_variable_attribute(self, attribute: str):
        for key, expected in METADATA_CONFIG.items(attribute):
            if key in self.nc.variables:
                value = getattr(self.nc.variables[key], attribute, "")
                if value != expected:
                    msg = utils.create_expected_received_msg(key, expected, value)
                    self._add_message(msg)

    def _add_message(self, message: Union[str, list]):
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


# ---------------------- #
# ------ Warnings ------ #
# ---------------------- #


@test("Test that unit attribute of variable matches expected value")
class TestUnits(Test):
    def run(self):
        self._test_variable_attribute("units")


@test(
    "Test that long_name attribute of variable matches expected value",
    ignore_products=[Product.MODEL],
)
class TestLongNames(Test):
    def run(self):
        self._test_variable_attribute("long_name")


@test(
    "Test that standard_name attribute of variable matches CF convention",
    ignore_products=[Product.MODEL],
)
class TestStandardNames(Test):
    def run(self):
        self._test_variable_attribute("standard_name")


@test("Find invalid data types")
class TestDataTypes(Test):
    def run(self):
        for key in self.nc.variables:
            expected = "float32"
            received = self.nc.variables[key].dtype.name
            for config_key, custom_value in METADATA_CONFIG.items("data_types"):
                if config_key == key:
                    expected = custom_value
                    break
            if received != expected:
                if key == "time" and received in ("float32", "float64"):
                    continue
                msg = utils.create_expected_received_msg(key, expected, received)
                self._add_message(msg)


@test("Find missing global attributes")
class TestGlobalAttributes(Test):
    def run(self):
        nc_keys = self.nc.ncattrs()
        config_keys = self._read_config_keys("required_global_attributes")
        missing_keys = list(set(config_keys) - set(nc_keys))
        for key in missing_keys:
            self._add_message(f"'{key}' is missing.")


@test("Test median LWP value", ErrorLevel.WARNING, [Product.MWR, Product.CATEGORIZE])
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


@test("Find suspicious data values")
class FindVariableOutliers(Test):
    def run(self):
        for key, limits_str in DATA_CONFIG.items("limits"):
            limits = [str2num(x) for x in limits_str.split(",")]
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


@test("Find suspicious global attribute values")
class FindAttributeOutliers(Test):
    def run(self):
        for key, limits_str in METADATA_CONFIG.items("attribute_limits"):
            limits = [str2num(x) for x in limits_str.split(",")]
            if hasattr(self.nc, key):
                value = str2num(self.nc.getncattr(key))
                if value < limits[0] or value > limits[1]:
                    msg = utils.create_out_of_bounds_msg(key, *limits, value)
                    self._add_message(msg)


@test("Test that file contains data", ignore_products=[Product.MODEL])
class TestDataCoverage(Test):
    def run(self):
        grid = ma.array(np.linspace(0, 24, int(24 * (60 / 5)) + 1))
        time = self.nc["time"][:]
        bins_with_no_data = 0
        for ind, t in enumerate(grid[:-1]):
            ind2 = np.where((time > t) & (time <= grid[ind + 1]))[0]
            if len(ind2) == 0:
                bins_with_no_data += 1
        missing = bins_with_no_data / len(grid) * 100
        if missing > 10:
            self._add_message(f"{round(missing)}% of day's data is missing.")


@test("Test that LDR values are proper", products=[Product.RADAR, Product.CATEGORIZE])
class TestLDR(Test):
    def run(self):
        if "ldr" in self.nc.variables:
            ldr = self.nc["ldr"][:]
            if ldr.mask.all():
                self._add_message("LDR exists but all the values are invalid.")


@test("Test radar folding", products=[Product.RADAR, Product.CATEGORIZE])
class FindFolding(Test):
    def run(self):
        v_threshold = 8
        data = self.nc["v"][:]
        difference = np.abs(np.diff(data, axis=1))
        n_suspicious = ma.sum(difference > v_threshold)
        if n_suspicious > 20:
            self._add_message(f"{n_suspicious} suspicious range gates. Folding might be present.")


@test("Test if beta not range-corrected", products=[Product.LIDAR])
class TestIfRangeCorrected(Test):
    def run(self):
        try:
            data = self.nc["beta_raw"][:]
        except IndexError:
            return
        noise_threshold = 2e-6
        std_threshold = 1e-6
        noise_ind = np.where(data < noise_threshold)
        noise_std = float(np.std(data[noise_ind]))
        if noise_std < std_threshold:
            self._add_message(
                f"Suspiciously low noise std ({utils.format_value(noise_std)}). "
                f"Data might not be range-corrected."
            )


@test(
    "Test that valid instrument PID exists",
    ErrorLevel.WARNING,
    [Product.MWR, Product.LIDAR, Product.RADAR, Product.DISDROMETER],
)
class TestInstrumentPid(Test):
    def run(self):
        key = "instrument_pid"
        try:
            getattr(self.nc, key)
        except AttributeError:
            self._add_message("Instrument PID is missing.")


# ---------------------#
# ------ Errors ------ #
# -------------------- #


@test("Test that time vector is continuous", ErrorLevel.ERROR)
class TestTimeVector(Test):
    def run(self):
        time = self.nc["time"][:]
        if time.ndim == 1 and time.shape == (0,):
            self._add_message("Time vector is empty.")
            return
        if len(time) == 1:
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


@test("Find missing variables", ErrorLevel.ERROR)
class TestVariableNames(Test):
    def run(self):
        nc_keys = self.nc.variables.keys()
        config_keys = self._read_config_keys("required_variables")
        missing_keys = list(set(config_keys) - set(nc_keys))
        for key in missing_keys:
            self._add_message(f"'{key}' is missing.")


# ------------------------------#
# ------ Error / Warning ------ #
# ----------------------------- #


@test("Test that file passes CF convention")
class TestCFConvention(Test):
    def run(self):
        standard_names = "CF_STANDARD_NAMES_XML"
        area_types = "CF_AREA_TYPES_XML"
        region_names = "CF_REGION_NAMES_XML"
        cf_version = "1.8"
        env = os.environ
        if all(key in env for key in (standard_names, area_types, region_names)):
            inst = cfchecks.CFChecker(
                silent=True,
                version=cf_version,
                cfStandardNamesXML=env[standard_names],
                cfAreaTypesXML=env[area_types],
                cfRegionNamesXML=env[region_names],
            )
        else:
            inst = cfchecks.CFChecker(silent=True, version=cf_version)
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
