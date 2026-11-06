"""The strategic decisions register (register.jsonl) and the notes (notes.jsonl).

Spec §4 step 5 and §5a. Both files are append-only and hash-chained (chained_log). A changed
choice is a new entry that names the entry it supersedes. Status is never stored: readers derive
it by replaying the lines in file order under the same rules the writers apply, and a line that
breaks a rule counts as absent and adds a named reason (ignored_lines). Every refusal is
RegisterRefused; LogRefused, EvidenceRefused and CaseRefused are re-raised as it, with the cause.
"""
from __future__ import annotations

import re
from pathlib import Path

# Aliased: add_entry takes a keyword named `evidence`.
from lib import case_files, chained_log, clock, paths
from lib import evidence as evidence_pages

CATEGORIES = (("why", "Why"), ("who", "Who"), ("what", "What"), ("where", "Where"),
              ("how-it-wins", "How it wins (commercial)"), ("price-and-model", "Price and model"),
              ("delivery", "Delivery to the customer"), ("when", "When"))
CATEGORY_KEYS = tuple(key for key, _ in CATEGORIES)

STATUSES = ("stated", "stated (coach)", "confirmed", "superseded")
SOURCES = ("proposal", "strategy", "user", "coach")
PLUGIN_SOURCE = re.compile(r"^plugin:[a-z0-9][a-z0-9-]*$")

AUTOMATED = case_files.AUTOMATED
# Sources that need a person present: an automated session records neither (ruling N-11).
_PERSON_SOURCES = ("coach", "user")


def is_automated(name) -> bool:
    """Whether a line's recorded_by or name marks it as written in an automated session. The one
    check the register and the conditions share, at write time and at read time."""
    return name == AUTOMATED


def session_recorded_by(case_dir) -> str:
    """The current session's person, or `automated`: what a register, notes or conditions line
    records as its writer. The one session check those modules share. Raises case_files.CaseRefused
    with no session; each caller re-raises it as its own refusal."""
    case_dir = Path(case_dir)
    if case_files.current_session(case_dir).get("mode") == AUTOMATED:
        return AUTOMATED
    return case_files.current_name(case_dir)


_ENTRY_ID = re.compile(r"^SD-([0-9]{3,})$")
_NOTE_ID = re.compile(r"^N-([0-9]{3,})$")
_ENTRY_FIELDS = frozenset({"line", "id", "category", "choice", "rejected_alternative", "evidence", "source",
                           "recorded_by", "date", "supersedes", "reason", "change_source", "prev"})
_CONFIRM_FIELDS = frozenset({"line", "ref", "question", "answer", "role", "name", "date", "prev"})
_NOTE_FIELDS = frozenset({"line", "id", "text", "source", "failed_tests", "reason", "recorded_by", "date",
                          "prev"})


class RegisterRefused(ValueError):
    """A register or notes operation the rules refuse, or a file that cannot be read."""


def _blank(value) -> bool:
    return not isinstance(value, str) or value.strip() == ""


def _fold(text: str) -> str:
    return " ".join(text.split()).casefold()


def _source_problem(source) -> str | None:
    if isinstance(source, str) and (source in SOURCES or PLUGIN_SOURCE.fullmatch(source)):
        return None
    return (f"the source {source!r} is not one of {', '.join(SOURCES)} "
            "or plugin:<name> (lowercase letters, digits and hyphens)")


def _automated_source_problem(source, automated: bool) -> str | None:
    if automated and source in _PERSON_SOURCES:
        return (f"an automated session may not record source {source}: no person is present; "
                "record the claim with source strategy, or as a note")
    return None


def _fields_problem(record: dict, allowed: frozenset) -> str | None:
    extra = sorted(set(record) - allowed)
    missing = sorted(allowed - set(record) - {"prev"})
    if extra or missing:
        parts = ([f"unknown field(s) {', '.join(extra)}"] if extra else []) + (
            [f"missing field(s) {', '.join(missing)}"] if missing else [])
        return "the line has " + " and ".join(parts)
    return None


