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


def run_folder(root, output) -> Path:
    """The output folder, only when it is a folder of a ux-design run (STORY-366).

    A folder of a run has the name `.ux-artifacts` after each link is followed, or holds the `pages.json` of
    a run. The skill writes in `<project>/.ux-artifacts`, and `<project>` can be a folder below the git root.
    So a folder of the person, such as `docs/`, or a link `.ux-artifacts -> docs`, is refused.
    """
    from uxlib.ingest import ARTIFACTS, PAGES_FILE, output_folder, read_pages_file

    root = Path(root).resolve()
    folder = output_folder(root, output)
    if folder.name == ARTIFACTS:
        return folder
    run_ref = None
    if not (folder / PAGES_FILE).is_symlink():
        try:
            run_ref, _ = read_pages_file(folder)
        except DataError:
            run_ref = None
    if run_ref is None:
        raise DataError(f"{shown(root, folder)} is not a folder of a ux-design run: its name is not {ARTIFACTS}, "
                        f"and it holds no pages.json of a run. Remove the file yourself")
    return folder


def path_of(root, output, reviewer=None) -> Path:
    """The open-questions file of the run, or of 1 reviewer, inside the output folder of a run."""
    root = Path(root).resolve()
    folder = run_folder(root, output)
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
