# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""bc.py: the business-case CLI, the only way the prose layer touches a case's files.

Every subcommand but `temp-dir` takes --case DIR. Exit 0 means ok, 1 means not done (`status` only), and 2 means
refused or a usage error; a refusal prints one line, `REFUSED: <reason>`, to stderr. Text a person
typed (a section body, a decision's reason) is read from a file, so it is kept byte for byte with
no shell quoting. No option sets who wrote a judge report: code decides that from the receipt.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import (
    basis,  # noqa: E402
    case_doc,  # noqa: E402
    case_files,  # noqa: E402
    chained_log,  # noqa: E402
    conditions,  # noqa: E402
    decision_record,  # noqa: E402
    evidence,  # noqa: E402
    evidence_from_result,  # noqa: E402
    figures,  # noqa: E402
    finance,  # noqa: E402
    finance_view,  # noqa: E402
    handoff,  # noqa: E402
    install_check,  # noqa: E402
    judge_brief,  # noqa: E402
    judge_receipt,  # noqa: E402
    judge_report,  # noqa: E402
    ledger,  # noqa: E402
    loop_end,  # noqa: E402
    paths,  # noqa: E402
    plugin_map,  # noqa: E402
    register,  # noqa: E402
    rubric,  # noqa: E402
    rubric_move,  # noqa: E402
    settle,  # noqa: E402
    strategy_view,  # noqa: E402
    team_brief,  # noqa: E402
    team_files,  # noqa: E402
    team_record,  # noqa: E402
    team_reply,  # noqa: E402
    team_runs,  # noqa: E402
)

COACH_COPY_LINE = "coach copy: this report can be viewed but cannot end the loop; run the judge again"

# A refusal's budget in bytes, newline included: the line lands in the coach's context. Four
# 200-byte reasons, defined here so no plugin imports another.
REFUSAL_BYTE_CEILING = 800
CLIP_MARKER = f" ... [refusal clipped at {REFUSAL_BYTE_CEILING} bytes]"


class Refused(Exception):
    """A refusal the CLI itself makes."""


# The library's deliberate refusals. Any other exception, a stray ValueError included, is a bug
# and is reported as `unexpected error`. test_every_lib_refusal_class_is_caught_by_name derives the
# lib population and holds this tuple to it.
REFUSALS = (
    Refused,
    basis.BasisRefused,
    case_files.CaseRefused,
    case_doc.CaseDocError,
    chained_log.LogRefused,
    conditions.ConditionRefused,
    decision_record.DecisionRefused,
    evidence.EvidenceRefused,
    figures.FigureRefused,
    finance.FinanceRefused,
    install_check.GitFailed,  # caught inside install_check.check; here for the total check of lib refusals
    judge_brief.BriefRefused,
    judge_brief.BudgetExhausted,
    judge_receipt.ReceiptRefused,
    judge_report.ReplyRefused,
    ledger.LedgerRefused,
    register.RegisterRefused,
    rubric.RubricError,
    rubric_move.MoveRefused,
    team_files.TeamBudgetExhausted,
    team_files.TeamRefused,
    OSError,
)

# Lock order (Task 18 carry (d)): a command that holds the decisions lock (ledger.CASE_LOCK) and the
# figures lock at once takes the decisions lock first. Today no command nests them: `brief` holds the
# decisions lock and only reads figures.jsonl; `figure` and `mark FIG-NNN` take only the figures lock;
# `move-rubric` and `decide` take only the decisions lock; `compute` takes none.
# test_no_new_command_takes_the_decisions_lock_inside_the_figures_lock pins it.


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        _refuse(f"usage: {self.prog}: {message}")


def _one_line(reason: str) -> str:
    """`REFUSED: <reason>` on one line, clipped to REFUSAL_BYTE_CEILING keeping its start."""
    return _clip("REFUSED: " + reason.replace("\r", " ").replace("\n", " "))


def _clip(line: str) -> str:
    """A line clipped to REFUSAL_BYTE_CEILING bytes, its newline included, keeping its start."""
    data = line.encode("utf-8")
    if len(data) + 1 <= REFUSAL_BYTE_CEILING:
        return line
    keep = REFUSAL_BYTE_CEILING - 1 - len(CLIP_MARKER.encode("utf-8"))
    return data[:keep].decode("utf-8", "ignore") + CLIP_MARKER


def _refuse(reason: str) -> None:
    print(_one_line(reason), file=sys.stderr)
    sys.exit(2)


def _read_text(path, what: str) -> str:
    """A file's text exactly as given: UTF-8, with no newline translation. A file that cannot be
    read is refused naming which file it is."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Refused(f"{what} {path} cannot be read: {exc.strerror or exc}") from None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused(f"{what} {path} is not UTF-8 text") from None


def _question(a) -> str:
    """--question as given, or the text of --question-file read like --reason-file."""
    if a.question_file is not None:
        return _read_text(a.question_file, "the question file")
    return a.question


def _add_question(p) -> None:
    """Exactly one of --question and --question-file, on decide, mark and move-rubric."""
    q = p.add_mutually_exclusive_group(required=True)
    q.add_argument("--question")
    q.add_argument("--question-file", type=Path, help="the question the user saw, kept verbatim")


def _case_arg(text: str) -> Path:
    """--case for every subcommand: refused unless its resolved path is <anything>/business-cases/<slug>."""
    try:
        case_files.check_case_path(text)
    except case_files.CaseRefused as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None
    return Path(text)


def _need_session(case: Path) -> dict:
    return case_files.current_session(case)


def _need_person(case: Path) -> str:
    """The current session's person. An automated session has none, so it is refused."""
    return case_files.current_name(case)


# The next step after a broken file is repaired: the brief is written again; any other command is
# run again (Task 18 fix round, concern 1).
REPAIR_RERUN = "repair the file, then run this command again"


def _remedy(command: str) -> str:
    return judge_report.REPAIR_FILE if command == "brief" else REPAIR_RERUN


@contextlib.contextmanager
def _repair_remedy(command: str):
    """A file the finances read that cannot be read, or holds a line that does not count, is refused
    naming it, with the command's next step (never "run the judge again": a new run cannot pass until
    the file is repaired)."""
    try:
        yield
    except (figures.FigureRefused, finance.FinanceRefused, case_files.CaseRefused) as exc:
        raise Refused(f"{exc}; {_remedy(command)}") from None


def _figures_whole(case: Path, command: str) -> None:
    """Every command that reads figures.jsonl refuses a broken one first, naming the file and line
    (Task 18 fix round, concern 3). test_every_figures_reader_is_covered derives which commands read it."""
    with _repair_remedy(command):
        figures.check_file(case)


# -- subcommands -------------------------------------------------------------------------------

def cmd_init(a) -> int:
    case_files.init_case(a.case, slug=a.slug, offering=a.offering, market=a.market,
                         rubric_version=a.rubric_version)
    print(a.case)
    return 0


def cmd_session(a) -> int:
    entry = case_files.start_session(a.case, session_id=a.id, name=a.name, automated=a.automated)
    if entry.get("resumed"):
        print(f"session {entry['id']} ({entry['mode']}) resumed; {entry['judge_runs']} judge runs used")
    else:
        print(f"session {entry['id']} ({entry['mode']})")
    return 0


def cmd_ingest(a) -> int:
    print(case_files.store_original(a.case, a.kind, a.file, text=a.text_file))
    return 0


def cmd_change(a) -> int:
    _need_session(a.case)
    body = _read_text(a.body_file, "the body file")
    case_files.apply_change(a.case, section=a.section, body=body, summary=a.summary, source=a.source)
    print(a.case / paths.CASE_DOC)
    return 0


def cmd_ledger(a) -> int:
    _need_session(a.case)
    with chained_log.locked_append(a.case / ledger.CASE_LOCK, ledger.LedgerRefused):  # beside a decide
        ledger.set_entry(a.case, a.item, coach_class=a.coach_class, evidence=a.evidence, note=a.note)
    print(a.item)
    return 0


def cmd_evidence(a) -> int:
    """`--page-json FILE` writes a page built by hand; `--from-result FILE --result-id ID --grade G --items IDS`
    builds one from a result, every field but the grade and the items filled by code. Prints its EV-NNN."""
    _need_person(a.case)
    with_result = (("--result-id", a.result_id), ("--grade", a.grade), ("--items", a.items))
    if a.from_result is not None:
        missing = [name for name, value in with_result if value is None]
        if missing:
            raise Refused(f"--from-result needs {', '.join(missing)}")
        items = [i.strip() for i in a.items.split(",") if i.strip()]
        print(evidence_from_result.write_page_from_result(a.case, plugin_map.load(), a.from_result, a.result_id,
                                                          a.grade, items))
        return 0
    given = [name for name, value in with_result if value is not None]
    if given:
        raise Refused(f"{', '.join(given)} go with --from-result only")
    try:
        page = json.loads(_read_text(a.page_json, "the evidence page file"))
    except json.JSONDecodeError as exc:
        raise Refused(f"the evidence page file {a.page_json} is not JSON: {exc}") from None
    if isinstance(page, dict) and "result_ref" in page:
        raise Refused("a hand page holds no result_ref; a page built from a result is written by --from-result")
    print(evidence.write_page(a.case, page))
    return 0


def cmd_decide(a) -> int:
    _need_person(a.case)
    _figures_whole(a.case, "decide")
    question = _question(a)
    reason = _read_text(a.reason_file, "the reason file")
    record = decision_record.write_decision(
        a.case, kind=a.kind, role=a.role, question=question, options=a.option, shown=a.shown,
        choice=a.choice, reason=reason, subject_type=a.subject_type, subject_ref=a.subject,
        item_id=a.item, cite=a.cite)
    print(record["id"])
    return 0


def cmd_brief(a) -> int:
    """Every check runs before write_brief counts a run (ruling PF-12). The decisions lock is held from
    before finance.json is written until the brief is, so the two read one decisions.jsonl length
    (ruling P3-03); nothing inside takes the lock again. A brief refused before finance.json is written
    (a strategy file, the budget, the figures file) leaves finance.json as it was; one refused inside
    write_brief, after it, leaves the new finance.json in place, and no run is counted."""
    _need_session(a.case)
    with chained_log.locked_append(a.case / ledger.CASE_LOCK, judge_brief.BriefRefused):
        conditions.check_strategy_files(a.case)
        judge_brief.check_budget(a.case)
        _figures_whole(a.case, "brief")  # a new run cannot pass until then
        with _repair_remedy("brief"):
            finance.write_finance_json(a.case)
        path, _ = judge_brief.write_brief(a.case, check_finance=True)
    print(path)
    return 0


def cmd_save_report(a) -> int:
    _need_session(a.case)
    # A relative --brief or --coach-copy is relative to the case, not to the shell's directory.
    brief = Path(a.case) / a.brief
    if a.coach_copy is None:
        print(judge_report.save_report(a.case, brief))
    else:
        print(judge_report.save_coach_copy(a.case, brief, Path(a.case) / a.coach_copy))
        print(COACH_COPY_LINE)
    return 0


def cmd_status(a) -> int:
    status, states = loop_end.status_and_states(a.case)
    if a.json:
        data = dataclasses.asdict(status)
        data["item_states"] = states
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"done: {'yes' if status.done else 'no'}")
        print(f"stopped_by_budget: {'yes' if status.stopped_by_budget else 'no'}")
        for field in ("open_items", "undecided_findings", "stale_files", "absent_categories", "orphaned_conditions"):
            value = getattr(status, field)  # None: a strategy file cannot be read, so the list is unknown
            print(f"{field}: {'unknown' if value is None else ', '.join(value) or '-'}")
        print("reasons:")
        for reason in status.reasons:
            print(f"- {reason}")
        # Spec 0.4.0 item 6: their own block; they never change done or the exit code.
        print("funding_changes:" if status.funding_changes else "funding_changes: -")
        for line in status.funding_changes:
            print(f"- {line}")
    return 0 if status.done else 1


