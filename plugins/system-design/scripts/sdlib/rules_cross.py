"""The rules that read other graphs (spec section 8.3). A probe miss gives SKIP lines."""
from __future__ import annotations

import re
from pathlib import Path

from sdlib import schema
from sdlib.issues import ERROR, SKIP, WARN, Issue
from sdlib.knowledge_client import Knowledge
from sdlib.regen import strip_generated

TEXT = {"X1": "realizes", "X2": "cites", "X3": "used_by", "X4": "the GAP rule",
        "X5": "the lifecycle of linked ADRs", "X6": "parent_spec", "X7": "graph IDs in body text"}
TYPED = (("X1", "realizes", ("Capability",)), ("X2", "cites", ("Constraint", "Metric")), ("X3", "used_by", ("Persona",)))
ADR_EDGES = ("governed_by", "about", "decisions.adr", "approaches.adr")
GRAPH_ID_RE = re.compile(r"(?<![\w/-])([a-z][a-z0-9-]*):([A-Z]+-\d{2,})(?![\w-])")
LEGACY = re.compile(r"^(?:/)?docs/product/system-design\.md#(.+)$")
LINK_RE = re.compile(r"^[a-z][a-z0-9-]*:/")


def _state_issue(ctx, rule, path, key, link, entry, wanted):
    state = entry["state"]
    if state == "found":
        found = (entry.get("frontmatter") or {}).get("type")
        if wanted and found not in wanted:
            return ctx.issue(ERROR, rule, path, f"{key}: {link} is a {found}, not a {' or '.join(wanted)}", key)
        return None
    if state == "missing":
        return ctx.issue(ERROR, rule, path, f"{key}: {link} does not exist", key)
    return ctx.issue(WARN, rule, path, f"{key}: {link} is not checked ({state})", key)


def run(ctx) -> list:
    knowledge = Knowledge.find(ctx.root)
    if knowledge is None:
        return [Issue(SKIP, rule, f"the knowledge plugin is not installed, so {text} is not checked") for rule, text in TEXT.items()]
    out, wanted = [], []
    for path, page in ctx.live().items():
        for rule, key, _types in TYPED:
            wanted += schema.edge_values(page.frontmatter, key)
        for key in ADR_EDGES:
            wanted += [v for v in schema.edge_values(page.frontmatter, key) if v.startswith("adr:")]
        for line in strip_generated(page.body).splitlines():
            wanted += [f"{m.group(1)}:/{m.group(2)}.md" for m in GRAPH_ID_RE.finditer(line)]
    # A value that is not a well-formed `<graph>:/<path>` link is skipped here; E2 reports it. [inferred]
    shown = knowledge.show([v for v in wanted if LINK_RE.match(v)])
    for path, page in ctx.live().items():
        for rule, key, types in TYPED:
            for link in schema.edge_values(page.frontmatter, key):
                if not LINK_RE.match(link):
                    continue
                issue = _state_issue(ctx, rule, path, key, link, shown[link], types)
                if issue:
                    out.append(issue)
        for key in ADR_EDGES:
            for link in (v for v in schema.edge_values(page.frontmatter, key) if v.startswith("adr:")):
                if not LINK_RE.match(link):
                    continue
                entry = shown[link]
                lifecycle = (entry.get("frontmatter") or {}).get("lifecycle")
                if entry["state"] == "found" and lifecycle in ("superseded", "deprecated"):
                    out.append(ctx.issue(WARN, "X5", path, f"{key}: {link} is {lifecycle}", key.split(".")[0]))
        for line in strip_generated(page.body).splitlines():
            for match in GRAPH_ID_RE.finditer(line):
                link = f"{match.group(1)}:/{match.group(2)}.md"
                issue = _state_issue(ctx, "X7", path, "body", match.group(0), shown[link], ())
                if issue:
                    out.append(issue)
    out += gap(ctx, knowledge) + parent_spec(ctx, knowledge)
    return out


def gap(ctx, knowledge) -> list:
    scopes = knowledge.pages("prd", "Scope")
    system = ctx.system()
    if scopes is None:
        return [Issue(WARN, "X4", "the graph prd is not in .claude/knowledge.json, so the GAP rule is not checked",
                      ctx.shown(ctx.dir / "system.md"))]
    realized = {v for comp in ctx.of_type("Component").values() for v in schema.edge_values(comp.frontmatter, "realizes")}
    accepted = bool(system and not system.error and system.frontmatter.get("design_state") == "accepted")
    out = []
    for scope in scopes:
        fm = scope["frontmatter"]
        if fm.get("kind") != "release" or fm.get("status") == "deprecated":
            continue
        for include in fm.get("includes") or []:
            capability = f"prd:{include.get('to')}"
            if capability not in realized:
                out.append(ctx.issue(ERROR if accepted else WARN, "X4", ctx.dir / "system.md",
                                     f"GAP: {capability} is in scope, and no component realizes it"))
    return out


def parent_spec(ctx, knowledge) -> list:
    adrs = knowledge.pages("adr")
    if adrs is None:
        return [Issue(WARN, "X6", "the graph adr is not in .claude/knowledge.json, so parent_spec is not checked",
                      ctx.shown(ctx.dir / "system.md"))]
    by_anchor = {anchor: slug for slug, anchor in schema.anchors().items()}
    out = []
    for adr in adrs:
        fm = adr["frontmatter"]
        if fm.get("lifecycle") == "superseded":
            continue
        spec = str(fm.get("parent_spec") or "")
        match = re.match(r"^system-design:/areas/([a-z-]+)\.md$", spec)
        legacy = LEGACY.match(spec)
        slug = match.group(1) if match else by_anchor.get(legacy.group(1)) if legacy else None
        area = ctx.pages.get(ctx.dir / "areas" / f"{slug}.md") if slug else None
        if area is None or area.error:
            continue
        rows = {Path(str(r.get("adr", "")).split(":", 1)[-1]).name for r in area.frontmatter.get("decisions") or []}
        if Path(adr["path"]).name not in rows:
            out.append(ctx.issue(ERROR, "X6", area.path,
                                 f"adr:{adr['path']} names this area in parent_spec, and no decision row links it", "decisions"))
    return out
