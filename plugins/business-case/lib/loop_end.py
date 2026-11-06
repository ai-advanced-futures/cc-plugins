"""Loop end: each item's state, the loop status and the session budget, derived from the files.

Spec §4 steps 7 and 8: "Code, not the model, decides the loop is done." Nothing here is stored.
An item is met only in the latest judge report, while that report is current; the ledger's coach
class never makes an item met. accept and waive count toward loop end; fix, approve_estimate and
reject_estimate do not. When a finding or proposal has several valid answers, the latest one in
decisions.jsonl counts. An estimate's (item, page) pair and an exclusion's figure may have several
proposals: the latest valid answer to any of them decides it (_latest_by_subject). A coach copy
never ends the loop (ADR-006).

After a rubric move (plan 3 spec §7), an item decision counts only while the met-test ID it answered
equals the item's met-test ID in today's rubric copy (MET_TEST_KINDS); one that does not is listed as
"needs another look" and never deleted, until a decision on today's test answers the same finding or
proposal. An answer to a proposal counts only while the proposal does. Estimate and exclusion
approvals are not under this rule, and an estimate proposal they answered is never listed.

A finding is decided only by its own latest answer (spec §4 step 8, ruling FR-I1). An accept or a
waive on one finding says nothing about the item's other findings. The one item-level decision is a
waive of a propose_not_relevant proposal: it decides every finding on that item. A finding's ID does
not hold its item (ADR-008), so the judge may file one finding under another item in a later report.
The answer still decides the finding, but it closes only the item the answer itself names (ruling
I-1); the status names such an item, the finding and the item the answer was for, so the funder
answers the finding again for the open item. A whole-plan finding has no item: its answer names none and closes no item.

The strategy files give the status its absent categories and orphaned conditions. A strategy file
that cannot be read, and each line its reader ignores, is a named reason; it never makes the loop
raise.

Nothing read is trusted as written. Every decision record is re-checked with decision_record's
own write-time rules, and a record that fails counts as no answer. A saved report is not a judge
input, so an edit to it would not make it stale. So every saved report is read once, through one
check: it counts as the judge's only when it is marked "written_by": "judge", its receipt verifies
and it equals the report the judge's reply yields by save_report's own checks, current or stale
(rulings FR-I2, FR-I2b). That equality covers its brief and manifest, which the reply's brief fixes
(ruling S-11). Only a counted report's findings are ever used. A met on an estimated page is also
re-checked against the estimate approvals.
"""
from __future__ import annotations

import json
import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from lib import (
    case_files,
    chained_log,
    conditions,
    decision_record,
    digest,
    evidence,
    figures,
    finance,
    judge_receipt,
    judge_report,
    paths,
    register,
    rubric,
)

ItemState = Literal["met", "accepted_risk", "waived", "not_relevant_proposed", "estimate_proposed",
                    "fix_requested", "open"]

# When an item matches several states, the first in this order wins.
STATE_PRECEDENCE = ("met", "accepted_risk", "waived", "not_relevant_proposed", "estimate_proposed",
                    "fix_requested", "open")
CLOSING_STATES = frozenset({"met", "accepted_risk", "waived"})

# §4 step 7: the answers to a finding that decide it. fix does not.
DECIDING_KINDS = frozenset({"accept", "waive"})
# The item state a finding's deciding answer gives its item, once every finding on the item has one.
_ITEM_STATE_OF = {"accept": "accepted_risk", "waive": "waived"}
_PROPOSED_STATE = {"propose_not_relevant": "not_relevant_proposed", "propose_estimate": "estimate_proposed"}
# Plan 3 spec §7 "Decisions after a move": the item decisions that answer the item's met test. One
# counts only while the met-test ID it answered equals the item's current one. The estimate pair
# (approve_estimate, reject_estimate) and the exclusion pair approve evidence or an exclusion for a
# figure, not an answer to a met test, so they survive a move.
MET_TEST_KINDS = frozenset({"fix", "accept", "waive", "propose_not_relevant", "propose_estimate",
                            "reject_not_relevant"})
ESTIMATE_ANSWERS = frozenset({"approve_estimate", "reject_estimate"})
ANOTHER_LOOK = "decision {id} answered {old}; {item} now has {new}: needs another look"
# Spec 0.4.0 item 6: a file the latest recorded funding decision cites changed since the decision.
FUNDING_FILE_CHANGED = ("funding decision {id} no longer matches {path}, which changed since the decision; "
                        "restore the file, or run the independent review again and record a new funding decision")
