"""Exact figures: inputs read as written, outputs rounded half away from zero."""
import math
from decimal import Decimal
from fractions import Fraction
from typing import Union

Number = Union[int, float, Fraction]


def as_written(x: Number) -> Fraction:
    """The number as the person wrote it: a Fraction or an int as is,
    a float as its shortest decimal text."""
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            raise ValueError("not a finite number: %r" % (x,))
        return Fraction(repr(x))
    return Fraction(x)


def shown(x: Number, places: int) -> Decimal:
    """`x` rounded half away from zero to `places` decimal places, for output only."""
    q = as_written(x) * 10 ** places
    n = math.floor(abs(q) + Fraction(1, 2))
    digits = tuple(int(c) for c in str(n))
    return Decimal((1 if q < 0 else 0, digits, -places))


def as_float(v: Number) -> float:
    """float(v); a value above the float range becomes plus or minus infinity."""
    try:
        return float(v)
    except OverflowError:
        return math.copysign(math.inf, -1 if v < 0 else 1)
