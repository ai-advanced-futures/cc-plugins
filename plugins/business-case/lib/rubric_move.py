"""Moving a case to a newer rubric version (plan 3 spec §7 "Moving a case").

A case stays on the rubric version it was created with until the person moves it. The move:
0. refuses unless the session has a named person, and checks the decision's own fields;
1. refuses a version that does not ship, an older one, and the current one, unless an earlier move
   to it stopped before its decision was written;
2. copies the rubric, then updates scope.json, then case.json, then adds a ledger entry for each
   new applicable item, under the decisions lock (ledger.CASE_LOCK);
3. releases the lock and writes the funder's `move_rubric` decision LAST. write_decision takes the
   same lock, and a second flock on another descriptor in one process blocks.

The decision is the record that the move is finished. A run that stopped before it is completed by
running the command again; a finished move returns its decision and writes nothing.

"Current" is scope.json's version, the judge's input, which step 2 writes before case.json. A move
is unfinished when the target equals the current version, differs from the version the case was
created on, and no counted move_rubric decision cites today's rubric.json.

Two moves run at once may both write a decision (the second's step 1 ran before the first's step 3);
both are equal, and _finished_move reads the latest. Every OSError in steps 2 and 3 is a MoveRefused.

No lock here nests with the figures lock: the move never touches figures.jsonl (Task 13 carry).
"""
from __future__ import annotations

from pathlib import Path

from lib import case_files, chained_log, decision_record, digest, ledger, paths, rubric

FIRST_VERSION = "1.0.0"  # a case with no created_rubric_version was created on it (before 0.3.0)


class MoveRefused(ValueError):
    """A rubric move the rules refuse. Nothing is written."""


def _created_version(meta: dict) -> str:
    return meta.get("created_rubric_version") or FIRST_VERSION


def _finished_move(case_dir: Path) -> "str | None":
    """The ID of the latest counted move_rubric decision that cites today's rubric.json, or None."""
    try:
        records = decision_record.read_decisions(case_dir)
        today = digest.file_digest(case_dir / paths.RUBRIC_COPY)
    except (decision_record.DecisionRefused, OSError) as exc:
        raise MoveRefused(f"cannot read the recorded decisions: {exc}") from exc
    found = None
    for record in records:
        if record.get("kind") != decision_record.MOVE_KIND:
            continue
        try:
            decision_record.check_recorded(case_dir, record)
        except decision_record.DecisionRefused:
            continue
        if record["cited"].get(paths.RUBRIC_COPY) == today:
            found = record["id"]
    return found


def _check_version(case_dir: Path, to_version: str) -> "str | None":
    """Step 1. None for a move to make; the decision ID for a finished move. Refuses the rest."""
    try:
        target = rubric.version_key(to_version)
    except rubric.RubricError:
        raise MoveRefused(f"{to_version!r} is not a rubric version; give one that ships: "
                          f"{', '.join(rubric.shipped_versions())}") from None
    if to_version not in rubric.shipped_versions():
        raise MoveRefused(f"rubric {to_version} does not ship with this plugin; the versions that ship are "
                          f"{', '.join(rubric.shipped_versions())}")
    try:
        current = case_files.read_scope(case_dir).get("rubric_version")
        created = _created_version(case_files.read_meta(case_dir))
        current_key = rubric.version_key(current)
    except (case_files.CaseRefused, rubric.RubricError) as exc:
        raise MoveRefused(f"cannot read the case's rubric version: {exc}") from exc
    if target < current_key:
        raise MoveRefused(f"rubric {to_version} is older than the case's rubric {current}; a case never moves back")
    if target > current_key:
        return None
    finished = _finished_move(case_dir)
    if finished is not None:
        return finished
    if to_version == created:
        raise MoveRefused(f"the case is already on rubric {to_version}, the version it was created with; "
                          "there is no move to make")
    return None  # an earlier move to this version stopped before its decision: complete it


def _move_files(case_dir: Path, to_version: str) -> None:
    """Step 2: the rubric copy, scope.json, case.json, then the ledger, in that order. Each write is
    atomic, so a re-run after a stop finds every file whole."""
    source = rubric.shipped_rubric_path(to_version)
    try:
        data = rubric.load_rubric(source)
        scope = case_files.read_scope(case_dir)
        items = sorted(i["id"] for i in rubric.applicable_items(data, scope["market"]))
        case_files._atomic_write(case_dir / paths.RUBRIC_COPY, source.read_bytes())
        case_files._write_json(case_dir / paths.SCOPE, dict(scope, rubric_version=to_version,
                                                            applicable_item_ids=items))
        meta = case_files.read_meta(case_dir)
        meta.setdefault("created_rubric_version", FIRST_VERSION)
        meta["rubric_version"] = to_version
        case_files.write_meta(case_dir, meta)
        ledger.add_items(case_dir, items)
    except (rubric.RubricError, case_files.CaseRefused, ledger.LedgerRefused, OSError) as exc:
        raise MoveRefused(f"cannot move the case's files to rubric {to_version}: {exc}; "
                          "repair the cause, then run the move again to complete it") from exc


def move_rubric(case_dir, *, to_version: str, question: str, reason: str) -> tuple:
    """Move the case to `to_version`. Returns (decision ID, True when the move was already recorded)."""
    case_dir = Path(case_dir)
    try:
        case_files.current_name(case_dir)
    except case_files.CaseRefused as exc:
        raise MoveRefused(f"a rubric move is the funder's decision and needs a named person: {exc}") from exc
    kind = decision_record.MOVE_KIND
    options = list(decision_record.MOVE_OPTIONS)
    try:
        decision_record._check_fields(kind, "funder", "case", question, reason, options, kind, [])
    except decision_record.DecisionRefused as exc:
        raise MoveRefused(str(exc)) from exc

    # Steps 1 and 2 under the decisions lock, so two moves never interleave their writes. The lock
    # is released before step 3: write_decision takes it again.
    with chained_log.locked_append(case_dir / ledger.CASE_LOCK, MoveRefused):
        finished = _check_version(case_dir, to_version)
        if finished is not None:
            return finished, True
        old = case_files.read_scope(case_dir).get("rubric_version")
        _move_files(case_dir, to_version)

    slug = case_files.read_meta(case_dir).get("slug")
    shown = [f"Move from rubric {old} to rubric {to_version}"] if old != to_version else [
        f"Finish the move to rubric {to_version}"]
    try:
        record = decision_record.write_decision(
            case_dir, kind=kind, role="funder", question=question, options=options, shown=shown, choice=kind,
            reason=reason, subject_type="case", subject_ref=slug, item_id=None, cite=[paths.RUBRIC_COPY])
    except (decision_record.DecisionRefused, OSError) as exc:  # never a traceback (fix round 1)
        raise MoveRefused(f"the case's files moved to rubric {to_version}, but the decision was not "
                          f"recorded: {exc}; run the move again to complete it") from exc
    return record["id"], False
