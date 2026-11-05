"""The one way this script runs git.

Six call sites ran their own `subprocess.run(["git", ...])`, and they did not
agree on what a missing git means: four caught OSError and two did not, so on
a machine with no git one rule raised a traceback and the rest returned a
verdict. `run` gives every caller the same answer, and `output` gives the
common "the stdout of a command that succeeded, else None" shape.

A command that fails is not an error here. git is absent, the directory is
not a repository, or the repository has no commit yet; each caller decides
what that means for its own rule.
"""
import subprocess
from pathlib import Path


def run(root: Path, *arguments) -> subprocess.CompletedProcess | None:
    """One git command in `root`. None when git is not on PATH."""
    try:
        return subprocess.run(["git", *arguments], cwd=str(root),
                              capture_output=True, text=True)
    except OSError:
        return None


def ok(root: Path, *arguments) -> bool:
    """True when the command ran and succeeded."""
    result = run(root, *arguments)
    return result is not None and result.returncode == 0


def output(root: Path, *arguments) -> str | None:
    """The stripped stdout of a command that succeeded, else None."""
    result = run(root, *arguments)
    if result is None or result.returncode != 0:
        return None
    return result.stdout.strip()


def is_repository(root: Path) -> bool:
    return output(root, "rev-parse", "--is-inside-work-tree") == "true"
