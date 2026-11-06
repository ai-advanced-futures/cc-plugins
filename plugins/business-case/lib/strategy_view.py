"""The strategy view (strategy-view.md): a read-only projection of the register for people (spec §5a).

Code writes this file and nobody edits it. It is not a judge input: the register is.
"""
from __future__ import annotations

from pathlib import Path

from lib import case_files, paths, register

ABSENT_LINE = "absent: no stated or confirmed entry"
_HEADER = "Code projects this file from register.jsonl. Do not edit it. Run bc.py view to rebuild it."


def _one_line(text: str) -> str:
    """The text on one line, so a line break in it cannot add a heading or an entry to the view."""
    return " ".join(text.split())


def render(case_dir) -> str:
    case_dir = Path(case_dir)
    offering = case_files.offering(case_dir)
    live = register.live_entries(case_dir)
    absent = register.absent_categories(case_dir)
    blocks = [f"# Strategy view: {offering}", _HEADER]
    for key, title in register.CATEGORIES:
        lines = [f"## {title}", ""]
        for entry in (e for e in live if e["category"] == key):
            label = "confirmed" if entry["status"] == "confirmed" else "unconfirmed"
            lines.append(f"- {entry['id']} ({label}): {_one_line(entry['choice'])} "
                         f"Rejected: {_one_line(entry['rejected_alternative'])}")
        if key in absent:
            if len(lines) > 2:
                lines.append("")
            lines.append(ABSENT_LINE)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def write_view(case_dir) -> Path:
    path = Path(case_dir) / paths.STRATEGY_VIEW
    case_files._atomic_write(path, render(case_dir).encode("utf-8"))
    return path