def cmd_items(a) -> int:
    _figures_whole(a.case, "items")
    items = case_files.applicable_items(a.case)
    entries = ledger.read_ledger(a.case)
    states = loop_end.item_states(a.case)
    rows = [{"item_id": i["id"], "title": i["title"],
             "coach_class": (entries.get(i["id"]) or {}).get("coach_class"), "state": states[i["id"]]}
            for i in items]
    if a.json:
        owners = plugin_map.load()["items"]
        for row in rows:  # the owning analyst, so the coach never reads the map itself (live run F6)
            row["owner"] = (owners.get(row["item_id"]) or {}).get("owner")
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print(f"{row['item_id']}\t{row['state']}\t{row['coach_class']}\t{row['title']}")
    return 0


# The keys each strategy JSON file may hold: (required, optional). Anything else is refused, so no
# file can set a field code fills in (id, recorded_by, date) or a status code derives.
_SUPERSEDE_KEYS = ("supersedes", "reason", "change_source")
ENTRY_KEYS = (("category", "choice", "rejected_alternative", "evidence", "source"), _SUPERSEDE_KEYS)
CONDITION_KEYS = (("text", "supports", "evidence", "source"), _SUPERSEDE_KEYS)
NOTE_KEYS = (("text", "source", "failed_tests", "reason"), ())
ENTRY_UNSUPPORTED = "a register entry is confirmed or superseded, never unsupported"
FIGURE_UNSUPPORTED = "a figure is confirmed or superseded, never unsupported"


