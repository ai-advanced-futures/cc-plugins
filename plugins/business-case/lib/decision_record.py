"""The decision record: the only writer of decisions.jsonl, an append-only judge input.

Spec §5 and §6, ADR-002 and ADR-005. Every decision comes from an explicit answer by a named
person, in the proposer or the funder role. What a decision cites is fixed by its kind and subject,
so an edit to the case document does not cancel an earlier accept or waive.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import tempfile
from pathlib import Path

from lib import (
    case_files,
    chained_log,
    clock,
    digest,
    evidence,
    figures,
    judge_report,
    ledger,
    loop_end,
    paths,
    rubric,
)

ROLES = ("proposer", "funder")

# kind -> (the role that may record it, the subject types it may be about)
KINDS = {
    "fix": ("funder", frozenset({"finding"})),
    "accept": ("funder", frozenset({"finding"})),
    "waive": ("funder", frozenset({"finding", "proposal"})),
    "approve_estimate": ("funder", frozenset({"proposal"})),
    "reject_estimate": ("funder", frozenset({"proposal"})),
    "propose_estimate": ("proposer", frozenset({"item"})),
    "propose_not_relevant": ("proposer", frozenset({"item"})),
    "reject_not_relevant": ("funder", frozenset({"proposal"})),
    "fund": ("funder", frozenset({"case"})),
    "do_not_fund": ("funder", frozenset({"case"})),
    "defer": ("funder", frozenset({"case"})),
    "propose_exclusion": ("proposer", frozenset({"figure"})),
    "approve_exclusion": ("funder", frozenset({"proposal"})),
    "reject_exclusion": ("funder", frozenset({"proposal"})),
    "move_rubric": ("funder", frozenset({"case"})),
}
FUNDING_KINDS = frozenset({"fund", "do_not_fund", "defer"})
# Decisions about the case as a whole (ruling P3-46). A move changes the standard the case is
# judged by, so the funder records it; only rubric_move writes it (bc.py decide leaves it out).
MOVE_KIND = "move_rubric"
CASE_KINDS = FUNDING_KINDS | {MOVE_KIND}
MOVE_OPTIONS = ["move_rubric", "stay"]
PROPOSAL_KINDS = frozenset({"propose_estimate", "propose_not_relevant", "propose_exclusion"})
EXCLUSION_ANSWERS = frozenset({"approve_exclusion", "reject_exclusion"})
PROPOSER_CHOICE = "propose"

# A decision cites the validated report, never the raw reply or its receipt, and never a file the
# coach keeps for itself or one that changes with every edit.
NEVER_CITED = (f"{paths.INPUTS_DIR}/", paths.CHANGELOG, paths.LEDGER, paths.CASE_META, paths.SCOPE,
               paths.DECISIONS, f"{paths.JUDGE_DIR}/brief-", f"{paths.JUDGE_DIR}/reply-")

# The one grammar of an evidence-page cite; loop_end reuses it.
EVIDENCE_CITE = re.compile(r"^evidence/(EV-[0-9]{3,})\.json$")
_ID = re.compile(r"^D-([0-9]{3,})$")


class DecisionRefused(ValueError):
    """A decision the rules refuse. Nothing is appended, except for RecordedButLedgerFailed."""


class Reads:
    """The files a pass over many records reads, each read once (loop_end re-checks every record).
    The files do not change during one pass, so each answer is the one a fresh read gives; a read
    that raised raises the same exception again."""

    def __init__(self, case_dir, records: list, figures_upto: int | None = None):
        self.case_dir = Path(case_dir)
        self.records = list(records)  # read_decisions(case_dir)
        self.figures_upto = figures_upto  # figures.jsonl cut at this length (None: the whole file)
        self._memo = {}

    def get(self, key, read):
        if key not in self._memo:
            try:
                self._memo[key] = (read(), None)
            except Exception as exc:  # kept and raised again, as a fresh read would raise it
                self._memo[key] = (None, exc)
        value, exc = self._memo[key]
        if exc is not None:
            raise exc
        return value

    def reports(self) -> dict:
        """relpath -> report or None, newest first: judge_report.parsed_reports, read once."""
        return self.get("reports", lambda: dict(judge_report.parsed_reports(self.case_dir)))

    def report(self, rel: str):
        reports = self.reports()
        if rel in reports:
            return reports[rel]
        return self.get(("report", rel), lambda: judge_report.read_report(self.case_dir / rel))


def _get(reads, key, read):
    return read() if reads is None else reads.get(key, read)


class RecordedButLedgerFailed(DecisionRefused):
    """The decision WAS appended to decisions.jsonl; only the ledger reference failed. A caller
    must not retry: that would record the decision twice."""


def _blank(value) -> bool:
    return not isinstance(value, str) or value.strip() == ""


def read_records(case_dir) -> list:
    """(record, end) for each record in file order. `end` is the byte offset just past the record's
    line, so a report whose manifest recorded N bytes of decisions.jsonl read every record with
    end <= N. Lines are split on \\n only: write_decision ends each record with one \\n, and a
    U+2028 inside a reason is text, not a line break."""
    path = Path(case_dir) / paths.DECISIONS
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise DecisionRefused(f"cannot read {path}: {exc}") from exc
    out = []
    start = 0
    for n, raw in enumerate(data.split(b"\n"), 1):
        end = min(start + len(raw) + 1, len(data))
        start += len(raw) + 1
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DecisionRefused(f"cannot read {path}: line {n} is not UTF-8: {exc}") from exc
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DecisionRefused(f"{path} line {n} is not JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise DecisionRefused(f"{path} line {n} is not a JSON object")
        out.append((obj, end))
    return out


def read_decisions(case_dir) -> list:
    return [record for record, _ in read_records(case_dir)]


def get_decision(case_dir, decision_id, reads: Reads = None):
    for d in read_decisions(case_dir) if reads is None else reads.records:
        if d.get("id") == decision_id:
            return d
    return None


def is_valid(decision: dict, case_dir, reads: Reads = None) -> bool:
    """True while every file the decision cites still has the digest recorded with it."""
    cited = decision.get("cited")
    if not isinstance(cited, dict):
        return False
    for rel, recorded in cited.items():
        try:
            if _get(reads, ("digest", rel), lambda rel=rel: digest.file_digest(Path(case_dir) / rel)) != recorded:
                return False
        except OSError:
            return False
    return True


def _clean_cite(case_dir: Path, rel) -> str:
    if not isinstance(rel, str) or rel == "" or rel != rel.strip() or "\\" in rel or "\x00" in rel:
        raise DecisionRefused(f"cited path {rel!r} is not a plain relative path")
    if rel.startswith("/") or posixpath.normpath(rel) != rel or rel.split("/")[0] == "..":
        raise DecisionRefused(f"cited path {rel!r} is not a plain path inside the case folder")
    for prefix in NEVER_CITED:
        if rel.casefold().startswith(prefix.casefold()):  # case-folded, as the judge guard compares
            raise DecisionRefused(f"{rel} may not be cited: a decision cites the validated report, "
                                  "the case document and evidence pages, not raw or coach files")
    full = Path(case_dir) / rel
    if not full.is_file() or not full.resolve().is_relative_to(Path(case_dir).resolve()):
        raise DecisionRefused(f"cited file {rel} is missing or outside the case folder")
    return rel


def _evidence_page(case_dir: Path, rel: str) -> dict:
    m = EVIDENCE_CITE.match(rel)
    if not m:
        raise DecisionRefused(f"{rel} is not an evidence page")
    try:
        return evidence.read_page(case_dir, m.group(1))
    except evidence.EvidenceRefused as exc:
        raise DecisionRefused(str(exc)) from exc


def _figures(case_dir: Path, reads: Reads = None) -> dict:
    """The counted figures by ID (figures.figures), read once per pass. Every figures read here goes
    through this helper, so a broken figures.jsonl is a DecisionRefused naming the file: loop_end
    counts the record as not counted, and never raises."""
    upto = None if reads is None else reads.figures_upto
    try:
        return _get(reads, "figures", lambda: figures.figures(case_dir, upto))
    except (figures.FigureRefused, evidence.EvidenceRefused, OSError) as exc:
        raise DecisionRefused(f"{paths.FIGURES} cannot be read: {exc}") from exc


def _overridden_estimate(case_dir: Path, item_id, ev_id: str, reads: Reads = None) -> bool:
    """True when a live figure on (item_id, ev_id) is graded estimated by figures.grade (spec §4
    "The grade"): a terminal value, or a page sourced from business-case.md. Today's figures."""
    for fig in _figures(case_dir, reads).values():
        if fig["status"] == "superseded" or (fig.get("item_id"), fig.get("evidence")) != (item_id, ev_id):
            continue
        try:
            if figures.grade(case_dir, fig) == "estimated":
                return True
        except (figures.FigureRefused, evidence.EvidenceRefused, OSError) as exc:
            raise DecisionRefused(f"{paths.FIGURES}: {fig['id']} cannot be graded: {exc}") from exc
    return False


