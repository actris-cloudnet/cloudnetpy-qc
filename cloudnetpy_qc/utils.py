""" Helper functions. """
import configparser
import re
from functools import lru_cache

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


def _format_list(values: list[str]):
    if len(values) == 0:
        return ""
    if len(values) == 1:
        return "'" + values[0] + "'"
    return "'" + "', '".join(values[:-1]) + "' or '" + values[-1] + "'"


def create_expected_received_msg(
    expected: str | list[str],
    received: str,
    variable: str | None = None,
) -> str:
    if isinstance(expected, str):
        expected = [expected]
    msg = f"Expected {_format_list(expected)} but received '{received}'"
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
        f"Value {format_value(value)} exceeds expected limits {format_value(lower_limit)} ... "
        f"{format_value(upper_limit)} with variable '{variable}'"
    )


def format_value(value: str | int | float) -> str:
    return "{:,g}".format(float(value))


@lru_cache
def fetch_pid(pid: str) -> dict:
    match = re.fullmatch(PID_FORMAT, pid)
    if match is None:
        raise ValueError("Invalid PID format")
    url = "https://hdl.handle.net/api/handles/" + match[1]
    res = requests.get(url)
    res.raise_for_status()
    return res.json()
