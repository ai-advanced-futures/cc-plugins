"""links.tsv at the root of each bundle (standard section 2)."""
from __future__ import annotations

import re

HEADER = "source\trelation\ttarget\n"
GRAPH_RE = re.compile(r"^[a-z][a-z0-9-]*:/[^/\s]\S*$")


def _links(value) -> list[str]:
    if isinstance(value, str):
        v = value.strip()
        return [v] if (v.startswith("/") and ".md" in v) or GRAPH_RE.match(v) else []
    if isinstance(value, list):
        return [x for item in value for x in _links(item)]
    if isinstance(value, dict):
        return [x for item in value.values() for x in _links(item)]
    return []


def text(bundle, base, for_links) -> str:
    rows = set()
    for path, (page_bundle, frontmatter) in for_links.items():
        if page_bundle != bundle:
            continue
        for key, value in frontmatter.items():
            if key in ("generated", "verified"):
                continue
            rows |= {("/" + path.relative_to(base).as_posix(), key, link) for link in _links(value)}
    return HEADER + "".join(f"{s}\t{r}\t{t}\n" for s, r, t in sorted(rows))
