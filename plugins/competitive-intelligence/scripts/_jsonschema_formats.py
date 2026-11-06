# plugins/competitive-intelligence/scripts/_jsonschema_formats.py
"""Shared JSON Schema validation primitives for competitive-intelligence scripts.

Single source of truth for FormatChecker registration (uuid + date-time) and the
SCHEMAS_DIR constant. Imported (package-form `from scripts._jsonschema_formats`)
by competitive-intelligence scripts that validate against the schemas in the
`schemas/` folder of this plugin. The plugin holds its own copy and imports from
no other plugin. Deliberately STRICT / fail-closed (distinct from the legacy
scripts/schema_validator.py which degrades gracefully when jsonschema is absent).
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import FormatChecker

# The schemas folder of this plugin: scripts/ -> plugin root -> schemas/.
SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"

FORMAT_CHECKER = FormatChecker()

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


@FORMAT_CHECKER.checks("uuid", raises=ValueError)
def _check_uuid(value):
    if not isinstance(value, str):
        raise ValueError(f"uuid must be string, got {type(value).__name__}")
    if not _UUID_RE.match(value):
        raise ValueError(f"invalid uuid: {value!r}")
    return True


@FORMAT_CHECKER.checks("date-time", raises=ValueError)
def _check_iso8601(value):
    if not isinstance(value, str):
        raise ValueError(f"date-time must be string, got {type(value).__name__}")
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return True


@FORMAT_CHECKER.checks("uri", raises=ValueError)
def _check_uri(value):
    if not isinstance(value, str):
        raise ValueError(f"uri must be string, got {type(value).__name__}")
    parsed = urlparse(value)
    if not parsed.scheme:
        raise ValueError(f"invalid uri (missing scheme): {value!r}")
    if parsed.scheme in ("http", "https", "ftp", "wss") and not parsed.netloc:
        raise ValueError(f"invalid uri (empty authority for {parsed.scheme}): {value!r}")
    return True
