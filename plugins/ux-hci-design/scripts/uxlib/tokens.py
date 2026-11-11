"""tokens: the design tokens and the components of a run, and their save into the system design (STORY-244 row 19).

The tokens are in the `record` of the pattern pages and of the screen pages: the record holds the full output file of the
run. `--save` writes one `Convention` page of the system-design graph, and writes it only through `system_design.py`
(ADR-0006). That script writes frontmatter fields and no body, so the tokens are in the field `rule`.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from uxlib import DataError, UsageError, schema
from uxlib.bundle import read
from uxlib.page import parse
from uxlib.read import find_run, graph_folder, of_run

TAG = "design-tokens"
TITLE = "Design tokens of the user interface"
DESCRIPTION = ("The design tokens and the components that the screens of the product use: "
               "colors, type, spacing, motion and components.")
# The key of the object, and the word of the sentence of `rule`.
GROUPS = (("colors", "Colors"), ("typography", "Typography"), ("spacing", "Spacing"), ("animation", "Motion"),
          ("components", "Components"))
TOKEN_LISTS = ("colors", "typography", "spacing", "animation")
PROBE = Path(__file__).resolve().parents[1] / "probe-plugin.sh"
NO_TOKENS = "The run has no design tokens."


def record_of(page, run_id, name):
    """The document of one output file in the record of a page, for the run, or an empty mapping."""
    record = (page.frontmatter or {}).get("record") or {}
    document = record.get(f"{run_id}/{name}")
    return document if isinstance(document, dict) else {}


def collect(root, run) -> tuple[str, dict]:
    """The run ID and the object of the tokens. Each list is sorted, with no duplicates."""
    bundle = read(root)
    wanted = find_run(bundle, run or "latest")
    found: dict[str, set[str]] = {key: set() for key, _ in GROUPS}
    for path, page in sorted(bundle.pages.items()):
        if not page.live or not of_run(bundle, wanted, path, page):
            continue
        if page.type == "InteractionRule" and (page.frontmatter or {}).get("pattern_kind") == "pattern":
            pattern = record_of(page, wanted.id, "interaction_patterns.json").get("pattern")
            given = pattern.get("design_tokens") if isinstance(pattern, dict) else None
            for key in TOKEN_LISTS:
                values = given.get(key) if isinstance(given, dict) else None
                found[key].update(v for v in values or [] if isinstance(v, str) and v.strip())
        elif page.type == "Screen":
            wireframe = record_of(page, wanted.id, "wireframes.json").get("wireframe")
            components = wireframe.get("components") if isinstance(wireframe, dict) else None
            found["components"].update(c["type"] for c in components or []
                                       if isinstance(c, dict) and isinstance(c.get("type"), str) and c["type"].strip())
    return wanted.id, {key: sorted(values) for key, values in found.items()}


def rule_text(run_id, found) -> str:
    groups = [f"{label}: {', '.join(found[key])}." for key, label in GROUPS if found[key]]
    return f"Each screen uses only these design tokens and components, from the run {run_id} of the UX brain. " + " ".join(groups)


def system_design_script() -> Path:
    """The `system_design.py` of the system-design plugin, found with probe-plugin.sh."""
    done = subprocess.run(["bash", str(PROBE), "system-design", "scripts/system_design.py"], capture_output=True, text=True)
    if done.returncode != 0 or not done.stdout.strip():
        raise UsageError("Install the system-design plugin to add the design tokens to the system design: "
                         "claude plugin install system-design@cc-plugins")
    return Path(done.stdout.strip()) / "scripts" / "system_design.py"


def tagged_pages(folder) -> list:
    """The live Convention pages of the system design that have the tag `design-tokens`, in the order of their IDs."""
    directory = folder / "conventions"
    pages = [parse(path) for path in sorted(directory.glob("*.md"))] if directory.is_dir() else []
    return [page for page in pages
            if page.type == "Convention" and page.live and TAG in ((page.frontmatter or {}).get("tags") or [])]


def run(root, run_key, save) -> int:
    """Print the tokens as JSON, or save them. Return the exit code."""
    run_id, found = collect(root, run_key)
    if not save:
        print(json.dumps(found, indent=2, ensure_ascii=False))
        return 0
    if not any(found.values()):
        print(NO_TOKENS)
        return 0
    folder = graph_folder(root, "system-design", "system-design")
    script = system_design_script()
    pages = tagged_pages(folder)
    if len(pages) > 1:
        raise DataError(f"{len(pages)} Convention pages have the tag {TAG}: {', '.join(p.id for p in pages)}. Keep 1.")
    # system_design.py reads each KEY=VALUE as YAML, and the sentence holds ": " and a color can hold "#".
    # A JSON string is a YAML string, so the page holds the same text.
    rule = "rule=" + json.dumps(rule_text(run_id, found), ensure_ascii=False)
    if pages:
        command = ["set", pages[0].id, rule]
    else:
        command = ["new", "Convention", "--title", TITLE, "--description", DESCRIPTION, "--set", f"tags=[{TAG}]", "--set", rule]
    done = subprocess.run([sys.executable, str(script), "--root", str(root), *command, "--by", schema.plugin_actor()],
                          capture_output=True, text=True)
    print(done.stdout, end="")
    print(done.stderr, end="", file=sys.stderr)
    return 0 if done.returncode == 0 else (done.returncode if done.returncode in (1, 2) else 1)
