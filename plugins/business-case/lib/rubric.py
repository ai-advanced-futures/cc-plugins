"""The versioned rubric: load and validate a rubric file, and select the items a market needs.

A rubric file is JSON:
    {"version": str, "estimated_share_threshold": float in (0, 1),
     "items": [{"id", "title", "section", "lens", "applies_to", "needs_code_arithmetic", "met_test"}]}
where `met_test` is {"id": "<item id>.M<n>", "text": str}. An item may also carry "computed": true.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from lib import paths

# The nine lens keys of /product:explore, verbatim (spec §3).
PRD_LENSES = ("problem", "personas", "journeys", "capabilities", "scope",
              "success-metrics", "business-model", "go-to-market", "risks-assumptions")

MARKETS = ("B2B", "B2C", "both")

_TOP_KEYS = frozenset({"version", "estimated_share_threshold", "items"})
_ITEM_KEYS = frozenset({"id", "title", "section", "lens", "applies_to", "needs_code_arithmetic", "met_test"})
# An item may carry "computed": true (code settles it, the review does not). Only true.
_OPTIONAL_ITEM_KEYS = frozenset({"computed"})
# \Z, not $: `$` also matches before a final newline, so "BC-JOBS.M1\n" would pass (Task 15 carry a).
MET_TEST_ID = re.compile(r"^(?P<item>BC-[A-Z0-9-]+)\.M(?P<n>[1-9][0-9]*)\Z")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+\Z")
_MET_TEST_KEYS = frozenset({"id", "text"})
_SECTION_KEY = re.compile(r"^[a-z-]+\Z")


class RubricError(ValueError):
    """A rubric file, market or item ID is not valid."""


def shipped_rubric_path(version: str) -> Path:
    """The path of a rubric version shipped with the plugin."""
    return paths.PLUGIN_ROOT / "rubric" / f"rubric-{version}.json"


def version_key(version: str) -> tuple:
    """A version "N.N.N" as a tuple of three numbers, for ordering. Raises RubricError otherwise."""
    if not isinstance(version, str) or not _VERSION.match(version):
        raise RubricError(f"rubric version {version!r} is not N.N.N")
    major, minor, patch = (int(x) for x in version.split("."))
    return (major, minor, patch)


def shipped_versions() -> tuple:
    """Every rubric version shipped with the plugin, oldest first."""
    found = []
    for f in (paths.PLUGIN_ROOT / "rubric").glob("rubric-*.json"):
        found.append(f.name[len("rubric-"):-len(".json")])
    return tuple(sorted(found, key=version_key))


def newest_version() -> str:
    """The newest rubric version shipped with the plugin. A new case opens on it."""
    versions = shipped_versions()
    if not versions:
        raise RubricError(f"no rubric file ships in {paths.PLUGIN_ROOT / 'rubric'}")
    return versions[-1]


def _nonblank(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _item_problems(n: int, entry) -> list:
    if not isinstance(entry, dict):
        return [f"item {n} is not an object"]
    iid = entry.get("id")
    where = f"item {iid}" if _nonblank(iid) else f"item {n}"
    problems = []
    if not _ITEM_KEYS <= set(entry) or not set(entry) <= _ITEM_KEYS | _OPTIONAL_ITEM_KEYS:
        missing = sorted(_ITEM_KEYS - set(entry))
        extra = sorted(set(entry) - _ITEM_KEYS - _OPTIONAL_ITEM_KEYS)
        problems.append(f"{where} keys: missing {missing}, extra {extra}")
    if "computed" in entry and entry["computed"] is not True:
        problems.append(f"{where} computed {entry['computed']!r} is not true")
    if not _nonblank(iid):
        problems.append(f"{where} has no id")
    if not _nonblank(entry.get("title")):
        problems.append(f"{where} has no title")
    section = entry.get("section")
    if not isinstance(section, str) or not _SECTION_KEY.match(section):
        problems.append(f"{where} section {section!r} is not a lowercase key")
    if entry.get("lens") not in PRD_LENSES:
        problems.append(f"{where} lens {entry.get('lens')!r} is not one of {list(PRD_LENSES)}")
    if entry.get("applies_to") not in MARKETS:
        problems.append(f"{where} applies_to {entry.get('applies_to')!r} is not one of {list(MARKETS)}")
    if not isinstance(entry.get("needs_code_arithmetic"), bool):
        problems.append(f"{where} needs_code_arithmetic is not true or false")
    met = entry.get("met_test")
    if not isinstance(met, dict) or set(met) != _MET_TEST_KEYS:
        problems.append(f"{where} met_test is not {{id, text}}")
    else:
        found = MET_TEST_ID.match(met.get("id")) if isinstance(met.get("id"), str) else None
        if not found or found.group("item") != iid:
            problems.append(f"{where} met_test id {met.get('id')!r} is not {iid}.M<n>")
        if not _nonblank(met.get("text")):
            problems.append(f"{where} met_test text is empty")
    return problems


def validate_rubric(data) -> list:
    """Every problem with a parsed rubric; an empty list means it is valid."""
    if not isinstance(data, dict):
        return ["the rubric is not a JSON object"]
    problems = []
    if set(data) != _TOP_KEYS:
        missing, extra = sorted(_TOP_KEYS - set(data)), sorted(set(data) - _TOP_KEYS)
        problems.append(f"top-level keys: missing {missing}, extra {extra}")
    if not _nonblank(data.get("version")):
        problems.append("version is missing")
    threshold = data.get("estimated_share_threshold")
    if not isinstance(threshold, (int, float)) or not 0 < threshold < 1:  # true and false fall outside
        problems.append(f"estimated_share_threshold {threshold!r} is not a number between 0 and 1")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        problems.append("items is not a non-empty list")
        return problems
    seen = set()
    section_lens = {}  # the template's marker carries one lens per section
    for n, entry in enumerate(items, 1):
        problems.extend(_item_problems(n, entry))
        if isinstance(entry, dict) and isinstance(entry.get("section"), str):
            first = section_lens.setdefault(entry["section"], entry.get("lens"))
            if first != entry.get("lens"):
                problems.append(f"section {entry['section']} has two lenses: {first!r} and {entry.get('lens')!r}")
        iid = entry.get("id") if isinstance(entry, dict) else None
        if not isinstance(iid, str):
            continue
        if iid in seen:
            problems.append(f"item id {iid} repeats")
        seen.add(iid)
    return problems


def load_rubric(path: Path) -> dict:
    """Read and validate a rubric file. Raises RubricError naming every problem."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RubricError(f"cannot read rubric {path}: {exc}") from exc
    problems = validate_rubric(data)
    if problems:
        raise RubricError(f"rubric {path} is not valid: " + "; ".join(problems))
    return data