FUNDING_CASE_CHANGED = "the case changed since funding decision {id}; the funder decides again"


@dataclass(frozen=True)
class LoopStatus:
    """The loop's state. The sequences are tuples, so a frozen status cannot change in place.
    absent_categories and orphaned_conditions are None, unknown, while a strategy file cannot be read.
    funding_changes names each file the latest recorded funding decision cites that changed since it;
    it is never a reason or a repair and never changes `done`. It has no default, so a status built
    without it is refused rather than read as "nothing changed"."""
    done: bool
    stopped_by_budget: bool
    reasons: tuple[str, ...]
    open_items: tuple[str, ...]
    undecided_findings: tuple[str, ...]
    stale_files: tuple[str, ...]
    absent_categories: tuple[str, ...] | None
    orphaned_conditions: tuple[str, ...] | None
    funding_changes: tuple[str, ...]


@dataclass(frozen=True)
class _Book:
    """The decision record as the loop counts it."""
    counted: dict      # decision ID -> (record, end byte offset): passed decision_record.check_recorded
    answers: dict      # (subject type, ref) -> (record, end): the latest valid counted answer
    proposals: dict    # item ID -> record: the latest valid counted proposer decision
    approvals: dict    # (item ID, evidence ID) -> (end offset, ID) of the pair's latest valid answer, an approve_estimate
    rejected: frozenset  # (item ID, evidence ID) pairs whose latest valid answer is reject_estimate; disjoint from approvals
    not_counted: tuple  # reasons, one per record that failed the re-check
    waived_items: frozenset  # items whose not-relevant proposal the funder waived: the one item-level decision
    exclusions: dict   # figure ID -> ("approved" | "rejected" | "pending", decision ID): the latest valid answer
                       # to any of its valid propose_exclusions (the latest proposal's ID while none is answered)
    another_look: tuple  # reasons, one per valid item decision that answered a met test the item no longer has
                         # and that no counted decision on today's test has answered again
    estimate_proposals: frozenset = frozenset()  # (item ID, EV-NNN) pairs some valid propose_estimate cites


def _subject(record: dict) -> tuple:
    subject = record.get("subject")
    if not isinstance(subject, dict):
        return (None, None)
    return (subject.get("type"), subject.get("ref"))


@dataclass(frozen=True)
class _Reports:
    """The saved reports as the loop reads them."""
    latest: tuple | None    # (relpath, report) of the newest saved report, when it parses
    latest_unreadable: bool  # the newest saved report exists but does not parse
    reasons: tuple          # one per saved report that cannot be read
    judge_problem: object   # None, or why the latest report, marked written_by judge, does not count
    by_judge: bool          # the latest report counts as the judge's
    findings: list          # the latest report's findings when it counts; otherwise empty


def _reports(case_dir: Path) -> _Reports:
    """Read every saved report once; only the newest, the one used, goes through _judge_problem. One that cannot be read is a named
    reason and holds no findings; it never makes the loop raise. Only a report that counts gives
    findings, for any purpose."""
    latest, unreadable, reasons = None, False, []
    judge_problem, by_judge, latest_findings = None, False, []
    for n, rel in enumerate(judge_report.saved_reports(case_dir)):
        try:
            report = json.loads((case_dir / rel).read_text(encoding="utf-8"))
            if not isinstance(report, dict):
                raise ValueError("it is not a JSON object")
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            reasons.append(f"{rel} cannot be read ({exc}); it holds no findings")
            unreadable = unreadable or n == 0
            continue
        if n == 0:  # only the newest report is used, so only it is re-derived
            judged = _judge_problem(case_dir, rel, report) if report.get("written_by") == "judge" else None
            counts = judged is None and report.get("written_by") == "judge"
            latest, judge_problem, by_judge = (rel, report), judged, counts
            latest_findings = report.get("findings") if counts and isinstance(report.get("findings"), list) else []
    return _Reports(latest, unreadable, tuple(reasons), judge_problem, by_judge, latest_findings)


