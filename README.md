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
from cloudnetpy_qc import quality
report = quality.run_tests('cloudnet-file.nc')
json_object = json.dumps(report, indent=2)
print(json_object)
```

## Format of the report
* `timestamp`: UTC timestamp of the test
* `qcVersion`: `cloudnetpy-qc` version
* `tests`: `Test[]`

### `Test`
* `testId`: Unique name of the test
* `exceptions`: `Exception[]`

### `Exception`
* `message`: Free-form message about the exception
* `result`: `"info"`, `"error"` or `"warning"`


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

## License
MIT
