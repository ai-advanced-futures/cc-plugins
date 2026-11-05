"""The brain standard for ddd: the manifest, the registry entry, and upgrade (A14)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from dddlib import logbook, regen, schema
from dddlib.bundle import page_files
from dddlib.config import bundle_dir, read_config
from dddlib.page import dump, parse, write_text

ACTOR = "process:ddd-upgrade"
BODY = "\n# The ddd brain\n\nAsk with `/business-domain:ask`. Learn with `/business-domain:learn`.\n"


def manifest_fields() -> dict:
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The ddd brain",
            "description": "The domain model: bounded contexts, terms, aggregates, events, and relationships.",
            "status": "stable", "brain": "ddd", "plugin": "business-domain", "plugin_version": version,
            "ask_skill": {"plugin": "business-domain:ask", "skills": "business-domain-ask"},
            "install": "claude plugin install business-domain@cc-plugins", "save_code": "scripts/ddd.py",
            "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in schema.types().values()],
            "answers": ["what does X mean in context Y", "which contexts use X", "what emits event X"],
            "required_links": {"Relationship": ["between"]},
            "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"ddd/{version}", "at": logbook.timestamp(logbook.now())}}


def write_manifest(directory: Path) -> bool:
    path = directory / "manifest.md"
    fields = manifest_fields()
    if path.is_file():
        old = yaml.safe_load(path.read_text("utf-8").split("---\n")[1]) or {}
        fields["retired_ids"] = old.get("retired_ids") or []
        if {k: v for k, v in old.items() if k != "generated"} == {k: v for k, v in fields.items() if k != "generated"}:
            return False
    path.write_text("---\n" + yaml.safe_dump(fields, sort_keys=False, width=1000) + "---\n" + BODY, encoding="utf-8")
    return True


def registry_add(root: Path, path: str) -> bool:
    file = Path(root) / ".claude" / "knowledge.json"
    data = json.loads(file.read_text("utf-8")) if file.is_file() else {"graphs": {}}
    if data.setdefault("graphs", {}).get("ddd") == {"path": path}:
        return False
    data["graphs"]["ddd"] = {"path": path}
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def finish(root: Path) -> list[str]:
    """Write the manifest and the registry entry, after regen (A14)."""
    changes = []
    if write_manifest(bundle_dir(root)):
        changes.append("wrote manifest.md")
    if registry_add(root, read_config(root)["dir"]):
        changes.append("wrote the registry entry ddd")
    return changes


def upgrade(root: Path) -> list[str]:
    directory = bundle_dir(root)
    changes = []
    for path in page_files(directory):
        page = parse(path)
        if page.frontmatter is not None and not isinstance(page.frontmatter.get("generated"), dict):
            when = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0)
            write_text(path, dump({**page.frontmatter, "generated": {"by": ACTOR, "at": logbook.timestamp(when)}}, page.body))
            changes.append(f"updated {path.relative_to(root).as_posix()}")
    if not (directory / "log.md").exists():
        (directory / "log.md").write_text(logbook.HEADER + "\n", encoding="utf-8")
        changes.append("added log.md")
    changes += [f"regenerated {p.relative_to(root).as_posix()}" for p in regen.write(root)]
    changes += finish(root)
    if changes:
        when = logbook.now()
        logbook.append(directory / "log.md", logbook.entry("Upgrade", f"brought the bundle to the brain standard "
                                                           f"({len(changes)} changes)", ACTOR, when), when)
    return changes
