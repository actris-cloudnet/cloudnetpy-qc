# Changelog

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
