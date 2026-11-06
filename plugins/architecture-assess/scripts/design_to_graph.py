#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the design of a run into the system-design graph.

Reads `design-pages.json` (the file that the synthesizer writes in design mode) and runs
`system_design.py` of the system-design plugin, in this order:
  1. `new Component` for each entry of `components`.
  2. `link <from ID> uses /components/<to ID>.md` for each entry of `uses`.

It stops at the first command that fails, prints that command and its error, and exits 1.
With --dry-run it prints the commands and runs none.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

ACTOR = "architecture-assess"
AREA = "building-blocks"
COMPONENT_KINDS = {"service", "ui", "cli", "library", "job", "data-store", "queue", "external"}
EDGE_STYLES = {"sync", "async", "event"}


class DesignError(Exception):
    pass


def load_pages(path: Path) -> tuple[list[dict], list[dict]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DesignError(f"cannot read {path}: {error}") from error
    components = data.get("components") if isinstance(data, dict) else None
    uses = data.get("uses", []) if isinstance(data, dict) else None
    if not isinstance(components, list) or not components or not isinstance(uses, list):
        raise DesignError(f"{path} needs a non-empty list `components` and a list `uses`")
    keys = set()
    for entry in components:
        for field in ("key", "title", "description", "kind"):
            if not isinstance(entry, dict) or not entry.get(field):
                raise DesignError(f"a component has no `{field}`: {entry!r}")
        if entry["kind"] not in COMPONENT_KINDS:
            raise DesignError(f"component {entry['key']}: kind `{entry['kind']}` is not one of {sorted(COMPONENT_KINDS)}")
        if entry["key"] in keys:
            raise DesignError(f"two components have the key {entry['key']}")
        keys.add(entry["key"])
    for entry in uses:
        for field in ("from", "to", "style"):
            if not isinstance(entry, dict) or not entry.get(field):
                raise DesignError(f"a use has no `{field}`: {entry!r}")
        if entry["style"] not in EDGE_STYLES:
            raise DesignError(f"use {entry['from']} -> {entry['to']}: style `{entry['style']}` is not one of {sorted(EDGE_STYLES)}")
        for end in ("from", "to"):
            if entry[end] not in keys:
                raise DesignError(f"use {entry['from']} -> {entry['to']}: `{entry[end]}` is not a component key")
    return components, uses


def base_command(system_design: Path, root: Path) -> list[str]:
    return ["uv", "run", str(system_design / "scripts" / "system_design.py"), "--root", str(root)]


def new_command(base: list[str], entry: dict) -> list[str]:
    description = entry["description"]
    if entry.get("technology"):
        description = f"{description} Technology: {entry['technology']}."
    return base + ["new", "Component", "--title", entry["title"], "--description", description,
                   "--set", f"kind={entry['kind']}", "--set", f"areas=[{AREA}]", "--by", ACTOR]


def link_command(base: list[str], from_id: str, to_id: str, entry: dict) -> list[str]:
    command = base + ["link", from_id, "uses", f"/components/{to_id}.md", "--with", f"style={entry['style']}"]
    if entry.get("technology"):
        command += ["--with", f"technology={json.dumps(entry['technology'])}"]
    return command + ["--by", ACTOR]


def id_from_output(output: str) -> str:
    """`new` prints the path of the page; the ID is the file stem."""
    lines = output.strip().splitlines()
    if not lines:
        raise DesignError("`new` printed no path")
    return Path(lines[-1].strip()).stem


def run_all(system_design: Path, root: Path, pages: Path, dry_run: bool) -> int:
    components, uses = load_pages(pages)
    base = base_command(system_design, root)
    ids: dict[str, str] = {}

    def execute(command: list[str]) -> str:
        print(shlex.join(command))
        if dry_run:
            return ""
        done = subprocess.run(command, capture_output=True, text=True)
        if done.returncode != 0:
            print(f"ERROR: the command above failed with exit {done.returncode}", file=sys.stderr)
            print(done.stderr.strip() or done.stdout.strip(), file=sys.stderr)
            raise SystemExit(1)
        return done.stdout

    for entry in components:
        output = execute(new_command(base, entry))
        ids[entry["key"]] = id_from_output(output) if not dry_run else f"<ID of {entry['key']}>"
    for entry in uses:
        execute(link_command(base, ids[entry["from"]], ids[entry["to"]], entry))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--system-design", type=Path, required=True, help="the root of the system-design plugin")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="the project root")
    parser.add_argument("--dry-run", action="store_true", help="print the commands, run none")
    parser.add_argument("pages", type=Path, help="design-pages.json")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_all(args.system_design, args.root.resolve(), args.pages, args.dry_run)
    except DesignError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
