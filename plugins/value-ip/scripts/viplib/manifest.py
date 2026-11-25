"""manifest.md of the value-ip graph (standard section 6)."""
from __future__ import annotations

from pathlib import Path

from viplib import DataError
from viplib.page import dump, parse, write_text

NAME = "manifest.md"
BODY = ("\n# The value-ip brain\n\nAsk with `/value-ip:ask`. Learn with "
        "`/value-ip:learn`. Forget with `/knowledge:forget`.\n")


def fields() -> dict:
    from viplib import schema
    from viplib.logbook import stamp

    types = schema.types()
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The value-ip brain",
            "description": "The differentiators, the verdicts and the gaps that the runs of value-ip:analyze found, with the run that found each.",
            "status": "stable", "brain": "value-ip", "plugin": "value-ip",
            "plugin_version": version,
            "ask_skill": {"plugin": "value-ip:ask", "skills": "value-ip-ask"},
            "install": "claude plugin install value-ip@cc-plugins",
            "save_code": "scripts/vip_graph.py", "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in types.values()],
            "answers": ["which differentiators survived the debate on artifact X, and which frameworks support each",
                        "what is the overall verdict and the mean score of the latest run",
                        "which results did a run not produce, and why",
                        "which pages did a person confirm"],
            "required_links": {name: list(links) for name, links in schema.REQUIRED_LINKS.items()},
            "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"value-ip/{version}", "at": stamp()}}


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
