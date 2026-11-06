"""Evidence pages from a plugin's result file, or from a result in an analyst's checked reply (spec §5.7):
`bc.py evidence --from-result FILE --result-id ID --grade G --items IDS`.

Code fills every field of the page but its grade and its items:

- `source`: `"<command>, result <id>"`; for an analyst's reply the command is its brief, `brief NNN`;
- `summary`: the result's label, then the `ref` of each source, its own and every cited result's;
- `method`: the result's own;
- `result_ref`: `{"path", "sha256"}` of the file, the path relative to the git root;
- `supplied_by` and `grade_confirmed_by`: the session's named person;
- `produced_by_plugin`: the file's `plugin`; `business-case` for a reply, set by code, never read from it;
- `off_map`: true for a reply result with no `cites`, false for a plugin's file and a citing reply result;
- `date`: the oldest dated source, counting every cited result's sources, with `YYYY` read as
  `YYYY-01-01` and `YYYY-MM` as `YYYY-MM-01`; with none, the date of `run.finished_at`.

The ceiling is the most the page can be graded: the weakest source of the result (`source_ceiling`),
lowered by the map's ceiling for the file's command and the result's kind, and by the ceiling of every
cited result, followed through their own cites. A reply result that cites no plugin result (`off_map`) is
capped at `secondary` (OFF_MAP_CEILING). A cited result from an unmapped file (`unmapped`: its command is
not a map command, or not its plugin's) caps the page at `estimated` (UNMAPPED_CEILING); such a file is
refused as the direct file. A grade above the ceiling is
refused, never lowered.

A plugin's file must lie inside the git root, pass the checker and the file name rule, come from at least
the map's `min_version` of its plugin, and pass the case rule (`team_reply.case_rule_problem`); so must
every cited file. A source date that names no real day is refused. A reply must have a receipt
(`team_guard.verify_analyst_receipt`) and a check record (`team_reply.read_check`) whose sha256 is the
reply's own; a plan reply is refused, since a plan's results never become a page. Each file the reply's
result cites must still have the sha256 its check record holds. At write time every file read is hashed
again, and the page is refused when one has changed.

Imported only by bc.py: `evidence` sits in the hook's import closure, and this module imports
`team_reply`, which brings `plugin_result` and `plugin_map` with it."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from lib import (
    case_files,
    digest,
    evidence,
    judge_receipt,
    paths,
    plugin_map,
    plugin_result,
    team_files,
    team_guard,
    team_reply,
)
from lib.evidence import EvidenceRefused

GRADE_ORDER = ("estimated", "secondary", "primary")
# The most a source of each type can support (spec §5.7).
SOURCE_CEILINGS = {"default": "estimated", "model": "estimated", "person": "estimated",
                   "published": "secondary", "customer_data": "primary"}

_REPLY_NAME = re.compile(r"^reply-([0-9]{3}|[1-9][0-9]{3,})\.json$")
_YEAR = re.compile(r"^[0-9]{4}$")
_MONTH = re.compile(r"^[0-9]{4}-[0-9]{2}$")
# The most an analyst's reply result that cites no plugin result can be graded (ruling M-4): its source
# types are the analyst's own word, so primary needs a cited plugin result or the person's own page.
OFF_MAP_CEILING = "secondary"
# The most a cited result from an unmapped file can support: no version or ceiling is known for it.
UNMAPPED_CEILING = "estimated"


@dataclass
class _File:
    rel: str  # relative to the git root
    sha256: str
    doc: dict


def _lowest(grades) -> str:
    return min(grades, key=GRADE_ORDER.index)


def source_ceiling(result) -> str:
    """The weakest source's ceiling; `estimated` for a result that rests on a default or has no source."""
    if result.get("rests_on_default"):
        return "estimated"
    grades = [SOURCE_CEILINGS.get(s.get("type"), "estimated") for s in result.get("sources") or []]
    return _lowest(grades) if grades else "estimated"


def result_ceiling(m, doc, result, *, cited=()) -> str:
    """The most a page of `result` (in the file `doc`) can be graded: its source ceiling, the map's
    ceiling for the file's command and the result's kind, and the ceiling of each `(doc, result)` in
    `cited`, whichever is lowest."""
    grades = [source_ceiling(result)]
    capped = plugin_map.ceiling(m, doc.get("command"), result.get("kind"))
    if capped is not None:
        grades.append(capped)
    grades += [result_ceiling(m, d, r) for d, r in cited]
    return _lowest(grades)


# -- reading files --------------------------------------------------------------------------------

def _bytes(root: Path, target: Path, what: str):
    """(rel, data) of a file inside the git root, or EvidenceRefused."""
    rel = team_files.inside_root(root, target)
    if rel is None:
        raise EvidenceRefused(f"{what} {target} is not a path inside the git root {root}")
    try:
        return rel, (root / rel).read_bytes()
    except OSError as exc:
        raise EvidenceRefused(f"{what} {rel} cannot be read: {exc.strerror or exc}") from None