def _require_item(case_dir: Path, item_id, reads: Reads = None) -> None:
    try:
        known = isinstance(item_id, str) and item_id in _get(reads, "ledger", lambda: ledger.read_ledger(case_dir))
    except ledger.LedgerRefused as exc:
        raise DecisionRefused(str(exc)) from exc
    if not known:
        raise DecisionRefused(f"{item_id!r} is not an applicable item of this case")


def _only_evidence(cite: list) -> None:
    for rel in cite:
        if not EVIDENCE_CITE.match(rel):
            raise DecisionRefused(f"{rel} may not be cited here: only evidence pages")


def _finding_in(case_dir: Path, rel: str, finding_id, reads: Reads = None) -> dict | None:
    """The finding with this ID in the saved report at `rel`, or None."""
    if not judge_report.is_report_relpath(rel):
        return None
    report = judge_report.read_report(Path(case_dir) / rel) if reads is None else reads.report(rel)
    findings = report.get("findings") if isinstance(report, dict) else None
    for f in findings if isinstance(findings, list) else []:
        if isinstance(f, dict) and f.get("id") == finding_id:
            return f
    return None


def _check_subject(case_dir: Path, kind: str, subject_type: str, subject_ref, item_id, cite: list,
                   recorded: bool = False, reads: Reads = None, cited: dict = None) -> None:
    """The per-subject rules of the cite policy (ADR-005). `recorded` re-checks a record already in
    the file: newer reports may exist since it was written, so a decision on a finding may cite any
    saved report that holds the finding, and a funding decision any saved report. `cited` is the
    recorded path -> digest map; a recorded funding decision's snapshot is checked against it."""
    if kind in FUNDING_KINDS:
        slug = _get(reads, "meta", lambda: case_files.read_meta(case_dir)).get("slug")
        if subject_ref != slug:
            raise DecisionRefused(f"a funding decision is about the case {slug!r}, not {subject_ref!r}")
        if item_id is not None:
            raise DecisionRefused("a funding decision has no item")
        if recorded:
            reports = [c for c in cite if judge_report.is_report_relpath(c)]
            if paths.CASE_DOC not in cite or len(reports) != 1:
                raise DecisionRefused(f"a funding decision cites one saved report and {paths.CASE_DOC}")
            # From 0.3.0 it also cites that report's snapshot; a record from before cites only the two.
            snapshot = snapshot_relpath(reports[0])
            extra = set(cite) - {reports[0], paths.CASE_DOC}
            if extra and extra != {snapshot}:
                raise DecisionRefused(f"a funding decision cites one saved report, {paths.CASE_DOC} and that "
                                      f"report's snapshot {snapshot}, nothing else")
            if extra:  # the snapshot holds the bytes the report read, as write_decision saved them
                report = (judge_report.read_report(Path(case_dir) / reports[0]) if reads is None
                          else reads.report(reports[0]))
                manifest = report.get("manifest") if isinstance(report, dict) else None
                read = manifest.get(paths.FINANCE) if isinstance(manifest, dict) else None
                if not digest._is_digest(read) or (cited or {}).get(snapshot) != read:
                    raise DecisionRefused(f"its snapshot {snapshot} is not the {paths.FINANCE} that "
                                          f"{reports[0]} read")
            return
        latest = judge_report.latest_report(case_dir)
        if latest is None:
            raise DecisionRefused("no judge report is saved; a funding decision cites the latest one")
        if sorted(cite) != sorted([latest[0], paths.CASE_DOC]):
            raise DecisionRefused(f"a funding decision cites exactly {latest[0]} and {paths.CASE_DOC}")
        return

    if kind == MOVE_KIND:  # before _require_item, which refuses a decision with no item
        slug = _get(reads, "meta", lambda: case_files.read_meta(case_dir)).get("slug")
        if subject_ref != slug:
            raise DecisionRefused(f"a rubric move is about the case {slug!r}, not {subject_ref!r}")
        if item_id is not None:
            raise DecisionRefused("a rubric move has no item")
        if cite != [paths.RUBRIC_COPY]:
            raise DecisionRefused(f"a rubric move cites exactly {paths.RUBRIC_COPY}, the copy it moved to")
        return

    if subject_type == "finding":
        # A whole-plan finding has no item, and a decision on it names none (ADR-008).
        if item_id is not None:
            _require_item(case_dir, item_id, reads)
        parsed = None if reads is None else list(reads.reports().items())
        found = judge_report.find_finding(case_dir, subject_ref, parsed)
        if found is None:
            raise DecisionRefused(f"{subject_ref!r} is not a finding in any saved report")
        report_rel, finding = found
        if recorded:
            held = [(rel, _finding_in(case_dir, rel, subject_ref, reads)) for rel in cite]
            holders = [(rel, f) for rel, f in held if f is not None]
            if len(holders) != 1:
                raise DecisionRefused(f"a decision on a finding cites one saved report that holds it, "
                                      f"such as {report_rel}")
            report_rel, finding = holders[0]
        if finding.get("item_id") != item_id:
            raise DecisionRefused(f"finding {subject_ref} is about {finding.get('item_id')}, not {item_id}")
        if report_rel not in cite:
            raise DecisionRefused(f"a decision on a finding cites the report that holds it, {report_rel}")
        _only_evidence([c for c in cite if c != report_rel])
        return

    if subject_type == "figure":  # propose_exclusion: before _require_item, which refuses no item
        if item_id is not None:
            raise DecisionRefused("an exclusion proposal has no item; its subject names the figure")
        fig = _figures(case_dir, reads).get(subject_ref)
        if fig is None:
            raise DecisionRefused(f"{subject_ref!r} is not a recorded figure")
        if fig["status"] == "superseded" or fig.get("kind") != "excluded" or fig.get("restates"):
            raise DecisionRefused(f"{subject_ref} is not a live judgment exclusion (an excluded figure with "
                                  "no restates); only a judgment exclusion needs the funder's approval")
        if cite:
            raise DecisionRefused("an exclusion proposal cites nothing; its subject names the figure")
        return

    if subject_type == "proposal" and kind in EXCLUSION_ANSWERS:
        proposal = get_decision(case_dir, subject_ref, reads)
        if proposal is None:
            raise DecisionRefused(f"{subject_ref!r} is not a recorded decision")
        if proposal.get("kind") != "propose_exclusion":
            raise DecisionRefused(f"{subject_ref} is not an exclusion proposal; a {kind} answers one")
        if item_id is not None:
            raise DecisionRefused(f"a {kind} has no item; its subject names the proposal")
        if cite:
            raise DecisionRefused(f"a {kind} cites nothing; its subject names the proposal")
        return

    _require_item(case_dir, item_id, reads)

    if subject_type == "item":
        if subject_ref != item_id:
            raise DecisionRefused(f"the subject {subject_ref!r} must be the item {item_id!r}")
        if kind == "propose_estimate":
            if not cite:
                raise DecisionRefused("an estimate proposal cites one or more estimated evidence pages")
            for rel in cite:
                page = _evidence_page(case_dir, rel)
                if page.get("grade") == "estimated" and item_id in page.get("item_ids", []):
                    continue
                if not _overridden_estimate(case_dir, item_id, EVIDENCE_CITE.match(rel).group(1), reads):
                    raise DecisionRefused(f"{rel} is not an estimated page that lists {item_id}, and no live "
                                          f"figure for {item_id} on it is graded estimated")
        else:
            _only_evidence(cite)
        return

    # subject_type == "proposal"
    proposal = get_decision(case_dir, subject_ref, reads)
    if proposal is None:
        raise DecisionRefused(f"{subject_ref!r} is not a recorded decision")
    if proposal.get("item_id") != item_id:
        raise DecisionRefused(f"proposal {subject_ref} is about {proposal.get('item_id')}, not {item_id}")
    if kind in ("waive", "reject_not_relevant"):
        if proposal.get("kind") != "propose_not_relevant":
            raise DecisionRefused(f"{subject_ref} is not a not-relevant proposal; "
                                  "a waiver on a proposal answers one")
        if cite:
            raise DecisionRefused(f"a {kind} on a proposal cites nothing; its subject names the proposal")
        return
    proposed = proposal.get("cited")
    if proposal.get("kind") != "propose_estimate" or not isinstance(proposed, dict):
        raise DecisionRefused(f"{subject_ref} is not an estimate proposal")
    if sorted(cite) != sorted(proposed):
        raise DecisionRefused(f"an estimate decision cites exactly the pages the proposal cites: {sorted(proposed)}")


