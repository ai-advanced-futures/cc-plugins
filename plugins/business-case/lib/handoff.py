"""The handoff: business-case-handoff.json, what the person and a later session read when a run ends.

Spec §10: an automated run records no decision and ends with a handoff naming the open items, the
register categories with no stated or confirmed entry, and the orphaned conditions.
Every value is derived from the case's files through loop_end; nothing here is judged.

The handoff is the run's reporting exit (Task 18 fix rounds 2 and 3): it never refuses on case
content. `problems` holds exactly the reasons `status` gives that ask for a file to be repaired
(loop_end.repairs), so the two never disagree, then each review contradiction (`contradictions`),
then a latest independent review that read no finance.json (`review_without_finance`), then a
funding decision that no longer matches the files it cites (`loop_end.funding_changes`), then each
refused figure proposal, or the refusal of the whole run, and the amounts the run left uncovered
(`refused_proposals`); needs_human is true while any is open. When the
loop's status itself cannot be read, open_items, absent_categories and orphaned_conditions are null
(unknown, never an empty list that claims nothing is open), and the cause is named in `problems`.
"""
from __future__ import annotations

import json
from pathlib import Path

from lib import (
    case_doc,
    case_files,
    chained_log,
    clock,
    conditions,
    decision_record,
    evidence,
    figures,
    finance,
    judge_report,
    ledger,
    loop_end,
    paths,
    plugin_map,
    register,
    rubric,
)

SOURCE_PLUGIN = "business-case"
SCHEMA_VERSION = "2"
MODES = ("automated", "interactive")
# The map's owner value, in the words a person reads. An analyst's name passes through unchanged.
OWNER_TEXT = {"coach": "coach", "finance-engine": "the finance engine"}


def evidence_needed(open_items) -> list:
    """Each item the loop still holds open, with its owner (spec 5.9, rulings C13 and 2026-11-02): the
    same set and order as `open_items`. An item the map does not list is the coach's."""
    m = plugin_map.load()
    items = m.get("items", {})
    owners = [(iid, items.get(iid, {}).get("owner", "coach")) for iid in open_items]
    return [{"item_id": iid, "owner": OWNER_TEXT.get(o, o)} for iid, o in owners]


def write_handoff(case_dir, *, mode: str) -> Path:
    """Write business-case-handoff.json from the loop's current status and return its path.

    status is "done" when the loop is done and `problems` is empty, "stopped_by_budget" when the
    session has used its judge runs, and "open" otherwise. `problems` names a file to repair, a
    review contradiction, a latest independent review that read no finance.json, a funding decision
    that no longer matches the files it cites, a refused figure
    proposal or the refusal of the whole run, and the amounts the latest figure run left uncovered.
    needs_human is true unless the status is "done". absent_categories and orphaned_conditions are
    null while a strategy file cannot be read."""
    if mode not in MODES:
        raise ValueError(f"mode {mode!r} is not one of {', '.join(MODES)}")
    case_dir = Path(case_dir)
    # problems are status's own file-repair reasons (loop_end.repairs), never a list of our own
    # (Task 18 fix round 3). When the loop cannot be read, its file repairs and the cause.
    try:
        status, states = loop_end.status_and_states(case_dir)
        problems = list(loop_end.repairs(case_dir))
    except _content_errors() as exc:
        status, states = None, {}
        problems = list(loop_end.file_repairs(case_dir))
        cause = str(exc)
        if not any(cause in p for p in problems):  # case.json may already be named, with this cause
            problems.append(f"the loop's status cannot be read: {cause}; {judge_report.REPAIR_FILE}")
    try:
        latest = judge_report.saved_reports(case_dir)
    except _content_errors() as exc:
        latest = None
        problems.append(f"the saved reports cannot be read: {exc}; {judge_report.REPAIR_FILE}")
    if latest and status is not None:
        problems.extend(contradictions(case_dir, status.undecided_findings))
    problems.extend(review_without_finance(case_dir))
    if status is not None:  # a change after funding (spec 0.4.0 item 6); never a repair
        problems.extend(status.funding_changes)
    problems.extend(refused_proposals(case_dir))
    done = status is not None and status.done and not problems
    if done:
        state = "done"
    elif status is not None and status.stopped_by_budget:
        state = "stopped_by_budget"
    else:
        state = "open"
    data = {
        "source_plugin": SOURCE_PLUGIN,
        "schema_version": SCHEMA_VERSION,
        "status": state,
        "completed_at": clock.now(),
        "output_dir": str(case_dir.resolve()),
        "open_items": None if status is None else [{"item_id": iid, "state": states[iid]}
                                                   for iid in status.open_items],
        "needs_human": not done,
        "latest_report": latest[0] if latest else None,
        "mode": mode,
        # null, not []: while a strategy file cannot be read, the gaps are unknown (final review M-1)
        "absent_categories": None if status is None or status.absent_categories is None
        else list(status.absent_categories),
        "orphaned_conditions": None if status is None or status.orphaned_conditions is None
        else list(status.orphaned_conditions),
        "problems": problems,
        # null, like open_items, while the loop's status cannot be read
        "evidence_needed": None if status is None else evidence_needed(status.open_items),
    }
    path = case_dir / paths.HANDOFF
    case_files._write_json(path, data)
    return path


