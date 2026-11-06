"""The judge guard's decisions, and the receipt of a completed judge Write (ADR-006).

Imported by hooks-handlers/judge_guard.py, which may run under Python 3.9, so this module
and everything it imports keep to 3.9 syntax."""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from lib import case_files, digest, judge_brief, paths, team_guard

JUDGE_AGENT_TYPE = "business-case:judge"
# MultiEdit is not a current Claude Code tool. It stays here and in the hooks.json matcher
# because it costs nothing and an older client may still send it; no ADR requires it, and the
# tests pin that the matcher and GUARDED_TOOLS agree.
GUARDED_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
# Agent is the current sub-agent tool; Task is matched in case an older client sends it.
DISPATCH_TOOLS = ("Agent", "Task")
# The bare name is guarded too, in case Claude Code resolves "judge" to this plugin's agent.
JUDGE_DISPATCH_NAMES = (JUDGE_AGENT_TYPE, "judge")
BRIEF_FIRST_LINE = judge_brief.BRIEF_TEMPLATE.split("\n", 1)[0]
REPLY_NAME = re.compile(rf"^reply-(?P<nnn>{judge_brief.NNN})\.json$")
RECEIPT_FIELDS = ("brief", "reply", "sha256", "bytes", "agent_id", "agent_type", "session_id", "tool_name")
DISPATCH_RULE = ("dispatch business-case:judge with the text of its judge/brief-NNN.txt as the whole "
                 "prompt, byte for byte, adding nothing")
CASE_FOLDER_HINT = ("code writes every file in a business-case folder, business-case.md through bc.py change; "
                    "write your own files outside the case folder, for example in the temporary directory. "
                    "To keep a copy of the judge's JSON, write it outside the case and run "
                    "bc.py save-report --coach-copy")


@dataclass(frozen=True)
class GuardDecision:
    verdict: str  # "allow": approve this one call; "deny": block it; "pass": not ours, say nothing
    reason: str


class ReceiptRefused(ValueError):
    pass


def receipt_relpath(nnn: int) -> str:
    return f"{paths.JUDGE_DIR}/reply-{nnn:03d}.receipt.json"


def judge_folder_of(path: Path) -> Path | None:
    """The resolved judge folder of path, or None. Path is resolved first. The folder is the first
    of path and its ancestors named judge whose parent is a case slug (paths.SLUG_PATTERN) and whose
    grandparent is named business-cases."""
    resolved = Path(path).resolve()
    for p in (resolved, *resolved.parents):
        if (p.name == "judge" and p.parent.parent.name == "business-cases"
                and paths.SLUG_PATTERN.match(p.parent.name)):
            return p
    return None


def in_judge_folder(path: Path) -> bool:
    """True when path lies in a business-case judge folder, however it is spelled. The deny side of
    the guard uses this. A case-insensitive filesystem (macOS APFS) opens JUDGE/ or ACME/ as the
    same directory, so the names are compared case-folded and the slug is tested after folding."""
    resolved = Path(path).resolve()
    for p in (resolved, *resolved.parents):
        if (p.name.casefold() == "judge" and p.parent.parent.name.casefold() == "business-cases"
                and paths.SLUG_PATTERN.match(p.parent.name.casefold())):
            return True
    return False


def in_case_folder(path: Path) -> bool:
    """True when path, or any of its ancestors, is a case folder: a folder whose name is a slug
    (paths.SLUG_PATTERN) and whose parent is named business-cases. Path is resolved first. The rule
    is by name only. As in in_judge_folder, the names are also compared case-folded, because a
    case-insensitive filesystem opens Business-Cases/ACME/ as the real case folder."""
    return _names_a_case(Path(path).resolve())


def _names_a_case(path: Path) -> bool:
    """in_case_folder's name rule on path as given, without resolving it."""
    for p in (path, *path.parents):
        if p.parent.name.casefold() == "business-cases" and paths.SLUG_PATTERN.match(p.name.casefold()):
            return True
    return False


def _reply_slot(target: Path) -> tuple[Path, int] | None:
    """(judge folder, NNN) when target, already resolved, is judge/reply-NNN.json directly inside a judge folder."""
    folder = judge_folder_of(target)
    m = REPLY_NAME.match(target.name)
    if folder is None or m is None or target.parent != folder:
        return None
    return folder, int(m["nnn"])


def _target(hook_input: dict, raw: str) -> Path:
    return (Path(hook_input.get("cwd") or ".") / raw).resolve()


def _deny_readings(hook_input: dict, raw: str) -> list:
    """Every place a raw path may name, for the deny side, each resolved and also as normalised text:
    the literal reading, and for ~ or ~/... also the home folder's reading, since a file tool may
    expand it. The text reading keeps the names a symlinked business-cases or slug folder loses on
    resolving. The allow side stays literal and resolved."""
    bases = [Path(hook_input.get("cwd") or ".") / raw]
    if raw == "~" or raw.startswith("~/"):
        bases.append(Path.home() / raw[2:])
    return [r for b in bases for r in (b.resolve(), Path(os.path.normpath(b)))]


