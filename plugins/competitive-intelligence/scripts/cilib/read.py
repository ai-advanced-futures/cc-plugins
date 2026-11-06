"""The read operations for the readers: `results` and `pages` (spec rows 7 and 14). They write nothing."""
from __future__ import annotations

from cilib import DataError, UsageError, regen, schema
from cilib.bundle import read, ref, shown
from cilib.ids import require_type, resolve

RUN_FIELDS = ("started_at", "finished_at", "mode", "subject", "case", "run_id", "answers")


def runs(bundle) -> list:
    return [(path, page) for path, page in sorted(bundle.pages.items()) if page.type == "Run"]


def latest(candidates):
    if not candidates:
        raise DataError("no run matches")
    return max(candidates, key=lambda item: (item[1].frontmatter.get("finished_at") or item[1].frontmatter.get("started_at") or "",
                                             item[0].name))[1]


def find_run(bundle, key):
    """The Run page for an ID (RUN-01), a run_id (acme-0007), or the word latest."""
    candidates = runs(bundle)
    if key == "latest":
        return latest(candidates)
    try:
        page = bundle.pages[resolve(bundle, key)]
        if page.type == "Run":
            return page
    except DataError:
        pass
    hits = [item for item in candidates if item[1].frontmatter.get("run_id") == key]
    if not hits:
        raise DataError(f"no run has the ID or the run_id {key!r}")
    return latest(hits)


def run_ref(bundle, run_page) -> str:
    return ref(bundle.dir, run_page.path)


def pick_run(bundle, run, run_id, latest_flag, command, case):
    if run:
        page = find_run(bundle, run)
        fm = page.frontmatter
        if (command and fm.get("command") != command) or (case and fm.get("case") != case):
            raise DataError(f"the run {run} does not match the command or the case")
        return page
    candidates = [item for item in runs(bundle)
                  if (not run_id or item[1].frontmatter.get("run_id") == run_id)
                  and (not command or item[1].frontmatter.get("command") == command)
                  and (not case or item[1].frontmatter.get("case") == case)]
    if not run_id and not latest_flag:
        raise UsageError("give --run, --run-id or --latest")
    return latest(candidates)


def run_pages(bundle, run_page, type_name):
    wanted = run_ref(bundle, run_page)
    return [(path, page) for path, page in sorted(bundle.pages.items())
            if page.type == type_name and wanted in schema.edge_values(page.frontmatter, "run")]


def result_id(page) -> str:
    return (page.frontmatter.get("aliases") or [page.id])[0].split("/", 1)[-1]


def entry(root, bundle, page):
    fm = page.frontmatter
    out = {"id": result_id(page), "kind": fm.get("kind"), "label": fm.get("label"),
           "value": fm.get("value")}
    out.update({key: fm[key] for key in ("unit", "period") if key in fm})
    out.update({"sources": fm.get("result_sources") or [], "method": fm.get("method"),
                "rests_on_default": bool(fm.get("rests_on_default")), "defaults": fm.get("defaults") or []})
    if fm.get("confidence"):
        out["confidence"] = fm["confidence"]
    about = schema.edge_values(fm, "about")
    if about:
        out["detail"] = shown(root, bundle.dir / about[0].lstrip("/"))
    cites = []
    for target in schema.edge_values(fm, "cites"):
        cited = bundle.pages.get(bundle.dir / target.lstrip("/"))
        if cited is not None:
            cites.append({"file": shown(root, bundle.dir / target.lstrip("/")),
                          "result_id": result_id(cited)})
    if cites:
        out["cites"] = cites
    return out


def results(root, run, run_id, latest_flag, command, case) -> dict:
    bundle = read(root)
    page = pick_run(bundle, run, run_id, latest_flag, command, case)
    fm = page.frontmatter
    gaps = [{"kind": g.frontmatter.get("kind"), "label": g.title, "why": g.frontmatter.get("why")}
            for _path, g in run_pages(bundle, page, "Gap") if g.frontmatter.get("kind")]
    return {"schema": "plugin-result/1", "plugin": "competitive-intelligence",
            "plugin_version": fm.get("plugin_version"), "command": fm.get("command"),
            "run": {key: fm[key] for key in RUN_FIELDS if key in fm},
            "results": [entry(root, bundle, p) for _path, p in run_pages(bundle, page, "Result")],
            "gaps": gaps}


def pages(root, type_name, run) -> list:
    require_type(type_name)
    bundle = read(root)
    wanted = find_run(bundle, run) if run else None
    out = []
    for path, page in sorted(bundle.pages.items()):
        if page.type != type_name:
            continue
        if wanted is not None and path != wanted.path and run_ref(bundle, wanted) not in schema.edge_values(page.frontmatter, "run"):
            continue
        out.append({"path": shown(root, path), "frontmatter": page.frontmatter, "body": regen.strip_generated(page.body).strip("\n")})
    return out