def snapshot_relpath(report_rel: str) -> str:
    """funding/finance-report-NNN.json, the funding snapshot named after the report judge/report-NNN.json."""
    return f"{paths.FUNDING_DIR}/finance-report-{judge_report.report_number(report_rel):03d}.json"


def _finance_read_by(case_dir: Path, report_rel: str) -> dict:
    """The digest of finance.json in the cited report's manifest. A report saved before 0.3.0 read
    no finance.json, so there is nothing to save as the funding baseline."""
    read = judge_report.finance_read_by(judge_report.read_report(case_dir / report_rel))
    if read is None:
        raise DecisionRefused(f"{judge_report.READ_NO_FINANCE}; run the independent review again first")
    return read


def _save_snapshot(case_dir: Path, report_rel: str, read: dict) -> str:
    """Save the exact finance.json bytes the report read as its funding snapshot and return its path.
    The caller holds the decisions lock, the lock `bc.py brief` holds while it writes finance.json,
    so the bytes read here are not being rewritten. No other lock is taken here. An existing
    snapshot with the same bytes is reused; one with other bytes is never rewritten."""
    rel = snapshot_relpath(report_rel)
    try:
        data = (case_dir / paths.FINANCE).read_bytes()
    except OSError as exc:  # a broken file is repaired, not reviewed again (controller ruling, Task 14)
        raise DecisionRefused(f"{paths.FINANCE} cannot be read: {exc}; {judge_report.REPAIR_FILE}") from exc
    if digest._digest_of(data) != read:
        raise DecisionRefused("the numbers changed since the independent review; run it again")
    path = case_dir / rel
    try:
        path.parent.mkdir(exist_ok=True)
    except OSError as exc:  # funding/ is a file, or the case folder is read-only
        raise DecisionRefused(f"cannot write {rel}: {exc}") from None
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".snapshot-")
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.link(tmp, path)  # fails when the snapshot is there, so it is never overwritten
    except FileExistsError:
        try:
            same = path.is_file() and path.read_bytes() == data
        except OSError:
            same = False
        if not same:
            raise DecisionRefused(f"{rel} already exists with other bytes; a funding snapshot is never "
                                  "rewritten") from None
    except OSError as exc:
        raise DecisionRefused(f"cannot write {rel}: {exc}") from None
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:  # a dot file left in funding/; never a traceback on the funding path
                pass
    return rel


