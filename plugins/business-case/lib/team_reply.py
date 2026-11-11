"""The reply check, `bc.py team-reply --check` (spec §5.5): the code check every analyst reply passes
before the coach uses it.

`check_reply` first verifies the reply's receipt through `team_guard.verify_analyst_receipt`, which binds
the reply to the brief at its slot by digest, checks the bytes against the receipt and the receipt's
session. It then checks the reply against that brief: the kind the brief names, and

- a plan: business-case's plan schema (`schemas/team-plan.schema.json`) and the rules the schema cannot
  state, listed in its description; its own `results` get the results checks below;
- results: the standard's `check_result()` (never the name rule: a reply's name is not a result file
  name), the brief's `run` and `plugin_version`, and every cited file: it exists and holds the cited
  result id, passes `check_result()` and `check_result_file()`, and passes the case rule
  (`case_rule_problem`); a source whose `ref` names a file in a plugin's `results/` folder, judged by file
  identity, needs a `cites` entry for it. A cited path must stay in the git root once resolved.

A passing reply gets `team/reply-NNN.check.json`: `{"reply", "reply_sha256", "kind", "cited": {path:
sha256}}`, each path relative to the git root. The analyst computes no digest; this check does.

The brief body keys this module reads, which `team-brief` writes: a plan brief's `questions_paths`
(map command -> the absolute path of its questions list), and a results brief's `run` and
`plugin_version`.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from lib import (
    brain_read,
    case_files,
    digest,
    judge_receipt,
    paths,
    plugin_map,
    plugin_result,
    team_files,
    team_guard,
)
from lib.team_files import TeamRefused

BODY_QUESTIONS_PATHS = "questions_paths"
BODY_RUN = "run"
BODY_PLUGIN_VERSION = "plugin_version"
PLAN_SCHEMA = paths.PLUGIN_ROOT / "schemas" / "team-plan.schema.json"
MAX_OPTIONS = 4
RECOMMENDED = " (Recommended)"  # the suffix, its leading space included
ITEM_ID = re.compile(r"\bBC-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")  # the shape of a map item id; the check keeps the map's own

_REPLY_NAME = re.compile(r"^reply-([0-9]{3}|[1-9][0-9]{3,})\.json$")
_CARDS_NAME = re.compile(r"^cards-([0-9]{3}|[1-9][0-9]{3,})\.json$")


def _load_schema(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# -- the slot and the reply ---------------------------------------------------------------------

def _slot(case: Path, reply_path) -> int:
    target = Path(reply_path).resolve()
    match = _REPLY_NAME.match(target.name)
    if match is None or target.parent != case / paths.TEAM_DIR:
        raise TeamRefused(f"{reply_path} is not this case's team/reply-NNN.json")
    return int(match.group(1))


def _json_bytes(data: bytes, what: str):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise TeamRefused(f"{what} is not JSON") from None


def check_reply(case_dir, reply_path, m) -> Path:
    """Check the analyst reply at `<case>/team/reply-NNN.json` against its brief and write
    `team/reply-NNN.check.json`; returns its path. Raises TeamRefused naming every problem found."""
    case = Path(case_dir).resolve()
    nnn = _slot(case, reply_path)
    rel = team_files.reply_relpath(nnn)
    try:
        receipt = team_guard.verify_analyst_receipt(case, nnn)
    except judge_receipt.ReceiptRefused as exc:
        raise TeamRefused(f"{rel} is refused: {exc}") from None
    brief = team_files.read_brief(case / team_files.brief_relpath(nnn))
    if brief.case_dir != str(case) or brief.reply_path != str(case / rel):
        raise TeamRefused(f"{team_files.brief_relpath(nnn)} names another case folder or reply path than where it sits")
    data = (case / rel).read_bytes()
    if digest.sha256_hex(data) != receipt.get("sha256"):
        raise TeamRefused(f"{rel} changed after its receipt was checked")
    reply = _json_bytes(data, rel)
    if not isinstance(reply, dict):
        raise TeamRefused(f"{rel} is not a JSON object")
    kind = "results" if "schema" in reply else "plan"
    if kind != brief.reply_kind:
        raise TeamRefused(f"{rel} is a {kind} reply; its brief {team_files.brief_relpath(nnn)} asks for a "
                          f"{brief.reply_kind} reply")
    if kind == "plan":
        problems, cited = _plan_problems(case, reply, brief, m)
    else:
        problems, cited = _results_problems(case, reply, brief)
    if problems:
        raise TeamRefused(f"{rel} is refused: " + "; ".join(problems))
    out = case / team_files.check_relpath(nnn)
    case_files._write_json(out, {"reply": rel, "reply_sha256": digest.sha256_hex(data), "kind": kind,
                                 "cited": cited})
    return out


def read_check(case_dir, nnn: int) -> dict:
    """The check record of reply NNN; TeamRefused when the reply has none."""
    path = Path(case_dir).resolve() / team_files.check_relpath(nnn)
    if not path.is_file():
        raise TeamRefused(f"no {team_files.check_relpath(nnn)}: reply {nnn:03d} has not passed team-reply --check")
    record = _json_bytes(path.read_bytes(), team_files.check_relpath(nnn))
    if not isinstance(record, dict):
        raise TeamRefused(f"{team_files.check_relpath(nnn)} is not a JSON object")
    return record


# -- plans --------------------------------------------------------------------------------------

def _questions(path_text, command: str):
    """(questions by input, None) from a questions list file, or (None, problem)."""
    if not isinstance(path_text, str) or not path_text:
        return None, f"its brief names no questions list for {command}"
    try:
        resolved = Path(path_text).resolve()
    except (OSError, ValueError, RuntimeError):
        resolved = None
    want = f"{plugin_result.command_part(command)}.json"
    if resolved is None or resolved.name != want or resolved.parent.name != "questions":
        return None, f"the questions list of {command} is not a questions/{want} once resolved: {path_text}"
    try:
        doc = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None, f"the questions list of {command} cannot be read: {path_text}"
    errors = plugin_result.CHECK.check_questions(doc)
    if errors:
        return None, f"the questions list of {command} fails the checker: {errors[0]}"
    return {q["input"]: q for q in doc["questions"]}, None


def _plan_results_problems(case: Path, results: list, brief):
    """A plan's own research results get the full results check: the checker over them as one file of
    the brief's analyst and run, then the cites and source rules (the same as a results reply)."""
    if not results:
        return [], {}
    doc = {"schema": "plugin-result/1", "plugin": "business-case", "plugin_version": team_files.plugin_version(),
           "command": brief.agent_type,
           "run": team_files.brief_run_object(case, list(brief.items) or [brief.agent_type], brief.written_at),
           "results": results, "gaps": []}
    errors = plugin_result.check_result(doc)
    if errors:
        return [f"its results fail the checker: {e}" for e in errors], {}
    return _result_list_problems(case, results)


