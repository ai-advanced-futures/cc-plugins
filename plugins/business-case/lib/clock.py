"""The one date and time source. Tests set BUSINESS_CASE_TODAY and BUSINESS_CASE_NOW to pin them."""
from __future__ import annotations

import os
from datetime import date, datetime, timezone


def today() -> str:
    """The ISO date: BUSINESS_CASE_TODAY when it is set and not empty, else today's date."""
    return os.environ.get("BUSINESS_CASE_TODAY") or date.today().isoformat()


def now() -> str:
    """An ISO 8601 UTC timestamp, YYYY-MM-DDTHH:MM:SSZ: BUSINESS_CASE_NOW when it is set and not
    empty, else the current time in UTC."""
    return os.environ.get("BUSINESS_CASE_NOW") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
