"""`prd.py ready`: the work an agent may take.

An item is ready when its state is `ready` and no claim holds it. A Story
also needs a `spec` field whose value is not `none`: `product:work` refuses a
Story that no spec covers, and this command must not offer work that the
skill then refuses. The order is the target_date of the milestone, then the
ID. An item with no milestone, or with a milestone that has no date, comes
last.
"""
from datetime import datetime, timezone
from pathlib import Path

from .claims import is_live
from .ghmodel import page_id_of
from .regen import collect
from .registry import WORK_ITEMS
from .textsafe import escape_controls

MISSING = "-"


def _milestone_of(frontmatter: dict) -> str:
    target = frontmatter.get("milestone")
    return page_id_of(str(target)) if target else ""


def rows(root: Path, milestone: str | None = None,
         type_name: str | None = None,
         now: datetime | None = None) -> list[str]:
    """One `ID<tab>title<tab>milestone` line for each item an agent may take."""
    now = now or datetime.now(timezone.utc)
    pages = collect(root)
    dates = {path.stem: frontmatter.get("target_date")
             for path, (_bundle, frontmatter, _body) in pages.items()
             if frontmatter.get("type") == "Milestone"}
    found = []
    for path, (bundle, frontmatter, _body) in pages.items():
        if bundle != "roadmap" or frontmatter.get("type") not in WORK_ITEMS:
            continue
        if frontmatter.get("state") != "ready":
            continue
        if is_live(frontmatter.get("claim"), now):
            continue
        # `product:work` refuses a Story that no spec covers, and a `spec: none`
        # Story needs no build. An item that the skill must refuse is not
        # offered. Only a Story holds the slot, so no other type is filtered.
        if frontmatter.get("type") == "Story" \
                and str(frontmatter.get("spec") or "") in ("", "none"):
            continue
        if type_name and frontmatter.get("type") != type_name:
            continue
        own = _milestone_of(frontmatter)
        if milestone and own != milestone:
            continue
        date = dates.get(own)
        # (0, date) sorts before (1, ""), so a dated milestone comes first.
        key = (0, str(date)) if date else (1, "")
        found.append((key, path.stem,
                      f"{escape_controls(path.stem)}\t"
                      f"{escape_controls(frontmatter.get('title', ''))}\t"
                      f"{escape_controls(own) if own else MISSING}"))
    return [row for _key, _page_id, row in sorted(found)]
