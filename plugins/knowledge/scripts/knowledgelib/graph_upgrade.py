"""upgrade: bring an existing generic graph to the standard (A14), also an old wiki."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from knowledgelib import DataError, UsageError, graph_regen, logbook, manifest, okf, registry
from knowledgelib import changes as change_list
from knowledgelib.graph import GRAPH, MANIFEST_BODY, TYPES, manifest_fields, stamp

ACTOR = "process:knowledge-upgrade"
FED_HEADING = "## Pages this source fed"
DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def find_directory(root) -> str:
    graphs = registry.read(root)
    if GRAPH in graphs:
        return graphs[GRAPH].path
    legacy = Path(root) / ".claude" / "wiki.json"
    if legacy.is_file():
        container = json.loads(legacy.read_text("utf-8")).get("container")
        if isinstance(container, str) and container.strip():
            return registry.check_path(container.rstrip("/") + "/bundle", GRAPH)
    raise UsageError("no knowledge graph to upgrade: the registry has no knowledge entry and "
                     ".claude/wiki.json is absent. Run init.")


def _fix_stamp(value):
    if isinstance(value, dict) and DATE_ONLY.match(str(value.get("at", ""))):
        return {**value, "at": f"{value['at']}T00:00:00Z"}
    return value


def _upgrade_page(root, file) -> bool:
    text = okf.read_text(file)
    page = okf.parse_text(file, text)
    if page.error:
        raise DataError(f"{file.relative_to(root)}: {page.error}. Correct the page, then run upgrade again.")
    body = page.body
    if page.frontmatter.get("type") == "Source" and FED_HEADING in body:
        body = body.split(FED_HEADING, 1)[0].rstrip("\n") + "\n"
    data = dict(page.frontmatter)
    if not isinstance(data.get("generated"), dict):
        when = datetime.fromtimestamp(file.stat().st_mtime, timezone.utc).replace(microsecond=0)
        data["generated"] = {"by": ACTOR, "at": stamp(when)}
    data["generated"] = _fix_stamp(data["generated"])
    if isinstance(data.get("verified"), list):
        data["verified"] = [_fix_stamp(item) for item in data["verified"]]
    head = text[: len(text) - len(page.body)]
    new = head + body if data == page.frontmatter else okf.dump(data, body)
    if new == text:
        return False
    okf.write_text(file, new)
    return True


def upgrade(root, directory=None) -> list[str]:
    directory = registry.check_path(directory, GRAPH) if directory else find_directory(root)
    bundle = Path(root) / directory
    if not bundle.is_dir():
        raise UsageError(f"{directory} does not exist")
    changes = []
    for folder in TYPES.values():
        (bundle / folder).mkdir(exist_ok=True)
    for file in okf.bundle_pages(bundle):
        if _upgrade_page(root, file):
            changes.append(f"updated {file.relative_to(root).as_posix()}")
    log = bundle / "log.md"
    if not log.is_file():
        log.write_text(logbook.HEADER + "\n", encoding="utf-8")
        change_list.note(log)
        changes.append("added log.md")
    changes += [f"regenerated {p.relative_to(root).as_posix()}" for p in graph_regen.write(root, bundle)]
    data = manifest.read(bundle)
    fields = manifest_fields()
    if data is None:
        manifest.write(bundle, fields, MANIFEST_BODY)
        changes.append("wrote manifest.md")
    elif data.get("plugin_version") != fields["plugin_version"]:
        data.update(plugin=fields["plugin"], plugin_version=fields["plugin_version"])
        manifest.write(bundle, data, okf.read_page(bundle / manifest.NAME).body)
        changes.append("updated manifest.md")
    if registry.add(root, GRAPH, directory):
        changes.append("wrote the registry entry knowledge")
    if changes:
        when = stamp()
        logbook.append(log, logbook.entry("Upgrade", f"brought {directory} to the brain standard "
                                          f"({len(changes)} changes)", ACTOR, when), when[:10])
    return changes