def decide_write(hook_input: dict) -> GuardDecision:
    """PreToolUse on Write|Edit|MultiEdit|NotebookEdit. Reads the disk; writes nothing. An analyst's
    Write is team_guard's to decide."""
    analyst = team_guard.decide_analyst_write(hook_input)
    if analyst is not None:
        return analyst
    tool = hook_input.get("tool_name")
    if tool not in GUARDED_TOOLS:
        return GuardDecision("pass", "not a file-writing tool")
    tool_input = hook_input.get("tool_input") or {}
    raws = [tool_input[k] for k in ("file_path", "notebook_path") if tool_input.get(k)]
    is_judge = hook_input.get("agent_type") == JUDGE_AGENT_TYPE
    if not raws or not all(isinstance(r, str) for r in raws):
        mention = json.dumps(tool_input, default=str).casefold()
        if is_judge or "judge" in mention or "business-cases" in mention:
            return GuardDecision("deny", "no readable path; a write that may touch a business-case folder is refused")
        return GuardDecision("pass", "no path to guard")
    targets = [_target(hook_input, r) for r in raws]
    if not is_judge:
        if any(_names_a_case(p) for r in raws for p in _deny_readings(hook_input, r)):
            return GuardDecision("deny", CASE_FOLDER_HINT)
        return GuardDecision("pass", "outside every business-case folder")
    target = targets[0]
    if not any(in_judge_folder(t) for t in targets):
        return GuardDecision("deny", "the judge writes only its reply, at the reply_path its brief names")
    if any(t != target for t in targets):
        return GuardDecision("deny", "the judge's Write names two different paths")
    if tool != "Write":
        return GuardDecision("deny", "the judge writes its reply once, with Write; it never edits a file")
    slot = _reply_slot(target)
    if slot is None:
        return GuardDecision("deny", f"the judge may write only judge/reply-NNN.json in the exact spelling, not {target.name}")
    folder, nnn = slot
    if not (folder / judge_brief.brief_name(nnn)).is_file():
        return GuardDecision("deny", f"no {judge_brief.brief_name(nnn)} for this reply")
    if paths.stat_exists(target) or paths.stat_exists(folder.parent / receipt_relpath(nnn)):
        return GuardDecision("deny", f"{judge_brief.reply_name(nnn)} is already written; a judge run writes once")
    if not isinstance(tool_input.get("content"), str):
        return GuardDecision("deny", "the judge's Write carries no content")
    return GuardDecision("allow", "business-case judge reply")


def decide_dispatch(hook_input: dict) -> GuardDecision:
    """PreToolUse on Agent|Task. The judge's prompt must be exactly an unanswered brief's text. An
    analyst's dispatch is team_guard's to decide."""
    analyst = team_guard.decide_analyst_dispatch(hook_input)
    if analyst is not None:
        return analyst
    if hook_input.get("tool_name") not in DISPATCH_TOOLS:
        return GuardDecision("pass", "not a sub-agent dispatch")
    tool_input = hook_input.get("tool_input") or {}
    if tool_input.get("subagent_type") not in JUDGE_DISPATCH_NAMES:
        return GuardDecision("pass", "not the business-case judge")
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return GuardDecision("deny", f"the judge's dispatch carries no prompt; {DISPATCH_RULE}")
    lines = prompt.split("\n")
    reply_lines = [line for line in lines if line.startswith("reply_path: ")]
    if lines[0] != BRIEF_FIRST_LINE or len(reply_lines) != 1:
        return GuardDecision("deny", DISPATCH_RULE)
    raw = Path(reply_lines[0][len("reply_path: "):])
    slot = _reply_slot(raw.resolve()) if raw.is_absolute() else None
    if slot is None:
        return GuardDecision("deny", DISPATCH_RULE)
    folder, nnn = slot
    brief = folder / judge_brief.brief_name(nnn)
    try:
        prompt_bytes = prompt.encode("utf-8")
    except UnicodeEncodeError:  # a lone surrogate from a JSON escape
        return GuardDecision("deny", DISPATCH_RULE)
    if not brief.is_file() or prompt_bytes != brief.read_bytes():
        return GuardDecision("deny", DISPATCH_RULE)
    if paths.stat_exists(folder / judge_brief.reply_name(nnn)) or paths.stat_exists(folder.parent / receipt_relpath(nnn)):
        return GuardDecision("deny", f"{judge_brief.brief_name(nnn)} is already answered; run bc.py brief for a new one")
    return GuardDecision("pass", f"the prompt is exactly {judge_brief.brief_name(nnn)}")


