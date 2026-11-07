"""The generic graph (spec section 7.2): its types, folders, actor, and schema."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from knowledgelib import UsageError, registry

GRAPH = "knowledge"
DEFAULT_DIR = "docs/knowledge/bundle"
TYPES = {"Source": "sources", "Entity": "entities", "Concept": "concepts",
         "Synthesis": "synthesis", "OpenQuestion": "open-questions"}
HEADINGS = {"sources": "Sources", "entities": "Entities", "concepts": "Concepts",
            "synthesis": "Synthesis", "open-questions": "Open Questions"}
ROOT_LINES = [
    ("Manifest", "manifest.md", "What this bundle is and how to read it."),
    ("Log", "log.md", "The record of each change, newest first."),
    ("Sources", "sources/index.md", "One page for each raw source."),
    ("Entities", "entities/index.md", "Organizations, publications, and people that recur across sources."),
    ("Concepts", "concepts/index.md", "Ideas, metrics, formulas, and frameworks."),
    ("Synthesis", "synthesis/index.md", "Pages that join several pages into one answer."),
    ("Open Questions", "open-questions/index.md", "Questions that the graph cannot answer yet."),
]
LINK_FIELDS = ("sources",)
INVERSE = {"sources": "fed"}
OPERATIONS = ("Setup", "Learn", "Forget", "Upgrade", "Report")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PLUGIN_ROOT / "schema" / "knowledge.schema.json"
MANIFEST_BODY = ("\n# The knowledge brain\n\nAsk with `/knowledge:ask`. Add with `/knowledge:learn`. "
                 "Remove with `/knowledge:forget`.\n")


def plugin_version() -> str:
    return json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text("utf-8"))["version"]


def plugin_actor() -> str:
    return f"knowledge/{plugin_version()}"


def stamp(when=None) -> str:
    when = when or datetime.now(timezone.utc).replace(microsecond=0)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def bundle_dir(root) -> Path:
    graphs = registry.read(root)
    if GRAPH not in graphs:
        registry.check_root(graphs)
        raise UsageError("the knowledge graph is not in .claude/knowledge.json. Run /knowledge:setup first.")
    bundle = Path(root) / graphs[GRAPH].path
    if not bundle.is_dir():
        raise UsageError(f"the knowledge graph folder {graphs[GRAPH].path} does not exist. Run /knowledge:setup first.")
    return bundle


def manifest_fields() -> dict:
    version = plugin_version()
    return {"type": "Manifest", "title": "The knowledge brain",
            "description": "The generic graph: sources, entities, concepts, synthesis, and open questions.",
            "status": "stable", "brain": GRAPH, "plugin": "knowledge", "plugin_version": version,
            "ask_skill": {"plugin": "knowledge:ask", "skills": "knowledge-ask"},
            "install": "claude plugin install knowledge@cc-plugins",
            "save_code": "scripts/knowledge_graph.py", "id_pattern": r"^[a-z0-9]+(-[a-z0-9]+)*\.md$",
            "id_folders": list(TYPES.values()),
            "answers": ["what do the sources say about X", "which sources support a claim",
                        "which questions are still open"],
            "required_links": {}, "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"knowledge/{version}", "at": stamp()}}


@lru_cache(maxsize=1)
def _defs() -> dict:
    return json.loads(SCHEMA_PATH.read_text("utf-8"))["$defs"]


@lru_cache(maxsize=None)
def _validator(type_name):
    from jsonschema import Draft7Validator

    return Draft7Validator({"$defs": _defs(), "$ref": f"#/$defs/{type_name}"})


def validate(type_name, frontmatter) -> list[str]:
    if type_name not in TYPES:
        return [f"{type_name!r} is not a type of the generic graph: use {', '.join(TYPES)}"]
    return sorted(f"{'.'.join(map(str, e.absolute_path)) or '(page)'}: {e.message}"
                  for e in _validator(type_name).iter_errors(frontmatter))
