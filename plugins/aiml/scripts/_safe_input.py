"""Safe reads of the input of the aiml scripts (STORY-368).

read_json(path) opens the file 1 time, checks the open file with fstat, and reads at most MAX_INPUT_BYTES. It
accepts only a regular file: a link is followed, and its target must be a regular file. O_NONBLOCK keeps the open of
a named pipe from waiting. Each number must be a finite float: NaN, Infinity, 1e999 and an integer too large for a
float are refused. Each of these problems raises InputFileError with 1 line that starts with the path. A missing
file raises FileNotFoundError, as before, so each script keeps its own line for it.

finite_float is an argparse type that accepts only a finite number, and is_finite tests a parsed value.

Standard library only. A helper script imports this module inside main(), after it puts the folder of the script on
sys.path.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import stat

MAX_INPUT_BYTES = 8 * 1024 * 1024


class InputFileError(ValueError):
    """An input file that a script does not read. The text is 1 line, and it starts with the path."""


class _NumberError(ValueError):
    pass


def _float(text):
    value = float(text)
    if not math.isfinite(value):
        raise _NumberError(f"the number {text[:40]} is not finite")
    return value


def _int(text):
    value = int(text)  # more than 4300 digits raises ValueError
    try:
        float(value)
    except OverflowError:
        raise _NumberError(f"the number {text[:20]}... is too large") from None
    return value


def _constant(name):
    raise _NumberError(f"the value {name} is not a number")


def read_json(path):
    """The JSON value of the file at `path`. Raises FileNotFoundError or InputFileError."""
    name = os.fspath(path)
    try:
        fd = os.open(name, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise InputFileError(f"{name}: cannot read the file: {exc.strerror}") from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise InputFileError(f"{name}: not a regular file")
        if info.st_size > MAX_INPUT_BYTES:
            raise InputFileError(f"{name}: larger than {MAX_INPUT_BYTES} bytes")
        with os.fdopen(fd, "rb") as handle:  # fdopen takes the fd: closing the handle closes it
            fd = -1
            data = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise InputFileError(f"{name}: cannot read the file: {exc.strerror}") from None
    finally:
        if fd >= 0:
            os.close(fd)
    if len(data) > MAX_INPUT_BYTES:
        raise InputFileError(f"{name}: larger than {MAX_INPUT_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise InputFileError(f"{name}: not UTF-8 text") from None
    try:
        return json.loads(text, parse_float=_float, parse_int=_int, parse_constant=_constant)
    except RecursionError:
        raise InputFileError(f"{name}: nested too deep") from None
    except _NumberError as exc:
        raise InputFileError(f"{name}: {exc}") from None
    except ValueError as exc:
        raise InputFileError(f"{name}: not valid JSON: {exc}") from None


def is_finite(value) -> bool:
    """True for an int or a float that is finite. A bool is not a number here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def finite_float(text):
    """An argparse type: a finite number. NaN and Infinity are refused."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid number: {text!r}") from None
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError(f"not a finite number: {text!r}")
    return value


def finite_int(text):
    """An argparse type: a whole number that a float can hold. 10**400 is refused."""
    try:
        value = int(text)  # more than 4300 digits raises ValueError
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid whole number: {text[:40]!r}") from None
    try:
        float(value)
    except OverflowError:
        raise argparse.ArgumentTypeError(f"the number {text[:20]}... is too large") from None
    return value