def applicable_items(rubric: dict, market: str) -> list:
    """The items that apply to a case with this market, in rubric order.
    A `both` case needs every item; a B2B or B2C case skips the other market's items."""
    if market not in MARKETS:
        raise RubricError(f"market {market!r} is not one of {list(MARKETS)}")
    if market == "both":
        return list(rubric["items"])
    return [i for i in rubric["items"] if i["applies_to"] in (market, "both")]


def item(rubric: dict, item_id: str) -> dict:
    """The item with this ID. Raises RubricError when the rubric has no such item."""
    for entry in rubric["items"]:
        if entry["id"] == item_id:
            return entry
    raise RubricError(f"rubric {rubric.get('version')} has no item {item_id}")


def met_test_id(rub: dict, item_id: str) -> str:
    """The met-test ID of an item, as its rubric file writes it."""
    return item(rub, item_id)["met_test"]["id"]


def computed_item_ids(rub: dict) -> frozenset:
    """The items the rubric marks "computed": code settles them."""
    return frozenset(i["id"] for i in rub["items"] if i.get("computed") is True)


# The words by which a met test's "Evidence that counts" names the case's own text.
CASE_TEXT_MARKERS = ("the case", "as written", "section", "register")
# A met test that asks for the evidence behind a plan or forecast: case text is not that evidence.
PLAN_EVIDENCE = "the evidence behind"

_EVIDENCE_THAT_COUNTS = re.compile(r"Evidence that counts:(.*)", re.S)


def evidence_that_counts(entry: dict) -> str | None:
    """The text after "Evidence that counts:" in an item's met test, stripped, or None."""
    m = _EVIDENCE_THAT_COUNTS.search(entry["met_test"]["text"])
    return m.group(1).strip() if m else None


def statement_item_ids(rub: dict) -> frozenset:
    """The items for which the case's own text is the evidence: their "Evidence that counts" names
    the case's text and does not ask for the evidence behind a plan. Only for these may a page
    sourced from the case be graded primary or secondary."""
    out = set()
    for entry in rub["items"]:
        text = evidence_that_counts(entry)
        if text is None:
            continue
        folded = text.casefold()
        if any(m in folded for m in CASE_TEXT_MARKERS) and PLAN_EVIDENCE not in folded:
            out.add(entry["id"])
    return frozenset(out)