def _judge_problem(case_dir: Path, rel: str, report: dict):
    """None when a report marked written_by judge equals what the judge's receipted reply yields
    now (judge_report.rederive); otherwise why not. Current or stale alike. The rederived brief and
    manifest come from the code-written brief, so a report whose manifest is not its brief's never
    counts (ruling S-11)."""
    try:
        rebuilt = judge_report.rederive(case_dir, judge_report.report_number(rel))
    except (judge_receipt.ReceiptRefused, judge_report.ReplyRefused) as exc:
        return str(exc)
    differ = [key for key in rebuilt if report.get(key) != rebuilt[key]]
    if differ:
        return f"its {', '.join(differ)} differ from what the judge's reply yields"
    return None


@dataclass(frozen=True)
class FinanceAnswers:
    """The funder's answers the finances read (plan 3, Task 8)."""
    approved: frozenset   # (item ID, EV-NNN) pairs: approved_pages' rule
    rejected: frozenset   # (item ID, EV-NNN) pairs whose latest valid answer is reject_estimate; disjoint from approved
    exclusions: dict      # figure ID -> ("approved" | "rejected" | "pending", decision ID), as _Book.exclusions
    proposed: frozenset = frozenset()  # (item ID, EV-NNN) pairs a valid propose_estimate cites (Task 17)


def _latest_by_subject(counted: dict, valid: set, answers: dict, kind: str, subjects_of) -> dict:
    """The one per-subject rule (Task 8 fix round 1 ruling): subject -> (latest valid proposal's
    ID, the latest valid answer to ANY valid proposal of `kind` on that subject, or None). A subject
    is an estimate's (item ID, EV-NNN) pair or an exclusion's figure ID. A new proposal with no
    answer yet does not reset the subject; `answers` holds each proposal's latest valid answer."""
    out = {}
    for rid, (record, _) in counted.items():  # file order
        if rid not in valid or record["kind"] != kind:
            continue
        answer = answers.get(("proposal", rid))
        for subject in subjects_of(record):
            latest = out.get(subject, (None, None))[1]
            if answer is not None and (latest is None or answer[1] > latest[1]):
                latest = answer
            out[subject] = (rid, latest)
    return out


def _estimate_pairs(record: dict) -> list:
    """S-8: an estimate proposal decides its own item on each page it cites, and nothing else."""
    return [(record.get("item_id"), m.group(1)) for rel in record.get("cited", {})
            for m in [decision_record.EVIDENCE_CITE.match(rel)] if m]


def _current_met_tests(case_dir: Path) -> dict:
    """Item ID -> its met-test ID in today's rubric copy; empty when the copy cannot be read (every
    reader of the item states then refuses on the copy itself, through _applicable)."""
    try:
        rub = rubric.load_rubric(case_dir / paths.RUBRIC_COPY)
    except rubric.RubricError:
        return {}
    return {i["id"]: i["met_test"]["id"] for i in rub["items"]}


def answered_met_test(record: dict) -> str:
    """The met-test ID an item decision answered. A decision written before 0.3.0 has none: it
    answered the 1.0.0 test, `<item>.M1`, because 1.0.0 is the only version those cases could use."""
    return record["met_test_id"] if "met_test_id" in record else f"{record.get('item_id')}.M1"


def _answered_an_old_test(record: dict, current: dict) -> str | None:
    """The "needs another look" reason when `record` is an item decision whose met test the item no
    longer has; otherwise None."""
    item = record.get("item_id")
    if item is None or record.get("kind") not in MET_TEST_KINDS or item not in current:
        return None
    old = answered_met_test(record)
    if old == current[item]:
        return None
    return ANOTHER_LOOK.format(id=record.get("id"), old=old, item=item, new=current[item])


