""" Helper functions. """
import configparser
import re
from typing import Any, Dict, Union


def read_config(filename: str) -> configparser.ConfigParser:
    conf = configparser.ConfigParser()
    conf.optionxform = str  # type: ignore
    conf.read(filename)
    return conf


def read_version() -> str:
    version: Dict[str, Any] = {}
    with open("cloudnetpy_qc/version.py", encoding="utf-8") as f:
        exec(f.read(), version)  # pylint: disable=W0122
    return version["__version__"]


def format_value(value: Union[str, int, float]) -> Union[float, int]:
    value = str2num(value)
    if isinstance(value, int):
        return value
    return round(float(value), 3)


def format_msg(msg_in: Union[str, list]) -> str:
    msg = msg_in[0] if isinstance(msg_in, list) else msg_in
    if not msg.endswith("."):
        msg += "."
    x = re.search("^(.+):", msg)
    if x:
        msg = msg[x.end() :]
    msg = re.sub(" +", " ", msg)
    msg = msg.strip()
    msg = msg[0].capitalize() + msg[1:]
    return msg


def str2num(value: Union[str, int, float]) -> Union[float, int]:
    if not isinstance(value, str):
        return value
    try:
        return int(value)
    except ValueError:
        return float(value)
