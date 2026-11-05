"""Rule E7: one name for one thing in one context (Evans §A7).

Within one context, two live pages have the same title or alias, or a title
is also in the `avoid` list of another page. A name is compared with no
case, and with spaces, hyphens, and underscores removed, so `Order placed`
and `OrderPlaced` are the same name.
"""
import re
from collections import defaultdict

from .bundle import Bundle, context_id, glossary_types, names
from .issues import ERROR, Issue
from .page import line_of


def fold(name) -> str:
    return re.sub(r"[\s_-]+", "", str(name)).casefold()


def e7(bundle: Bundle) -> list:
    groups = defaultdict(list)
    for page in bundle.pages.values():
        if page.type in glossary_types() and page.live:
            context = context_id(bundle, page)
            if context != "-":
                groups[context].append(page)
    out = []
    for context, pages in sorted(groups.items()):
        owner = {}
        for page in sorted(pages, key=lambda p: p.path):
            for name in [page.title] + names(page.frontmatter.get("aliases")):
                key = fold(name)
                first = owner.setdefault(key, page)
                if first is not page:
                    out.append(Issue(ERROR, "E7", page.path, line_of(page, "title"),
                                     f"the name {name!r} is also a name of "
                                     f"{first.id} in {context}"))
        by_title = defaultdict(list)
        for page in pages:
            by_title[fold(page.title)].append(page)
        for page in pages:
            for word in names(page.frontmatter.get("avoid")):
                for other in by_title.get(fold(word), []):
                    if other is not page:
                        out.append(Issue(ERROR, "E7", other.path,
                                         line_of(other, "title"),
                                         f"the title {other.title!r} is in the "
                                         f"avoid list of {page.id} in {context}"))
    return out


RULES = [e7]