def _check_fields(kind, role, subject_type, question, reason, options, choice, shown) -> None:
    """The rules on a decision's own fields, shared by write_decision and check_recorded."""
    if not isinstance(kind, str) or kind not in KINDS:
        raise DecisionRefused(f"kind {kind!r} is not one of {', '.join(KINDS)}")
    if role not in ROLES:
        raise DecisionRefused(f"role {role!r} is not proposer or funder")
    need_role, subject_types = KINDS[kind]
    if role != need_role:
        raise DecisionRefused(f"{kind} is the {need_role}'s decision, not the {role}'s")
    if not isinstance(subject_type, str) or subject_type not in subject_types:
        raise DecisionRefused(f"{kind} is not about a {subject_type!r}; it is about {sorted(subject_types)}")
    if _blank(question):
        raise DecisionRefused("the decision needs the question that was asked")
    if _blank(reason):
        raise DecisionRefused("the decision needs the person's reason")
    if (not isinstance(options, list) or len(options) < 2
            or not all(isinstance(o, str) and o.strip() for o in options)):
        raise DecisionRefused("a decision needs a list of at least two options")
    if choice not in options:
        raise DecisionRefused(f"choice {choice!r} is not one of the options shown")
    want = PROPOSER_CHOICE if kind in PROPOSAL_KINDS else kind
    if choice != want:
        raise DecisionRefused(f"a {kind} decision records the choice {want!r}, not {choice!r}")
    if kind in FUNDING_KINDS and options != ["fund", "do_not_fund", "defer"]:
        raise DecisionRefused("a funding decision shows exactly the options fund, do_not_fund, defer")
    if kind == MOVE_KIND and options != MOVE_OPTIONS:
        raise DecisionRefused("a rubric move shows exactly the options move_rubric, stay")
    if not isinstance(shown, list) or not all(isinstance(s, str) for s in shown):
        raise DecisionRefused("shown is a list of strings")


