# CloudnetPy-QC

![](https://github.com/actris-cloudnet/cloudnetpy-qc/workflows/CloudnetPy-QC%20CI/badge.svg)

Software for evaluating quality of [ACTRIS-Cloudnet](https://cloudnet.fmi.fi) data products.

Installation
------------
```shell
$ pip3 install cloudnetpy-qc
```

Usage
-----
```python
import json
from pathlib import Path
from cloudnetpy_qc import quality
report = quality.run_tests(Path('cloudnet-file.nc'))
json_object = json.dumps(report, indent=2)
print(json_object)
```

## Format of the report
* `timestamp`: UTC timestamp of the test
* `qcVersion`: `cloudnetpy-qc` version
* `tests`: `Test[]`

### `Test`
* `testId`: Unique name of the test
* `description`: Free-form description of the test
* `exceptions`: `Exception[]`

### `Exception`
* `message`: Free-form message about the exception
* `result`: `"error"` or `"warning"`


### Example:

```json
{
  "timestamp": "2022-10-13T07:00:26.906815Z",
  "qcVersion": "1.1.2",
  "tests": [
    {
      "testId": "TestUnits",
      "description": "Test that unit attribute of variable matches expected value",
      "exceptions": []
    },
    {
      "testId": "TestInstrumentPid",
      "description": "Test that valid instrument PID exists",
      "exceptions": [
        {
          "message": "Instrument PID is missing.",
          "result": "warning"
        }
      ]
    },
    {
      "testId": "TestTimeVector",
      "description": "Test that time vector is continuous",
      "exceptions": []
    },
    {
      "testId": "TestVariableNames",
      "description": "Find missing variables",
      "exceptions": []
    },
    {
      "testId": "TestCFConvention",
      "description": "Test that file passes CF convention",
      "exceptions": []
    }
  ]
}
```

## License
MIT