def _plan_problems(case: Path, reply: dict, brief, m):
    """(problems, cited) for a plan reply."""
    errors = plugin_result.validate(reply, _load_schema(PLAN_SCHEMA))
    if errors:
        return [f"it fails the plan schema: {e}" for e in errors], {}
    problems, cited = _plan_results_problems(case, reply.get("results", []), brief)
    commands = plugin_map.commands(m)
    questions_paths = brief.body.get(BODY_QUESTIONS_PATHS)
    questions_paths = questions_paths if isinstance(questions_paths, dict) else {}
    lists = {}
    ids = [card["id"] for card in reply["cards"]]
    problems += [f"card id {i} is used twice" for i in sorted({i for i in ids if ids.count(i) > 1})]
    for card in reply["cards"]:
        problems += _card_problems(card, commands, m, questions_paths, lists)
    hard = {card["id"] for card in reply["cards"] if card["hard_to_undo"]}
    problems += [f"follow_up {f} is not one of the plan's own hard_to_undo cards"
                 for f in reply.get("follow_up", []) if f not in hard]
    runs = reply["runs"]
    for command in runs:
        if command in commands:
            problems += [f"runs names {command} with {dep}; {command} reads {dep}'s result, so they run in "
                         "different rounds" for dep in plugin_map.reads_from(m, command) if dep in runs]
    return list(dict.fromkeys(problems)), cited


