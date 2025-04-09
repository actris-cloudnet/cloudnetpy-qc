"""Helper functions."""

import configparser
import re
from functools import lru_cache

import numpy as np
import numpy.typing as npt
import requests

PID_FORMAT = r"https?://hdl\.handle\.net/(.+)"


def read_config(filename: str) -> configparser.ConfigParser:
    conf = configparser.ConfigParser()
    conf.optionxform = str  # type: ignore
    conf.read(filename)
    return conf


def format_msg(msg_in: str | list) -> str:
    msg = msg_in[0] if isinstance(msg_in, list) else msg_in
    if not msg.endswith("."):
        msg += "."
    x = re.search("^\\(.+\\):", msg)
    if x:
        msg = msg[x.end() :]
    msg = re.sub(" +", " ", msg)
    msg = msg.strip()
    msg = msg[0].capitalize() + msg[1:]
    return msg


def format_list(values: list[str], conj: str) -> str:
    if len(values) == 0:
        return ""
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + f" {conj} " + values[-1]


def create_expected_received_msg(
    expected: str | list[str],
    received: str,
    variable: str | None = None,
) -> str:
    if isinstance(expected, str):
        expected = [expected]
    expected = format_list([f"'{var}'" for var in expected], "or")
    msg = f"Expected {expected} but received '{received}'"
    if variable is not None:
        return f"{msg} with variable '{variable}'"
    return msg


def create_out_of_bounds_msg(
    variable: str,
    lower_limit: str | int | float,
    upper_limit: str | int | float,
    value: str | int | float,
) -> str:
    return (
        f"Value {format_value(value)} exceeds expected limits "
        f"{format_value(lower_limit)} ... {format_value(upper_limit)} "
        f"with variable '{variable}'"
    )


def format_value(value: str | int | float) -> str:
    return f"{float(value):,g}".replace(",", "\u202f")


@lru_cache
def fetch_pid(pid: str) -> dict:
    match = re.fullmatch(PID_FORMAT, pid)
    if match is None:
        raise ValueError("Invalid PID format")
    url = "https://hdl.handle.net/api/handles/" + match[1]
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    return res.json()


def integer_ranges(ints: list[int]) -> list[str]:
    """Convert given integers to list of ranges.

    >>> integer_ranges([1,2,3,5,7,8,9])
    ['1–3', '5', '7–9']
    """
    if len(ints) == 0:
        return []
    ints = sorted(ints)
    output = [[ints[0], ints[0]]]
    for x in ints[1:]:
        if x == output[-1][1] + 1:
            output[-1][1] = x
        else:
            output.append([x, x])
    return [str(a) if a == b else f"{a}–{b}" for a, b in output]


def calc_pressure(altitude: float) -> float:
    """Calculate atmospheric pressure in International Standard Atmosphere.

    Args:
        altitude: Geopotential altitude above mean sea level (m)

    Returns:
        Atmospheric pressure (Pa)
    """
    if np.any(altitude >= 11_000):
        raise NotImplementedError("Implemented only up to 11 km")
    P0 = 101_325  # Standard atmospheric pressure at sea level (Pa)
    T0 = 288.15  # Standard temperature at sea level (K)
    L = 0.0065  # Temperature lapse rate (K m-1)
    g = 9.80665  # Gravitational acceleration (m s-2)
    R = 287.0528  # Specific gas constant (J kg-1 K-1)
    return P0 * (1 - L * altitude / T0) ** (g / (R * L))


def haversine(
    lat1: float | npt.ArrayLike,
    lon1: float | npt.ArrayLike,
    lat2: float | npt.ArrayLike,
    lon2: float | npt.ArrayLike,
) -> npt.NDArray:
    """Calculate the great-circle distance between coordinates on Earth.

    Returns:
        Distance in kilometers.
    """
    r = 6371  # Radius of Earth (km)

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def find_closest(x: npt.NDArray, x_new: npt.NDArray) -> npt.NDArray[np.intp]:
    """Find the closest values between two arrays.

    Args:
        x: Sorted array.
        x_new: Sorted array.

    Returns:
        Indices into `x` which correspond to the closest values in `x_new`.

    Example:
        >>> x = np.array([0.9, 1.2, 2.0, 2.1])
        >>> x_new = np.array([1, 2])
        >>> find_closest(x, x_new)
        array([0, 2])
    """
    idx = np.searchsorted(x, x_new)
    idx_left = np.clip(idx - 1, 0, len(x) - 1)
    idx_right = np.clip(idx, 0, len(x) - 1)
    diff_left = np.abs(x_new - x[idx_left])
    diff_right = np.abs(x_new - x[idx_right])
    return np.where(diff_left < diff_right, idx_left, idx_right)


def average_coordinate(
    latitude: npt.NDArray, longitude: npt.NDArray
) -> tuple[float, float]:
    """Calculate average position from given coordinates.

    Args:
        latitude: Array of latitudes.
        longitude: Array of longitudes.

    Returns:
        Tuple of average latitude and longitude.
    """
    if latitude.size == longitude.size == 1:
        return latitude[0], longitude[0]
    latitude = np.radians(latitude)
    longitude = np.radians(longitude)
    x = np.mean(np.cos(latitude) * np.cos(longitude))
    y = np.mean(np.cos(latitude) * np.sin(longitude))
    z = np.mean(np.sin(latitude))
    avg_lat = np.degrees(np.atan2(z, np.sqrt(x * x + y * y)))
    avg_lon = np.degrees(np.atan2(y, x))
    return avg_lat, avg_lon
