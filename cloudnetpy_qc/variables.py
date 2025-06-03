"""Variable definitions."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import Enum
from typing import Literal, NamedTuple

import netCDF4


class Product(Enum):
    # Level 1b
    RADAR = "radar"
    LIDAR = "lidar"
    MWR = "mwr"
    DISDROMETER = "disdrometer"
    MODEL = "model"
    WEATHER_STATION = "weather-station"
    DOPPLER_LIDAR = "doppler-lidar"
    DOPPLER_LIDAR_WIND = "doppler-lidar-wind"
    RAIN_RADAR = "rain-radar"
    RAIN_GAUGE = "rain-gauge"
    # Level 1c
    CATEGORIZE = "categorize"
    MWR_L1C = "mwr-l1c"
    CATEGORIZE_VOODOO = "categorize-voodoo"
    # Level 2
    CLASSIFICATION = "classification"
    CLASSIFICATION_VOODOO = "classification-voodoo"
    IWC = "iwc"
    LWC = "lwc"
    DER = "der"
    IER = "ier"
    DRIZZLE = "drizzle"
    MWR_SINGLE = "mwr-single"
    MWR_MULTI = "mwr-multi"
    EPSILON_LIDAR = "epsilon-lidar"
    # Level 3
    L3_CF = "l3-cf"
    L3_IWC = "l3-iwc"
    L3_LWC = "l3-lwc"
    CPR = "cpr-simulation"

    @classmethod
    def all(cls) -> set[Product]:
        return set(cls)


Level = Literal["1b", "1c", "2", "3"]

LEVELS: dict[Product, Level] = {
    Product.RADAR: "1b",
    Product.LIDAR: "1b",
    Product.MWR: "1b",
    Product.DISDROMETER: "1b",
    Product.MODEL: "1b",
    Product.WEATHER_STATION: "1b",
    Product.DOPPLER_LIDAR: "1b",
    Product.RAIN_GAUGE: "1b",
    Product.DOPPLER_LIDAR_WIND: "1c",
    Product.RAIN_RADAR: "1b",
    Product.CATEGORIZE: "1c",
    Product.CATEGORIZE_VOODOO: "1c",
    Product.MWR_L1C: "1c",
    Product.CLASSIFICATION: "2",
    Product.CLASSIFICATION_VOODOO: "2",
    Product.IWC: "2",
    Product.LWC: "2",
    Product.DER: "2",
    Product.IER: "2",
    Product.DRIZZLE: "2",
    Product.MWR_SINGLE: "2",
    Product.MWR_MULTI: "2",
    Product.EPSILON_LIDAR: "2",
    Product.L3_CF: "3",
    Product.L3_IWC: "3",
    Product.L3_LWC: "3",
    Product.CPR: "3",
}


class Dtype(str, Enum):
    FLOAT = "float32"
    DOUBLE = "float64"
    INT = "int32"
    SHORT = "int16"
    BYTE = "int8"


class Variable(NamedTuple):
    long_name: str
    comment: str | None = None
    units: str | Callable[[netCDF4.Dataset], str] | None = "1"
    dtype: str = Dtype.FLOAT
    standard_name: str | None = None
    required: Iterable[Product] | None = None


def time_units(nc: netCDF4.Dataset) -> str:
    return f"hours since {nc.year}-{nc.month}-{nc.day} 00:00:00 +00:00"


VARIABLES = {
    # -------------------------------
    # Required in RADAR Level 1b file
    # -------------------------------
    "radar_frequency": Variable(
        long_name="Radar transmit frequency",
        units="GHz",
        required=[Product.RADAR],
    ),
    "Zh": Variable(
        long_name="Radar reflectivity factor",
        units="dBZ",
        required=[
            Product.RADAR,
            Product.RAIN_RADAR,
        ],
    ),
    "nyquist_velocity": Variable(
        long_name="Nyquist velocity",
        units="m s-1",
        required=[Product.RADAR],
    ),
    # -------------------------------
    # Required in LIDAR Level 1b file
    # -------------------------------
    "wavelength": Variable(
        long_name="Laser wavelength",
        units="nm",
        required=[Product.LIDAR],
    ),
    "zenith_angle": Variable(
        long_name="Zenith angle",
        units="degree",
        standard_name="zenith_angle",
        required=[Product.LIDAR],
    ),
    # -------------------------------------
    # Required in DISDROMETER Level 1b file
    # -------------------------------------
    "radar_reflectivity": Variable(
        long_name="Equivalent radar reflectivity factor",
        units="dBZ",
        standard_name="equivalent_reflectivity_factor",
        required=[Product.DISDROMETER],
    ),
    "n_particles": Variable(
        long_name="Number of particles in time interval",
        dtype=Dtype.INT,
    ),
    # --------------------------------------------
    # Recommended in WEATHER STATION Level 1b file
    # --------------------------------------------
    "air_temperature": Variable(
        long_name="Air temperature",
        standard_name="air_temperature",
        units="K",
    ),
    "rainfall_amount": Variable(
        long_name="Rainfall amount",
        units="m",
        standard_name="thickness_of_rainfall_amount",
        comment="Cumulated precipitation since 00:00 UTC",
        required=[Product.RAIN_GAUGE],
    ),
    "precipitation_rate": Variable(
        long_name="Precipitation rate",
        units="m s-1",
        standard_name="lwe_precipitation_rate",
    ),
    "precipitation_amount": Variable(
        long_name="Precipitation amount",
        units="m",
        standard_name="lwe_thickness_of_precipitation_amount",
        comment="Cumulated precipitation since 00:00 UTC",
    ),
    "snowfall_amount": Variable(
        long_name="Snowfall amount",
        units="m",
        standard_name="thickness_of_snowfall_amount",
        comment="Cumulated snow since 00:00 UTC",
    ),
    # ------------------------------------
    # Required in RAIN RADAR Level 1b file
    # ------------------------------------
    "pia": Variable(
        long_name="Path integrated rain attenuation",
        units="dB",
        required=[Product.RAIN_RADAR],
    ),
    # ------------------------------------
    # Required in CATEGORIZE Level 1c file
    # ------------------------------------
    "lidar_wavelength": Variable(
        long_name="Laser wavelength",
        units="nm",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "insect_prob": Variable(
        long_name="Insect probability",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "uwind": Variable(
        long_name="Zonal wind",
        units="m s-1",
        required=[
            Product.MODEL,
            Product.CATEGORIZE,
            Product.CATEGORIZE_VOODOO,
            Product.DOPPLER_LIDAR_WIND,
        ],
    ),
    "uwind_raw": Variable(
        long_name="Non-screened zonal wind",
        units="m s-1",
    ),
    "vwind": Variable(
        long_name="Meridional wind",
        units="m s-1",
        required=[
            Product.MODEL,
            Product.CATEGORIZE,
            Product.CATEGORIZE_VOODOO,
            Product.DOPPLER_LIDAR_WIND,
        ],
    ),
    "vwind_raw": Variable(
        long_name="Non-screened meridional wind",
        units="m s-1",
    ),
    "wwind": Variable(
        long_name="Vertical wind",
        units="m s-1",
    ),
    "azimuth_offset": Variable(
        long_name="Azimuth offset of the instrument (positive clockwise from north)",
        units="degrees",
    ),
    "zenith_offset": Variable(
        long_name="Zenith offset of the instrument",
        units="degrees",
    ),
    "q": Variable(
        long_name="Specific humidity",
        units="1",
        required=[Product.MODEL, Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "rh": Variable(
        long_name="Relative humidity",
        units="1",
        required=[Product.MODEL],
    ),
    "Tw": Variable(
        long_name="Wet-bulb temperature",
        units="K",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "category_bits": Variable(
        long_name="Target categorization bits",
        dtype=Dtype.INT,
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "radar_liquid_atten": Variable(
        long_name="Two-way radar attenuation due to liquid water",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "radar_gas_atten": Variable(
        long_name="Two-way radar attenuation due to atmospheric gases",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "radar_rain_atten": Variable(
        long_name="Two-way radar attenuation due to rain",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "radar_melting_atten": Variable(
        long_name="Two-way radar attenuation due to melting ice",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "quality_bits": Variable(
        long_name="Data quality bits",
        dtype=Dtype.INT,
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "beta": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
        # Lidar has its own beta test
        required=[
            Product.CATEGORIZE,
            Product.CATEGORIZE_VOODOO,
            Product.DOPPLER_LIDAR,
        ],
    ),
    "beta_error": Variable(
        long_name="Error in attenuated backscatter coefficient",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "beta_bias": Variable(
        long_name="Bias in attenuated backscatter coefficient",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "v_sigma": Variable(
        long_name="Standard deviation of mean Doppler velocity",
        units="m s-1",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "Z": Variable(
        long_name="Radar reflectivity factor",
        units="dBZ",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "Z_bias": Variable(
        long_name="Bias in radar reflectivity factor",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "Z_error": Variable(
        long_name="Error in radar reflectivity factor",
        units="dB",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "Z_sensitivity": Variable(
        long_name="Minimum detectable radar reflectivity",
        units="dBZ",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "model_time": Variable(
        long_name="Model time UTC",
        units=time_units,
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    "model_height": Variable(
        long_name="Height of model variables above mean sea level",
        units="m",
        required=[Product.CATEGORIZE, Product.CATEGORIZE_VOODOO],
    ),
    # ---------------------------------------
    # Required in CLASSIFICATION Level 2 file
    # ---------------------------------------
    "target_classification": Variable(
        long_name="Target classification",
        required=[Product.CLASSIFICATION, Product.CLASSIFICATION_VOODOO],
        dtype=Dtype.INT,
    ),
    "detection_status": Variable(
        long_name="Radar and lidar detection status",
        required=[Product.CLASSIFICATION, Product.CLASSIFICATION_VOODOO],
        dtype=Dtype.INT,
    ),
    "cloud_base_height_amsl": Variable(
        long_name="Height of cloud base above mean sea level",
        units="m",
        required=[Product.CLASSIFICATION, Product.CLASSIFICATION_VOODOO],
    ),
    "cloud_top_height_amsl": Variable(
        long_name="Height of cloud top above mean sea level",
        units="m",
        required=[Product.CLASSIFICATION, Product.CLASSIFICATION_VOODOO],
    ),
    "cloud_base_height_agl": Variable(
        long_name="Height of cloud base above ground level",
        units="m",
        required=[Product.CLASSIFICATION, Product.CLASSIFICATION_VOODOO],
    ),
    "cloud_top_height_agl": Variable(
        long_name="Height of cloud top above ground level",
        units="m",
        required=[Product.CLASSIFICATION, Product.CLASSIFICATION_VOODOO],
    ),
    # ----------------------------
    # Required in LWC Level 2 file
    # ----------------------------
    "lwc": Variable(
        long_name="Liquid water content",
        units="kg m-3",
        required=[
            Product.LWC,
            Product.RAIN_RADAR,
        ],
    ),
    "lwc_error": Variable(
        long_name="Random error in liquid water content, one standard deviation",
        units="dB",
        required=[Product.LWC],
    ),
    "lwc_retrieval_status": Variable(
        long_name="Liquid water content retrieval status",
        dtype=Dtype.INT,
        required=[Product.LWC],
    ),
    # ----------------------------
    # Required in IWC Level 2 file
    # ----------------------------
    "iwc": Variable(
        long_name="Ice water content",
        units="kg m-3",
        required=[Product.IWC],
    ),
    "iwc_error": Variable(
        long_name="Random error in ice water content",
        units="dB",
        required=[Product.IWC],
    ),
    "iwc_bias": Variable(
        long_name="Possible bias in ice water content",
        units="dB",
        required=[Product.IWC],
    ),
    "iwc_sensitivity": Variable(
        long_name="Minimum detectable ice water content",
        units="kg m-3",
        required=[Product.IWC],
    ),
    "iwc_retrieval_status": Variable(
        long_name="Ice water content retrieval status",
        dtype=Dtype.INT,
        required=[Product.IWC],
    ),
    # Deprecated:
    "iwc_inc_rain": Variable(
        long_name="Ice water content including rain",
        units="kg m-3",
    ),
    # --------------------------------
    # Required in DRIZZLE Level 2 file
    # --------------------------------
    "Do": Variable(
        long_name="Drizzle median diameter",
        units="m",
        required=[Product.DRIZZLE],
    ),
    "mu": Variable(
        long_name="Drizzle droplet size distribution shape parameter",
        required=[Product.DRIZZLE],
    ),
    "S": Variable(
        long_name="Lidar backscatter-to-extinction ratio",
        units="sr",
        required=[Product.DRIZZLE],
    ),
    "beta_corr": Variable(
        long_name="Lidar backscatter correction factor",
        required=[Product.DRIZZLE],
    ),
    "drizzle_N": Variable(
        long_name="Drizzle number concentration",
        units="m-3",
        required=[Product.DRIZZLE],
    ),
    "drizzle_lwc": Variable(
        long_name="Drizzle liquid water content",
        units="kg m-3",
        required=[Product.DRIZZLE],
    ),
    "drizzle_lwf": Variable(
        long_name="Drizzle liquid water flux",
        units="kg m-2 s-1",
        required=[Product.DRIZZLE],
    ),
    "v_drizzle": Variable(
        long_name="Drizzle droplet fall velocity",
        units="m s-1",
        required=[Product.DRIZZLE],
    ),
    "v_air": Variable(
        long_name="Vertical air velocity",
        units="m s-1",
        required=[Product.DRIZZLE],
    ),
    "Do_error": Variable(
        units="dB",
        long_name="Random error in drizzle median diameter",
        required=[Product.DRIZZLE],
    ),
    "drizzle_lwc_error": Variable(
        units="dB",
        long_name="Random error in drizzle liquid water content",
        required=[Product.DRIZZLE],
    ),
    "drizzle_lwf_error": Variable(
        units="dB",
        long_name="Random error in drizzle liquid water flux",
        required=[Product.DRIZZLE],
    ),
    "S_error": Variable(
        long_name="Random error in lidar backscatter-to-extinction ratio",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "Do_bias": Variable(
        long_name="Possible bias in drizzle median diameter",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "drizzle_lwc_bias": Variable(
        long_name="Possible bias in drizzle liquid water content",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "drizzle_lwf_bias": Variable(
        long_name="Possible bias in drizzle liquid water flux",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "drizzle_N_error": Variable(
        long_name="Random error in drizzle number concentration",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "v_drizzle_error": Variable(
        long_name="Random error in drizzle droplet fall velocity",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "mu_error": Variable(
        long_name="Random error in drizzle droplet size distribution shape parameter",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "drizzle_N_bias": Variable(
        long_name="Possible bias in drizzle number concentration",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "v_drizzle_bias": Variable(
        long_name="Possible bias in drizzle droplet fall velocity",
        units="dB",
        required=[Product.DRIZZLE],
    ),
    "drizzle_retrieval_status": Variable(
        long_name="Drizzle parameter retrieval status",
        required=[Product.DRIZZLE],
        dtype=Dtype.INT,
    ),
    # ----------------------------
    # Required in IER Level 2 file
    # ----------------------------
    "ier": Variable(
        long_name="Ice effective radius",
        units="m",
        required=[Product.IER],
    ),
    "ier_error": Variable(
        long_name="Random error in ice effective radius",
        units="m",
        required=[Product.IER],
    ),
    "ier_retrieval_status": Variable(
        long_name="Ice effective radius retrieval status",
        dtype=Dtype.INT,
        required=[Product.IER],
    ),
    # Deprecated:
    "ier_inc_rain": Variable(
        long_name="Ice effective radius including rain",
        units="m",
    ),
    # ----------------------------
    # Required in DER Level 2 file
    # ----------------------------
    "der": Variable(
        long_name="Droplet effective radius",
        units="m",
        required=[Product.DER],
    ),
    "der_error": Variable(
        long_name="Absolute error in droplet effective radius",
        units="m",
        required=[Product.DER],
    ),
    "der_scaled": Variable(
        long_name="Droplet effective radius (scaled to LWP)",
        units="m",
        required=[Product.DER],
    ),
    "der_scaled_error": Variable(
        long_name="Absolute error in droplet effective radius (scaled to LWP)",
        units="m",
        required=[Product.DER],
    ),
    "N_scaled": Variable(
        long_name="Cloud droplet number concentration",
        required=[Product.DER],
    ),
    "der_retrieval_status": Variable(
        long_name="Droplet effective radius retrieval status",
        dtype=Dtype.INT,
        required=[Product.DER],
    ),
    # ------------------------
    # Required in MWR L1C file
    # ------------------------
    "frequency": Variable(
        long_name="Nominal centre frequency of microwave channels",
        units="GHz",
        standard_name="radiation_frequency",
        required=[Product.MWR_L1C],
    ),
    "receiver": Variable(
        long_name="Corresponding microwave receiver for each channel",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "bandwidth": Variable(
        long_name="Bandwidth of microwave channels",
        units="GHz",
        required=[Product.MWR_L1C],
    ),
    "sideband_IF_separation": Variable(
        long_name="Sideband IF separation",
        units="GHz",
        required=[Product.MWR_L1C],
    ),
    "freq_shift": Variable(
        long_name="Frequency shift of the microwave channels",
        units="GHz",
        required=[Product.MWR_L1C],
    ),
    "tb": Variable(
        long_name="Microwave brightness temperature",
        units="K",
        standard_name="brightness_temperature",
        required=[Product.MWR_L1C],
    ),
    "tb_spectrum": Variable(
        long_name="Retrieved brightness temperature spectrum",
        units="K",
    ),
    "receiver_nb": Variable(
        long_name="Microwave receiver number",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "met_quality_flag": Variable(
        long_name="Meteorological data quality flag",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "ir_beamwidth": Variable(
        long_name="Beam width of the infrared radiometer",
        units="degree",
    ),
    "n_sidebands": Variable(
        long_name="Number of sidebands",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "pointing_flag": Variable(
        long_name="Pointing flag",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "t_amb": Variable(
        long_name="Ambient target temperature",
        units="K",
        required=[Product.MWR_L1C],
    ),
    "t_rec": Variable(
        long_name="Receiver physical temperature",
        units="K",
        required=[Product.MWR_L1C],
    ),
    "t_sta": Variable(
        long_name="Receiver temperature stability",
        units="K",
        required=[Product.MWR_L1C],
    ),
    "quality_flag_status": Variable(
        long_name="Quality flag status",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "liquid_cloud_flag": Variable(
        long_name="Liquid cloud flag",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "liquid_cloud_flag_status": Variable(
        long_name="Liquid cloud flag status",
        dtype=Dtype.INT,
        required=[Product.MWR_L1C],
    ),
    "ir_wavelength": Variable(
        long_name="Wavelength of infrared channels",
        units="m",
    ),
    "ir_bandwidth": Variable(
        long_name="Bandwidth of infrared channels",
        units="m",
    ),
    "irt": Variable(
        long_name="Infrared brightness temperatures",
        units="K",
    ),
    "ir_azimuth_angle": Variable(
        long_name="Infrared sensor azimuth angle",
        units="degree",
    ),
    "ir_zenith_angle": Variable(
        long_name="Infrared sensor zenith angle",
        units="degree",
    ),
    # ---------------------------
    # Required in MWR SINGLE file
    # ---------------------------
    "iwv_quality_flag": Variable(
        long_name="Integrated water vapour quality flag",
        units="1",
        required=[Product.MWR_SINGLE],
        dtype=Dtype.INT,
    ),
    "iwv_quality_flag_status": Variable(
        long_name="Integrated water vapour quality flag status",
        units="1",
        required=[Product.MWR_SINGLE],
        dtype=Dtype.INT,
    ),
    "absolute_humidity_quality_flag": Variable(
        long_name="Absolute humidity quality flag",
        units="1",
        required=[Product.MWR_SINGLE],
        dtype=Dtype.INT,
    ),
    "absolute_humidity_quality_flag_status": Variable(
        long_name="Absolute humidity quality flag status",
        units="1",
        required=[Product.MWR_SINGLE],
        dtype=Dtype.INT,
    ),
    "lwp_quality_flag": Variable(
        long_name="Liquid water path quality flag",
        units="1",
        required=[Product.MWR_SINGLE],
        dtype=Dtype.INT,
    ),
    "lwp_quality_flag_status": Variable(
        long_name="Liquid water path quality flag status",
        units="1",
        required=[Product.MWR_SINGLE],
        dtype=Dtype.INT,
    ),
    "lwp_offset": Variable(
        long_name="Subtracted offset correction of liquid water path",
        units="kg m-2",
        required=[Product.MWR_SINGLE],
    ),
    "absolute_humidity": Variable(
        long_name="Absolute humidity",
        units="kg m-3",
        required=[Product.MWR_SINGLE],
    ),
    # ----------------------------------------
    # Required in MWR MULTI and MWR MULTI file
    # ----------------------------------------
    "potential_temperature": Variable(
        long_name="Potential temperature",
        units="K",
        required=[Product.MWR_MULTI],
    ),
    "equivalent_potential_temperature": Variable(
        long_name="Equivalent potential temperature",
        units="K",
        required=[Product.MWR_MULTI],
    ),
    "relative_humidity": Variable(
        long_name="Relative humidity",
        standard_name="relative_humidity",
        required=[Product.MWR_MULTI],
    ),
    "temperature_quality_flag": Variable(
        long_name="Temperature quality flag",
        units="1",
        required=[Product.MWR_MULTI],
        dtype=Dtype.INT,
    ),
    "temperature_quality_flag_status": Variable(
        long_name="Temperature quality flag status",
        units="1",
        required=[Product.MWR_MULTI],
        dtype=Dtype.INT,
    ),
    # ---------------------------------------
    # Required in cpr-simulation Level 3 file
    # ---------------------------------------
    "sat_ifov": Variable(
        long_name="Satellite instantaneous field of view",
        units="m",
        required=[Product.CPR],
    ),
    "sat_range_resolution": Variable(
        long_name="Satellite range resolution",
        units="m",
        required=[Product.CPR],
    ),
    "sat_along_track_resolution": Variable(
        long_name="Satellite along-track resolution",
        units="m",
        required=[Product.CPR],
    ),
    "ze": Variable(
        long_name="Radar reflectivity factor of input",
        units="dBZ",
        required=[Product.CPR],
    ),
    "vm": Variable(
        long_name="Mean Doppler velocity of input",
        units="m s-1",
        required=[Product.CPR],
    ),
    "ze_sat": Variable(
        long_name="Convolved and integrated radar reflectivity factor",
        units="dBZ",
        required=[Product.CPR],
    ),
    "vm_sat": Variable(
        long_name="Convolved and integrated mean Doppler velocity",
        units="m s-1",
        required=[Product.CPR],
    ),
    "vm_sat_vel": Variable(
        long_name=(
            "Convolved and integrated mean Doppler velocity with satellite motion error"
        ),
        units="m s-1",
        required=[Product.CPR],
    ),
    "vm_sat_noise": Variable(
        long_name=(
            "Convolved and integrated mean Doppler velocity "
            "with noise and satellite motion error"
        ),
        units="m s-1",
        required=[Product.CPR],
    ),
    "ze_sat_noise": Variable(
        long_name="Convolved and integrated radar reflectivity factor with noise",
        units="dBZ",
        required=[Product.CPR],
    ),
    "vm_sat_folded": Variable(
        long_name="Doppler velocity with noise, satellite motion error, and folding",
        units="m s-1",
        required=[Product.CPR],
    ),
    "nubf": Variable(
        long_name="Non-uniform beam filling",
        units="dBZ",
        required=[Product.CPR],
    ),
    "nubf_flag": Variable(
        long_name="Non-uniform beam filling flag",
        dtype=Dtype.INT,
        required=[Product.CPR],
    ),
    "ms_flag": Variable(
        long_name="Multiple scattering flag",
        dtype=Dtype.INT,
        required=[Product.CPR],
    ),
    "folding_flag": Variable(
        long_name="Folding flag",
        dtype=Dtype.INT,
        required=[Product.CPR],
    ),
    "along_track_sat": Variable(
        long_name="Along-track distance at satellite resolution",
        units="m",
        required=[Product.CPR],
    ),
    "along_track": Variable(
        long_name="Along-track distance",
        units="m",
        required=[Product.CPR],
    ),
    "mean_wind": Variable(
        long_name="Mean horizontal wind",
        units="m s-1",
        required=[Product.CPR],
    ),
    "height_sat": Variable(
        long_name="Height above mean sea level at satellite resolution",
        units="m",
        dtype=Dtype.FLOAT,
        required=[Product.CPR],
    ),
    # ----------------------------------------
    # Required in Epsilon (lidar)
    # ----------------------------------------
    "epsilon": Variable(
        long_name="Dissipation rate of turbulent kinetic energy",
        units="m2 s-3",
        required=[
            Product.EPSILON_LIDAR,
        ],
    ),
    "rolling_window_period": Variable(
        long_name="Rolling window period",
        units="s",
        required=[
            Product.EPSILON_LIDAR,
        ],
    ),
    # -------------------------
    # Required in several files
    # -------------------------
    "rainfall_rate": Variable(
        long_name="Rainfall rate",
        units="m s-1",
        standard_name="rainfall_rate",
        required=[
            Product.RAIN_GAUGE,
            Product.DISDROMETER,
            Product.RAIN_RADAR,
        ],
    ),
    "range": Variable(
        long_name="Range from instrument",
        units="m",
        required=[
            Product.RADAR,
            Product.LIDAR,
        ],
    ),
    "v": Variable(
        long_name="Doppler velocity",
        units="m s-1",
        required=[
            Product.RADAR,
            Product.CATEGORIZE,
            Product.CATEGORIZE_VOODOO,
            Product.DOPPLER_LIDAR,
            Product.RAIN_RADAR,
        ],
    ),
    "temperature": Variable(
        long_name="Temperature",
        units="K",
        required=[
            Product.MODEL,
            Product.CATEGORIZE,
            Product.CATEGORIZE_VOODOO,
            Product.MWR_MULTI,
        ],
    ),
    "pressure": Variable(
        long_name="Pressure",
        units="Pa",
        required=[
            Product.MODEL,
            Product.CATEGORIZE,
            Product.CATEGORIZE_VOODOO,
        ],
    ),
    "lwp": Variable(
        long_name="Liquid water path",
        units="kg m-2",
        standard_name="atmosphere_cloud_liquid_water_content",
        required=[
            Product.MWR,
            Product.LWC,
            Product.MWR_SINGLE,
        ],
    ),
    "lwp_error": Variable(
        long_name="Error in liquid water path",
        units="kg m-2",
        required=[Product.LWC],
    ),
    "height": Variable(
        long_name="Height above mean sea level",
        units="m",
        standard_name="height_above_mean_sea_level",
        required=Product.all()
        - {
            Product.MWR,
            Product.DISDROMETER,
            Product.WEATHER_STATION,
            Product.RAIN_GAUGE,
            Product.MWR_L1C,
            Product.L3_CF,
            Product.L3_IWC,
            Product.L3_LWC,
        },
    ),
    "time": Variable(
        long_name="Time UTC",
        units=time_units,
        standard_name="time",
        required=Product.all(),
    ),
    "altitude": Variable(
        long_name="Altitude of site",
        units="m",
        standard_name="altitude",
        required=Product.all()
        - {Product.MODEL, Product.L3_CF, Product.L3_IWC, Product.L3_LWC},
    ),
    "latitude": Variable(
        long_name="Latitude of site",
        units="degree_north",
        standard_name="latitude",
        required=Product.all(),
    ),
    "longitude": Variable(
        long_name="Longitude of site",
        units="degree_east",
        standard_name="longitude",
        required=Product.all(),
    ),
    # --------------------------------------------
    # Variables included in some of Level 1b files
    # --------------------------------------------
    "calibration_offset": Variable(
        long_name="Radar reflectivity calibration offset",
        units="dBZ",
    ),
    "range_offset": Variable(
        long_name="Radar range offset",
        units="m",
    ),
    "r_accum_RT": Variable(
        long_name="Real time accumulated rainfall",
        units="m",
    ),
    "r_accum_NRT": Variable(
        long_name="Near real time accumulated rainfall",
        units="m",
    ),
    "rainfall_rate_1min_total": Variable(
        long_name="Total precipitation rate",
        units="m s-1",
    ),
    "rainfall_rate_1min_solid": Variable(
        long_name="Solid precipitation rate",
        units="m s-1",
    ),
    "snowfall_rate": Variable(
        long_name="Snowfall rate",
        units="m s-1",
    ),
    "velocity": Variable(
        long_name="Center fall velocity of precipitation particles",
        units="m s-1",
    ),
    "velocity_spread": Variable(
        long_name="Width of velocity interval",
        units="m s-1",
    ),
    "velocity_bnds": Variable(
        long_name="Velocity bounds",
        units="m s-1",
    ),
    "diameter": Variable(
        long_name="Center diameter of precipitation particles",
        units="m",
    ),
    "diameter_spread": Variable(
        long_name="Width of diameter interval",
        units="m",
    ),
    "diameter_bnds": Variable(
        long_name="Diameter bounds",
        units="m",
    ),
    "synop_WaWa": Variable(
        long_name="Synop code WaWa",
        dtype=Dtype.INT,
    ),
    "interval": Variable(
        long_name="Length of measurement interval",
        units="s",
        dtype=Dtype.INT,
    ),
    "sig_laser": Variable(
        long_name="Signal amplitude of the laser strip",
        dtype=Dtype.INT,
    ),
    "T_sensor": Variable(
        long_name="Temperature in the sensor housing",
        units="K",
    ),
    "I_heating": Variable(
        long_name="Heating current",
        units="A",
    ),
    "kinetic_energy": Variable(
        long_name="Kinetic energy of the hydrometeors",
        units="J m-2 h-1",
    ),
    "V_power_supply": Variable(
        long_name="Power supply voltage",
        units="V",
    ),
    "V_sensor_supply": Variable(
        long_name="Sensor supply voltage",
        units="V",
    ),
    "state_sensor": Variable(
        long_name="State of the sensor",
        dtype=Dtype.INT,
    ),
    "error_code": Variable(
        long_name="Error code",
        dtype=Dtype.INT,
    ),
    "number_concentration": Variable(
        long_name="Number of particles per diameter class",
        units="m-3 mm-1",
    ),
    "fall_velocity": Variable(
        long_name="Average velocity of each diameter class",
        units="m s-1",
    ),
    "data_raw": Variable(
        long_name="Raw data as a function of particle diameter and velocity",
        units="1",
        dtype=Dtype.SHORT,
    ),
    "phi_cx": Variable(
        long_name="Co-cross-channel differential phase",
        units="rad",
    ),
    "rho_cx": Variable(
        long_name="Co-cross-channel correlation coefficient",
    ),
    "kurtosis": Variable(
        long_name="Kurtosis of spectra",
    ),
    "skewness": Variable(
        long_name="Skewness of spectra",
    ),
    "azimuth_angle": Variable(
        long_name="Azimuth angle",
        units="degree",
        standard_name="sensor_azimuth_angle",
    ),
    "beta_raw": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_cross_raw": Variable(
        long_name="Attenuated backscatter coefficient for the cross-polarised signal",
        units="sr-1 m-1",
    ),
    "beta_cross": Variable(
        long_name="Attenuated backscatter coefficient for the cross-polarised signal",
        units="sr-1 m-1",
    ),
    "iwv": Variable(
        long_name="Integrated water vapour",
        units="kg m-2",
        standard_name="atmosphere_mass_content_of_water_vapor",
    ),
    "ldr": Variable(
        long_name="Linear depolarisation ratio",
        units="dB",
    ),
    "sldr": Variable(
        long_name="Slanted linear depolarisation ratio",
        units="dB",
    ),
    "width": Variable(
        long_name="Spectral width",
        units="m s-1",
        required=[Product.RAIN_RADAR],
    ),
    "calibration_factor": Variable(
        long_name="Attenuated backscatter calibration factor",
    ),
    "beta_smooth": Variable(
        long_name="Attenuated backscatter coefficient", units="sr-1 m-1"
    ),
    "depolarisation": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "depolarisation_raw": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "file_code": Variable(
        long_name="File code",
        dtype=Dtype.INT,
    ),
    "program_number": Variable(
        long_name="Program number",
        dtype=Dtype.INT,
    ),
    "model_number": Variable(
        long_name="Model number",
        dtype=Dtype.INT,
    ),
    "antenna_separation": Variable(
        long_name="Antenna separation",
        units="m",
    ),
    "antenna_diameter": Variable(
        long_name="Antenna diameter",
        units="m",
    ),
    "antenna_gain": Variable(
        long_name="Antenna gain",
        units="dB",
    ),
    "half_power_beam_width": Variable(
        long_name="Half power beam width",
        units="degree",
    ),
    "dual_polarization": Variable(
        long_name="Dual polarisation type",
        dtype=Dtype.INT,
    ),
    "sample_duration": Variable(
        long_name="Sample duration",
        units="s",
    ),
    "calibration_interval": Variable(
        long_name="Calibration interval in samples",
        dtype=Dtype.INT,
    ),
    "number_of_spectral_samples": Variable(
        long_name="Number of spectral samples in each chirp sequence",
        dtype=Dtype.INT,
    ),
    "chirp_start_indices": Variable(
        long_name="Chirp sequences start indices",
        dtype=Dtype.INT,
    ),
    "number_of_averaged_chirps": Variable(
        long_name="Number of averaged chirps in sequence",
        dtype=Dtype.INT,
    ),
    "integration_time": Variable(
        long_name="Integration time",
        units="s",
    ),
    "range_resolution": Variable(
        long_name="Vertical resolution of range",
        units="m",
    ),
    "FFT_window": Variable(
        long_name="FFT window type",
        dtype=Dtype.INT,
    ),
    "input_voltage_range": Variable(
        long_name="ADC input voltage range (+/-)",
        units="mV",
        dtype=Dtype.INT,
    ),
    "noise_threshold": Variable(
        long_name="Noise filter threshold factor",
    ),
    "time_ms": Variable(
        long_name="Time ms",
        units="ms",
        dtype=Dtype.INT,
    ),
    "quality_flag": Variable(
        long_name="Quality flag",
        dtype=Dtype.INT,
    ),
    "pc_temperature": Variable(
        long_name="PC temperature",
        units="K",
    ),
    "receiver_temperature": Variable(
        long_name="Receiver temperature",
        units="K",
    ),
    "transmitter_temperature": Variable(
        long_name="Transmitter temperature",
        units="K",
    ),
    "transmitted_power": Variable(
        long_name="Transmitted power",
        units="W",
    ),
    "status_flag": Variable(
        long_name="Status flag for heater and blower",
    ),
    "air_pressure": Variable(
        long_name="Air pressure",
        units="Pa",
        standard_name="air_pressure",
    ),
    "wind_speed": Variable(
        long_name="Wind speed",
        standard_name="wind_speed",
        units="m s-1",
    ),
    "wind_direction": Variable(
        long_name="Wind direction",
        units="degree",
        standard_name="wind_from_direction",
    ),
    "voltage": Variable(
        long_name="Voltage",
        units="V",
    ),
    "brightness_temperature": Variable(
        long_name="Brightness temperature",
        units="K",
    ),
    "if_power": Variable(
        long_name="IF power at ACD",
        units="uW",
    ),
    "level": Variable(
        long_name="Model level",
        units=None,
        dtype=Dtype.SHORT,
    ),
    "flux_level": Variable(
        long_name="Model flux level",
        units=None,
        dtype=Dtype.SHORT,
    ),
    "sfc_categorical_snow": Variable(
        long_name="",
        dtype=Dtype.SHORT,
    ),
    "sfc_categorical_ice": Variable(
        long_name="",
        dtype=Dtype.SHORT,
    ),
    "sfc_categorical_freezing_rain": Variable(
        long_name="",
        dtype=Dtype.SHORT,
    ),
    "sfc_categorical_rain": Variable(
        long_name="",
        dtype=Dtype.SHORT,
    ),
    "sfc_albedo_sw_direct": Variable(
        long_name="Surface albedo (shortwave direct)",
        # standard_name="surface_albedo_shortwave_direct",
    ),
    "sfc_albedo_sw_diffuse": Variable(
        long_name="Surface albedo (shortwave diffuse)",
        # standard_name="surface_albedo_shortwave_diffuse",
    ),
    "sfc_albedo_lw_direct": Variable(
        long_name="Surface albedo (longwave direct)",
        # standard_name="surface_albedo_longwave_direct",
    ),
    "sfc_albedo_lw_diffuse": Variable(
        long_name="Surface albedo (longwave diffuse)",
        # standard_name="surface_albedo_longwave_diffuse",
    ),
    "nfft": Variable(
        long_name="Number of FFT points",
        dtype=Dtype.INT,
    ),
    "nave": Variable(
        long_name="Number of spectral averages (not accounting for overlapping FFTs)",
        dtype=Dtype.INT,
    ),
    "prf": Variable(
        long_name="Pulse Repetition Frequency",
        units="Hz",
        dtype=Dtype.INT,
    ),
    "rg0": Variable(
        long_name="Number of lowest range gates",
        dtype=Dtype.INT,
    ),
    "SNR": Variable(
        long_name="Signal-to-noise ratio",
        units="dB",
    ),
    "radar_pitch": Variable(
        long_name="Radar pitch angle",
        units="degree",
        standard_name="platform_roll",
    ),
    "radar_yaw": Variable(
        long_name="Radar yaw angle",
        units="degree",
        standard_name="platform_yaw",
    ),
    "radar_roll": Variable(
        long_name="Radar roll angle",
        units="degree",
        standard_name="platform_roll",
    ),
    "zdr": Variable(
        long_name="Differential reflectivity",
        units="dB",
    ),
    "rho_hv": Variable(
        long_name="Correlation coefficient",
    ),
    "phi_dp": Variable(
        long_name="Differential phase",
        units="rad",
    ),
    "srho_hv": Variable(
        long_name="Slanted correlation coefficient",
    ),
    "kdp": Variable(
        long_name="Specific differential phase shift",
        units="rad km-1",
    ),
    "differential_attenuation": Variable(
        long_name="Differential attenuation",
        units="dB km-1",
    ),
    "synop_WW": Variable(
        long_name="Synop code WW",
        dtype=Dtype.INT,
    ),
    "measurement_quality": Variable(
        long_name="Measurement quality",
        units="%",
        dtype=Dtype.INT,
    ),
    "status_laser": Variable(
        long_name="Status of laser",
        dtype=Dtype.INT,
    ),
    "static_signal": Variable(
        long_name="Static signal",
        dtype=Dtype.INT,
    ),
    "status_T_laser_analogue": Variable(
        long_name="Status of laser temperature (analogue)",
        dtype=Dtype.INT,
    ),
    "status_T_laser_digital": Variable(
        long_name="Status of laser temperature (digital)",
        dtype=Dtype.INT,
    ),
    "status_I_laser_analogue": Variable(
        long_name="Status of laser current (analogue)",
        dtype=Dtype.INT,
    ),
    "status_I_laser_digital": Variable(
        long_name="Status of laser current (digital)",
        dtype=Dtype.INT,
    ),
    "status_sensor_supply": Variable(
        long_name="Status of sensor supply",
        dtype=Dtype.INT,
    ),
    "status_laser_heating": Variable(
        long_name="Status of laser heating",
        dtype=Dtype.INT,
    ),
    "status_receiver_heating": Variable(
        long_name="Status of receiver heating",
        dtype=Dtype.INT,
    ),
    "status_temperature_sensor": Variable(
        long_name="Status of temperature sensor",
        dtype=Dtype.INT,
    ),
    "status_heating_supply": Variable(
        long_name="Status of heating supply",
        dtype=Dtype.INT,
    ),
    "status_heating_housing": Variable(
        long_name="Status of heating housing",
        dtype=Dtype.INT,
    ),
    "status_heating_heads": Variable(
        long_name="Status of heating heads",
        dtype=Dtype.INT,
    ),
    "status_heating_carriers": Variable(
        long_name="Status of heating carriers",
        dtype=Dtype.INT,
    ),
    "status_laser_power": Variable(
        long_name="Status of laser power",
        dtype=Dtype.INT,
    ),
    "T_interior": Variable(
        long_name="Interior temperature",
        units="K",
    ),
    "T_laser_driver": Variable(
        long_name="Temperature of laser driver",
        units="K",
    ),
    "T_ambient": Variable(
        long_name="Ambient temperature",
        units="K",
    ),
    "I_mean_laser": Variable(
        long_name="Mean value of laser current",
        units="mA",
    ),
    "V_control": Variable(
        long_name="Control voltage",
        units="mV",
        dtype=Dtype.INT,
    ),
    "V_optical_output": Variable(
        long_name="Voltage of optical control output",
        units="mV",
        dtype=Dtype.INT,
    ),
    "I_heating_laser_head": Variable(
        long_name="Laser head heating current",
        units="mA",
        dtype=Dtype.INT,
    ),
    "I_heating_receiver_head": Variable(
        long_name="Receiver head heating current",
        units="mA",
        dtype=Dtype.INT,
    ),
    "maximum_hail_diameter": Variable(
        long_name="Maximum hail diameter",
        units="mm",
    ),
    # rv-polarstern specific
    "beta_1064_raw": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_1064": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_532_raw": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_532": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_355_raw": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_355": Variable(
        long_name="Attenuated backscatter coefficient",
        units="sr-1 m-1",
    ),
    "beta_355_nr": Variable(
        long_name="Attenuated backscatter coefficient (near range)",
        units="sr-1 m-1",
    ),
    "beta_355_nr_raw": Variable(
        long_name="Attenuated backscatter coefficient (near range)",
        units="sr-1 m-1",
    ),
    "beta_532_nr": Variable(
        long_name="Attenuated backscatter coefficient (near range)",
        units="sr-1 m-1",
    ),
    "beta_532_nr_raw": Variable(
        long_name="Attenuated backscatter coefficient (near range)",
        units="sr-1 m-1",
    ),
    "calibration_factor_1064": Variable(
        long_name="Attenuated backscatter at 1064 calibration factor",
    ),
    "calibration_factor_532": Variable(
        long_name="Attenuated backscatter at 532 calibration factor",
    ),
    "calibration_factor_355": Variable(
        long_name="Attenuated backscatter at 355 calibration factor",
    ),
    "calibration_factor_355_nr": Variable(
        long_name="Attenuated backscatter at 355 near range calibration factor",
    ),
    "calibration_factor_532_nr": Variable(
        long_name="Attenuated backscatter at 532 near range calibration factor",
    ),
    "depolarisation_355_raw": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "depolarisation_355": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "depolarisation_532_raw": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "depolarisation_532": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "depolarisation_1064": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "depolarisation_1064_raw": Variable(
        long_name="Lidar volume linear depolarisation ratio",
    ),
    "snr_1064": Variable(
        long_name="Signal-to-Noise Ratio (1064 nm)",
    ),
    "snr_532": Variable(
        long_name="Signal-to-Noise Ratio (532 nm)",
    ),
    "snr_355": Variable(
        long_name="Signal-to-Noise Ratio (355 nm)",
    ),
    "snr_532_nr": Variable(
        long_name="Signal-to-Noise Ratio (532 nm near range)",
    ),
    "snr_355_nr": Variable(
        long_name="Signal-to-Noise Ratio (355 nm near range)",
    ),
    # rv-polarstern categorize specific
    "lidar_depolarisation": Variable(
        long_name="Calibrated volume depolarisation (532 nm)"
    ),
    "beamwidthV": Variable(
        long_name="Vertical angular beamwidth",
        units="degree",
    ),
    "beamwidthH": Variable(
        long_name="Horizontal angular beamwidth",
        units="degree",
    ),
    "rain_detected": Variable(long_name="Rain detected", dtype=Dtype.INT),
    "air_pressure_quality_flag": Variable(
        long_name="Air pressure quality flag",
        dtype=Dtype.BYTE,
    ),
    "air_temperature_quality_flag": Variable(
        long_name="Air temperature quality flag",
        dtype=Dtype.BYTE,
    ),
    "relative_humidity_quality_flag": Variable(
        long_name="Relative humidity quality flag",
        dtype=Dtype.BYTE,
    ),
    "wind_speed_quality_flag": Variable(
        long_name="Wind speed quality flag",
        dtype=Dtype.BYTE,
    ),
    "wind_direction_quality_flag": Variable(
        long_name="Wind direction quality flag",
        dtype=Dtype.BYTE,
    ),
    "rainfall_rate_quality_flag": Variable(
        long_name="Rainfall rate quality flag",
        dtype=Dtype.BYTE,
    ),
    "dew_point_temperature": Variable(
        long_name="Dew point temperature",
        dtype=Dtype.FLOAT,
        units="K",
    ),
    "dew_point_temperature_quality_flag": Variable(
        long_name="Dew point temperature quality flag",
        dtype=Dtype.BYTE,
    ),
    "wind_speed_gust": Variable(
        long_name="Wind speed gust",
        dtype=Dtype.FLOAT,
        units="m s-1",
    ),
    "wind_speed_gust_quality_flag": Variable(
        long_name="Wind speed gust quality flag",
        dtype=Dtype.BYTE,
    ),
    "visibility_quality_flag": Variable(
        long_name="Visibility quality flag",
        dtype=Dtype.BYTE,
    ),
    "elevation_angle": Variable(
        long_name="Sensor elevation angle",
        units="degree",
    ),
    "ir_elevation_angle": Variable(
        long_name="Infrared sensor elevation angle",
        units="degree",
    ),
    "liquid_prob": Variable(
        long_name="Liquid probability",
        required=[Product.CATEGORIZE_VOODOO],
    ),
    "polariser_bleed_through": Variable(
        long_name="Polariser bleed-through",
    ),
    "pulses_per_ray": Variable(long_name="Pulses per ray", units="1", dtype=Dtype.INT),
    "ray_accumulation_time": Variable(
        long_name="Ray accumulation time", units="s", dtype=Dtype.FLOAT
    ),
    "lifted_index": Variable(
        long_name="Lifted index",
    ),
    "ko_index": Variable(
        long_name="KO index",
    ),
    "total_totals": Variable(
        long_name="Total totals index",
    ),
    "k_index": Variable(
        long_name="K index",
    ),
    "showalter_index": Variable(
        long_name="Showalter index",
    ),
    "cape": Variable(
        long_name="Convective available potential energy",
    ),
    "stability_quality_flag": Variable(
        long_name="Quality flag for stability products",
        dtype=Dtype.INT,
    ),
    "stability_quality_flag_status": Variable(
        long_name="Quality flag status for stability products",
        dtype=Dtype.INT,
    ),
    "visibility": Variable(
        long_name="Meteorological optical range (MOR) visibility",
        units="m",
        standard_name="visibility_in_air",
        dtype=Dtype.INT,
    ),
    "snr_limit": Variable(
        long_name="SNR limit",
        units="dB",
        comment="SNR threshold used in data screening.",
        dtype=Dtype.FLOAT,
    ),
    "correction_bits": Variable(
        long_name="Correction bits",
        dtype=Dtype.INT,
    ),
}