def _read_json_object(path, what: str, keys: tuple) -> dict:
    """A strategy JSON file as keyword arguments: one object, every required key, no other key."""
    try:
        data = json.loads(_read_text(path, what))
    except json.JSONDecodeError as exc:
        raise Refused(f"{what} {path} is not JSON: {exc}") from None
    if not isinstance(data, dict):
        raise Refused(f"{what} {path} is not a JSON object")
    required, optional = keys
    extra = sorted(set(data) - set(required) - set(optional))
    if extra:
        raise Refused(f"{what} {path} holds the key(s) {', '.join(extra)}; "
                      f"the keys allowed are {', '.join(required + optional)}")
    missing = [k for k in required if k not in data]
    if missing:
        raise Refused(f"{what} {path} lacks the key(s) {', '.join(missing)}")
    return data


def _rebuild_view(case: Path, recorded: str) -> None:
    """Rewrite strategy-view.md after a line was appended. A failure here must not invite a retry,
    which would record the line twice (ruling M-5)."""
    try:
        strategy_view.write_view(case)
    except Exception as exc:  # whatever the cause, the line is already recorded
        # A refusal or a failed write names its cause; any other exception is a bug, named as main
        # names one (T8-1).
        cause = str(exc) if isinstance(exc, REFUSALS + (OSError,)) else f"unexpected error {type(exc).__name__}: {exc}"
        raise Refused(f"recorded as {recorded}; the view was not rebuilt: {cause}; run bc.py view; "
                      "do not record again") from None


