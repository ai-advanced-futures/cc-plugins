"""The change list of one run of the save code (standard section 9).

Each write or delete of a graph file calls `note`. At the end of a run, `flush`
appends the noted paths to `<git dir>/knowledge-changed`, one path for each line,
relative to the git root. The hook takes that file to find the pages that changed.
A run that noted no path still makes the file, empty. So a missing file tells the
hook that no run wrote a list, and the hook then checks everything.
`KNOWLEDGE_NO_CHANGE_LIST=1` turns the list off. The hook sets it for each step it runs.
Outside a git repository there is no list and no error. When the list cannot be
written, `flush` prints one WARN line on stderr, and the exit code does not change.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

NAME = "knowledge-changed"
SWITCH = "KNOWLEDGE_NO_CHANGE_LIST"

_noted: set[Path] = set()


def note(path) -> None:
    _noted.add(Path(path).absolute())


def flush(root) -> None:
    """Append the noted paths to the change list (an empty list when none), then forget them."""
    paths = sorted(_noted)
    _noted.clear()
    if os.environ.get(SWITCH):
        return
    try:
        found = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir", "--show-toplevel"],
                               capture_output=True, text=True, check=True).stdout.splitlines()
        git_dir, top = Path(found[0]), Path(found[1]).resolve()
        lines = []
        for path in paths:
            try:
                lines.append(path.parent.resolve().joinpath(path.name).relative_to(top).as_posix())
            except ValueError:
                continue
        with open(git_dir / NAME, "a", encoding="utf-8") as handle:
            if lines:
                handle.write("\n".join(lines) + "\n")
    except subprocess.CalledProcessError:
        return  # not a git repository: no list and no error
    except (OSError, IndexError) as error:
        print(f"WARN: the change list was not written ({error}). The hook checks every page.", file=sys.stderr)
