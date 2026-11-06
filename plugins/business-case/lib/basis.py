"""The financial basis: five lines read from the case with no defaults, and the month grid.

Money is `decimal.Decimal` under `CONTEXT`. Nothing here guesses a value: a line that is
missing, blank, given twice or not understood becomes a reason in `Basis.unparsed`.
"""
from __future__ import annotations

import decimal
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from . import case_doc, paths

CONTEXT = decimal.Context(prec=28)

CURRENCIES = {
    "USD": ("$", "US$"),
    "EUR": ("€",),
    "GBP": ("£",),
    "JPY": ("¥", "JP¥"),
    "CHF": ("CHF",),
    "CAD": ("$", "C$", "CA$"),
    "AUD": ("$", "A$", "AU$"),
    "NZD": ("$", "NZ$"),
    "SGD": ("$", "S$"),
    "HKD": ("$", "HK$"),
    "INR": ("₹",),
    "CNY": ("¥", "CN¥"),
    "SEK": ("kr",),
    "NOK": ("kr",),
    "DKK": ("kr",),
    "BRL": ("R$",),
    "MXN": ("$", "MX$"),
    "ZAR": ("R",),
}

LABELS = ("Discount rate", "Horizon", "Currency", "Start month", "Cost assumptions")

_RATE = re.compile(r"([0-9]{1,3}(?:\.[0-9]{1,12})?)[ \t]*(?:%|percent)(?:[ \t]+(?:a year|per year|per annum|annual))?",
                   re.IGNORECASE)
_HORIZON = re.compile(r"([0-9]{1,3})[ \t]+(months?|years?)", re.IGNORECASE)
_START = re.compile(r"([0-9]{4})-([0-9]{2})")
_CURRENCY_FIRST = re.compile(r"([A-Za-z]+)(?:[ \t].*)?")


class BasisRefused(ValueError):
    """A basis value or a month range is not valid."""


@dataclass(frozen=True)
class Basis:
    rate: "Decimal | None"
    horizon: "int | None"
    currency: "str | None"
    start_month: "str | None"
    cost_assumptions: "str | None"
    unparsed: "tuple[str, ...]"

    @property
    def complete(self) -> bool:
        return self.unparsed == ()


def _parse_rate(value: str):
    m = _RATE.fullmatch(value)
    if not m:
        raise BasisRefused(f"'{value}' is not a percent")
    with decimal.localcontext(CONTEXT):
        rate = Decimal(m.group(1)) / 100
    if not (0 <= rate < 1):
        raise BasisRefused(f"'{value}' is not from 0% up to (not including) 100%")
    return rate, value


def _parse_horizon(value: str):
    m = _HORIZON.fullmatch(value)
    if not m:
        raise BasisRefused(f"'{value}' is not a number of months or years")
    months = int(m.group(1)) * (12 if m.group(2).lower().startswith("year") else 1)
    if not 1 <= months <= 600:
        raise BasisRefused(f"'{value}' is not from 1 to 600 months")
    return months, value


def _parse_currency(value: str):
    m = _CURRENCY_FIRST.fullmatch(value)
    if not m or m.group(1) not in CURRENCIES:
        raise BasisRefused(f"'{value}' does not start with a known currency code")
    return m.group(1), value


def _parse_start_month(value: str):
    m = _START.fullmatch(value)
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise BasisRefused(f"'{value}' is not a month written YYYY-MM")
    return value, value


def _parse_cost(value: str):
    if not value.strip():
        raise BasisRefused("is blank")
    return value.strip(), value


_PARSERS = {
    "Discount rate": _parse_rate,
    "Horizon": _parse_horizon,
    "Currency": _parse_currency,
    "Start month": _parse_start_month,
    "Cost assumptions": _parse_cost,
}


def _reason(label: str, err: BasisRefused) -> str:
    text = str(err)
    return f"{label}: {text}" if text.startswith("'") else f"{label} {text}"


def _label_lines(body: str) -> dict:
    """Label -> the values on its lines (stripped of the line ending and of end spaces)."""
    folded = {label.casefold(): label for label in LABELS}
    out = {label: [] for label in LABELS}
    for line in body.splitlines():
        head, sep, rest = line.partition(":")
        label = folded.get(head.casefold())
        if sep and label:
            out[label].append(rest.strip(" \t"))
    return out


def parse_basis(financials_body: str) -> Basis:
    values, unparsed = {}, []
    found = _label_lines(financials_body)
    for label in LABELS:
        lines = found[label]
        if not lines:
            unparsed.append(f"{label} is missing")
        elif len(lines) > 1:
            unparsed.append(f"{label} is stated twice")
        elif not lines[0]:
            unparsed.append(f"{label} is blank")
        else:
            try:
                values[label] = _PARSERS[label](lines[0])[0]
            except (BasisRefused, ArithmeticError, ValueError) as err:
                unparsed.append(_reason(label, err))
    return Basis(values.get("Discount rate"), values.get("Horizon"), values.get("Currency"),
                 values.get("Start month"), values.get("Cost assumptions"), tuple(unparsed))


NO_FINANCIALS = "the case has no “{heading}” section"


def _financials_heading() -> str:
    """The template's heading for the financials section, as the person reads it (Task 17)."""
    try:
        return case_doc.headings(paths.TEMPLATE.read_text(encoding="utf-8")).get("financials", "financial basis")
    except (OSError, UnicodeDecodeError):
        return "financial basis"


def _unread(reason: str) -> Basis:
    return Basis(None, None, None, None, None, (reason,))


def basis_of_sections(sections: dict) -> Basis:
    """The basis from business-case.md's sections. No financials section is one reason that says so,
    in the funder's words: the section by its heading, never the file or the key."""
    body = sections.get("financials")
    if body is None:
        return _unread(NO_FINANCIALS.format(heading=_financials_heading()))
    return parse_basis(body)


def read_basis(case_dir) -> Basis:
    """The `financials` section of business-case.md. A file that cannot be read or split into
    sections is one reason naming the cause, never five missing lines (Task 8 carry)."""
    try:
        text = (Path(case_dir) / paths.CASE_DOC).read_text(encoding="utf-8")
        sections = case_doc.parse_sections(text)
    except (OSError, UnicodeDecodeError, case_doc.CaseDocError) as exc:
        return _unread(f"{paths.CASE_DOC} cannot be read: {exc}")
    return basis_of_sections(sections)


def monthly_rate(annual: Decimal) -> Decimal:
    with decimal.localcontext(CONTEXT):
        return (1 + annual) ** (Decimal(1) / 12) - 1


def spread(amount: Decimal, first: int, last: int) -> dict:
    """Month -> share. Equal shares, and the last month takes the remainder, so the sum is exact."""
    if last < first:
        raise BasisRefused(f"month {last} is before month {first}")
    n = last - first + 1
    with decimal.localcontext(CONTEXT):
        share = amount / n
        out = {m: share for m in range(first, last)}
        out[last] = amount - share * (n - 1)
    return out
