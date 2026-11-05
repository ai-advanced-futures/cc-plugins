# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""
fact_schema.py — JSON schema validator for grounded-synthesis fact files.

Fact file schema (BUILD_PLAN §2.5.1):

  {
    "session_id":        "<uuid4>",               -- required
    "source_path":       "<absolute path>",       -- required
    "source_type":       "md|txt|pdf",            -- required, enum
    "extraction_model":  "claude-sonnet-4-6",     -- required
    "facts": [                                    -- required, minItems=BOUNDS[0], maxItems=BOUNDS[1]
      {
        "id":    "src{i}-f{n}",                   -- required
        "claim": "<one-sentence atomic statement>",-- required
        "provenance": {                           -- required
          "locator_type": "page|line|section|verbatim", -- required, enum
          "locator":      "<page 3 | line 47 | ...>"    -- required
        }
      }
    ],
    "extraction_notes": "<optional string>"       -- optional
  }

CLI mode: uv run ${CLAUDE_PLUGIN_ROOT}/lib/fact_schema.py --validate-session <dir>
  Scans all source-*-facts.json files in <dir>, sorted by source index.
  Prints to stdout:
    {"valid": [0, 2, 3], "invalid": [{"index": 1, "error": "..."}]}
  Exit 0 always (orchestrator reads the JSON to decide whether to abort).

Used by: grounded-synthesis-orchestrator (BUILD_PLAN §2.5.4 step 4)
         tests/unit/test_fact_schema.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

# When imported as part of the uv/pytest workspace, lib.constants is on sys.path.
# When executed as __main__ via `uv run ${CLAUDE_PLUGIN_ROOT}/lib/fact_schema.py`, the plugin
# root directory may not be on sys.path yet — add it before the import.
if __name__ == "__main__":
    _plugin_root = Path(__file__).resolve().parent.parent
    if str(_plugin_root) not in sys.path:
        sys.path.insert(0, str(_plugin_root))

from lib.constants import FACTS_PER_SOURCE_BOUNDS
from lib.jsonschema_utils import format_error, load_json_file

_MIN_FACTS, _MAX_FACTS = FACTS_PER_SOURCE_BOUNDS

# ---------------------------------------------------------------------------
# JSON Schema definition (mirrors BUILD_PLAN §2.5.1)
# ---------------------------------------------------------------------------

_FACT_SCHEMA: dict = {
    "type": "object",
    "required": ["session_id", "source_path", "source_type", "extraction_model", "facts"],
    "additionalProperties": True,
    "properties": {
        "session_id": {"type": "string", "minLength": 1},
        "source_path": {"type": "string", "minLength": 1},
        "source_type": {"type": "string", "enum": ["md", "txt", "pdf"]},
        "extraction_model": {"type": "string", "minLength": 1},
        "extraction_notes": {"type": "string"},
        "facts": {
            "type": "array",
            "minItems": _MIN_FACTS,
            "maxItems": _MAX_FACTS,
            "items": {
                "type": "object",
                "required": ["id", "claim", "provenance"],
                "additionalProperties": True,
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "claim": {"type": "string", "minLength": 1},
                    "provenance": {
                        "type": "object",
                        "required": ["locator_type", "locator"],
                        "additionalProperties": True,
                        "properties": {
                            "locator_type": {
                                "type": "string",
                                "enum": ["page", "line", "section", "verbatim"],
                            },
                            "locator": {"type": "string", "minLength": 1},
                        },
                    },
                },
            },
        },
    },
}

# Pre-compile the validator once for performance.
_VALIDATOR = jsonschema.Draft7Validator(_FACT_SCHEMA)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactValidationResult:
    """Result of validating a single fact file against the schema."""

    valid: bool
    errors: list[str] = field(default_factory=list)


def validate_fact_file(path: str) -> FactValidationResult:
    """Validate the fact file at *path* against the fact-file JSON schema.

    Returns FactValidationResult(valid=True, errors=[]) on success.
    Returns FactValidationResult(valid=False, errors=[<messages>]) on failure.
    Does NOT raise on JSON-parse errors or schema violations.
    """
    data, err = load_json_file(path)
    if err is not None:
        return FactValidationResult(valid=False, errors=[err])

    validation_errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    if not validation_errors:
        return FactValidationResult(valid=True, errors=[])

    messages = [format_error(e) for e in validation_errors]
    return FactValidationResult(valid=False, errors=messages)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _source_index_from_filename(filename: str) -> int | None:
    """Extract the integer source index from 'source-{N}-facts.json'.

    Returns None if the filename does not match the expected pattern.
    """
    match = re.fullmatch(r"source-(\d+)-facts\.json", filename)
    if match:
        return int(match.group(1))
    return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _run_validate_session(session_dir: str) -> None:
    """Walk source-*-facts.json files in session_dir, validate each, print JSON result."""
    dir_path = Path(session_dir)
    # Collect files matching the naming convention, sorted by index.
    candidates: list[tuple[int, Path]] = []
    for child in dir_path.iterdir():
        if child.is_file():
            idx = _source_index_from_filename(child.name)
            if idx is not None:
                candidates.append((idx, child))

    candidates.sort(key=lambda t: t[0])

    valid_indices: list[int] = []
    invalid_entries: list[dict] = []

    for idx, file_path in candidates:
        result = validate_fact_file(str(file_path))
        if result.valid:
            valid_indices.append(idx)
        else:
            invalid_entries.append(
                {
                    "index": idx,
                    "error": result.errors[0] if result.errors else "unknown error",
                }
            )

    output = {"valid": valid_indices, "invalid": invalid_entries}
    print(json.dumps(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate grounded-synthesis fact files against the fact-file JSON schema."
    )
    parser.add_argument(
        "--validate-session",
        metavar="DIR",
        required=True,
        help="Path to the session directory containing source-*-facts.json files.",
    )
    args = parser.parse_args()
    _run_validate_session(args.validate_session)
    sys.exit(0)
