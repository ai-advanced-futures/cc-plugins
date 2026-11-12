"""The Run page: one execution of the declared checks of one work item.

A Run is written one time and is then read-only. Rule E9 reports a later
change to a Run that git tracks.
"""
from datetime import datetime, timezone
from pathlib import Path

from . import DataError, UsageError
from .checks import NOT_CHECKED, head_commit, results_for
from .ghmodel import page_id_of
from .graph import own_target
from .ids import new_run_id, resolve
from .lock import write_lock
from .logbook import append_entry, entry_line, timestamp
from .page import Page, write_page
from .regen import write as regen_write  # [inferred]
from .schema import validate_frontmatter
from .statecmd import require_actor
from .textsafe import escape_controls
from .tree import bundle_dir

PASSED = "passed"
FAILED = "failed"


def _body(page_id: str, title: str, item_id: str, results: list[dict]) -> str:
    lines = [f"\n# {page_id}: {title}\n"]
    if not results:
        lines.append(f"{item_id} has no acceptance criterion.\n")
        return "\n".join(lines)
    lines += [f"The declared checks of {item_id}.\n",
              "| Criterion | Exit code |", "|---|---|"]
    for entry in results:
        code = entry.get("exit_code")
        lines.append(f"| {page_id_of(entry['criterion'])} | "
                     f"{NOT_CHECKED if code is None else code} |")
    return "\n".join(lines) + "\n"


def failure_text(entry: dict, output: str) -> str:
    """The text of one failed check: the criterion and the exit code, a line
    break, then the output of the check."""
    return (f"{escape_controls(page_id_of(entry['criterion']))} exited "
            f"{entry['exit_code']}\n{output}")


def run_checks(root: Path, identifier: str, actor: str,
               spec: str | None = None, pull_request: str | None = None,
               now: datetime | None = None) -> tuple[Path, str, list[str]]:
    """Run each declared check, then write one Run page and one Run Event.

    The checks run before the lock is taken. A check can run for minutes and
    a lock older than 60 seconds is stale, so a lock held across the checks
    is deleted under its own writer.

    The run regenerates the bundle after it writes the page. regen owns a
    LINKS block on each page that holds a relationship field, and `Run.item`
    is one, so a run that writes the page alone leaves the Run, the two
    indexes, and the target item stale, and `check` exits 1 with E10. The
    regen also gives the new Run its LINKS block before the page reaches a
    commit, so a later regen changes no Run page and rule E9 stays quiet.
    [inferred]
    """
    require_actor(actor)
    item = resolve(root, identifier)
    started = now or datetime.now(timezone.utc)
    commit = head_commit(root)
    pairs = results_for(root, identifier, commit)
    results = [entry for entry, _output in pairs]
    failures = [failure_text(entry, output)
                for entry, output in pairs if entry.get("exit_code", 0) != 0]
    ended = started if now else datetime.now(timezone.utc)
    # A run in which no check ran tested nothing, so it did not pass. It is
    # no failure either: the exit code stays 0, and a person reads the page.
    ran = [entry for entry in results if entry.get("exit_code") is not None]
    if failures:
        outcome = FAILED
    elif ran:
        outcome = PASSED
    else:
        outcome = NOT_CHECKED
    if outcome == NOT_CHECKED:
        description = (f"No declared check of {item.stem} ran at "
                       f"{timestamp(ended)}.")
    else:
        description = (f"The declared checks of {item.stem} ran at "
                       f"{timestamp(ended)} and {outcome}.")

    frontmatter = {
        "type": "Run",
        "title": f"Checks of {item.stem}",
        "description": description,
        "status": "stable",
        "item": own_target(root, item),
        "agent": actor,
        "started_at": timestamp(started),
        "ended_at": timestamp(ended),
        "outcome": outcome,
        "results": results,
    }
    for key, value in (("spec", spec), ("pull_request", pull_request),
                       ("commit", commit)):
        if value:
            frontmatter[key] = value
    # The same check rule E2 runs, before the page is written: a Run the
    # checker would refuse must never reach the disk.
    errors = validate_frontmatter("Run", frontmatter)
    if errors:
        raise DataError("the Run page fails the schema:\n" + "\n".join(errors))

    bundle_root = bundle_dir(root, "roadmap")
    with write_lock(root):
        page_id = new_run_id(ended)
        path = bundle_root / "runs" / f"{page_id}.md"
        write_page(Page(path=path, frontmatter=frontmatter,
                        body=_body(page_id, frontmatter["title"], item.stem,
                                   results)))
        append_entry(
            bundle_root / "log.md",
            entry_line("Run", page_id,
                       str(path.relative_to(bundle_root)),
                       f"{outcome}, {len(results)} criteria", actor, ended),
            ended)
    # regen takes the same lock, so it runs after this one is given back.
    # [inferred]
    regen_write(root)
    return path, outcome, failures
