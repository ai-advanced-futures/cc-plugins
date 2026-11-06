"""The analyst guards (spec §5.8 Dispatch and Writes): an analyst is dispatched only with the exact
text of an open team brief; it writes once, with Write, to its reply file; a completed reply Write gets
a receipt.

judge_receipt asks this module first, in decide_write, decide_dispatch and record_write. Each decide
function returns None when the call is not an analyst's, and judge_receipt then decides as before.

An analyst type is `business-case:<name>`, where name is the frontmatter `name:` of a
`case-*-analyst.md` in the agents folder; a test pins name == file stem. When that folder or a name in
it cannot be read, the guard denies every call whose agent name has an analyst's shape
(`case-*-analyst` after its last colon); every other call is not an analyst's and is left alone. The
bare name is guarded too, in case Claude Code resolves it to this plugin's agent, but only when no
agent of that name is found in $CLAUDE_CONFIG_DIR/agents, ~/.claude/agents, or the .claude/agents of
$CLAUDE_PROJECT_DIR, the cwd, and each of their parents up to the git root or HOME; otherwise the bare
name is denied, and the coach uses the full name. Agents from --agents, settings and managed policy are
not scanned. A test pins that no other plugin's agent in this repo has an analyst's name.

Binding: no hook field ties a sub-agent to the brief it was dispatched with. A reply slot belongs to
the brief's agent_type, and the reply binds to its brief by content: the reply JSON carries
`brief_sha256`, the brief's own sha256: header, which the run holds because its prompt is the brief.
The write guard, the receipt and verify_analyst_receipt refuse a reply whose brief_sha256 is not the
digest of the brief at its slot, so a run whose brief expired, was cancelled or was answered, or a run
on another case, cannot write another brief's slot. team_files.write_brief also keeps one brief open
per agent_type, and the write guard refuses an analyst Write while more than one is open for its type.
Residual: a run that reads another brief file and copies its digest can still write that brief's slot.

Imported by hooks-handlers/judge_guard.py, which may run under Python 3.9, so this module and
everything it imports keep to 3.9 syntax."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from lib import case_files, digest, judge_receipt, paths, team_files

PLUGIN_PREFIX = "business-case:"
AGENTS_DIR = paths.PLUGIN_ROOT / "agents"
_ANALYST_FILE = re.compile(r"^case-.+-analyst\.md$")
_ANALYST_NAME = re.compile(r"^case-.+-analyst$")
_REPLY_NAME = re.compile(r"^reply-([0-9]{3}|[1-9][0-9]{3,})\.json$")
DISPATCH_RULE = ("dispatch an analyst with the text of its open team/brief-NNN.txt as the whole prompt, "
                 "byte for byte, adding nothing")
ALLOW_REASON = "business-case analyst reply"
DIGEST_REFUSAL = "this analyst reply does not belong to the brief this run was given"
# Final review M2: a cut-off or non-JSON reply is refused for what it is. It names no brief and no digest.
MALFORMED_REPLY = ("the analyst's reply is not one complete JSON object holding brief_sha256 as text; write the whole "
                   "reply again with one Write")


class AgentsUnreadable(OSError):
    """The agents folder, or an analyst file's frontmatter name, cannot be read: the guard denies."""


def frontmatter_name(path) -> str | None:
    """The `name:` of the frontmatter block that opens the file, unquoted; None when there is none.
    Raises OSError or UnicodeDecodeError when the file cannot be read."""
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].rstrip() != "---":
        return None
    for line in lines[1:]:
        if line.rstrip() == "---":
            return None
        if line.startswith("name:"):
            value = line[len("name:"):].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1].strip()
            return value or None
    return None


def analyst_types(agents_dir=None) -> frozenset:
    """`business-case:<frontmatter name>` for each `case-*-analyst.md` in agents_dir (default
    AGENTS_DIR). AgentsUnreadable when the folder, a file, or a file's name cannot be read."""
    folder = Path(agents_dir) if agents_dir is not None else AGENTS_DIR
    types = set()
    try:
        files = sorted(p for p in folder.iterdir() if _ANALYST_FILE.match(p.name) and paths.stat_is_file(p))
        for path in files:
            name = frontmatter_name(path)
            if name is None:
                raise AgentsUnreadable(f"{path} has no frontmatter name")
            types.add(PLUGIN_PREFIX + name)
    except (OSError, UnicodeDecodeError) as exc:
        if isinstance(exc, AgentsUnreadable):
            raise
        raise AgentsUnreadable(f"the analyst agents in {folder} cannot be read: {exc}") from None
    return frozenset(types)


def bare(name: str) -> str:
    """The agent name without its plugin: `business-case:case-x-analyst` -> `case-x-analyst`."""
    return name.split(":", 1)[1] if ":" in name else name