def _book(case_dir: Path, upto: int | None = None, figures_upto: int | None = None) -> _Book:
    """The decision record as counted. A record whose line ends after `upto` bytes is left out
    before anything is counted, so a reader sees the file as it was at that length; None reads
    the whole file. The records are checked against figures.jsonl cut at `figures_upto` bytes."""
    counted, not_counted = {}, []
    records = decision_record.read_records(case_dir)
    if upto is not None:
        records = [(record, end) for record, end in records if end <= upto]
    reads = decision_record.Reads(case_dir, [record for record, _ in records], figures_upto)  # each file read once
    for record, end in records:
        rid = record.get("id")
        try:
            decision_record.check_recorded(case_dir, record, reads)  # the write-time rules, ID format included
            if rid in counted:
                raise decision_record.DecisionRefused("its ID is used by an earlier record")
        except decision_record.DecisionRefused as exc:
            not_counted.append(f"decision {rid!r} is not counted: {exc}" if not isinstance(rid, str)
                               else f"decision {rid} is not counted: {exc}")
            continue
        counted[rid] = (record, end)

    valid = {rid for rid, (record, _) in counted.items() if decision_record.is_valid(record, case_dir, reads)}
    # A valid item decision on a met test the item no longer has stays valid (an estimate approval
    # may still answer its proposal), but it gives no item state and decides no finding.
    current = _current_met_tests(case_dir)
    stale = {rid: why for rid, (record, _) in counted.items() if rid in valid  # file order
             for why in [_answered_an_old_test(record, current)] if why is not None}
    answers, proposals = {}, {}
    for rid, (record, end) in counted.items():  # file order: a later answer overrides an earlier one
        if rid not in valid or rid in stale:
            continue
        kind, key = record["kind"], _subject(record)
        if kind in _PROPOSED_STATE:
            proposals[record.get("item_id")] = record
        elif key[0] == "finding":
            answers[key] = (record, end)
        elif key[0] == "proposal" and key[1] in valid:  # M-5: the proposal it answers is still valid
            # Fix round 1 ruling: an answer counts only while the proposal it answers counts. The
            # estimate pair is the exception: an approval survives a move (spec §7).
            if key[1] in stale and kind not in ESTIMATE_ANSWERS:
                continue
            answers[key] = (record, end)

    estimates = _latest_by_subject(counted, valid, answers, "propose_estimate", _estimate_pairs)
    approvals = {pair: (a[1], a[0]["id"]) for pair, (_, a) in estimates.items()
                 if a is not None and a[0]["kind"] == "approve_estimate"}
    rejected = frozenset(pair for pair, (_, a) in estimates.items()
                         if a is not None and a[0]["kind"] == "reject_estimate")
    waived = frozenset(d.get("item_id") for (subject_type, _), (d, _) in answers.items()
                       if subject_type == "proposal" and d["kind"] == "waive")
    # propose_exclusion is about a figure, not an item, so it never enters `proposals`.
    exclusions = {}
    for fig_id, (pid, a) in _latest_by_subject(counted, valid, answers, "propose_exclusion",
                                                lambda r: [r["subject"]["ref"]]).items():
        exclusions[fig_id] = (("pending", pid) if a is None
                              else ("approved" if a[0]["kind"] == "approve_exclusion" else "rejected", a[0]["id"]))
    # Fix round 1 ruling: a stale decision is listed only while no counted decision on today's test
    # is about the same subject (a re-answer of the finding or proposal, or a new proposal on the
    # item), and never when it is an estimate proposal whose answer survives the move.
    today = {_subject(counted[rid][0]) for rid in valid if rid not in stale}
    answered_estimates = {key[1] for key, (record, _) in answers.items()
                          if key[0] == "proposal" and record["kind"] in ESTIMATE_ANSWERS}
    another_look = tuple(why for rid, why in stale.items()
                         if _subject(counted[rid][0]) not in today and rid not in answered_estimates)
    return _Book(counted, answers, proposals, approvals, rejected, tuple(not_counted), waived, exclusions,
                 another_look, frozenset(estimates))


def _well_formed_funding(record) -> bool:
    """A funding line the reader can use: a string ID, a funding kind and a non-empty cited mapping.
    The lines are not re-checked (fix round 1), so a hand-written one may hold any type; any other
    line is skipped (fix round 2)."""
    return (isinstance(record, dict) and isinstance(record.get("id"), str)
            and isinstance(record.get("kind"), str) and record["kind"] in decision_record.FUNDING_KINDS
            and isinstance(record.get("cited"), dict) and bool(record["cited"]))


def _inside_case(rel) -> bool:
    """A plain relative path that stays in the case folder; any other is never read."""
    return (isinstance(rel, str) and rel != "" and not rel.startswith("/")
            and posixpath.normpath(rel).split("/")[0] != "..")


def _funding_changes(case_dir: Path):
    """(ID, changed paths) of the latest well-formed funding line, or None; see funding_changes."""
    latest = None
    for record, _ in decision_record.read_records(case_dir):  # file order: the last one wins
        if _well_formed_funding(record):
            latest = record
    if latest is None:
        return None
    changed = []
    for rel, recorded in latest["cited"].items():
        try:
            same = _inside_case(rel) and digest.file_digest(case_dir / rel) == recorded
        except (OSError, ValueError):  # missing, unreadable, or a path no file can have (a NUL byte)
            same = False
        if not same:
            changed.append(rel)
    return (latest["id"], changed) if changed else None


