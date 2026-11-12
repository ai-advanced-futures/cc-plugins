"""Step 4 of the migration: the hashes, last.

Step 3 is the skill and the user: they write a better title, a description,
the missing `kind` and `role` values, and the text in Google style. Each of
those changes the body, so a hash stored at step 2 would be false at step 3.
The hash is therefore stored here, after the human work.
"""
from datetime import datetime, timezone
from pathlib import Path


from . import UsageError
from .check import report
from .check import run as check_run
from .graph import target_path
from .hashing import body_hash
from .lock import write_lock
from .logbook import append_entry, entry_line
from .page import load_page, safe_load, write_page
from .regen import require_readable
from .regen import write_locked
from .tree import BUNDLES, bundle_dir, iter_pages, product_dir

DRIFT_RECORD = "archive/migrate-drift.yaml"
# The actor of the two log lines. The migration is a decision of a person,
# so it is not a `system:` actor.
ACTOR = "human:migrate"
# The page each log line names: the root page of its bundle.
LOG_SUBJECT = {"prd": ("product", "product.md"),
               "roadmap": ("PROJECT-01", "projects/PROJECT-01.md")}


def _entries(root: Path) -> list[dict]:
    """The drift record of step 2. Absent, the user skipped the main run."""
    record = product_dir(root) / DRIFT_RECORD
    if not record.is_file():
        raise UsageError(
            f"{DRIFT_RECORD} is absent. Run `prd.py migrate` first.")
    entries = safe_load(record.read_text(encoding="utf-8")) or []
    return [entry for entry in entries if isinstance(entry, dict)]


def _was_drifted(entries: list[dict], item: str, target: str) -> bool:
    """The verdict of the v3 drift check for one trace. A trace that the
    record does not name was not drifted: the record holds every trace of the
    v3 roadmap, so a trace that is absent from it came from step 3."""
    return any(entry.get("item") == item and entry.get("to") == target
               and entry.get("drifted") for entry in entries)


def _items_with_traces(root: Path):
    """(bundle, page) for each page that holds a `traces` list."""
    for bundle in BUNDLES:
        base = bundle_dir(root, bundle)
        if not base.is_dir():
            continue
        for path in iter_pages(base):
            page = load_page(path)
            if page.frontmatter.get("traces"):
                yield bundle, page


def finish(root: Path) -> int:
    """Take the lock, then store the hashes (`_finish`)."""
    with write_lock(root):
        return _finish(root)


def _finish(root: Path) -> int:
    """`finish` with the lock held by the caller. The read of the drift record
    and of the tree, the hashes, the 2 `Migrate` lines and the regen are
    inside 1 lock (STORY-441)."""
    entries = _entries(root)
    # A page the reader cannot use holds traces this step must store a hash
    # for, so it exits 1 here instead of skipping the page in silence.
    require_readable(root)
    for bundle, page in _items_with_traces(root):
        drifted = []
        for trace in page.frontmatter["traces"]:
            # Both keys are new IDs: the main run wrote the record
            # through the ID map, so no translation happens here.
            was_drifted = _was_drifted(entries, page.id, trace.get("to"))
            target = target_path(root, bundle, trace.get("to", ""))
            if was_drifted or not target.is_file():
                drifted.append(trace["to"])
                continue
            trace["hash"] = body_hash(load_page(target).body, target.stem)
        if drifted:
            page.frontmatter["drifted"] = drifted
        write_page(page)
    now = datetime.now(timezone.utc)
    for bundle in BUNDLES:
        page_id, link = LOG_SUBJECT[bundle]
        append_entry(bundle_dir(root, bundle) / "log.md",
                     entry_line("Migrate", page_id, link,
                                "the v3 files became this bundle", ACTOR, now),
                     now)
    write_locked(root)
    # The findings of `check` are printed, and they do not become the exit
    # code: a tree that was migrated one minute ago always holds E2 errors,
    # because `kind`, `role` and `addresses` are step 3 work that the script
    # does not guess.
    report(check_run(root, BUNDLES), strict=False, fmt="text")
    print("the hashes are stored. Next: fix each finding above, then run "
          "`prd.py check` until it is clean.")
    return 0
