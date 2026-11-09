"""regen: the indexes, the LINKS blocks, and links.tsv."""
from __future__ import annotations

import os
from pathlib import Path

from bclib import schema
from bclib.bundle import read, read_registry, ref
from bclib.page import read_text, write_text

LINKS_START = "<!-- LINKS:START (generated, do not edit) -->"
LINKS_END = "<!-- LINKS:END -->"
HEADINGS = {"cases": "Cases", "runs": "Runs", "parts": "Parts", "evidence": "Evidence", "decisions": "Decisions",
            "strategy": "Strategy entries", "conditions": "Conditions", "notes": "Notes", "figures": "Figures",
            "finance": "Finance", "reviews": "Reviews", "open-items": "Open items", "verdicts": "Item verdicts",
            "findings": "Findings"}
TYPE_TEXT = {"cases": "The business cases, one page for each case folder.",
             "runs": "The sessions of the coach on a case.",
             "parts": "The text of each section of a case, split into pages that a reader can open.",
             "evidence": "The evidence of the cases, with its grade and its source.",
             "decisions": "The decisions that people took, with their reasons.",
             "strategy": "The entries of the strategy register.",
             "conditions": "The conditions of the plans, with their marks.",
             "notes": "The notes of the strategy.",
             "figures": "The money figures that the plans use.",
             "finance": "The numbers that code computed from the figures.",
             "reviews": "The reports of the independent judge.",
             "open-items": "The rubric items that the loop of the coach has not closed, one page for each item.",
             "verdicts": "The verdict of each report of the judge on each rubric item.",
             "findings": "The findings of each report of the judge, one page for each finding."}


def _rel(target, start) -> str:
    return os.path.relpath(target, start).replace(os.sep, "/")


def oneline(value) -> str:
    return " ".join(str(value or "").split())


def strip_generated(body) -> str:
    start = body.find(LINKS_START)
    if start >= 0:
        end = body.find(LINKS_END, start)
        body = body[:start] + (body[end + len(LINKS_END):] if end >= 0 else "")
    return body.rstrip("\n")


def assemble(body, lines) -> str:
    parts = [strip_generated(body)]
    if lines:
        parts.append("\n".join([LINKS_START, "", "## Links", ""] + lines + [LINKS_END]))
    return "\n\n".join(p for p in parts if p) + "\n"


def _graph_line(root, registry, label, value, start) -> str:
    if ":" not in value:
        return f"- {label}: {value} (not a link)"
    name, path = value.split(":", 1)
    entry = registry.get(name)
    if entry and "repo" not in entry:
        return f"- {label}: [{value}]({_rel(Path(root) / entry['path'] / path.lstrip('/'), start)})"
    return f"- {label}: {value}"


def page_links(bundle, registry, path, page):
    """The out lines of one page, and the (target, inverse line) pairs that it gives."""
    out, inverse = [], []
    targets = [(name.replace("_", " "), value, spec.get("inverse_label"))
               for name, spec in schema.edges().items() for value in schema.edge_values(page.frontmatter, name)]
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
        result[path] = page.head + assemble(page.body, lines[path] + sorted(set(inverse[path])))
    for folder, heading in HEADINGS.items():
        entries = [f"* [{p.stem}: {pages[p].title}]({p.name}) - {oneline(pages[p].frontmatter.get('description'))}"
                   for p in sorted(p for p in pages if p.parent == bundle.dir / folder)]
        result[bundle.dir / folder / "index.md"] = "\n".join([f"# {heading}", ""] + entries) + "\n"
    root_lines = ["* [Manifest](manifest.md) - What this bundle is and how to read it.",
                  "* [Log](log.md) - The record of each change, newest first."]
    root_lines += [f"* [{heading}]({folder}/index.md) - {TYPE_TEXT[folder]}" for folder, heading in HEADINGS.items()]
    result[bundle.dir / "index.md"] = ('---\nokf_version: "0.2"\n---\n\n# Business case\n\n'
                                       + "\n".join(root_lines) + "\n")
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
