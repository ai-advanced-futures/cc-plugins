"""The conditions list (conditions.jsonl): what must be true for a register entry's choice to work.

Spec §4 and §5. The file is append-only and hash-chained (chained_log). A condition line names
the entry it `supports`; mark lines set it `confirmed` or `unsupported`, and the latest counted
mark wins. A changed condition is a new condition that names the one it supersedes. Status is
never stored: readers replay the lines in file order under the rules the writers apply, and a
line that breaks one counts as absent and adds a named reason (ignored_lines).

`supports` is never resolved. A live condition whose entry is superseded is orphaned; the coach
records it again against the successor by superseding the condition.

The orphan rule on a mark is a write-time rule only. The register and the conditions are two
files with no shared order, so a reader cannot tell whether a mark came before or after the
entry's supersede. For the same reason a reader checks only that `supports` names a counted
entry, not that the entry was live when the condition was written.

Every refusal is ConditionRefused; LogRefused, EvidenceRefused, RegisterRefused and CaseRefused
are re-raised as it, with the cause.
"""
from __future__ import annotations

import re
from pathlib import Path

# Aliased: add_condition takes a keyword named `evidence`.
from lib import case_files, chained_log, clock, paths, register
from lib import evidence as evidence_pages

STATUSES = ("stated", "stated (coach)", "confirmed", "unsupported", "superseded")
MARKS = ("confirmed", "unsupported")
REQUIRED_STATES = ("orphaned", "unsupported")  # in precedence order

_CONDITION_ID = re.compile(r"^C-([0-9]{3,})$")
_CONDITION_FIELDS = frozenset({"line", "id", "text", "supports", "evidence", "source", "recorded_by", "date",
                               "supersedes", "reason", "change_source", "prev"})
_MARK_FIELDS = frozenset({"line", "ref", "as", "question", "answer", "role", "name", "date", "prev"})


class ConditionRefused(ValueError):
    """A conditions operation the rules refuse, or a file that cannot be read."""


_blank = register._blank


class _Conditions:
    """The conditions derived from their lines: counted conditions, latest marks, supersedes, reasons."""

    def __init__(self, entries: dict) -> None:
        self.entries = entries  # the register's counted entries, with derived status
        self.conditions: dict = {}
        self.latest_mark: dict = {}
        self.superseded_by: dict = {}
        self.ignored: list = []
        self.last_number = 0

    def confirmed(self) -> frozenset:
        return frozenset(c for c, mark in self.latest_mark.items() if mark["as"] == "confirmed")

    def condition_problem(self, case_dir: Path, rec: dict) -> str | None:
        problem = register._fields_problem(rec, _CONDITION_FIELDS)
        if problem:
            return problem
        if (not isinstance(rec["id"], str) or not _CONDITION_ID.fullmatch(rec["id"])
                or rec["id"] in self.conditions):
            return f"the condition ID {rec['id']!r} is not a new C-NNN"
        if _blank(rec["text"]):
            return "the condition's text must not be blank"
        supports = rec["supports"]
        if not isinstance(supports, str) or supports not in self.entries:
            return f"{supports!r} is not a recorded entry; a condition supports a register entry"
        problem = register._source_problem(rec["source"])
        if problem:
            return problem
        if _blank(rec["recorded_by"]) or _blank(rec["date"]):
            return "recorded_by and date must not be blank"
        automated = register.is_automated(rec["recorded_by"])
        problem = register._automated_source_problem(rec["source"], automated)
        if problem:
            return problem
        ev = rec["evidence"]
        if not isinstance(ev, list) or not all(isinstance(e, str) for e in ev):
            return "the evidence is a list of evidence page IDs"
        try:
            evidence_pages.check_support_pages(case_dir, ev)
            register._check_supersede(rec["supersedes"], rec["reason"], rec["change_source"],
                                      categories={c: None for c in self.conditions},
                                      superseded_by=self.superseded_by, confirmed=self.confirmed(),
                                      category=None, automated=automated, refused=ConditionRefused)
        except (evidence_pages.EvidenceRefused, ConditionRefused) as exc:
            return str(exc)
        return None

    def mark_problem(self, rec: dict) -> str | None:
        problem = register._fields_problem(rec, _MARK_FIELDS)
        if problem:
            return problem
        if _blank(rec["name"]) or _blank(rec["question"]) or _blank(rec["answer"]) or _blank(rec["date"]):
            return "a mark's name, question, answer and date must not be blank"
        if register.is_automated(rec["name"]):
            return ("the mark names automated: an automated session may not mark a condition; "
                    "only a named person marks one")
        if rec["role"] != "proposer":
            return f"the role {rec['role']!r} is not proposer; only the proposer marks a condition"
        if rec["as"] not in MARKS:
            return f"the mark {rec['as']!r} is not confirmed or unsupported"
        ref = rec["ref"]
        if not isinstance(ref, str) or ref not in self.conditions:
            return f"{ref!r} is not a recorded condition"
        if ref in self.superseded_by:
            return f"{ref} is superseded by {self.superseded_by[ref]}; mark {self.superseded_by[ref]} instead"
        if rec["as"] == "confirmed" and not self.conditions[ref]["evidence"]:
            return (f"{ref} lists no evidence page; a condition is confirmed only with evidence; "
                    "record the condition again with its evidence, or mark it unsupported")
        return None

    def orphan_problem(self, ref: str) -> str | None:
        """Write time only (see the module docstring)."""
        supports = self.conditions[ref]["supports"]
        successor = self.entries[supports]["superseded_by"]
        if successor is None:
            return None
        return (f"{ref} is orphaned: the entry it supports, {supports}, is superseded by {successor}; "
                f"record the condition again against {successor} by superseding {ref}")

    def count(self, case_dir: Path, n: int, rec: dict) -> None:
        kind = rec.get("line")
        if kind == "condition":
            m = _CONDITION_ID.fullmatch(rec["id"]) if isinstance(rec.get("id"), str) else None
            if m:
                self.last_number = max(self.last_number, int(m.group(1)))
            problem = self.condition_problem(case_dir, rec)
        elif kind == "mark":
            problem = self.mark_problem(rec)
        else:
            problem = f"the line kind {kind!r} is not condition or mark"
        if problem:
            self.ignored.append(f"{paths.CONDITIONS} line {n}: {problem}; the line does not count")
            return
        if kind == "condition":
            self.conditions[rec["id"]] = rec
            if rec["supersedes"] is not None:
                self.superseded_by[rec["supersedes"]] = rec["id"]
        else:
            self.latest_mark[rec["ref"]] = rec


