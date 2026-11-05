"""regen: the indexes, the LINKS blocks, links.tsv, and (Task 32) the system.md blocks."""
from __future__ import annotations

import os
import re
from pathlib import Path

from sdlib import schema, system_blocks
from sdlib.bundle import read, read_registry, ref
from sdlib.page import read_text, write_text

LINKS_START = "<!-- LINKS:START (generated, do not edit) -->"
LINKS_END = "<!-- LINKS:END -->"
SD_BLOCK_RE = re.compile(r"\n*<!-- SD:[A-Z-]+:START \(generated, do not edit\) -->.*?<!-- SD:[A-Z-]+:END -->\n*", re.DOTALL)
HEADINGS = {"areas": "Areas", "components": "Components", "interfaces": "Interfaces", "data": "Data entities",
            "scenarios": "Quality scenarios", "conventions": "Conventions", "risks": "Technical risks",
            "deferred": "Deferred decisions", "assumptions": "Assumptions", "nodes": "Deployment nodes",
            "glossary": "Glossary"}
TYPE_TEXT = {"areas": "The eight design areas, in blocking order.",
             "components": "The building blocks, and the outside systems with kind external.",
             "interfaces": "The contracts at each boundary.", "data": "The shared data entities and their owners.",
             "scenarios": "The quality scenarios.", "conventions": "The crosscutting rules.",
             "risks": "The technical risks, the debt, and the non-risks.",
             "deferred": "The decisions left to a later spec.", "assumptions": "The decisions inferred from code.",
             "nodes": "The places where components run.", "glossary": "The technical terms of the system."}


def _rel(target, start) -> str:
    return os.path.relpath(target, start).replace(os.sep, "/")


def oneline(value) -> str:
    return " ".join(str(value or "").split())


def strip_generated(body) -> str:
    start = body.find(LINKS_START)
    if start >= 0:
        end = body.find(LINKS_END, start)
        body = body[:start] + (body[end + len(LINKS_END):] if end >= 0 else "")
    return SD_BLOCK_RE.sub("\n\n", body).rstrip("\n")


def assemble(body, sections, lines) -> str:
    parts = [strip_generated(body)] + list(sections)
    if lines:
        parts.append("\n".join([LINKS_START, "", "## Links", ""] + lines + [LINKS_END]))
    return "\n\n".join(p for p in parts if p) + "\n"


def _graph_line(root, registry, label, value, start) -> str:
    if ":" not in value:
        # A hand-edited value with no `<graph>:/` form is not a link; E2 reports the bad value. [inferred]
        return f"- {label}: {value} (not a link)"
    name, path = value.split(":", 1)
    entry = registry.get(name)
    if entry and "repo" not in entry:
        return f"- {label}: [{value}]({_rel(Path(root) / entry['path'] / path.lstrip('/'), start)})"
    return f"- {label}: {value}"


def page_links(bundle, registry, path, page):
    """The out lines of one page, and the (target, inverse line) pairs that it gives."""
    out, inverse = [], []
    targets = [(name.replace(".", " ").replace("_", " "), value, spec.get("inverse_label"))
               for name, spec in schema.edges().items() for value in schema.edge_values(page.frontmatter, name)]
    targets += [("area", f"/areas/{slug}.md", "named by")
                for key in ("areas", "area") for slug in schema.edge_values(page.frontmatter, key)]
    for label, value, inverse_label in targets:
        if not value.startswith("/"):
            out.append(_graph_line(bundle.root, registry, label, value, path.parent))
            continue
        target = bundle.dir / value.lstrip("/")
        found = bundle.pages.get(target)
        if found is None or found.error:
            out.append(f"- {label}: {value} (missing)")
            continue
        out.append(f"- {label}: [{found.id}: {found.title}]({_rel(target, path.parent)})")
        if inverse_label:
            inverse.append((target, f"- {inverse_label}: [{page.id}: {page.title}]({_rel(path, target.parent)})"))
    return out, inverse


def expected(root, directory=None) -> dict:
    bundle = read(root, directory)
    registry = read_registry(root)
    pages = {p: pg for p, pg in bundle.pages.items() if not pg.error}
    lines, inverse, rows = {p: [] for p in pages}, {p: [] for p in pages}, []
    for path, page in pages.items():
        out, back = page_links(bundle, registry, path, page)
        lines[path] = out
        for target, line in back:
            if target in inverse:
                inverse[target].append(line)
        for name in schema.edges():
            rows += [(ref(bundle.dir, path), name, v) for v in schema.edge_values(page.frontmatter, name)]
    result = {}
    for path, page in pages.items():
        sections = system_blocks.sections(root, registry, bundle.dir, pages) if path == bundle.dir / "system.md" else []
        result[path] = page.head + assemble(page.body, sections, lines[path] + sorted(set(inverse[path])))
    for folder in HEADINGS:
        entries = []
        if folder == "areas":
            for slug in schema.areas():
                found = pages.get(bundle.dir / "areas" / f"{slug}.md")
                if found:
                    fm = found.frontmatter
                    entries.append(f"* [{found.title}]({slug}.md) - {fm.get('area_state')}: {oneline(fm.get('description'))}")
        else:
            for path in sorted(p for p in pages if p.parent == bundle.dir / folder):
                entries.append(f"* [{path.stem}: {pages[path].title}]({path.name}) - {oneline(pages[path].frontmatter.get('description'))}")
        result[bundle.dir / folder / "index.md"] = "\n".join([f"# {HEADINGS[folder]}", ""] + entries) + "\n"
    system = pages.get(bundle.dir / "system.md")
    system_text = oneline(system.frontmatter.get("description")) if system else "The system in scope."
    root_lines = [f"* [System](system.md) - {system_text}",
                  "* [Manifest](manifest.md) - What this bundle is and how to read it.",
                  "* [Log](log.md) - The record of each change, newest first."]
    root_lines += [f"* [{HEADINGS[f]}]({f}/index.md) - {TYPE_TEXT[f]}" for f in HEADINGS]
    result[bundle.dir / "index.md"] = '---\nokf_version: "0.2"\n---\n\n# System design\n\n' + "\n".join(root_lines) + "\n"
    result[bundle.dir / "links.tsv"] = "source\trelation\ttarget\n" + "".join(f"{s}\t{r}\t{t}\n" for s, r, t in sorted(rows))
    return result


def _stale(plan) -> list[Path]:
    return sorted(path for path, text in plan.items() if not path.is_file() or read_text(path) != text)


def differences(root, directory=None) -> list[Path]:
    return _stale(expected(root, directory))


def write(root, directory=None) -> list[Path]:
    plan = expected(root, directory)
    changed = _stale(plan)
    for path in changed:
        write_text(path, plan[path])
    return changed
