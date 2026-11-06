# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
JTBD session state management — file-based I/O for orchestrator pattern.

Keeps orchestrator context window lean by persisting all phase data to disk.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASE_NAMES = {
    1: "1_job_identification",
    2: "2_job_decomposition",
    3: "3_need_generation",
    4: "4_effort_quantification",
    5: "5_survey_design",
    6: "6_opportunity_scoring",
    7: "7_evc_calculation",
    8: "8_segmentation",
    9: "9_wtp_validation",
    10: "10_output_generation",
}


NEW_ROOT = ".jtbd-market-discovery"
OLD_ROOT = ".jtbd"
FINAL_PHASE = PHASE_NAMES[10]


def get_default_session_dir() -> Path:
    """Return .jtbd-market-discovery/{timestamp} relative to cwd."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Path(NEW_ROOT) / ts


def create_session(
    session_dir: Path, run_id: str | None = None, case: str | None = None
) -> dict:
    """Create a new session state and write state.json."""
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "session_id": session_dir.name,
        "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "case": case,
        "current_phase": 0,
        "phases": {
            name: {"status": "pending"}
            for name in PHASE_NAMES.values()
        },
    }
    _write_state(state, session_dir)
    return state


def _started_at(state: dict) -> datetime | None:
    """Parse started_at ("+00:00" or "Z"); None when it is absent or unreadable."""
    raw = state.get("started_at")
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _newest_plain_session(root: Path, needs: tuple[str, ...] = ()) -> Path | None:
    """Newest person's session in `root` (no run_id and no case) that holds each file in
    `needs`, by started_at; never by folder name. A session with a case is a coach run's."""
    best: tuple[datetime, Path] | None = None
    if not root.is_dir():
        return None
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        try:
            state = load_session(folder)
        except RuntimeError:
            continue
        if state is None or state.get("run_id") is not None or state.get("case") is not None:
            continue
        if not all((folder / name).is_file() for name in needs):
            continue
        started = _started_at(state)
        if started is not None and (best is None or started > best[0]):
            best = (started, folder)
    return best[1] if best else None


def latest_session_dir(base: Path = Path(".")) -> Path | None:
    """Newest person's session (no run_id, no case): under NEW_ROOT first, then OLD_ROOT."""
    base = Path(base)
    return _newest_plain_session(base / NEW_ROOT) or _newest_plain_session(base / OLD_ROOT)


def finished_session_dir(base: Path = Path(".")) -> Path | None:
    """Newest session without a run_id whose discover run wrote p7.json and p8.json."""
    base = Path(base)
    needs = ("p7.json", "p8.json")
    return _newest_plain_session(base / NEW_ROOT, needs) or _newest_plain_session(base / OLD_ROOT, needs)


def new_wtp_folder(base: Path = Path(".")) -> Path:
    """A new, empty folder for a person's wtp-check run. It has no state.json, so no session
    lookup ever resumes it."""
    stem = Path(base) / NEW_ROOT / ("wtp-check-" + get_default_session_dir().name)
    folder, n = stem, 1
    while folder.exists():
        n += 1
        folder = stem.with_name("%s-%d" % (stem.name, n))
    folder.mkdir(parents=True)
    return folder


def _is_unfinished(session_dir: Path) -> bool:
    state = load_session(session_dir)
    return (
        state is not None
        and (state.get("phases") or {}).get(FINAL_PHASE, {}).get("status") != "complete"
    )


def select_session_dir(base: Path, run_id: str | None, case: str | None = None) -> Path:
    """Pick the session for this run. `base` is the git root of the run's working directory.

    With a run_id: base/NEW_ROOT/<run_id>, created when absent and reused only when its
    state.json holds the same run_id. It never returns another session.
    Without one: the latest person's session (no run_id, no case) when it is unfinished,
    else a new one under NEW_ROOT. It never resumes a session that has a case.
    """
    base = Path(base)
    if run_id is None:
        latest = latest_session_dir(base)
        if latest is not None and _is_unfinished(latest):
            return latest
        folder = base / get_default_session_dir()
        create_session(folder)
        return folder
    if not run_id or run_id in (".", "..") or "/" in run_id or "\\" in run_id:
        raise ValueError(f"run_id {run_id!r} is not a folder name")
    folder = base / NEW_ROOT / run_id
    state = load_session(folder)
    if state is None:
        create_session(folder, run_id, case)
    elif state.get("run_id") != run_id:
        raise ValueError(
            f"{folder} belongs to run_id {state.get('run_id')!r}, not {run_id!r}"
        )
    return folder


