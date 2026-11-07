"""The brain rules of the jtbd graph (STORY-87 spec, row 9)."""
from __future__ import annotations

from jtbdlib import manifest, regen, schema
from jtbdlib.bundle import ID_RE
from jtbdlib.issues import ERROR, WARN

# The page type that the `about` link of each result kind points to (spec row 14).
RESULT_ABOUT = {"job": "Job", "job_step": "JobStep", "opportunity_score": "Outcome", "customer_value": "Outcome",
                "customer_segment": "Segment", "willingness_to_pay": "WtpValidation"}
# The fields that a Result page holds, so that the page of its item must not hold them (spec "Design", field map).
MOVED = {("opportunity_score", "Outcome"): ("importance", "satisfaction", "opportunity_score"),
         ("customer_value", "Outcome"): ("annual_evc",),
         ("willingness_to_pay", "WtpValidation"): ("validated_wtp", "wtp_range")}


def moved_fields(kind) -> tuple:
    """The fields of the item page that a Result page of this kind holds."""
    return MOVED.get((kind, RESULT_ABOUT.get(kind)), ())


def run_keys(page) -> list[str]:
    return schema.edge_values(page.frontmatter, "run")


def own_run(page) -> str | None:
    keys = run_keys(page)
    return keys[0] if keys else None


def j_schema(ctx):
    out = [ctx.issue(ERROR, "J-schema", folder, f"cannot read the folder: {reason}") for folder, reason in ctx.unreadable]
    out += [ctx.issue(ERROR, "J-schema", p, pg.error) for p, pg in ctx.pages.items() if pg.error]
    for path, page in ctx.pages.items():
        if not page.error and not page.type:
            out.append(ctx.issue(ERROR, "J-schema", path, "the page has no type"))
    for path, page in ctx.ok().items():
        for problem in schema.validate(page.type, page.frontmatter):
            out.append(ctx.issue(ERROR, "J-schema", path, problem, problem.split(":")[0].split(".")[0]))
    return out


def j_id(ctx):
    out = []
    for path, page in ctx.ok().items():
        spec = schema.types().get(page.type)
        if spec is None:
            out.append(ctx.issue(ERROR, "J-id", path, f"{page.type!r} is not a page type of the jtbd graph", "type"))
            continue
        match = ID_RE.match(path.stem)
        if path.parent != ctx.dir / spec["directory"] or not match or match.group(1) != spec["prefix"]:
            out.append(ctx.issue(ERROR, "J-id", path, f"a {page.type} page is {spec['directory']}/{spec['prefix']}-NN.md", "type"))
    return out


def j_link(ctx):
    """A link points to a page that exists, of a type that the field allows."""
    out = []
    for path, page in ctx.ok().items():
        for name, spec in schema.edges().items():
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                target = ctx.at(value)
                if target is None or target.error:
                    out.append(ctx.issue(ERROR, "J-link", path, f"{name}: {value} does not exist", name))
                elif target.type not in spec["targets"]:
                    out.append(ctx.issue(ERROR, "J-link", path,
                                         f"{name}: {value} is a {target.type}, not a {' or '.join(spec['targets'])}", name))
                elif not target.live and page.live:
                    out.append(ctx.issue(WARN, "J-link", path, f"{name}: {value} is deprecated", name))
    return out


def j_required(ctx):
    out = []
    required = (manifest.read(ctx.dir) or {}).get("required_links") or schema.REQUIRED_LINKS
    for path, page in ctx.ok().items():
        for name in required.get(page.type, []):
            if not schema.edge_values(page.frontmatter, name):
                out.append(ctx.issue(ERROR, "J-required", path, f"a {page.type} page needs the link {name}", name))
    return out


def j_run(ctx):
    """Each page that is not a Run page has 1 run link, and its target is a Run page."""
    out = []
    for path, page in ctx.ok().items():
        if page.type == "Run":
            continue
        keys = run_keys(page)
        if len(keys) != 1:
            out.append(ctx.issue(ERROR, "J-run", path, "the page needs 1 link to a Run page", "run"))
        for key in keys:
            target = ctx.at(key)
            if target is not None and target.type != "Run":
                out.append(ctx.issue(ERROR, "J-run", path, f"run: {key} is not a Run page", "run"))
    return out


def same_run(ctx, path, page, field, allowed, label):
    """One link of `page` must point to a page of a run in `allowed`."""
    out = []
    for value in schema.edge_values(page.frontmatter, field):
        target = ctx.at(value)
        if target is None or target.error:
            continue
        if own_run(target) not in allowed:
            out.append(ctx.issue(ERROR, "J-tree", path, f"{field}: {value} is not a page of {label}", field))
    return out


