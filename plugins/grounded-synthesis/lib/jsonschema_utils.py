"""
jsonschema_utils.py — Shared jsonschema helpers for grounded-synthesis.

Used by: lib/fact_schema.py, lib/handoff_schema.py
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def format_error(error: jsonschema.ValidationError) -> str:
    """Produce a human-readable error string from a jsonschema ValidationError."""
    path_str = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else ""
    if path_str:
        return f"{path_str}: {error.message}"
    return error.message


def load_json_file(path: str) -> tuple[dict | None, str | None]:
    """Read and parse a JSON file at *path*.

    Returns (data, None) on success.
    Returns (None, error_message) on OSError or JSON parse failure.
    Does NOT raise.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"File read error: {exc}"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error: {exc}"

    return data, None
