"""manifest.md of the jtbd graph (standard section 6)."""
from __future__ import annotations

from pathlib import Path

from jtbdlib import DataError
from jtbdlib.page import dump, parse, write_text

NAME = "manifest.md"
BODY = ("\n# The jtbd brain\n\nAsk with `/jtbd-market-discovery:ask`. Learn with "
        "`/jtbd-market-discovery:learn`. Forget with `/knowledge:forget`.\n")


def fields() -> dict:
    from jtbdlib import schema
    from jtbdlib.logbook import stamp

    types = schema.types()
    version = schema.plugin_version()
    return {"type": "Manifest", "title": "The jtbd brain",
            "description": "The jobs, outcomes, segments and willingness to pay that the runs of jtbd-market-discovery found.",
            "status": "stable", "brain": "jtbd", "plugin": "jtbd-market-discovery",
            "plugin_version": version,
            "ask_skill": {"plugin": "jtbd-market-discovery:ask", "skills": "jtbd-market-discovery-ask"},
            "install": "claude plugin install jtbd-market-discovery@cc-plugins",
            "save_code": "scripts/jtbd_graph.py", "id_pattern": r"^[A-Z]+-\d{2,}\.md$",
            "id_folders": [spec["directory"] for spec in types.values()],
            "answers": ["which outcomes are most underserved", "which segment values outcome X most",
                        "what will segment S pay", "how did the scores of job J change between runs",
                        "which result rests on a default"],
            "required_links": {name: list(links) for name, links in schema.REQUIRED_LINKS.items()},
            "fixed_pages": [], "retired_ids": [],
            "generated": {"by": f"jtbd-market-discovery/{version}", "at": stamp()}}


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