def funding_changes(case_dir) -> tuple | None:
    """Spec 0.4.0 item 6: the latest well-formed funding decision (fund, do_not_fund or defer)
    recorded in decisions.jsonl, counted or not, and each path it cites whose digest changed, whose
    file is missing or cannot be digested, or that is absolute or leaves the case folder (never
    read), in cited order; None when that decision is still valid or there
    is none. Counted or not (fix round 1 ruling): a deleted cited file stops the decision counting,
    and it must still be named. A newer valid funding decision clears an older one's changes.
    Never raises for a funding line or a cited path."""
    return _funding_changes(Path(case_dir))


def funding_lines(found) -> tuple:
    """One line per changed path of funding_changes' result: business-case.md reads that the funder
    decides again; any other file, that it is restored or reviewed and funded again."""
    if found is None:
        return ()
    rid, changed = found
    return tuple(FUNDING_CASE_CHANGED.format(id=rid) if rel == paths.CASE_DOC
                 else FUNDING_FILE_CHANGED.format(id=rid, path=rel) for rel in changed)


def approved_pages(case_dir) -> set:
    """(item ID, evidence ID) pairs a valid propose_estimate cites, whose latest valid answer across
    all their valid proposals is approve_estimate (Task 8 fix round 1). An approval covers only the
    item its proposal is about (ruling S-8)."""
    case_dir = Path(case_dir)
    return set(_book(case_dir).approvals)


def finance_answers(case_dir, upto: int | None = None, figures_upto: int | None = None) -> FinanceAnswers:
    """The estimate and exclusion answers the finances read, from decisions.jsonl cut at `upto`
    bytes, checked against figures.jsonl cut at `figures_upto` bytes (None: the whole file)."""
    book = _book(Path(case_dir), upto, figures_upto)
    return FinanceAnswers(frozenset(book.approvals), book.rejected, dict(book.exclusions), book.estimate_proposals)


def _applicable(case_dir: Path) -> list:
    """Applicable item IDs in rubric order. The market comes from scope.json, the judge's input, as
    in `bc.py items` (final review M-3)."""
    return [i["id"] for i in case_files.applicable_items(case_dir)]


def _met_problems(case_dir: Path, iid: str, entry: dict, approvals: dict, report_read: int) -> list:
    """Why the code refuses a met the report records; empty when it holds. `report_read` is how many
    bytes of decisions.jsonl the report's judge read. Only a counted report reaches here, and it
    passed save_report's checks on today's files: its met test, its pages and their items are
    already checked. What is left is the estimate approval, which is a later decision."""
    unapproved, late = [], []
    for ev_id in entry["evidence"]:
        if evidence.read_page(case_dir, ev_id).get("grade") != "estimated":
            continue
        approved_at = approvals.get((iid, ev_id))
        if approved_at is None:
            unapproved.append(ev_id)
        elif approved_at[0] > report_read:
            late.append(f"{ev_id} (by {approved_at[1]})")
    problems = []
    if unapproved:
        problems.append(f"it cites the estimated page(s) {', '.join(unapproved)} with no approve_estimate "
                        f"for {iid}: the proposer proposes the estimate, the funder approves it, "
                        "then the judge runs again")
    if late:
        problems.append(f"the estimated page(s) {', '.join(late)} were approved after this report; "
                        "an approved estimate goes back to the judge: run the judge again")
    return problems


def _refused_mets(case_dir: Path, latest, applicable: list, book: _Book) -> dict:
    """item ID -> problems, for each item a usable report marks met. A met on an item code computes
    cites finance.json, which is no page and needs no approval: save_report's checks, which the
    counted report passed, already held code's result to its met test (Task 15). The pages it cites
    beside finance.json are checked as any met's pages."""
    report = latest[1]
    read = report.get("manifest", {}).get(paths.DECISIONS, {}).get("bytes", 0)
    computed = rubric.computed_item_ids(rubric.load_rubric(case_dir / paths.RUBRIC_COPY))
    out = {}
    for iid, entry in report.get("items", {}).items():
        if iid in applicable and isinstance(entry, dict) and entry.get("status") == "met":
            if iid in computed:
                entry = dict(entry, evidence=[e for e in entry.get("evidence") or [] if e != paths.FINANCE])
            out[iid] = _met_problems(case_dir, iid, entry, book.approvals, read)
    return out


