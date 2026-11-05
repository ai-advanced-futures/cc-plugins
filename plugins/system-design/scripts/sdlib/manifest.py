"""manifest.md of the system-design graph (standard section 6)."""
from __future__ import annotations

from pathlib import Path

from sdlib import DataError
from sdlib.page import dump, parse, write_text

NAME = "manifest.md"
BODY = ("\n# The system-design brain\n\nAsk with `/system-design:ask`. Learn with "
        "`/system-design:learn`. Forget with `/knowledge:forget`.\n")


def fields() -> dict:
    from sdlib import schema
    from sdlib.logbook import stamp

    types = schema.types()
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The system-design brain",
            "description": "The architecture of the system: components, interfaces, data, quality, and deployment.",
            "status": "stable", "brain": "system-design", "plugin": "system-design", "plugin_version": version,
            "ask_skill": {"plugin": "system-design:ask", "skills": "system-design-ask"},
            "install": "claude plugin install system-design@cc-plugins",
            "save_code": "scripts/system_design.py", "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in types.values() if spec["prefix"]],
            "answers": ["which component realizes capability X", "which interface do A and B use",
                        "which scenarios constrain this component", "why is the design this way"],
            "required_links": {"Interface": ["provided_by"], "DataEntity": ["owned_by"],
                               "QualityScenario": ["cites"]},
            "fixed_pages": ["system.md", "areas/*.md"], "retired_ids": [],
            "generated": {"by": f"system-design/{version}", "at": stamp()}}


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