def _check_met_test_id(met, item_id) -> None:
    """A recorded met-test ID is `<item>.M<n>` for the record's own item; a record with no item has none."""
    if item_id is None:
        raise DecisionRefused("the record has a met-test ID but no item; only a decision about an item has one")
    found = rubric.MET_TEST_ID.fullmatch(met) if isinstance(met, str) else None
    if found is None or found.group("item") != item_id:
        raise DecisionRefused(f"its met-test ID {met!r} is not a met-test ID of its item {item_id}")


def check_recorded(case_dir, record, reads: Reads = None) -> None:
    """Re-apply write_decision's rules to a record already in decisions.jsonl. Raises
    DecisionRefused naming the first rule it breaks. A reader that counts decisions (loop_end) calls
    this, so a line appended by hand counts only when write_decision would have written it. A
    caller checking many records passes one Reads, so each file is read once."""
    case_dir = Path(case_dir)
    if not isinstance(record, dict):
        raise DecisionRefused("a decision record is a JSON object")
    rid = record.get("id")
    if not isinstance(rid, str) or not _ID.match(rid):
        raise DecisionRefused(f"its ID {rid!r} is not D-NNN")
    subject = record.get("subject")
    if not isinstance(subject, dict) or not isinstance(subject.get("ref"), str):
        raise DecisionRefused("the record has no subject {type, ref} with a string ref")
    if _blank(record.get("name")):
        raise DecisionRefused("the record has no name")
    _check_fields(record.get("kind"), record.get("role"), subject.get("type"), record.get("question"),
                  record.get("reason"), record.get("options"), record.get("choice"), record.get("shown"))
    cited = record.get("cited")
    if not isinstance(cited, dict):
        raise DecisionRefused("the record's cited is not an object of path -> digest")
    clean = [_clean_cite(case_dir, rel) for rel in cited]
    _check_subject(case_dir, record["kind"], subject.get("type"), subject.get("ref"), record.get("item_id"),
                   clean, recorded=True, reads=reads, cited=cited)
    if "met_test_id" in record:  # absent on a record written before 0.3.0
        _check_met_test_id(record.get("met_test_id"), record.get("item_id"))


