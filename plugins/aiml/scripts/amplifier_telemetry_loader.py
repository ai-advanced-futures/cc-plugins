"""Loader for amplifier-telemetry-input.json. Validates against Charter §7.10 schema."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft7Validator

# Ensure the scripts dir is on sys.path so the shared module is importable when
# this loader is invoked as `python3 plugins/aiml/scripts/amplifier_telemetry_loader.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402

# Resolve schema path relative to repo root (3 parents up from plugins/aiml/scripts/).
_SCHEMA_PATH = SCHEMAS_DIR / "amplifier-telemetry-input.schema.json"


@dataclass(frozen=True)
class AmplifierReading:
    amp_id: int           # 1-8
    multiplier_p75: float
    multiplier_p95: float
    sample_size_n: int
    detection_signal: str
    present: bool


@dataclass(frozen=True)
class MeasurementWindow:
    start: str
    end: str
    duration_days: int


@dataclass(frozen=True)
class AmplifierTelemetryInput:
    engagement_id: str
    produced_at: str
    schema_version: str
    audience: str
    measurement_window: MeasurementWindow
    telemetry_source: str
    amplifiers: dict[int, AmplifierReading]
    notes: str = ""


def load_and_validate(path: Path) -> AmplifierTelemetryInput:
    """Load JSON, validate against Charter §7.10 schema, return AmplifierTelemetryInput."""
    try:
        raw = json.loads(Path(path).read_text())
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Input file not found: {path}") from e
    schema = json.loads(_SCHEMA_PATH.read_text())
    # Enable format-checker so "format": "uuid" and "format": "date-time" are enforced.
    # FORMAT_CHECKER is the shared instance from _jsonschema_formats.py with UUID +
    # date-time explicitly registered (bundled jsonschema omits uuid + may omit
    # date-time depending on Python version).
    Draft7Validator(schema, format_checker=FORMAT_CHECKER).validate(raw)

    mw = MeasurementWindow(**raw["measurement_window"])
    amps: dict[int, AmplifierReading] = {}
    for k, v in raw["amplifiers"].items():
        amps[int(k)] = AmplifierReading(
            amp_id=int(k),
            multiplier_p75=v["measured_p75"],
            multiplier_p95=v["measured_p95"],
            sample_size_n=v["sample_size_n"],
            detection_signal=v["detection_signal"],
            present=v["present"],
        )

    return AmplifierTelemetryInput(
        engagement_id=raw["engagement_id"],
        produced_at=raw["produced_at"],
        schema_version=raw["schema_version"],
        audience=raw["audience"],
        measurement_window=mw,
        telemetry_source=raw["telemetry_source"],
        amplifiers=amps,
        notes=raw.get("notes", ""),
    )


if __name__ == "__main__":
    import sys
    result = load_and_validate(Path(sys.argv[1]))
    print(f"OK: engagement_id={result.engagement_id}, amps={len(result.amplifiers)}")
