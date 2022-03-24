from os import path
from cloudnetpy_qc import Quality

SCRIPT_PATH = path.dirname(path.realpath(__file__))


def test_valid_file():
    filename = f'{SCRIPT_PATH}/data/20211129_juelich_hatpro.nc'
    check = Check(filename)
    check.check_metadata()
    check.check_data()


def test_invalid_lwp():
    filename = f'{SCRIPT_PATH}/data/20220215_schneefernerhaus_hatpro.nc'
    check = Check(filename)
    check.check_metadata()
    res = check.check_data(1)
    assert 'medianLwp' in res
    assert 'outOfBounds' in res


class Check:
    def __init__(self, filename: str):
        self.quality = Quality(filename)

    def check_metadata(self, n_failures: int = 0):
        self.quality.check_metadata()
        assert self.quality.n_metadata_test_failures == n_failures

    def check_data(self, n_failures: int = 0):
        res = self.quality.check_data()
        assert self.quality.n_data_test_failures == n_failures
        return res