def _json(data: bytes, rel: str):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise EvidenceRefused(f"{rel} is not JSON") from None


def unmapped(m, doc) -> bool:
    """True when the map knows no version or ceiling for this file: its `command` is not a map command,
    or the part of its `command` before the first `:` is not its `plugin`."""
    command, plugin = doc.get("command"), doc.get("plugin")
    return (not isinstance(command, str) or command not in plugin_map.commands(m)
            or command.split(":", 1)[0] != plugin)


def _version(text) -> tuple:
    return tuple(int(part) for part in text.split("."))


def _result_file(case: Path, root: Path, m, target: Path, what: str) -> _File:
    """A plugin's result file that passes the checker, the name rule, the map's min_version for a map
    plugin, and the case rule."""
    rel, data = _bytes(root, target, what)
    doc = _json(data, rel)
    errors = plugin_result.check_result(doc)
    if not errors:
        errors = plugin_result.check_result_file(root / rel)
    if errors:
        raise EvidenceRefused(f"{what} {rel} fails the checker: " + "; ".join(errors))
    plugin = doc["plugin"]
    if plugin in m.get("plugins", {}):
        least = plugin_map.min_version(m, plugin)
        if _version(doc["plugin_version"]) < _version(least):
            raise EvidenceRefused(f"{what} {rel} comes from {plugin} {doc['plugin_version']}, older than {least}, "
                                  "the oldest version the plugin map accepts; run the command again")
    problem = team_reply.case_rule_problem(case, doc, root / rel)
    if problem is not None:
        raise EvidenceRefused(f"{what} {rel} does not serve this case: {problem}")
    return _File(rel, digest.sha256_hex(data), doc)


def _result(file: _File, result_id) -> dict:
    for result in file.doc.get("results") or []:
        if isinstance(result, dict) and result.get("id") == result_id:
            return result
    raise EvidenceRefused(f"{file.rel} holds no result {result_id}")