def _findings_by_item(findings) -> dict:
    """item ID -> the IDs of its findings, in report order."""
    out = {}
    for f in findings if isinstance(findings, list) else []:
        if isinstance(f, dict):
            out.setdefault(f.get("item_id"), []).append(f.get("id"))
    return out


def _states(applicable: list, mets: dict, book: _Book, findings) -> dict:
    """`findings` are the findings that answers may close items through: those of the latest report."""
    found = {iid: set() for iid in applicable}

    def add(iid, state):
        if iid in found:
            found[iid].add(state)

    for iid, problems in mets.items():
        if not problems:
            add(iid, "met")
    for iid in book.waived_items:
        add(iid, "waived")
    by_item = _findings_by_item(findings)
    for iid, ids in by_item.items():
        # Ruling I-1: an answer counts toward closing an item only when the answer names that item.
        answers = [book.answers.get(("finding", f)) for f in ids]
        kinds = [a[0]["kind"] if a is not None and a[0].get("item_id") == iid else None for a in answers]
        if "fix" in kinds:
            add(iid, "fix_requested")
        if all(k in DECIDING_KINDS for k in kinds):  # every finding on the item has its own deciding answer
            for k in kinds:
                add(iid, _ITEM_STATE_OF[k])
    for iid, proposal in book.proposals.items():
        if ("proposal", proposal["id"]) not in book.answers:
            add(iid, _PROPOSED_STATE[proposal["kind"]])
    return {iid: next((s for s in STATE_PRECEDENCE if s in found[iid]), "open") for iid in applicable}


@dataclass(frozen=True)
class _View:
    applicable: list
    book: _Book
    reports: _Reports
    current: bool
    stale: list
    judge_problem: object  # None, or why a report marked written_by judge does not count as the judge's
    by_judge: bool         # the latest report counts as the judge's
    mets: dict
    states: dict


def _read(case_dir: Path) -> _View:
    applicable = _applicable(case_dir)
    reports = _reports(case_dir)
    book = _book(case_dir)
    latest = reports.latest
    current, stale = False, []
    if latest is not None:
        current, stale = digest.is_current(latest[1].get("manifest", {}), case_dir)
    usable = reports.by_judge and current
    mets = _refused_mets(case_dir, latest, applicable, book) if usable else {}
    # M-4: only the findings of a report that counts as the judge's let answers close an item.
    return _View(applicable, book, reports, current, stale, reports.judge_problem,
                 reports.by_judge, mets, _states(applicable, mets, book, reports.findings))


def item_states(case_dir) -> dict:
    """Applicable item ID -> its state. Derived, never stored."""
    return _read(Path(case_dir)).states


def _decided(finding: dict, book: _Book) -> bool:
    """Ruling FR-I1: a finding is decided by its own latest answer, accept or waive; a fix leaves it
    undecided (ruling T10-fix-wins). A finding with no answer of its own is decided only when the
    funder waived its item's not-relevant proposal. An accept or waive on another finding of the
    same item decides nothing here."""
    answer = book.answers.get(("finding", finding.get("id")))
    if answer is not None:
        return answer[0]["kind"] in DECIDING_KINDS
    return finding.get("item_id") in book.waived_items


def _carried(iid: str, findings, book: _Book) -> list:
    """(finding ID, other item) for each finding the report files under `iid` whose deciding answer
    names another item. The finding is decided, but the answer does not close `iid` (ruling I-1)."""
    out = []
    for f in findings:
        if not isinstance(f, dict) or f.get("item_id") != iid:
            continue
        answer = book.answers.get(("finding", f.get("id")))
        if answer is not None and answer[0]["kind"] in DECIDING_KINDS and answer[0].get("item_id") != iid:
            out.append((f.get("id"), answer[0].get("item_id")))
    return out


def finding_is_decided(finding: dict, case_dir) -> bool:
    """True when the finding's latest counted answer is accept or waive, or when it has no answer
    and the funder waived its item's not-relevant proposal. A fix never decides a finding. The
    records are read and re-checked from case_dir."""
    case_dir = Path(case_dir)
    return _decided(finding, _book(case_dir))


