"""Shared JSON Schema validation primitives for aiml plugin scripts.

Single source of truth for FormatChecker registration (uuid + date-time)
and the SCHEMAS_DIR constant. Imported by all aiml scripts that validate
against the federation schemas in the folder schemas/ of the plugin.

This module was extracted from duplicated code in amplifier_telemetry_loader.py,
p15_trigger_input_loader.py, p15_trigger_emitter.py, and
cost_amplifier_readout_emitter.py.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import FormatChecker

# Single source of truth for the schemas folder of the plugin.
SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"

# Single shared FormatChecker. Both UUID and date-time formats are explicitly
# registered because bundled jsonschema's default FormatChecker omits UUID
# entirely and may omit date-time depending on Python version.
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
    s = value.replace("Z", "+00:00")
    datetime.fromisoformat(s)
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
