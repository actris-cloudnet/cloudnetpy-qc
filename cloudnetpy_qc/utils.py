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
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    return res.json()


def integer_ranges(ints: list[int]) -> list[str]:
    """
    Convert given integers to list of ranges.
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
