"""upgrade (A14) and the migration of docs/product/system-design.md (spec section 8.4)."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from sdlib import DataError, UsageError, logbook, manifest, regen, schema
from sdlib.bundle import DEFAULT_DIR, GRAPH, bundle_dir, page_files, read_registry, registry_add
from sdlib.ids import next_id
from sdlib.page import dump, ordered, parse, write_text
from sdlib.writer import check_dir, stamp

ACTOR = "process:system-design-upgrade"
SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
ID_LINE_RE = re.compile(r"^\s*[-*]?\s*\**(QS|CV|RK|DF)-(\d+)\**\s*[:.\-]?\s*(.+)$")
LABEL_RE = re.compile(r"(source|stimulus|environment|artifact|response measure|response|importance|risk|"
                      r"mitigation|acceptance|reason|trigger|area)\s*:\s*([^;|]+)", re.IGNORECASE)
ADR_NAME_RE = re.compile(r"^\d{4}(-\d{2}-\d{2})?-.+\.md$")
QUALITY_WORDS = {"performance": "performance-efficiency", "latency": "performance-efficiency",
                 "available": "reliability", "reliab": "reliability", "secur": "security",
                 "maintain": "maintainability", "usab": "interaction-capability", "compat": "compatibility",
                 "safety": "safety", "flexib": "flexibility", "portab": "flexibility", "correct": "functional-suitability"}


def upgrade(root, directory=None) -> list[str]:
    entry = read_registry(root).get(GRAPH) or {}
    directory = check_dir(directory) if directory else entry.get("path") or DEFAULT_DIR
    folder = Path(root) / directory
    if not folder.is_dir():
        raise UsageError(f"{directory} does not exist. Run init.")
    changes = []
    for spec in schema.types().values():
        if spec["directory"]:
            (folder / spec["directory"]).mkdir(exist_ok=True)
    for path in page_files(folder):
        page = parse(path)
        if page.error:
            raise DataError(f"{path}: {page.error}. Correct the page, then run upgrade again.")
        if not isinstance(page.frontmatter.get("generated"), dict):
            when = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0)
            write_text(path, dump({**page.frontmatter, "generated": {"by": ACTOR, "at": logbook.stamp(when)}}, page.body))
            changes.append(f"updated {path.relative_to(root).as_posix()}")
    if not (folder / "log.md").exists():
        (folder / "log.md").write_text(logbook.HEADER + "\n", encoding="utf-8")
        changes.append("added log.md")
    changes += [f"regenerated {p.relative_to(root).as_posix()}" for p in regen.write(root, folder)]
    data = manifest.read(folder)
    if data is None:
        manifest.write(folder, manifest.fields())
        changes.append("wrote manifest.md")
    elif data.get("plugin_version") != schema.plugin_version():
        data["plugin_version"] = schema.plugin_version()
        manifest.write(folder, data)
        changes.append("updated manifest.md")
    if registry_add(root, GRAPH, directory):
        changes.append("wrote the registry entry system-design")
    if changes:
        logbook.append(folder / "log.md", "Upgrade", f"brought {directory} to the brain standard ({len(changes)} changes)", ACTOR)
    return changes


def sections(body) -> dict:
    parts = SECTION_RE.split(body)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def table_rows(text) -> list[list[str]]:
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in text.splitlines() if line.strip().startswith("|") and not re.match(r"^\|\s*-", line.strip())]
    return rows[1:]


def labels(text) -> dict:
    return {m.group(1).lower(): m.group(2).strip() for m in LABEL_RE.finditer(text)}


def lead(text) -> str:
    match = LABEL_RE.search(text)
    return (text[: match.start()] if match else text).strip().rstrip(";").strip()


class Writer:
    def __init__(self, root, actor):
        self.root, self.actor = Path(root), actor
        self.folder = bundle_dir(root)
        self.numbers = {}
        self.written = set()

    def allocate(self, type_name) -> str:
        if type_name not in self.numbers:
            self.numbers[type_name] = int(next_id(self.folder, type_name).split("-")[1])
        page_id = f"{schema.types()[type_name]['prefix']}-{self.numbers[type_name]:02d}"
        self.numbers[type_name] += 1
        return f"/{schema.types()[type_name]['directory']}/{page_id}.md"

    def put(self, link, type_name, title, description, fields, body="") -> list[str]:
        fm = {"type": type_name, "title": title, "description": description, "status": "draft", **fields,
              "generated": stamp(self.actor)}
        fm = ordered({k: v for k, v in fm.items() if v not in (None, [], "")}, schema.types()[type_name]["key_order"])
        problems = schema.validate(type_name, fm)
        if problems:
            return problems
        page_id = Path(link).stem
        heading = f"# {page_id}: {title}" if schema.types()[type_name]["prefix"] else f"# {title}"
        write_text(self.folder / link.lstrip("/"), dump(fm, f"\n{heading}\n\n{body or description}\n"))
        self.written.add(link)
        return []

    def update(self, link, changes, body=None) -> None:
        page = parse(self.folder / link.lstrip("/"))
        fm = {**page.frontmatter, **changes, "generated": stamp(self.actor)}
        write_text(page.path, dump(fm, body if body is not None else page.body))


def migrate(root, old_path, actor=None) -> list[str]:
    old = Path(root) / old_path
    if not old.is_file():
        raise UsageError(f"{old_path} does not exist")
    page = parse(old)
    if page.error:
        raise DataError(f"{old_path}: {page.error}")
    w, fm, parts, report, ids = Writer(root, actor or schema.plugin_actor()), page.frontmatter, sections(page.body), [], {}
    block = re.search(r"```yaml\n(.*?)```", parts.get("Building blocks", ""), re.DOTALL)
    catalogue = (yaml.safe_load(block.group(1)) or {}).get("components") or [] if block else []
    contracts = [r for r in table_rows(parts.get("Contracts", "")) if r and r[0].startswith("IF-")]
    items = {kind: [m for m in (ID_LINE_RE.match(line) for line in parts.get(title, "").splitlines()) if m and m.group(1) == kind]
             for kind, title in (("QS", "Quality scenarios"), ("CV", "Crosscutting conventions"), ("RK", "Risks"), ("DF", "Deferred"))}
    for item in catalogue:
        ids[item["id"]] = w.allocate("Component")
    for row in contracts:
        ids[row[0]] = w.allocate("Interface")
    for kind, type_name in (("QS", "QualityScenario"), ("CV", "Convention"), ("RK", "TechnicalRisk"), ("DF", "Deferred")):
        for match in items[kind]:
            ids[f"{kind}-{match.group(2)}"] = w.allocate(type_name)

    def link_of(value):
        value = str(value)
        if ADR_NAME_RE.match(value):
            return f"adr:/{value}"
        if value.startswith("CAPABILITY-"):
            return f"prd:/capabilities/{value}.md"
        return ids.get(value)

    def component_of(text):
        text = text.strip()
        return ids.get(text) or next((ids[c["id"]] for c in catalogue if c.get("name") == text), None)

    written = w.written

    def done(old_id, problems):
        if problems:
            report.append(f"not migrated: {old_id} ({'; '.join(problems)})")

    kinds = {c["id"]: c.get("kind") for c in catalogue}
    for row in contracts:
        provider = component_of(row[1]) if len(row) > 1 else None
        consumers = [c for c in (component_of(x) for x in (row[2] if len(row) > 2 else "").split(",")) if c]
        if not provider or not consumers:
            report.append(f"not migrated: {row[0]} (the provider or a consumer is not a catalogue component)")
            continue
        ends = [row[1].strip()] + [x.strip() for x in row[2].split(",")]
        external = any(kinds.get(e) == "external" for e in ends)
        mechanism = row[3].strip().lower() if len(row) > 3 else "other"
        done(row[0], w.put(ids[row[0]], "Interface", row[0], f"The {row[0]} contract.", {
            "direction": "outbound" if external else "internal",
            "mechanism": mechanism if mechanism in ("openapi", "asyncapi", "graphql", "grpc", "event-schema", "cli", "file", "library-call") else "other",
            "style": "sync", "versioning": row[4] if len(row) > 4 else "", "provided_by": provider,
            "consumed_by": consumers, "aliases": [row[0]]}))
    for match in items["QS"]:
        old_id, text = f"QS-{match.group(2)}", match.group(3)
        lab, cite = labels(text), re.search(r"(CONSTRAINT|METRIC)-\d{2,}", text)
        quality = next((q for word, q in QUALITY_WORDS.items() if word in text.lower()), None)
        missing = [k for k in ("source", "stimulus", "environment", "response", "response measure", "importance") if k not in lab]
        if not cite or not quality or missing:
            report.append(f"not migrated: {old_id} (no {', '.join(missing + ([] if cite else ['cites']) + ([] if quality else ['quality']))})")
            continue
        folder = "constraints" if cite.group(1) == "CONSTRAINT" else "metrics"
        artifact = [x for x in (component_of(a) for a in lab.get("artifact", "").split(",")) if x] or ["/system.md"]
        done(old_id, w.put(ids[old_id], "QualityScenario", lead(text)[:60] or old_id, lab["response measure"], {
            "quality": quality, "scenario_kind": "usage", "source": lab["source"], "stimulus": lab["stimulus"],
            "environment": lab["environment"], "artifact": artifact, "response": lab["response"],
            "response_measure": lab["response measure"], "importance": lab["importance"].upper()[:1],
            "risk_rating": lab.get("risk", "").upper()[:1] or None, "cites": f"prd:/{folder}/{cite.group(0)}.md",
            "aliases": [old_id]}, text))
    for match in items["CV"]:
        old_id, text = f"CV-{match.group(2)}", match.group(3).strip()
        done(old_id, w.put(ids[old_id], "Convention", " ".join(text.split()[:8]), text, {"rule": text, "aliases": [old_id]}))
    for match in items["RK"]:
        old_id, text = f"RK-{match.group(2)}", match.group(3)
        lab = labels(text)
        if not (lab.get("mitigation") or lab.get("acceptance")):
            report.append(f"not migrated: {old_id} (no mitigation and no acceptance)")
            continue
        done(old_id, w.put(ids[old_id], "TechnicalRisk", lead(text)[:60], lead(text), {
            "risk_kind": "risk", "failure": lead(text), "mitigation": lab.get("mitigation"),
            "acceptance": None if lab.get("mitigation") else lab.get("acceptance"), "aliases": [old_id]}))
    for match in items["DF"]:
        old_id, text = f"DF-{match.group(2)}", match.group(3)
        lab = labels(text)
        if not (lab.get("reason") and lab.get("trigger") and lab.get("area") in schema.areas()):
            report.append(f"not migrated: {old_id} (no reason, trigger, or area)")
            continue
        done(old_id, w.put(ids[old_id], "Deferred", lead(text)[:60], lead(text), {
            "area": lab["area"], "reason": lab["reason"], "trigger": lab["trigger"], "aliases": [old_id]}))
    for row in table_rows(parts.get("Assumptions", "")):
        if len(row) >= 2 and row[0]:
            done(row[0], w.put(w.allocate("Assumption"), "Assumption", row[0][:60], row[0],
                               {"decision": row[0], "inferred_from": row[1]}))
    # The components come last, so that each link points to a page that was written.
    for item in catalogue:
        uses = [{"to": ids[d["id"]], "style": d.get("style", "sync"),
                 **({"via": ids[d["contract"]]} if ids.get(d.get("contract")) in written else {})}
                for d in item.get("depends_on") or [] if d.get("id") in ids]
        kind = item.get("kind") if item.get("kind") in ("service", "ui", "cli", "library", "job", "data-store", "queue", "external") else "service"
        done(item["id"], w.put(ids[item["id"]], "Component", item.get("name", item["id"]), item.get("summary") or item.get("name", ""), {
            "slug": item["id"][2:], "kind": kind, "areas": item.get("areas") or [], "uses": uses,
            "governed_by": [x for x in (link_of(g) for g in item.get("governed_by") or []) if x and (x.startswith("adr:") or x in written)],
            "realizes": [link_of(r) for r in item.get("realizes") or [] if str(r).startswith("CAPABILITY-")],
            "satisfies": [ids[r] for r in item.get("realizes") or [] if str(r).startswith("QS-") and ids.get(r) in written],
            "aliases": [item["id"]]}))
    rows = {}
    for row in table_rows(parts.get("Decision index", "")):
        if len(row) >= 6:
            rows.setdefault(row[3], []).append({"key": row[0], "binds": row[4], **({"adr": f"adr:/{row[1]}"} if row[1] else {}),
                                                "source": row[5]})
    for slug in schema.areas():
        changes = {"area_state": (fm.get("areas") or {}).get(slug, "open")}
        if rows.get(slug):
            changes["decisions"] = rows[slug]
        w.update(f"/areas/{slug}.md", changes)
    summary = parts.get("Summary", "").strip() or "No summary yet."
    w.update("/system.md", {"design_state": "accepted" if fm.get("status") == "accepted" else "draft",
                            "version": fm.get("version", 1), "prd_tree": fm.get("prd_tree"), "session": fm.get("session"),
                            "title": fm.get("title", "System design")},
             f"\n# {fm.get('title', 'System design')}\n\n## Summary\n\n{summary}\n")
    regen.write(root)
    logbook.append(w.folder / "log.md", "Migrate",
                   f"migrated {old_path} ({len(ids)} items, {len(report)} not migrated); the old file stays", w.actor)
    return report + [f"kept {old_path}: delete it when you no longer need it"]