CONTRADICTION = ("the independent review's verdict is not supported because of finding {id}: {summary}; "
                 "the person answers it: correct the figure, bring newer evidence, or answer it in the case "
                 "text, then run the independent review again")


# {named} is " (P2, Build)", " (P2)", " (Build)" or "": whichever of the label and the line exists.
REFUSED_PROPOSAL = ("proposal {proposal}{named} of the latest figure run was refused: {reason}; "
                    "a person supplies what it needs, then records it again")
REFUSED_RUN = ("the latest figure run recorded no figure after this refusal: {reason}; "
               "a person repairs the cause, then runs `figure` again")
# {count} is "1 money amount" or "N money amounts"; {amounts} each "<section heading>: <amount>", joined "; ".
UNCOVERED_RUN = ("the latest figure run left {count} with no recorded figure: {amounts}; "
                 "a person records them, or the extractor runs again")


def _line(r: dict) -> str:
    """One record of figure-refusals.json in the handoff's words."""
    if r.get("kind") == "run":
        return REFUSED_RUN.format(reason=r.get("reason"))
    if r.get("kind") == "uncovered":
        left = r["amounts"]
        count = "1 money amount" if len(left) == 1 else f"{len(left)} money amounts"
        return UNCOVERED_RUN.format(count=count, amounts="; ".join(left))
    shown = [x for x in (r.get("label"), r.get("line")) if x]
    named = f" ({', '.join(map(str, shown))})" if shown else ""
    return REFUSED_PROPOSAL.format(proposal=r.get("proposal"), named=named, reason=r.get("reason"))


def refused_proposals(case_dir) -> list:
    """One line per refused proposal of the latest `bc.py figure` run, or the refusal of the whole run,
    then one for the amounts it left uncovered, read from the file that run wrote, so an automated
    run hands each one to a person. No file: no run yet, nothing to name."""
    path = Path(case_dir) / paths.FIGURE_REFUSALS
    try:
        if not paths.stat_exists(path):
            return []
        return [_line(r) for r in json.loads(path.read_text(encoding="utf-8"))]
    except (OSError, UnicodeDecodeError, ValueError, TypeError, AttributeError, KeyError) as exc:
        return [f"{paths.FIGURE_REFUSALS} cannot be read: {exc}; run `figure` again to rewrite it"]


def contradictions(case_dir, undecided) -> list:
    """One line per finding a verdict of not_supported below its ceiling rests on, while no decision
    answers it (`undecided`: status's undecided findings). Such a verdict rests on what the
    independent review found, not on the numbers, so a person must answer it; an automated run
    changes no figure (Task 21 carry, operator decision 2026-10-29). Derived from the latest saved
    report; a report that cannot be read gives none here, as the loop is not done while its newest
    report cannot be read."""
    try:
        found = judge_report.latest_report(Path(case_dir))
    except (judge_report.ReplyRefused, *_content_errors()):
        return []
    report = found[1] if found else None
    ceiling = report.get("investment_ceiling") if isinstance(report, dict) else None
    if not isinstance(ceiling, dict) or report.get("investment_verdict") != "not_supported" \
            or ceiling.get("value") == "not_supported":
        return []
    rests_on = report.get("verdict_rests_on") if isinstance(report.get("verdict_rests_on"), list) else []
    summaries = {f.get("id"): f.get("summary") for f in report.get("findings", []) if isinstance(f, dict)}
    return [CONTRADICTION.format(id=fid, summary=" ".join(str(summaries.get(fid)).split()).rstrip("."))
            for fid in rests_on if fid in undecided]


def review_without_finance(case_dir) -> list:
    """One line when the latest saved report is a JSON object that read no finance.json (a report
    saved before 0.3.0): a funding decision refuses such a report, so the case is not ready to fund,
    even one funded under 0.2.0. No report, or one that cannot be read or is not an object, gives
    none: the loop is not done then, so the handoff is already open. The handoff never refuses on
    case content, so a reader's refusal gives none too."""
    try:
        found = judge_report.latest_report(Path(case_dir))
    except (judge_report.ReplyRefused, *_content_errors()):
        return []
    if found is None or not isinstance(found[1], dict) or judge_report.finance_read_by(found[1]) is not None:
        return []
    return [f"{judge_report.READ_NO_FINANCE}; run the independent review again before a funding decision"]


def _content_errors() -> tuple:
    """The refusals a reader raises for a case file it cannot read. A function, so no attribute of
    decision_record is read at import time (Global Constraints, P3-04)."""
    return (case_files.CaseRefused, case_doc.CaseDocError, chained_log.LogRefused, conditions.ConditionRefused,
            decision_record.DecisionRefused, evidence.EvidenceRefused, figures.FigureRefused,
            finance.FinanceRefused, ledger.LedgerRefused, register.RegisterRefused, rubric.RubricError,
            OSError, UnicodeDecodeError)