def load_session(session_dir: Path) -> dict | None:
    """Load existing state.json or return None."""
    path = Path(session_dir) / "state.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Corrupt state.json in {session_dir}: {e}") from e


def mark_phase_complete(phase: int, session_dir: Path) -> None:
    """Mark phase as complete and advance current_phase."""
    if phase not in PHASE_NAMES:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-10.")
    session_dir = Path(session_dir)
    state = load_session(session_dir)
    if state is None:
        raise RuntimeError(f"No session state found in {session_dir}")
    phase_key = PHASE_NAMES[phase]
    state["phases"][phase_key]["status"] = "complete"
    state["phases"][phase_key]["completed_at"] = datetime.now(timezone.utc).isoformat()
    state["current_phase"] = min(phase + 1, 10)
    _write_state(state, session_dir)


def is_phase_complete(phase: int, session_dir: Path) -> bool:
    """Return True if phase is marked complete."""
    if phase not in PHASE_NAMES:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-10.")
    state = load_session(Path(session_dir))
    if state is None:
        return False
    return state["phases"][PHASE_NAMES[phase]]["status"] == "complete"


def write_phase_output(phase: int, data: dict, session_dir: Path) -> None:
    """Write phase output to pN.json (atomic write)."""
    if phase not in PHASE_NAMES:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-10.")
    path = Path(session_dir) / f"p{phase}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(path)


def read_phase_output(phase: int, session_dir: Path) -> dict | None:
    """Read phase output from pN.json or return None."""
    if phase not in PHASE_NAMES:
        raise ValueError(f"Invalid phase: {phase}. Must be 1-10.")
    path = Path(session_dir) / f"p{phase}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _write_state(state: dict, session_dir: Path) -> None:
    path = Path(session_dir) / "state.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(path)


def main(argv: list[str] | None = None) -> int:
    """`select --base <git root> [--run-id X] [--case Y]`: print the absolute session_dir.
    `latest --base <git root>`: print the newest session without a run_id; exit 1 when none.
    `finished --base <git root>`: print the newest session without a run_id that holds p7.json
    and p8.json; exit 1 when none.
    `wtp-folder --base <git root>`: make and print a new folder for a person's wtp-check run.
    `now`: print the UTC time to the second, as `YYYY-MM-DDTHH:MM:SSZ`."""
    parser = argparse.ArgumentParser(prog="jtbd_state.py")
    sub = parser.add_subparsers(dest="command", required=True)
    pick = sub.add_parser("select", help="print the session folder for this run")
    pick.add_argument("--base", required=True, type=Path)
    pick.add_argument("--run-id", default=None)
    pick.add_argument("--case", default=None)
    newest = sub.add_parser("latest", help="print the newest session without a run_id")
    newest.add_argument("--base", required=True, type=Path)
    done = sub.add_parser("finished", help="print the newest session with p7.json and p8.json")
    done.add_argument("--base", required=True, type=Path)
    own = sub.add_parser("wtp-folder", help="make a new folder for a person's wtp-check run")
    own.add_argument("--base", required=True, type=Path)
    sub.add_parser("now", help="print the UTC time to the second")
    args = parser.parse_args(argv)
    if args.command == "now":
        print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        return 0
    if args.command == "finished":
        folder = finished_session_dir(args.base)
        if folder is None:
            print(f"jtbd_state.py: no finished session under {args.base}", file=sys.stderr)
            return 1
        print(folder.resolve())
        return 0
    if args.command == "wtp-folder":
        print(new_wtp_folder(args.base).resolve())
        return 0
    if args.command == "latest":
        folder = latest_session_dir(args.base)
        if folder is None:
            print(f"jtbd_state.py: no session under {args.base}", file=sys.stderr)
            return 1
        print(folder.resolve())
        return 0
    try:
        folder = select_session_dir(args.base, args.run_id, args.case)
    except ValueError as err:
        print(f"jtbd_state.py: {err}", file=sys.stderr)
        return 1
    print(folder.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
