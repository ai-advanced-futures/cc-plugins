"""Evidence pages: one JSON file per source, graded, with the grade confirmed by a person.

Spec §5. A page is never edited or overwritten; a new source is a new page.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path

from lib import case_doc, case_files, paths, rubric

GRADES = ("primary", "secondary", "estimated")

_ID_PATTERN = re.compile(r"^EV-[0-9]{3,}$")
_STRING_FIELDS = ("source", "date", "method", "grade", "grade_confirmed_by", "supplied_by")
_ALLOWED = frozenset(_STRING_FIELDS) | {"produced_by_plugin", "off_map", "item_ids", "summary", "result_ref"}

# The one form in which a page names the case's own text as its source.
STATEMENT_SOURCE = re.compile(r"^business-case\.md §(?P<key>[a-z-]+)$")
# The case's strategy files. Each records a choice or projects one; none is evidence for it.
STRATEGY_FILES = (paths.REGISTER, paths.CONDITIONS, paths.NOTES, paths.STRATEGY_VIEW)
CASE_FILES = (paths.CASE_DOC,) + STRATEGY_FILES
# A case file name as a whole name (fix round 2, N-1): no name character joined before it, and none
# after it. A name character is a letter, a digit, `_`, `-`, or a `.` that joins more of a name, so
# `my-register.jsonl` and `register.jsonl.bak` are other files. Any other mark may follow: `:3`,
# `/SD-001`, `!`, `?`, `#`, `,`, a space, a full stop that ends a sentence, or the end of the text.
_CASE_FILE_NAME = re.compile(r"(?<![\w.\-])(" + "|".join(re.escape(n) for n in CASE_FILES)
                             + r")(?![\w\-]|\.[\w\-])")


class EvidenceRefused(ValueError):
    """An evidence page the rules refuse."""


def _blank(value) -> bool:
    return not isinstance(value, str) or value.strip() == ""


def relpath(ev_id: str) -> str:
    return f"{paths.EVIDENCE_DIR}/{ev_id}.json"


def page_path(case_dir: Path, ev_id: str) -> Path:
    if not isinstance(ev_id, str) or not _ID_PATTERN.fullmatch(ev_id):
        raise EvidenceRefused(f"{ev_id!r} is not an evidence ID (EV-001 and up)")
    return Path(case_dir) / paths.EVIDENCE_DIR / f"{ev_id}.json"


def read_page(case_dir: Path, ev_id: str) -> dict:
    """The page, or EvidenceRefused when it cannot be read, is not an object with a list of item IDs,
    or has a grade outside GRADES (only a hand edit makes one)."""
    path = page_path(case_dir, ev_id)
    try:
        page = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceRefused(f"cannot read evidence page {ev_id}: {exc}") from exc
    ids = page.get("item_ids") if isinstance(page, dict) else None
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        raise EvidenceRefused(f"evidence page {ev_id} is not an object with a list of item IDs")
    if page.get("grade") not in GRADES:
        raise EvidenceRefused(f"evidence page {ev_id} has grade {page.get('grade')!r}, not one of "
                              f"{', '.join(GRADES)}; correct the page")
    return page


def _validate(case_dir: Path, page: dict, person: str) -> dict:
    if not isinstance(page, dict):
        raise EvidenceRefused("an evidence page is a JSON object")
    extra = sorted(set(page) - _ALLOWED)
    if extra:
        raise EvidenceRefused(f"unknown evidence field(s): {', '.join(extra)}")
    for field in _STRING_FIELDS:
        if _blank(page.get(field)):
            raise EvidenceRefused(f"the evidence field {field} is blank or missing")
    try:
        date.fromisoformat(page["date"].strip())
    except ValueError:
        raise EvidenceRefused(f"the evidence field date {page['date']!r} is not an ISO date (YYYY-MM-DD)") from None
    if page["grade_confirmed_by"].strip() != person:
        raise EvidenceRefused(f"the evidence field grade_confirmed_by {page['grade_confirmed_by']!r} is not the "
                              f"session's person, {person!r}; the person in the session confirms the grade")
    if page["grade"] not in GRADES:
        raise EvidenceRefused(f"the evidence field grade {page['grade']!r} is not one of {', '.join(GRADES)}")
    plugin = page.get("produced_by_plugin")
    if plugin is not None and not isinstance(plugin, str):
        raise EvidenceRefused("the evidence field produced_by_plugin is a string or null")
    off_map = page.get("off_map", False)
    if not isinstance(off_map, bool):
        raise EvidenceRefused("the evidence field off_map is true or false")
    summary = page.get("summary", "")
    if not isinstance(summary, str):
        raise EvidenceRefused("the evidence field summary is a string")
    ids = page.get("item_ids")
    # An empty list is a page cited only as support of an entry or a condition (ruling M-11).
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        raise EvidenceRefused("the evidence field item_ids is a list of rubric item IDs")
    case_dir = Path(case_dir)
    rub = rubric.load_rubric(case_dir / paths.RUBRIC_COPY)
    known = {i["id"] for i in rub["items"]}
    applicable = set(case_files.read_scope(case_dir)["applicable_item_ids"])
    if len(set(ids)) != len(ids):
        repeated = sorted({i for i in ids if ids.count(i) > 1})
        raise EvidenceRefused(f"item_ids repeats {', '.join(repeated)}")
    for item_id in ids:
        if item_id not in known:
            raise EvidenceRefused(f"item_ids names {item_id}, which is not a rubric item")
        if item_id not in applicable:
            raise EvidenceRefused(f"item_ids names {item_id}, which does not apply to this case's scope")
    problem = case_source_problem(case_dir, page, rubric.statement_item_ids(rub))
    if problem:
        raise EvidenceRefused(problem)
    return {**page, "date": page["date"].strip(), "grade_confirmed_by": page["grade_confirmed_by"].strip(),
            "produced_by_plugin": plugin, "off_map": off_map, "summary": summary}


def _case_sections(case_dir: Path) -> dict:
    try:
        return case_doc.parse_sections((Path(case_dir) / paths.CASE_DOC).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, case_doc.CaseDocError):
        return {}


def case_files_named(source: str) -> list:
    """The case files a source names, in order, each matched as a whole name, case folded:
    `./business-case.md §pricing`, `register.jsonl:3` and `docs/notes.jsonl/N-001` name one;
    `meeting-notes.jsonl` and `register.jsonl.bak` name none (final review M-9, fix round 2 N-1).
    The one test for both checks below."""
    return [m.group(1) for m in _CASE_FILE_NAME.finditer(source.casefold())]


def _first_case_file(folded: str) -> str | None:
    """The case file the source's first word names, or None: the first whole name, with no space
    before it, so a path or a mark may come first (`./register.jsonl`, `(register.jsonl)`)."""
    m = _CASE_FILE_NAME.search(folded)
    return m.group(1) if m and not any(c.isspace() for c in folded[:m.start()]) else None


def case_source_problem(case_dir: Path, page: dict, statement_ids: frozenset) -> str | None:
    """Why a page's source does not count, or None. A check on how the source starts: a source
    whose first word is a strategy file, or a path to one, is refused; one whose first word is
    `business-case.md`, or a path to it, must read `business-case.md §<section>` for a section the
    case has, and is graded `estimated` unless every item it lists is a statement item. Any other
    source passes this check."""
    source = page.get("source") if isinstance(page, dict) else None
    if not isinstance(source, str):
        return None
    folded = source.strip().casefold()
    first = _first_case_file(folded)
    if first in STRATEGY_FILES:
        return f"a strategy file is not evidence; cite the page behind it (source {source!r})"
    if first != paths.CASE_DOC:
        return None
    m = STATEMENT_SOURCE.match(folded)
    if not m or m.group("key") not in _case_sections(case_dir):
        return (f"the source {source!r} names the case; write it as business-case.md §<section>, "
                "for a section the case has")
    ids = page.get("item_ids")
    others = [i for i in ids if i not in statement_ids] if isinstance(ids, list) else []
    if others and page.get("grade") != "estimated":
        return (f"a page sourced from the case is graded estimated when it lists {', '.join(others)}: "
                "for these items the case's own text is not primary or secondary evidence")
    return None


def check_support_pages(case_dir: Path, ev_ids) -> list:
    """The pages cited as support of an entry or a condition, each checked: it exists, and its
    source names none of the case's own files. Its item_ids may be empty. Raises EvidenceRefused
    naming the page."""
    out = []
    for ev_id in ev_ids:
        page = read_page(case_dir, ev_id)
        source = page.get("source")
        if not isinstance(source, str) or not source.strip():
            raise EvidenceRefused(f"evidence page {ev_id} has no source")
        named = case_files_named(source)
        if named:
            raise EvidenceRefused(f"evidence page {ev_id} names {named[0]}, a file of this case, as its source; "
                                  "a support page cites the source behind the case")
        out.append(ev_id)
    return out


def write_page(case_dir: Path, page: dict) -> str:
    """Validate a page and write it as the next EV-NNN. Returns the ID. Needs a named person in the
    current session: a grade is the person's to confirm, so an automated session is refused."""
    case_dir = Path(case_dir)
    person = case_files.current_name(case_dir)
    clean = _validate(case_dir, page, person)
    folder = case_dir / paths.EVIDENCE_DIR
    folder.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.stem[3:]) for p in folder.glob("EV-*.json") if _ID_PATTERN.fullmatch(p.stem)]
    data = (json.dumps(clean, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    n = max(numbers, default=0) + 1
    # Write the whole page to a temp file, then link it to its ID: the link fails when the ID is
    # taken, so no two pages share an ID and a page is never overwritten, and a crash never leaves
    # a half-written EV-NNN.json.
    fd, tmp = tempfile.mkstemp(dir=str(folder), prefix=".page-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        while True:
            ev_id = f"EV-{n:03d}"
            try:
                os.link(tmp, folder / f"{ev_id}.json")
            except FileExistsError:
                n += 1
                continue
            return ev_id
    finally:
        os.unlink(tmp)
