"""`prd.py regen`: every generated thing in the two bundles.

plan() gives the intended text of each file it owns. `regen` writes the files
that differ; `regen --check` writes nothing and names them. Rule E10 and
`regen --check` both call differences(), so the two verdicts agree.
"""
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import DataError
from . import linkstsv
from . import status as status_mod
from .indexes import by_parent, closed_index, directory_index, \
    root_index
from .links import END as LINKS_END, START as LINKS_START, block_for, \
    incoming_index, replace_block
from .lock import write_lock
from .logbook import append_entries, state_line
from .page import (Page, dump_page, normalise, safe_load,
                   split_frontmatter)
from .registry import CLOSED_STATES, DIRECTORY_ORDER, WORK_ITEMS, spec_for_path
from .status import END as STATUS_END, START as STATUS_START
from .tree import BUNDLES, bundle_dir, iter_pages

COMPUTED_STATES = ("ready", "blocked")
REGEN_ACTOR = "process:regen"
# The files regen owns whole. Every other planned path is a page whose
# frontmatter and prose belong to its author.
GENERATED_NAMES = ("index.md", "closed.md", "links.tsv")


def read_tree(root: Path) -> tuple[dict, list[Path]]:
    """One walk of both bundles: (pages, broken).

    pages maps an absolute path to (bundle, frontmatter, body) for each page
    the reader can use. broken holds each page it cannot: no frontmatter, a
    frontmatter that does not parse, one that is not a mapping, or one with no
    `type`. `check` reports each broken page as E1.

    The two answers come from one read of each file because every caller
    wants both: regen and drift stop on a broken page and then read the
    readable ones.
    """
    pages = {}
    broken = []
    for bundle in BUNDLES:
        base = bundle_dir(root, bundle)
        if not base.is_dir():
            continue
        for path in iter_pages(base):
            fm_text, body = split_frontmatter(path.read_text(encoding="utf-8"))
            if fm_text is None:
                broken.append(path)
                continue
            try:
                data = safe_load(fm_text)
            except yaml.YAMLError:
                broken.append(path)
                continue
            if not isinstance(data, dict):
                broken.append(path)
                continue
            frontmatter = normalise(data)
            # A page with no `type` is rule E1, the same as a frontmatter that
            # does not parse. It is broken, not absent: dropping it in silence
            # leaves it out of every index and out of the drift scan, and both
            # commands still exit 0.
            if not frontmatter.get("type"):
                broken.append(path)
                continue
            # closed.md is a generated page. regen writes it from the work
            # items, so reading it back would make it a source of itself.
            if frontmatter["type"] != "ClosedItems":
                pages[path] = (bundle, frontmatter, body)
    return pages, sorted(broken)


def collect(root: Path) -> dict:
    """Every readable page: absolute path -> (bundle, frontmatter, body)."""
    return read_tree(root)[0]


def unreadable(root: Path) -> list[Path]:
    """Each page that the reader cannot use, sorted."""
    return read_tree(root)[1]


def require_readable(root: Path, broken: list | None = None) -> None:
    """Raise a DataError naming every page the reader cannot use.

    regen and drift both read the whole tree before they write anything.
    Without this call they would skip, or crash on, the same page `check`
    reports as E1. Call this before that whole-tree read, so the command
    exits 1 with a clear message instead of a traceback or a `clean` verdict.
    """
    broken = unreadable(root) if broken is None else broken
    if broken:
        names = ", ".join(str(path.relative_to(root)) for path in broken)
        raise DataError(
            f"the reader cannot use the frontmatter of {names}. "
            f"Run `prd.py check` to see the details.")


def computed_state(frontmatter: dict, bundle_root: Path, pages: dict) -> str | None:
    """For an item in ready or blocked: blocked when one blocker or more is
    open, ready when none is. No actor sets these two states directly.

    pages maps an absolute path to (bundle, frontmatter).
    """
    if frontmatter.get("type") not in WORK_ITEMS:
        return None
    if frontmatter.get("state") not in COMPUTED_STATES:
        return None
    for target in frontmatter.get("blocked_by") or []:
        blocker = pages.get(bundle_root / str(target).lstrip("/"))
        if blocker is None or blocker[1].get("state") not in CLOSED_STATES:
            return "blocked"
    return "ready"


def state_overrides(root: Path, pages: dict) -> dict:
    """path -> the state regen would write. Only a change is in the map.

    pages maps an absolute path to (bundle, frontmatter, body).
    """
    for_state = {p: (b, fm) for p, (b, fm, _body) in pages.items()}
    out = {}
    for path, (bundle, frontmatter, _body) in pages.items():
        wanted = computed_state(frontmatter, bundle_dir(root, bundle), for_state)
        if wanted and wanted != frontmatter.get("state"):
            out[path] = wanted
    return out