def cmd_register(a) -> int:
    _need_session(a.case)
    kwargs = _read_json_object(a.entry_json, "the entry file", ENTRY_KEYS)
    entry_id = register.add_entry(a.case, **kwargs)["id"]
    _rebuild_view(a.case, entry_id)
    print(entry_id)
    return 0


def cmd_condition(a) -> int:
    _need_session(a.case)
    kwargs = _read_json_object(a.condition_json, "the condition file", CONDITION_KEYS)
    condition_id = conditions.add_condition(a.case, **kwargs)["id"]
    _rebuild_view(a.case, condition_id)
    print(condition_id)
    return 0


def cmd_note(a) -> int:
    _need_session(a.case)
    kwargs = _read_json_object(a.note_json, "the note file", NOTE_KEYS)
    note_id = register.add_note(a.case, **kwargs)["id"]
    _rebuild_view(a.case, note_id)
    print(note_id)
    return 0


def cmd_mark(a) -> int:
    _need_session(a.case)
    if a.ref.startswith("SD-"):
        if a.as_status != "confirmed":
            raise Refused(ENTRY_UNSUPPORTED)
        answer = _read_text(a.answer_file, "the answer file")
        register.confirm_entry(a.case, a.ref, question=_question(a), answer=answer)
    elif a.ref.startswith("C-"):
        answer = _read_text(a.answer_file, "the answer file")
        conditions.mark_condition(a.case, a.ref, as_status=a.as_status, question=_question(a), answer=answer)
    elif a.ref.startswith("FIG-"):
        if a.as_status != "confirmed":
            raise Refused(FIGURE_UNSUPPORTED)
        answer = _read_text(a.answer_file, "the answer file")
        question = _question(a)
        _figures_whole(a.case, "mark")
        figures.confirm_figure(a.case, a.ref, question=question, answer=answer)
        print(a.ref)  # a figure is in no strategy view: nothing to rebuild
        return 0
    else:
        raise Refused(f"{a.ref!r} is not a register entry (SD-NNN), a condition (C-NNN) or a figure (FIG-NNN)")
    _rebuild_view(a.case, a.ref)
    print(a.ref)
    return 0


CANNOT_READ = "cannot_read"


def _read_proposals(path: Path) -> list:
    """The proposals file: a JSON array, from outside the case folder (the coach writes it there).
    The extractor's one failure reply, an object with exactly the key `cannot_read` holding a
    non-empty list of non-blank strings, is the refusal of the run naming the paths it could not read."""
    if judge_receipt.in_case_folder(path):
        raise Refused(f"the proposals file {path} is inside the case folder; save it outside the case")
    try:
        data = json.loads(_read_text(path, "the proposals file"))
    except json.JSONDecodeError as exc:
        raise Refused(f"the proposals file {path} is not JSON: {exc}") from None
    if isinstance(data, dict) and set(data) == {CANNOT_READ}:
        unread = data[CANNOT_READ]
        if isinstance(unread, list) and unread and all(isinstance(x, str) and x.strip() for x in unread):
            raise Refused("the figure extractor could not read: " + ", ".join(unread))
    if not isinstance(data, list):
        raise Refused(f"the proposals file {path} is not a JSON array of proposals")
    return data


def cmd_figure(a) -> int:
    """Record each proposal that passes the checks as the next FIG-NNN, `stated`. One line per
    proposal, in order; a refused proposal is a line, not an exit, so the rest are still recorded.
    A proposal's `label` (P1, P2, ...) resolves to the ID code gave it (figures.Labels). Then one
    line names the amounts the run left uncovered, if any. With --clear-refusals it only rewrites
    the refusals file to `[]`, once the session check passes, and records nothing."""
    if a.clear_refusals:  # a refused session check leaves the file as it was, unlike a run
        _need_session(a.case)
        case_files._write_json(a.case / paths.FIGURE_REFUSALS, [])
        return 0
    refused = []  # the latest run's refused proposals, or the refusal of the whole run, and the amounts
    # it left uncovered, for the handoff
    failed = True
    try:
        _need_session(a.case)
        _record_proposals(a, refused)
        failed = False
    except Exception as exc:  # any end that is not success, in the words `main` prints
        refused.append(_refusal("run", exc if isinstance(exc, REFUSALS)
                                else f"unexpected error {type(exc).__name__}: {exc}"))
        raise
    finally:  # on any end, so no older run's refusals stay
        try:
            case_files._write_json(a.case / paths.FIGURE_REFUSALS, refused)
        except OSError:
            if not failed:
                raise  # else the run's own cause stays the one reported
    return 0


