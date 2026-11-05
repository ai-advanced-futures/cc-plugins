"""log.md: the Event log of a bundle.

No frontmatter. The file starts with `# Log`. Entries sit under a
`## YYYY-MM-DD` heading in UTC, newest heading first, and a new entry goes at
the top of the heading for its date.
"""
from datetime import datetime
from pathlib import Path

HEADER = "# Log"


def timestamp(when: datetime) -> str:
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def init_log(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER + "\n", encoding="utf-8")


def state_line(page_id: str, link: str, old: str, new: str,
               actor: str, when: datetime,
               approved_by: str | None = None) -> str:
    """The Event line of the spec. The link text is the ID only.

    An approval goes before `, at`, because ghpull adds its note after the
    timestamp."""
    approval = f", approved by {approved_by}" if approved_by else ""
    return (f"* **State**: [{page_id}]({link}) "
            f"{old} -> {new}, by {actor}{approval}, at {timestamp(when)}")


def entry_line(kind: str, page_id: str, link: str, text: str,
               actor: str, when: datetime) -> str:
    """A Save, Migrate, Plan, Sync, Claim, or Run entry, with the same
    shape as the State line."""
    return (f"* **{kind}**: [{page_id}]({link}) "
            f"{text}, by {actor}, at {timestamp(when)}")


def append_entry(path: Path, line: str, when: datetime) -> None:
    append_entries(path, [line], when)


def append_entries(path: Path, new_lines: list, when: datetime) -> None:
    """Add every line under the heading of the day, in one read and one
    write. A caller that holds many lines would otherwise rewrite the whole
    file once for each of them."""
    if not new_lines:
        return
    heading = f"## {when.strftime('%Y-%m-%d')}"
    text = path.read_text(encoding="utf-8") if path.exists() else HEADER + "\n"
    lines = text.splitlines()
    if not lines or lines[0].strip() != HEADER:
        lines.insert(0, HEADER)
    # The newest entry goes first, as one call for each line would leave it.
    block = list(reversed(new_lines))
    if heading in lines:
        at = lines.index(heading) + 1
        lines[at:at] = block
    else:
        lines[1:1] = ["", heading, *block]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")
