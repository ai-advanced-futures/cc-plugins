"""The brain standard for prd: manifests, registry entries, and upgrade (A14)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import logbook, regen
from .page import load_page, split_frontmatter, write_page
from .registry import DIRECTORY_ORDER
from .schema import plugin_actor
from .tree import BUNDLES, bundle_dir, iter_pages

ACTOR = "process:prd-upgrade"
PATTERNS = {"prd": r"^[A-Z]+-\d{2,}\.md$", "roadmap": r"^[A-Z]+-[0-9A-Za-z-]+\.md$"}
FIXED = {"prd": ["product.md"], "roadmap": ["*/closed.md"]}
ANSWERS = {"prd": ["what problem does the product solve", "which capability serves need X", "what is in scope"],
           "roadmap": ["what is the next work", "which items trace capability X", "what is blocked"]}
REQUIRED = {"prd": {}, "roadmap": {"Story": ["parent"], "Task": ["parent"], "AcceptanceCriterion": ["item"]}}


def fields(bundle) -> dict:
    version = plugin_actor().split("/", 1)[1]
    return {"type": "Manifest", "title": f"The {bundle} brain",
            "description": f"The {'requirements' if bundle == 'prd' else 'work plan'} of the product.",
            "status": "stable", "brain": bundle, "plugin": "product", "plugin_version": version,
            "ask_skill": {"plugin": "product:ask", "skills": "product-ask"},
            "install": "claude plugin install product@cc-plugins", "save_code": "scripts/prd.py",
            "id_pattern": PATTERNS[bundle], "id_folders": list(DIRECTORY_ORDER[bundle]),
            "answers": ANSWERS[bundle], "required_links": REQUIRED[bundle], "fixed_pages": FIXED[bundle],
            "retired_ids": [], "generated": {"by": plugin_actor(), "at": logbook.timestamp(datetime.now(timezone.utc))}}


def write_manifest(root, bundle) -> bool:
    path = bundle_dir(root, bundle) / "manifest.md"
    data = fields(bundle)
    retired_file = bundle_dir(root, bundle) / ".retired-ids.json"
    if path.is_file():
        old = yaml.safe_load(split_frontmatter(path.read_text("utf-8"))[0]) or {}
        data["retired_ids"] = old.get("retired_ids") or []
        if {k: v for k, v in old.items() if k != "generated"} == {k: v for k, v in data.items() if k != "generated"}:
            return False
    elif retired_file.is_file():
        # `edit.remove` (Task 61) recorded retired IDs here before a manifest existed; this is
        # the first manifest write for the bundle, so fold the record in and drop the file. [inferred]
        data["retired_ids"] = json.loads(retired_file.read_text("utf-8"))
        retired_file.unlink()
    path.write_text("---\n" + yaml.safe_dump(data, sort_keys=False, width=1000) + "---\n\n"
                    f"# The {bundle} brain\n\nAsk with `/product:ask`. Learn with `/product:learn`.\n", encoding="utf-8")
    return True


def registry_add(root) -> bool:
    file = Path(root) / ".claude" / "knowledge.json"
    data = json.loads(file.read_text("utf-8")) if file.is_file() else {"graphs": {}}
    graphs = data.setdefault("graphs", {})
    wanted = {b: {"path": bundle_dir(root, b).relative_to(root).as_posix()} for b in BUNDLES}
    if all(graphs.get(b) == entry for b, entry in wanted.items()):
        return False
    graphs.update(wanted)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def finish(root) -> list[str]:
    changes = [f"wrote {b}/manifest.md" for b in BUNDLES if write_manifest(root, b)]
    if registry_add(root):
        changes.append("wrote the registry entries prd and roadmap")
    return changes


def backfill(root, actor) -> list[str]:
    """Write `generated` on each page that has none (init and upgrade use it)."""
    changes = []
    for bundle in BUNDLES:
        for path in iter_pages(bundle_dir(root, bundle)):
            page = load_page(path)
            if not isinstance(page.frontmatter.get("generated"), dict):
                when = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0)
                page.frontmatter["generated"] = {"by": actor, "at": logbook.timestamp(when)}
                write_page(page)
                changes.append(f"updated {path.relative_to(root).as_posix()}")
    return changes


def upgrade(root) -> list[str]:
    changes = backfill(root, ACTOR)
    for bundle in BUNDLES:
        log = bundle_dir(root, bundle) / "log.md"
        if not log.exists():
            log.write_text(logbook.HEADER + "\n", encoding="utf-8")
            changes.append(f"added {bundle}/log.md")
    changes += [f"regenerated {p.relative_to(root).as_posix()}" for p in regen.write(root)]
    changes += finish(root)
    if changes:
        when = datetime.now(timezone.utc)
        for bundle in BUNDLES:
            logbook.append_entries(bundle_dir(root, bundle) / "log.md", [
                f"* **Upgrade**: brought the bundle to the brain standard ({len(changes)} changes), by {ACTOR}, "
                f"at {logbook.timestamp(when)}"], when)
    return changes
