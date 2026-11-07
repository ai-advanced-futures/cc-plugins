"""publish: write the facts of one case folder into the pages of the graph (spec, rows 6 and 7).

`plan` reads the case folder and returns the pages that the case should have, with no change to the bundle.
`publish` writes the pages that are new or changed into a temporary copy of the bundle, regenerates the
indexes, runs the check, and moves the files into the bundle only when the check finds no error.

The case folder is read through the read functions of `lib/` (`case_doc`, `case_files`). The files that have
no read function with a stable shape (the jsonl logs, the evidence pages, the reports) are read as JSON here.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from bclib import DataError, UsageError, logbook, manifest, regen, schema, writer
from bclib.bundle import DEFAULT_DIR, GRAPH, bundle_dir, has_entry, read
from bclib.ids import next_id
from bclib.mapping import SECTION_PART, SECTIONS
from bclib.page import dump, ordered, read_text, write_text

try:  # Windows has no fcntl; the lock is then skipped
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

NO_ENTRY = object()
STICKY = ("finished_at", "plugin_version")
META_KEYS = frozenset({"type", "title", "description", "status", "tags", "aliases", "generated", "verified",
                       "protected", *STICKY})
CHUNK_LINES, CHUNK_WORDS = 70, 400  # a Part page stays well under the limits of the schema table
FUNDING_KINDS = frozenset({"fund", "do_not_fund", "defer"})
_SECTION_MARKER = re.compile(r"^<!-- section: (?P<key>[a-z-]+) lens: (?P<lens>[a-z-]+) -->$")
_REPORT_RE = re.compile(r"report-(\d{2,})\.json$")


@dataclass
class Item:
    type: str
    alias: str
    title: str
    description: str
    fields: dict = field(default_factory=dict)
    links: dict = field(default_factory=dict)  # link field -> list of aliases (this graph) or `<graph>:/path`
    body: str = ""


# --- reading the case folder -------------------------------------------------------------------

def _json(path, default):
    """The JSON of a case file. The default is only for a file that does not exist.

    A file that exists and cannot be read or parsed is a data error: a quiet default would drop its pages and
    publish would still exit 0.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return default
    except (OSError, UnicodeDecodeError) as error:
        raise DataError(f"cannot read {Path(path).name}: {error}") from error
    try:
        return json.loads(text)
    except ValueError as error:
        raise DataError(f"{Path(path).name} is not valid JSON, so nothing is written: {error}") from error