def _refusal(kind: str, reason, n=None, proposal=None) -> dict:
    """One record of figure-refusals.json: a refused proposal (`kind` "proposal", with its number,
    label and line) or the refusal of the whole run (`kind` "run"). The amounts a run left uncovered
    are a record of their own (`kind` "uncovered"), written by `_record_proposals`."""
    record = {"kind": kind, "reason": " ".join(str(reason).split())}
    if kind == "proposal":
        item = proposal if isinstance(proposal, dict) else {}
        record.update(proposal=n, label=item.get("label"), line=item.get("line"))
    return record


def _record_proposals(a, refused: list) -> None:
    proposals = _read_proposals(a.proposals_file)
    _figures_whole(a.case, "figure")
    labels = figures.Labels()  # P1, P2, ... resolve to the IDs code gives, never by position
    quoted = set()  # the occurrences the refused proposals quoted: a refused proposal's line names its sentence anyway
    for n, proposal in enumerate(proposals, 1):
        try:
            fig_id = figures.record_figure(a.case, labels.resolve(proposal))["id"]
        except figures.FiguresFileRefused as exc:  # the file, not the proposal: one refusal, exit 2
            raise Refused(f"proposal {n} and any after it were not recorded: {exc}; {_remedy('figure')}") from None
        except figures.FigureRefused as exc:
            labels.done(None)
            record = _refusal("proposal", exc, n, proposal)
            refused.append(record)
            quoted |= _quoted(proposal)
            print(_clip(f"refused: proposal {n}: {record['reason']}"))
        else:
            labels.done(fig_id)
            print(fig_id)
    left = settle.left_uncovered(a.case, quoted)
    if left:
        refused.append({"kind": "uncovered", "amounts": left})
        count = "1 money amount has" if len(left) == 1 else f"{len(left)} money amounts have"
        print(f"left uncovered: {count} no recorded figure: {'; '.join(left)}")  # every amount: never clipped


def _quoted(proposal) -> set:
    """The occurrences a refused proposal quoted; a malformed quote gives none."""
    try:
        return set(figures.occurrences(proposal))
    except (KeyError, TypeError, AttributeError):
        return set()


def cmd_compute(a) -> int:
    """Write finance-view.md, the person's preview of the numbers. Never finance.json: only `brief`
    writes that (spec §6)."""
    _need_session(a.case)
    _figures_whole(a.case, "compute")
    with _repair_remedy("compute"):
        path = finance_view.write_view(a.case)
    print(path)
    return 0


def cmd_move_rubric(a) -> int:
    question = _question(a)
    reason = _read_text(a.reason_file, "the reason file")
    decision_id, already = rubric_move.move_rubric(a.case, to_version=a.to, question=question, reason=reason)
    print(f"already recorded as {decision_id}" if already else decision_id)
    return 0


def cmd_view(a) -> int:
    _need_session(a.case)
    print(strategy_view.write_view(a.case))
    return 0


def cmd_handoff(a) -> int:
    """The reporting exit: it never refuses on case content and names each problem in the handoff
    (Task 18 fix rounds 2 and 3). It refuses only when there is no case (no case.json) or no session
    was ever started. A case.json that exists but cannot be read falls back to --mode; the handoff
    names case.json, and needs_human is true."""
    try:
        case_files.read_meta(a.case)
    except case_files.CaseRefused:
        if not (a.case / paths.CASE_META).is_file():
            raise
    else:
        session = _need_session(a.case)
        if session.get("mode") != a.mode:
            raise Refused(f"--mode {a.mode} does not match session {session.get('id')}, which is "
                          f"{session.get('mode')}; give --mode {session.get('mode')}")
    print(handoff.write_handoff(a.case, mode=a.mode))
    return 0


def cmd_team_brief(a) -> int:
    """`--analyst NAME --items IDS --kind plan|results [--tier2-file FILE]` writes the analyst's next brief,
    its items in the order of work, and prints `<path> business-case:<analyst> <plan|results>`, the brief's
    reply kind last; then `waits <items>: ...` for each other item set, naming the request to make next, and
    `left out <item>: <reason>` for each item left out. `--status` lists the open team
    briefs, one line each: NNN, reply kind, agent, items, and each brief that cannot be read with the command that
    cancels it; then `held <key>: <question>` for each card held open and `last ask <key>: <question>` for each
    card whose one extra ask is due (spec §5.6). `--cancel NNN` cancels one, which frees its slot."""
    if a.analyst is None:
        given = [flag for flag, value in (("--items", a.items), ("--kind", a.kind), ("--tier2-file", a.tier2_file))
                 if value is not None]
        if given:
            raise Refused(f"{', '.join(given)} go only with --analyst")
    else:
        if a.items is None or a.kind is None:
            raise Refused("--analyst needs --items and --kind")
        with team_files.team_lock(a.case):
            return _write_team_brief(a)
    if a.cancel is not None:
        with team_files.team_lock(a.case):
            team_brief.cancel(a.case, plugin_map.load(), a.cancel)
        print(f"cancelled {a.cancel:03d}")
        return 0
    case = Path(a.case).resolve()
    lines = [f"{nnn:03d} cannot be read: {why}; " + team_files.UNREADABLE_REMEDY.format(nnn=nnn)
             for nnn, why in team_files.unreadable_briefs(case)]
    for nnn in team_files.open_briefs(case, readable_only=True):
        brief = team_files.read_brief(case / team_files.brief_relpath(nnn))
        lines.append(f"{nnn:03d} {brief.reply_kind} {brief.agent_type} {', '.join(brief.items)}".rstrip())
    lines = lines or ["no open team briefs"]
    cards = team_record.latest_cards(case)
    lines += [f"held {key}: {cards[key]['question']}" for key in team_record.held_cards(case)]
    lines += [f"last ask {key}: {cards[key]['question']}" for key in team_record.last_ask_cards(case)]
    print("\n".join(lines))
    return 0