def plan(root: Path, pages: dict | None = None) -> dict[Path, str]:
    """path -> the full text that regen would write.

    `pages` is the read_tree() map, when the caller already holds one. plan
    applies the computed state to it in place, so a caller that needs the
    stored state reads it before the call.
    """
    if pages is None:
        pages = collect(root)
    # The computed state comes first: the status table of the parent and the
    # closed index both read the state of a page.
    for path, wanted in state_overrides(root, pages).items():
        pages[path][1]["state"] = wanted
    for_links = {p: (b, fm) for p, (b, fm, _body) in pages.items()}
    # One pass over the graph for the whole run, not one pass for each page.
    incoming = incoming_index(for_links, root)
    children = status_mod.child_index(for_links)
    out = {}
    for path, (bundle, frontmatter, body) in pages.items():
        # The status table comes first and the LINKS block stays last, so the
        # status pass runs before the links pass.
        base = bundle_dir(root, bundle)
        new_body = status_mod.replace_block(
            body, status_mod.block_for(path, base, for_links, children))
        new_body = replace_block(
            new_body, block_for(path, for_links, root, incoming))
        out[path] = dump_page(Page(path=path, frontmatter=frontmatter,
                                   body=new_body))
    # One grouping pass for every index below, instead of one filter of the
    # whole page map for each of the 24 type directories.
    grouped = by_parent(for_links)
    for bundle in BUNDLES:
        base = bundle_dir(root, bundle)
        if not base.is_dir():
            continue
        out[base / "index.md"] = root_index(bundle, base, for_links, grouped)
        out[base / "links.tsv"] = linkstsv.text(bundle, base, for_links)
        for name in DIRECTORY_ORDER[bundle]:
            directory = base / name
            spec = spec_for_path(bundle, name)
            index = directory_index(directory, base, spec.name, for_links,
                                    grouped)
            if index is not None:
                out[directory / "index.md"] = index
            closed = closed_index(directory, base, spec.name, for_links,
                                  grouped)
            if closed is not None:
                out[directory / "closed.md"] = closed
    return out


def owned(root: Path) -> set[Path]:
    """Every path regen owns: the root index of each bundle, and the index.md
    and closed.md of each type directory. plan() returns only the files it
    writes, so this is the set that says what a stale file is."""
    out = set()
    for bundle in BUNDLES:
        base = bundle_dir(root, bundle)
        if not base.is_dir():
            continue
        out.add(base / "index.md")
        out.add(base / "links.tsv")
        for name in DIRECTORY_ORDER[bundle]:
            out.add(base / name / "index.md")
            out.add(base / name / "closed.md")
    return out


def stale(root: Path, planned: dict) -> list[Path]:
    """An owned file on disk that plan() no longer writes."""
    return sorted(path for path in owned(root)
                  if path.exists() and path not in planned)


def _regions(text: str) -> list[str]:
    """The STATUS block and the LINKS block of one page, `""` for a block the
    page does not carry."""
    out = []
    for start, end in ((STATUS_START, STATUS_END), (LINKS_START, LINKS_END)):
        _head, marker, tail = text.partition(start)
        out.append(marker + tail.partition(end)[0] if marker else "")
    return out


# The two reasons regen changes a file. The caller turns each one into its
# own message: `regen --check` prints a STALE line, rule E10 prints a finding.
GENERATED = "generated"
COMPUTED_STATE = "state"


def differences(root: Path, pages: dict | None = None) -> dict[Path, str]:
    """path -> the reason `regen` would change it.

    `pages` is a `read_tree` map the caller already holds. Both callers hold
    one: `check` has just parsed every page for rules E1 to E3, and
    `regen --check` reads the tree for require_readable(). Without it this
    function parses the whole bundle a second time in each command.

    This is the one comparison. `regen --check` and rule E10 both call it, so
    the two verdicts cannot disagree. It compares the generated regions of a
    page, never the whole page: the key order and the quoting of a
    hand-written frontmatter belong to its author, and `regen` normalises
    them with no finding.

    It does not call require_readable(). Rule E1 owns a page that does not
    parse, and `check` must still report E1 instead of stopping here.
    """
    pages = collect(root) if pages is None else pages
    # state_overrides reads the stored state, and plan() overwrites it in
    # place with the computed one, so the two run in this order.
    changed = state_overrides(root, pages)
    planned = plan(root, pages)
    out = {path: GENERATED for path in stale(root, planned)}
    for path, text in planned.items():
        if not path.exists():
            out[path] = GENERATED
        elif path.name in GENERATED_NAMES:
            if path.read_text(encoding="utf-8") != text:
                out[path] = GENERATED
        elif _regions(path.read_text(encoding="utf-8")) != _regions(text):
            out[path] = GENERATED
    for path in changed:
        out.setdefault(path, COMPUTED_STATE)
    # The manifest of a bundle that has a page in a folder that its
    # `id_folders` does not name. `regen --check`, rule E10 and the K-fresh
    # rule of the general check agree on it. (`standard` imports this module,
    # so the import is here, the form of init_bundle.py.)
    from . import standard
    for manifest in standard.stale_manifests(root):
        out.setdefault(manifest, GENERATED)
    return out


def write(root: Path) -> list[Path]:
    pages, broken = read_tree(root)
    require_readable(root, broken)
    # regen rewrites pages and appends to log.md, so it takes the same lock as
    # new, state and drift --write. Without it a regen and a state run
    # interleave their writes to one page and to one log.
    with write_lock(root):
        changes = state_overrides(root, pages)
        # The log line names the state that was stored, and plan() overwrites
        # it in place, so it is read here, before plan runs.
        before = {path: pages[path][1].get("state", "") for path in changes}
        planned = plan(root, pages)
        now = datetime.now(timezone.utc)
        # One read and one write of each log, not one for each change.
        # append_entry rewrites the whole file, and a regen that unblocks
        # many items would rewrite the growing log once for each of them.
        by_bundle = {}
        for path, wanted in changes.items():
            bundle, _frontmatter, _body = pages[path]
            base = bundle_dir(root, bundle)
            by_bundle.setdefault(base, []).append(
                state_line(path.stem, str(path.relative_to(base)),
                           before[path], wanted, REGEN_ACTOR, now))
        for base, lines in by_bundle.items():
            append_entries(base / "log.md", lines, now)
        written = []
        for path in stale(root, planned):
            path.unlink()
            written.append(path)
        for path, text in planned.items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                written.append(path)
        from . import standard
        for bundle in BUNDLES:
            if standard.refresh_id_folders(root, bundle):
                written.append(bundle_dir(root, bundle) / "manifest.md")
    return sorted(written)
