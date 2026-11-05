# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
session_paths.py — Session directory lifecycle for grounded-synthesis.

Architecture (§2.5.7):
  Session directories are user-home-rooted to avoid polluting project repos.
  Base location: ${GROUNDED_SYNTHESIS_HOME:-$HOME/.cache/grounded-synthesis-sessions}

  resolver   — resolve_session_dir(session_id) → absolute Path (pure, no mkdir)
  sweeper    — sweep_old_sessions(days=30) → int (deletes subdirs older than days)

Used by: grounded-synthesis-orchestrator (via Bash CLI mode)
Replaces logic that would otherwise live in orchestrator agent prose.

Session directory location:
  ${GROUNDED_SYNTHESIS_HOME:-$HOME/.cache/grounded-synthesis-sessions}/{session_id}/

The directory is user-home-rooted (NOT cwd-rooted) to avoid polluting project repos.
Override via the GROUNDED_SYNTHESIS_HOME environment variable.

Lifecycle:
  1. Orchestrator calls sweep_old_sessions(days=30) at startup to prune sessions
     older than 30 days (based on mtime of session directory).
  2. Orchestrator calls resolve_session_dir(session_id) to get the absolute path
     for the new session.
  3. Orchestrator creates the directory with Path(absolute_path).mkdir(parents=True, exist_ok=True).
  4. Sub-agents receive the absolute session_dir_absolute via dispatch context —
     they never resolve env vars themselves.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
import time
import uuid
from pathlib import Path

DEFAULT_SUBPATH = ".cache/grounded-synthesis-sessions"


def _get_base() -> Path:
    """Return the base session directory, honouring GROUNDED_SYNTHESIS_HOME.

    Refuses a base that is relative, is the root folder, or is the home folder.
    """
    override = os.environ.get("GROUNDED_SYNTHESIS_HOME")
    base = Path(override) if override else Path.home() / DEFAULT_SUBPATH
    if not base.is_absolute():
        raise ValueError(f"session base must be an absolute path: {base}")
    resolved = base.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError(f"session base must not be the root or the home folder: {resolved}")
    return base


def _is_uuid4(name: str) -> bool:
    """True if `name` is the canonical text of a uuid4."""
    try:
        value = uuid.UUID(name)
    except ValueError:
        return False
    return value.version == 4 and str(value) == name


def resolve_session_dir(session_id: str) -> Path:
    """Resolve the absolute session directory path for a given session_id.

    Reads GROUNDED_SYNTHESIS_HOME env var; falls back to
    $HOME/.cache/grounded-synthesis-sessions/{session_id}.

    Returns an absolute Path. Does NOT create the directory.
    Raises ValueError if the result is not a direct child of the base folder.
    """
    base = _get_base().resolve()
    session_dir = (base / session_id).resolve()
    if session_dir.parent != base:
        raise ValueError(f"session id leaves the session base folder: {session_id!r}")
    return session_dir


def sweep_old_sessions(days: int = 30) -> int:
    """Remove session directories older than `days` days.

    Scans the parent session directory (GROUNDED_SYNTHESIS_HOME or default).
    Removes subdirectories whose mtime is older than `days` days and whose name
    is a uuid4. Skips regular files, symbolic links, and any other name.

    Returns the count of directories removed.
    Does not raise if the parent directory does not exist yet.
    Raises ValueError if `days` is less than 1.
    """
    if days < 1:
        raise ValueError(f"sweep days must be 1 or more, got {days}")
    base = _get_base()
    if not base.exists():
        return 0
    threshold = time.time() - days * 86400
    deleted = 0
    for child in base.iterdir():
        if child.is_symlink() or not _is_uuid4(child.name):
            continue
        st = child.lstat()
        if not stat.S_ISDIR(st.st_mode):
            continue
        if st.st_mtime < threshold:
            shutil.rmtree(child)
            deleted += 1
    return deleted


if __name__ == "__main__":
    # CLI mode: uv run ${CLAUDE_PLUGIN_ROOT}/lib/session_paths.py --resolve <session_id> [--sweep-days N]
    # With --sweep-days, first delete session folders older than N days.
    # Then make the session folder and print its absolute path to stdout.
    parser = argparse.ArgumentParser(
        description="Resolve the absolute session directory path for a given session_id."
    )
    parser.add_argument(
        "--resolve",
        metavar="SESSION_ID",
        required=True,
        help="Session ID to resolve to an absolute directory path.",
    )
    parser.add_argument(
        "--sweep-days",
        metavar="N",
        type=int,
        default=None,
        help="Before the resolve, delete session folders older than N days.",
    )
    args = parser.parse_args()
    try:
        if args.sweep_days is not None:
            sweep_old_sessions(days=args.sweep_days)
        session_dir = resolve_session_dir(args.resolve)
    except ValueError as exc:
        print(f"session_paths: {exc}", file=sys.stderr)
        sys.exit(2)
    session_dir.mkdir(parents=True, exist_ok=True)
    print(str(session_dir))
    sys.exit(0)
