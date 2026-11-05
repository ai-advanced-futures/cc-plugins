"""The generated indexes and links.tsv.

- each type directory `index.md`: one line for each page, with no
  frontmatter. Term, Aggregate, and Event lines are grouped under one
  heading for each context. Deprecated pages go under `## Deprecated`.
- the bundle-root `index.md`: the list of contexts and one link for each
  type directory that exists now, between the markers. The text around the
  markers belongs to the user.
- `links.tsv`: one row for each stored edge.
"""
from .bundle import Bundle, context_id, context_page, glossary_types, sort_key, stored_edges
from .config import OKF_VERSION
from .links import replace_marked
from .page import FRONTMATTER_RE, read_text
from .schema import types

ROOT_START = "<!-- DDD:INDEX START (generated, do not edit) -->"
ROOT_END = "<!-- DDD:INDEX END -->"
TSV_HEADER = ("source", "relation", "target", "source_type", "target_type",
              "source_context", "target_context", "target_status")
ROOT_DEFAULT = (
    f'---\nokf_version: "{OKF_VERSION}"\n---\n\n# Domain model\n\n'
    "The domain model of this repository. One page holds one bounded "
    "context, term, aggregate, event, relationship, question, or source.\n")


def _one_line(value) -> str:
    return " ".join(str(value or "").split())


def index_line(page, link: str | None = None) -> str:
    link = link or f"{page.id}.md"
    return f"* [{page.id}: {page.title}]({link}) - {_one_line(page.frontmatter.get('description'))}"


def _section(heading: str, pages) -> str:
    return "\n".join([heading, ""] + [index_line(p) for p in pages])


def _by_id(pages):
    return sorted(pages, key=lambda p: sort_key(p.id))


def directory_pages(bundle: Bundle, type_name: str):
    """(page files, parsed pages) of the directory of one type."""
    directory = bundle.dir / types()[type_name]["directory"]
    files = [p for p in list(bundle.pages) + list(bundle.broken)
             if p.parent == directory]
    pages = [bundle.pages[p] for p in files if p in bundle.pages]
    return files, _by_id(pages)


def directory_index(bundle: Bundle, type_name: str):
    """The text of one type index, or None when the directory holds no page
    file: a directory with no pages does not exist."""
    files, pages = directory_pages(bundle, type_name)
    if not files:
        return None
    directory = types()[type_name]["directory"]
    sections = [f"# {directory.capitalize()}"]
    live = [p for p in pages if p.live]
    if type_name in glossary_types():
        groups = {}
        for page in live:
            context = context_page(bundle, page)
            groups.setdefault(context and context.id, (context, []))[1].append(page)
        for key in sorted((k for k in groups if k is not None), key=sort_key):
            context, members = groups[key]
            sections.append(_section(f"## {key}: {context.title}", members))
        if None in groups:
            sections.append(_section("## No context", groups[None][1]))
    elif live:
        sections.append("\n".join(index_line(p) for p in live))
    dead = [p for p in pages if not p.live]
    if dead:
        sections.append(_section("## Deprecated", dead))
    if not pages:
        sections.append("No page of this directory parses. Run `ddd.py check`.")
    return "\n\n".join(sections) + "\n"


def root_block(bundle: Bundle) -> str:
    contexts = [p for p in bundle.pages.values()
                if p.type == "Context" and p.live]
    context_lines = [index_line(p, p.path.relative_to(bundle.dir).as_posix())
                     for p in _by_id(contexts)] or ["No context yet."]
    type_lines = []
    for type_name, spec in types().items():
        files, _pages = directory_pages(bundle, type_name)
        if files:
            name = spec["directory"]
            type_lines.append(f"* [{name.capitalize()}]({name}/index.md)")
    return "\n".join([ROOT_START, "## Contexts", "", *context_lines, "",
                      "## Types", "", *(type_lines or ["No page yet."]),
                      ROOT_END])


def root_index(bundle: Bundle) -> str:
    """The root index with a new generated block. The frontmatter and the
    text around the markers stay byte for byte."""
    path = bundle.dir / "index.md"
    text = read_text(path) if path.is_file() else ROOT_DEFAULT
    match = FRONTMATTER_RE.match(text)
    head = text[:match.end()] if match else ""
    return head + replace_marked(text[len(head):], ROOT_START, ROOT_END,
                                 root_block(bundle))


def _cell(value) -> str:
    return _one_line(value) or "-"


def links_tsv(bundle: Bundle) -> str:
    order = list(types())
    rows = ["\t".join(TSV_HEADER)]
    pages = sorted(bundle.pages.values(),
                   key=lambda p: (order.index(p.type) if p.type in order
                                  else len(order), sort_key(p.id)))
    for page in pages:
        for field_name, target_id, target in stored_edges(bundle, page):
            other = bundle.pages.get(target)
            rows.append("\t".join(_cell(v) for v in (
                page.id, field_name, target_id, page.type,
                other.type if other else "-",
                context_id(bundle, page), context_id(bundle, other),
                other.status if other else "missing")))
    return "\n".join(rows) + "\n"
