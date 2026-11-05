"""One ISO time as an aware datetime.

A time with no zone reads as UTC, because a naive datetime cannot compare
with the aware `now` and the comparison raises.
"""
from datetime import datetime, timezone


def parse_time(value) -> datetime | None:
    """One ISO time as an aware datetime, or None when it does not parse."""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
