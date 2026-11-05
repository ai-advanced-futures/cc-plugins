"""The check runner of `prd.py run-checks`.

A check is an argv list, not a string: the script never starts a shell. Only
a `human:` actor declares one, and rule E8 enforces it, because a check runs
code on the machine of the user. This is a convention that the checker
enforces. It is not a security boundary: a person who can write the file can
write the field.
"""
import subprocess
from pathlib import Path

from . import DataError, git
from .graph import own_target
from .ids import resolve
from .page import load_page
from .regen import collect
from .registry import WORK_ITEMS

NOT_CHECKED = "not-checked"
# The codes a shell uses, so a reader of the Run page knows them.
MISSING_PROGRAM = 127
TIMED_OUT = 124
TIMEOUT_SECONDS = 600


def criteria_of(root: Path, identifier: str) -> list[Path]:
    """Each AcceptanceCriterion page whose `item` points at this work item."""
    path = resolve(root, identifier)
    page = load_page(path)
    if page.type not in WORK_ITEMS:
        raise DataError(f"{path.stem} is a {page.type}, which has no criteria")
    target = own_target(root, path)
    return sorted(candidate for candidate, _frontmatter
                  in _criteria_with_frontmatter(root, target))


def _criteria_with_frontmatter(root: Path, target: str):
    """(path, frontmatter) of each criterion of one item.

    The frontmatter comes from the same read that found the page, so the
    caller does not load each page a second time.
    """
    return [(candidate, frontmatter)
            for candidate, (_bundle, frontmatter, _body)
            in collect(root).items()
            if frontmatter.get("type") == "AcceptanceCriterion"
            and frontmatter.get("item") == target]


def run_one(root: Path, argv: list) -> tuple[int, str]:
    """The exit code and the output of one check."""
    try:
        result = subprocess.run([str(word) for word in argv], cwd=root,
                                capture_output=True, text=True,
                                timeout=TIMEOUT_SECONDS)
    except OSError as error:
        return MISSING_PROGRAM, f"{argv[0]}: {error}"
    except subprocess.TimeoutExpired:
        return TIMED_OUT, f"the check ran longer than {TIMEOUT_SECONDS} seconds"
    return result.returncode, result.stdout + result.stderr


def head_commit(root: Path) -> str | None:
    """The commit of the working tree, or None outside a git repository."""
    return git.output(root, "rev-parse", "HEAD")


def results_for(root: Path, identifier: str,
                commit: str | None = None) -> list[tuple[dict, str]]:
    """One (result, output) pair for each criterion, in ID order.

    A criterion with no check gets an entry with no `exit_code`: that entry
    is the not-checked result of the spec. `commit` is the commit of the
    working tree; a caller that already read it passes it here, so the
    function does not run `git rev-parse` once for each criterion.
    """
    path = resolve(root, identifier)
    page = load_page(path)
    if page.type not in WORK_ITEMS:
        raise DataError(f"{path.stem} is a {page.type}, which has no criteria")
    if commit is None:
        commit = head_commit(root)
    pairs = []
    for criterion, frontmatter in sorted(
            _criteria_with_frontmatter(root, own_target(root, path))):
        entry = {"criterion": own_target(root, criterion)}
        output = ""
        argv = frontmatter.get("check") or []
        if argv:
            entry["exit_code"], output = run_one(root, argv)
            if commit:
                entry["commit"] = commit
        pairs.append((entry, output))
    return pairs