def _check_supersede(supersedes, reason, change_source, *, categories: dict, superseded_by: dict,
                     confirmed, category, automated: bool, refused: type) -> None:
    """Raise `refused` when a supersede breaks a rule. Takes the already-derived state (ruling PF-14):
    `categories` maps every counted ID to its category (None where there is none), `superseded_by`
    maps a superseded ID to its successor, `confirmed` holds the confirmed IDs. With `category` None
    there is no same-category rule (conditions, ruling N-7)."""
    given = [not _blank(reason), not _blank(change_source)]
    if supersedes is None:
        if any(given) or reason is not None or change_source is not None:
            raise refused("a reason and a change source are given only with supersedes")
        return
    if not all(given):
        raise refused("a supersede needs a reason and a change source, neither blank")
    if not isinstance(supersedes, str) or supersedes not in categories:
        raise refused(f"{supersedes!r} is not a recorded ID; supersede one that is")
    if supersedes in superseded_by:
        raise refused(f"{supersedes} is already superseded by {superseded_by[supersedes]}; "
                      f"supersede {superseded_by[supersedes]} instead")
    if category is not None and categories[supersedes] != category:
        raise refused(f"{supersedes} is in category {categories[supersedes]}, not {category}; "
                      "an entry supersedes only an entry of its own category")
    if automated and supersedes in confirmed:
        raise refused(f"an automated session may not supersede {supersedes}: a person confirmed it")


class _Register:
    """The register derived from its lines: counted entries, confirmations, supersedes, reasons."""

    def __init__(self) -> None:
        self.entries: dict = {}
        self.confirmed: dict = {}
        self.superseded_by: dict = {}
        self.ignored: list = []
        self.last_number = 0

    def entry_problem(self, case_dir: Path, rec: dict) -> str | None:
        problem = _fields_problem(rec, _ENTRY_FIELDS)
        if problem:
            return problem
        if not isinstance(rec["id"], str) or not _ENTRY_ID.fullmatch(rec["id"]) or rec["id"] in self.entries:
            return f"the entry ID {rec['id']!r} is not a new SD-NNN"
        if rec["category"] not in CATEGORY_KEYS:
            return f"the category {rec['category']!r} is not one of {', '.join(CATEGORY_KEYS)}"
        if _blank(rec["choice"]) or _blank(rec["rejected_alternative"]):
            return "the choice and the rejected alternative must not be blank"
        if _fold(rec["choice"]) == _fold(rec["rejected_alternative"]):
            return "the rejected alternative is the choice itself; name the choice it rules out"
        problem = _source_problem(rec["source"])
        if problem:
            return problem
        if _blank(rec["recorded_by"]) or _blank(rec["date"]):
            return "recorded_by and date must not be blank"
        automated = is_automated(rec["recorded_by"])
        problem = _automated_source_problem(rec["source"], automated)
        if problem:
            return problem
        ev = rec["evidence"]
        if not isinstance(ev, list) or not all(isinstance(e, str) for e in ev):
            return "the evidence is a list of evidence page IDs"
        try:
            evidence_pages.check_support_pages(case_dir, ev)
            _check_supersede(rec["supersedes"], rec["reason"], rec["change_source"],
                             categories={i: e["category"] for i, e in self.entries.items()},
                             superseded_by=self.superseded_by, confirmed=self.confirmed,
                             category=rec["category"], automated=automated, refused=RegisterRefused)
        except (evidence_pages.EvidenceRefused, RegisterRefused) as exc:
            return str(exc)
        return None

    def confirm_problem(self, rec: dict) -> str | None:
        problem = _fields_problem(rec, _CONFIRM_FIELDS)
        if problem:
            return problem
        if _blank(rec["name"]) or _blank(rec["question"]) or _blank(rec["answer"]) or _blank(rec["date"]):
            return "a confirmation's name, question, answer and date must not be blank"
        if is_automated(rec["name"]):
            return ("the confirmation names automated: an automated session may not confirm an entry; "
                    "only a named person confirms one")
        if rec["role"] != "proposer":
            return f"the role {rec['role']!r} is not proposer; only the proposer confirms an entry"
        ref = rec["ref"]
        if not isinstance(ref, str) or ref not in self.entries:
            return f"{ref!r} is not a recorded entry"
        if ref in self.superseded_by:
            return f"{ref} is superseded by {self.superseded_by[ref]}; confirm {self.superseded_by[ref]} instead"
        if ref in self.confirmed:
            return f"{ref} is already confirmed"
        return None

    def count(self, case_dir: Path, n: int, rec: dict) -> None:
        kind = rec.get("line")
        if kind == "entry":
            m = _ENTRY_ID.fullmatch(rec["id"]) if isinstance(rec.get("id"), str) else None
            if m:
                self.last_number = max(self.last_number, int(m.group(1)))
            problem = self.entry_problem(case_dir, rec)
        elif kind == "confirm":
            problem = self.confirm_problem(rec)
        else:
            problem = f"the line kind {kind!r} is not entry or confirm"
        if problem:
            self.ignored.append(f"{paths.REGISTER} line {n}: {problem}; the line does not count")
            return
        if kind == "entry":
            self.entries[rec["id"]] = rec
            if rec["supersedes"] is not None:
                self.superseded_by[rec["supersedes"]] = rec["id"]
        else:
            self.confirmed[rec["ref"]] = rec


