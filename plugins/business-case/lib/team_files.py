"""The team folder: the files the coach's analyst team works through, and the budget on briefs.

Everything lives under `<case>/team/`. None of it is a judge input (`paths.JUDGE_INPUT_GLOBS` names
no `team` file). This module is the one place that defines the file shapes below; a later task that
writes or reads one of them reads the definition here.

Brief files
-----------
`brief-NNN.txt` is fixed text code writes for one analyst run. Lines, in this order: the first line
`business-case team brief v1`, then `case_dir:`, `session_id:`, `agent_type:`, `reply_kind:`
(`plan` or `results`), `reply_path:`, `written_at:` (UTC, `YYYY-MM-DDTHH:MM:SSZ`), `items:` (a comma
list), `sha256:` (the digest of every other line), `body:`, and one line holding one JSON object.
`read_brief` refuses a file that is not exactly what `write_brief` renders for what the file says.
`brief-NNN.cancelled.json` marks a brief the coach cancelled: `{"cancelled": NNN, "at", "session_id",
"agent_type", "reply_kind", "items"}`, the last four as far as the brief can still be read. A cancelled brief
that cannot be read counts by them, in the round cap and the budget. The analyst's own files are
`reply-NNN.json`, `reply-NNN.receipt.json` and `reply-NNN.check.json` (`reply_relpath`,
`receipt_relpath`, `check_relpath`).

A brief is `open` until it is `cancelled`, `answered` (its reply file is there) or `expired`
(`BRIEF_EXPIRY_MINUTES` after `written_at`). A cancelled or expired brief frees its slot in
`RUNNING_MAX`. It still counts in `RUNS_PER_ITEM` and `RUNS_PER_SESSION`; a refused brief counts in
neither, because a refused brief writes no file.

Every path below that ends `result_file` is relative to the git root. `repo_relative` turns a path
into that form.

cards-NNN.json
--------------
One file per coach call NNN, written atomically, cumulative:

    {"call": NNN, "merged": [<brief NNN>], "capped": [<brief NNN>], "cards": {"<key>": {
        "brief": NNN | null, "id": "<card id>" | null,
        "made_by": "plan" | "conflict" | "case" | "gap" | "rerun" | "reading",
        "round": 1 | 2, "blocks": "now" | "later", "hard_to_undo": bool, "header": str,
        "question": str, "options": [{"label", "description", "sets"?}],
        "answer": {"label": str, "settled_by": "person" | "recommended"} | null,
        "free_text": [str],
        "passed": [<call NNN>],
        "last_ask": bool, "held": bool, "again_because": str | null,
        "subject": {"result_file"?: str, "item"?: str, "command"?: str, "finished_at"?: str,
                    "run"?: str, "briefs"?: [NNN], "card"?: str, "label"?: str, "text"?: str}}}}

`header` (at most 12 characters) is the plan card's own, or one code made for a code-made card.
`merged` lists every plan brief whose checked plan a call has merged, so no later call merges it again.
`capped` lists every second-brief plan the after-cap rule has applied to, so it applies once.
A key is `<brief NNN>:<id>` or `code:<n>`. `passed` holds each call in which the coach passed an answer
for the card, counting `[No preference]` and free text; a card with an empty `passed` list is "not yet
asked". `last_ask` is true while the one extra ask a `hard_to_undo` card gets after the cap is due; the
next answer passed for it ends it, and `held` turns true when that answer is no option (`[No preference]` or
free text): code never fills a held card. A card written before `held` existed reads as `held: false`.
`again_because` is the reason a card that was asked before is asked again, or null; a card written before
`again_because` existed reads as `again_because: null`.
`subject.result_file` is relative to the git root. A case card whose `answer.label` equals
`CASE_ANSWER_LABEL` is the "case answer" for the `subject.result_file` it names; its subject also holds
the file's `command` and `finished_at`. A gap card's subject is `{"item"}`. A rerun card's subject holds
its `command`, the key of the earlier run it asks about (`run`), and the plan briefs it covers (`briefs`).
A reading card (`made_by: reading`, header "Your words") asks whether the coach's reading of the person's
text is right: its subject holds the key of the card it asks about (`card`), the option label of the reading
(`label`) and the person's text (`text`).

answers-NNN.json
----------------
The plugin result standard's answers shape (`plugin_result.check_answers` passes it).

runs.json
---------
    {"runs": [{"key": "<run_id>" | "person:<NNN>:<command>", "command": str, "run_id": str | null,
               "briefs": [NNN], "state": "open" | "ended" | "gap",
               "result_file": "<relative to the git root>" | null,
               "finished_at": str | null, "reason": str | null}]}

A key is `person:<NNN>:<command>` for any run with no `run_id`, and not only for a command with
`coach_runs: false`. NNN is the lowest brief that names the command; `briefs` lists every brief that
names it (`person_run_key`).

Python 3.9 syntax only: `judge_receipt` imports this module in the hook.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib import case_files, clock, digest, paths

try:
    import fcntl  # POSIX only
except ImportError:  # Windows: team calls run without the lock
    fcntl = None

BRIEF_FIRST_LINE = "business-case team brief v1"
# Measured: the 2026-11-03 probe (CLI, haiku) took 34 s, 32 s and 30 s for three plan rounds; the live run took
# 12 to 41 s for all twelve analyst rounds. 60 minutes is a margin for a person who answers late: a long expiry
# only holds a running place, which `team-brief --cancel` frees.
BRIEF_EXPIRY_MINUTES = 60
RUNS_PER_ITEM = 4
RUNS_PER_SESSION = 24
RUNNING_MAX = 3

REPLY_KINDS = ("plan", "results")
STATES = ("open", "answered", "cancelled", "expired")

# The "case answer" a case card carries when the person chose to use a result for this case.
CASE_ANSWER_LABEL = "use it for this case"
RUNS_FILE = "runs.json"
# Every bc.py team writer holds an exclusive lock on this file for the whole command (final review I1).
TEAM_LOCK = ".lock"
_ANALYST_PREFIX = "business-case:"
UNREADABLE_REMEDY = "cancel it with bc.py team-brief --cancel {nnn}"

_NNN = r"[0-9]{3}|[1-9][0-9]{3,}"
_BRIEF_NAME = re.compile(rf"^brief-({_NNN})\.txt$")
_STAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
_HEADER_KEYS = ("case_dir", "session_id", "agent_type", "reply_kind", "reply_path", "written_at", "items",
                "sha256")
_PLUGIN_JSON = paths.PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


class TeamRefused(ValueError):
    """A team file this module will not write, or a file that is not one it wrote."""


class TeamBudgetExhausted(TeamRefused):
    """A brief refused because its item or its session has used its runs."""


@dataclass
class Brief:
    nnn: int
    case_dir: str
    session_id: str
    agent_type: str
    reply_kind: str
    reply_path: str
    written_at: str
    items: list
    body: dict
    sha256: str = ""  # the brief's own `sha256:` header; an analyst's reply carries it as `brief_sha256`


# -- names ------------------------------------------------------------------------------------

def brief_name(nnn: int) -> str:
    return f"brief-{nnn:03d}.txt"


def _cancel_name(nnn: int) -> str:
    return f"brief-{nnn:03d}.cancelled.json"


def brief_relpath(nnn: int) -> str:
    return f"{paths.TEAM_DIR}/{brief_name(nnn)}"


def reply_relpath(nnn: int) -> str:
    return f"{paths.TEAM_DIR}/reply-{nnn:03d}.json"


def receipt_relpath(nnn: int) -> str:
    return f"{paths.TEAM_DIR}/reply-{nnn:03d}.receipt.json"


def check_relpath(nnn: int) -> str:
    return f"{paths.TEAM_DIR}/reply-{nnn:03d}.check.json"


def cards_relpath(nnn: int) -> str:
    return f"{paths.TEAM_DIR}/cards-{nnn:03d}.json"


def answers_relpath(nnn: int) -> str:
    return f"{paths.TEAM_DIR}/answers-{nnn:03d}.json"


def runs_relpath() -> str:
    return f"{paths.TEAM_DIR}/{RUNS_FILE}"


def person_run_key(nnn: int, command: str) -> str:
    """The `runs.json` key of a run with no run_id: `person:<NNN>:<command>`."""
    return f"person:{nnn:03d}:{command}"


def load_runs(case_dir) -> list:
    """The runs in `team/runs.json`; [] before the first run."""
    path = Path(case_dir).resolve() / runs_relpath()
    try:
        if not paths.stat_is_file(path):
            return []
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise TeamRefused(f"{runs_relpath()} cannot be read") from None
    if not isinstance(doc, dict) or not isinstance(doc.get("runs"), list) \
            or not all(isinstance(r, dict) for r in doc["runs"]):
        raise TeamRefused(f"{runs_relpath()} is not a run list")
    return doc["runs"]


def plugin_version() -> str:
    return json.loads(_PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


# -- the git root -----------------------------------------------------------------------------

def git_root(path):
    """The nearest folder at or above `path` that holds a `.git` (a folder, or a file in a worktree);
    None when there is none."""
    start = Path(path).resolve()
    for folder in (start, *start.parents):
        if (folder / ".git").exists():
            return folder
    return None


def repo_root(case_dir) -> Path:
    """The git root, resolved; with no `.git` above the case, the folder that holds `business-cases/`.
    Every path that `result_file` names is relative to it."""
    root = git_root(case_dir)
    if root is not None:
        return root.resolve()
    case = Path(case_dir).resolve()
    return case.parent.parent if case.parent.name == "business-cases" else case.parent


def inside_root(root, path):
    """`path` relative to `root`, as POSIX, once every symlink and `..` is resolved; None when it leaves
    the root or cannot be resolved. The one path rule for files a reply or a file names."""
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except (OSError, ValueError, RuntimeError):
        return None


def repo_relative(path, case_dir) -> str:
    """`path` as a POSIX path relative to the git root, the form `result_file` takes. An absolute path
    must lie inside the root. A relative path is taken as already relative to the root and is only
    cleaned; one that leaves the root is refused."""
    text = os.fspath(path)
    if not text.strip():
        raise TeamRefused("a result file path is empty")
    root = repo_root(case_dir)
    if Path(text).is_absolute():
        try:
            return Path(text).resolve().relative_to(root).as_posix()
        except ValueError:
            raise TeamRefused(f"{text} is outside the git root {root}") from None
    clean = posixpath.normpath(text.replace("\\", "/"))
    if clean in (".", "..") or clean.startswith("../"):
        raise TeamRefused(f"{text} is outside the git root")
    return clean


def brief_run_object(case_dir, labels: list, written_at: str) -> dict:
    """The `run` block of a plugin result a brief stands for: `started_at` and `finished_at` are
    `written_at`, the mode is interactive, the subject joins the labels, `case` is relative to the git root."""
    if not isinstance(labels, list) or not labels or not all(isinstance(x, str) and x for x in labels):
        raise TeamRefused("a run object needs one or more labels")
    if not isinstance(written_at, str) or not _STAMP.match(written_at):
        raise TeamRefused(f"written_at {written_at!r} is not a UTC time like 2026-10-27T12:00:00Z")
    return {"started_at": written_at, "finished_at": written_at, "mode": "interactive",
            "subject": "; ".join(labels), "case": repo_relative(Path(case_dir).resolve(), case_dir)}


# -- time -------------------------------------------------------------------------------------

def utc_stamp(now) -> str:
    """`now` as `YYYY-MM-DDTHH:MM:SSZ`: a string as given, a datetime in UTC, or the clock."""
    if now is None:
        now = clock.now()
    if isinstance(now, datetime):
        moment = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).strftime(_STAMP_FORMAT)
    if not isinstance(now, str) or not _STAMP.match(now):
        raise TeamRefused(f"time {now!r} is not a UTC time like 2026-10-27T12:00:00Z")
    return now


def _moment(stamp: str) -> datetime:
    return datetime.strptime(stamp, _STAMP_FORMAT).replace(tzinfo=timezone.utc)


# -- the brief file ---------------------------------------------------------------------------

def _one_line(value, what: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\n" in value or "\r" in value:
        raise TeamRefused(f"{what} must be one non-blank line")
    return value


def _render(case_dir: str, session_id: str, agent_type: str, reply_kind: str, nnn: int, written_at: str,
            items: list, body: dict) -> str:
    head = [
        BRIEF_FIRST_LINE,
        f"case_dir: {case_dir}",
        f"session_id: {session_id}",
        f"agent_type: {agent_type}",
        f"reply_kind: {reply_kind}",
        f"reply_path: {case_dir}/{reply_relpath(nnn)}",
        f"written_at: {written_at}",
        f"items: {', '.join(items)}",
    ]
    tail = ["body:", json.dumps(body, sort_keys=True, ensure_ascii=False)]
    return "\n".join(head + [f"sha256: {_digest_of(head + tail)}"] + tail) + "\n"


def _digest_of(lines: list) -> str:
    return digest.sha256_hex(("\n".join(lines) + "\n").encode("utf-8"))


def brief_number(path) -> int:
    match = _BRIEF_NAME.match(Path(path).name)
    if not match:
        raise TeamRefused(f"{path} is not a team brief file name")
    return int(match.group(1))


def read_brief(path) -> Brief:
    """Parse a brief file. Refused unless the file is exactly what `write_brief` renders for what it says."""
    path = Path(path)
    nnn = brief_number(path)
    try:
        text = path.read_bytes().decode("utf-8")
    except OSError as exc:
        raise TeamRefused(f"{path} cannot be read: {exc.strerror or exc}") from None
    except UnicodeDecodeError:
        raise TeamRefused(f"{path} is not UTF-8") from None
    lines = text.split("\n")
    shaped = len(lines) == 12 and lines[0] == BRIEF_FIRST_LINE and lines[9] == "body:" and lines[11] == ""
    values = {}
    if shaped:
        for key, line in zip(_HEADER_KEYS, lines[1:9]):
            prefix = key + ":"
            if not line.startswith(prefix + " ") and line != prefix:
                shaped = False
                break
            values[key] = line[len(prefix):].lstrip(" ") if line != prefix else ""
    if not shaped:
        raise TeamRefused(f"{path} is not a team brief")
    if _digest_of(lines[:8] + lines[9:11]) != values["sha256"]:
        raise TeamRefused(f"{path} has changed since it was written: its text does not match its digest")
    try:
        body = json.loads(lines[10])
    except ValueError:
        raise TeamRefused(f"{path} has a body that is not JSON") from None
    items = values["items"].split(", ") if values["items"] else []
    if not isinstance(body, dict) or values["reply_kind"] not in REPLY_KINDS or not _STAMP.match(values["written_at"]) \
            or _render(values["case_dir"], values["session_id"], values["agent_type"], values["reply_kind"], nnn,
                       values["written_at"], items, body) != text:
        raise TeamRefused(f"{path} does not match the team brief template")
    return Brief(nnn=nnn, case_dir=values["case_dir"], session_id=values["session_id"],
                 agent_type=values["agent_type"], reply_kind=values["reply_kind"],
                 reply_path=values["reply_path"], written_at=values["written_at"], items=items, body=body,
                 sha256=values["sha256"])


def _brief_numbers(team_dir: Path) -> list:
    if not paths.stat_is_dir(team_dir):
        return []
    return sorted(brief_number(p) for p in team_dir.iterdir() if _BRIEF_NAME.match(p.name))


def _scan(case_dir) -> tuple:
    """(every readable brief, in NNN order; [(NNN, why)] for each brief that cannot be read and is not
    cancelled). A cancelled brief that cannot be read is left out of both: it names no item and holds no slot."""
    team_dir = Path(case_dir).resolve() / paths.TEAM_DIR
    briefs, unreadable = [], []
    for n in _brief_numbers(team_dir):
        try:
            briefs.append(read_brief(team_dir / brief_name(n)))
        except TeamRefused as exc:
            marker = team_dir / _cancel_name(n)
            if marker.is_file():
                briefs.append(_cancelled_stand_in(n, marker))
            else:
                unreadable.append((n, str(exc)))
    return briefs, unreadable


def _salvage(path: Path, owners) -> dict:
    """What can still be read of a brief that `read_brief` refuses: its `session_id`, `agent_type` and
    `reply_kind` header lines, and its items, from the `items:` line and from the body's `items` ids (both, as
    either may be the damaged part). Only the items `owners` (the map's item -> owner) gives the analyst its
    `agent_type` header names are kept, so a damaged or crafted body spends no other analyst's items; with no
    readable analyst, or no `owners`, it keeps no item and counts only in the session budget."""
    try:
        lines = path.read_bytes().decode("utf-8", errors="replace").split("\n")
    except OSError:
        lines = []
    head = {}
    for line in lines[1:9]:
        key, sep, value = line.partition(": ")
        if sep and key in ("session_id", "agent_type", "reply_kind", "items"):
            head[key] = value
    items = [i for i in head.get("items", "").split(", ") if i]
    if "body:" in lines:
        try:
            body = json.loads(lines[lines.index("body:") + 1])
            items += [e["id"] for e in body.get("items", []) if isinstance(e, dict) and isinstance(e.get("id"), str)]
        except (ValueError, IndexError, AttributeError, TypeError):
            pass
    kind = head.get("reply_kind")
    agent = head.get("agent_type", "")
    analyst = agent[len(_ANALYST_PREFIX):] if agent.startswith(_ANALYST_PREFIX) else None
    items = [i for i in dict.fromkeys(items) if analyst is not None and (owners or {}).get(i) == analyst]
    return {"session_id": head.get("session_id", ""), "agent_type": agent,
            "reply_kind": kind if kind in REPLY_KINDS else "", "items": items}


def _cancelled_stand_in(nnn: int, marker: Path) -> Brief:
    """A cancelled brief that cannot be read, as its cancel marker recorded it: it still counts in the round
    cap (spec §5.6) and in `RUNS_PER_ITEM` and `RUNS_PER_SESSION` by the items and session the marker kept."""
    try:
        kept = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        kept = {}
    kept = kept if isinstance(kept, dict) else {}
    items = kept.get("items") if isinstance(kept.get("items"), list) else []
    at = kept.get("at") if isinstance(kept.get("at"), str) and _STAMP.match(kept["at"]) else "1970-01-01T00:00:00Z"
    return Brief(nnn=nnn, case_dir="", session_id=str(kept.get("session_id") or ""),
                 agent_type=str(kept.get("agent_type") or ""), reply_kind=str(kept.get("reply_kind") or ""),
                 reply_path="", written_at=at, items=[i for i in items if isinstance(i, str)], body={})


def unreadable_briefs(case_dir) -> list:
    """[(NNN, why)] for each brief that cannot be read and is not cancelled; `team-brief --status` names each
    with UNREADABLE_REMEDY."""
    return _scan(case_dir)[1]


def all_briefs(case_dir) -> list:
    """Every brief of the case, in NNN order, whatever its state. Refused while a brief that is not cancelled
    cannot be read: the refusal names it and UNREADABLE_REMEDY."""
    briefs, unreadable = _scan(case_dir)
    if unreadable:
        nnn, why = unreadable[0]
        raise TeamRefused(f"{why}; if it cannot be put back as it was written, "
                          + UNREADABLE_REMEDY.format(nnn=nnn))
    return briefs


def _state_of(case_dir: Path, brief: Brief, now: str) -> str:
    team_dir = case_dir / paths.TEAM_DIR
    if paths.stat_is_file(team_dir / _cancel_name(brief.nnn)):
        return "cancelled"
    if paths.stat_is_file(case_dir / reply_relpath(brief.nnn)):
        return "answered"
    if _moment(now) >= _moment(brief.written_at) + timedelta(minutes=BRIEF_EXPIRY_MINUTES):
        return "expired"
    return "open"


@contextmanager
def team_lock(case_dir):
    """Hold the case's team lock (`team/.lock`, made with the folder when absent) until the block ends.

    Every `bc.py` command that writes team state (a brief, a cancel, a card record, an answers file, the run
    list) runs inside it, so its reads and its writes are one step for every other team command. On Windows
    `fcntl` does not exist and the block runs without the lock (`chained_log.locked_append`)."""
    team_dir = Path(case_dir).resolve() / paths.TEAM_DIR
    try:
        team_dir.mkdir(exist_ok=True)
    except OSError as exc:
        raise TeamRefused(f"cannot make the {paths.TEAM_DIR} folder: {exc}") from None
    # chained_log.locked_append's pattern, written here: the hook imports this module, and its closure
    # stays without chained_log.
    try:
        fd = os.open(str(team_dir / TEAM_LOCK), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    except OSError as exc:
        raise TeamRefused(f"{paths.TEAM_DIR}/{TEAM_LOCK}: cannot open the team lock: {exc}") from None
    try:
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX)
        except OSError as exc:
            raise TeamRefused(f"{paths.TEAM_DIR}/{TEAM_LOCK}: cannot lock: {exc}") from None
        yield
    finally:
        os.close(fd)  # closing the file releases the lock


def _create_new(path: Path, data: bytes) -> bool:
    """Write `data` to a new file at `path` in one step; False when `path` already exists."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        try:
            os.link(tmp, path)
        except FileExistsError:
            return False
        return True
    finally:
        os.unlink(tmp)


def write_brief(case_dir, *, agent_type: str, reply_kind: str, items: list, body: dict, now=None) -> Path:
    """Write the next `team/brief-NNN.txt`; returns its path.

    Refused, with nothing written and nothing counted, when an input is malformed, when an item has used
    `RUNS_PER_ITEM` briefs or the session `RUNS_PER_SESSION` (TeamBudgetExhausted), or when a brief for
    `agent_type` is open or `RUNNING_MAX` briefs are open (TeamRefused). Needs a session."""
    _one_line(agent_type, "agent_type")
    if reply_kind not in REPLY_KINDS:
        raise TeamRefused(f"reply_kind must be one of {', '.join(REPLY_KINDS)}")
    if not isinstance(items, list) or not all(isinstance(i, str) and i and i == i.strip() and "," not in i
                                              and "\n" not in i and "\r" not in i for i in items):
        raise TeamRefused("items must be a list of names with no comma and no line break")
    if not isinstance(body, dict):
        raise TeamRefused("the body must be a JSON object")
    try:
        json.dumps(body)
    except (TypeError, ValueError) as exc:
        raise TeamRefused(f"the body cannot be written as JSON: {exc}") from None
    case_dir = Path(case_dir).resolve()
    session_id, written_at, briefs = check_room(case_dir, agent_type=agent_type, items=items, now=now)
    team_dir = case_dir / paths.TEAM_DIR
    team_dir.mkdir(exist_ok=True)
    nnn = max((b.nnn for b in briefs), default=0) + 1
    while True:
        text = _render(str(case_dir), session_id, agent_type, reply_kind, nnn, written_at, items, body)
        path = team_dir / brief_name(nnn)
        if _create_new(path, text.encode("utf-8")):
            return path
        nnn += 1


def check_room(case_dir, *, agent_type: str, items: list, now=None) -> tuple:
    """The budget and running checks `write_brief` makes, writing nothing: (session ID, written_at, every
    brief). Refused as `write_brief` refuses (TeamBudgetExhausted, TeamRefused). `team-brief` runs it before it
    changes any card for a results brief."""
    case_dir = Path(case_dir).resolve()
    session_id = _one_line(case_files.current_session(case_dir)["id"], "the session ID")
    written_at = utc_stamp(now)
    briefs = all_briefs(case_dir)
    for item in dict.fromkeys(items):
        used = sum(1 for b in briefs if item in b.items)
        if used >= RUNS_PER_ITEM:
            raise TeamBudgetExhausted(f"item {item} has used its {RUNS_PER_ITEM} team briefs")
    if sum(1 for b in briefs if b.session_id == session_id) >= RUNS_PER_SESSION:
        raise TeamBudgetExhausted(f"session {session_id} has used its {RUNS_PER_SESSION} team briefs")
    running = [b.nnn for b in briefs if _state_of(case_dir, b, written_at) == "open"]
    same = [n for n in running if any(b.nnn == n and b.agent_type == agent_type for b in briefs)]
    if same:
        raise TeamRefused(f"{brief_name(same[0])} is open for {agent_type}; one brief per analyst runs at once "
                          "(it binds the analyst's reply to its brief); wait for it, or cancel it")
    if len(running) >= RUNNING_MAX:
        raise TeamRefused(f"{len(running)} team briefs are open ({', '.join(f'{n:03d}' for n in running)}); "
                          f"at most {RUNNING_MAX} run at once; wait for one, or cancel it")
    return session_id, written_at, briefs


def state_of(case_dir, brief: Brief, now=None) -> str:
    """The state of a `Brief` from `all_briefs`, reading no file again: a cancelled brief that cannot be read
    is in `all_briefs` only as its marker's stand-in, so `brief_state` by NNN would refuse it."""
    return _state_of(Path(case_dir).resolve(), brief, utc_stamp(now))


def brief_state(case_dir, nnn: int, now=None) -> str:
    """One of `STATES`. Cancelled first, then answered, then expired, else open."""
    case_dir = Path(case_dir).resolve()
    path = case_dir / brief_relpath(nnn)
    if not path.is_file():
        raise TeamRefused(f"team brief {nnn:03d} does not exist")
    return _state_of(case_dir, read_brief(path), utc_stamp(now))


def open_briefs(case_dir, kind=None, now=None, *, readable_only=False) -> list:
    """The numbers of the open briefs, in order; `kind` ("plan" or "results") keeps one `reply_kind`.
    `readable_only` leaves out a brief that cannot be read instead of refusing (`team-brief --status`)."""
    if kind is not None and kind not in REPLY_KINDS:
        raise TeamRefused(f"kind must be one of {', '.join(REPLY_KINDS)}")
    case_dir = Path(case_dir).resolve()
    stamp = utc_stamp(now)
    briefs = _scan(case_dir)[0] if readable_only else all_briefs(case_dir)
    return [b.nnn for b in briefs
            if (kind is None or b.reply_kind == kind) and _state_of(case_dir, b, stamp) == "open"]


def cancel(case_dir, nnn: int, owners=None) -> None:
    """Write `team/brief-NNN.cancelled.json`. A cancelled brief frees its slot. Refused for a brief
    that is not there or is already answered; cancelling twice changes nothing. A brief that cannot be read
    is cancelled whatever its state, so it no longer blocks the team (`all_briefs`)."""
    case_dir = Path(case_dir).resolve()
    try:
        state = brief_state(case_dir, nnn)
    except TeamRefused:
        if not (case_dir / brief_relpath(nnn)).is_file():
            raise
        state = "unreadable"
    if state == "cancelled":
        return
    if state == "answered":
        raise TeamRefused(f"team brief {nnn:03d} is already answered")
    kept = _salvage(case_dir / brief_relpath(nnn), owners)  # so a brief that cannot be read still counts once cancelled
    case_files._write_json(case_dir / paths.TEAM_DIR / _cancel_name(nnn), {"cancelled": nnn, "at": clock.now(), **kept})
