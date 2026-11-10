"""The read operations for the readers: `pages` and `behavior` (STORY-257 rows 11 and 15). They write nothing."""
from __future__ import annotations

from uxlib import DataError, regen, schema
from uxlib.bundle import read, ref, shown
from uxlib.ids import require_type, resolve

# The map to the PRD (DECISION-05, point 2): the page type, the PRD page type, and the kind on that page.
BEHAVIOR = {"Screen": ("Experience", "structure"), "StateRule": ("Experience", "state-rule"),
            "InteractionRule": ("Experience", "interaction-rule")}
USER_FLOW = ("Journey", "user-flow")


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
        out.append({"prd_type": prd_type, "kind": kind, "path": ref(bundle.dir, path), "title": page.title,
                    "description": " ".join(str(fm.get("description") or "").split())})
    return out
