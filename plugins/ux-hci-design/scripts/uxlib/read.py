"""The read operations for the readers: `pages` and `behavior` (STORY-257 rows 11 and 15, STORY-244 row 18). They write nothing."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from uxlib import DataError, UsageError, regen, schema
from uxlib.bundle import read, read_registry, ref, shown
from uxlib.ids import require_type, resolve
from uxlib.ingest import MARK
from uxlib.page import parse

# The map to the PRD (DECISION-05, point 2): the page type, the PRD page type, and the kind on that page.
BEHAVIOR = {"Screen": ("Experience", "structure"), "StateRule": ("Experience", "state-rule"),
            "InteractionRule": ("Experience", "interaction-rule")}
USER_FLOW = ("Journey", "user-flow")
# The keys of a brain page that change with no change of the behavior: a confirmation and a reuse write them again.
VOLATILE = ("generated", "verified", "status", "run", "record")
# The keys of an output file that are run facts, not behavior (the output schemas put agent and time in `metadata`).
RUN_FACTS = ("metadata", "schema_version")
HASH_LENGTH = 6
RESOURCE = "ux-hci-design:"
PRD_FOLDERS = ("experiences", "journeys")


def runs(bundle) -> list:
    return [(path, page) for path, page in sorted(bundle.pages.items()) if page.type == "Run"]


def latest(candidates):
    if not candidates:
        raise DataError("no run matches")
    return max(candidates, key=lambda item: (item[1].frontmatter.get("started_at") or "", item[0].name))[1]


def find_run(bundle, key):
    """The Run page for an ID (RUN-01), an alias, a bundle path, or the word latest."""
    if key == "latest":
        return latest(runs(bundle))
    page = bundle.pages[resolve(bundle, key)]
    if page.type != "Run":
        raise DataError(f"{key} is a {page.type} page, not a Run page")
    return page


def of_run(bundle, wanted, path, page) -> bool:
    return wanted is None or ref(bundle.dir, wanted.path) in schema.edge_values(page.frontmatter, "run")


def pages(root, type_name, run) -> list:
    require_type(type_name)
    bundle = read(root)
    wanted = find_run(bundle, run) if run else None
    return [{"path": shown(root, path), "frontmatter": page.frontmatter,
             "body": regen.strip_generated(page.body).strip("\n")}
            for path, page in sorted(bundle.pages.items())
            if page.type == type_name and (of_run(bundle, wanted, path, page) or path == getattr(wanted, "path", None))]


def run_of_item(bundle, wanted, page):
    """The ID of the run of one item: the run of `--run`, or the latest run of the page."""
    if wanted is not None:
        return wanted.id
    refs = schema.edge_values(page.frontmatter, "run")
    found = [(path, run) for path, run in runs(bundle) if ref(bundle.dir, path) in refs]
    return latest(found).id if found else None


def unmark(value):
    """The value with each child marker `@@<page ID>` written as `@@`, because a child page is its own result."""
    if isinstance(value, str):
        return MARK if value.startswith(MARK) else value
    if isinstance(value, list):
        return [unmark(item) for item in value]
    if isinstance(value, dict):
        return {key: unmark(item) for key, item in value.items()}
    return value


def result_hash(bundle, wanted, page) -> str:
    """The first 6 hex characters of the SHA-256 of the behavior of one brain page (row 18): the frontmatter, the body,
    and the record entry of the run of the item, each with the volatile parts left out."""
    run_id = run_of_item(bundle, wanted, page)
    record = {}
    for key, value in ((page.frontmatter or {}).get("record") or {}).items():
        prefix, _, name = str(key).partition("/")
        if prefix == run_id:
            if isinstance(value, dict):
                value = {k: v for k, v in value.items() if k not in RUN_FACTS}
            record[name] = unmark(value)
    document = {"frontmatter": {k: v for k, v in (page.frontmatter or {}).items() if k not in VOLATILE},
                "body": regen.strip_generated(page.body), "record": record}
    text = json.dumps(document, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:HASH_LENGTH]


def behavior(root, run) -> list:
    """The behavior results of the brain, as one list for the save of the PRD (row 15)."""
    bundle = read(root)
    wanted = find_run(bundle, run) if run else None
    out = []
    for path, page in sorted(bundle.pages.items()):
        fm = page.frontmatter or {}
        if page.type in BEHAVIOR:
            prd_type, kind = BEHAVIOR[page.type]
        elif page.type == "Diagram" and fm.get("diagram_kind") == "user-flow":
            prd_type, kind = USER_FLOW
        else:
            continue
        if not page.live or not of_run(bundle, wanted, path, page):
            continue
        item = {"prd_type": prd_type, "kind": kind, "path": ref(bundle.dir, path), "title": page.title,
                "description": " ".join(str(fm.get("description") or "").split()), "brain_type": page.type}
        if page.type == "InteractionRule":
            item["pattern_kind"] = fm.get("pattern_kind")
        item["hash"] = result_hash(bundle, wanted, page)
        out.append(item)
    return out


# ---- the check against the PRD (row 18) ---------------------------------------------------------

def graph_folder(root, name, plugin) -> Path:
    """The folder of the graph `name` of the registry. It must be a folder of this clone: no `repo`, no absolute path, no `..`.
    `plugin` is the plugin whose setup command makes the entry."""
    entry = read_registry(root).get(name)
    if not entry:
        raise UsageError(f"The registry has no {name} graph. Run /{plugin}:setup first.")
    path = entry.get("path") or ""
    folder = Path(root) / path
    if entry.get("repo") or not path or Path(path).is_absolute() or ".." in Path(path).parts or not folder.is_dir():
        raise UsageError(f"The {name} graph is not a folder of this clone: {path}.")
    return folder


def id_order(page) -> tuple:
    """The sort key of a PRD page: the prefix of its ID, then the number as a number (EXPERIENCE-99 before EXPERIENCE-100)."""
    prefix, _, number = page.id.rpartition("-")
    return (prefix, int(number) if number.isdigit() else -1, page.id)


def prd_pages(folder) -> tuple[list, list]:
    """The pages of experiences/ and journeys/ that parse, in the order of their IDs, and the (path, reason) of each page that
    does not parse. The `index.md` of a folder is a generated file with no frontmatter: it is not a page."""
    pages, broken = [], []
    for name in PRD_FOLDERS:
        for path in sorted((folder / name).glob("*.md")) if (folder / name).is_dir() else []:
            if path.name == "index.md":
                continue
            page = parse(path)
            if page.frontmatter is None:
                broken.append((path, page.error))
            else:
                pages.append(page)
    return sorted(pages, key=id_order), broken


def sources_of(page) -> list:
    value = (page.frontmatter or {}).get("sources")
    return [entry for entry in value if isinstance(entry, dict)] if isinstance(value, list) else []


def source_of(page, resource):
    return next((entry for entry in sources_of(page) if entry.get("resource") == resource), None)


def judge(item, matches) -> str:
    """The line for one result. `matches` are the PRD pages that hold its resource."""
    resource = RESOURCE + item["path"]
    live = [page for page in matches if page.live]
    if not matches:
        return f"missing {item['path']}"
    if not live:
        return f"rejected {matches[0].id} {item['path']}"
    if len(live) > 1:
        return f"different {live[0].id} {item['path']}: {len(live)} PRD pages hold this result ({', '.join(p.id for p in live[1:])})"
    page = live[0]
    fm = page.frontmatter
    wanted = (("type", item["prd_type"]), ("kind", item["kind"]) if item["prd_type"] == "Experience" else None,
              ("hash", item["hash"]))
    have = {"type": fm.get("type"), "kind": fm.get("kind"), "hash": source_of(page, resource).get("hash")}
    for field, value in filter(None, wanted):
        if have[field] != value:
            return f"different {page.id} {item['path']}: {field} is {have[field]}, not {value}"
    return f"present {page.id}"


def check_prd(root, run) -> tuple[int, list]:
    """The lines of `behavior --check-prd` and the exit code. It writes nothing. An unknown run is a usage error."""
    folder = graph_folder(root, "prd", "product")
    try:
        items = behavior(root, run)
    except DataError as error:
        raise UsageError(str(error)) from error
    pages, broken = prd_pages(folder)
    lines = [f"today {datetime.datetime.now(datetime.timezone.utc).date().isoformat()}"]
    for item in items:
        resource = RESOURCE + item["path"]
        lines.append(judge(item, [page for page in pages if source_of(page, resource)]))
    if not run:
        known = {RESOURCE + item["path"] for item in items}
        for page in pages:
            for entry in sources_of(page):
                resource = str(entry.get("resource") or "")
                if resource.startswith(RESOURCE) and resource not in known:
                    lines.append(f"extra {page.id}: {resource} is not a behavior result of the brain")
    # A page that does not parse may hold the source of a result: the result then prints `missing`, and the person must see why.
    lines.extend(f"error {shown(root, path)}: {reason}" for path, reason in broken)
    return (1 if any(line.split(" ", 1)[0] in ("missing", "different", "extra", "error") for line in lines[1:]) else 0), lines
