#!/usr/bin/env python3
"""Deterministic scaffolder for the knowledge plugin.

Writes the container files (AGENTS.md and raw/.gitkeep), makes the bundle
through the save code (graph_ops.init: the indexes, log.md, manifest.md,
links.tsv, and the registry entry), and writes the knowledge router block in
CLAUDE.md. It never overwrites a file: when any target exists, it refuses and
writes nothing.
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import claude_md_router  # noqa: E402
from knowledgelib import UsageError, graph_ops, registry  # noqa: E402
from knowledgelib.graph import TYPES  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"
RENDERED = TEMPLATES / "rendered"
CLAUDE_MD_BLOCK = TEMPLATES / "claude-md-block.md"
TOKEN_NAMES = ("CONTAINER", "SUBJECT", "REPO", "HUMAN_ACTOR", "AGENT_ACTOR", "TODAY")
TYPE_DIRS = tuple(TYPES.values())
RENDERED_FILES = ["AGENTS.md"]
BUNDLE_FILES = ["bundle/index.md", "bundle/log.md", "bundle/manifest.md", "bundle/links.tsv"] + \
    [f"bundle/{name}/index.md" for name in TYPE_DIRS]


class ScaffoldError(Exception):
    pass


def normalize_container(raw: str) -> str:
    c = raw.strip()
    if not c:
        raise ScaffoldError("--container must not be empty")
    if c.startswith("/"):
        raise ScaffoldError(f"--container must be repo-root-relative, not absolute: {raw!r}")
    while c.startswith("./"):
        c = c[2:]
    if not c.endswith("/"):
        c += "/"
    parts = [p for p in c.split("/") if p]
    if not parts or any(p in ("..", ".") for p in parts):
        raise ScaffoldError(f"--container must not escape the target repo: {raw!r}")
    if c == "bundle/":
        raise ScaffoldError("--container must not be 'bundle/': the bundle sits inside the container")
    return c


def render(text: str, tokens: dict) -> str:
    for name, value in tokens.items():
        text = text.replace("{{" + name + "}}", value)
    return text


def container_manifest() -> list:
    return list(RENDERED_FILES) + ["raw/.gitkeep"] + BUNDLE_FILES


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold the knowledge graph into a target repo")
    for flag in ("--target", "--container", "--subject", "--repo", "--human-actor", "--agent-actor", "--today"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the manifest, write nothing")
    args = ap.parse_args()
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: --target '{target}' is not a directory", file=sys.stderr)
        return 1
    try:
        container = normalize_container(args.container)
    except ScaffoldError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    tokens = {"CONTAINER": container, "SUBJECT": args.subject, "REPO": args.repo,
              "HUMAN_ACTOR": args.human_actor, "AGENT_ACTOR": args.agent_actor, "TODAY": args.today}
    full = [container + rel for rel in container_manifest()] + [".claude/knowledge.json"]
    if args.dry_run:
        for rel in full:
            print(f"  {rel}")
        print("  CLAUDE.md  (the knowledge router block)")
        return 0
    # .claude/knowledge.json is shared with every other brain, so only the
    # bundle files and the registry's own "knowledge" entry refuse a rerun. [inferred]
    existing = [rel for rel in full if rel != ".claude/knowledge.json" and (target / rel).exists()]
    if existing or "knowledge" in registry.read(target):
        print("ERROR: refusing to overwrite existing files:", file=sys.stderr)
        for rel in existing or [".claude/knowledge.json (entry knowledge)"]:
            print(f"  {rel}", file=sys.stderr)
        return 1
    for rel in RENDERED_FILES:
        dst = target / container / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(render((RENDERED / rel).read_text("utf-8"), tokens), encoding="utf-8")
    (target / container / "raw").mkdir(parents=True, exist_ok=True)
    (target / container / "raw" / ".gitkeep").write_text("", encoding="utf-8")
    try:
        graph_ops.init(target, container + "bundle", actor=args.agent_actor)
    except UsageError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    claude_md = target / "CLAUDE.md"
    before = claude_md.read_text("utf-8") if claude_md.exists() else ""
    block = claude_md_router.render("knowledge", render(CLAUDE_MD_BLOCK.read_text("utf-8"), tokens))
    try:
        after = claude_md_router.merge(before, "knowledge", block)
    except ValueError as error:
        print(f"ERROR: CLAUDE.md: {error}", file=sys.stderr)
        return 1
    if after != before:
        claude_md.write_text(after, encoding="utf-8")
    missing = [rel for rel in full if not (target / rel).exists()]
    leftover = [rel for rel in full + ["CLAUDE.md"] if (target / rel).is_file() and "{{" in (target / rel).read_text("utf-8")]
    if missing or leftover:
        print(f"ERROR: missing {missing}, unrendered tokens in {leftover}", file=sys.stderr)
        return 1
    for rel in full:
        print(f"wrote {rel}")
    print(f"{len(full)} files written, CLAUDE.md router block written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