def _agent_folders(cwd) -> list:
    """The agent folders a bare name may come from: $CLAUDE_CONFIG_DIR/agents when set, ~/.claude/agents,
    and the .claude/agents of $CLAUDE_PROJECT_DIR (when set) and of cwd, each with its parents up to and
    including the git root (the first folder holding .git) or HOME."""
    home = Path.home().resolve()
    folders = []
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    if config:
        folders.append(Path(config) / "agents")
    folders.append(home / ".claude" / "agents")
    starts = [os.environ.get("CLAUDE_PROJECT_DIR"), cwd]
    for start in (Path(s).resolve() for s in starts if s):
        for folder in (start, *start.parents):
            folders.append(folder / ".claude" / "agents")
            if (folder / ".git").exists() or folder == home:
                break
    return folders


def _shadowed(name: str, cwd) -> bool:
    """True when an agent in one of _agent_folders(cwd) is named `name`, by file stem or by frontmatter
    name. A file that cannot be read counts as one (fail closed)."""
    for folder in _agent_folders(cwd):
        try:
            if not paths.stat_is_dir(folder):
                continue
        except OSError:
            return True
        for path in folder.rglob("*.md"):
            if path.stem == name:
                return True
            try:
                if frontmatter_name(path) == name:
                    return True
            except (OSError, UnicodeDecodeError):
                return True
    return False


def _as_analyst(name, hook_input: dict):
    """(full analyst type, None) when `name` is an analyst under its full name, or under its bare name
    with no project or user agent of that name; (None, refusal) for a shadowed bare analyst name;
    (None, None) when it is not an analyst. A name without an analyst's shape is not one, and the
    agents folder is not read for it. Raises AgentsUnreadable."""
    if not isinstance(name, str) or not _ANALYST_NAME.match(name.rsplit(":", 1)[-1]):
        return None, None
    types = analyst_types()
    if name in types:
        return name, None
    if ":" not in name and PLUGIN_PREFIX + name in types:
        if _shadowed(name, hook_input.get("cwd") or os.getcwd()):
            return None, (f"the bare name {name} is also a project or user agent; name the analyst in full: "
                          f"{PLUGIN_PREFIX}{name}")
        return PLUGIN_PREFIX + name, None
    return None, None


def _reply_slot(target: Path):
    """(case folder, NNN) when target, already resolved, is `<case>/team/reply-NNN.json` in the exact
    spelling, with the case a folder named by a slug inside business-cases; else None."""
    m = _REPLY_NAME.match(target.name)
    team = target.parent
    case = team.parent
    if (m is None or team.name != paths.TEAM_DIR or case.parent.name != "business-cases"
            or not paths.SLUG_PATTERN.match(case.name)):
        return None
    return case, int(m.group(1))


def _brief_at(case: Path, nnn: int):
    """The brief that sits at `<case>/team/brief-NNN.txt`, read through read_brief, or a refusal reason.
    Its case_dir and reply_path headers must name where the file sits: read_brief does not check that."""
    path = case / team_files.brief_relpath(nnn)
    if not path.is_file():
        return None, f"no {team_files.brief_relpath(nnn)} for this analyst reply"
    try:
        brief = team_files.read_brief(path)
    except team_files.TeamRefused as exc:
        return None, f"the analyst's brief is refused: {exc}"
    if brief.case_dir != str(case) or brief.reply_path != str(case / team_files.reply_relpath(nnn)):
        return None, (f"{team_files.brief_relpath(nnn)} names another case folder or reply path than where it "
                      "sits; it authorises no analyst Write and no analyst dispatch")
    return brief, None


def _deny(reason: str):
    return judge_receipt.GuardDecision("deny", reason)


