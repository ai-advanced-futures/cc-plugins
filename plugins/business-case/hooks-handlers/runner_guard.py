#!/usr/bin/env python3
"""The runner guard (ADR-016): in a session that runs a build, approve only the exact runner script calls.

A grant of `allowed-tools` ends with the turn, and its `*` matches any text. This hook gives an `allow` that
does not end with the turn, for 1 call at a time:

- post-bash: a `bc.py session --id <this session>` call that worked marks the session as a build session, and adds
  its `--case` folder to the mark.
- pre-bash: in a marked session, allow a command that is exactly 1 call of a script in RUNNER_CALLS, of bc.py, or
  of `bc_graph.py publish`.
- pre-write: in a marked session, allow a write under `.<plugin>/` of the project, or in a temporary folder of bc.py.
- pre-read: in a marked session, allow a read of a file of an available runner plugin, or of an answers file of a case.
- pre-skill: in a marked session, allow a `Skill` call of the main conversation for a route whose args are the
  plugin-run block that team-answers printed for an open run of that route in a case of the mark (the SHA-256 of the
  block is in the run) (STORY-251, D-1049, #1597). The learn skill gets no allow (D-1065).

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
import unicodedata
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
        "result_name.py": {"first": ["now", "run-id", "name", "version"]},
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
# The 7 skill routes that build.md starts with the Skill tool, with the plugin-run block as args (STORY-251). Each has
# a `Skill(<name>)` grant in build.md, and that grant ends with the turn of the command, so a route that starts after a
# dispatch in the background asks the person. pre-skill allows a route only for a planned run: its args must hold the
# block of an open run of that route (D-1049). The 8th grant, `Skill(business-case:learn)`, gets no allow: Claude Code
# asks the person in a later turn (D-1065). test_runner_guard.py compares SKILL_ROUTES and that 1 exception with the
# `Skill` grants of build.md, so a new grant fails the test until it is here.
SKILL_ROUTES = frozenset({
    "competitive-intelligence:discover", "competitive-intelligence:analyze",
    "jtbd-market-discovery:discover", "jtbd-market-discovery:wtp-check",
    "gtm:marketing-launch-runner", "gtm:marketing-brand-runner", "gtm:marketing-funnel-runner",
})
PLUGIN_RUN_FENCE = "```plugin-run"
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


def mark(session: str, case) -> None:
    """Mark the session, and add the case folder of its session call as 1 line of the mark (STORY-251, #1597)."""
    folder = marks_folder()
    folder.mkdir(parents=True, exist_ok=True)
    limit = time.time() - KEEP_DAYS * 86400
    for old in folder.iterdir():
        if old.stat().st_mtime < limit:
            old.unlink()
    path = folder / session
    cases = session_cases(session)
    if case is not None and str(case) not in cases:
        cases.append(str(case))
    # Write a new file and replace the mark with it, so that a reader never sees half a line.
    scratch = folder / f".{session}.{os.getpid()}"
    scratch.write_bytes("".join(f"{line}\n" for line in cases).encode("utf-8"))
    os.replace(scratch, path)


def session_cases(session: str) -> list:
    """The case folders of the session calls of a marked session; [] for a mark of an older version (no line). A
    line ends at the new line only: `splitlines` also splits at a carriage return and other control characters, and
    `read_text` turns a carriage return into a new line, so the file is read as bytes and split at `\\n` (#1621)."""
    try:
        text = (marks_folder() / session).read_bytes().decode("utf-8")
        return [line for line in text.split("\n") if line]
    except (OSError, UnicodeDecodeError):
        return []


def post_bash(data: dict) -> None:
    session = data.get("session_id") or ""
    words = words_of(data.get("tool_input", {}).get("command", "")) or []
    if (SESSION_NAME.match(session) and words[:2] == ["uv", "run"] and words[3:4] == ["session"] and _is_bc(words[2])
            and "--id" in words and words[words.index("--id") + 1:][:1] == [session]):
        given = words[words.index("--case") + 1:][:1] if "--case" in words else []
        # bc.py takes the last of 2 `--case` words, and argparse takes an abbreviation: only 1 exact `--case` word and
        # no other word that starts with `--ca` names the case of this call, else the call adds no line.
        if [w for w in words if w.startswith("--ca")] != ["--case"]:
            given = []
        case = (Path(data.get("cwd") or os.getcwd()) / given[0]).resolve() if given and given[0] else None
        # A control character in the case folder, typed or from a link or the `cwd`, would split 1 mark line: 1 call
        # writes 1 line, so such a call gives no mark (#1621).
        if any(unicodedata.category(c) == "Cc" for c in (given[0] if given else "") + str(case or "")):
            return
        mark(session, case)


def block_text(args):
    """The JSON line of the plugin-run block that `args` holds: the fenced block as team-answers prints it, or its JSON
    line alone, with no other text. None for each other value."""
    if not isinstance(args, str):
        return None
    text = args.strip()
    if text.startswith(PLUGIN_RUN_FENCE + "\n") and text.endswith("\n```"):
        text = text[len(PLUGIN_RUN_FENCE) + 1:-4].strip()
    return text


def block_of(args):
    """The plugin-run block that `args` holds, as a dict with the 3 keys that the guard reads. None for each other
    value."""
    text = block_text(args)
    try:
        block = json.loads(text) if text is not None else None
    except ValueError:
        return None
    if not isinstance(block, dict) or not all(isinstance(block.get(key), str) and block[key]
                                              for key in ("command", "run_id", "case")):
        return None
    return block


def planned_run(skill: str, args, session: str, cwd: str) -> bool:
    """True when `args` is the text of a block that team-answers printed for an open run of a case of this session:
    the SHA-256 of the JSON line is the `block_sha256` of the run, and the route of its command in the plugin map is
    `skill` (D-1049, #1597)."""
    block = block_of(args)
    if block is None:
        return False
    from lib import plugin_map, team_files  # imported late: most Skill calls never reach this
    root = (team_files.git_root(cwd) or Path(cwd)).resolve()
    case = root / block["case"]
    if team_files.inside_root(root, case) is None or case.resolve().parent.name != "business-cases" \
            or team_files.repo_root(case) != root or str(case.resolve()) not in session_cases(session):
        return False
    # The runs file is the proof of the run: refuse a link in its path (a link could point outside the case).
    if team_files.inside_root(case.resolve(), case / team_files.runs_relpath()) is None:
        return False
    digest = team_files.block_sha256(block_text(args))
    runs = team_files.load_runs(case)
    if not any(r.get("run_id") == block["run_id"] and r.get("command") == block["command"] and r.get("state") == "open"
               and r.get("block_sha256") == digest for r in runs):
        return False
    spec = plugin_map.commands(plugin_map.load()).get(block["command"])
    return isinstance(spec, dict) and spec.get("route") == skill


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
    elif mode == "pre-skill":
        # A subagent has the session_id of its session, and its hook input also has agent_id: the coach starts each
        # route in its own conversation, so a call of a subagent gets no decision.
        name = given.get("skill")
        if name in SKILL_ROUTES and "agent_id" not in data and marked(data.get("session_id")) \
                and planned_run(name, given.get("args"), data["session_id"], data.get("cwd") or os.getcwd()):
            allow("business-case: a skill route of an open run of a build session")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except Exception:  # noqa: BLE001 - no decision: Claude Code applies its own rules
        pass
    sys.exit(0)