def write_receipt(path: Path, receipt: dict) -> None:
    """Create the receipt; never overwrite one (O_EXCL raises FileExistsError)."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)


def record_write(hook_input: dict) -> Path | None:
    """PostToolUse on Write: Claude Code calls it only after the Write succeeded. For a judge
    reply, hash the bytes now on disk and create the receipt. An analyst's reply gets its receipt
    from team_guard. Otherwise do nothing."""
    analyst = team_guard.record_analyst_write(hook_input)
    if analyst is not None:
        return analyst
    if hook_input.get("tool_name") != "Write" or hook_input.get("agent_type") != JUDGE_AGENT_TYPE:
        return None
    raw = (hook_input.get("tool_input") or {}).get("file_path")
    if not isinstance(raw, str) or not raw:
        return None
    target = _target(hook_input, raw)
    slot = _reply_slot(target)
    if slot is None:
        return None
    folder, nnn = slot
    if not (folder / judge_brief.brief_name(nnn)).is_file() or not target.is_file():
        return None
    content = (hook_input.get("tool_input") or {}).get("content")
    data = target.read_bytes()
    try:
        written = content.encode("utf-8") if isinstance(content, str) else None
    except UnicodeEncodeError:
        written = None
    if data != written:
        return None  # the bytes on disk are not the bytes this Write carried: something else wrote them
    receipt = {"brief": judge_brief.brief_relpath(nnn), "reply": judge_brief.reply_relpath(nnn),
               "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
               "agent_id": str(hook_input.get("agent_id", "")), "agent_type": JUDGE_AGENT_TYPE,
               "session_id": str(hook_input.get("session_id", "")), "tool_name": "Write"}
    path = folder.parent / receipt_relpath(nnn)
    write_receipt(path, receipt)
    return path


def receipt_session(case_dir: Path, nnn: int):
    """The session_id a readable receipt for reply NNN names, or None."""
    try:
        receipt = json.loads((Path(case_dir) / receipt_relpath(nnn)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sid = receipt.get("session_id") if isinstance(receipt, dict) else None
    return sid if isinstance(sid, str) else None


def verify_receipt(case_dir: Path, nnn: int, *, any_recorded_session: bool = False) -> dict:
    """The receipt for reply NNN, or ReceiptRefused naming every problem. The receipt's session must
    be the case's current session; with any_recorded_session, any session the case recorded. Loop
    end uses that to re-check a report saved in an earlier session (ruling FR-I2)."""
    case_dir = Path(case_dir)
    receipt_path = case_dir / receipt_relpath(nnn)
    reply_path = case_dir / judge_brief.reply_relpath(nnn)
    problems = []
    receipt = None
    if not receipt_path.is_file():
        problems.append(f"no {receipt_relpath(nnn)}: no completed judge Write was recorded for this reply")
    else:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except ValueError:
            problems.append(f"{receipt_relpath(nnn)} is not valid JSON")
        else:
            if not isinstance(receipt, dict):
                problems.append(f"{receipt_relpath(nnn)} is not a JSON object")
                receipt = None
    if receipt is not None:
        if tuple(sorted(receipt)) != tuple(sorted(RECEIPT_FIELDS)):
            problems.append("the receipt's fields are not the receipt field set")
        if receipt.get("agent_type") != JUDGE_AGENT_TYPE:
            problems.append(f"the receipt's agent_type is {receipt.get('agent_type')!r}, not {JUDGE_AGENT_TYPE!r}")
        for key, want in (("brief", judge_brief.brief_relpath(nnn)), ("reply", judge_brief.reply_relpath(nnn)),
                          ("tool_name", "Write")):
            if receipt.get(key) != want:
                problems.append(f"the receipt's {key} is {receipt.get(key)!r}, not {want!r}")
        if any_recorded_session:
            try:
                recorded = {s.get("id") for s in case_files.read_meta(case_dir)["sessions"]}
            except (case_files.CaseRefused, KeyError, TypeError, AttributeError):
                recorded = set()
            if receipt.get("session_id") not in recorded:
                problems.append("the receipt's session is not a session this case recorded")
        else:
            try:
                session_id = case_files.current_session(case_dir)["id"]
            except case_files.CaseRefused:
                problems.append("this case has no current session to match the receipt against")
            else:
                if receipt.get("session_id") != session_id:
                    problems.append("the receipt's session is not this case's current session")
    if not reply_path.is_file():
        problems.append(f"no {judge_brief.reply_relpath(nnn)}")
    elif receipt is not None:
        on_disk = digest.file_digest(reply_path)
        if on_disk["sha256"] != receipt.get("sha256") or on_disk["bytes"] != receipt.get("bytes"):
            problems.append("the reply's bytes differ from the bytes the receipt recorded")
    if problems:
        raise ReceiptRefused("; ".join(problems))
    return receipt