def _read(case_dir: Path, name: str) -> list:
    try:
        return chained_log.read(Path(case_dir) / name)
    except chained_log.LogRefused as exc:
        raise RegisterRefused(str(exc)) from exc


def _derive(case_dir: Path) -> _Register:
    state = _Register()
    for n, rec in enumerate(_read(case_dir, paths.REGISTER), 1):
        state.count(case_dir, n, rec)
    return state


def _append(case_dir: Path, name: str, record) -> dict:
    try:
        return chained_log.append(Path(case_dir) / name, record)
    except chained_log.LogRefused as exc:
        raise RegisterRefused(str(exc)) from exc


def _recorded_by(case_dir: Path) -> str:
    """session_recorded_by, refused as RegisterRefused."""
    try:
        return session_recorded_by(case_dir)
    except case_files.CaseRefused as exc:
        raise RegisterRefused(str(exc)) from exc


def add_entry(case_dir, *, category, choice, rejected_alternative, evidence=(), source,
              supersedes=None, reason=None, change_source=None) -> dict:
    """Record a new entry as the next SD-NNN and return the stored line."""
    case_dir = Path(case_dir)
    recorded_by = _recorded_by(case_dir)
    ev = list(evidence) if isinstance(evidence, (list, tuple)) else evidence

    def build() -> dict:  # under the log's lock, so the number follows the lines on file
        state = _derive(case_dir)
        rec = {"line": "entry", "id": f"SD-{state.last_number + 1:03d}", "category": category, "choice": choice,
               "rejected_alternative": rejected_alternative, "evidence": ev, "source": source,
               "recorded_by": recorded_by, "date": clock.today(), "supersedes": supersedes, "reason": reason,
               "change_source": change_source}
        if isinstance(ev, list):
            try:  # checked here too, so the refusal keeps the page's own exception as its cause
                evidence_pages.check_support_pages(case_dir, ev)
            except evidence_pages.EvidenceRefused as exc:
                raise RegisterRefused(str(exc)) from exc
        problem = state.entry_problem(case_dir, rec)
        if problem:
            raise RegisterRefused(problem)
        return rec
    return _append(case_dir, paths.REGISTER, build)


def confirm_entry(case_dir, entry_id, *, question, answer) -> dict:
    """Record the proposer's confirmation of a live, unconfirmed entry, with the answer verbatim.
    Needs a named person: an automated session is refused."""
    case_dir = Path(case_dir)
    try:
        name = case_files.current_name(case_dir)
    except case_files.CaseRefused as exc:
        raise RegisterRefused(f"{exc}; only a named person confirms an entry") from exc
    if _blank(question) or _blank(answer):
        raise RegisterRefused("the question and the person's answer must not be blank")
    rec = {"line": "confirm", "ref": entry_id, "question": question, "answer": answer, "role": "proposer",
           "name": name, "date": clock.today()}

    def build() -> dict:  # under the log's lock, so the check reads the lines on file
        problem = _derive(case_dir).confirm_problem(rec)
        if problem:
            raise RegisterRefused(problem)
        return rec
    return _append(case_dir, paths.REGISTER, build)


def _status(state: _Register, entry_id: str) -> str:
    if entry_id in state.superseded_by:
        return "superseded"
    if entry_id in state.confirmed:
        return "confirmed"
    return "stated (coach)" if state.entries[entry_id]["source"] == "coach" else "stated"


def _number(entry_id: str) -> int:
    return int(_ENTRY_ID.fullmatch(entry_id).group(1))


