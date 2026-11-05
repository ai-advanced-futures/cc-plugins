"""The brain check of the generic graph: G1 to G5."""
from __future__ import annotations

from knowledgelib import graph_regen, okf
from knowledgelib.graph import SLUG_RE, TYPES, bundle_dir, validate
from knowledgelib.issues import ERROR, WARN, Issue
from knowledgelib.okf import shown

def run(root) -> list[Issue]:
    bundle = bundle_dir(root)
    issues, pages, inbound = [], {}, set()
    for file in okf.bundle_pages(bundle):
        where = shown(root, file)
        page = okf.read_page(file)
        if page.error:
            issues.append(Issue(ERROR, "G1", page.error, where))
            continue
        type_name = page.frontmatter.get("type")
        parts = file.relative_to(bundle).parts
        if type_name not in TYPES:
            issues.append(Issue(ERROR, "G2", f"{type_name!r} is not a type of the generic graph", where))
            continue
        if len(parts) != 2 or parts[0] != TYPES[type_name]:
            issues.append(Issue(ERROR, "G2", f"a {type_name} page belongs in {TYPES[type_name]}/", where))
        if not SLUG_RE.fullmatch(file.stem):
            issues.append(Issue(ERROR, "G3", "the file name is not a lowercase slug", where))
        for problem in validate(type_name, page.frontmatter):
            issues.append(Issue(ERROR, "G1", problem, where))
        pages[file] = page
        links = [v for _f, v in okf.frontmatter_links(page.frontmatter)] + okf.body_links(file, bundle, page.body)
        for value in links:
            if value.startswith("/") and bundle / value.lstrip("/") != file:
                inbound.add(bundle / value.lstrip("/").split("#")[0])
    for file, page in pages.items():
        if page.frontmatter.get("type") != "Source" and file not in inbound:
            issues.append(Issue(WARN, "G4", "no other page links to this page. Link it from a page, or forget it.", shown(root, file)))
    for path in graph_regen.differences(root):
        issues.append(Issue(ERROR, "G5", "the generated part is stale. Run knowledge_graph.py regen.", shown(root, path)))
    return issues
