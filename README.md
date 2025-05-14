# CloudnetPy-QC

[![CloudnetPy-QC CI](https://github.com/actris-cloudnet/cloudnetpy-qc/actions/workflows/test.yml/badge.svg)](https://github.com/actris-cloudnet/cloudnetpy-qc/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/cloudnetpy-qc.svg)](https://badge.fury.io/py/cloudnetpy-qc)

Software for evaluating quality of [ACTRIS-Cloudnet](https://cloudnet.fmi.fi) data products.

## Installation

```shell
$ pip3 install cloudnetpy-qc
```

## Usage

```python
import json
from cloudnetpy_qc import quality
site_meta = {"latitude": 61.844, "longitude": 24.287, "altitude": 150}
report = quality.run_tests('cloudnet-file.nc', site_meta)
json_object = json.dumps(report.to_dict(), indent=2)
print(json_object)
```

## Format of the report

- `timestamp`: UTC timestamp of the test
- `qcVersion`: `cloudnetpy-qc` version
- `tests`: `Test[]`
- `data_coverage`: float

### `Test`

- `testId`: Unique name of the test
- `exceptions`: `Exception[]`

### `Exception`

- `message`: Free-form message about the exception
- `result`: `"info"`, `"error"` or `"warning"`

### Example:

```json
{
  "timestamp": "2022-10-13T07:00:26.906815Z",
  "qcVersion": "1.1.2",
  "tests": [
    {
      "testId": "TestUnits",
      "exceptions": []
    },
    {
      "testId": "TestInstrumentPid",
      "exceptions": [
        {
          "message": "Instrument PID is missing.",
          "result": "warning"
        }
      ]
    },
    {
      "testId": "TestTimeVector",
      "exceptions": []
    },
    {
      "testId": "TestVariableNames",
      "exceptions": []
    },
    {
      "testId": "TestCFConvention",
      "exceptions": []
    }
  ]
}
```

## Tests

| Test                        | Description                                                                             |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `FindAttributeOutliers`     | Find suspicious values in global attributes.                                            |
| `FindFolding`               | Test for radar folding.                                                                 |
| `FindVariableOutliers`      | Find suspicious data values.                                                            |
| `TestBrightnessTemperature` | Test that brightness temperature data are valid.                                        |
| `TestCFConvention`          | Test compliance with the CF metadata conventions.                                       |
| `TestComment`               | Check that variables have expected comments.                                            |
| `TestCoordinateVariables`   | Test dimensions of coordinate variables are correct.                                    |
| `TestCoordinates`           | Check that file coordinates match site coordinates.                                     |
| `TestDataCoverage`          | Test that file contains enough data.                                                    |
| `TestDataModel`             | Test netCDF data model.                                                                 |
| `TestDataTypes`             | Check that variables have expected data types.                                          |
| `TestFillValue`             | Test that fill value is explicitly set for variables with missing data.                 |
| `TestFloatingPointValues`   | Test for special floating-point values which may indicate problems with the processing. |
| `TestGlobalAttributes`      | Check that file contains required global attributes.                                    |
| `TestIfRangeCorrected`      | Test that beta is range corrected.                                                      |
| `TestInstrumentPid`         | Test that valid instrument PID exists.                                                  |
| `TestLDR`                   | Test that LDR values are proper.                                                        |
| `TestLidarBeta`             | Test that one beta variable exists.                                                     |
| `TestLongNames`             | Check that variables have expected long names.                                          |
| `TestMWRMultiTemperature`   | Test that temperature data are valid.                                                   |
| `TestMWRSingleLWP`          | Test that LWP data are valid.                                                           |
| `TestMask`                  | Test that data are not completely masked.                                               |
| `TestMedianLwp`             | Test that LWP data are valid.                                                           |
| `TestModelData`             | Test that model data are valid.                                                         |
| `TestRainfallConsistency`   | Test that precipitation rate and amount are consistent.                                 |
| `TestStandardNames`         | Check that variable have expected standard names.                                       |
| `TestTimeVector`            | Test that time vector is continuous.                                                    |
| `TestUnexpectedMask`        | Test if data contain unexpected masked values.                                          |
| `TestUnits`                 | Check that variables have expected units.                                               |
| `TestVariableNames`         | Check that file contains required variables.                                            |
| `TestVariableNamesDefined`  | Check that variables have expected names.                                               |

## License

MIT
