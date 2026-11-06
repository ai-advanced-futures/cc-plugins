"""Shared JSON Schema validation primitives for gtm plugin scripts.

This file holds the FormatChecker rules (uuid, date-time, uri) and the
SCHEMAS_DIR constant. Other gtm scripts import it as
`from scripts._jsonschema_formats import ...`. They use it to check data
against the schemas in the `schemas/` folder of this plugin. This file has
its own copy of the helper. It imports nothing from another plugin.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import FormatChecker

# The schemas are in the `schemas/` folder of the plugin (parents[1] is the plugin folder).
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
