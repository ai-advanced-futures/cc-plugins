# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Session lifecycle management for strategic-partnerships.

Run it with uv, from the folder of the person. It reads and writes `.sp-tmp/<session_id>/`.

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --init [--session-id ID]
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --sweep [--max-age-minutes 60]
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-preflight --session-id ID --phase P --confidence HIGH|MEDIUM|LOW [--missing a,b]
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-preflight --session-id ID --phase P --from-file FILE
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-evaluator --session-id ID --phase P --result PASS|FAIL [--gaps a,b]
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-evaluator --session-id ID --phase P --from-file FILE
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --complete-phase --session-id ID --phase P
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --complete --session-id ID

With `--from-file`, the values come from the JSON file that `simulate_phase.py --out` or
`evaluate_phase.py --out` wrote (`confidence` and `missing`, or `result` and `gaps`), so no
one copies a value into the command. `--from-file` and `--confidence`, `--missing`, `--result`
or `--gaps` together are a usage error.

A call that fails prints 1 line to standard error and exits 1.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PHASES = ["assess", "discover", "structure", "architect", "monetize", "synthesize"]
SP_TMP_DIR = ".sp-tmp"
CONFIDENCE_LEVELS = ["HIGH", "MEDIUM", "LOW"]
EVALUATOR_RESULTS = ["PASS", "FAIL"]


def session_id_arg(value: str) -> str:
    """Accept a plain name only, so the session folder stays inside `.sp-tmp/`.

    The other two scripts of this plugin hold the same check; each script is a single file.
    """
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", value) or value in (".", ".."):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a plain name (1 to 64 characters of A-Z, a-z, 0-9, '.', '_' and '-')"
        )
    return value


def generate_session_id() -> str:
    return str(uuid.uuid4())[:8]


def create_session(base_dir: Path, session_id: str) -> dict:
    session_dir = Path(base_dir) / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": session_id,
        "started_at": _now_iso(),
        "phases_complete": [],
        "current_phase": PHASES[0],
        "preflight_scores": {},
        "evaluator_scores": {},
        "evaluator_gaps": {},
        "apollo_enrichment_used": False,
        "discover_workers_complete": [],
        "conflict_pairs": [],
        "completed_at": None,
    }
    (session_dir / "session.json").write_text(json.dumps(data, indent=2))
    return data


def load_session(base_dir: Path, session_id: str) -> Optional[dict]:
    path = Path(base_dir) / session_id / "session.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _require_session(base_dir: Path, session_id: str) -> dict:
    current = load_session(base_dir, session_id)
    if current is None:
        raise ValueError(f"Session not found: {session_id}")
    return current


def _save(base_dir: Path, session_id: str, current: dict, updates: dict) -> None:
    path = Path(base_dir) / session_id / "session.json"
    path.write_text(json.dumps({**current, **updates}, indent=2))


def _with_phase(current: dict, key: str, phase: str, value) -> dict:
    """The dict `key` of the session, with `value` set for `phase`."""
    return {**current.get(key, {}), phase: value}


def update_session(base_dir: Path, session_id: str, updates: dict) -> None:
    _save(base_dir, session_id, _require_session(base_dir, session_id), updates)


