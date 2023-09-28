# Changelog

## 1.13.7 - 2023-09-28

- Test relative amount of masked lwp data points

## 1.13.6 - 2023-09-26

- Avoid division by zero

## 1.13.5 - 2023-09-26

- Improve bad-LDR test

## 1.13.4 - 2023-09-25

- Filter outliers in range correction test

## 1.13.3 - 2023-09-22

- Improve range correction test for CT25K and PollyXT

## 1.13.2 - 2023-09-20

- Adjust HATPRO stare resolutions
- Add `calibration_offset` to optional variables
- Allow `pid` as optional global attribute

## 1.13.1 - 2023-09-19

- Fix data coverage test

## 1.13.0 - 2023-09-19

- Add test for floating-point values
- Test global attributes by product

## 1.12.1 - 2023-09-18

- Fix global attribute test

## 1.12.0 - 2023-09-18

- Set expected resolution of disdrometer to 1 min
- Improve global attribute tests

## 1.11.2 - 2023-09-12

- Add support for MRR-PRO

## 1.11.1 - 2023-08-21

- Fix data coverage test on file with little data

## 1.11.0 - 2023-08-18

- Test if data matches the expected resolution
- Support HALO serial number format

## 1.10.8 - 2023-08-11

- Add `tb_spectrum`
- Fix URL names

## 1.10.7 - 2023-05-26

- Handle missing value in instrument PID test

## 1.10.6 - 2023-05-17

- Re-release package

## 1.10.5 - 2023-05-17

- Update CF standard name table

## 1.10.4 - 2023-05-17

- Allow sparser sampling resolution with mwr-multi

## 1.10.3 - 2023-05-11

- Ignore zenith angle check for mwrpy files
- Check `time` and `model_time` units

## 1.10.2 - 2023-05-09

- Skip time vector data type test

## 1.10.1 - 2023-05-09

- Update `lwp` limits

## 1.10.0 - 2023-05-09

- Add mwrpy variables
- Change `lwp` unit to `kg m-2`

## 1.9.5 - 2023-05-08

- Set HTTP timeout

## 1.9.4 - 2023-05-08

- Extend instrument PID test

## 1.9.3 - 2023-05-05

- Specify `data_raw` units and dtype

## 1.9.2 - 2023-05-04

- Add snowfall rate

## 1.9.1 - 2023-04-25

- Increase range correction threshold

## 1.9.0 - 2023-04-14

- Add doppler lidar tests

## 1.8.1 - 2023-04-06

- Fix exception type in range correction test

## 1.8.0 - 2023-04-06

- Make range correction test more robust

## 1.7.2 - 2023-03-10

- Add `galileo` specific variables

## 1.7.1 - 2023-03-03

- Add more parsivel specifications

## 1.7.0 - 2023-02-28

- Change rain_rate to rainfall_rate

## 1.6.1 - 2023-02-28

- Harmonize degree unit
- Add standard name to wind_direction

## 1.6.0 - 2023-02-27

- Add weather-station
- Add py.typed
- Update CF tables
- Add script for updating CF tables
- Move data files to own directory

## 1.5.2 - 2023-02-01

- Add `lidar_depolarisation` definition

## 1.5.1 - 2023-01-26

- Add more rv-polarstern long_names

## 1.5.0 - 2023-01-12

- Add rv-polarstern varibles
- Allow several options for lidar beta
- Fix copyright
- Update `setup-python`

## 1.4.2 - 2022-12-20

- Update `ier` units

## 1.4.1 - 2022-12-01

- Use datetime.timezone

## 1.4.0 - 2022-11-30

- Add thies variables
- Adjust disdrometer variables

## 1.3.2 - 2022-11-29

- Add more variables

## 1.3.1 - 2022-11-29

- Adjust data coverage test for real time processing

## 1.3.0 - 2022-11-29

- Add `info` error level
- Define expected variables in variables.py
- Update Python to 3.10

## 1.2.1 - 2022-11-04

- Embed XML files to Python package

## 1.2.0 - 2022-10-24

- Add human-readable test names
- Add height to required model variables

## 1.1.2 - 2022-10-07

- Add sldr long_name and unit

## 1.1.1 - 2022-10-04

- Change import location

## 1.1.0 - 2022-10-04

- Add option to ignore tests

## 1.0.8 - 2022-10-04

- Test for empty instrument PID

## 1.0.7 - 2022-10-01

- Make checks more robust

## 1.0.6 - 2022-09-30

- Make checks more robust

## 1.0.5 - 2022-09-30

- Fix testing of scalar time vector
- Add fallback behaviour if local cf convention xml files are missing

## 1.0.4 - 2022-09-29

- Read cf tables from local files

## 1.0.3 - 2022-09-29

- Add ignore_products option

## 1.0.2 - 2022-09-29

- Remove model from standard_name check

## 1.0.1 - 2022-09-29

- Add IER and DER products

## 1.0.0 - 2022-09-29

- Implement three level QC (pass, warning, error)
- Add standard name for IWV

## 0.2.0 - 2022-08-17

- Adjust zenith angle limits
- Fix azimuth angle

## 0.1.12 - 2022-08-11

- Check iwv unit and long name

## 0.1.11 - 2022-06-06

- Check units and long names of rainfall variables

## 0.1.10 - 2022-05-24

- Add ier and der units

## 0.1.9 - 2022-05-23

- Add ier variables to tests

## 0.1.8 - 2022-05-20

- Add ier_retrieval_status data type check

## 0.1.7 - 2022-05-20

- Add initial required variables for ier

## 0.1.6 - 2022-05-19

- Test drizzle_retrieval_status data type

## 0.1.5 - 2022-05-19

- Add der product

## 0.1.4 - 2022-03-24

- Fix median lwp test

## 0.1.3 - 2022-03-24

- Use ma.median

## 0.1.2 - 2022-03-24

- Add missing return

## 0.1.1 - 2022-03-24

- Run lwp test

## 0.1.0 - 2022-03-24

- Test for median LWP

## 0.0.19 - 2022-03-12

- Initial set of quality and metadata tests
