"""The brain rules of the value-ip graph."""
from __future__ import annotations

from viplib import manifest, regen, schema
from viplib.bundle import ID_RE
from viplib.issues import ERROR, WARN


def vip_schema(ctx):
    out = [ctx.issue(ERROR, "VIP-schema", p, pg.error) for p, pg in ctx.pages.items() if pg.error]
    for path, page in ctx.pages.items():
        if not page.error and not page.type:
            out.append(ctx.issue(ERROR, "VIP-schema", path, "the page has no type"))
    for path, page in ctx.ok().items():
        for problem in schema.validate(page.type, page.frontmatter):
            out.append(ctx.issue(ERROR, "VIP-schema", path, problem, problem.split(":")[0].split(".")[0]))
    return out


def vip_id(ctx):
    out = []
    for path, page in ctx.ok().items():
        spec = schema.types().get(page.type)
        if spec is None:
            out.append(ctx.issue(ERROR, "VIP-id", path, f"{page.type!r} is not a page type of value-ip", "type"))
            continue
        match = ID_RE.match(path.stem)
        if path.parent != ctx.dir / spec["directory"] or not match or match.group(1) != spec["prefix"]:
            out.append(ctx.issue(ERROR, "VIP-id", path, f"a {page.type} page is {spec['directory']}/{spec['prefix']}-NN.md", "type"))
    return out


def vip_link(ctx):
    """A link points to a page that exists, of a type that the field allows."""
    out = []
    for path, page in ctx.ok().items():
        for name, spec in schema.edges().items():
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                target = ctx.at(value)
                if target is None or target.error:
                    out.append(ctx.issue(ERROR, "VIP-link", path, f"{name}: {value} does not exist", name))
                elif target.type not in spec["targets"]:
                    out.append(ctx.issue(ERROR, "VIP-link", path,
                                         f"{name}: {value} is a {target.type}, not a {' or '.join(spec['targets'])}", name))
                elif not target.live and page.live:
                    out.append(ctx.issue(WARN, "VIP-link", path, f"{name}: {value} is deprecated", name))
    return out


def vip_required(ctx):
    out = []
    required = (manifest.read(ctx.dir) or {}).get("required_links") or schema.REQUIRED_LINKS
    for path, page in ctx.ok().items():
        for name in required.get(page.type, []):
            if not schema.edge_values(page.frontmatter, name):
                out.append(ctx.issue(ERROR, "VIP-required", path, f"a {page.type} page needs the link {name}", name))
    return out


def vip_run(ctx):
    """Each result of a run is on the pages of that run only, and 2 Run pages never share a result file."""
    out, seen = [], {}
    for path, page in ctx.ok().items():
        if page.type != "Run":
            continue
        name = page.frontmatter.get("result_file")
        seen.setdefault(name, []).append(path)
    for name, paths in seen.items():
        if len(paths) > 1:
            out += [ctx.issue(ERROR, "VIP-run", p, f"the result file {name} is on more than 1 Run page", "result_file")
                    for p in paths]
    return out


def vip_verified(ctx):
    """A page is `stable` only after a person confirmed it: it holds a `verified` entry of a `human:` actor."""
    out = []
    for path, page in ctx.ok().items():
        if page.frontmatter.get("status") != "stable":
            continue
        entries = page.frontmatter.get("verified") or []
        if not any(isinstance(e, dict) and str(e.get("by", "")).startswith("human:") for e in entries):
            out.append(ctx.issue(ERROR, "VIP-verified", path, "a stable page needs a verified entry of a person", "status"))
    return out


def vip_stale(ctx):
    return [ctx.issue(ERROR, "VIP-stale", path, "the generated part is stale. Run vip_graph.py regen.")
            for path in regen.differences(ctx.root, ctx.dir)]


RULES = [vip_schema, vip_id, vip_link, vip_required, vip_run, vip_verified, vip_stale]