def loop_status(case_dir) -> LoopStatus:
    """Done only when all five hold: a latest report exists; the judge wrote it; it is current;
    every applicable item is met, accepted_risk or waived; every finding in it is decided."""
    return status_and_states(case_dir)[0]


def status_and_states(case_dir) -> tuple:
    """(loop_status, item_states) from one read of the case's files."""
    case_dir = Path(case_dir)
    view = _read(case_dir)
    return _status(case_dir, view), view.states


@dataclass(frozen=True)
class _StrategyGaps:
    absent: tuple | None    # category keys with no stated or confirmed entry; None when a file cannot be read
    orphaned: tuple | None  # live conditions whose entry is superseded; None when a file cannot be read
    reasons: tuple    # a file that cannot be read, or one per ignored line
    broken: bool      # a strategy file cannot be read


def _strategy_gaps(case_dir: Path) -> _StrategyGaps:
    """The register's gaps for the status. Each file is read in turn, so a refusal names the file
    that cannot be read; the cause is the reader's own message. Never raises for a strategy file."""
    reads = ((paths.REGISTER, register.entries), (paths.NOTES, register.notes),
             (paths.CONDITIONS, conditions.conditions))
    for name, read in reads:
        try:
            read(case_dir)
        except (register.RegisterRefused, conditions.ConditionRefused, chained_log.LogRefused) as exc:
            cause = str(exc)
            cause = cause[len(name) + 2:] if cause.startswith(f"{name}: ") else cause
            return _StrategyGaps(None, None, (f"{name} cannot be read: {cause}; repair the file before the next brief",),
                                 True)
    try:
        absent = register.absent_categories(case_dir)
        orphaned = tuple(c["id"] for c in conditions.live_conditions(case_dir) if c["orphaned"])
        ignored = register.ignored_lines(case_dir) + conditions.ignored_lines(case_dir)
    except (register.RegisterRefused, conditions.ConditionRefused, chained_log.LogRefused) as exc:
        return _StrategyGaps(None, None, (f"a strategy file cannot be read: {exc}; repair the file before the next brief",),
                             True)
    # M-2: an ignored line is repaired like a broken file, and its reason says so (build.md step 9).
    return _StrategyGaps(absent, orphaned, tuple(f"{r}; repair the file before the next brief" for r in ignored),
                         False)


def file_repairs(case_dir: Path, gaps: "_StrategyGaps | None" = None) -> tuple:
    """The file-repair reasons that need no saved report: each strategy file that cannot be read or
    holds an ignored line, each such line of figures.jsonl, and a case.json with no offering name.
    The one source for status's file-repair lines and the handoff's problems (Task 18 fix round 3).
    Never raises."""
    gaps = _strategy_gaps(case_dir) if gaps is None else gaps
    out = list(gaps.reasons) + list(figures_reasons(case_dir))
    try:
        case_files.offering(case_dir)
    except case_files.CaseRefused as exc:
        out.append(f"{exc}; {judge_report.REPAIR_FILE}")
    if not out:  # a file the numbers read, when nothing above already names a broken one
        try:
            finance.compute(case_dir)
        except finance.FinanceRefused as exc:
            out.append(f"{exc}; {judge_report.REPAIR_FILE}")
    return tuple(out)


def repairs(case_dir) -> tuple:
    """Every reason status gives that asks for a file to be repaired, in status's order: the file
    repairs, then the saved report's lines that a broken file causes. Raises what status_and_states
    raises when the loop cannot be read."""
    case_dir = Path(case_dir)
    view = _read(case_dir)
    gaps = _strategy_gaps(case_dir)
    return file_repairs(case_dir, gaps) + tuple(line for line, repair in _report_lines(case_dir, view, gaps) if repair)


