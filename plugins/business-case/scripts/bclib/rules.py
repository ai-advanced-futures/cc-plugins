"""The brain rules of the business-case graph (spec, "Brain check")."""
from __future__ import annotations

import re
from pathlib import Path

from bclib import manifest, regen, schema
from bclib.bundle import ID_RE
from bclib.issues import ERROR, SKIP, WARN, Issue
from bclib.mapping import ALIAS_TAIL, SECTION_PART, SECTIONS, SNAPSHOT_DIR, SOURCE_RESULT_RE


def run_keys(page) -> list[str]:
    return schema.edge_values(page.frontmatter, "run")


def case_key(ctx, path, page) -> str:
    """The bundle path of the Case page that the page belongs to."""
    if page.type == "Case":
        return "/" + path.relative_to(ctx.dir).as_posix()
    return (schema.edge_values(page.frontmatter, "case") or [""])[0]


def bc_schema(ctx):
    out = [ctx.issue(ERROR, "BC-schema", p, pg.error) for p, pg in ctx.pages.items() if pg.error]
    for path, page in ctx.pages.items():
        if not page.error and not page.type:
            out.append(ctx.issue(ERROR, "BC-schema", path, "the page has no type"))
    for path, page in ctx.ok().items():
        for problem in schema.validate(page.type, page.frontmatter):
            out.append(ctx.issue(ERROR, "BC-schema", path, problem, problem.split(":")[0].split(".")[0]))
    return out


def bc_id(ctx):
    out = []
    for path, page in ctx.ok().items():
        spec = schema.types().get(page.type)
        if spec is None:
            out.append(ctx.issue(ERROR, "BC-id", path, f"{page.type!r} is not a page type of business-case", "type"))
            continue
        match = ID_RE.match(path.stem)
        if path.parent != ctx.dir / spec["directory"] or not match or match.group(1) != spec["prefix"]:
            out.append(ctx.issue(ERROR, "BC-id", path, f"a {page.type} page is {spec['directory']}/{spec['prefix']}-NN.md", "type"))
    return out


def bc_link(ctx):
    """A link points to a page that exists, of a type that the field allows."""
    out = []
    for path, page in ctx.ok().items():
        for name, spec in schema.edges().items():
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                target = ctx.at(value)
                if target is None or target.error:
                    out.append(ctx.issue(ERROR, "BC-link", path, f"{name}: {value} does not exist", name))
                elif target.type not in spec["targets"]:
                    out.append(ctx.issue(ERROR, "BC-link", path,
                                         f"{name}: {value} is a {target.type}, not a {' or '.join(spec['targets'])}", name))
                elif not target.live and page.live:
                    out.append(ctx.issue(WARN, "BC-link", path, f"{name}: {value} is deprecated", name))
    return out


def bc_required(ctx):
    out = []
    required = (manifest.read(ctx.dir) or {}).get("required_links") or schema.REQUIRED_LINKS
    for path, page in ctx.ok().items():
        for name in required.get(page.type, []):
            if not schema.edge_values(page.frontmatter, name):
                out.append(ctx.issue(ERROR, "BC-required", path, f"a {page.type} page needs the link {name}", name))
    return out


def bc_case(ctx):
    """A page links to 1 Case page, and each page that it links to has the same case."""
    out = []
    for path, page in ctx.ok().items():
        mine = case_key(ctx, path, page)
        if page.type != "Case":
            target = ctx.at(mine) if mine.startswith("/") else None
            if target is None or target.type != "Case":
                out.append(ctx.issue(ERROR, "BC-case", path, f"case: {mine or '(none)'} is not a Case page", "case"))
                continue
        for name in schema.edges():
            if name == "case":
                continue
            for value in schema.edge_values(page.frontmatter, name):
                if not value.startswith("/"):
                    continue
                target = ctx.at(value)
                if target is not None and not target.error and target.type:
                    if case_key(ctx, target.path, target) != mine:
                        out.append(ctx.issue(ERROR, "BC-case", path, f"{name}: {value} belongs to another case", name))
    return out