def _card_problems(card: dict, commands: dict, m, questions_paths: dict, lists: dict) -> list:
    cid, options = card["id"], card["options"]
    problems = []
    if len(options) > MAX_OPTIONS:
        problems.append(f"card {cid} has {len(options)} options; a card has at most four")
    labels = [o["label"] for o in options]
    if not labels[0].endswith(RECOMMENDED) or any(label.endswith(RECOMMENDED) for label in labels[1:]):
        problems.append(f"card {cid}: the recommended option comes first and alone, its label ending \"{RECOMMENDED}\"")
    if card["blocks"] == "later" and any(o.get("sets") for o in options):  # an empty `sets` sets no input
        problems.append(f"card {cid} blocks later and sets inputs; it is asked after its runs end, so it sets none")
    if not card["because"].strip():
        problems.append(f"card {cid} has a blank because; say in 1 sentence what the answer changes in the case")
    shown = [card["header"], card["because"], card["question"]]
    shown += [text for o in options for text in (o["label"], o.get("description", ""))]
    known = m.get("items", {})
    found = sorted({i for text in shown for i in ITEM_ID.findall(text) if i in known})
    if found:
        problems.append(f"card {cid} names the item id {', '.join(found)}; say the item's title, because the "
                        "person reads the card")
    named = {}
    for o in options:
        for command, inputs in o.get("sets", {}).items():
            if command not in commands:
                problems.append(f"card {cid} sets inputs of {command}, which is not a map command")
                continue
            for name, value in inputs.items():
                if name in plugin_map.never_set(m, command):
                    problems.append(f"card {cid} sets {name} of {command}, which the map marks never set")
                named.setdefault((command, name), []).append(value)
    recommended = options[0].get("sets", {})
    for (command, name), values in named.items():
        if command not in lists:
            lists[command] = _questions(questions_paths.get(command), command)
        by_input, problem = lists[command]
        if problem is not None:
            problems.append(problem)
            continue
        question = by_input.get(name)
        if question is None:
            problems.append(f"card {cid} sets {name}, which is not an input of {command}'s questions list")
        else:
            if "default" not in question and name not in recommended.get(command, {}):
                problems.append(f"card {cid} names {name} of {command}, which has no default, and its recommended "
                                "option leaves it unset")
            problems += [f"card {cid} sets {name} of {command} to {json.dumps(v)}, which is not {why}"
                         for v in values for why in [_misfit(question, v)] if why]
    return list(dict.fromkeys(problems))


def _misfit(question: dict, value):
    """What a value for `question` must be, when `value` is not that; else None (final review I2)."""
    kind = question["type"]
    if kind == "number":
        ok, want = isinstance(value, (int, float)) and not isinstance(value, bool), "a number"
    elif kind == "boolean":
        ok, want = isinstance(value, bool), "true or false"
    elif kind == "choice":
        allowed = [o["value"] for o in question.get("options", [])]
        ok = any(type(value) is type(a) and value == a for a in allowed)
        want = "one of its options: " + ", ".join(json.dumps(a) for a in allowed)
    else:  # text, path
        ok, want = isinstance(value, str), "text"
    return None if ok else want


# -- results ------------------------------------------------------------------------------------

def _cited_path(case: Path, text):
    """(resolved path, path relative to the git root) of a cited or referred file, or None when the text
    names no path inside the git root once every symlink and `..` is resolved."""
    if not isinstance(text, str) or not text.strip():
        return None
    root = team_files.repo_root(case)
    target = Path(text) if Path(text).is_absolute() else root / text
    rel = team_files.inside_root(root, target)
    return None if rel is None else (target.resolve(), rel)


# The standard's result file name (PLUGIN_RESULT_FILE.md, "Where it goes"): `<UTC timestamp
# YYYYMMDDTHHMMSSZ>-<command>-<subject slug>[-<run_id>][-<n>].json`, where every part after the
# timestamp is lower case a-z, 0-9 and `-`. Other files in a results folder (a README, an index) are no
# result and force no cite.
RESULT_FILE_NAME = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+\.json$")