def _write_team_brief(a) -> int:
    case = Path(a.case).resolve()
    tier2 = None
    if a.tier2_file is not None:
        try:
            tier2 = json.loads(_read_text(a.tier2_file, "the tier-2 file"))
        except json.JSONDecodeError as exc:
            raise Refused(f"the tier-2 file {a.tier2_file} is not JSON: {exc}") from None
    m = plugin_map.load()
    items = [i.strip() for i in a.items.split(",")]
    selection = team_brief.select(case, m, analyst=a.analyst, items=items, kind=a.kind)
    written = team_brief.write_briefs(case, m, analyst=a.analyst, items=items, kind=a.kind, tier2=tier2,
                                      selection=selection)
    lines = [f"{path} {team_brief.PLUGIN_PREFIX}{a.analyst} {selection.groups[0][0]}" for path in written]
    lines += [f"waits {', '.join(group)}: one brief per analyst runs at once; once this brief has its reply, ask "
              f"again with --analyst {a.analyst} --items {','.join(group)} --kind {kind}"
              for kind, group in selection.groups[1:]]
    lines += [f"left out {item}: {why}" for item, why in selection.left_out.items()]
    print("\n".join(lines))
    return 0


def cmd_team_answers(a) -> int:
    """`--answers-file FILE` records the card answers in it, then applies the after-cap rule to each item set
    whose second-brief plan caps in this call (spec §5.6); prints the card record's path, the answers
    file's path, `open <key>` for each card still open, then each new run: its route's `subagent_type: ...`
    and `plugin-run` block, and any line for the person. `--case-card FILE` and `--gap-card ITEM` make one
    card code asks, and print its key. The whole command holds the team lock."""
    with team_files.team_lock(a.case):
        return _team_answers(a)


def _team_answers(a) -> int:
    if a.case_card is not None:
        print(team_record.case_card(a.case, a.case_card))
        return 0
    if a.gap_card is not None:
        print(team_record.gap_card(a.case, a.gap_card))
        return 0
    data = _read_json_object(a.answers_file, "the answers file", (("answers",), ()))
    m = plugin_map.load()
    call = team_record.record_call(a.case, m, data["answers"])
    team_record.apply_after_cap(a.case, m, call)
    case = Path(a.case).resolve()
    lines = [str(case / team_files.cards_relpath(call.nnn)), str(case / team_files.answers_relpath(call.nnn))]
    lines += [f"open {key}" for key in team_record.open_cards(a.case)]
    lines += team_runs.render(team_runs.blocks_for_call(a.case, m, call))
    print("\n".join(lines))
    return 0


def _run_line(run: dict) -> str:
    tail = run.get("result_file") or (run.get("reason") if run.get("state") == "gap" else "") or ""
    if run.get("refused"):
        tail = f"refused: {run['refused']}"
    return f"{run['state']} {run['key']} {run['command']} {tail}".rstrip()


def cmd_team_run(a) -> int:
    """`--done RUN_ID` records the run as ended with its result file, or as a gap; `--fail KEY` records a run
    or a person-run entry as a gap; `--status` ends each open run whose file now exists. Each prints one line
    per run: state, key, command, then the result file or the gap's reason. The whole command holds the team
    lock."""
    with team_files.team_lock(a.case):
        return _team_run(a)


def _team_run(a) -> int:
    if a.done is not None:
        runs = [team_runs.done(a.case, a.done)]
    elif a.fail is not None:
        runs = [team_runs.fail(a.case, a.fail)]
    else:
        runs = team_runs.status(a.case)
    print("\n".join(_run_line(r) for r in runs) if runs else "no open runs")
    return 0


def cmd_team_reply(a) -> int:
    """`--check REPLY_PATH` checks an analyst's reply against its brief; prints the check file's path."""
    print(team_reply.check_reply(a.case, a.check, plugin_map.load()))
    return 0


