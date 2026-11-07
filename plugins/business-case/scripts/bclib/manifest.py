"""manifest.md of the business-case graph (standard section 6)."""
from __future__ import annotations

from pathlib import Path

from bclib import DataError
from bclib.page import dump, parse, write_text

NAME = "manifest.md"
BODY = ("\n# The business-case brain\n\nAsk with `/business-case:ask`. Learn with "
        "`/business-case:learn`. Forget with `/knowledge:forget`.\n")


def fields() -> dict:
    from bclib import schema
    from bclib.logbook import stamp

    types = schema.types()
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The business-case brain",
            "description": "The business cases of the plugin: the text of each section, the evidence, the decisions, the money figures and the reports of the judge.",
            "status": "stable", "brain": "business-case", "plugin": "business-case",
            "plugin_version": version,
            "ask_skill": {"plugin": "business-case:ask", "skills": "business-case-ask"},
            "install": "claude plugin install business-case@cc-plugins",
            "save_code": "scripts/bc_graph.py", "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in types.values()],
            "answers": ["what does business case X say about its customers, price or market",
                        "which evidence supports claim X, and how good is that evidence",
                        "which decisions did the person take on case X, and why",
                        "what strategy and conditions does case X have, and which are confirmed",
                        "which money figures does case X use, and what do the NPV, payback and ROI say",
                        "what did the independent judge find in case X"],
            "required_links": {name: list(links) for name, links in schema.REQUIRED_LINKS.items()},
            "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"business-case/{version}", "at": stamp()}}


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
