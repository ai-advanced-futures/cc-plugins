"""regen of the generic graph: the indexes, the LINKS blocks, and links.tsv."""
from __future__ import annotations

import os
from pathlib import Path

from knowledgelib import links as linklib
from knowledgelib import okf, registry
from knowledgelib.graph import HEADINGS, INVERSE, ROOT_LINES, TYPES, bundle_dir
from knowledgelib.okf import oneline


def _pages(bundle) -> dict:
    out = {}
    for folder in TYPES.values():
        for file in sorted((bundle / folder).glob("*.md")):
            if file.name != "index.md":
                out[file] = okf.read_page(file)
    return out


def _rel(target, start) -> str:
    return os.path.relpath(target, start).replace(os.sep, "/")


def _line(root, graphs, bundle, file, field, value, pages) -> str:
    if value.startswith("/"):
        target = bundle / value.lstrip("/").split("#")[0]
        if target in pages:
            title = okf.label((pages[target].frontmatter or {}).get("title") or target.stem)
            return f"- {field}: [{title}]({_rel(target, file.parent)})"
        return f"- {field}: {value} (missing)"
    name, path = linklib.split(value)
    graph = graphs.get(name)
    if graph is None or graph.remote:
        return f"- {field}: {value}"
    return f"- {field}: [{value}]({_rel(Path(root) / graph.path / path.lstrip('/'), file.parent)})"


def with_block(body, lines) -> str:
    rest = okf.strip_links_block(body).rstrip("\n")
    if not lines:
        return rest + "\n"
    return rest + "\n\n" + "\n".join([okf.LINKS_START, "", "## Links", ""] + lines + [okf.LINKS_END]) + "\n"


def expected(root, bundle=None) -> dict:
    bundle = Path(bundle) if bundle else bundle_dir(root)
    graphs = registry.read(root)
    pages = _pages(bundle)
    inverse = {file: [] for file in pages}
    rows, out = [], {}
    for file, page in pages.items():
        if page.error:
            continue
        for field, value in okf.frontmatter_links(page.frontmatter):
            rows.append((okf.bundle_path(bundle, file), field, value))
            target = bundle / value.lstrip("/").split("#")[0] if value.startswith("/") else None
            if target in inverse and field in INVERSE:
                title = okf.label(page.frontmatter.get("title"))
                inverse[target].append(f"- {INVERSE[field]}: [{title}]({_rel(file, target.parent)})")
    for file, page in pages.items():
        if page.error:
            continue
        text = okf.read_text(file)
        head = text[: len(text) - len(page.body)]
        lines = [_line(root, graphs, bundle, file, f, v, pages) for f, v in okf.frontmatter_links(page.frontmatter)]
        out[file] = head + with_block(page.body, lines + sorted(set(inverse[file])))
    for folder in TYPES.values():
        entries = [f"* [{okf.label(p.frontmatter.get('title'))}]({f.name}) - {oneline(p.frontmatter.get('description'))}"
                   for f, p in pages.items() if f.parent == bundle / folder and not p.error]
        out[bundle / folder / "index.md"] = "\n".join([f"# {HEADINGS[folder]}", ""] + entries) + "\n"
    root_lines = [f"* [{title}]({link}) - {text}" for title, link, text in ROOT_LINES]
    out[bundle / "index.md"] = '---\nokf_version: "0.2"\n---\n\n# Knowledge\n\n' + "\n".join(root_lines) + "\n"
    out[bundle / "links.tsv"] = "source\trelation\ttarget\n" + "".join(f"{s}\t{r}\t{t}\n" for s, r, t in sorted(rows))
    return out


def _stale(plan) -> list[Path]:
    return sorted(path for path, text in plan.items() if not path.is_file() or okf.read_text(path) != text)


def differences(root, bundle=None) -> list[Path]:
    return _stale(expected(root, bundle))


def write(root, bundle=None) -> list[Path]:
    plan = expected(root, bundle)
    changed = _stale(plan)
    for path in changed:
        okf.write_text(path, plan[path])
    return changed
