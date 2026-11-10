"""The brain rules of the ux-hci-design graph (spec, "Brain check")."""
from __future__ import annotations

from uxlib import manifest, regen, schema
from uxlib.bundle import ID_RE
from uxlib.ids import fold
from uxlib.issues import ERROR, WARN


def run_keys(page) -> list[str]:
    return schema.edge_values(page.frontmatter, "run")


def ux_schema(ctx):
    out = [ctx.issue(ERROR, "UX-schema", p, pg.error) for p, pg in ctx.pages.items() if pg.error]
    for path, page in ctx.pages.items():
        if not page.error and not page.type:
            out.append(ctx.issue(ERROR, "UX-schema", path, "the page has no type"))
    for path, page in ctx.ok().items():
        for problem in schema.validate(page.type, page.frontmatter):
            out.append(ctx.issue(ERROR, "UX-schema", path, problem, problem.split(":")[0].split(".")[0]))
    return out


def ux_id(ctx):
    out = []
    for path, page in ctx.ok().items():
        spec = schema.types().get(page.type)
        if spec is None:
            out.append(ctx.issue(ERROR, "UX-id", path, f"{page.type!r} is not a page type of ux-hci-design", "type"))
            continue
        match = ID_RE.match(path.stem)
        if path.parent != ctx.dir / spec["directory"] or not match or match.group(1) != spec["prefix"]:
            out.append(ctx.issue(ERROR, "UX-id", path, f"a {page.type} page is {spec['directory']}/{spec['prefix']}-NN.md", "type"))
    return out


def ux_link(ctx):
    """A link points to a page that exists, of a type that the field allows."""
    out = []
    for path, page in ctx.ok().items():
        for name, spec in schema.edges().items():
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                target = ctx.at(value)
                if target is None or target.error:
                    out.append(ctx.issue(ERROR, "UX-link", path, f"{name}: {value} does not exist", name))
                elif target.type not in spec["targets"]:
                    out.append(ctx.issue(ERROR, "UX-link", path,
                                         f"{name}: {value} is a {target.type}, not a {' or '.join(spec['targets'])}", name))
                elif not target.live and page.live:
                    out.append(ctx.issue(WARN, "UX-link", path, f"{name}: {value} is deprecated", name))
    return out


def ux_required(ctx):
    out = []
    required = (manifest.read(ctx.dir) or {}).get("required_links") or schema.REQUIRED_LINKS
    for path, page in ctx.ok().items():
        for name in required.get(page.type, []):
            if not schema.edge_values(page.frontmatter, name):
                out.append(ctx.issue(ERROR, "UX-required", path, f"a {page.type} page needs the link {name}", name))
    return out


def ux_run(ctx):
    """Each page except a Run page names its run, and the run is a Run page."""
    out = []
    for path, page in ctx.ok().items():
        if page.type == "Run":
            continue
        keys = run_keys(page)
        if not keys:
            out.append(ctx.issue(ERROR, "UX-run", path, "the page has no link to a Run page", "run"))
        for key in keys:
            target = ctx.at(key)
            if target is not None and target.type != "Run":
                out.append(ctx.issue(ERROR, "UX-run", path, f"run: {key} is not a Run page", "run"))
    return out


def ux_duplicate(ctx):
    """No 2 live Persona pages with 1 name, no 2 Screen pages with 1 wireframe_id, and the same for a concept and a pattern."""
    out, seen = [], {}
    keys = {"Persona": "name", "Screen": "wireframe_id", "InteractionRule": "pattern_id", "Concept": "concept_id"}
    for path, page in ctx.live().items():
        field = keys.get(page.type)
        if field is None or not page.frontmatter.get(field):
            continue
        if page.type == "InteractionRule" and page.frontmatter.get("pattern_kind") != "pattern":
            continue
        seen.setdefault((page.type, fold(page.frontmatter[field])), []).append(path)
    for key, paths in seen.items():
        if len(paths) > 1:
            names = ", ".join(p.stem for p in sorted(paths))
            out += [ctx.issue(ERROR, "UX-duplicate", p, f"{key[0]} pages {names} have the same key") for p in paths]
    return out


def ux_behavior(ctx):
    """WARN: a state rule or a screen interaction has no Screen, so a PRD page has no structure to point to.

    A pattern (`pattern_kind: pattern`) is a rule for all screens, so it needs no Screen.
    """
    out = []
    for kind, field in (("StateRule", "screen"), ("InteractionRule", "screens")):
        for path, page in ctx.of_type(kind).items():
            if kind == "InteractionRule" and page.frontmatter.get("pattern_kind") != "screen_interaction":
                continue
            if not schema.edge_values(page.frontmatter, field):
                out.append(ctx.issue(WARN, "UX-behavior", path, f"a {kind} page has no {field} link, so no PRD page has a structure to point to", field))
    return out


def ux_journey(ctx):
    """WARN: a journey has no persona link, because no Persona page has its persona_name."""
    return [ctx.issue(WARN, "UX-journey", path, "the journey has no persona link: no Persona page has the name "
                      f"{page.frontmatter.get('persona_name')!r}", "persona")
            for path, page in ctx.of_type("Journey").items()
            if not schema.edge_values(page.frontmatter, "persona")]


def ux_stale(ctx):
    return [ctx.issue(ERROR, "UX-stale", path, "the generated part is stale. Run ux_graph.py regen.")
            for path in regen.differences(ctx.root, ctx.dir)]


RULES = [ux_schema, ux_id, ux_link, ux_required, ux_run, ux_duplicate, ux_behavior, ux_journey, ux_stale]
