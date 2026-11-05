"""log.md: the log of the bundle.

No frontmatter. The file starts with `# Log`. Entries sit under a
`## YYYY-MM-DD` heading in UTC, the newest heading first, and a new entry
goes at the top of the heading of its date.
"""
from datetime import datetime, timezone
from pathlib import Path

HEADER = "# Log"
OPERATIONS = ("Setup", "Apply", "Merge", "Learn", "Forget", "Upgrade", "Report")


def now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(when: datetime) -> str:
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def entry(operation: str, text: str, actor: str, when: datetime) -> str:
    return f"* **{operation}**: {' '.join(text.split())}, by {actor}, at {timestamp(when)}"


def append(path: Path, line: str, when: datetime) -> None:
    heading = f"## {when.astimezone(timezone.utc).strftime('%Y-%m-%d')}"
    text = path.read_text(encoding="utf-8") if path.exists() else HEADER + "\n"
    lines = text.splitlines()
    if not lines or lines[0].strip() != HEADER:
        lines.insert(0, HEADER)
    if heading in lines:
        at = lines.index(heading) + 1
        lines[at:at] = [line]
    else:
        lines[1:1] = ["", heading, line]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
