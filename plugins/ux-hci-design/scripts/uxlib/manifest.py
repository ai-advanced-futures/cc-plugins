"""manifest.md of the ux-hci-design graph (standard section 6)."""
from __future__ import annotations

from pathlib import Path

from uxlib import DataError
from uxlib.page import dump, parse, write_text

NAME = "manifest.md"
BODY = ("\n# The ux-hci-design brain\n\nAsk with `/ux-hci-design:ask`. Learn with "
        "`/ux-hci-design:learn`. Forget with `/knowledge:forget`.\n")


def fields() -> dict:
    from uxlib import schema
    from uxlib.logbook import stamp

    types = schema.types()
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The ux-hci-design brain",
            "description": "The research, the personas, the screens, the rules, and the evaluations that the runs of the ux-design skill made.",
            "status": "stable", "brain": "ux-hci-design", "plugin": "ux-hci-design",
            "plugin_version": version,
            "ask_skill": {"plugin": "ux-hci-design:ask", "skills": "ux-hci-design-ask"},
            "install": "claude plugin install ux-hci-design@cc-plugins",
            "save_code": "scripts/ux_graph.py", "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in types.values()],
            "answers": ["which personas does the product have, and on which findings",
                        "which screens, state rules and interaction rules does the design have",
                        "what did the evaluation of screen X find", "which journey does flow X belong to"],
            "required_links": {name: list(links) for name, links in schema.REQUIRED_LINKS.items()},
            "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"ux-hci-design/{version}", "at": stamp()}}


def read(directory) -> dict | None:
    file = Path(directory) / NAME
    if not file.is_file():
        return None
    page = parse(file)
    if page.error:
        raise DataError(f"{file}: {page.error}")
    return page.frontmatter


def write(directory, data, body=BODY) -> None:
    write_text(Path(directory) / NAME, dump(data, body))


def retire(directory, key) -> None:
    page = parse(Path(directory) / NAME)
    retired = list(page.frontmatter.get("retired_ids") or [])
    if key not in retired:
        page.frontmatter["retired_ids"] = retired + [key]
        write_text(page.path, dump(page.frontmatter, page.body))
