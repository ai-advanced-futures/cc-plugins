"""Every case-relative file name, the plugin's own template path, and the path checks that fail closed.

Python 3.9 syntax only: the judge guard imports this module."""
from __future__ import annotations

import os
import re
import stat
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

CASE_META = "case.json"
SCOPE = "scope.json"
RUBRIC_COPY = "rubric.json"
INPUTS_DIR = "inputs"
CHANGELOG = "changelog.jsonl"
CASE_DOC = "business-case.md"
EVIDENCE_DIR = "evidence"
LEDGER = "ledger.json"
DECISIONS = "decisions.jsonl"
JUDGE_DIR = "judge"
HANDOFF = "business-case-handoff.json"
REGISTER = "register.jsonl"
CONDITIONS = "conditions.jsonl"
NOTES = "notes.jsonl"
STRATEGY_VIEW = "strategy-view.md"
FIGURES = "figures.jsonl"
FINANCE = "finance.json"
# The funder's read-only view of the numbers; code writes it, never a judge input.
FINANCE_VIEW = "finance-view.md"
# The latest `bc.py figure` run's refused proposals, or the refusal of the whole run; code writes it,
# replaced each run; never a judge input.
FIGURE_REFUSALS = "figure-refusals.json"
# A funding decision's copy of the finance.json its report read; never rewritten, never a judge input.
FUNDING_DIR = "funding"
# The coach's analyst team works through files here (briefs, replies, cards, answers, runs); never a judge input.
TEAM_DIR = "team"
TEMPLATE = PLUGIN_ROOT / "templates" / "business-case.md"

# The files the judge reads. Nothing the coach keeps for itself is on this list.
JUDGE_INPUT_GLOBS = ("business-case.md", "rubric.json", "scope.json", "evidence/*.json", "decisions.jsonl",
                     "register.jsonl", "conditions.jsonl", "notes.jsonl", "figures.jsonl", "finance.json")

# Files that only grow. A report stays current while its bytes are still the start of the file.
# The strategy files and figures.jsonl also only grow, but a new line in one is a change the judge
# must see (spec §12; plan 3 Task 13): a figure recorded or confirmed after the brief makes the
# report not current.
APPEND_ONLY = frozenset({"decisions.jsonl"})

SESSION_BUDGET_DEFAULT = 5

# A case slug is one lowercase folder name; no dots, slashes or spaces.
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _mode(path):
    """The st_mode of `path`, following symlinks; None when nothing is there. Any other OSError raises,
    a folder that cannot be read among them: from Python 3.14 Path.is_file(), is_dir() and exists()
    read that as absent, so a check that must fail closed cannot use them."""
    try:
        return os.stat(path).st_mode
    except (FileNotFoundError, NotADirectoryError):
        return None


def stat_is_file(path) -> bool:
    mode = _mode(path)
    return mode is not None and stat.S_ISREG(mode)


def stat_is_dir(path) -> bool:
    mode = _mode(path)
    return mode is not None and stat.S_ISDIR(mode)


def stat_exists(path) -> bool:
    return _mode(path) is not None