def entries(case_dir) -> dict:
    """The counted entries by ID, each with its derived `status` and `superseded_by`."""
    state = _derive(Path(case_dir))
    out = {}
    for entry_id, rec in state.entries.items():
        line = {k: v for k, v in rec.items() if k != "prev"}
        out[entry_id] = dict(line, status=_status(state, entry_id),
                             superseded_by=state.superseded_by.get(entry_id))
    return out


def live_entries(case_dir) -> list:
    """The entries not superseded, in ID order."""
    return sorted((e for e in entries(case_dir).values() if e["status"] != "superseded"),
                  key=lambda e: _number(e["id"]))


def absent_categories(case_dir) -> tuple:
    """Category keys, in CATEGORY_KEYS order, with no live entry that is stated or confirmed. An entry
    the coach proposed (`stated (coach)`) does not fill its category."""
    filled = {e["category"] for e in live_entries(case_dir) if e["status"] in ("stated", "confirmed")}
    return tuple(key for key in CATEGORY_KEYS if key not in filled)


# --- notes ------------------------------------------------------------------------------------


def _failed_tests_problem(failed) -> str | None:
    if (not isinstance(failed, list) or not failed
            or not all(isinstance(t, int) and not isinstance(t, bool) and 1 <= t <= 4 for t in failed)
            or len(set(failed)) != len(failed)):
        return "failed_tests is a non-empty list of distinct test numbers from 1 to 4"
    return None


def _note_problem(rec: dict, seen: set) -> str | None:
    problem = _fields_problem(rec, _NOTE_FIELDS)
    if problem:
        return problem
    if not isinstance(rec["id"], str) or not _NOTE_ID.fullmatch(rec["id"]) or rec["id"] in seen:
        return f"the note ID {rec['id']!r} is not a new N-NNN"
    if _blank(rec["text"]) or _blank(rec["reason"]):
        return "a note's text and reason must not be blank"
    problem = _source_problem(rec["source"]) or _failed_tests_problem(rec["failed_tests"])
    if problem:
        return problem
    if _blank(rec["recorded_by"]) or _blank(rec["date"]):
        return "recorded_by and date must not be blank"
    return _automated_source_problem(rec["source"], is_automated(rec["recorded_by"]))


def _derive_notes(case_dir: Path) -> tuple:
    """(counted notes, reasons for ignored lines, highest N number seen)."""
    counted, ignored, last = [], [], 0
    seen: set = set()
    for n, rec in enumerate(_read(case_dir, paths.NOTES), 1):
        m = _NOTE_ID.fullmatch(rec["id"]) if isinstance(rec.get("id"), str) else None
        if m:
            last = max(last, int(m.group(1)))
        problem = (_note_problem(rec, seen) if rec.get("line") == "note"
                   else f"the line kind {rec.get('line')!r} is not note")
        if problem:
            ignored.append(f"{paths.NOTES} line {n}: {problem}; the line does not count")
            continue
        seen.add(rec["id"])
        counted.append({k: v for k, v in rec.items() if k != "prev"})
    return counted, ignored, last


def add_note(case_dir, *, text, source, failed_tests, reason) -> dict:
    """Record a claim that fails the four-part test (§5a) as the next N-NNN, with the parts it fails."""
    case_dir = Path(case_dir)
    recorded_by = _recorded_by(case_dir)

    def build() -> dict:  # under the log's lock, so the number follows the lines on file
        _, _, last = _derive_notes(case_dir)
        rec = {"line": "note", "id": f"N-{last + 1:03d}", "text": text, "source": source,
               "failed_tests": list(failed_tests) if isinstance(failed_tests, tuple) else failed_tests,
               "reason": reason, "recorded_by": recorded_by, "date": clock.today()}
        problem = _note_problem(rec, set())
        if problem:
            raise RegisterRefused(problem)
        return rec
    return _append(case_dir, paths.NOTES, build)


def notes(case_dir) -> list:
    """The counted notes, in file order."""
    return _derive_notes(Path(case_dir))[0]


def ignored_lines(case_dir) -> tuple:
    """One reason per line of register.jsonl or notes.jsonl that the readers do not count."""
    case_dir = Path(case_dir)
    return tuple(_derive(case_dir).ignored + _derive_notes(case_dir)[1])