def _derive(case_dir: Path) -> _Conditions:
    try:
        state = _Conditions(register.entries(case_dir))
        records = chained_log.read(case_dir / paths.CONDITIONS)
    except (register.RegisterRefused, chained_log.LogRefused) as exc:
        raise ConditionRefused(str(exc)) from exc
    for n, rec in enumerate(records, 1):
        state.count(case_dir, n, rec)
    return state


def _append(case_dir: Path, record) -> dict:
    try:
        return chained_log.append(case_dir / paths.CONDITIONS, record)
    except chained_log.LogRefused as exc:
        raise ConditionRefused(str(exc)) from exc


def _recorded_by(case_dir: Path) -> str:
    """register.session_recorded_by, refused as ConditionRefused."""
    try:
        return register.session_recorded_by(case_dir)
    except case_files.CaseRefused as exc:
        raise ConditionRefused(str(exc)) from exc


def add_condition(case_dir, *, text, supports, evidence=(), source, supersedes=None, reason=None,
                  change_source=None) -> dict:
    """Record a new condition on a live register entry as the next C-NNN and return the stored line."""
    case_dir = Path(case_dir)
    recorded_by = _recorded_by(case_dir)
    ev = list(evidence) if isinstance(evidence, (list, tuple)) else evidence

    def build() -> dict:  # under the log's lock, so the number follows the lines on file
        state = _derive(case_dir)
        if isinstance(supports, str) and supports in state.entries:
            successor = state.entries[supports]["superseded_by"]
            if successor is not None:
                raise ConditionRefused(f"{supports} is superseded by {successor}; "
                                       f"record the condition against {successor}")
        rec = {"line": "condition", "id": f"C-{state.last_number + 1:03d}", "text": text, "supports": supports,
               "evidence": ev, "source": source, "recorded_by": recorded_by, "date": clock.today(),
               "supersedes": supersedes, "reason": reason, "change_source": change_source}
        if isinstance(ev, list):
            try:  # checked here too, so the refusal keeps the page's own exception as its cause
                evidence_pages.check_support_pages(case_dir, ev)
            except evidence_pages.EvidenceRefused as exc:
                raise ConditionRefused(str(exc)) from exc
        problem = state.condition_problem(case_dir, rec)
        if problem:
            raise ConditionRefused(problem)
        return rec
    return _append(case_dir, build)


