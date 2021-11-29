from os import path
from cloudnetpy_qc import Quality

SCRIPT_PATH = path.dirname(path.realpath(__file__))

filename = f'{SCRIPT_PATH}/data/20211129_juelich_hatpro.nc'

quality = Quality(filename)


def test_metadata():
    result = quality.check_metadata()
    assert quality.n_metadata_test_failures == 0, result


def test_data():
    result = quality.check_data()
    assert quality.n_data_test_failures == 0, result
