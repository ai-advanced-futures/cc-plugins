"""manifest.md of the competitive-intelligence graph (standard section 6)."""
from __future__ import annotations

from pathlib import Path

from cilib import DataError
from cilib.page import dump, parse, write_text

NAME = "manifest.md"
BODY = ("\n# The competitive-intelligence brain\n\nAsk with `/competitive-intelligence:ask`. Learn with "
        "`/competitive-intelligence:learn`. Forget with `/knowledge:forget`.\n")


def fields() -> dict:
    from cilib import schema
    from cilib.logbook import stamp

    types = schema.types()
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The competitive-intelligence brain",
            "description": "The competitors of a market, their offers, and what the runs of the plugin found about them.",
            "status": "stable", "brain": "competitive-intelligence", "plugin": "competitive-intelligence",
            "plugin_version": version,
            "ask_skill": {"plugin": "competitive-intelligence:ask", "skills": "competitive-intelligence-ask"},
            "install": "claude plugin install competitive-intelligence@cc-plugins",
            "save_code": "scripts/ci_graph.py", "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in types.values()],
            "answers": ["which competitors does market X have", "what do we know about competitor X, and from which sources",
                        "which offers and prices does competitor X have",
                        "what are the strengths, weaknesses, opportunities and threats against competitor X",
                        "which recommendations rest on finding X", "which results did run X give, and on which sources",
                        "what changed at competitor X since the last run"],
            "required_links": {name: list(links) for name, links in schema.REQUIRED_LINKS.items()},
            "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"competitive-intelligence/{version}", "at": stamp()}}


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
