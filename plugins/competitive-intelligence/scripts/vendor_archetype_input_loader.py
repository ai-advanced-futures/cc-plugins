"""Load + validate the agent-written vendor-archetype input JSON.

Produces a frozen VendorArchetypeInput carrying vendor identity plus the validated
7-bool VendorPricingSignals block. Wrong type / unknown enum / missing required
field -> ValueError. NO cross-plugin import.
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path

from scripts.vendor_archetype_classifier import VendorPricingSignals

_CONFIDENCE = {"high", "medium", "low"}
# Derived from VendorPricingSignals fields — single source of truth.
# No parallel tuple to keep in sync.
_SIGNAL_KEYS = tuple(f.name for f in dataclasses.fields(VendorPricingSignals))


@dataclass(frozen=True)
class VendorArchetypeInput:
    vendor_name: str
    pricing_page_url: str | None
    schema_version: str
    confidence: str
    rationale: str
    signals: VendorPricingSignals
    multi_sku: bool


def _require_str(d: dict, key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v:
        raise ValueError(f"{key} must be a non-empty string, got {v!r}")
    return v


def _signals(d: dict) -> VendorPricingSignals:
    raw = d.get("signals")
    if not isinstance(raw, dict):
        raise ValueError(f"signals must be an object, got {type(raw).__name__}")
    for key in _SIGNAL_KEYS:
        if key not in raw:
            raise ValueError(f"signals missing required key: {key}")
        if not isinstance(raw[key], bool):
            raise ValueError(f"signal {key} must be bool, got {type(raw[key]).__name__}")
    extra = set(raw) - set(_SIGNAL_KEYS)
    if extra:
        raise ValueError(f"signals has unknown keys: {sorted(extra)}")
    return VendorPricingSignals(**{k: raw[k] for k in _SIGNAL_KEYS})


def load_and_validate(path: str) -> VendorArchetypeInput:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    confidence = _require_str(data, "confidence")
    if confidence not in _CONFIDENCE:
        raise ValueError(f"confidence must be one of {sorted(_CONFIDENCE)}, got {confidence!r}")
    url = data.get("pricing_page_url")
    if url is not None and not isinstance(url, str):
        raise ValueError(f"pricing_page_url must be string or absent, got {type(url).__name__}")
    multi_sku = data.get("multi_sku", False)
    if not isinstance(multi_sku, bool):
        raise ValueError(f"multi_sku must be bool, got {type(multi_sku).__name__}")
    return VendorArchetypeInput(
        vendor_name=_require_str(data, "vendor_name"),
        pricing_page_url=url,
        schema_version=_require_str(data, "schema_version"),
        confidence=confidence,
        rationale=_require_str(data, "rationale"),
        signals=_signals(data),
        multi_sku=multi_sku,
    )
