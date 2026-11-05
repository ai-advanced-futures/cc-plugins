"""The brain check of system-design (spec section 8.3). Each rule is a function of Ctx."""
from __future__ import annotations

from sdlib import regen, rules_cross, rules_semantic, schema
from sdlib.bundle import ID_RE, ref
from sdlib.context import make
from sdlib.issues import ERROR, WARN
from sdlib.ids import fold


def e1(ctx):
    out = [ctx.issue(ERROR, "E1", p, pg.error) for p, pg in ctx.pages.items() if pg.error]
    return out + [ctx.issue(ERROR, "E1", p, "the page has no type") for p, pg in ctx.pages.items()
                  if not pg.error and not pg.type]


def e2(ctx):
    out = []
    for path, page in ctx.ok().items():
        for problem in schema.validate(page.type, page.frontmatter):
            out.append(ctx.issue(ERROR, "E2", path, problem, problem.split(":")[0].split(".")[0]))
    return out


def e3(ctx):
    out = []
    if ctx.dir / "system.md" not in ctx.pages:
        out.append(ctx.issue(ERROR, "E3", ctx.dir / "system.md", "the bundle has no system.md"))
    for slug in schema.areas():
        if ctx.dir / "areas" / f"{slug}.md" not in ctx.pages:
            out.append(ctx.issue(ERROR, "E3", ctx.dir / "areas" / f"{slug}.md", f"the bundle has no Area page {slug}.md"))
    for path, page in ctx.ok().items():
        rel = path.relative_to(ctx.dir).as_posix()
        if rel == "system.md":
            if page.type != "System":
                out.append(ctx.issue(ERROR, "E3", path, "system.md must have type System", "type"))
            continue
        if rel.startswith("areas/"):
            if page.type != "Area":
                out.append(ctx.issue(ERROR, "E3", path, "a page in areas/ must have type Area", "type"))
            elif path.stem not in schema.areas():
                out.append(ctx.issue(ERROR, "E3", path, f"{path.stem} is not one of the eight areas"))
            elif page.frontmatter.get("area") != path.stem:
                out.append(ctx.issue(ERROR, "E3", path, "area must equal the file name", "area"))
            continue
        spec = schema.types().get(page.type)
        if spec is None or spec["prefix"] is None:
            out.append(ctx.issue(ERROR, "E3", path, f"{page.type!r} is not a page type with an ID", "type"))
            continue
        match = ID_RE.match(path.stem)
        if path.parent != ctx.dir / spec["directory"] or not match or match.group(1) != spec["prefix"]:
            out.append(ctx.issue(ERROR, "E3", path, f"a {page.type} page is {spec['directory']}/{spec['prefix']}-NN.md", "type"))
    return out


def e4(ctx):
    out = []
    for path, page in ctx.ok().items():
        for name, spec in schema.edges().items():
            local = [t for t in spec["targets"] if ":" not in t]
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                key = name.split(".")[0]
                target = ctx.at(value)
                if target is None or target.error:
                    out.append(ctx.issue(ERROR, "E4", path, f"{name}: {value} does not exist", key))
                elif target.type not in local:
                    out.append(ctx.issue(ERROR, "E4", path, f"{name}: {value} is a {target.type}, not a {' or '.join(local)}", key))
                elif name == "part_of" and target.type != page.type:
                    out.append(ctx.issue(ERROR, "E4", path, "part_of must point to a page of the same type", key))
                elif not target.live and page.live:
                    out.append(ctx.issue(WARN, "W8", path, f"{name}: {value} is deprecated", key))
    return out


def _in_cycle(edges, start) -> bool:
    seen, stack = set(), list(edges.get(start, []))
    while stack:
        node = stack.pop()
        if node == start:
            return True
        if node not in seen:
            seen.add(node)
            stack += edges.get(node, [])
    return False


def e5(ctx):
    out = []
    for name, rule, level in (("part_of", "E5", ERROR), ("uses.to", "W1", WARN)):
        edges = {ref(ctx.dir, p): schema.edge_values(pg.frontmatter, name) for p, pg in ctx.ok().items()}
        for path, page in ctx.ok().items():
            if _in_cycle(edges, ref(ctx.dir, path)):
                out.append(ctx.issue(level, rule, path, f"{name.split('.')[0]} makes a cycle", name.split(".")[0]))
    return out


def e6(ctx):
    out, owners, slugs = [], {}, {}
    live_ids = {page.id for page in ctx.live().values()}
    for path, page in ctx.ok().items():
        for alias in page.frontmatter.get("aliases") or []:
            owners.setdefault(fold(alias), []).append(path)
            if str(alias) in live_ids:
                out.append(ctx.issue(ERROR, "E6", path, f"the alias {alias} is a live ID", "aliases"))
        if page.type == "Component" and page.frontmatter.get("slug"):
            slugs.setdefault(page.frontmatter["slug"], []).append(path)
    for alias, paths in owners.items():
        if len(paths) > 1:
            out += [ctx.issue(ERROR, "E6", p, f"the alias {alias} names more than one page", "aliases") for p in paths]
    for slug, paths in slugs.items():
        if len(paths) > 1:
            out += [ctx.issue(ERROR, "E6", p, f"the slug {slug} names more than one component", "slug") for p in paths]
    return out


def e7(ctx):
    return [ctx.issue(ERROR, "E7", path, "the generated part is stale. Run system_design.py regen.")
            for path in regen.differences(ctx.root)]


RULES = [e1, e2, e3, e4, e5, e6, e7, *rules_semantic.RULES, rules_cross.run]


def run(root) -> list:
    ctx = make(root)
    issues = []
    for rule in RULES:
        issues += rule(ctx)
    return issues