def _report_lines(case_dir: Path, view: "_View", gaps: "_StrategyGaps") -> list:
    """The latest report's status lines, each with True when it asks for a file repair. A broken
    strategy file or figures.jsonl, or a report problem a broken file causes, asks for the repair:
    no new run can pass until the file is whole."""
    latest, current, stale = view.reports.latest, view.current, view.stale
    broken = gaps.broken or bool(figures_reasons(case_dir)) or judge_report.needs_repair(view.judge_problem)
    repair = judge_report.REPAIR_FILE
    out = []
    if latest is None and not view.reports.latest_unreadable:
        out.append(("no judge report is saved; write a brief and run the judge", False))
    elif latest is not None:
        rel, report = latest
        if report.get("written_by") != "judge":
            out.append((f"{rel} is a coach copy, and a coach copy never ends the loop; "
                        "run the judge again with a new brief", False))
        elif view.judge_problem is not None:
            out.append((f"{rel} does not count as the judge's report: {view.judge_problem}; "
                        + (repair if broken else judge_report.RUN_JUDGE_AGAIN), broken))
        if not current:
            out.append((f"{rel} is not current: changed since the judge read it: {', '.join(stale)}; "
                        + (repair if broken else "run the judge again"), broken))
    return out


def figures_reasons(case_dir: Path) -> tuple:
    """One reason per line of figures.jsonl the readers do not count, or one for a file that cannot
    be read, each naming the file and line with the repair remedy. Read whether or not a report is
    saved (Review Focus 4). Never raises."""
    try:
        ignored = figures.ignored_lines(case_dir)
    except figures.FigureRefused as exc:
        ignored = (str(exc),)
    return tuple(f"{r}; {judge_report.REPAIR_FILE}" for r in ignored)


def _marked_not_met(entry) -> bool:
    return isinstance(entry, dict) and entry.get("status") == "not_met"


def _status(case_dir: Path, view: _View) -> LoopStatus:
    applicable, book, latest, current, stale = view.applicable, view.book, view.reports.latest, view.current, view.stale
    mets, states = view.mets, view.states

    gaps = _strategy_gaps(case_dir)
    # A broken strategy file, or a broken file the numbers come from, is repaired first: no judge run
    # can pass until it is (ruling I-3; review I9). file_repairs and _report_lines are also what the
    # handoff names (repairs), so the two never disagree.
    reasons = (list(file_repairs(case_dir, gaps)) + list(view.reports.reasons)
               + list(book.not_counted) + list(book.another_look))
    by_judge = view.by_judge
    reasons.extend(line for line, _ in _report_lines(case_dir, view, gaps))
    usable = latest is not None and by_judge and current
    marked = latest[1].get("items") if latest else None
    marked = marked if isinstance(marked, dict) else {}

    open_items = [iid for iid in applicable if states[iid] not in CLOSING_STATES]
    for iid in open_items:
        if mets.get(iid):
            reasons.append(f"item {iid} is {states[iid]}: the latest report marks it met, but the code "
                           f"refuses that: {'; '.join(mets[iid])}")
        elif not usable and states[iid] == "open" and not _marked_not_met(marked.get(iid)):
            continue  # the report-level line above already names the cause
        elif carried := _carried(iid, view.reports.findings, book):
            reasons.extend(f"item {iid} is {states[iid]}: its finding {fid} was decided for item {other}; "
                           f"item {iid} needs its own answer to {fid}" for fid, other in carried)
        else:
            reasons.append(f"item {iid} is {states[iid]}: not met, accepted or waived")

    undecided = []
    for f in view.reports.findings:
        if not _decided(f, book):
            undecided.append(f.get("id"))
            answer = book.answers.get(("finding", f.get("id")))
            why = "its latest answer is fix; after the change, answer it again" if answer else \
                "it needs an accept or a waive"
            target = f.get("target") if isinstance(f.get("target"), dict) else {}
            on = f.get("item_id") if f.get("item_id") is not None else f"{target.get('kind')} {target.get('ref')}"
            reasons.append(f"finding {f.get('id')} on {on} is not decided: {why}")

    done = latest is not None and by_judge and current and not open_items and not undecided

    stopped = False
    if not done:
        try:
            session = case_files.current_session(case_dir)
        except case_files.CaseRefused:  # no session yet: nothing is spent
            session = None
        budget = case_files.read_meta(case_dir)["session_budget"]
        if session is not None and session.get("judge_runs", 0) >= budget:
            stopped = True
            reasons.append(f"session {session.get('id')} has used its {budget} judge runs, "
                           "the session budget; start a new session to go on")

    return LoopStatus(done=done, stopped_by_budget=stopped, reasons=tuple(reasons), open_items=tuple(open_items),
                      undecided_findings=tuple(undecided), stale_files=tuple(stale),
                      absent_categories=gaps.absent, orphaned_conditions=gaps.orphaned,
                      funding_changes=funding_lines(_funding_changes(case_dir)))
