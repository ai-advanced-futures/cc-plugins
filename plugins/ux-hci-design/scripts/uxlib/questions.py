"""Remove the open-questions file of an agent before the skill starts the agent again.

The skill ux-design runs this through ux_graph.py, because its allowed-tools
approve ux_graph.py and approve no `rm` (STORY-136, STORY-343).
"""
from __future__ import annotations

from pathlib import Path

from uxlib import DataError, UsageError
from uxlib.bundle import shown

QUESTIONS_FILE = "open-questions.md"
REVIEWERS = ("accessibility-reviewer", "usability-reviewer", "ai-hci-reviewer")


def path_of(root, output, reviewer=None) -> Path:
    """The open-questions file of the run, or of 1 reviewer, inside the output folder."""
    from uxlib.ingest import output_folder

    root = Path(root).resolve()
    folder = output_folder(root, output)
    if reviewer is None:
        return folder / QUESTIONS_FILE
    if reviewer not in REVIEWERS:
        raise UsageError(f"{reviewer!r} is not a reviewer: use {', '.join(REVIEWERS)}")
    base = folder / "reviews" / reviewer
    if base.exists() and base.resolve() != base:
        raise UsageError(f"{shown(root, base)} is a symbolic link, or is in one: remove the file yourself")
    return base / QUESTIONS_FILE


def remove(root, output, reviewer=None) -> str:
    root = Path(root).resolve()
    target = path_of(root, output, reviewer)
    if target.is_symlink():
        raise DataError(f"{shown(root, target)} is a symbolic link: remove it yourself")
    if not target.exists():
        return f"no file {shown(root, target)}"
    if not target.is_file():
        raise DataError(f"{shown(root, target)} is not a file: remove it yourself")
    target.unlink()
    return f"removed {shown(root, target)}"