def j_tree(ctx):
    """The pages of a tree belong to 1 run (a WtpValidation reads the segments of its input run)."""
    out = []
    for path, page in ctx.live().items():
        run = own_run(page)
        if page.type == "Outcome":
            out += same_run(ctx, path, page, "step", {run}, "the same run")
        elif page.type == "JobStep":
            out += same_run(ctx, path, page, "job", {run}, "the same run")
        elif page.type == "Segment":
            out += same_run(ctx, path, page, "job", {run}, "the same run")
            out += same_run(ctx, path, page, "top_outcomes", {run}, "the same run")
        elif page.type == "WtpValidation":
            run_page = ctx.at(run) if run else None
            inputs = schema.edge_values(run_page.frontmatter, "input_run") if run_page is not None else []
            allowed = set(inputs) if inputs else {run}
            label = "the input run of the Run page" if inputs else "the same run"
            out += same_run(ctx, path, page, "segment", allowed, label)
    return out


def j_score(ctx):
    out = []
    for path, page in ctx.of_type("Outcome").items():
        fm = page.frontmatter
        for name in ("importance", "satisfaction"):
            value = fm.get(name)
            if isinstance(value, (int, float)) and not 1 <= value <= 10:
                out.append(ctx.issue(ERROR, "J-score", path, f"{name} must be from 1 to 10, not {value}", name))
        value = fm.get("opportunity_score")
        if isinstance(value, (int, float)) and value < 0:
            out.append(ctx.issue(ERROR, "J-score", path, f"opportunity_score must be 0 or more, not {value}", "opportunity_score"))
    return out


def j_rank(ctx):
    out, seen = [], {}
    for path, page in ctx.of_type("Outcome").items():
        rank = page.frontmatter.get("rank")
        if rank is not None:
            seen.setdefault((own_run(page), rank), []).append(path)
    for (_run, rank), paths in seen.items():
        if len(paths) > 1:
            names = ", ".join(p.stem for p in sorted(paths))
            out += [ctx.issue(WARN, "J-rank", p, f"the Outcome pages {names} have the same rank {rank}", "rank") for p in paths]
    return out


def j_finished(ctx):
    return [ctx.issue(ERROR, "J-finished", path, "a Run page with status stable needs finished_at", "status")
            for path, page in ctx.of_type("Run").items()
            if page.frontmatter.get("status") == "stable" and not page.frontmatter.get("finished_at")]


def j_result(ctx):
    out = []
    for path, page in ctx.of_type("Result").items():
        fm = page.frontmatter
        kind = fm.get("kind")
        about = fm.get("about")
        run = own_run(page)
        if kind not in RESULT_ABOUT:
            out.append(ctx.issue(ERROR, "J-result", path, f"the kind {kind!r} is not 1 of the 6 kinds: {', '.join(RESULT_ABOUT)}", "kind"))
        elif not about:
            out.append(ctx.issue(WARN, "J-result", path, "the Result page has no about link"))
        else:
            target = ctx.at(about)
            if target is not None and not target.error:
                if target.type != RESULT_ABOUT[kind]:
                    out.append(ctx.issue(ERROR, "J-result", path,
                                         f"a result of kind {kind} is about a {RESULT_ABOUT[kind]}, not a {target.type}", "about"))
                allowed = {run}
                run_page = ctx.at(run) if run else None
                if kind == "customer_value" and run_page is not None:
                    allowed |= set(schema.edge_values(run_page.frontmatter, "input_run"))
                if own_run(target) not in allowed:
                    out.append(ctx.issue(ERROR, "J-result", path, "the about page is not a page of the run of the result", "about"))
        sources = fm.get("result_sources") or []
        default = any(isinstance(s, dict) and s.get("type") == "default" for s in sources) or bool(fm.get("defaults"))
        if bool(fm.get("rests_on_default")) != default:
            out.append(ctx.issue(ERROR, "J-result", path,
                                 f"rests_on_default must be {str(default).lower()}: a source has the type default, or defaults is not empty, or neither",
                                 "rests_on_default"))
    return out


def j_once(ctx):
    """A value is on 1 page only: the item page of a Result page of the same run holds no field that the Result page holds."""
    out = []
    for path, page in ctx.of_type("Result").items():
        about = page.frontmatter.get("about")
        target = ctx.at(about) if about else None
        if target is None or target.error or own_run(target) != own_run(page):
            continue
        for name in MOVED.get((page.frontmatter.get("kind"), target.type), ()):
            if name in target.frontmatter:
                out.append(ctx.issue(ERROR, "J-once", about_path(ctx, about),
                                     f"{name} is on the Result page {path.stem}, so the {target.type} page must not hold it", name))
    return out


def about_path(ctx, link):
    return ctx.dir / link.lstrip("/")


def j_stale(ctx):
    return [ctx.issue(ERROR, "J-stale", path, "the generated part is stale. Run jtbd_graph.py regen.")
            for path in regen.differences(ctx.root, ctx.dir)]


RULES = [j_schema, j_id, j_link, j_required, j_run, j_tree, j_score, j_rank, j_finished, j_result, j_once, j_stale]