def _results_files(root: Path, case=None) -> list:
    """Every result file (RESULT_FILE_NAME) under a `.<plugin>/results/` folder at the git root, and every
    snapshot in `team/upstream/` of the case. The folder of a plugin that has a graph in the plugin map is
    not read: the case reads a run of such a plugin from its graph, and keeps it as a snapshot."""
    graph_folders = {"." + name for name in brain_read.graph_plugins()}
    found = []
    for folder in sorted(root.iterdir()):
        results = folder / "results"
        if folder.name in graph_folders:
            continue
        if len(folder.name) > 1 and folder.name.startswith(".") and paths.stat_is_dir(results):
            found += [f for f in results.rglob("*") if paths.stat_is_file(f) and RESULT_FILE_NAME.match(f.name)]
    upstream = brain_read.upstream_dir(case) if case is not None else None
    if upstream is not None and paths.stat_is_dir(upstream):
        found += [f for f in sorted(upstream.iterdir())
                  if paths.stat_is_file(f) and RESULT_FILE_NAME.match(f.name)]
    return found


def _ref_spellings(ref: str) -> list:
    """The path spellings a source ref may hold, for the identity check: as given, without a `file:`
    scheme and its authority, and without a `#fragment` or a `?query`."""
    text = ref.strip()
    bases = [text]
    if text.lower().startswith("file:"):
        rest = text[len("file:"):]
        if rest.startswith("//"):
            rest = rest[2:]
            rest = rest[rest.find("/"):] if "/" in rest else ""
        bases.append(rest)
    out = []
    for base in bases:
        out += [base, base.split("#", 1)[0], base.split("?", 1)[0]]
    return [s for s in dict.fromkeys(out) if s]


def _results_files_named(root: Path, ref, files: list) -> list:
    """Every result file a source ref names: by its stem in the ref's text, and by file identity of a
    path the ref spells (letter case and symlinks included)."""
    if not isinstance(ref, str):
        return []
    # Total check by name: a ref whose text holds a result file's stem (its name without `.json`),
    # compared case-folded, names that file, whatever is around it (a scheme, a host, quotes, brackets,
    # prose, punctuation, another extension). Safe because a result file's stem carries a UTC timestamp
    # and its command, slug and run id, so it is unique; it fails closed: a ref that only mentions a
    # result file still needs a cite.
    folded = ref.casefold()
    named = [f for f in files if f.stem.casefold() in folded]
    for spelling in _ref_spellings(ref):
        try:
            path = Path(spelling) if Path(spelling).is_absolute() else root / spelling
            if path.is_file():
                named += [f for f in files if f not in named and os.path.samefile(path, f)]
        except (OSError, ValueError):
            continue
    return named


def _results_problems(case: Path, reply: dict, brief):
    doc = {k: v for k, v in reply.items() if k != "brief_sha256"}
    errors = plugin_result.check_result(doc)
    if errors:
        return [f"it fails the checker: {e}" for e in errors], {}
    problems = [f"its {field} differs from the {field} its brief names"
                for field in (BODY_RUN, BODY_PLUGIN_VERSION) if doc[field] != brief.body.get(field)]
    more, cited = _result_list_problems(case, doc["results"])
    return list(dict.fromkeys(problems + more)), cited


def _result_list_problems(case: Path, results: list):
    """The cites and source rules over results that already passed the checker: (problems, cited)."""
    problems, cited = [], {}
    root = team_files.repo_root(case)
    files = _results_files(root, case)
    for result in results:
        cite_paths = []
        for entry in result.get("cites", []):
            found = _cited_path(case, entry["file"])
            if found is None:
                problems.append(f"result {result['id']} cites {entry['file']}, which is not a path in the git root")
                continue
            path, rel = found
            cite_paths.append(path)
            problem, sha = _cited_problem(case, path, rel, entry["result_id"])
            if problem is not None:
                problems.append(f"result {result['id']} cites {entry['file']}: {problem}")
            else:
                cited[rel] = sha
        for source in result["sources"]:
            uncited = [f for f in _results_files_named(root, source["ref"], files)
                       if not any(p.is_file() and os.path.samefile(p, f) for p in cite_paths)]
            if uncited:
                problems.append(f"result {result['id']} has a source {source['ref']} in a plugin's results folder or in the "
                                "team/upstream/ folder of the case, and no cites entry for it")
    return problems, cited


