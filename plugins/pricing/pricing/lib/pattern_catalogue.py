"""Pattern catalogue — promoted from schemas/agentic-pricing/pattern_catalogue.yaml.

Per spec §7. Loaded at import time from the YAML; sha256-pinned for drift detection.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml


@dataclass(frozen=True)
class PatternDef:
    pattern_id: str
    name: str
    acv_band: str
    description: str
    audience_default: Literal["internal", "customer-facing", "mixed"]


def _yaml_path() -> Path:
    """Location of pattern_catalogue.yaml in the schema folder of this plugin."""
    return Path(__file__).resolve().parents[2] / "schemas" / "agentic-pricing" / "pattern_catalogue.yaml"


def _load() -> tuple[dict[str, PatternDef], str]:
    path = _yaml_path()
    raw = path.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()
    data = yaml.safe_load(raw)
    patterns: dict[str, PatternDef] = {}
    for entry in data["patterns"]:
        pdef = PatternDef(
            pattern_id=entry["pattern_id"],
            name=entry["name"],
            acv_band=entry["acv_band"],
            description=entry["description"],
            audience_default=entry["audience_default"],
        )
        patterns[pdef.pattern_id] = pdef
    return patterns, actual_hash


# Initial bootstrap: empty string. The bootstrap script writes the actual hash.
# When this is empty, ALL tests pass (no drift to detect). When non-empty,
# test_pattern_catalogue_hash_matches_pin enforces.
_YAML_SHA256_PINNED: str = "ca268549e36f7a758912f6f005167744019e72cea270ff5f58c58f0f64f4eca2"

PATTERNS, _YAML_SHA256_ACTUAL = _load()
PATTERN_IDS: frozenset[str] = frozenset(PATTERNS.keys())

# Drift sanity at import: if a hash is pinned and doesn't match, warn (do not fail
# at import — the test will fail explicitly so failures surface in pytest, not in
# every import).
if _YAML_SHA256_PINNED and _YAML_SHA256_PINNED != _YAML_SHA256_ACTUAL:
    import warnings
    warnings.warn(
        f"pattern_catalogue.yaml sha256 drift: pinned={_YAML_SHA256_PINNED!r} "
        f"actual={_YAML_SHA256_ACTUAL!r}",
        UserWarning,
    )
