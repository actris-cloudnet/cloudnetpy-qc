# Changelog

## 1.25.9 – 2025-06-03

- Add correction_bits

## 1.25.8 – 2025-05-14

- Add precipitation variables
- Update CF tables

## 1.25.7 – 2025-05-02

- Make temperature and relative humidity optional in mwr-single

## 1.25.6 – 2025-04-28

- Fix exception when generating coordinate test error message

## 1.25.5 – 2025-04-25

- Correctly calculate percentile of masked array

## 1.25.4 – 2025-04-16

- Make `air_pressure` optional variable

## 1.25.3 – 2025-04-15

- Support model files with multiple locations
- Log name of the test that raised an exception

## 1.25.2 – 2025-04-10

- Fix numpy array check

## 1.25.1 – 2025-04-10

- Support mobile sites in coordinate test
- Print stack trace if test raises an exception

## 1.25.0 – 2025-04-08

- Add public function for data coverage (#17)

## 1.24.3 – 2025-04-07

- Fix formatting of longitude over 180 in error message

## 1.24.2 – 2025-04-04

- Allow longitude range only from -180 to 180
- Fix number formatting in error message

## 1.24.1 – 2025-04-03

- Handle model products in coordinate test

## 1.24.0 – 2025-04-02

- Add test for coordinates
- Update CF tables

## 1.23.0 – 2025-03-31

- Add test for coordinate variables

## 1.22.0 – 2025-03-05

- Add epsilon-lidar product

## 1.21.0 – 2025-03-04

- Add data model test
- Add WindCube models
- Update CF tables

## 1.20.0 – 2025-02-11

- Add cpr-simulation variables

## 1.19.5 – 2025-02-03

- Add snr_limit variable

## 1.19.4 – 2025-01-29

- Add `zenith_offset` variable

## 1.19.3 – 2025-01-29

- Make rain variables optional in weather station

## 1.19.2 – 2025-01-27

- Make visibility not mandatory

## 1.19.1 – 2025-01-27

- Fix rainfall amount check

## 1.19.0 – 2025-01-27

- Add rainfall consistency test

## 1.18.6 – 2025-01-17

- Test comment and empty attributes

## 1.18.5 – 2025-01-14

- Add rain gauges
- Add model variables

## 1.18.4 – 2025-01-07

- Remove mask check from zenith and azimuth angles

## 1.18.3 – 2024-12-19

- Fix long names for MWR single and multi

## 1.18.2 – 2024-12-18

- Update long name of MWRpy product

## 1.18.1 – 2024-12-03

- Add MIRA-10

## 1.18.0 – 2024-12-03

- Add windcube
- Add LPM
- Add test for unexpected mask
- Fix empty data check in outlier test

## 1.17.23 – 2024-11-19

- Use flags when checking mwrpy data limits

## 1.17.22 – 2024-11-19

- Add new mwrpy variables
- Increase relative humidity upper limit to 105%

## 1.17.21 – 2024-11-15

- Allow lower MWR time resolution

## 1.17.20 – 2024-11-14

- Add VOODOO products

## 1.17.19 – 2024-10-07

- Support `ecmwf-open` model

## 1.17.18 – 2024-09-25

- Specify pressure limits by altitude
- Remove `ier_inc_rain` and `iwc_inc_rain` from required variables
- Add `radar_rain_atten` and `radar_melting_atten` variables

## 1.17.17 – 2024-08-23

- Add beta cross channel to doppler lidar stare depol product

## 1.17.16 – 2024-08-21

- Adjust mwrpy tests

## 1.17.15 – 2024-08-21

- Add mwrpy tests

## 1.17.14 – 2024-08-20

- Make missing LWP in categorize an warning

## 1.17.13 – 2024-08-02

- Increase allowed gap for `mwr-multi`

## 1.17.12 – 2024-07-31

- Use space as thousand separator

## 1.17.11 – 2024-07-30

- Update limits for weather station variables

## 1.17.10 – 2024-07-03

- Add azimuth offset

## 1.17.9 – 2024-06-07

- Consider models "CHM 15k" and "CHM 15k-x" equal

## 1.17.8 – 2024-05-29

- Check hour 24 exists in model

## 1.17.7 – 2024-05-10

- Fix attribute validation of mwr-single and mwr-multi

## 1.17.6 – 2024-05-10

- Fix typo

## 1.17.5 – 2024-05-06

- List tests in README.md
- Remove non-screened wind from required doppler lidar wind variables

## 1.17.4 – 2024-04-18

- Make `n_particles` optional

## 1.17.3 – 2024-04-17

- Fix more data types

## 1.17.2 – 2024-04-17

- Fix data types of Thies variables

## 1.17.1 – 2024-03-26

- Fix PID test for RPG-FMCW-35

## 1.17.0 – 2024-03-21

- Add fill value test

## 1.16.3 – 2024-03-06

- Update instrument vocabulary links

## 1.16.2 – 2024-02-29

- Add `liquid_prob` variable

## 1.16.1 – 2024-02-23

- Add elevation angles

## 1.16.0 – 2024-02-15

- Add doppler-lidar-wind product

## 1.15.8 – 2024-02-14

- Return error from failing tests
- Improve PID test output

## 1.15.7 – 2024-01-30

- Support Lindenberg weather station
- Fix visibility `long_name`

## 1.15.6 – 2024-01-18

- Add `rain_detected`

## 1.15.5 – 2024-01-09

- Handle request errors in instrument PID test

## 1.15.4 – 2023-12-13

- Define mwr-single and mwr-multi variables

## 1.15.3 – 2023-11-22

- Make `rainfall_rate` optional in categorize file

## 1.15.2 – 2023-11-22

- Fix typo in product definition

## 1.15.1 – 2023-11-21

- Fix vocabulary links

## 1.15.0 – 2023-11-17

- Refactor types
- Fix vocabulary links of RAL instruments

## 1.14.6 – 2023-11-08

- Make `ir_beamwidth` variable optional

## 1.14.5 – 2023-10-26

- Simplify output from model data test

## 1.14.4 – 2023-10-25

- Handle missing variables in model data test

## 1.14.3 – 2023-10-23

- Check if radar data is completely masked

## 1.14.2 – 2023-10-19

- Add check for masked model profiles

## 1.14.1 – 2023-10-12

- Fix data coverage test with single timestamp

## 1.14.0 – 2023-10-11

- Check L3 products

## 1.13.8 – 2023-09-29

- Adjust Copernicus variables

## 1.13.7 – 2023-09-28

- Test relative amount of masked lwp data points

## 1.13.6 – 2023-09-26

- Avoid division by zero

## 1.13.5 – 2023-09-26

- Improve bad-LDR test

## 1.13.4 – 2023-09-25

- Filter outliers in range correction test

## 1.13.3 – 2023-09-22

- Improve range correction test for CT25K and PollyXT

## 1.13.2 – 2023-09-20

- Adjust HATPRO stare resolutions
- Add `calibration_offset` to optional variables
- Allow `pid` as optional global attribute

## 1.13.1 – 2023-09-19

- Fix data coverage test

## 1.13.0 – 2023-09-19

- Add test for floating-point values
- Test global attributes by product

## 1.12.1 – 2023-09-18

- Fix global attribute test

## 1.12.0 – 2023-09-18

- Set expected resolution of disdrometer to 1 min
- Improve global attribute tests

## 1.11.2 – 2023-09-12

- Add support for MRR-PRO

## 1.11.1 – 2023-08-21

- Fix data coverage test on file with little data

## 1.11.0 – 2023-08-18

- Test if data matches the expected resolution
- Support HALO serial number format

## 1.10.8 – 2023-08-11

- Add `tb_spectrum`
- Fix URL names

## 1.10.7 – 2023-05-26

- Handle missing value in instrument PID test

## 1.10.6 – 2023-05-17

- Re-release package

## 1.10.5 – 2023-05-17

- Update CF standard name table

## 1.10.4 – 2023-05-17

- Allow sparser sampling resolution with mwr-multi

## 1.10.3 – 2023-05-11

- Ignore zenith angle check for mwrpy files
- Check `time` and `model_time` units

## 1.10.2 – 2023-05-09

- Skip time vector data type test

## 1.10.1 – 2023-05-09

- Update `lwp` limits

## 1.10.0 – 2023-05-09

- Add mwrpy variables
- Change `lwp` unit to `kg m-2`

## 1.9.5 – 2023-05-08

- Set HTTP timeout

## 1.9.4 – 2023-05-08

- Extend instrument PID test

## 1.9.3 – 2023-05-05

- Specify `data_raw` units and dtype

## 1.9.2 – 2023-05-04

- Add snowfall rate

## 1.9.1 – 2023-04-25

- Increase range correction threshold

## 1.9.0 – 2023-04-14

- Add doppler lidar tests

## 1.8.1 – 2023-04-06

- Fix exception type in range correction test

## 1.8.0 – 2023-04-06

- Make range correction test more robust

## 1.7.2 – 2023-03-10

- Add `galileo` specific variables

## 1.7.1 – 2023-03-03

- Add more parsivel specifications

## 1.7.0 – 2023-02-28

- Change `rain_rate` to `rainfall_rate`

## 1.6.1 – 2023-02-28

- Harmonize degree unit
- Add standard name to `wind_direction`

## 1.6.0 – 2023-02-27

- Add weather-station
- Add py.typed
- Update CF tables
- Add script for updating CF tables
- Move data files to own directory

## 1.5.2 – 2023-02-01

- Add `lidar_depolarisation` definition

## 1.5.1 – 2023-01-26

- Add more rv-polarstern `long_names`

## 1.5.0 – 2023-01-12

- Add rv-polarstern variables
- Allow several options for lidar beta
- Fix copyright
- Update `setup-python`

## 1.4.2 – 2022-12-20

- Update `ier` units

## 1.4.1 – 2022-12-01

- Use datetime.timezone

## 1.4.0 – 2022-11-30

- Add thies variables
- Adjust disdrometer variables

## 1.3.2 – 2022-11-29

- Add more variables

## 1.3.1 – 2022-11-29

- Adjust data coverage test for real time processing

## 1.3.0 – 2022-11-29

- Add `info` error level
- Define expected variables in variables.py
- Update Python to 3.10

## 1.2.1 – 2022-11-04

- Embed XML files to Python package

## 1.2.0 – 2022-10-24

- Add human-readable test names
- Add height to required model variables

## 1.1.2 – 2022-10-07

- Add sldr `long_name` and unit

## 1.1.1 – 2022-10-04

- Change import location

## 1.1.0 – 2022-10-04

- Add option to ignore tests

## 1.0.8 – 2022-10-04

- Test for empty instrument PID

## 1.0.7 – 2022-10-01

- Make checks more robust

## 1.0.6 – 2022-09-30

- Make checks more robust

## 1.0.5 – 2022-09-30

- Fix testing of scalar time vector
- Add fallback behaviour if local cf convention xml files are missing

## 1.0.4 – 2022-09-29

- Read cf tables from local files

## 1.0.3 – 2022-09-29

- Add `ignore_products` option

## 1.0.2 – 2022-09-29

- Remove model from `standard_name` check

## 1.0.1 – 2022-09-29

- Add IER and DER products

## 1.0.0 – 2022-09-29

- Implement three level QC (pass, warning, error)
- Add standard name for IWV

## 0.2.0 – 2022-08-17

- Adjust zenith angle limits
- Fix azimuth angle

## 0.1.12 – 2022-08-11

- Check iwv unit and long name

## 0.1.11 – 2022-06-06

- Check units and long names of rainfall variables

## 0.1.10 – 2022-05-24

- Add ier and der units

## 0.1.9 – 2022-05-23

- Add ier variables to tests

## 0.1.8 – 2022-05-20

- Add `ier_retrieval_status` data type check

## 0.1.7 – 2022-05-20

- Add initial required variables for ier

## 0.1.6 – 2022-05-19

- Test `drizzle_retrieval_status` data type

## 0.1.5 – 2022-05-19

- Add der product

## 0.1.4 – 2022-03-24

- Fix median lwp test

## 0.1.3 – 2022-03-24

- Use ma.median

## 0.1.2 – 2022-03-24

- Add missing return

## 0.1.1 – 2022-03-24

- Run lwp test

## 0.1.0 – 2022-03-24

- Test for median LWP

## 0.0.19 – 2022-03-12

- Initial set of quality and metadata tests
