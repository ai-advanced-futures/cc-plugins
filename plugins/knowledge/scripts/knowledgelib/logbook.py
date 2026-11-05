"""log.md entries (standard section 2): newest date first, one line for each entry."""
from __future__ import annotations

from pathlib import Path

from knowledgelib import changes

HEADER = "# Log"


def entry(operation, text, actor, when) -> str:
    return f"* **{operation}**: {' '.join(str(text).split())}, by {actor}, at {when}"


def append(path, line, day) -> None:
    path = Path(path)
    lines = path.read_text("utf-8").splitlines() if path.is_file() else []
    if not lines or not lines[0].startswith("# "):
        lines.insert(0, HEADER)
    heading = f"## {day}"
    if heading in lines:
        at = lines.index(heading) + 1
        while at < len(lines) and lines[at].startswith("* "):
            at += 1
        lines.insert(at, line)
    else:
        lines[1:1] = ["", heading, line]
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
    changes.note(path)
