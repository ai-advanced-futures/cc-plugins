#!/usr/bin/env python3
"""The runner guard (ADR-016): in a session that runs a build, approve only the exact runner script calls.

A grant of `allowed-tools` ends with the turn, and its `*` matches any text. This hook gives an `allow` that
does not end with the turn, for 1 call at a time:

- post-bash: a `bc.py session --id <this session>` call that worked marks the session as a build session.
- pre-bash: in a marked session, allow a command that is exactly 1 call of a script in RUNNER_CALLS, of bc.py, or
  of `bc_graph.py publish`.
- pre-write: in a marked session, allow a write under `.<plugin>/` of the project, or in a temporary folder of bc.py.
- pre-read: in a marked session, allow a read of a file of an available runner plugin, or of an answers file of a case.

Each other case gives no decision, so Claude Code applies its own rules: a deny or ask rule still wins. An error
gives no decision too. This hook runs on each Bash call of each session, so it must never stop a call.

Python 3.9 syntax, standard library only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The scripts that a run of the coach calls. A list of first words limits the script to these subcommands, and
# `before` names the options that can come before the subcommand. The first word "name" stands for the call
# `result_name.py <finished_at> <command> <subject> [run_id]`: its first word is a time stamp (TIME_STAMP). See
# test_runner_guard.py: a test compares this table with the text of each route.
RUNNER_CALLS = {
    "competitive-intelligence": {
        "ci_graph.py": {"before": ["--root"], "first": ["ingest", "pages", "view"]},
        "result_name.py": {"first": ["now", "run-id", "name"]},
    },
    "gtm": {
        "result_name.py": {"first": ["now", "run-id", "name"]},
    },
    "jtbd-market-discovery": {
        "composite_scorer.py": {},
        "jtbd_graph.py": {"before": ["--root"], "first": ["write-run"]},
        "jtbd_state.py": {"before": ["--root"], "first": ["finished", "merge-needs", "now", "place-result", "select", "wtp-folder"]},
        "report_exporter.py": {},
        "run_phase_6.py": {},
        "run_phase_7.py": {},
        "run_phase_8.py": {},
        "run_phase_9.py": {},
        "survey_adapter.py": {"first": ["apply", "propose"]},
    },
    "pricing": {
        "brain_read.py": {"before": ["--root"], "first": ["moats", "outcomes", "wtp"]},
        "pricing_calculator.py": {},
        "result_name.py": {"first": ["now", "run-id", "name"]},
    },
    "product-finance": {
        "ai_roi_calculator.py": {},
        "jtbd_read.py": {"before": ["--root"], "first": ["latest", "run"]},
        "market_sizing_calculator.py": {},
        "plugin_result_check.py": {"first": ["result"]},
        "result_name.py": {"first": ["now", "run-id", "name"]},
    },
}
# The save code of the case graph (STORY-89): build.md runs `publish` after each `handoff`, and a judge that runs in
# the background ends the turn before that call. Each other first word (remove, set, ...) gets no decision.
BC_GRAPH_CALL = {"before": ["--root"], "first": ["publish"]}
SESSION_NAME = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
TEMP_FOLDER = re.compile(r"^bc-[a-z0-9-]*-[0-9a-f]{8}$")
TIME_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
KEEP_DAYS = 30
OUTSIDE_QUOTES_REFUSED = set(";&|<>()`$*?[]{}~#!\n")
IN_DOUBLE_QUOTES_REFUSED = set("$`\\!\n")


def words_of(command: str):
    """The words of a command with no shell feature in it, else None. Single quotes keep each character but a
    newline. Outside quotes, a backslash and a newline join 2 lines, `\\'` is a quote character, and each other
    backslash is refused."""
    words, word, quote, i = [], None, None, 0
    while i < len(command):
        c = command[i]
        if quote == "'":
            if c == "\n":
                return None
            if c == "'":
                quote = None
            else:
                word += c
        elif quote == '"':
            if c in IN_DOUBLE_QUOTES_REFUSED:
                return None
            if c == '"':
                quote = None
            else:
                word += c
        elif c in ("'", '"'):
            quote, word = c, word or ""
        elif c == "\\":
            following = command[i + 1:i + 2]
            if following == "'":
                word = (word or "") + "'"
            elif following == "\n":
                pass  # the shell removes both characters, and the word goes on
            else:
                return None
            i += 1
        elif c in " \t":
            if word is not None:
                words.append(word)
                word = None
        elif c in OUTSIDE_QUOTES_REFUSED:
            return None
        else:
            word = (word or "") + c
        i += 1
    if quote:
        return None
    if word is not None:
        words.append(word)
    return words


def subcommands() -> set:
    """The subcommands of bc.py, from its parser, so this list cannot differ from the program."""
    from lib import bc  # imported late: most Bash calls never reach this
    return set(bc.subcommand_names())


def installs(cwd: str) -> dict:
    """The install folder of each map plugin that the install check calls available."""
    from lib import install_check, plugin_map
    states = install_check.check(plugin_map.load(), config_dir=install_check.config_dir(), cwd=Path(cwd))
    return {name: state["install_path"] for name, state in states.items() if state.get("state") == "available"}


def _form_holds(rule: dict, args: list) -> bool:
    first = rule.get("first")
    if first is None:
        return True
    i = 0
    while i + 1 < len(args) and args[i] in rule.get("before", []):
        i += 2
    if i >= len(args):
        return False
    return args[i] in first or ("name" in first and bool(TIME_STAMP.match(args[i])))


def _is_bc(script: str) -> bool:
    """A resolved compare: the install path can pass through a link, such as /tmp on macOS."""
    return os.path.isabs(script) and Path(script).resolve() == ROOT / "lib" / "bc.py"


def _is_bc_graph(script: str) -> bool:
    return os.path.isabs(script) and Path(script).resolve() == ROOT / "scripts" / "bc_graph.py"


def exact_call(command: str, cwd: str) -> bool:
    words = words_of(command)
    if not words or len(words) < 3 or words[:2] != ["uv", "run"]:
        return False
    script, args = words[2], words[3:]
    if _is_bc(script):
        return bool(args) and args[0] in subcommands()
    if _is_bc_graph(script):
        return _form_holds(BC_GRAPH_CALL, args)
    path = Path(script)
    if not path.is_absolute() or ".." in path.parts:
        return False
    for plugin, scripts in RUNNER_CALLS.items():
        if path.name in scripts and plugin in path.parts:
            folder = installs(cwd).get(plugin)
            if not folder:
                return False
            scripts_folder = (Path(folder) / "scripts").resolve()
            # A script sits in `scripts/`, or in `scripts/plugin_result/` (the result checker of product-finance).
            parents = [scripts_folder] + ([scripts_folder / "plugin_result"] if path.name == "plugin_result_check.py" else [])
            return path.is_file() and path.resolve().parent in parents and _form_holds(scripts[path.name], args)
    return False


def write_allowed(file_path: str, project: str) -> bool:
    if not file_path or not os.path.isabs(file_path):
        return False
    path = Path(file_path).resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if path.parent.parent == temp and TEMP_FOLDER.match(path.parent.name):
        return True
    top = Path(project).resolve()
    return any(path.is_relative_to(top / f".{plugin}") and path != top / f".{plugin}" for plugin in RUNNER_CALLS)


# The folders of this plugin that build.md reads in a later turn: the template, the rubric, the extractor rule.
OWN_FOLDERS = ("templates", "rubric", "agents")
ANSWERS_FILE = re.compile(r"^answers-[^/]*\.json$")


def read_allowed(file_path: str, cwd: str) -> bool:
    """A file of an available runner plugin, a file of the template, rubric or agents folder of this plugin, or the
    answers file of a case."""
    if not file_path or not os.path.isabs(file_path):
        return False
    path = Path(file_path).resolve()
    if any(path.is_relative_to(ROOT / folder) for folder in OWN_FOLDERS):
        return True
    if ANSWERS_FILE.match(path.name) and path.parent.name == "team" and path.parent.parent.parent.name == "business-cases":
        return True
    folders = installs(cwd)
    return any(path.is_relative_to(Path(folders[name]).resolve()) for name in RUNNER_CALLS if name in folders)


def marks_folder() -> Path:
    return Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "build-sessions"


def marked(session: str) -> bool:
    return bool(SESSION_NAME.match(session or "")) and (marks_folder() / session).is_file()


def mark(session: str) -> None:
    folder = marks_folder()
    folder.mkdir(parents=True, exist_ok=True)
    limit = time.time() - KEEP_DAYS * 86400
    for old in folder.iterdir():
        if old.stat().st_mtime < limit:
            old.unlink()
    (folder / session).write_text("", encoding="utf-8")


def post_bash(data: dict) -> None:
    session = data.get("session_id") or ""
    words = words_of(data.get("tool_input", {}).get("command", "")) or []
    if (SESSION_NAME.match(session) and words[:2] == ["uv", "run"] and words[3:4] == ["session"] and _is_bc(words[2])
            and "--id" in words and words[words.index("--id") + 1:][:1] == [session]):
        mark(session)


def allow(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                             "permissionDecisionReason": reason}}))


def main(mode: str) -> None:
    data = json.load(sys.stdin)
    given = data.get("tool_input", {})
    if mode == "post-bash":
        post_bash(data)
    elif mode == "pre-bash":
        command = given.get("command", "")
        if command.lstrip().startswith("uv run") and marked(data.get("session_id")) \
                and exact_call(command, data.get("cwd") or os.getcwd()):
            allow("business-case: 1 exact call of a runner script in a build session")
    elif mode == "pre-write":
        project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ""
        if marked(data.get("session_id")) and write_allowed(given.get("file_path", ""), project):
            allow("business-case: a write in a runner folder or a temporary folder of a build session")
    elif mode == "pre-read":
        if marked(data.get("session_id")) and read_allowed(given.get("file_path", ""), data.get("cwd") or os.getcwd()):
            allow("business-case: a read of a runner plugin file or an answers file in a build session")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except Exception:  # noqa: BLE001 - no decision: Claude Code applies its own rules
        pass
    sys.exit(0)
