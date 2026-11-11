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


def _manifest_folders(path) -> list | None:
    """The `id_folders` of a manifest, or None when the manifest has no
    mapping frontmatter or no list there. A hand edit or a merge conflict can
    break a manifest, and `check` must still run on that bundle: the general
    check (K-manifest) owns the finding."""
    head = split_frontmatter(path.read_text("utf-8"))[0]
    if head is None:
        return None
    try:
        old = yaml.safe_load(head)
    except yaml.YAMLError:
        return None
    folders = old.get("id_folders") if isinstance(old, dict) else None
    return folders if isinstance(folders, list) else None


def stale_manifests(root) -> list[Path]:
    """The manifest of each bundle that has a page in a folder that its
    `id_folders` does not name (rule K-id of the general check says that page
    is not in a folder of `id_folders`). A bundle with no `manifest.md`, or
    with a manifest that holds no `id_folders` list, has no entry: the
    K-manifest WARN of today stays. It reads file names and the manifests,
    and parses no page."""
    out = []
    for bundle in BUNDLES:
        base = bundle_dir(root, bundle)
        manifest = base / "manifest.md"
        if not manifest.is_file():
            continue
        named = _manifest_folders(manifest)
        if named is None:
            continue
        for path in iter_pages(base):
            parts = path.relative_to(base).parts
            if (len(parts) >= 2 and parts[0] in DIRECTORY_ORDER[bundle]
                    and parts[-1] != "closed.md" and parts[0] not in named):
                out.append(manifest)
                break
    return out


def refresh_id_folders(root, bundle) -> bool:
    """Write the manifest again when a folder that holds an ID page is not in
    its `id_folders` (the first Experience page of a bundle that an older
    release made). `write_manifest` keeps `retired_ids`. With no manifest it
    writes nothing. Returns True when it wrote."""
    manifest = bundle_dir(root, bundle) / "manifest.md"
    if manifest not in stale_manifests(root):
        return False
    return write_manifest(root, bundle)


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
