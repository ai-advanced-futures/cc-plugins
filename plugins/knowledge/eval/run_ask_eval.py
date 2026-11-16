#!/usr/bin/env python3
"""Historical page-by-page evaluation scoring; live execution is retired.

The local ask and ponder readers produce no page-by-page walk state. Use the
native runner in plugins/knowledge/evals/benchmark.py for reader measurements.
The score and verdict helpers remain for the historical fixture tests.
"""
from __future__ import annotations

import argparse
import sys


def score(answer: str, state: dict | None, expect: list, total: int) -> bool:
    # A missing walk state is unmeasured, not efficient. Citations alone cannot
    # establish how many pages the historical page-by-page reader visited.
    if state is None:
        return False
    cited = all(link in answer for link in expect)
    return cited and len(state.get("done", [])) < total / 2


def verdict(runs: list) -> bool:
    return sum(1 for ok in runs if ok) >= 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--runs", type=int, default=3, help="retired option")
    parser.parse_args()
    parser.error("The page-by-page evaluator is retired: ask and ponder do not write walk state. "
                 "Use plugins/knowledge/evals/benchmark.py; this command starts no model sessions.")


if __name__ == "__main__":
    sys.exit(main())
