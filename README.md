# cloudnetpy-qc
CloudnetPy quality control

Installation
------------
```shell
$ pip3 install cloudnetpy_qc
```

Usage
-----
```python
from cloudnetpy_qc import Quality
quality = Quality('cloudnet-file.nc')
metadata_result = quality.check_metadata()
data_result = quality.check_data()
```