def cmd_installs(a) -> int:
    """Each map plugin's install state as this session's working directory sees it, one line each: name,
    state, then the install path when there is one. `--json` prints the whole result as one object."""
    result = install_check.check(plugin_map.load(), config_dir=install_check.config_dir(), cwd=Path.cwd(),
                                 managed=install_check.default_managed_path())
    if a.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("\n".join(f"{name} {v['state']} {v['install_path'] or ''}".rstrip() for name, v in result.items()))
    return 0


def cmd_temp_dir(a) -> int:
    """The temporary directory, one line: the coach writes its text files there. It names the folder so
    no command needs a shell default such as `${TMPDIR:-/tmp}`, which always asks for approval."""
    print(tempfile.gettempdir())
    return 0


# -- the parser --------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--case", required=True, type=_case_arg, metavar="DIR",
                        help="the case folder, <repo>/business-cases/{slug}")
    parser = _Parser(prog="bc.py", description="The business-case CLI.")
    subs = parser.add_subparsers(dest="command", required=True, metavar="SUBCOMMAND")

    def sub(name, func, help_text):
        p = subs.add_parser(name, parents=[common], help=help_text, description=help_text)
        p.set_defaults(func=func)
        return p

    p = sub("init", cmd_init, "Create a case folder and its starting files.")
    p.add_argument("--slug", required=True)
    p.add_argument("--offering", required=True)
    p.add_argument("--market", required=True, choices=rubric.MARKETS)
    p.add_argument("--rubric-version", default=None,
                   help="the rubric version; with none, the newest rubric that ships")

    p = sub("session", cmd_session, "Start a session: a named person, or an automated run with none.")
    p.add_argument("--id", required=True, help="the Claude Code session ID")
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--name", help="the person in this session")
    who.add_argument("--automated", action="store_true", help="an automated run; it records no decision")

    p = sub("ingest", cmd_ingest, "Keep a proposal or strategy as given, once.")
    p.add_argument("--kind", required=True, choices=("proposal", "strategy"))
    p.add_argument("--file", required=True, type=Path)
    p.add_argument("--text-file", type=Path, help="the UTF-8 text of a file that is not UTF-8")

    p = sub("change", cmd_change, "Replace one section of business-case.md and log the change.")
    p.add_argument("--section", required=True)
    p.add_argument("--body-file", required=True, type=Path, help="the new section body, kept exactly")
    p.add_argument("--summary", required=True)
    p.add_argument("--source", required=True)

    p = sub("ledger", cmd_ledger, "Set the coach's class, evidence and note for one item.")
    p.add_argument("--item", required=True)
    p.add_argument("--class", dest="coach_class", required=True, choices=ledger.COACH_CLASSES)
    p.add_argument("--evidence", action="append", default=[], metavar="EV")
    p.add_argument("--note", default="")

    p = sub("evidence", cmd_evidence, "Write an evidence page; prints its EV-NNN.")
    page = p.add_mutually_exclusive_group(required=True)
    page.add_argument("--page-json", type=Path)
    page.add_argument("--from-result", type=Path, metavar="FILE",
                      help="a plugin's result file, or an analyst's checked team/reply-NNN.json")
    p.add_argument("--result-id", metavar="ID", help="with --from-result: the result to page")
    p.add_argument("--grade", choices=evidence.GRADES, help="with --from-result: the grade the person confirmed")
    p.add_argument("--items", metavar="IDS", help="with --from-result: the rubric item IDs, comma separated")

    p = sub("decide", cmd_decide, "Record one decision, in the current session person's name.")
    # Ruling P3-44: only `move-rubric` writes a move_rubric decision, after it moved the files.
    p.add_argument("--kind", required=True,
                   choices=tuple(k for k in decision_record.KINDS if k != decision_record.MOVE_KIND))
    p.add_argument("--role", required=True, choices=decision_record.ROLES)
    _add_question(p)
    p.add_argument("--option", action="append", required=True)
    p.add_argument("--choice", required=True)
    p.add_argument("--reason-file", required=True, type=Path, help="the person's reason, kept verbatim")
    p.add_argument("--subject-type", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--item")
    p.add_argument("--shown", action="append", default=[])
    p.add_argument("--cite", action="append", default=[], metavar="RELPATH")

    sub("brief", cmd_brief, "Write the next judge brief; prints its path. Counts one judge run.")

    p = sub("save-report", cmd_save_report, "Validate the judge's reply to a brief and save the report.")
    p.add_argument("--brief", required=True, type=Path)
    p.add_argument("--coach-copy", type=Path, metavar="FILE",
                   help="the fallback: a copy of the judge's JSON, saved as a coach copy that cannot end the loop")

    p = sub("status", cmd_status, "Print the loop status; exit 0 when done, 1 when not.")
    p.add_argument("--json", action="store_true")

    p = sub("items", cmd_items, "Print each applicable item with its title, coach class and state.")
    p.add_argument("--json", action="store_true")

    p = sub("register", cmd_register, "Record one strategic decision as the next SD-NNN; prints its ID.")
    p.add_argument("--entry-json", required=True, type=Path,
                   help="category, choice, rejected_alternative, evidence, source; optional supersedes, "
                        "reason, change_source")

    p = sub("condition", cmd_condition, "Record one condition on a register entry as the next C-NNN; prints its ID.")
    p.add_argument("--condition-json", required=True, type=Path,
                   help="text, supports, evidence, source; optional supersedes, reason, change_source")

    p = sub("note", cmd_note, "Record a claim that fails the four-part test as the next N-NNN; prints its ID.")
    p.add_argument("--note-json", required=True, type=Path, help="text, source, failed_tests, reason")

    p = sub("mark", cmd_mark, "Record the person's answer: confirm an entry or a figure, or mark a condition.")
    p.add_argument("--ref", required=True, help="SD-NNN, C-NNN or FIG-NNN")
    p.add_argument("--as", dest="as_status", required=True, choices=conditions.MARKS)
    _add_question(p)
    p.add_argument("--answer-file", required=True, type=Path, help="the person's answer, kept verbatim")

    sub("view", cmd_view, "Rewrite strategy-view.md from the register; prints its path.")

    p = sub("figure", cmd_figure, "Record each proposed figure that passes the checks; prints one line per proposal, "
                                  "then one naming the amounts left uncovered.")
    run = p.add_mutually_exclusive_group(required=True)
    run.add_argument("--proposals-file", type=Path,
                     help="a JSON array of proposed figures, saved outside the case folder; a later "
                          "proposal names an earlier one by its label (P1, P2, ...)")
    run.add_argument("--clear-refusals", action="store_true",
                     help="rewrite the refusals file to an empty list; records nothing")

    sub("compute", cmd_compute, "Rewrite finance-view.md from the financial figures file; prints its path.")

    p = sub("move-rubric", cmd_move_rubric, "Move the case to a newer rubric version; prints the decision ID.")
    p.add_argument("--to", required=True, metavar="VERSION")
    _add_question(p)
    p.add_argument("--reason-file", required=True, type=Path, help="the person's reason, kept verbatim")

    p = sub("team-brief", cmd_team_brief, "Write an analyst's plan or results brief; list the open team briefs, "
                                          "or cancel one.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--status", action="store_true", help="list the open briefs")
    mode.add_argument("--cancel", type=int, metavar="NNN", help="cancel brief NNN; it frees its slot")
    mode.add_argument("--analyst", metavar="NAME", help="write a brief for this analyst, e.g. case-pricing-analyst")
    p.add_argument("--items", metavar="IDS", help="with --analyst: the rubric item IDs, comma separated")
    p.add_argument("--kind", choices=("plan", "results"), help="with --analyst: the reply the brief asks for")
    p.add_argument("--tier2-file", type=Path, metavar="FILE",
                   help='with --analyst: the coach\'s temp file, {"candidates": [{"name", "description"}], '
                        '"outputs": ["<absolute path>"]}')

    p = sub("team-reply", cmd_team_reply, "Check an analyst's reply; prints the check file's path.")
    p.add_argument("--check", required=True, type=Path, metavar="REPLY_PATH",
                   help="the analyst's team/reply-NNN.json")

    p = sub("team-answers", cmd_team_answers, "Record the person's card answers; writes the card record and the answers file.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--answers-file", type=Path, metavar="FILE",
                      help='the coach\'s temp file: {"answers": [{"key": "<brief NNN>:<id>" | "code:<n>", "answer": "<text>"}]}')
    mode.add_argument("--case-card", type=Path, metavar="FILE",
                      help="make a case card for a result file with no run.case; prints its key")
    mode.add_argument("--gap-card", metavar="ITEM", help="make a gap card for an item with no result yet; prints its key")

    p = sub("team-run", cmd_team_run, "Record a route run as ended, or as a gap; or list the open runs.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--done", metavar="RUN_ID", help="the route's dispatch has ended: find its result file by run_id")
    mode.add_argument("--fail", metavar="KEY", help="record the run, or the person-run entry, as a gap")
    mode.add_argument("--status", action="store_true",
                      help="end each open run whose result file now exists; list the runs still open")

    p = sub("installs", cmd_installs, "Report each map plugin's install state.")
    p.add_argument("--json", action="store_true")

    p = sub("handoff", cmd_handoff, "Write business-case-handoff.json; prints its path.")
    p.add_argument("--mode", required=True, choices=handoff.MODES)

    help_text = "Print the temporary directory the coach writes its text files to."
    p = subs.add_parser("temp-dir", help=help_text, description=help_text)
    p.set_defaults(func=cmd_temp_dir)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except REFUSALS as exc:
        reason = str(exc)
    except Exception as exc:  # the exit code is a contract: a crash is not "not done"
        reason = f"unexpected error {type(exc).__name__}: {exc}"
    _refuse(reason)
    return 2


if __name__ == "__main__":
    sys.exit(main())
