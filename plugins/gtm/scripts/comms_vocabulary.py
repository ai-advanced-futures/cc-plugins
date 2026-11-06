"""Build-time operator-vs-customer vocabulary lint for the comms templates.

This is a NEW lexicon/validator — NOT gtm's truth_tier_validator (which only
checks superlatives). check_customer_vocabulary() lints customer-audience
template SOURCE files at test time; it does NOT (and cannot) gate the LLM's
runtime-rendered copy. See ADR-003 decision 3.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

_LEXICON_PATH = Path(__file__).resolve().parent.parent / "definitions" / "comms-vocabulary.json"


@functools.lru_cache(maxsize=None)
def load_lexicon() -> dict:
    return json.loads(_LEXICON_PATH.read_text())


def check_customer_vocabulary(text: str) -> list[str]:
    """Return the operator-grade denylist terms present in customer-audience text.

    Empty list == clean (no operator-grade vocabulary leaked into customer copy).
    """
    lowered = text.lower()
    return [term for term in load_lexicon()["operator_denylist"] if term.lower() in lowered]
