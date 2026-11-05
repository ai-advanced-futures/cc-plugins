"""The design rules of system-design (research "Lint rules", spec section 8.3)."""
from __future__ import annotations

import re

from sdlib import schema
from sdlib.bundle import ref
from sdlib.issues import ERROR, WARN
from sdlib.regen import strip_generated

SIX = ("source", "stimulus", "environment", "response", "response_measure")
BODY_ID_RE = re.compile(r"(?<![\w:/-])([A-Z]+)-(\d{2,})(?![\w-])")
MEASURE_RE = re.compile(r"\d|<|>|=")
SOURCE_RE = re.compile(r"^(adr|human:[A-Za-z0-9._-]+, \d{4}-\d{2}-\d{2})$")


def e8_w2(ctx):
    out = []
    for path, comp in ctx.of_type("Component").items():
        own = ref(ctx.dir, path)
        for use in comp.frontmatter.get("uses") or []:
            if not isinstance(use, dict):
                continue
            if not use.get("technology"):
                out.append(ctx.issue(WARN, "W2", path, f"the uses entry to {use.get('to')} has no technology (C4)", "uses"))
            iface = ctx.at(use["via"]) if use.get("via") else None
            if iface is None or iface.error or iface.type != "Interface":
                continue
            fm = iface.frontmatter
            if fm.get("provided_by") != use.get("to"):
                out.append(ctx.issue(ERROR, "E8", path, f"uses {use.get('to')} via {use['via']}, but {use['via']} is provided by {fm.get('provided_by')}", "uses"))
            if own not in (fm.get("consumed_by") or []):
                out.append(ctx.issue(ERROR, "E8", path, f"{own} is not a consumer of {use['via']}", "uses"))
            if fm.get("style") != use.get("style"):
                out.append(ctx.issue(ERROR, "E8", path, f"the style {use.get('style')} differs from the style of {use['via']}", "uses"))
    return out


def e9(ctx):
    out = []
    for path, iface in ctx.of_type("Interface").items():
        fm = iface.frontmatter
        if not fm.get("consumed_by"):
            out.append(ctx.issue(ERROR, "E9", path, "an Interface has one or more consumers", "consumed_by"))
        for end in [fm.get("provided_by")] + list(fm.get("consumed_by") or []):
            target = ctx.at(end) if end else None
            if target and not target.error and target.frontmatter.get("kind") == "external" and fm.get("direction") == "internal":
                out.append(ctx.issue(ERROR, "E9", path, f"{end} is external: use direction inbound or outbound", "direction"))
    return out


def e10_w3(ctx):
    out = []
    for path, entity in ctx.of_type("DataEntity").items():
        fm = entity.frontmatter
        store = ctx.at(fm["stored_in"]) if fm.get("stored_in") else None
        if store and not store.error and store.frontmatter.get("kind") not in ("data-store", "queue"):
            out.append(ctx.issue(ERROR, "E10", path, f"stored_in {fm['stored_in']} is not a data-store or a queue", "stored_in"))
        for access in fm.get("accessed_by") or []:
            if access.get("access") == "write" and access.get("component") != fm.get("owned_by"):
                out.append(ctx.issue(WARN, "W3", path, f"{access.get('component')} writes {entity.id}, and it is not the owner", "accessed_by"))
    return out


def scenarios(ctx):
    out = []
    live = ctx.of_type("QualityScenario")
    for path, scenario in live.items():
        fm = scenario.frontmatter
        for part in SIX:
            if not str(fm.get(part) or "").strip():
                out.append(ctx.issue(ERROR, "E11", path, f"the part {part} is empty", part))
        if not fm.get("artifact"):
            out.append(ctx.issue(ERROR, "E11", path, "the artifact is empty", "artifact"))
        if not MEASURE_RE.search(str(fm.get("response_measure") or "")):
            out.append(ctx.issue(WARN, "W4", path, "the response measure has no number and no comparator", "response_measure"))
    if not 3 <= len(live) <= 5 and ctx.system():
        out.append(ctx.issue(WARN, "W5", ctx.dir / "system.md", f"the design has {len(live)} live quality scenarios: write 3 to 5"))
    return out


def e12_w6_e13(ctx):
    out = []
    for path, risk in ctx.of_type("TechnicalRisk").items():
        fm = risk.frontmatter
        if fm.get("risk_kind") in ("risk", "tech-debt"):
            if not fm.get("failure"):
                out.append(ctx.issue(ERROR, "E12", path, "a risk states the failure that a test can show", "risk_kind"))
            if bool(fm.get("mitigation")) == bool(fm.get("acceptance")):
                out.append(ctx.issue(ERROR, "E12", path, "a risk has a mitigation or an acceptance, not both and not neither", "risk_kind"))
        elif not fm.get("assumes"):
            out.append(ctx.issue(ERROR, "E12", path, "a non-risk names one or more assumptions", "risk_kind"))
    for path, assumption in ctx.of_type("Assumption").items():
        source = assumption.frontmatter.get("inferred_from")
        if source and not (ctx.root / source).exists():
            out.append(ctx.issue(WARN, "W6", path, f"inferred_from {source} does not exist in the repository", "inferred_from"))
    for path, node in ctx.of_type("DeploymentNode").items():
        if not node.frontmatter.get("regions"):
            out.append(ctx.issue(ERROR, "E13", path, "a DeploymentNode names its regions", "type"))
    return out


