"""Pre-flight simulator for product-finance commands.

Call simulate_command(command_name) before executing any command to verify
that required inputs (assumptions.json, etc.) are present and valid.
Returns a dict: {can_proceed: bool, missing: [str], warnings: [str]}.

Commands that do NOT require assumptions.json:
  - discover  (first-run, no prior data needed)

All other commands require .product-finance/assumptions.json with at
minimum: pricing and costs sections.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ASSUMPTIONS_PATH = Path(".product-finance/assumptions.json")

# Commands that can run without assumptions.json
_NO_ASSUMPTIONS_REQUIRED = {"discover"}

# Required top-level sections per command.
# Commands not listed here require only the base sections.
_REQUIRED_SECTIONS: dict[str, list[str]] = {
    "unit-economics": ["pricing", "costs"],
    "health-check": ["pricing", "costs"],
    "ai-economics": ["pricing", "costs"],
    "feature-roi": ["pricing", "costs"],
    "instrumentation": ["pricing", "costs"],
}
_BASE_REQUIRED_SECTIONS = ["pricing", "costs"]


def simulate_command(command: str) -> dict[str, Any]:
    """Simulate command feasibility. Returns {can_proceed, missing, warnings}."""
    missing: list[str] = []
    warnings: list[str] = []

    if command in _NO_ASSUMPTIONS_REQUIRED:
        return {"can_proceed": True, "missing": missing, "warnings": warnings}

    # Unknown commands (not in _REQUIRED_SECTIONS) are allowed to proceed without checks.
    if command not in _REQUIRED_SECTIONS:
        return {"can_proceed": True, "missing": missing, "warnings": warnings}

    if not _ASSUMPTIONS_PATH.exists():
        missing.append(
            ".product-finance/assumptions.json not found — run /product-finance:setup first"
        )
        return {"can_proceed": False, "missing": missing, "warnings": warnings}

    try:
        with open(_ASSUMPTIONS_PATH) as f:
            assumptions = json.load(f)
    except json.JSONDecodeError as e:
        missing.append(f".product-finance/assumptions.json is invalid JSON: {e}")
        return {"can_proceed": False, "missing": missing, "warnings": warnings}

    required = _REQUIRED_SECTIONS.get(command, _BASE_REQUIRED_SECTIONS)
    for section in required:
        if section not in assumptions:
            missing.append(f"assumptions.json missing required section: '{section}'")

    _check_sanity_warnings(assumptions, warnings)

    return {
        "can_proceed": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }


def _check_sanity_warnings(assumptions: dict, warnings: list[str]) -> None:
    """Add warnings for suspicious but non-blocking assumption values."""
    cogs = assumptions.get("costs", {}).get("cogs", {})
    for field in ("hosting_per_user", "ai_per_user", "support_per_user"):
        val = cogs.get(field)
        if val is not None and val < 0:
            warnings.append(
                f"costs.cogs.{field} is negative ({val}) — verify this is intentional"
            )

    pricing = assumptions.get("pricing", {})
    price = pricing.get("price_per_seat_monthly")
    if price is not None and price > 10000:
        warnings.append(
            f"pricing.price_per_seat_monthly={price} seems very high — verify units"
        )