def write_decision(case_dir, *, kind, role, question, options, shown, choice, reason,
                   subject_type, subject_ref, item_id, cite) -> dict:
    """Append one decision to decisions.jsonl and return it. Refuses, and appends nothing, for a
    missing or automated session, a blank question or reason, a role or subject the kind does not
    allow, a choice that is not an option, a funding decision before loop end, and a cite the
    policy does not allow."""
    case_dir = Path(case_dir)
    try:
        name = case_files.current_name(case_dir)
    except case_files.CaseRefused as exc:
        raise DecisionRefused(f"no decision without a named person: {exc}") from exc
    _check_fields(kind, role, subject_type, question, reason, options, choice, shown)
    if kind in FUNDING_KINDS:
        status = loop_end.loop_status(case_dir)
        if not status.done:
            raise DecisionRefused("a funding decision waits for the loop to end, and the loop is not done: "
                                  + "; ".join(status.reasons))
    if not isinstance(cite, list):
        raise DecisionRefused("cite is a list of paths")
    clean = [_clean_cite(case_dir, rel) for rel in cite]
    if len(set(clean)) != len(clean):
        raise DecisionRefused("a path is cited twice")
    _check_subject(case_dir, kind, subject_type, subject_ref, item_id, clean)
    funding_report = None
    if kind in FUNDING_KINDS:  # _check_subject: clean is exactly [the latest report, business-case.md]
        funding_report = next(rel for rel in clean if judge_report.is_report_relpath(rel))
        finance_read = _finance_read_by(case_dir, funding_report)
    met = {}
    if item_id is not None:
        try:
            met = {"met_test_id": rubric.met_test_id(rubric.load_rubric(case_dir / paths.RUBRIC_COPY), item_id)}
        except rubric.RubricError as exc:
            raise DecisionRefused(f"cannot read the met-test ID of {item_id}: {exc}") from exc

    record = {"id": None, "kind": kind, "role": role, "name": name,
              "date": clock.today(), "question": question, "options": list(options), "shown": list(shown),
              "choice": choice, "reason": reason,
              "subject": {"type": subject_type, "ref": subject_ref}, "item_id": item_id, **met,
              "cited": {rel: digest.file_digest(case_dir / rel) for rel in clean}, "outcome": {}}
    try:
        json.dumps(record, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise DecisionRefused(f"the decision text is not valid UTF-8 (a lone surrogate?): {exc}") from exc
    target = case_dir / paths.DECISIONS
    # One lock across reading the IDs, appending and the ledger reference, so two writers never
    # take the same D-NNN and never drop each other's reference (ledger.CASE_LOCK).
    with chained_log.locked_append(target, DecisionRefused) as fd:
        if target.stat().st_size > 0:
            with open(target, "rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    raise DecisionRefused(f"{paths.DECISIONS} does not end in a newline; "
                                          "a new record would join its last line. Repair the file first")
        if funding_report is not None:  # the snapshot is saved before the decision that cites it
            # The latest report was chosen before the lock; a save-report since then makes it old.
            # This narrows the window to the lock-to-append span: save-report does not take this lock.
            try:
                latest = judge_report.latest_report(case_dir)
            except judge_report.ReplyRefused as exc:
                raise DecisionRefused(str(exc)) from exc
            if latest is None or latest[0] != funding_report:
                newer = latest[0] if latest else "no saved report"
                raise DecisionRefused(f"a newer independent review, {newer}, was saved after {funding_report}; "
                                      "answer it first, then record the funding decision again")
            snapshot = _save_snapshot(case_dir, funding_report, finance_read)
            record["cited"][snapshot] = digest.file_digest(case_dir / snapshot)
        numbers = [int(m.group(1)) for d in read_decisions(case_dir) for m in [_ID.match(str(d.get("id")))] if m]
        record["id"] = f"D-{max(numbers, default=0) + 1:03d}"
        line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
        try:
            os.write(fd, line)  # one write of one line
        except OSError as exc:
            raise DecisionRefused(f"{paths.DECISIONS}: cannot append: {exc}") from exc
        if item_id is not None:
            try:
                ledger.add_decision_ref(case_dir, item_id, record["id"])
            except ledger.LedgerRefused as exc:
                raise RecordedButLedgerFailed(
                    f"the decision WAS recorded as {record['id']}, but the ledger reference failed: {exc}. "
                    "Do not record it again") from exc
    return record