def _cited_problem(case: Path, path: Path, rel: str, result_id: str):
    """(problem, None) or (None, sha256) for one cited file and result id."""
    if not path.is_file():
        return "the file does not exist", None
    data = path.read_bytes()
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return "the file is not JSON", None
    errors = plugin_result.check_result(doc) + plugin_result.check_result_file(path)
    if errors:
        return "the file fails the checker: " + "; ".join(errors), None
    if result_id not in {r["id"] for r in doc["results"]}:
        return f"the file holds no result {result_id}", None
    problem = case_rule_problem(case, doc, path)
    if problem is not None:
        return problem, None
    return None, digest.sha256_hex(data)


def case_rule_problem(case_dir, doc, path) -> str | None:
    """The case rule (spec §5.7): None when a result file may serve this case; else why not. Its
    `run.case`, compared as text, must be the case folder's path relative to the git root; a file with
    no `run.case` needs the card record's CASE_ANSWER_LABEL answer for it, from the newest case card
    that names the file."""
    case = Path(case_dir).resolve()
    want = team_files.repo_relative(case, case)
    run = doc.get("run") if isinstance(doc, dict) else None
    run_case = run.get("case") if isinstance(run, dict) else None
    if run_case is not None:
        return None if run_case == want else f"its run.case is {run_case!r}, not this case, {want!r}"
    found = _cited_path(case, str(path))
    answered, unreadable = _case_answer(case, found[1]) if found is not None else (False, None)
    if answered:
        return None
    if unreadable is not None:
        return f"it has no run.case, and {unreadable}"
    return f"it has no run.case, and the card record holds no {team_files.CASE_ANSWER_LABEL!r} answer for it"


def _case_answer(case: Path, rel: str):
    """(answered, unreadable): whether `newest_case_answer` for the result file `rel` is CASE_ANSWER_LABEL.
    `unreadable` names a cards file that cannot be read."""
    try:
        label = newest_case_answer(case, rel)
    except TeamRefused as exc:
        return False, str(exc)
    return label == team_files.CASE_ANSWER_LABEL, None


def newest_case_answer(case_dir, rel: str):
    """The label of the newest answered case card for the result file `rel` (relative to the git root), in
    the newest cards-NNN.json (each one is cumulative); None when there is none, or when any case card for
    the file is open (an open case card refuses its file, spec §5.0 step 2). A card's age is the newest call
    in its `passed`, then its `code:<n>` number. Refused when the card record cannot be read."""
    case = Path(case_dir).resolve()
    team_dir = case / paths.TEAM_DIR
    names = sorted((int(mt.group(1)), p) for p in team_dir.iterdir()
                   if (mt := _CARDS_NAME.match(p.name))) if paths.stat_is_dir(team_dir) else []
    if not names:
        return None
    relpath = f"{paths.TEAM_DIR}/{names[-1][1].name}"
    try:
        newest_file = names[-1][1].resolve()
        if newest_file.parent != team_dir.resolve():
            raise ValueError("outside the team folder")
        record = json.loads(newest_file.read_text(encoding="utf-8"))
        cards = list(record["cards"].items())
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError, AttributeError):
        raise TeamRefused(f"the card record {relpath} cannot be read") from None
    newest = None
    for key, card in cards:
        if not isinstance(card, dict) or card.get("made_by") != "case":
            continue
        answer, subject = card.get("answer"), card.get("subject")
        if not isinstance(subject, dict):
            continue
        found = _cited_path(case, subject.get("result_file"))
        if found is None or found[1] != rel:
            continue
        if not isinstance(answer, dict):
            return None  # an open case card for the file
        passed = [n for n in card.get("passed") or [] if isinstance(n, int) and not isinstance(n, bool)]
        number = key.split(":", 1)[1] if isinstance(key, str) and key.startswith("code:") else ""
        age = (max(passed, default=0), int(number) if number.isdigit() else 0)
        if newest is None or age > newest[0]:
            newest = (age, answer.get("label"))
    return newest[1] if newest is not None else None