def mark_condition(case_dir, condition_id, *, as_status, question, answer) -> dict:
    """Record the proposer's mark (`confirmed` or `unsupported`) on a live condition, with the answer
    verbatim. Needs a named person: an automated session is refused."""
    case_dir = Path(case_dir)
    try:
        name = case_files.current_name(case_dir)
    except case_files.CaseRefused as exc:
        raise ConditionRefused(f"{exc}; only a named person marks a condition") from exc
    if as_status not in MARKS:
        raise ConditionRefused(f"the mark {as_status!r} is not confirmed or unsupported")
    if _blank(question) or _blank(answer):
        raise ConditionRefused("the question and the person's answer must not be blank")
    rec = {"line": "mark", "ref": condition_id, "as": as_status, "question": question, "answer": answer,
           "role": "proposer", "name": name, "date": clock.today()}

    def build() -> dict:  # under the log's lock, so the check reads the lines on file
        state = _derive(case_dir)
        problem = state.mark_problem(rec) or state.orphan_problem(condition_id)
        if problem:
            raise ConditionRefused(problem)
        return rec
    return _append(case_dir, build)


def _status(state: _Conditions, condition_id: str) -> str:
    if condition_id in state.superseded_by:
        return "superseded"
    if condition_id in state.latest_mark:
        return state.latest_mark[condition_id]["as"]
    return "stated (coach)" if state.conditions[condition_id]["source"] == "coach" else "stated"


def _number(condition_id: str) -> int:
    return int(_CONDITION_ID.fullmatch(condition_id).group(1))


def conditions(case_dir) -> dict:
    """The counted conditions by ID, each with its derived `status`, `superseded_by` and `orphaned`
    (live, and the entry it supports is superseded). `supports` is returned as recorded."""
    state = _derive(Path(case_dir))
    out = {}
    for condition_id, rec in state.conditions.items():
        line = {k: v for k, v in rec.items() if k != "prev"}
        live = condition_id not in state.superseded_by
        out[condition_id] = dict(line, status=_status(state, condition_id),
                                 superseded_by=state.superseded_by.get(condition_id),
                                 orphaned=live and state.entries[rec["supports"]]["status"] == "superseded")
    return out


def live_conditions(case_dir) -> list:
    """The conditions not superseded, in ID order."""
    return sorted((c for c in conditions(case_dir).values() if c["status"] != "superseded"),
                  key=lambda c: _number(c["id"]))


def required_states(case_dir) -> dict:
    """Live condition ID -> `orphaned` when orphaned, else `unsupported` when its status is
    `unsupported`. Every other condition is absent."""
    out = {}
    for c in live_conditions(case_dir):
        holds = {"orphaned": c["orphaned"], "unsupported": c["status"] == "unsupported"}
        state = next((s for s in REQUIRED_STATES if holds[s]), None)  # the first that holds wins
        if state is not None:
            out[c["id"]] = state
    return out


def ignored_lines(case_dir) -> tuple:
    """One reason per line of conditions.jsonl that the readers do not count."""
    return tuple(_derive(Path(case_dir)).ignored)


# The start of check_strategy_files' refusal. It never says to run the judge again (ruling I-3).
BRIEF_NOT_WRITTEN = ("no judge brief was written and no judge run was counted; "
                     "a strategy file must be repaired first")


def check_strategy_files(case_dir) -> None:
    """Refuse when register.jsonl, conditions.jsonl or notes.jsonl cannot be read, or when any line
    of them is ignored: the judge would read a line code does not count (rulings I-3, N-10).
    `bc.py brief` calls this before judge_brief.write_brief counts a run, so a refusal spends no
    run. It lives here, not in judge_brief, to keep the strategy modules out of the fail-closed
    hook's import closure (ruling PF-12)."""
    case_dir = Path(case_dir)
    try:
        ignored = register.ignored_lines(case_dir) + ignored_lines(case_dir)
    except (register.RegisterRefused, ConditionRefused) as exc:
        raise ConditionRefused(f"{BRIEF_NOT_WRITTEN}: {exc}") from exc
    if ignored:
        raise ConditionRefused(f"{BRIEF_NOT_WRITTEN}: {'; '.join(ignored)}")