def areas(ctx):
    out = []
    named = set()
    for page in ctx.live().values():
        if page.frontmatter.get("type") == "Area":
            # An Area page names its own slug in `area`, which must not count as coverage. [inferred]
            continue
        named |= set(schema.edge_values(page.frontmatter, "areas")) | set(schema.edge_values(page.frontmatter, "area"))
    for path, comp in ctx.of_type("Component").items():
        if not comp.frontmatter.get("areas"):
            out.append(ctx.issue(ERROR, "E14", path, "a component names one or more areas", "areas"))
    states = {}
    for slug in schema.areas():
        path = ctx.dir / "areas" / f"{slug}.md"
        page = ctx.pages.get(path)
        if page is None or page.error:
            continue
        state = page.frontmatter.get("area_state")
        states[slug] = state
        if slug not in named and not page.frontmatter.get("decisions") and state not in ("open", "not-applicable"):
            out.append(ctx.issue(ERROR, "E14", path, f"the area has no page and no decision row, so it is open or not-applicable, not {state}", "area_state"))
    system = ctx.system()
    if system and not system.error and system.frontmatter.get("design_state") == "accepted":
        for slug, state in states.items():
            if state in ("open", "fog"):
                out.append(ctx.issue(ERROR, "E15", ctx.dir / "system.md", f"the design is accepted, and the area {slug} is {state}", "design_state"))
    return out


def e16(ctx):
    out, seen, retired = [], {}, set()
    area_pages = {slug: ctx.pages.get(ctx.dir / "areas" / f"{slug}.md") for slug in schema.areas()}
    for page in area_pages.values():
        if page and not page.error:
            retired |= set(page.frontmatter.get("retired_keys") or [])
    for slug, page in area_pages.items():
        if not page or page.error:
            continue
        path = page.path
        for row in page.frontmatter.get("decisions") or []:
            key = str(row.get("key"))
            if not re.fullmatch(rf"{re.escape(slug)}-\d+", key):
                out.append(ctx.issue(ERROR, "E16", path, f"the row key {key} must be {slug}-<n>", "decisions"))
            if key in seen:
                out.append(ctx.issue(ERROR, "E16", path, f"the row key {key} is also in {seen[key]}", "decisions"))
            seen[key] = slug
            if key in retired:
                out.append(ctx.issue(ERROR, "E16", path, f"the row key {key} is retired", "decisions"))
            if "|" in str(row.get("binds")) or "\n" in str(row.get("binds")):
                out.append(ctx.issue(ERROR, "E16", path, f"the row {key} binds text has a | or a new line", "decisions"))
            if not row.get("adr") and not str(row.get("source", "")).startswith("human:"):
                out.append(ctx.issue(ERROR, "E16", path, f"the row {key} has no ADR, so its source starts with human:", "decisions"))
            if not SOURCE_RE.match(str(row.get("source", ""))):
                out.append(ctx.issue(ERROR, "E16", path, f"the row {key} source is adr or human:<login>, <date>", "decisions"))
    return out


def e17(ctx):
    out = []
    by_prefix = schema.by_prefix()
    system = ctx.system()
    draft = bool(system and not system.error and system.frontmatter.get("design_state") == "draft")
    tolerant = draft and not ctx.of_type("Component")
    for path, page in ctx.ok().items():
        for number, line in enumerate(strip_generated(page.body).splitlines(), page.head.count("\n") + 1):
            for match in BODY_ID_RE.finditer(line):
                prefix, page_id = match.group(1), match.group(0)
                if prefix not in by_prefix:
                    continue
                target = ctx.dir / schema.types()[by_prefix[prefix]]["directory"] / f"{page_id}.md"
                if target in ctx.pages:
                    continue
                if tolerant and prefix == "COMPONENT":
                    out.append(ctx.issue(WARN, "W7", path, f"{page_id} does not exist yet; the draft has no component"))
                else:
                    issue = ctx.issue(ERROR, "E17", path, f"the ID {page_id} does not exist in this graph")
                    out.append(type(issue)(issue.level, issue.rule, issue.message, issue.file, number))
    return out


RULES = [e8_w2, e9, e10_w3, scenarios, e12_w6_e13, areas, e16, e17]
