"""`prd.py new`: assign the ID under the lock and write the page."""
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import DataError, UsageError
from .graph import FIELD_TARGETS, check_targets, target_path
from .hashing import body_hash
from .ids import new_run_id, next_id
from .lock import write_lock
from .logbook import timestamp
from .page import Page, load_page, load_set_value, normalise, write_page
from .registry import TYPES, WORK_ITEMS
from .schema import is_single_valued, plugin_actor, validate_frontmatter
from .tree import bundle_dir

# A new item starts in backlog. Only prd.py state sets `state`. Only regen and
# drift write the other three: --set must not give them a second write path.
REFUSED_SET_FIELDS = ("state", "actual_start_date", "actual_end_date",
                      "drifted")
# includes needs a {to, priority} mapping and traces needs a hash. --link
# writes a plain string, so it must send the caller to the option that
# builds the right shape instead of writing one that check would reject.
REFUSED_LINK_FIELDS = {
    "includes": "--set includes=[{to: TARGET, priority: must|should|could|wont}]",
    "traces": "--traces TARGET",
}


def trace_entry(root: Path, target: str) -> dict:
    path = target_path(root, "roadmap", target)
    if not path.is_file():
        raise DataError(f"the trace target {target} does not exist")
    return {"to": target, "hash": body_hash(load_page(path).body, path.stem)}


def create(root: Path, type_name: str, title: str, description: str,
           status: str | None = None, body: str | None = None,
           traces: list[str] | None = None,
           links: list[str] | None = None,
           sets: list[str] | None = None,
           actor: str | None = None) -> Path:
    if type_name not in TYPES:
        raise DataError(f"{type_name} is not a page type")
    spec = TYPES[type_name]
    if spec.prefix is None:
        raise DataError(f"a {type_name} page has no ID, so `new` cannot make one")

    frontmatter = {"type": type_name, "title": title,
                   "description": description, "status": status or "draft"}
    if type_name in WORK_ITEMS:
        frontmatter["state"] = "backlog"

    written = []
    # Every value is built before the lock and before the first write, so a
    # missing trace target leaves the repository with no change.
    for item in links or []:
        field, _, target = item.partition("=")
        if field in REFUSED_LINK_FIELDS:
            raise UsageError(
                f"--link cannot write {field}. Use "
                f"{REFUSED_LINK_FIELDS[field]}.")
        # A single-valued slot stores the target itself, not a one-item list.
        # A list there crashes the index writer, which calls `lstrip` on the
        # value, and defeats every `parent == own` test. The schema is what
        # says which slots those are, so a slot added to the schema cannot end
        # up on the wrong side of a hand-kept set here.
        if is_single_valued(type_name, field):
            if field in frontmatter:
                raise DataError(
                    f"{field} holds one target, so --link {field}= cannot be "
                    "given twice")
            frontmatter[field] = target
        else:
            frontmatter.setdefault(field, []).append(target)
        written.append(field)
    for item in sets or []:
        if "=" not in item:
            raise UsageError(f"--set {item} has no `=`. Use --set FIELD=YAML.")
        field, _, raw = item.partition("=")
        if field in REFUSED_SET_FIELDS:
            raise UsageError(
                f"--set cannot write {field}. A new item starts in backlog. "
                f"Only prd.py state, prd.py regen, and prd.py drift write it.")
        try:
            frontmatter[field] = normalise(load_set_value(raw))
        except yaml.YAMLError as error:
            raise UsageError(f"--set {item} does not parse: {error}")
        written.append(field)
    if traces:
        frontmatter["traces"] = [trace_entry(root, t) for t in traces]

    frontmatter["generated"] = {"by": actor or plugin_actor(),
                                "at": timestamp(datetime.now(timezone.utc))}

    # The same check that rule E2 runs, before the ID is assigned and before
    # the lock: a page that check would refuse must not be written at all.
    errors = validate_frontmatter(type_name, frontmatter)
    if errors:
        raise DataError(
            "the new page fails the schema:\n" + "\n".join(errors))
    # The E4 texts of `check` for each link field that this call writes
    # (row 8 of the spec of FEATURE-31): a target that does not exist, or of
    # a type that the field refuses, writes no file and takes no ID. It runs
    # after the schema check, so a target in a wrong form gets the text of
    # the schema and not "does not exist".
    check_targets(root, spec.bundle, frontmatter,
                  [f for f in written if f in FIELD_TARGETS])

    with write_lock(root):
        # A Run ID is a time and a token, never a number: two agents with no
        # lock between clones must not get the same one. registry.RUN_ID_RE
        # rejects the counted shape, so `new Run` cannot use next_id.
        page_id = new_run_id() if type_name == "Run" \
            else next_id(root, type_name)
        path = bundle_dir(root, spec.bundle) / spec.directory / f"{page_id}.md"
        text = body or description
        page = Page(path=path, frontmatter=frontmatter,
                    body=f"\n# {page_id}: {title}\n\n{text}\n")
        write_page(page)
    # A bundle from an older release has no `experiences` in `id_folders`, so
    # the first page of a new folder would fail K-id (row 9 of the spec).
    from . import standard  # local import: standard imports regen
    standard.refresh_id_folders(root, spec.bundle)
    return path