def bc_run(ctx):
    out = []
    for path, page in ctx.ok().items():
        if page.type in ("Case", "Run"):
            continue
        keys = run_keys(page)
        if not keys:
            out.append(ctx.issue(ERROR, "BC-run", path, "the page has no link to a Run page", "run"))
        for key in keys:
            target = ctx.at(key)
            if target is None:
                continue
            if target.type != "Run":
                out.append(ctx.issue(ERROR, "BC-run", path, f"run: {key} is not a Run page", "run"))
            elif case_key(ctx, target.path, target) != case_key(ctx, path, page):
                out.append(ctx.issue(ERROR, "BC-run", path, f"run: {key} is a run of another case", "run"))
    return out


def _alias_problem(ctx, path, page, slug_of, heads):
    slug = slug_of(path, page)
    aliases = [str(a) for a in (page.frontmatter.get("aliases") or [])]
    fm = page.frontmatter
    if page.type == "Case":
        return None if f"{fm.get('slug')}" in aliases else f"the alias {fm.get('slug')!r} is missing"
    if slug is None:
        return None
    if page.type == "Run":
        want = f"{slug}/{fm.get('run_id')}"
        return None if want in aliases else f"the alias {want!r} is missing"
    if page.type == "Part":
        pattern = re.compile(re.escape(f"{slug}/{fm.get('section')}") + r"(/\d+)?")
        hits = [a for a in aliases if pattern.fullmatch(a)]
        if not hits:
            return f"the alias {slug}/{fm.get('section')}[/N] is missing"
        first = path in heads
        if first and f"{slug}/{fm.get('section')}" not in aliases:
            return f"the first page of a section has the alias {slug}/{fm.get('section')}"
        return None
    tail = ALIAS_TAIL.get(page.type)
    if tail is None:
        return None
    if not any(re.fullmatch(re.escape(slug) + "/" + tail.pattern, a) for a in aliases):
        return f"the alias {slug}/{tail.pattern} is missing"
    return None


def bc_alias(ctx):
    out, seen = [], {}
    slugs = {}
    for path, page in ctx.ok().items():
        if page.type == "Case":
            slugs["/" + path.relative_to(ctx.dir).as_posix()] = str(page.frontmatter.get("slug") or "")
    followed = {str(v) for _p, pg in ctx.ok().items() if pg.type == "Part" for v in schema.edge_values(pg.frontmatter, "next")}
    heads = {p for p, pg in ctx.ok().items() if pg.type == "Part" and "/" + p.relative_to(ctx.dir).as_posix() not in followed}

    def slug_of(path, page):
        return slugs.get(case_key(ctx, path, page))

    for path, page in ctx.ok().items():
        problem = _alias_problem(ctx, path, page, slug_of, heads)
        if problem:
            out.append(ctx.issue(ERROR, "BC-alias", path, problem, "aliases"))
        for alias in page.frontmatter.get("aliases") or []:
            seen.setdefault(str(alias).casefold(), []).append(path)
    for alias, paths in seen.items():
        if len(paths) > 1:
            names = ", ".join(p.stem for p in sorted(paths))
            out += [ctx.issue(ERROR, "BC-alias", p, f"the alias {alias!r} is on more than 1 page: {names}", "aliases")
                    for p in paths]
    return out


def bc_part(ctx):
    out = []
    cases = {"/" + p.relative_to(ctx.dir).as_posix(): p for p, pg in ctx.ok().items() if pg.type == "Case"}
    for key, case_path in cases.items():
        parts = [(p, pg) for p, pg in ctx.ok().items() if pg.type == "Part" and case_key(ctx, p, pg) == key]
        by_section = {}
        for path, page in parts:
            section = page.frontmatter.get("section")
            by_section.setdefault(section, []).append((path, page))
            want = SECTION_PART.get(section)
            if want is None:
                out.append(ctx.issue(ERROR, "BC-part", path, f"{section!r} is not a section of the template", "section"))
            elif page.frontmatter.get("part") != want:
                out.append(ctx.issue(ERROR, "BC-part", path, f"part must be {want} for the section {section}", "part"))
        for section in SECTIONS:
            pages = by_section.get(section)
            if not pages:
                out.append(ctx.issue(ERROR, "BC-part", case_path, f"the case has no Part page for the section {section}"))
                continue
            followed = {v for _p, pg in pages for v in schema.edge_values(pg.frontmatter, "next")}
            heads = [p for p, _pg in pages if "/" + p.relative_to(ctx.dir).as_posix() not in followed]
            if len(heads) != 1:
                out.append(ctx.issue(ERROR, "BC-part", pages[0][0],
                                     f"the section {section} has {len(heads)} first pages, and needs 1 chain linked by next", "next"))
    return out