def _cited(case: Path, root: Path, m, result: dict, out: list, seen: set, record=None) -> None:
    """Append (file, result) for every result `result` cites, then for theirs. `record` maps each
    file the reply's check record holds to its sha256; a first-level cited file must match it."""
    for entry in result.get("cites") or []:
        text = entry.get("file") if isinstance(entry, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise EvidenceRefused(f"result {result.get('id')} has a cites entry with no file")
        target = Path(text) if Path(text).is_absolute() else root / text
        file = _result_file(case, root, m, target, "the cited file")
        if record is not None and record.get(file.rel) != file.sha256:
            raise EvidenceRefused(f"the cited file {file.rel} is not the file team-reply --check recorded; "
                                  "check the reply again")
        cited = _result(file, entry.get("result_id"))
        key = (file.rel, cited["id"])
        if key in seen:
            continue
        seen.add(key)
        out.append((file, cited))
        _cited(case, root, m, cited, out, seen)


def _reply_slot(case: Path, target: Path):
    """NNN when target is this case's team/reply-NNN.json once resolved, else None."""
    resolved = target.resolve()
    match = _REPLY_NAME.match(resolved.name)
    return int(match.group(1)) if match and resolved.parent == case / paths.TEAM_DIR else None


def _reply(case: Path, root: Path, nnn: int):
    """(file, check record) for an analyst's checked results reply."""
    try:
        team_guard.verify_analyst_receipt(case, nnn)
    except judge_receipt.ReceiptRefused as exc:
        raise EvidenceRefused(f"{team_files.reply_relpath(nnn)} is refused: {exc}") from None
    try:
        record = team_reply.read_check(case, nnn)
    except team_files.TeamRefused as exc:
        raise EvidenceRefused(str(exc)) from None
    rel, data = _bytes(root, case / team_files.reply_relpath(nnn), "the reply")
    sha = digest.sha256_hex(data)
    if record.get("reply") != team_files.reply_relpath(nnn) or record.get("reply_sha256") != sha:
        raise EvidenceRefused(f"the sha256 of {team_files.reply_relpath(nnn)} differs from its check record "
                              f"{team_files.check_relpath(nnn)}; check the reply again")
    doc = _json(data, rel)
    if record.get("kind") != "results" or not isinstance(doc, dict) or "schema" not in doc:
        raise EvidenceRefused(f"{team_files.reply_relpath(nnn)} is a plan reply; a plan's results never "
                              "become an evidence page")
    cited = record.get("cited")
    return _File(rel, sha, doc), cited if isinstance(cited, dict) else {}


# -- the page -------------------------------------------------------------------------------------

def _full_date(text, rel: str, result_id):
    """A source date as a date, its period's first day for `YYYY` or `YYYY-MM`; None when undated (null).
    A date string that names no real day (`2025-13`, `2025-02-30`) is refused, never read as undated: a
    page must never look newer than its source."""
    if text is None:
        return None
    full = text
    if isinstance(text, str) and _YEAR.match(text):
        full = text + "-01-01"
    elif isinstance(text, str) and _MONTH.match(text):
        full = text + "-01"
    try:
        return date.fromisoformat(full)
    except (TypeError, ValueError):
        raise EvidenceRefused(f"{rel} result {result_id} has a source dated {text!r}, which is no real date; "
                              "correct the result file") from None


def _page_date(doc: dict, results: list) -> str:
    """`results` holds (file rel, result) pairs."""
    dated = [d for rel, r in results for s in r.get("sources") or []
             if (d := _full_date(s.get("date"), rel, r.get("id"))) is not None]
    if dated:
        return min(dated).isoformat()
    return doc["run"]["finished_at"][:10]


def _summary(result: dict, results: list) -> str:
    refs = list(dict.fromkeys(s["ref"] for r in results for s in r.get("sources") or []))
    return f"{result.get('label', '')}. Sources: " + "; ".join(refs)


def _build(case_dir, m, path, result_id, grade, items):
    """(page, {rel: sha256} of every file read)."""
    case = Path(case_dir).resolve()
    root = team_files.repo_root(case)
    target = Path(path)
    nnn = _reply_slot(case, target)
    if nnn is not None:
        file, record = _reply(case, root, nnn)
        command, off_map, plugin = f"brief {nnn:03d}", None, "business-case"
    else:
        file, record = _result_file(case, root, m, target, "the result file"), None
        if unmapped(m, file.doc):
            raise EvidenceRefused(f"the result file {file.rel} comes from {file.doc['plugin']}'s command "
                                  f"{file.doc['command']}, which is not on the plugin map for that plugin; a page is "
                                  "built only from a map command's result or an analyst's reply")
        command, off_map, plugin = file.doc["command"], False, file.doc["plugin"]
    result = _result(file, result_id)
    if off_map is None:
        off_map = not result.get("cites")
    cited = []
    _cited(case, root, m, result, cited, set(), record)
    if grade not in GRADE_ORDER:
        raise EvidenceRefused(f"the grade {grade!r} is not one of {', '.join(GRADE_ORDER)}")
    ceiling = result_ceiling(m, file.doc, result, cited=[(f.doc, r) for f, r in cited])
    if off_map:
        ceiling = _lowest([ceiling, OFF_MAP_CEILING])
    if any(unmapped(m, f.doc) for f, _ in cited):
        ceiling = _lowest([ceiling, UNMAPPED_CEILING])
    if GRADE_ORDER.index(grade) > GRADE_ORDER.index(ceiling):
        raise EvidenceRefused(f"the grade {grade} is above {ceiling}, the most the sources of {file.rel} result "
                              f"{result_id} allow; a grade above the ceiling is refused, never lowered")
    person = case_files.current_name(case)
    every = [result] + [r for _, r in cited]
    page = {"source": f"{command}, result {result_id}",
            "date": _page_date(file.doc, [(file.rel, result)] + [(f.rel, r) for f, r in cited]),
            "method": result["method"], "grade": grade, "grade_confirmed_by": person, "supplied_by": person,
            "produced_by_plugin": plugin, "off_map": off_map, "item_ids": list(items),
            "summary": _summary(result, every), "result_ref": {"path": file.rel, "sha256": file.sha256}}
    hashes = {file.rel: file.sha256}
    hashes.update({f.rel: f.sha256 for f, _ in cited})
    return page, hashes


def page_from_result(case_dir, m, path, result_id, grade, items) -> dict:
    """The page for `result_id` in the file at `path`, every check passed; writes nothing."""
    return _build(case_dir, m, path, result_id, grade, items)[0]


def write_page_from_result(case_dir, m, path, result_id, grade, items) -> str:
    """Build the page, hash every file it read again, and write it through evidence.write_page.
    Returns its EV-NNN."""
    page, hashes = _build(case_dir, m, path, result_id, grade, items)
    root = team_files.repo_root(Path(case_dir).resolve())
    for rel, sha in hashes.items():
        try:
            now = digest.sha256_hex((root / rel).read_bytes())
        except OSError:
            now = None
        if now != sha:
            raise EvidenceRefused(f"{rel} changed while its page was built; build the page again")
    same = _same_page(case_dir, page)
    if same is not None:
        raise EvidenceRefused(f"{same} is already the page of {page['source']} in {page['result_ref']['path']} "
                              f"for {', '.join(page['item_ids'])}; use {same}, and write no second page")
    return evidence.write_page(case_dir, page)


def _same_page(case_dir, page: dict):
    """The EV-NNN of a page already built from the same result (file path and sha256, source) for the same
    items, or None (final review M1). A page that cannot be read is not a match."""
    folder = Path(case_dir) / paths.EVIDENCE_DIR
    want = (page["result_ref"], page["source"], sorted(page["item_ids"]))
    for path in sorted(folder.glob("EV-*.json")) if paths.stat_is_dir(folder) else []:
        try:
            old = evidence.read_page(case_dir, path.stem)
        except EvidenceRefused:
            continue
        if (old.get("result_ref"), old.get("source"), sorted(old["item_ids"])) == want:
            return path.stem
    return None