def _jsonl(path) -> list:
    """The records of a JSON Lines case file. A file that does not exist has none; a line that is not JSON is a data error."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError) as error:
        raise DataError(f"cannot read {Path(path).name}: {error}") from error
    out = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as error:
            raise DataError(f"{Path(path).name} line {number} is not valid JSON, so nothing is written: {error}") from error
        if isinstance(rec, dict):
            out.append({k: v for k, v in rec.items() if k != "prev"})
    return out


def _clean(mapping) -> dict:
    return {k: v for k, v in mapping.items() if v is not None}


def _one_line(text, limit=200, fallback="") -> str:
    text = " ".join(str(text or "").split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text or fallback


def _text_block(text) -> str:
    return str(text or "").strip()


def _lib():
    """The read functions of lib/. The plugin root is on sys.path (bc_graph.py puts it there)."""
    from lib import case_doc, case_files
    return case_doc, case_files


def _runs_of(sessions, recorded_by, date) -> list:
    """The session aliases that wrote a line: the session of the person (or the automated one) at that date."""
    if not sessions:
        return []
    want_auto = recorded_by == "automated"
    named = [s for s in sessions if (s.get("mode") == "automated" if want_auto else s.get("name") == recorded_by)]
    pool = [s for s in named if str(s.get("started") or "") <= str(date or "9999")] or named or sessions[-1:]
    return [pool[-1]["id"]]


def _chunks(text) -> list:
    """Split a section text at blank lines into pieces of at most CHUNK_LINES lines and CHUNK_WORDS words."""
    text = text.strip("\n")
    if not text.strip():
        return [""]
    pieces, current, lines, words = [], [], 0, 0
    for paragraph in re.split(r"\n\s*\n", text):
        pl, pw = paragraph.count("\n") + 1, len(paragraph.split())
        if current and (lines + pl + 1 > CHUNK_LINES or words + pw > CHUNK_WORDS):
            pieces.append("\n\n".join(current))
            current, lines, words = [], 0, 0
        if pl > CHUNK_LINES or pw > CHUNK_WORDS:  # one very long paragraph: cut it at line ends
            part_lines = paragraph.split("\n")
            buffer = []
            for line in part_lines:
                if buffer and (len(buffer) + 1 > CHUNK_LINES or sum(len(b.split()) for b in buffer) + len(line.split()) > CHUNK_WORDS):
                    pieces.append("\n".join(buffer))
                    buffer = []
                buffer.append(line)
            paragraph, pl, pw = "\n".join(buffer), len(buffer), sum(len(b.split()) for b in buffer)
        current.append(paragraph)
        lines += pl + 1
        words += pw
    if current:
        pieces.append("\n\n".join(current))
    return pieces


def _section_info(doc_text) -> dict:
    """Section key -> (lens, heading), from the markers and the `## ` headings of business-case.md."""
    out, heading = {}, None
    for line in doc_text.splitlines():
        match = _SECTION_MARKER.match(line.rstrip("\r\n"))
        if match:
            out[match.group("key")] = (match.group("lens"), heading)
            heading = None
        elif line.startswith("## "):
            heading = line[3:].strip()
    return out


_SOURCE_ID = re.compile(r", result (?P<id>[^,\s]+)$")


def _source_results(root, rel, source, team_runs) -> list:
    """The Result pages of the result of an evidence page and of each result that it cites (spec, row 14)."""
    match = _SOURCE_ID.search(str(source or ""))
    if not match:
        return []
    by_file = {Path(str(r.get("result_file") or "")).name: r.get("graph_results") or {} for r in team_runs}
    out, seen, todo = set(), set(), [(rel, match.group("id"))]
    while todo:
        rel, rid = todo.pop()
        if (rel, rid) in seen:
            continue
        seen.add((rel, rid))
        page = by_file.get(Path(rel).name, {}).get(rid)
        if isinstance(page, str):
            out.add(page)
        doc = _json(Path(root) / rel, {})
        for result in doc.get("results") or [] if isinstance(doc, dict) else []:
            if isinstance(result, dict) and result.get("id") == rid:
                todo += [(c["file"], c.get("result_id")) for c in result.get("cites") or []
                         if isinstance(c, dict) and isinstance(c.get("file"), str)]
    return sorted(out)


def plan(case_dir, case_folder=None) -> list:
    """The pages that the case folder gives, as `Item`s. The case folder is not changed."""
    case_dir = Path(case_dir)
    case_doc, case_files = _lib()
    try:
        meta = case_files.read_meta(case_dir)
    except Exception as error:
        raise DataError(f"cannot read the case: {error}") from error
    slug = str(meta.get("slug") or case_dir.name)
    offering = _one_line(meta.get("offering"), 300, slug)
    folder = case_folder or f"business-cases/{slug}"
    sessions = [s for s in meta.get("sessions") or [] if isinstance(s, dict) and s.get("id")]
    if not sessions:
        raise DataError(f"the case {slug} has no session, so no page can name a run. Start a session first.")
    run_alias = {s["id"]: f"{slug}/{s['id']}" for s in sessions}
    last_run = [run_alias[sessions[-1]["id"]]]

    def runs_for(recorded_by, date) -> list:
        return [run_alias[i] for i in _runs_of(sessions, recorded_by, date)] or last_run

    items: list = []
    case_link = {"case": [slug]}

    # Evidence
    evidence_ids, evidence_items = [], []
    git_root = case_dir.resolve()
    for _ in Path(folder).parts:
        git_root = git_root.parent
    runs_doc = _json(case_dir / "team" / "runs.json", {})
    team_runs = [r for r in (runs_doc.get("runs") if isinstance(runs_doc, dict) else []) or [] if isinstance(r, dict)]
    for file in sorted((case_dir / "evidence").glob("EV-*.json")) if (case_dir / "evidence").is_dir() else []:
        page = _json(file, None)
        if not isinstance(page, dict):
            continue
        ev = file.stem
        evidence_ids.append(ev)
        fields = _clean({k: page.get(k) for k in ("source", "summary", "method", "grade", "date", "item_ids",
                                                  "produced_by_plugin", "off_map", "result_ref", "supplied_by",
                                                  "grade_confirmed_by")})
        links = {**case_link, "run": last_run}
        ref = page.get("result_ref")
        if isinstance(ref, dict) and ref.get("path"):
            results = _source_results(git_root, str(ref["path"]), page.get("source"), team_runs)
            if results:
                links["source_results"] = results
        evidence_items.append(Item(
            "Evidence", f"{slug}/{ev}", f"{ev}: {_one_line(page.get('source'), 120, ev)}",
            _one_line(page.get("summary"), 300, f"Evidence {ev} of the case {slug}."), fields, links,
            _text_block(page.get("summary"))))

    # Decisions
    decisions = [d for d in _jsonl(case_dir / "decisions.jsonl") if isinstance(d.get("id"), str)]
    decision_items, funding = [], None
    for rec in decisions:
        did = rec["id"]
        fields = _clean({k: rec.get(k) for k in ("kind", "role", "question", "options", "choice", "subject",
                                                  "item_id", "shown", "cited", "outcome", "name", "date")})
        links = {**case_link, "run": runs_for(rec.get("name") or "automated", rec.get("date"))}
        cited = rec.get("cited") if isinstance(rec.get("cited"), dict) else {}
        reports = sorted(m.group(1) for k in cited for m in [_REPORT_RE.search(str(k))] if m)
        if reports:
            links["review"] = [f"{slug}/report-{reports[-1]}"]
        decision_items.append(Item(
            "Decision", f"{slug}/{did}", f"{did}: {rec.get('kind')}",
            _one_line(f"{rec.get('role')} decision {rec.get('kind')}: {rec.get('question')}", 300, f"Decision {did}."),
            fields, links, _text_block(rec.get("reason")) or "No reason is recorded."))
        if rec.get("kind") in FUNDING_KINDS:
            funding = f"{slug}/{did}"

    # Strategy register
    register = _jsonl(case_dir / "register.jsonl")
    confirms = {}
    for rec in register:
        if rec.get("line") == "confirm":
            confirms.setdefault(rec.get("ref"), []).append(_clean({k: rec.get(k) for k in ("name", "date", "answer")}))
    strategy_items = []
    for rec in register:
        sid = rec.get("id")
        if rec.get("line") == "confirm" or not isinstance(sid, str):
            continue
        fields = _clean({"category": rec.get("category"), "choice": rec.get("choice"),
                         "rejected_alternative": rec.get("rejected_alternative"),
                         "evidence_text": rec.get("evidence") or None, "source": rec.get("source"),
                         "recorded_by": rec.get("recorded_by"), "date": rec.get("date"), "reason": rec.get("reason"),
                         "change_source": rec.get("change_source"), "confirmed": confirms.get(sid) or None})
        links = {**case_link, "run": runs_for(rec.get("recorded_by"), rec.get("date"))}
        if rec.get("supersedes"):
            links["supersedes"] = [f"{slug}/{rec['supersedes']}"]
        strategy_items.append(Item(
            "StrategyEntry", f"{slug}/{sid}", f"{sid}: {rec.get('category')}",
            _one_line(f"{rec.get('category')}: {rec.get('choice')}", 300, f"Strategy entry {sid}."), fields, links,
            _text_block(rec.get("choice")) or "The entry has no choice text."))

    # Conditions
    conditions = _jsonl(case_dir / "conditions.jsonl")
    marks = {}
    for rec in conditions:
        if rec.get("line") == "mark":
            marks.setdefault(rec.get("ref"), []).append(_clean({"as": rec.get("as"), "name": rec.get("name"),
                                                                "date": rec.get("date"), "answer": rec.get("answer")}))
    condition_items = []
    for rec in conditions:
        cid = rec.get("id")
        if rec.get("line") == "mark" or not isinstance(cid, str):
            continue
        fields = _clean({"text": rec.get("text"), "evidence_text": rec.get("evidence") or None,
                         "source": rec.get("source"), "recorded_by": rec.get("recorded_by"), "date": rec.get("date"),
                         "reason": rec.get("reason"), "change_source": rec.get("change_source"),
                         "marked": marks.get(cid) or None})
        supports = rec.get("supports")
        supports = [supports] if isinstance(supports, str) else list(supports or [])
        links = {**case_link, "run": runs_for(rec.get("recorded_by"), rec.get("date")),
                 "supports": [f"{slug}/{s}" for s in supports]}
        if rec.get("supersedes"):
            links["supersedes"] = [f"{slug}/{rec['supersedes']}"]
        condition_items.append(Item(
            "Condition", f"{slug}/{cid}", f"{cid}: condition",
            _one_line(rec.get("text"), 300, f"Condition {cid}."), fields, links,
            _text_block(rec.get("text")) or "The condition has no text."))

    # Notes
    note_items = []
    for rec in _jsonl(case_dir / "notes.jsonl"):
        nid = rec.get("id")
        if not isinstance(nid, str):
            continue
        fields = _clean({k: rec.get(k) for k in ("text", "source", "failed_tests", "reason", "recorded_by", "date")})
        note_items.append(Item(
            "Note", f"{slug}/{nid}", f"{nid}: note", _one_line(rec.get("text"), 300, f"Note {nid}."), fields,
            {**case_link, "run": runs_for(rec.get("recorded_by"), rec.get("date"))},
            _text_block(rec.get("text")) or "The note has no text."))

    # Figures
    figure_lines = _jsonl(case_dir / "figures.jsonl")
    figure_confirms = {}
    for rec in figure_lines:
        if rec.get("record") == "confirm":
            figure_confirms.setdefault(rec.get("ref"), []).append(
                _clean({"name": rec.get("name"), "date": rec.get("date"), "answer": rec.get("answer")}))
    figure_items, figure_ids = [], []
    for rec in figure_lines:
        fid = rec.get("id")
        if rec.get("record") == "confirm" or not isinstance(fid, str):
            continue
        figure_ids.append(fid)
        fields = _clean({k: rec.get(k) for k in ("kind", "amount", "written_as", "currency", "scenario", "item_id",
                                                  "quote", "source", "stream", "months", "reason", "recorded_by", "date")})
        fields["figure_parts"] = rec.get("parts") or None
        fields["confirmed"] = figure_confirms.get(fid) or None
        fields = _clean(fields)
        links = {**case_link, "run": runs_for(rec.get("recorded_by"), rec.get("date"))}
        evidence = [f"{slug}/{e}" for e in rec.get("evidence") or [] if isinstance(e, str)]
        if evidence:
            links["evidence"] = evidence
        for name in ("replaces", "restates"):
            value = rec.get(name)
            value = [value] if isinstance(value, str) else list(value or [])
            if value:
                links[name] = [f"{slug}/{v}" for v in value]
        if rec.get("supersedes"):
            sup = rec["supersedes"]
            links["supersedes"] = [f"{slug}/{sup if isinstance(sup, str) else sup[0]}"]
        figure_items.append(Item(
            "Figure", f"{slug}/{fid}", f"{fid}: {rec.get('kind')} {rec.get('amount')} {rec.get('currency')}",
            _one_line(f"{rec.get('kind')} {rec.get('written_as') or rec.get('amount')} ({rec.get('scenario')})", 300,
                      f"Figure {fid}."), fields, links,
            _text_block((rec.get("quote") or {}).get("sentence") if isinstance(rec.get("quote"), dict) else "")
            or "The figure has no quoted sentence."))

    # Finance
    finance_items = []
    finance = _json(case_dir / "finance.json", None)
    if isinstance(finance, dict):
        numbers = {k: v for k, v in finance.items() if k not in ("inputs", "figures")}
        ceiling = finance.get("ceiling") if isinstance(finance.get("ceiling"), dict) else {}
        fields = _clean({"numbers": numbers, "verdict_ceiling": ceiling.get("value")})
        links = {**case_link, "run": last_run,
                 "figures": [f"{slug}/{f}" for f in (finance.get("figures") or {}) if f in figure_ids]}
        finance_items.append(Item(
            "Finance", f"{slug}/finance", f"{slug}: finance",
            _one_line(f"The numbers of the case {slug}; the verdict ceiling is {ceiling.get('value')}.", 300),
            fields, links, _text_block(ceiling.get("reason")) or "The ceiling has no reason."))

    # Reviews
    rubric = _json(case_dir / "rubric.json", {})
    rubric_items = [i for i in (rubric.get("items") if isinstance(rubric, dict) else []) or [] if isinstance(i, dict)]
    section_of = {i.get("id"): i.get("section") for i in rubric_items}
    review_items, latest_review = [], None
    for file in sorted((case_dir / "judge").glob("report-*.json")) if (case_dir / "judge").is_dir() else []:
        match = _REPORT_RE.search(file.name)
        report = _json(file, None)
        if not match or not isinstance(report, dict):
            continue
        number = match.group(1)
        verdict = report.get("investment_verdict")
        written = report.get("written_by")
        fields = _clean({"report": number, "written_by": written if written in ("judge", "coach-copy") else None,
                         "investment_verdict": verdict if verdict in ("supported", "undetermined", "not_supported") else None,
                         "manifest_digest": report.get("manifest_digest"), "item_verdicts": report.get("items")})
        findings = [f for f in report.get("findings") or [] if isinstance(f, dict)]
        sections = sorted({section_of.get(f.get("item_id")) for f in findings if section_of.get(f.get("item_id"))})
        links = {**case_link, "run": last_run, "parts": [f"{slug}/{s}" for s in sections]}
        lines = [f"- {f.get('id') or f.get('job')} ({f.get('job')}, {f.get('item_id') or 'no item'}): "
                 f"{_one_line(f.get('summary'), 240)}" for f in findings]
        review_items.append(Item(
            "Review", f"{slug}/report-{number}", f"{slug}: report {number}",
            _one_line(f"Report {number} of the independent judge; investment verdict {verdict or 'not given'}.", 300),
            fields, links, "\n".join(lines) or "The report has no findings."))
        latest_review = f"{slug}/report-{number}"

    # Parts
    doc_path = case_dir / "business-case.md"
    try:
        doc_text = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
        sections = case_doc.parse_sections(doc_text)
    except Exception as error:  # a file that cannot be read or decoded, or a document that does not parse
        raise DataError(f"cannot read business-case.md: {error}") from error
    info = _section_info(doc_text)
    ledger = _json(case_dir / "ledger.json", {})
    ledger = ledger if isinstance(ledger, dict) else {}
    changelog = _jsonl(case_dir / "changelog.jsonl")
    decisions_of_item = {}
    for rec in decisions:
        if rec.get("item_id"):
            decisions_of_item.setdefault(rec["item_id"], []).append(f"{slug}/{rec['id']}")
    part_items = []
    for key in SECTIONS:
        if key not in sections:
            raise DataError(f"business-case.md has no section {key}")
        lens, heading = info.get(key, ("", None))
        heading = heading or key
        rows = [i for i in rubric_items if i.get("section") == key]
        item_rows = [_clean({"id": i["id"], "title": i.get("title"),
                             "coach_class": (ledger.get(i["id"]) or {}).get("coach_class")}) for i in rows]
        evidence = sorted({f"{slug}/{e}" for i in rows for e in (ledger.get(i["id"]) or {}).get("evidence") or []
                           if isinstance(e, str)})
        decided = sorted({d for i in rows for d in decisions_of_item.get(i["id"], [])})
        runs = sorted({r for c in changelog if c.get("section") == key
                       for r in runs_for(c.get("accepted_by"), c.get("date"))}) or last_run
        pieces = _chunks(sections[key])
        for n, text in enumerate(pieces, 1):
            alias = f"{slug}/{key}" if n == 1 else f"{slug}/{key}/{n}"
            fields = {"section": key, "part": SECTION_PART[key]}
            if lens:
                fields["lens"] = lens
            fields["heading"] = heading
            links = {**case_link, "run": runs}
            if n == 1:
                if item_rows:
                    fields["items"] = item_rows
                if evidence:
                    links["evidence"] = evidence
                if decided:
                    links["decisions"] = decided
            if n < len(pieces):
                links["next"] = [f"{slug}/{key}/{n + 1}"]
            suffix = f" ({n})" if len(pieces) > 1 else ""
            part_items.append(Item(
                "Part", alias, f"{slug}: {heading}{suffix}",
                _one_line(f"The {heading} section of the case {slug}{', page %d' % n if n > 1 else ''}.", 300),
                fields, links, text.strip("\n") or "The section is empty."))

    # Runs
    run_items = []
    for s in sessions:
        fields = _clean({"command": "business-case:build", "subject": offering, "run_id": s["id"],
                         "mode": s.get("mode") if s.get("mode") in ("interactive", "automated") else None,
                         "person": s.get("name"), "started_at": s.get("started"), "judge_runs": s.get("judge_runs")})
        who = s.get("name") or "an automated run"
        run_items.append(Item("Run", run_alias[s["id"]], f"{slug}: session {s['id']}",
                              _one_line(f"Session {s['id']} of the case {slug}, by {who}.", 300), fields,
                              dict(case_link), f"Session {s['id']} of the case {slug}, by {who}."))

    # Case
    handoff = _json(case_dir / "business-case-handoff.json", {})
    handoff = handoff if isinstance(handoff, dict) else {}
    scope = _json(case_dir / "scope.json", {})
    market = meta.get("market") or (scope.get("market") if isinstance(scope, dict) else None)
    fields = _clean({"slug": slug, "offering": offering, "market": market if market in ("B2B", "B2C", "both") else None,
                     "rubric_version": meta.get("rubric_version"),
                     "created_rubric_version": meta.get("created_rubric_version"), "case_folder": folder,
                     "loop_status": handoff.get("status"), "needs_human": handoff.get("needs_human"),
                     "open_items": handoff.get("open_items"), "absent_categories": handoff.get("absent_categories"),
                     "orphaned_conditions": handoff.get("orphaned_conditions"), "problems": handoff.get("problems"),
                     "completed_at": handoff.get("completed_at")})
    links = {}
    if funding:
        links["funding_decision"] = [funding]
    if latest_review:
        links["latest_review"] = [latest_review]
    if finance_items:
        links["finance"] = [finance_items[0].alias]
    case_item = Item("Case", slug, slug, _one_line(f"The business case for {offering}", 300), fields, links,
                     _one_line(f"The business case for {offering}", 300))

    items = [case_item, *run_items, *part_items, *evidence_items, *decision_items, *strategy_items,
             *condition_items, *note_items, *figure_items, *finance_items, *review_items]
    known = {i.alias.casefold() for i in items}
    for item in items:  # a link to a record that has no page is dropped
        item.links = {name: [t for t in targets if ":" in t or t.casefold() in known]
                      for name, targets in item.links.items()}
        item.links = {name: targets for name, targets in item.links.items() if targets}
    return items


# --- comparing items and pages -----------------------------------------------------------------

def pages_by_alias(pages) -> dict:
    out = {}
    for path, page in pages.items():
        for alias in (page.frontmatter or {}).get("aliases") or []:
            out.setdefault(str(alias).casefold(), path)
    return out


def _body_text(page) -> str:
    text = regen.strip_generated(page.body).strip("\n")
    lines = text.split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def differs(item, page) -> bool:
    """True when the data fields, the title, the description, or the body of the page differ from the item."""
    fm = page.frontmatter or {}
    if fm.get("title") != item.title or fm.get("description") != item.description:
        return True
    if any(fm.get(k) != v for k, v in item.fields.items()):
        return True
    link_names = set(schema.edges())
    if any(k not in item.fields and k not in META_KEYS and k not in link_names for k in fm):
        return True
    return _body_text(page) != item.body.strip()


def snapshot_value(root, case_folder, result_ref, upstream_fm):
    """The `value` of the entry in the snapshot of the case that matches the Result page, or NO_ENTRY."""
    ids = {str(a).rsplit("/", 1)[-1] for a in (upstream_fm.get("aliases") or [])}
    candidates = []
    if isinstance(result_ref, dict) and result_ref.get("path"):
        candidates.append(Path(root) / str(result_ref["path"]))
    upstream = Path(case_folder) / "team" / "upstream"
    if upstream.is_dir():
        candidates += sorted(upstream.glob("*.json"))
    for file in candidates:
        doc = _json(file, None)
        for entry in (doc.get("results") if isinstance(doc, dict) else None) or []:
            if isinstance(entry, dict) and entry.get("id") in ids:
                return entry.get("value")
    return NO_ENTRY


# --- publish -----------------------------------------------------------------------------------

def _git_ignored(root, rel) -> bool:
    done = subprocess.run(["git", "check-ignore", "-q", rel], cwd=str(root), capture_output=True, text=True)
    return done.returncode == 0


def _first_error(issues) -> str:
    for issue in issues:
        if issue.level == "ERROR":
            return issue.text()
    return "the check failed"


def _init_once(root) -> bool:
    """Make the bundle when no other process made it first. Return True when this process made it."""
    parent = root / Path(DEFAULT_DIR).parent
    parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(parent, os.O_RDONLY)
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        if has_entry(root):
            return False
        writer.init(root, DEFAULT_DIR)
        return True
    finally:
        os.close(fd)


def publish(root, case_dir) -> dict:
    """Write the case into the bundle. Return the result as a dict (the caller prints it as JSON)."""
    from bclib import check

    root, case_dir = Path(root).resolve(), Path(case_dir)
    case_dir = case_dir if case_dir.is_absolute() else (root / case_dir)
    if not (case_dir / "case.json").is_file():
        raise UsageError(f"{case_dir} is not a case folder: it has no case.json")
    try:
        rel = case_dir.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise UsageError(f"the case folder {case_dir} is not inside the project root {root}") from error
    result = {"graph": GRAPH, "case_folder": rel}
    fresh = not has_entry(root)
    target = DEFAULT_DIR if fresh else bundle_dir(root).relative_to(root).as_posix()
    if _git_ignored(root, rel) and not _git_ignored(root, target + "/"):
        result["private"] = f"PRIVATE: {rel}/ is not in git; add {target}/ to .gitignore, then run publish again"
        return result
    if fresh and _init_once(root):
        result["init"] = f"INIT: {DEFAULT_DIR}/"
    folder = bundle_dir(root)
    items = plan(case_dir, rel)
    lock = open(folder / manifest.NAME, "r+", encoding="utf-8")
    try:
        if fcntl is not None:
            fcntl.flock(lock, fcntl.LOCK_EX)
        result.update(_write_all(root, folder, items, check))
    finally:
        lock.close()
    return result


def _write_all(root, folder, items, check) -> dict:
    existing = read(root, folder).pages
    by_alias = pages_by_alias(existing)
    version = schema.plugin_actor()
    # The work copy is a sibling of the bundle: a link to another graph (`source_results`) is written relative to
    # the page, so the copy needs the same depth as the bundle, or the moved page would hold a wrong link.
    with tempfile.TemporaryDirectory(prefix=".bc-publish-", dir=folder.parent) as tmp:
        work = Path(tmp)
        shutil.copytree(folder, work, dirs_exist_ok=True)
        paths = {}  # alias (folded) -> path in the work copy
        created = 0
        for item in items:  # pass 1: a path for each item; a new page gets a placeholder so the next ID moves on
            key = item.alias.casefold()
            if key in by_alias:
                paths[key] = work / by_alias[key].relative_to(folder)
            else:
                target = work / schema.types()[item.type]["directory"] / f"{next_id(work, item.type)}.md"
                write_text(target, "placeholder\n")
                paths[key] = target
                created += 1
        refs = {key: "/" + path.relative_to(work).as_posix() for key, path in paths.items()}
        edges = schema.edges()
        updated, unchanged = 0, 0
        now = logbook.stamp()
        for item in items:  # pass 2: the page itself
            key = item.alias.casefold()
            old = existing.get(by_alias[key]) if key in by_alias else None
            frontmatter = {"type": item.type, "title": item.title, "description": item.description}
            frontmatter.update(item.fields)
            for name, targets in item.links.items():
                values = [refs[t.casefold()] if ":" not in t else t for t in targets]
                frontmatter[name] = values if edges[name]["multivalued"] else values[0]
            if old is not None:
                same = (not differs(item, old)
                        and all((old.frontmatter or {}).get(n) == v for n, v in frontmatter.items() if n in edges)
                        and not any(n in (old.frontmatter or {}) and n not in frontmatter for n in edges))
                if same:
                    unchanged += 1
                    continue
                updated += 1
                old_fm = old.frontmatter or {}
                aliases = [item.alias] + [a for a in old_fm.get("aliases") or [] if str(a).casefold() != key]
                for name in ("verified", "protected", "tags"):
                    if name in old_fm:
                        frontmatter[name] = old_fm[name]
                if item.type == "Run" and old_fm.get("plugin_version"):
                    frontmatter["plugin_version"] = old_fm["plugin_version"]
            else:
                aliases = [item.alias]
            if item.type == "Run":
                frontmatter.setdefault("plugin_version", schema.plugin_version())
                frontmatter["finished_at"] = now
            frontmatter["status"] = "draft"
            frontmatter["aliases"] = aliases
            frontmatter["generated"] = {"by": version, "at": now}
            frontmatter = ordered(frontmatter, schema.types()[item.type]["key_order"])
            page_id = paths[key].stem
            body = f"\n# {page_id}: {item.title}\n\n{item.body.strip()}\n"
            problems = schema.validate(item.type, frontmatter)
            if problems:
                raise DataError(f"the page {item.alias} is not valid, so nothing is written: " + "; ".join(problems))
            write_text(paths[key], dump(frontmatter, body))
        # a placeholder that was never replaced cannot stay (a new page is always written in pass 2)
        regen.write(root, work)
        issues = check.run(root, work)
        if any(i.level == "ERROR" for i in issues):
            raise DataError("the check of the new pages found an error, so nothing is written. " + _first_error(issues))
        moved = []
        for path in sorted(work.rglob("*")):
            if not path.is_file():
                continue
            target = folder / path.relative_to(work)
            if path.name == "log.md" and target.parent == folder:
                continue
            if not target.is_file() or read_text(target) != read_text(path):
                write_text(target, read_text(path))
                moved.append(target)
        case_page = next(i for i in items if i.type == "Case")
        result = {"case": case_page.alias, "case_page": refs[case_page.alias.casefold()], "created": created,
                  "updated": updated, "unchanged": unchanged, "files_written": len(moved)}
        if created or updated:
            logbook.append(folder / "log.md", "Publish",
                           f"published the case {case_page.alias}: {created} new pages, {updated} changed pages",
                           version)
        return result