def decide_analyst_dispatch(hook_input: dict):
    """PreToolUse on Agent|Task. None when the sub-agent is not an analyst. An analyst's prompt must be
    exactly the bytes of an open brief for that analyst."""
    if hook_input.get("tool_name") not in judge_receipt.DISPATCH_TOOLS:
        return None
    tool_input = hook_input.get("tool_input") or {}
    try:
        analyst, refusal = _as_analyst(tool_input.get("subagent_type"), hook_input)
    except AgentsUnreadable as exc:
        return _deny(f"no dispatch while the analyst agents cannot be read: {exc}")
    if refusal is not None:
        return _deny(refusal)
    if analyst is None:
        return None
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return _deny(f"the analyst's dispatch carries no prompt; {DISPATCH_RULE}")
    lines = prompt.split("\n")
    reply_lines = [line for line in lines if line.startswith("reply_path: ")]
    if lines[0] != team_files.BRIEF_FIRST_LINE or len(reply_lines) != 1:
        return _deny(DISPATCH_RULE)
    raw = Path(reply_lines[0][len("reply_path: "):])
    slot = _reply_slot(raw.resolve()) if raw.is_absolute() else None
    if slot is None:
        return _deny(DISPATCH_RULE)
    case, nnn = slot
    brief, reason = _brief_at(case, nnn)
    if brief is None:
        return _deny(reason)
    try:
        prompt_bytes = prompt.encode("utf-8")
    except UnicodeEncodeError:  # a lone surrogate from a JSON escape
        return _deny(DISPATCH_RULE)
    if prompt_bytes != (case / team_files.brief_relpath(nnn)).read_bytes():
        return _deny(DISPATCH_RULE)
    if brief.agent_type != analyst:
        return _deny(f"{team_files.brief_relpath(nnn)} is for the analyst {brief.agent_type}, not {analyst}")
    state = team_files.brief_state(case, nnn)
    if state != "open" or paths.stat_exists(case / team_files.receipt_relpath(nnn)):
        state = "answered" if state == "open" else state
        return _deny(f"{team_files.brief_relpath(nnn)} is {state}; an analyst runs only on an open brief")
    return judge_receipt.GuardDecision("pass", f"the prompt is exactly {team_files.brief_relpath(nnn)}, an open brief")


def decide_analyst_write(hook_input: dict):
    """PreToolUse on Write|Edit|MultiEdit|NotebookEdit. None when the writer is not an analyst. An
    analyst writes once, with Write, to the reply slot of an open brief for that analyst: the brief's own
    team folder + reply-NNN.json, never the path its header names alone."""
    tool = hook_input.get("tool_name")
    if tool not in judge_receipt.GUARDED_TOOLS:
        return None
    try:
        analyst, refusal = _as_analyst(hook_input.get("agent_type"), hook_input)
    except AgentsUnreadable as exc:
        return _deny(f"no file write while the analyst agents cannot be read: {exc}")
    if refusal is not None:
        return _deny(refusal)
    if analyst is None:
        return None
    tool_input = hook_input.get("tool_input") or {}
    raws = [tool_input[k] for k in ("file_path", "notebook_path") if tool_input.get(k)]
    if not raws or not all(isinstance(r, str) for r in raws):
        return _deny("no readable path; an analyst writes only its reply, at its brief's reply slot")
    targets = [judge_receipt._target(hook_input, r) for r in raws]
    target = targets[0]
    if any(t != target for t in targets):
        return _deny("the analyst's Write names two different paths")
    if tool != "Write":
        return _deny("an analyst writes its reply once, with Write; it never edits a file")
    slot = _reply_slot(target)
    if slot is None:
        return _deny(f"an analyst may write only team/reply-NNN.json in the exact spelling, not {target}")
    case, nnn = slot
    brief, reason = _brief_at(case, nnn)
    if brief is None:
        return _deny(reason)
    if brief.agent_type != analyst:
        return _deny(f"{team_files.brief_relpath(nnn)} is for the analyst {brief.agent_type}, not {analyst}")
    state = team_files.brief_state(case, nnn)
    if state in ("cancelled", "expired"):
        return _deny(f"{team_files.brief_relpath(nnn)} is {state}; the analyst may not write its reply")
    if state == "answered" or paths.stat_exists(target) or paths.stat_exists(case / team_files.receipt_relpath(nnn)):
        return _deny(f"{team_files.reply_relpath(nnn)} is already written; an analyst run writes once")
    try:
        same = [n for n in team_files.open_briefs(case)
                if team_files.read_brief(case / team_files.brief_relpath(n)).agent_type == analyst]
    except team_files.TeamRefused as exc:
        return _deny(f"the analyst's open briefs cannot be read: {exc}")
    if len(same) > 1:
        return _deny(f"{len(same)} open briefs for the analyst {analyst} ({', '.join(f'{n:03d}' for n in same)}); "
                     "a reply binds to its brief only while one brief is open for its analyst")
    if not isinstance(tool_input.get("content"), str):
        return _deny("the analyst's Write carries no content")
    found = _reply_digest(tool_input["content"])
    if found is None:
        return _deny(MALFORMED_REPLY)
    if found != brief.sha256:
        # Generic on purpose: naming the slot's brief or its digest would tell a stale run what to copy.
        return _deny(DIGEST_REFUSAL)
    return judge_receipt.GuardDecision("allow", ALLOW_REASON)


def _reply_digest(text):
    """The `brief_sha256` string of a reply's JSON object; None when there is none."""
    try:
        reply = json.loads(text)
    except (TypeError, ValueError):
        return None
    value = reply.get("brief_sha256") if isinstance(reply, dict) else None
    return value if isinstance(value, str) else None


