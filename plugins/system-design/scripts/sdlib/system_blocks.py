"""The five generated blocks of system.md (spec section 8.2)."""
from __future__ import annotations

import os
from pathlib import Path

from sdlib import schema

ORDER = ("DESIGN-MAP", "DECISION-INDEX", "REQUIREMENTS", "COMPONENT-MAP", "CONTEXT-MAP")


def block(name, lines) -> str:
    return "\n".join([f"<!-- SD:{name}:START (generated, do not edit) -->", ""] + lines + ["", f"<!-- SD:{name}:END -->"])


def node(link_or_id) -> str:
    return Path(link_or_id).stem.replace("-", "_")


def _areas(directory, pages):
    return [(slug, pages.get(directory / "areas" / f"{slug}.md")) for slug in schema.areas()]


def design_map(directory, pages, system) -> list[str]:
    fm = system.frontmatter
    lines = ["## Design map", "", f"Destination: {fm.get('destination') or 'not stated'}", "", "### Frontier", ""]
    frontier = [f"- [{p.title}](areas/{slug}.md): {'; '.join(p.frontmatter.get('open_rows') or []) or 'no row yet'}"
                for slug, p in _areas(directory, pages) if p and p.frontmatter.get("area_state") == "open"]
    lines += frontier or ["- none"]
    lines += ["", "### Fog", ""]
    fog = [f"- {item.get('key')}: {item.get('question')} ([{slug}](areas/{slug}.md))"
           for slug, p in _areas(directory, pages) if p for item in p.frontmatter.get("fog") or []]
    lines += fog or ["- none"]
    lines += ["", "### Out of scope", ""]
    lines += [f"- {o.get('item')}: {o.get('reason')}" for o in fm.get("out_of_scope") or []] or ["- none"]
    return lines


def decision_index(root, registry, directory, pages) -> list[str]:
    lines = ["## Decision index", "", "| Row key | ADR | Area | What it binds | Source |", "|---|---|---|---|---|"]
    for slug, p in _areas(directory, pages):
        for row in (p.frontmatter.get("decisions") if p else None) or []:
            adr = row.get("adr") or ""
            cell = adr
            entry = registry.get("adr")
            if adr and entry and "repo" not in entry:
                target = Path(root) / entry["path"] / adr.split(":", 1)[1].lstrip("/")
                cell = f"[{adr}]({os.path.relpath(target, directory).replace(os.sep, '/')})"
            lines.append(f"| {row.get('key')} | {cell} | {slug} | {row.get('binds')} | {row.get('source')} |")
    return lines


def components(pages):
    return sorted((p for p in pages.values() if p.type == "Component" and p.live), key=lambda p: p.id)


def requirements(pages) -> list[str]:
    lines = ["## Requirements to components", "", "| Capability | Components |", "|---|---|"]
    by_capability = {}
    for comp in components(pages):
        for capability in schema.edge_values(comp.frontmatter, "realizes"):
            by_capability.setdefault(capability, []).append(comp.id)
    lines += [f"| {cap} | {', '.join(ids)} |" for cap, ids in sorted(by_capability.items())]
    return lines


def _shape(comp) -> str:
    title = comp.title.replace('"', "'")
    return f'{node(comp.id)}[["{title}"]]' if comp.frontmatter.get("kind") == "external" else f'{node(comp.id)}["{title}"]'


def component_map(pages) -> list[str]:
    lines = ["## Component map", "", "```mermaid", "flowchart LR"]
    lines += [f"  {_shape(comp)}" for comp in components(pages)]
    for comp in components(pages):
        for use in comp.frontmatter.get("uses") or []:
            label = " ".join(x for x in (use.get("style"), Path(use["via"]).stem if use.get("via") else "") if x)
            lines.append(f"  {node(comp.id)} -->|{label}| {node(use['to'])}")
    return lines + ["```"]


def context_map(pages, system) -> list[str]:
    title = system.title.replace('"', "'")
    lines = ["## Context map", "", "```mermaid", "flowchart LR", f'  SYSTEM["{title}"]']
    personas = sorted({p for comp in components(pages) for p in schema.edge_values(comp.frontmatter, "used_by")})
    lines += [f'  {node(p)}(["{Path(p).stem}"]) --> SYSTEM' for p in personas]
    lines += [f"  SYSTEM --> {_shape(comp)}" for comp in components(pages) if comp.frontmatter.get("kind") == "external"]
    return lines + ["```"]


def sections(root, registry, directory, pages) -> list[str]:
    system = pages.get(directory / "system.md")
    if system is None:
        return []
    content = {"DESIGN-MAP": design_map(directory, pages, system),
               "DECISION-INDEX": decision_index(root, registry, directory, pages),
               "REQUIREMENTS": requirements(pages), "COMPONENT-MAP": component_map(pages),
               "CONTEXT-MAP": context_map(pages, system)}
    return [block(name, content[name]) for name in ORDER]
