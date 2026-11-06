"""
Pricing Plugin — Shared Constants

Loads config/defaults.json at import time and exports config-governed thresholds
as named constants. Import from this module to avoid hardcoding threshold values
in calculator functions or test fixtures.

Usage:
    from pricing_constants import ACCURACY_FEAR_SIGNAL_THRESHOLD, AUTOMATION_RATE_FEAR_SIGNAL_THRESHOLD
"""

import json
from pathlib import Path

_DEFAULTS_PATH = Path(__file__).parent.parent / "config" / "defaults.json"

try:
    with open(_DEFAULTS_PATH) as _f:
        _defaults = json.load(_f)
except FileNotFoundError:
    raise FileNotFoundError(
        f"pricing_constants: config file not found: {_DEFAULTS_PATH}"
    ) from None
except json.JSONDecodeError as exc:
    raise ValueError(
        f"pricing_constants: malformed JSON in {_DEFAULTS_PATH}: {exc}"
    ) from exc


def _require(d: dict, *keys: str) -> float:
    """Walk nested dict keys, raising KeyError with full path on miss."""
    path = []
    for k in keys:
        path.append(k)
        if not isinstance(d, dict) or k not in d:
            raise KeyError(
                f"pricing_constants: missing key '{'.'.join(path)}' in {_DEFAULTS_PATH}"
            )
        d = d[k]
    return float(d)


ACCURACY_FEAR_SIGNAL_THRESHOLD: float = _require(
    _defaults, "formulas", "path_b", "accuracy_fear_signal_threshold"
)
AUTOMATION_RATE_FEAR_SIGNAL_THRESHOLD: float = _require(
    _defaults, "formulas", "path_c_fully_agentic", "automation_rate_fear_signal_threshold"
)
