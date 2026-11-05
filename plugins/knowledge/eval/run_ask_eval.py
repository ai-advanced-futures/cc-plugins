#!/usr/bin/env python3
"""Run the ask evaluation in headless Claude Code sessions (spec section 11, A19).

    python3 plugins/knowledge/eval/run_ask_eval.py [--runs 3]

It builds the fixture project, asks each question of ask-questions.yaml with
`claude -p`, loads the five plugins with --plugin-dir, reads the walk state that
knowledge:ask writes to KNOWLEDGE_WALK_STATE, and prints one line for each
question. Exit 1 when a question fails. pytest covers score() and verdict()
only, because a run needs live Haiku judgments.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PLUGINS = HERE.parents[1]
BRAINS = ("knowledge", "product", "business-domain", "architecture", "system-design")


def score(answer: str, state: dict | None, expect: list, total: int) -> bool:
    # A missing walk state is unmeasured, not efficient: the builder decides this does not count
    # as a PASS, because citations alone are not evidence of the efficiency claim (a shortcut
    # answer, or a run that never loaded knowledge:ask, could otherwise pass for free). [inferred]
    if state is None:
        return False
    cited = all(link in answer for link in expect)
    return cited and len(state.get("done", [])) < total / 2


def verdict(runs: list) -> bool:
    return sum(1 for ok in runs if ok) >= 2


def total_pages(root: Path) -> int:
    graphs = json.loads((root / ".claude" / "knowledge.json").read_text())["graphs"]
    return sum(1 for g in graphs.values() for p in (root / g["path"]).rglob("*.md") if p.name != "index.md")


def ask(root: Path, skill: str, question: str) -> tuple[str, dict]:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "walk.json"
        command = ["claude", "-p", f"/{skill} {question}", "--output-format", "json",
                   "--dangerously-skip-permissions"]
        for brain in BRAINS:
            command += ["--plugin-dir", str(PLUGINS / brain)]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                env={**os.environ, "KNOWLEDGE_WALK_STATE": str(state)}, timeout=900)
        answer = json.loads(result.stdout).get("result", "") if result.stdout.strip() else ""
        walk = json.loads(state.read_text()) if state.is_file() else None
        return answer, walk


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(HERE))
    import fixture_project

    questions = yaml.safe_load((HERE / "ask-questions.yaml").read_text())["questions"]
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = fixture_project.build(Path(tmp) / "shop")
        total = total_pages(root)
        for q in questions:
            runs = [score(*ask(root, q["skill"], q["question"]), q["expect"], total) for _ in range(args.runs)]
            ok = verdict(runs)
            failed += 0 if ok else 1
            print(f"{'PASS' if ok else 'FAIL'} {q['skill']}: {q['question']} ({sum(runs)}/{len(runs)} runs)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
