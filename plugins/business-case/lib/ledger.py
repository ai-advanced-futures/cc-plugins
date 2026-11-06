"""The item ledger: the coach's own record of each applicable rubric item.

Spec §4. The coach classes an item as present_factual, present_weak or missing. "met" is not a
coach class: only the judge makes an item met, so the ledger has no way to say it.
"""
from __future__ import annotations

import json
from pathlib import Path

# `evidence` is also set_entry's argument name, so the module is imported under another name.
from lib import case_files, paths
from lib import evidence as evidence_pages

COACH_CLASSES = ("present_factual", "present_weak", "missing")

# ledger.json is replaced whole on each write, so a lock on it would not survive the rename.
# Every read-modify-write of it runs under chained_log's lock on decisions.jsonl, which is only
# ever appended to: bc.py's `ledger` takes it around set_entry, and write_decision holds it through
# add_decision_ref. This module does not import chained_log: it sits inside the fail-closed hook's
# import closure, which keeps the strategy modules out (ruling PF-12). On macOS and Linux only;
# without fcntl, chained_log takes no lock.
CASE_LOCK = paths.DECISIONS


class LedgerRefused(ValueError):
    """A ledger change the rules refuse."""


def _blank_entry() -> dict:
    return {"coach_class": "missing", "evidence": [], "decisions": [], "note": ""}


def read_ledger(case_dir: Path) -> dict:
    path = Path(case_dir) / paths.LEDGER
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LedgerRefused(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LedgerRefused(f"{path} is not a JSON object")
    return data


def init_ledger(case_dir: Path) -> None:
    """Write one `missing` entry per applicable item. Refuses a ledger that already has entries."""
    case_dir = Path(case_dir)
    path = case_dir / paths.LEDGER
    # A crash between this write and case.json leaves a pristine ledger; a retry may start it over.
    if paths.stat_exists(path) and any(e != _blank_entry() for e in read_ledger(case_dir).values()):
        raise LedgerRefused(f"{path} already has coach entries; it is not started over")
    try:
        items = case_files.applicable_items(case_dir)
    except (OSError, ValueError) as exc:  # CaseRefused and RubricError are ValueErrors
        raise LedgerRefused(f"cannot work out the applicable items: {exc}") from exc
    case_files._write_json(path, {i["id"]: _blank_entry() for i in items})


def _entry(ledger_data: dict, item_id) -> dict:
    if not isinstance(item_id, str) or item_id not in ledger_data:
        raise LedgerRefused(f"{item_id!r} is not an applicable item of this case")
    entry = ledger_data[item_id]
    if not isinstance(entry, dict) or not isinstance(entry.get("decisions"), list):
        raise LedgerRefused(f"the ledger entry for {item_id} is malformed; it needs a decisions list")
    return entry


def set_entry(case_dir: Path, item_id: str, *, coach_class: str, evidence: list = (), note: str = "") -> dict:
    """Set the coach's class, evidence IDs and note for one item. Decision refs already on the
    entry are kept. Returns the new entry."""
    if coach_class not in COACH_CLASSES:
        raise LedgerRefused(f"coach_class {coach_class!r} is not one of {', '.join(COACH_CLASSES)}; "
                            "only the judge makes an item met")
    if not isinstance(note, str):
        raise LedgerRefused("the note is a string")
    case_dir = Path(case_dir)
    data = read_ledger(case_dir)
    old = _entry(data, item_id)
    if not isinstance(evidence, (list, tuple)):
        raise LedgerRefused("evidence is a list of evidence IDs")
    ids = list(evidence)
    for ev_id in ids:
        try:
            exists = evidence_pages.page_path(case_dir, ev_id).is_file()
        except evidence_pages.EvidenceRefused as exc:
            raise LedgerRefused(str(exc)) from exc
        if not exists:
            raise LedgerRefused(f"evidence page {ev_id} does not exist")
    data[item_id] = {"coach_class": coach_class, "evidence": ids, "decisions": old["decisions"], "note": note}
    case_files._write_json(case_dir / paths.LEDGER, data)
    return data[item_id]


def add_items(case_dir: Path, item_ids) -> None:
    """Add a blank `missing` entry for each item ID not yet in ledger.json; entries already there
    are kept as they are. A rubric move calls it for the new version's applicable items, and the
    caller holds the CASE_LOCK."""
    case_dir = Path(case_dir)
    data = read_ledger(case_dir)
    new = [i for i in item_ids if i not in data]
    if not new:
        return
    for item_id in new:
        if not isinstance(item_id, str) or item_id.strip() == "":
            raise LedgerRefused(f"{item_id!r} is not an item ID")
        data[item_id] = _blank_entry()
    case_files._write_json(case_dir / paths.LEDGER, data)


def add_decision_ref(case_dir: Path, item_id: str, decision_id: str) -> None:
    """Append a decision's ID to an item's entry. The caller holds the CASE_LOCK: write_decision,
    the only caller, holds it from numbering the decision to here."""
    if not isinstance(decision_id, str) or decision_id.strip() == "":
        raise LedgerRefused("the decision ID is blank")
    case_dir = Path(case_dir)
    data = read_ledger(case_dir)
    _entry(data, item_id)["decisions"].append(decision_id.strip())
    case_files._write_json(case_dir / paths.LEDGER, data)
