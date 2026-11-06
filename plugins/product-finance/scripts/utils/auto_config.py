"""Auto-config loader for the setup command.

When `.product-finance/auto-config.json` exists and `enabled: true`,
the setup command reads default answers from `question_keys` instead of
asking the person.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_CONFIG_PATH = Path(".product-finance/auto-config.json")


def load_auto_config() -> Optional[dict]:
    """Load auto-config from .product-finance/auto-config.json.

    Returns the config dict if file exists and enabled=true, else None.
    """
    if not _CONFIG_PATH.exists():
        return None
    with open(_CONFIG_PATH) as f:
        config = json.load(f)
    if not config.get("enabled", False):
        return None
    return config


def get_auto_answer(question_key: str) -> Optional[Any]:
    """Return the auto-answer for question_key, or None if not in auto mode.

    Usage in commands:
        answer = get_auto_answer("pricing_model")
        if answer is None:
            answer = AskUserQuestion(...)  # fallback to interactive
    """
    config = load_auto_config()
    if config is None:
        return None
    return config.get("question_keys", {}).get(question_key)


def is_auto_mode() -> bool:
    """Return True if auto-config is loaded and enabled."""
    return load_auto_config() is not None