def record_analyst_write(hook_input: dict):
    """PostToolUse on Write, after the Write succeeded. For an analyst's reply at the slot of its own
    brief, hash the bytes on disk and create team/reply-NNN.receipt.json, once. Otherwise None."""
    if hook_input.get("tool_name") != "Write":
        return None
    try:
        analyst, _ = _as_analyst(hook_input.get("agent_type"), hook_input)
    except AgentsUnreadable:
        return None
    raw = (hook_input.get("tool_input") or {}).get("file_path")
    if analyst is None or not isinstance(raw, str) or not raw:
        return None
    target = judge_receipt._target(hook_input, raw)
    slot = _reply_slot(target)
    if slot is None:
        return None
    case, nnn = slot
    brief, _ = _brief_at(case, nnn)
    if brief is None or brief.agent_type != analyst or not target.is_file():
        return None
    path = case / team_files.receipt_relpath(nnn)
    if path.exists():
        return None
    content = (hook_input.get("tool_input") or {}).get("content")
    data = target.read_bytes()
    try:
        written = content.encode("utf-8") if isinstance(content, str) else None
    except UnicodeEncodeError:
        written = None
    if data != written:
        return None  # the bytes on disk are not the bytes this Write carried: something else wrote them
    if _reply_digest(content) != brief.sha256:
        return None  # the reply answers another brief
    receipt = {"brief": team_files.brief_relpath(nnn), "reply": team_files.reply_relpath(nnn),
               "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
               "agent_id": str(hook_input.get("agent_id", "")), "agent_type": analyst,
               "session_id": str(hook_input.get("session_id", "")), "tool_name": "Write"}
    judge_receipt.write_receipt(path, receipt)
    return path


def verify_analyst_receipt(case_dir, nnn: int) -> dict:
    """The receipt for analyst reply NNN, or judge_receipt.ReceiptRefused naming every problem. The
    receipt's agent_type must be its brief's, and its session one the case recorded."""
    case_dir = Path(case_dir)
    receipt_path = case_dir / team_files.receipt_relpath(nnn)
    reply_path = case_dir / team_files.reply_relpath(nnn)
    problems = []
    receipt = None
    if not receipt_path.is_file():
        problems.append(f"no {team_files.receipt_relpath(nnn)}: no completed analyst Write was recorded for this reply")
    else:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except ValueError:
            problems.append(f"{team_files.receipt_relpath(nnn)} is not valid JSON")
        else:
            if not isinstance(receipt, dict):
                problems.append(f"{team_files.receipt_relpath(nnn)} is not a JSON object")
                receipt = None
    if receipt is not None:
        if tuple(sorted(receipt)) != tuple(sorted(judge_receipt.RECEIPT_FIELDS)):
            problems.append("the receipt's fields are not the receipt field set")
        try:
            brief = team_files.read_brief(case_dir / team_files.brief_relpath(nnn))
        except team_files.TeamRefused as exc:
            problems.append(f"the receipt's brief is refused: {exc}")
        else:
            if receipt.get("agent_type") != brief.agent_type:
                problems.append(f"the receipt's agent_type is {receipt.get('agent_type')!r}, not {brief.agent_type!r}")
            if reply_path.is_file():
                try:
                    reply_digest = _reply_digest(reply_path.read_bytes().decode("utf-8"))
                except UnicodeDecodeError:
                    reply_digest = None
                if reply_digest != brief.sha256:
                    problems.append(f"the reply's brief_sha256 is not the digest of {team_files.brief_relpath(nnn)}")
        for key, want in (("brief", team_files.brief_relpath(nnn)), ("reply", team_files.reply_relpath(nnn)),
                          ("tool_name", "Write")):
            if receipt.get(key) != want:
                problems.append(f"the receipt's {key} is {receipt.get(key)!r}, not {want!r}")
        try:
            recorded = {s.get("id") for s in case_files.read_meta(case_dir)["sessions"]}
        except (case_files.CaseRefused, KeyError, TypeError, AttributeError):
            recorded = set()
        if receipt.get("session_id") not in recorded:
            problems.append("the receipt's session is not a session this case recorded")
    if not reply_path.is_file():
        problems.append(f"no {team_files.reply_relpath(nnn)}")
    elif receipt is not None:
        on_disk = digest.file_digest(reply_path)
        if on_disk["sha256"] != receipt.get("sha256") or on_disk["bytes"] != receipt.get("bytes"):
            problems.append("the reply's bytes differ from the bytes the receipt recorded")
    if problems:
        raise judge_receipt.ReceiptRefused("; ".join(problems))
    return receipt