def bc_source(ctx):
    out = []
    for path, page in ctx.ok().items():
        if page.type != "Evidence":
            continue
        links = schema.edge_values(page.frontmatter, "source_results")
        if not links:
            continue
        for link in links:
            if not SOURCE_RESULT_RE.match(link):
                out.append(ctx.issue(ERROR, "BC-source", path, f"source_results: {link} is not <graph>:/results/RESULT-NN.md", "source_results"))
        ref = page.frontmatter.get("result_ref")
        ref_path = ref.get("path") if isinstance(ref, dict) else None
        if not isinstance(ref_path, str) or f"/{SNAPSHOT_DIR}" not in f"/{ref_path}":
            out.append(ctx.issue(ERROR, "BC-source", path, f"result_ref.path must be a snapshot path under {SNAPSHOT_DIR}", "result_ref"))
    return out


def _case_folder(ctx, page):
    folder = page.frontmatter.get("case_folder")
    if not isinstance(folder, str) or not folder:
        return None
    target = Path(ctx.root) / folder
    return target if target.is_dir() else None


def bc_fresh(ctx):
    """Each page of a case holds the values that `publish` would write now."""
    from bclib import publish

    out = []
    for path, page in ctx.ok().items():
        if page.type != "Case":
            continue
        folder = _case_folder(ctx, page)
        if folder is None:
            continue
        try:
            items = publish.plan(folder, page.frontmatter.get("case_folder"))
        except Exception as error:  # a case that cannot be read is not a stale page
            out.append(ctx.issue(WARN, "BC-fresh", path, f"the case folder cannot be read: {error}"))
            continue
        by_alias = publish.pages_by_alias(ctx.pages)
        for item in items:
            have = by_alias.get(item.alias.casefold())
            if have is None:
                out.append(ctx.issue(WARN, "BC-fresh", path, f"{item.alias} has no page. Run publish."))
            elif publish.differs(item, ctx.pages[have]):
                out.append(ctx.issue(WARN, "BC-fresh", have, f"{item.alias} differs from the case. Run publish, or the page was edited."))
    return out


def bc_upstream(ctx):
    """The value of a Result page that an Evidence page names is the value in the snapshot of the case."""
    from bclib import knowledge_client, publish

    pairs = [(p, pg, link) for p, pg in ctx.ok().items() if pg.type == "Evidence"
             for link in schema.edge_values(pg.frontmatter, "source_results")]
    if not pairs:
        return []
    client = knowledge_client.Knowledge.find(ctx.root)
    if client is None:
        return [Issue(SKIP, "BC-upstream", "the knowledge plugin is not installed, so the check reads no Result page")]
    graphs = set(ctx.registry)
    out = []
    for path, page, link in pairs:
        graph = link.split(":", 1)[0]
        if graph not in graphs:
            continue
        shown = client.show([link]).get(link)
        frontmatter = (shown or {}).get("frontmatter")
        if not frontmatter:
            continue
        case_page = ctx.at(case_key(ctx, path, page))
        folder = _case_folder(ctx, case_page) if case_page is not None else None
        if folder is None:
            continue
        snapshot = publish.snapshot_value(ctx.root, folder, page.frontmatter.get("result_ref"), frontmatter)
        if snapshot is publish.NO_ENTRY:
            out.append(ctx.issue(WARN, "BC-upstream", path, f"no snapshot of the case holds the entry of {link}", "source_results"))
        elif snapshot != frontmatter.get("value"):
            out.append(ctx.issue(WARN, "BC-upstream", path,
                                 f"{link} changed after the grade: its value differs from the snapshot", "source_results"))
    return out


def bc_stale(ctx):
    return [ctx.issue(ERROR, "BC-stale", path, "the generated part is stale. Run bc_graph.py regen.")
            for path in regen.differences(ctx.root, ctx.dir)]


RULES = [bc_schema, bc_id, bc_link, bc_required, bc_case, bc_run, bc_alias, bc_part, bc_source,
         bc_fresh, bc_upstream, bc_stale]