def _is_complete(entry: Path) -> bool:
    try:
        session = json.loads((entry / "session.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(session, dict) and bool(session.get("completed_at"))


def sweep_stale_sessions(base_dir: Path, max_age_minutes: int = 60) -> int:
    """Remove the session folders older than the limit.

    A session with `completed_at` stays: the sweep recovers from a crash, and a complete
    session holds the report of the person.
    """
    base = Path(base_dir)
    if not base.exists():
        return 0
    cutoff = time.time() - max_age_minutes * 60
    removed = 0
    for entry in base.iterdir():
        if entry.is_dir() and entry.stat().st_mtime < cutoff and not _is_complete(entry):
            shutil.rmtree(entry)
            removed += 1
    return removed


def record_preflight(
    base_dir: Path, session_id: str, phase: str, confidence: str, missing: list[str]
) -> dict:
    current = _require_session(base_dir, session_id)
    updates = {
        "preflight_scores": _with_phase(current, "preflight_scores", phase, confidence),
        "preflight_missing": _with_phase(current, "preflight_missing", phase, missing),
    }
    _save(base_dir, session_id, current, updates)
    return {"phase": phase, "confidence": confidence}


def record_evaluator(
    base_dir: Path, session_id: str, phase: str, result: str, gaps: list[str]
) -> dict:
    current = _require_session(base_dir, session_id)
    updates = {
        "evaluator_scores": _with_phase(current, "evaluator_scores", phase, result),
        "evaluator_gaps": _with_phase(current, "evaluator_gaps", phase, gaps),
    }
    _save(base_dir, session_id, current, updates)
    return {"phase": phase, "result": result}


def complete_phase(base_dir: Path, session_id: str, phase: str) -> dict:
    current = _require_session(base_dir, session_id)
    done = list(current.get("phases_complete", []))
    if phase not in done:
        done.append(phase)
    index = PHASES.index(phase)
    next_phase = PHASES[index + 1] if index + 1 < len(PHASES) else phase
    updates = {"phases_complete": done, "current_phase": next_phase}
    _save(base_dir, session_id, current, updates)
    return updates


def complete_session(base_dir: Path, session_id: str) -> dict:
    updates = {"completed_at": _now_iso()}
    update_session(base_dir, session_id, updates)
    return updates


def _split(value: Optional[str]) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a strategic-partnerships session.")
    commands = parser.add_mutually_exclusive_group(required=True)
    commands.add_argument("--init", action="store_true", help="make a session and print its id")
    commands.add_argument("--sweep", action="store_true", help="remove stale sessions, print the count")
    commands.add_argument("--update-preflight", action="store_true")
    commands.add_argument("--update-evaluator", action="store_true")
    commands.add_argument("--complete-phase", action="store_true")
    commands.add_argument("--complete", action="store_true")
    parser.add_argument("--session-id", type=session_id_arg)
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--confidence", choices=CONFIDENCE_LEVELS)
    parser.add_argument("--result", choices=EVALUATOR_RESULTS)
    parser.add_argument("--missing", help="comma-separated list of missing inputs")
    parser.add_argument("--gaps", help="comma-separated list of rubric gaps")
    parser.add_argument("--from-file", help="JSON file of simulate_phase.py or evaluate_phase.py (--out)")
    parser.add_argument("--max-age-minutes", type=int, default=60)
    return parser


def _init(args: argparse.Namespace, base: Path) -> str:
    session_id = args.session_id or generate_session_id()
    create_session(base, session_id)
    return session_id


def _sweep(args: argparse.Namespace, base: Path) -> str:
    return str(sweep_stale_sessions(base, args.max_age_minutes))


def _read_values(path: str, value_key: str, list_key: str, choices: list[str]) -> tuple[str, list[str]]:
    """The value and the list of a `--out` file, checked with the same choices as the flags."""
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("the file must hold a JSON object")
    value, items = data.get(value_key), data.get(list_key, [])
    if value not in choices:
        raise ValueError(f"'{value_key}' in the file must be one of {choices}, got {value!r}")
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise ValueError(f"'{list_key}' in the file must be a list of strings")
    return value, items


def _update_preflight(args: argparse.Namespace, base: Path) -> str:
    if args.from_file:
        confidence, missing = _read_values(args.from_file, "confidence", "missing", CONFIDENCE_LEVELS)
    else:
        confidence, missing = args.confidence, _split(args.missing)
    return json.dumps(record_preflight(base, args.session_id, args.phase, confidence, missing))


def _update_evaluator(args: argparse.Namespace, base: Path) -> str:
    if args.from_file:
        result, gaps = _read_values(args.from_file, "result", "gaps", EVALUATOR_RESULTS)
    else:
        result, gaps = args.result, _split(args.gaps)
    return json.dumps(record_evaluator(base, args.session_id, args.phase, result, gaps))


def _complete_phase(args: argparse.Namespace, base: Path) -> str:
    return json.dumps(complete_phase(base, args.session_id, args.phase))


def _complete(args: argparse.Namespace, base: Path) -> str:
    complete_session(base, args.session_id)
    return args.session_id


# Command -> (required arguments, handler). A handler returns the line to print.
COMMANDS = {
    "init": ((), _init),
    "sweep": ((), _sweep),
    "update_preflight": (("session_id", "phase", "confidence"), _update_preflight),
    "update_evaluator": (("session_id", "phase", "result"), _update_evaluator),
    "complete_phase": (("session_id", "phase"), _complete_phase),
    "complete": (("session_id",), _complete),
}


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = next(name for name in COMMANDS if getattr(args, name))
    required, handler = COMMANDS[command]
    if args.from_file:
        if not (args.update_preflight or args.update_evaluator):
            parser.error("--from-file is for --update-preflight and --update-evaluator")
        if any(getattr(args, name) is not None for name in ("confidence", "result", "missing", "gaps")):
            parser.error("--from-file cannot go with --confidence, --result, --missing or --gaps")
        required = tuple(name for name in required if name not in ("confidence", "result"))
    for name in required:
        if getattr(args, name) is None:
            parser.error(f"--{name.replace('_', '-')} is required for this command")

    try:
        print(handler(args, Path(SP_TMP_DIR)))
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
