# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Session manager — session.json and .done flag file helpers.

All run signaling is file-based: a domain agent writes a .done flag file when
it finishes, and the skill reads the flag files.

Command line:
  session_manager.py new <parent_dir> <domain...>
  session_manager.py create <session_id> <output_dir> <domain...>
  session_manager.py done <output_dir> <slug>
  session_manager.py all-done <output_dir> <slug...>
  session_manager.py has-files <output_dir> <file...>
  session_manager.py keep-prev <output_dir> <file...>
The command new makes a session id, makes the session in <parent_dir>/<id>, and
prints only the id. It exits 1 when it cannot make the folder.
The command all-done exits 0 when every slug has a flag. Else it prints the
missing slugs and exits 1. The command has-files does the same for output
files. A skill decides that a run is done with these 2 commands, and not with
the DONE line of an agent, which is a second sign.
The command keep-prev renames each file that exists in <output_dir> to
<stem>.prev<suffix>, and replaces an old .prev file. It exits 1 when a name is
not a plain file name, or when <output_dir> is not a folder in .data-strategy-tmp
of the current folder.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def create_session(session_dir: Path, session_id: str, domains: list[str]) -> None:
    """Write session.json. Raises FileExistsError if already exists."""
    path = Path(session_dir) / "session.json"
    if path.exists():
        raise FileExistsError(f"Session already exists at {path}")

    data = {
        "session_id": session_id,
        "domains_detected": domains,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def read_session(session_dir: Path) -> dict:
    """Read session.json. Raises FileNotFoundError if missing."""
    path = Path(session_dir) / "session.json"
    if not path.exists():
        raise FileNotFoundError(f"No session.json in {session_dir}")
    return json.loads(path.read_text())


def write_done_flag(session_dir: Path, slug: str) -> None:
    """Write a .done flag file for a domain slug."""
    flag = Path(session_dir) / f"{slug}.done"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text(slug)


def check_done_flag(session_dir: Path, slug: str) -> bool:
    """Return True if a .done flag exists for the given slug."""
    return (Path(session_dir) / f"{slug}.done").exists()


def all_done(session_dir: Path, slugs: list[str]) -> bool:
    """Return True when every slug in the list has a .done flag."""
    return all(check_done_flag(session_dir, slug) for slug in slugs)


def missing_files(session_dir: Path, names: list[str]) -> list[str]:
    """Return the names that are not files in the session folder."""
    return [name for name in names if not (Path(session_dir) / name).is_file()]


def keep_prev(session_dir: Path, names: list[str]) -> list[str]:
    """Rename each file that exists to <stem>.prev<suffix>. Return the names that were renamed."""
    renamed = []
    for name in names:
        path = Path(session_dir) / name
        if path.is_file():
            path.replace(path.with_name(f"{path.stem}.prev{path.suffix}"))
            renamed.append(name)
    return renamed


USAGE = (
    "Usage: session_manager.py new <parent_dir> <domain...>\n"
    "       session_manager.py create <session_id> <output_dir> <domain...>\n"
    "       session_manager.py done <output_dir> <slug>\n"
    "       session_manager.py all-done <output_dir> <slug...>\n"
    "       session_manager.py has-files <output_dir> <file...>\n"
    "       session_manager.py keep-prev <output_dir> <file...>"
)


def main(argv: list[str]) -> int:
    command, args = (argv[1], argv[2:]) if len(argv) > 1 else ("", [])
    if command == "new" and len(args) >= 2:
        parent, *domains = args
        session_id = uuid.uuid4().hex[:8]
        try:
            create_session(Path(parent) / session_id, session_id, domains)
        except OSError as exc:
            print(f"session_manager.py: {exc}", file=sys.stderr)
            return 1
        print(session_id)
        return 0
    if command == "create" and len(args) >= 3:
        session_id, out, *domains = args
        try:
            create_session(Path(out), session_id, domains)
        except FileExistsError as exc:
            print(f"session_manager.py: {exc}", file=sys.stderr)
            return 1
        print(f"Session {session_id} created at {out}")
        return 0
    if command == "done" and len(args) == 2:
        write_done_flag(Path(args[0]), args[1])
        print(f"Flag {args[1]}.done written in {args[0]}")
        return 0
    if command == "all-done" and len(args) >= 2:
        out, *slugs = args
        missing = [s for s in slugs if not check_done_flag(Path(out), s)]
        if missing:
            print("Missing .done flags: " + ", ".join(missing))
            return 1
        print("All .done flags present")
        return 0
    if command == "has-files" and len(args) >= 2:
        out, *names = args
        missing = missing_files(Path(out), names)
        if missing:
            print("Missing files: " + ", ".join(missing))
            return 1
        print("All files present")
        return 0
    if command == "keep-prev" and len(args) >= 2:
        out, *names = args
        bad = [n for n in names if n in (".", "..") or n != Path(n).name]
        if bad:
            print("Not a plain file name: " + ", ".join(bad), file=sys.stderr)
            return 1
        if Path(out).resolve().parent != Path.cwd().resolve() / ".data-strategy-tmp":
            print(f"Not a session folder in .data-strategy-tmp: {out}", file=sys.stderr)
            return 1
        try:
            renamed = keep_prev(Path(out), names)
        except OSError as exc:
            print(f"session_manager.py: {exc}", file=sys.stderr)
            return 1
        print("Renamed: " + (", ".join(renamed) or "none"))
        return 0
    print(USAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
