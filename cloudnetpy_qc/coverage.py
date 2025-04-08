import datetime

import netCDF4
import numpy as np

from cloudnetpy_qc.variables import Product

RESOLUTIONS = {
    Product.DISDROMETER: datetime.timedelta(minutes=1),
    Product.L3_CF: datetime.timedelta(hours=1),
    Product.L3_IWC: datetime.timedelta(hours=1),
    Product.L3_LWC: datetime.timedelta(hours=1),
    Product.MWR: datetime.timedelta(minutes=5),
    Product.MWR_MULTI: datetime.timedelta(minutes=30),
    Product.MWR_SINGLE: datetime.timedelta(minutes=5),
    Product.WEATHER_STATION: datetime.timedelta(minutes=10),
    Product.RAIN_GAUGE: datetime.timedelta(minutes=1),
    Product.DOPPLER_LIDAR_WIND: datetime.timedelta(hours=1.5),
}
DEFAULT_RESOLUTION = datetime.timedelta(seconds=30)


def data_coverage(
    nc: netCDF4.Dataset,
) -> tuple[float, datetime.timedelta, datetime.timedelta] | None:
    time = np.array(nc["time"][:])
    time_unit = datetime.timedelta(hours=1)
    try:
        n_time = len(time)
    except (TypeError, ValueError):
        return None
    if n_time < 2:
        return None
    if nc.cloudnet_file_type == "model":
        expected_res = _model_resolution(nc)
    else:
        product = Product(nc.cloudnet_file_type)
        expected_res = RESOLUTIONS.get(product, DEFAULT_RESOLUTION)
    duration = get_duration(nc)
    bins = max(1, duration // expected_res)
    hist, _ = np.histogram(time, bins=bins, range=(0, duration / time_unit))
    coverage = np.count_nonzero(hist > 0) / len(hist)
    actual_res = np.median(np.diff(time)) * time_unit
    return coverage, expected_res, actual_res


def _model_resolution(nc: netCDF4.Dataset) -> datetime.timedelta:
    source = nc.source.lower()
    if "gdas" in source or "ecmwf open" in source:
        return datetime.timedelta(hours=3)
    return datetime.timedelta(hours=1)


def get_duration(nc: netCDF4.Dataset) -> datetime.timedelta:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    if now.date() == _get_date(nc):
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        duration = now - midnight
    else:
        duration = datetime.timedelta(days=1)
    return duration


def _get_date(nc: netCDF4.Dataset) -> datetime.date:
    date_in_file = [int(getattr(nc, x)) for x in ("year", "month", "day")]
    return datetime.date(*date_in_file)
