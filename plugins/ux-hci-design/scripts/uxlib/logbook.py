"""log.md entries: newest date first, one line for each entry."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

HEADER = "# Log"
OPERATIONS = ("Setup", "Learn", "Ingest", "Forget", "Upgrade", "Report")


def stamp(when=None) -> str:
    when = when or datetime.now(timezone.utc).replace(microsecond=0)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def append(path, operation, text, actor) -> None:
    when = stamp()
    line = f"* **{operation}**: {' '.join(str(text).split())}, by {actor}, at {when}"
    path = Path(path)
    lines = path.read_text("utf-8").splitlines() if path.is_file() else []
    if not lines or not lines[0].startswith("# "):
        lines.insert(0, HEADER)
    heading = f"## {when[:10]}"
    if heading in lines:
        at = lines.index(heading) + 1
        while at < len(lines) and lines[at].startswith("* "):
            at += 1
        lines.insert(at, line)
    else:
        lines[1:1] = ["", heading, line]
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
