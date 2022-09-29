"""cloudnetpy-qc tests."""
from os import path
from pathlib import Path
from typing import Optional

from cloudnetpy_qc import quality

SCRIPT_PATH = path.dirname(path.realpath(__file__))


def test_valid_file():
    filename = f"{SCRIPT_PATH}/data/20211129_juelich_hatpro.nc"
    check = Check(filename)
    check.errors()
    for test in check.tests:
        exps = test["exceptions"]
        assert exps if test["testId"] == "TestInstrumentPid" else not exps


def test_legacy_file():
    filename = f"{SCRIPT_PATH}/data/20120203_arm-maldives_classification.nc"
    check = Check(filename, file_type="classification")
    keys = [
        "TestLongNames",
        "TestStandardNames",
        "TestDataTypes",
        "TestGlobalAttributes",
        "TestDataCoverage",
        "TestVariableNames",
        "TestCFConvention",
    ]
    check.verify_exceptions(keys)


def test_missing_data():
    filename = f"{SCRIPT_PATH}/data/20220729_norunda_cl51.nc"
    check = Check(filename)
    check.verify_exceptions(["TestDataCoverage"])


def test_invalid_lwp():
    filename = f"{SCRIPT_PATH}/data/20220214_schneefernerhaus_hatpro.nc"
    check = Check(filename)
    check.verify_exceptions(["FindVariableOutliers"])


class Check:
    """Check class."""

    def __init__(self, filename: str, file_type: Optional[str] = None):
        self.report = quality.run_tests(Path(filename), cloudnet_file_type=file_type)
        self.tests = self.report["tests"]

    def verify_exceptions(self, keys: list):
        n = 0
        for test in self.tests:
            if test["testId"] in keys:
                assert test["exceptions"]
                n += 1
        assert n == len(keys)

    def errors(self, n_expected: int = 0):
        assert self._count("error") == n_expected

    def warnings(self, n_expected: int = 0):
        assert self._count("warning") == n_expected

    def _count(self, level: str):
        n = 0
        for test in self.report["tests"]:
            for exp in test["exceptions"]:
                if exp["result"] == level:
                    n += 1
        return n
