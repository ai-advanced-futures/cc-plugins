"""The case's files: init, scope, originals, section changes and the change log, sessions.

Spec §5 (artifacts: case.json, scope, originals never edited, append-only change log) and §6
(a decision record without a name is refused).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from lib import case_doc, clock, digest, ledger, paths, rubric

# The name on every line an automated session writes. No person may take it (start_session).
AUTOMATED = "automated"


class CaseRefused(ValueError):
    """A case-file operation the rules refuse."""


def _atomic_write(path: Path, data: bytes) -> None:
    """Write to a temp file in the same folder, then move it into place."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _write_json(path: Path, obj) -> None:
    _atomic_write(path, (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def _append_jsonl(path: Path, obj) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _blank(value) -> bool:
    return not isinstance(value, str) or value.strip() == ""


def _int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def read_meta(case_dir: Path) -> dict:
    """case.json. Refused, naming the file, when it cannot be read or its sessions or budget have
    the wrong shape."""
    path = Path(case_dir) / paths.CASE_META
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaseRefused(f"cannot read {path}: {exc}") from exc
    sessions = meta.get("sessions") if isinstance(meta, dict) else None
    if (not isinstance(sessions, list) or not _int(meta.get("session_budget"))
            or not all(isinstance(s, dict) and _int(s.get("judge_runs")) for s in sessions)):
        raise CaseRefused(f"{path} has no session_budget number and sessions list with judge_runs counts")
    return meta


def offering(case_dir: Path) -> str:
    """The offering's name from case.json, which both views show. Refused, naming the file, when
    case.json has none. Only the views ask, so no other case.json reader refuses for it (Task 18
    fix round 2)."""
    name = read_meta(case_dir).get("offering")
    if not isinstance(name, str):
        raise CaseRefused(f"{Path(case_dir) / paths.CASE_META} has no offering name")
    return name


def read_scope(case_dir: Path) -> dict:
    """scope.json, with its market and applicable item IDs. Refused, naming the file, when it cannot
    be read or lacks either."""
    path = Path(case_dir) / paths.SCOPE
    try:
        scope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CaseRefused(f"cannot read {path}: {exc}") from exc
    if (not isinstance(scope, dict) or not isinstance(scope.get("market"), str)
            or not isinstance(scope.get("applicable_item_ids"), list)
            or not all(isinstance(i, str) for i in scope["applicable_item_ids"])):
        raise CaseRefused(f"{path} has no market and applicable_item_ids")
    return scope


def applicable_items(case_dir: Path) -> list:
    """The case's applicable rubric items, in rubric order: its rubric copy, for the market in
    scope.json, the judge's input (final review M-3)."""
    case_dir = Path(case_dir)
    market = read_scope(case_dir)["market"]  # first: a case with no scope is refused naming scope.json
    return rubric.applicable_items(rubric.load_rubric(case_dir / paths.RUBRIC_COPY), market)


def write_meta(case_dir: Path, meta: dict) -> None:
    _write_json(Path(case_dir) / paths.CASE_META, meta)


def check_case_path(case_dir) -> Path:
    """The case folder's resolved path, or CaseRefused. The write guard knows a case by the names on
    its resolved path, so a case folder must resolve to <anything>/business-cases/<slug>: a symlinked
    business-cases or slug folder whose real names differ is refused."""
    resolved = Path(case_dir).resolve()
    if resolved.parent.name != "business-cases" or not paths.SLUG_PATTERN.fullmatch(resolved.name):
        raise CaseRefused(f"the case folder {case_dir} resolves to {resolved}, which is not "
                          "<anything>/business-cases/<slug>; keep the case in a real business-cases folder")
    return resolved


def init_case(case_dir: Path, *, slug: str, offering: str, market: str,
              rubric_version: str = None) -> None:
    """Create the case folder and its starting files. Refuses an existing case, a blank slug or
    offering, and a folder that is not <anything>/business-cases/{slug}. With no rubric_version,
    the case opens on the newest shipped rubric."""
    case_dir = Path(case_dir)
    if not isinstance(slug, str) or not paths.SLUG_PATTERN.fullmatch(slug):
        raise CaseRefused(f"the case slug {slug!r} must be lowercase letters, digits and hyphens, starting with a letter or digit")
    if _blank(offering) or "\n" in offering or "\r" in offering:
        raise CaseRefused("the offering must be one non-blank line")
    if case_dir.name != slug or case_dir.parent.name != "business-cases":
        raise CaseRefused(f"a case folder must be <anything>/business-cases/{slug}; got {case_dir}")
    resolved = check_case_path(case_dir)
    if resolved.name != slug:
        raise CaseRefused(f"the case folder {case_dir} resolves to {resolved}, not to a folder named {slug}")
    if paths.stat_exists(case_dir / paths.CASE_META):
        raise CaseRefused(f"{case_dir} already holds a case ({paths.CASE_META} exists)")
    try:
        if rubric_version is None:
            rubric_version = rubric.newest_version()
        source = rubric.shipped_rubric_path(rubric_version)
        data = rubric.load_rubric(source)
        items = rubric.applicable_items(data, market)
    except rubric.RubricError as exc:
        raise CaseRefused(str(exc)) from exc
    template = paths.TEMPLATE.read_text(encoding="utf-8")
    anchor = "<!-- offering -->\n"
    if template.count(anchor) != 1:
        raise CaseRefused("the case template has no single `<!-- offering -->` line")
    doc = template.replace(anchor, anchor + f"Offering: {offering}\n")

    case_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(case_dir / paths.RUBRIC_COPY, source.read_bytes())
    _write_json(case_dir / paths.SCOPE, {"market": market, "rubric_version": rubric_version,
                                         "applicable_item_ids": sorted(i["id"] for i in items)})
    _atomic_write(case_dir / paths.CASE_DOC, doc.encode("utf-8"))
    try:
        ledger.init_ledger(case_dir)
    except ledger.LedgerRefused as exc:
        raise CaseRefused(str(exc)) from exc
    _atomic_write(case_dir / paths.DECISIONS, b"")
    # created_rubric_version never changes; a move changes rubric_version (rubric_move). A case
    # created before 0.3.0 has no created_rubric_version: it was created on 1.0.0.
    write_meta(case_dir, {"slug": slug, "offering": offering, "market": market,
                          "rubric_version": rubric_version, "created_rubric_version": rubric_version,
                          "session_budget": paths.SESSION_BUDGET_DEFAULT, "sessions": []})


def store_original(case_dir: Path, kind: str, source: Path, *, text: Path = None) -> Path:
    """Keep a proposal or strategy as given, once. A source that is not UTF-8 needs `text`, the
    session's UTF-8 extraction, which is stored beside it. For a UTF-8 source `text` is ignored."""
    case_dir, source = Path(case_dir), Path(source)
    if kind not in ("proposal", "strategy"):
        raise CaseRefused(f"kind {kind!r} is not proposal or strategy")
    inputs = case_dir / paths.INPUTS_DIR
    target = inputs / f"{kind}.original"
    if paths.stat_exists(target):
        raise CaseRefused(f"the {kind} original is already stored at {target}; it is never replaced")
    data = source.read_bytes()
    try:
        data.decode("utf-8")
        is_text = True
    except UnicodeDecodeError:
        is_text = False
    text_bytes = None
    if not is_text:
        if text is None:
            raise CaseRefused(f"{source} is not UTF-8 text; give the session's text extraction of it as `text`")
        text_bytes = Path(text).read_bytes()
        try:
            text_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise CaseRefused(f"the text extraction {text} is not UTF-8") from None
    inputs.mkdir(parents=True, exist_ok=True)
    if text_bytes is not None:
        _atomic_write(inputs / f"{kind}.text.md", text_bytes)
    _atomic_write(target, data)
    return target


def start_session(case_dir: Path, *, session_id: str, name, automated: bool = False) -> dict:
    """Record a new session, or resume a recorded one. Refuses a blank ID, a blank name in an
    interactive session, the name `automated` (any case) in an interactive session, and a name in
    an automated one.

    A recorded ID resumes that session (ruling FR-I3): it becomes current again and keeps its
    judge-run count, so the budget is never reset. Resuming as another person or in another mode
    is refused. The returned entry of a resumed session carries "resumed": True."""
    if _blank(session_id):
        raise CaseRefused("the session ID is blank")
    session_id = session_id.strip()
    if automated:
        if name is not None:
            raise CaseRefused("an automated session has no person; give no name")
        stored = None
    else:
        if _blank(name):
            raise CaseRefused("an interactive session needs the person's name")
        stored = name.strip()
        if stored.casefold() == AUTOMATED:
            raise CaseRefused("the name 'automated' marks the lines an automated session writes; "
                              "give the person's own name")
    mode = AUTOMATED if automated else "interactive"
    meta = read_meta(case_dir)
    for n, recorded in enumerate(meta["sessions"]):
        if recorded.get("id") != session_id:
            continue
        if recorded.get("mode") != mode:
            raise CaseRefused(f"session {session_id} is recorded as {recorded.get('mode')}; "
                              f"resume it as {recorded.get('mode')}")
        if recorded.get("name") != stored:
            raise CaseRefused(f"session {session_id} is recorded for {recorded.get('name')!r}; "
                              "resume it with that name")
        if n != len(meta["sessions"]) - 1:
            meta["sessions"].append(meta["sessions"].pop(n))
            write_meta(case_dir, meta)
        return dict(recorded, resumed=True)
    entry = {"id": session_id, "name": stored, "mode": mode,
             "started": clock.today(), "judge_runs": 0}
    meta["sessions"].append(entry)
    write_meta(case_dir, meta)
    return entry


def current_session(case_dir: Path) -> dict:
    """The last session. Raises CaseRefused when none was started."""
    sessions = read_meta(case_dir)["sessions"]
    if not sessions:
        raise CaseRefused("no session is started; run `session` first")
    return sessions[-1]


def current_name(case_dir: Path) -> str:
    """The current session's person. Refused with no session, in an automated session, and when
    the stored name is blank (spec §6: a record without a name is refused)."""
    session = current_session(case_dir)
    if session.get("mode") == AUTOMATED:
        raise CaseRefused("the current session is automated; it has no person to name")
    name = session.get("name")
    if _blank(name):
        raise CaseRefused("the current session has no name on record")
    return name


def bump_judge_runs(case_dir: Path) -> int:
    """Count one judge run against the current session; returns the new count."""
    meta = read_meta(case_dir)
    if not meta["sessions"]:
        raise CaseRefused("no session is started; run `session` first")
    meta["sessions"][-1]["judge_runs"] += 1
    write_meta(case_dir, meta)
    return meta["sessions"][-1]["judge_runs"]


def apply_change(case_dir: Path, *, section: str, body: str, summary: str, source: str) -> dict:
    """Replace one section of business-case.md and log the change, in one call.

    The document is written first, then the log line. A crash between the two leaves the new
    section in place with no change-log entry."""
    case_dir = Path(case_dir)
    if _blank(summary):
        raise CaseRefused("the change needs a summary")
    if _blank(source):
        raise CaseRefused("the change needs a source")
    session = current_session(case_dir)
    accepted_by = AUTOMATED if session.get("mode") == AUTOMATED else current_name(case_dir)
    doc_path = case_dir / paths.CASE_DOC
    before = doc_path.read_text(encoding="utf-8")
    try:
        after = case_doc.replace_section(before, section, body)
    except case_doc.CaseDocError as exc:
        raise CaseRefused(str(exc)) from exc
    if after == before:  # file text, not the body argument: replace_section normalises line endings
        raise CaseRefused(f"the new body of section {section} is the same as the current one")
    after_bytes = after.encode("utf-8")
    _atomic_write(doc_path, after_bytes)
    entry = {"date": clock.today(), "section": section, "summary": summary, "source": source,
             "accepted_by": accepted_by,
             "before_sha256": digest.sha256_hex(before.encode("utf-8")),
             "after_sha256": digest.sha256_hex(after_bytes)}
    _append_jsonl(case_dir / paths.CHANGELOG, entry)
    return entry
