"""The brain rules of the competitive-intelligence graph (spec, "Brain check")."""
from __future__ import annotations

from cilib import manifest, regen, schema
from cilib.bundle import ID_RE
from cilib.ids import fold
from cilib.issues import ERROR, WARN
from cilib.writer import FIELD_RUNS, PERSON_RUN

RESULT_ABOUT = {"competitor": "Competitor", "alternative": "Competitor", "timing_reason": "Finding",
                "differentiator": "SwotItem", "risk": "SwotItem"}


def run_keys(page) -> list[str]:
    return schema.edge_values(page.frontmatter, "run")


def made_by_a_person(page) -> bool:
    """`new` names (person) in `field_runs` for each field of the page. A run names its own run for each field that it gives."""
    runs = page.frontmatter.get(FIELD_RUNS)
    return isinstance(runs, dict) and bool(runs) and all(value == PERSON_RUN for value in runs.values())


def ci_schema(ctx):
    out = [ctx.issue(ERROR, "CI-schema", p, pg.error) for p, pg in ctx.pages.items() if pg.error]
    for path, page in ctx.pages.items():
        if not page.error and not page.type:
            out.append(ctx.issue(ERROR, "CI-schema", path, "the page has no type"))
    for path, page in ctx.ok().items():
        for problem in schema.validate(page.type, page.frontmatter):
            out.append(ctx.issue(ERROR, "CI-schema", path, problem, problem.split(":")[0].split(".")[0]))
    return out


def ci_id(ctx):
    out = []
    for path, page in ctx.ok().items():
        spec = schema.types().get(page.type)
        if spec is None:
            out.append(ctx.issue(ERROR, "CI-id", path, f"{page.type!r} is not a page type of competitive-intelligence", "type"))
            continue
        match = ID_RE.match(path.stem)
        if path.parent != ctx.dir / spec["directory"] or not match or match.group(1) != spec["prefix"]:
            out.append(ctx.issue(ERROR, "CI-id", path, f"a {page.type} page is {spec['directory']}/{spec['prefix']}-NN.md", "type"))
    return out


def ci_link(ctx):
    """A link points to a page that exists, of a type that the field allows."""
    out = []
    for path, page in ctx.ok().items():
        for name, spec in schema.edges().items():
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                target = ctx.at(value)
                if target is None or target.error:
                    out.append(ctx.issue(ERROR, "CI-link", path, f"{name}: {value} does not exist", name))
                elif target.type not in spec["targets"]:
                    out.append(ctx.issue(ERROR, "CI-link", path,
                                         f"{name}: {value} is a {target.type}, not a {' or '.join(spec['targets'])}", name))
                elif not target.live and page.live:
                    out.append(ctx.issue(WARN, "CI-link", path, f"{name}: {value} is deprecated", name))
    return out


def ci_required(ctx):
    out = []
    required = (manifest.read(ctx.dir) or {}).get("required_links") or schema.REQUIRED_LINKS
    for path, page in ctx.ok().items():
        for name in required.get(page.type, []):
            values = schema.edge_values(page.frontmatter, name)
            if not values:
                out.append(ctx.issue(ERROR, "CI-required", path, f"a {page.type} page needs the link {name}", name))
    return out


def ci_run(ctx):
    out = []
    for path, page in ctx.ok().items():
        if page.type == "Run":
            continue
        keys = run_keys(page)
        # A page that a person made with `new` needs no run (STORY-222). A page that a run wrote links to its run.
        if not keys and not made_by_a_person(page):
            out.append(ctx.issue(ERROR, "CI-run", path, "the page has no link to a Run page, and no person made it", "run"))
        for key in keys:
            target = ctx.at(key)
            if target is not None and target.type != "Run":
                out.append(ctx.issue(ERROR, "CI-run", path, f"run: {key} is not a Run page", "run"))
    return out


def ci_duplicate(ctx):
    out, seen = [], {}
    for path, page in ctx.live().items():
        fm = page.frontmatter
        if page.type == "Market":
            key = ("Market", fold(fm.get("name")))
        elif page.type == "Competitor":
            key = ("Competitor", fold(fm.get("name")), fold(fm.get("website") or ""))
        elif page.type == "Source":
            key = ("Source", fold(fm.get("resource")))
        else:
            continue
        seen.setdefault(key, []).append(path)
    for key, paths in seen.items():
        if len(paths) > 1:
            names = ", ".join(p.stem for p in sorted(paths))
            out += [ctx.issue(ERROR, "CI-duplicate", p, f"{key[0]} pages {names} have the same key") for p in paths]
    return out


def ci_lens(ctx):
    out, seen = [], {}
    for path, page in ctx.of_type("LensResult").items():
        fm = page.frontmatter
        for run in run_keys(page):
            seen.setdefault((run, fm.get("lens"), fm.get("competitor")), []).append(path)
    for (run, lens, competitor), paths in seen.items():
        if len(paths) > 1:
            names = ", ".join(p.stem for p in sorted(paths))
            out += [ctx.issue(ERROR, "CI-lens", p, f"run {run} has more than 1 LensResult for {lens} and {competitor}: {names}")
                    for p in paths]
    return out


def ci_result(ctx):
    out = []
    for path, page in ctx.of_type("Result").items():
        fm = page.frontmatter
        about = fm.get("about")
        if not about:
            out.append(ctx.issue(WARN, "CI-result", path, "the Result page has no about link"))
        else:
            target = ctx.at(about)
            want = RESULT_ABOUT.get(fm.get("kind"))
            if target is not None and not target.error:
                if want and target.type != want:
                    out.append(ctx.issue(ERROR, "CI-result", path, f"a result of kind {fm.get('kind')} is about a {want}, not a {target.type}", "about"))
                if not set(run_keys(page)) & set(run_keys(target)):
                    out.append(ctx.issue(ERROR, "CI-result", path, "the about page is not a page of the run of the result", "about"))
        sources = fm.get("result_sources") or []
        default = any(isinstance(s, dict) and s.get("type") == "default" for s in sources) or bool(fm.get("defaults"))
        if bool(fm.get("rests_on_default")) != default:
            out.append(ctx.issue(ERROR, "CI-result", path,
                                 f"rests_on_default must be {str(default).lower()}: a source has the type default, or defaults is not empty, or neither",
                                 "rests_on_default"))
    return out


def ci_evidence(ctx):
    return [ctx.issue(WARN, "CI-evidence", path, f"a {page.type} page cites no page", "cites")
            for t in ("SwotItem", "Recommendation") for path, page in ctx.of_type(t).items()
            if not schema.edge_values(page.frontmatter, "cites")]


def ci_stale(ctx):
    return [ctx.issue(ERROR, "CI-stale", path, "the generated part is stale. Run ci_graph.py regen.")
            for path in regen.differences(ctx.root, ctx.dir)]


RULES = [ci_schema, ci_id, ci_link, ci_required, ci_run, ci_duplicate, ci_lens, ci_result, ci_evidence, ci_stale]
