# CloudnetPy-QC

![](https://github.com/actris-cloudnet/cloudnetpy-qc/workflows/CloudnetPy-QC%20CI/badge.svg)

CloudnetPy quality control

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
json_object = json.dumps(report, indent=4)
print(json_object)
```
