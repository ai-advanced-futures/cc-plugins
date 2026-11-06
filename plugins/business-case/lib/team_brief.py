"""`bc.py team-brief --analyst`: an analyst's items in the order of work, and its plan or results brief
(spec §5.0 steps 1 and 6, §5.5, §5.6 "Two plan rounds").

Which items go in a brief (`select`):

- An item is **settled** (`settled`) when a checked results reply holds a result of a kind the map gives to
  it, or an evidence page names it, or its newest gap card is answered "go on without it". A results reply
  that lists the item's kind only in `gaps` settles nothing, and an open gap card, or one answered "wait for
  it", settles nothing.
- A plan request leaves out an item that already had a results brief (in any state): no plan brief follows a
  results brief, and the reason names the item's `--gap-card` command. It leaves out an item with an
  unsettled upstream item (`plugin_map.upstream`), naming each one and its `--gap-card` command.
- The items left form **item sets**. A plan request groups items by their plan round: the items with no plan
  brief form one set, and an item with one plan brief joins the other items of that brief. An item whose plan
  briefs number MAX_PLAN_ROUNDS (`plan_rounds`, cancelled and expired ones included, as `team_record._round`
  counts) gets a results brief instead: no third plan brief is ever written. A results request groups items
  by their newest plan brief; an item with no plan brief is left out. Every results brief, asked for or
  turned from a plan request, waits for its runs: an item is left out while a map command its set's checked
  plans named has an open run or no run, unless a card holds it (`_unfinished_runs`).
- The sets come in the order of work (`order_of_work`, from the map's `after` lists), and so do the items in
  each. `write_briefs` writes the first set's brief only: one brief per analyst runs at once
  (`team_files.write_brief`), so each other set waits for that brief's reply. When every item is left out it
  refuses, naming what is missing.

The brief bodies hold PLAN_BODY_KEYS or RESULTS_BODY_KEYS, every path in them absolute:

- plan: the items (`id`, `title`, the met test's text), the plan round, the install check, the tier-2
  candidates (as the coach's temp file gives them), the newest answers file, the questions list of each
  command of an `available` plugin (`team_reply.BODY_QUESTIONS_PATHS`), every ended run with a result file of
  a command the items' commands read from or that a plan for an upstream item named
  (`team_runs.BODY_UPSTREAM_RUNS`; every one, not only the newest: `team_runs.inputs_from` picks the newest),
  and the free text the person typed on the items' cards;
- results: the items; for each command the item set's checked plans named, the run of the newest plan round
  that named it (a rerun supersedes an earlier round's run; a person's run counts): its result file, or the
  earlier file a rerun card points at while it holds the command, or else a gap with its reason (held by an
  open card, named by key, or until the set's second plan round; ended as a gap, not ended, or never run); the
  install states of the plugins of the items'
  commands and the plans' commands, with the managed scope's; the newest answers file, the checked plan
  replies, the answered `blocks: later` cards, the tier-2 output paths, the free text, and the `run` and
  `plugin_version` the reply must carry (`team_reply.BODY_RUN`, `BODY_PLUGIN_VERSION`).

The tier-2 temp file: `{"candidates": [{"name", "description"}], "outputs": ["<absolute path>"]}`; both keys
are optional.

Python 3.9 syntax only.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from lib import (
    case_files,
    digest,
    evidence,
    install_check,
    paths,
    plugin_map,
    rubric,
    team_files,
    team_record,
    team_reply,
    team_runs,
)
from lib.team_files import TeamRefused

MAX_PLAN_ROUNDS = team_record.MAX_PLAN_ROUNDS
KINDS = team_files.REPLY_KINDS
GAP_CARD_COMMAND = "bc.py team-answers --gap-card {item}"
PLUGIN_PREFIX = "business-case:"

ITEMS, FREE_TEXT, ANSWERS_PATH = "items", "free_text", "answers_path"
PLAN_ROUND, INSTALLS, TIER2_CANDIDATES = "plan_round", "installs", "tier2_candidates"
RUNS, GAPS, PLAN_REPLIES = "runs", "gaps", "plan_replies"
LATER_ANSWERS, TIER2_OUTPUTS = "later_answers", "tier2_outputs"
PLAN_BODY_KEYS = (ITEMS, PLAN_ROUND, INSTALLS, TIER2_CANDIDATES, ANSWERS_PATH, team_reply.BODY_QUESTIONS_PATHS,
                  team_runs.BODY_UPSTREAM_RUNS, FREE_TEXT)
RESULTS_BODY_KEYS = (ITEMS, RUNS, GAPS, INSTALLS, ANSWERS_PATH, PLAN_REPLIES, LATER_ANSWERS, TIER2_OUTPUTS, FREE_TEXT,
                     team_reply.BODY_RUN, team_reply.BODY_PLUGIN_VERSION)

RESULTS_BRIEF_HAD = ("it has had its results brief, and no plan brief follows one; if it still has no result, "
                     "make its gap card: " + GAP_CARD_COMMAND)
WAITS_FOR = "it waits for {missing}, which has no result yet; to go on without it, make its gap card: {commands}"
# The refusal when every item is left out names each upstream item's gap card once (live run F8: one copy
# per item clipped a pricing refusal at 800 bytes).
WAITS_SHORT = "{item} waits for {missing}"
WAITS_GAP_CARDS = "none of these has a result yet; to go on without one, make its gap card: {commands}"
NO_PLAN_BRIEF = "it has had no plan brief; ask for its plan brief first"
RUNS_UNFINISHED = "its results brief waits until every run its plans named has ended or is held: {runs}; then ask again"
# What clears each unfinished run (spec §5.0 steps 2 and 4).
NOT_MERGED = ("{command}: plan brief {nnn:03d} is not merged yet; record the coach call with bc.py team-answers "
              "--answers-file FILE")
COACH_RUN_OPEN = ("{command}: run {key} is open; when its dispatch has ended, record it with bc.py team-run --done "
                  "{key} (or --status), or as a gap with bc.py team-run --fail {key}")
PERSON_RUN_OPEN = ("{command}: the person's run {key} is open; ask the person to run it and give its result file to "
                   "bc.py team-answers --case-card FILE, or record it as a gap with bc.py team-run --fail {key}")
# What the item set's second plan round waits for (spec §5.0 step 3), one text per state (team_record.round_2_step).
ROUND_2_UNWRITTEN = ("its second plan round is due: ask for its plan brief with --kind plan, check the reply, record "
                     "its cards with bc.py team-answers --answers-file FILE, then ask again")
ROUND_2_UNANSWERED = ("its second plan brief {nnn:03d} has no merged reply yet: reply to brief {nnn:03d} (dispatch its "
                      "analyst with it), check the reply with bc.py team-reply --check, record it with bc.py "
                      "team-answers --answers-file FILE, then ask again")
ROUND_2_CARDS = ("its second plan's cards {keys} are not yet asked: ask them, record the answers with bc.py "
                 "team-answers --answers-file FILE, then ask again")
ROUND_2_CAP = ("the after-cap rule has not yet run for its second plan brief {nnn:03d}, so cards {keys} are still "
               "open: run bc.py team-answers --answers-file FILE with an empty answers list, then ask again")
# The cap state with no card open: every card was passed, and none is held (final review M4).
ROUND_2_CAP_NO_CARDS = ("the after-cap rule has not yet run for its second plan brief {nnn:03d}: run bc.py "
                        "team-answers --answers-file FILE with an empty answers list, then ask again")
ROUND_2_TEXTS = {"unwritten": ROUND_2_UNWRITTEN, "unanswered": ROUND_2_UNANSWERED, "cards": ROUND_2_CARDS,
                 "cap": ROUND_2_CAP}
HELD_FOR_ROUND_2 = "held until its item set's second plan round is recorded and its cards asked"
LAST_ASK_FIRST = ("card {keys} is hard to undo and gets one more ask before the results brief of {items}: ask it, "
                  "record the answer with bc.py team-answers --answers-file FILE, then ask for the results brief "
                  "again")
NO_BLOCK = ("{command}: no run is recorded for it yet; run bc.py team-answers again and act on any error it "
            "prints in place of its block")

@dataclass
class Selection:
    groups: list = field(default_factory=list)  # [(reply kind, [item])], in the order of work
    left_out: dict = field(default_factory=dict)  # item -> why it is left out
    waits_for: dict = field(default_factory=dict)  # item left out -> [its unsettled upstream items]


# -- the briefs on disk --------------------------------------------------------------------------------

def _case(case_dir) -> Path:
    return Path(case_dir).resolve()


def _plan_briefs(case: Path, item) -> list:
    return [b for b in team_files.all_briefs(case) if b.reply_kind == "plan" and item in b.items]


def plan_rounds(case_dir, item) -> int:
    """How many plan briefs name `item`, in any state: open, answered, cancelled or expired (spec §5.6)."""
    return len(_plan_briefs(_case(case_dir), item))


def had_results_brief(case_dir, item) -> bool:
    """Whether a results brief, in any state, names `item`."""
    return any(b.reply_kind == "results" and item in b.items for b in team_files.all_briefs(_case(case_dir)))


def _checked_reply(case: Path, nnn: int, kind: str):
    """The reply of brief NNN when its check record is of `kind` and still matches the reply's bytes; else
    None."""
    try:
        record = team_reply.read_check(case, nnn)
    except TeamRefused:
        return None
    reply = case / team_files.reply_relpath(nnn)
    if record.get("kind") != kind or not reply.is_file():
        return None
    data = reply.read_bytes()
    if digest.sha256_hex(data) != record.get("reply_sha256"):
        return None
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


# -- settled -------------------------------------------------------------------------------------------

def _item_kinds(m, item) -> set:
    return {kind for kind, items in m.get("kinds", {}).items() if item in items}


def _has_page(case: Path, item) -> bool:
    folder = case / paths.EVIDENCE_DIR
    if not folder.is_dir():
        return False
    return any(item in evidence.read_page(case, path.stem)["item_ids"] for path in sorted(folder.glob("EV-*.json")))


def _gap_card_go_on(case: Path, item) -> bool:
    """Whether the newest gap card for `item` is answered "go on without it"."""
    found = [(int(key.split(":", 1)[1]), card) for key, card in team_record.latest_cards(case).items()
             if card.get("made_by") == "gap" and card.get("subject", {}).get("item") == item
             and key.startswith("code:")]
    if not found:
        return False
    answer = max(found, key=lambda x: x[0])[1].get("answer")
    return isinstance(answer, dict) and answer.get("label") == team_record.GO_ON


def settled(case_dir, m, item) -> bool:
    """Whether `item` counts as settled (spec §5.0 step 1): a checked results reply holds a result of one of
    its kinds, an evidence page names it, or its newest gap card is answered "go on without it"."""
    case = _case(case_dir)
    kinds = _item_kinds(m, item)
    for brief in team_files.all_briefs(case):
        if brief.reply_kind != "results":
            continue
        reply = _checked_reply(case, brief.nnn, "results")
        if reply and any(isinstance(r, dict) and r.get("kind") in kinds for r in reply.get("results", [])):
            return True
    return _has_page(case, item) or _gap_card_go_on(case, item)


# -- the order of work and the item sets ----------------------------------------------------------------

def order_of_work(m) -> list:
    """Every map item, each after the items its `after` list names; otherwise in map order."""
    items = m["items"]
    out, done = [], set()
    while len(out) < len(items):
        ready = [i for i in items if i not in done and all(a in done for a in items[i]["after"])]
        if not ready:
            raise TeamRefused("the plugin map's order of work has a cycle")
        out.append(ready[0])
        done.add(ready[0])
    return out


def _check_request(case: Path, m, analyst, items, kind) -> list:
    """The items in the order of work; refused for a kind, an analyst or an item team-brief cannot serve."""
    if kind not in KINDS:
        raise TeamRefused(f"kind must be one of {', '.join(KINDS)}")
    owners = {spec["owner"] for spec in m["items"].values()}
    if not (isinstance(analyst, str) and analyst.startswith("case-") and analyst.endswith("-analyst")
            and analyst in owners):
        raise TeamRefused(f"{analyst!r} is not an analyst of the plugin map; give its name, e.g. case-pricing-analyst")
    if not isinstance(items, list) or not items:
        raise TeamRefused("name one or more items")
    repeated = sorted({i for i in items if items.count(i) > 1})
    if repeated:
        raise TeamRefused(f"item {', '.join(repeated)} is named twice")
    mine = set(plugin_map.analyst_items(m, analyst))
    applicable = {i["id"] for i in case_files.applicable_items(case)}
    for item in items:
        if item not in mine:
            raise TeamRefused(f"{item} is not an item of {analyst}; its items are {', '.join(sorted(mine))}")
        if item not in applicable:
            raise TeamRefused(f"{item} does not apply to this case")
    return mine & applicable


def _check_item_sets(case: Path, items: list, served: set) -> None:
    """Refused when the request holds part of an item set: an item with a plan brief comes with every item of
    its newest plan brief that is still this analyst's and still applies (spec §5.0 step 1)."""
    missing = {}
    for item in items:
        plans = _plan_briefs(case, item)
        if plans:
            whole = [i for i in plans[-1].items if i in served]
            left = [i for i in whole if i not in items]
            if left:
                missing[plans[-1].nnn] = (whole, left)
    if missing:
        raise TeamRefused("; ".join(
            f"the item set of brief {nnn:03d} is {', '.join(whole)}, and this request leaves out {', '.join(left)}; "
            f"ask for the whole item set: --items {','.join(whole)}" for nnn, (whole, left) in sorted(missing.items())))


def _set_plans(case: Path, plan_briefs: list) -> dict:
    """The checked plan replies among `plan_briefs`, by brief NNN."""
    replies = {n: _checked_reply(case, n, "plan") for n in plan_briefs}
    return {n: reply for n, reply in replies.items() if reply is not None}


def _command_runs(case: Path, m, plans: dict) -> dict:
    """For each map command the checked `plans` named, in order: (the newest plan brief that named it, its
    state, the run). The run is the one of that newest plan round: a rerun supersedes an earlier round's run.
    The state is `ended` (the newest ended run with a result file), `open`, `gap` (the newest gap), `held`
    (an open card holds it; the run is the earlier run a rerun card points at, or None) or `none`."""
    known = plugin_map.commands(m)
    named = {}
    for nnn in sorted(plans):
        for command in plans[nnn].get("runs", []):
            if command in known:
                named[command] = nnn  # the newest plan brief wins
    held = team_runs.held_commands(case, list(plans))
    runs = team_files.load_runs(case)
    out = {}
    for command, newest in named.items():
        mine = [(i, r) for i, r in enumerate(runs) if r.get("command") == command and newest in r.get("briefs", [])]
        ended = [(r.get("finished_at") or "", i, r) for i, r in mine if r.get("state") == "ended" and r.get("result_file")]
        if any(r.get("state") == "open" for _, r in mine):
            out[command] = (newest, "open", next(r for _, r in mine if r.get("state") == "open"))
        elif ended:
            out[command] = (newest, "ended", max(ended, key=lambda x: (x[0], x[1]))[2])
        elif any(r.get("state") == "gap" for _, r in mine):
            out[command] = (newest, "gap", [r for _, r in mine if r.get("state") == "gap"][-1])
        elif command in held:
            out[command] = (newest, "held", team_runs.ended_runs_for(case, [newest]).get(command))
        else:
            out[command] = (newest, "none", None)
    return out


def round_2_reason(state: str, nnn, keys: list) -> str:
    """Why an item set waits for its second plan round, in state `state` (team_record.round_2_step)."""
    text = ROUND_2_CAP_NO_CARDS if state == "cap" and not keys else ROUND_2_TEXTS[state]
    return text.format(nnn=nnn or 0, keys=", ".join(keys))


def _unfinished_runs(case: Path, m, plan_briefs: list) -> list:
    """What clears each map command the checked plans named whose newest round's run has not ended and is not
    held (spec §5.0 steps 4-6: the results round comes after the runs)."""
    merged = set(team_record.latest_merged(case))
    out = []
    for command, (nnn, state, run) in _command_runs(case, m, _set_plans(case, plan_briefs)).items():
        if state == "open":
            line = COACH_RUN_OPEN if run.get("run_id") else PERSON_RUN_OPEN
            out.append(line.format(command=command, key=run["key"]))
        elif state == "none":
            out.append((NO_BLOCK if nnn in merged else NOT_MERGED).format(command=command, nnn=nnn))
    return out


def select(case_dir, m, *, analyst, items, kind) -> Selection:
    """Which items go in which brief, and why each other one is left out (see the module text)."""
    case = _case(case_dir)
    served = _check_request(case, m, analyst, items, kind)
    order = order_of_work(m)
    items = sorted(items, key=order.index)
    _check_item_sets(case, items, served)
    out = Selection()
    keyed = {}  # (reply kind, the plan brief the set follows, or 0) -> (reply kind, [item])
    for item in items:
        plans = _plan_briefs(case, item)
        if kind == "plan":
            if had_results_brief(case, item):
                out.left_out[item] = RESULTS_BRIEF_HAD.format(item=item)
                continue
            missing = sorted((u for u in plugin_map.upstream(m, item) if not settled(case, m, u)), key=order.index)
            if missing:
                out.waits_for[item] = missing
                out.left_out[item] = WAITS_FOR.format(
                    missing=", ".join(missing), commands="; ".join(GAP_CARD_COMMAND.format(item=u) for u in missing))
                continue
            reply_kind = "plan" if len(plans) < MAX_PLAN_ROUNDS else "results"
        else:
            if not plans:
                out.left_out[item] = NO_PLAN_BRIEF
                continue
            reply_kind = "results"
        step = next((st for st in (team_record.round_2_step(case, b.nnn) for b in plans) if st), None) \
            if reply_kind == "results" else None
        if step is not None:  # its next brief is a second plan brief (spec §5.0 step 3)
            state, nnn, keys = step
            out.left_out[item] = round_2_reason(state, nnn, keys)
            continue
        unfinished = _unfinished_runs(case, m, [b.nnn for b in plans]) if reply_kind == "results" else []
        if unfinished:  # every results brief comes after its plans' runs (spec §5.0 steps 4-6)
            out.left_out[item] = RUNS_UNFINISHED.format(runs="; ".join(unfinished))
            continue
        follows = plans[-1].nnn if plans else 0
        keyed.setdefault((reply_kind, follows), (reply_kind, []))[1].append(item)
    out.groups = sorted(keyed.values(), key=lambda g: order.index(g[1][0]))
    return out


# -- the bodies -----------------------------------------------------------------------------------------

def _items(case: Path, items: list) -> list:
    rub = rubric.load_rubric(case / paths.RUBRIC_COPY)
    out = []
    for item in items:
        entry = rubric.item(rub, item)
        out.append({"id": item, "title": entry["title"], "met_test": entry["met_test"]["text"]})
    return out


def _newest_answers(case: Path):
    """team_record's newest answers file, as text; None before the first call."""
    path = team_record.latest_answers_path(case)
    return str(path) if path is not None and path.is_file() else None


def _free_text(case: Path, items: list) -> dict:
    return {item: team_record.free_text(case, item) for item in items}


def _installs(m) -> dict:
    return install_check.check(m, config_dir=install_check.config_dir(), cwd=Path.cwd(),
                               managed=install_check.default_managed_path())


def _questions_paths(m, installs: dict) -> dict:
    """The questions list of each command of each `available` plugin that has one, absolute."""
    out = {}
    for name, plugin in m["plugins"].items():
        state = installs.get(name, {})
        if state.get("state") != "available" or not state.get("install_path"):
            continue
        for command in plugin["commands"]:
            path = install_check.questions_path(state["install_path"], command)
            if path.is_file():
                out[command] = str(path.resolve())
    return out


def _run_entry(case: Path, run: dict) -> dict:
    return {"command": run["command"], "run_id": run.get("run_id"),
            "result_file": str(team_files.repo_root(case) / run["result_file"])}


def _upstream_runs(case: Path, m, items: list) -> list:
    commands = plugin_map.commands(m)
    kinds = set().union(*(_item_kinds(m, i) for i in items))
    reads = {dep for spec in commands.values() if kinds & set(spec["kinds"]) for dep in spec["reads_from"]}
    upstream = set().union(*(plugin_map.upstream(m, i) for i in items))
    named_by = {b.nnn for b in team_files.all_briefs(case) if b.reply_kind == "plan" and upstream & set(b.items)}
    return [_run_entry(case, r) for r in team_files.load_runs(case)
            if r.get("state") == "ended" and r.get("result_file")
            and (r.get("command") in reads or named_by & set(r.get("briefs", [])))]


def _plan_body(case: Path, m, items: list, tier2: dict) -> dict:
    installs = _installs(m)
    return {ITEMS: _items(case, items), PLAN_ROUND: plan_rounds(case, items[0]) + 1, INSTALLS: installs,
            TIER2_CANDIDATES: tier2.get("candidates", []), ANSWERS_PATH: _newest_answers(case),
            team_reply.BODY_QUESTIONS_PATHS: _questions_paths(m, installs),
            team_runs.BODY_UPSTREAM_RUNS: _upstream_runs(case, m, items), FREE_TEXT: _free_text(case, items)}


def _gap_reason(case: Path, state: str, command: str, run) -> str:
    """Why a command the plans named has no result file to name (spec §5.0, its last paragraph)."""
    if state == "held":
        keys = team_runs.holding_cards(case, command)
        return f"held by open card {', '.join(keys)}" if keys else HELD_FOR_ROUND_2
    if state == "gap":
        return run.get("reason") or "it ended with no result file"
    if state == "open":
        return "it has not ended" if run.get("run_id") else "the person has not run it yet"
    return "no run of it was recorded"


def _installs_for(m, installs: dict, items: list, named) -> dict:
    """The install check's state of each plugin whose command serves the items or a plan named, and the
    managed scope's when the check reports it."""
    commands = plugin_map.commands(m)
    kinds = set().union(*(_item_kinds(m, i) for i in items))
    wanted = {c for c, spec in commands.items() if kinds & set(spec["kinds"])} | set(named)
    plugins = {c.split(":")[0] for c in wanted}
    out = {name: state for name, state in installs.items() if name in plugins}
    if install_check.MANAGED_SCOPE in installs:
        out[install_check.MANAGED_SCOPE] = installs[install_check.MANAGED_SCOPE]
    return out


def _results_body(case: Path, m, items: list, tier2: dict, written_at: str) -> dict:
    plan_briefs = sorted({b.nnn for item in items for b in _plan_briefs(case, item)})
    plans = _set_plans(case, plan_briefs)
    by_command = _command_runs(case, m, plans)
    cards = team_record.latest_cards(case)
    named_runs = [(c, run) for c, (_, state, run) in by_command.items() if state in ("ended", "held") and run]
    return {
        ITEMS: _items(case, items),
        RUNS: [_run_entry(case, run) for _, run in named_runs],
        GAPS: [{"command": c, "reason": _gap_reason(case, state, c, run)}
               for c, (_, state, run) in by_command.items() if not (state in ("ended", "held") and run)],
        INSTALLS: _installs_for(m, _installs(m), items, by_command),
        ANSWERS_PATH: _newest_answers(case),
        PLAN_REPLIES: [str(case / team_files.reply_relpath(n)) for n in sorted(plans)],
        LATER_ANSWERS: [{"key": key, "question": card.get("question"), "answer": card["answer"].get("label")}
                        for key, card in cards.items() if card.get("brief") in plan_briefs
                        and card.get("blocks") == "later" and isinstance(card.get("answer"), dict)],
        TIER2_OUTPUTS: tier2.get("outputs", []),
        FREE_TEXT: _free_text(case, items),
        team_reply.BODY_RUN: team_files.brief_run_object(case, items, written_at),
        team_reply.BODY_PLUGIN_VERSION: team_files.plugin_version(),
    }


def _within(folder: Path, path: Path) -> bool:
    """Whether `path`, resolved, lies in `folder`, judged by file identity (`os.path.samefile`) as T12's
    results-folder rule does: on a disk that ignores letter case, `TEAM/x` is in `team/`."""
    if not folder.is_dir():
        return False
    for parent in Path(path).resolve().parents:
        try:
            if os.path.samefile(parent, folder):
                return True
        except OSError:
            continue
    return False


def _check_tier2(case: Path, tier2) -> dict:
    """The coach's tier-2 temp file as given; refused when it has another shape, or names an output that does
    not exist or lies in the case's team or judge folder (an analyst reads every file its brief names)."""
    if tier2 is None:
        return {}
    what = "the tier-2 file"
    if not isinstance(tier2, dict) or not set(tier2) <= {"candidates", "outputs"}:
        raise TeamRefused(f'{what} must be one object with only "candidates" and "outputs"')
    candidates = tier2.get("candidates", [])
    if not isinstance(candidates, list) or not all(
            isinstance(c, dict) and set(c) == {"name", "description"} and isinstance(c["name"], str)
            and c["name"].strip() and isinstance(c["description"], str) for c in candidates):
        raise TeamRefused(f'{what}: "candidates" must be a list of {{"name", "description"}}, each a text, the name '
                          "not blank")
    outputs = tier2.get("outputs", [])
    if not isinstance(outputs, list) or not all(isinstance(o, str) and Path(o).is_absolute() for o in outputs):
        raise TeamRefused(f'{what}: "outputs" must be a list of absolute paths')
    for output in outputs:
        path = Path(output)
        if not path.is_file():
            raise TeamRefused(f"{what} names the output {output}, which is not a file")
        for folder in (paths.TEAM_DIR, paths.JUDGE_DIR):
            if _within(case / folder, path):
                raise TeamRefused(f"{what} names the output {output}, which is in the case's {folder}/ folder")
    return tier2


def _left_out_reasons(selection: Selection) -> str:
    """Why each item is left out, with each unsettled upstream item's gap-card command named once."""
    waits = selection.waits_for
    shared = {}  # a reason -> the items it leaves out, so a reason several items share is written once (M3)
    for item, why in selection.left_out.items():
        if item not in waits:
            shared.setdefault(why, []).append(item)
    reasons, named = [], set()
    for item, why in selection.left_out.items():
        if item in waits:
            reasons.append(WAITS_SHORT.format(item=item, missing=", ".join(waits[item])))
        elif why not in named:
            named.add(why)
            reasons.append(f"{', '.join(shared[why])}: {why}")
    upstream = list(dict.fromkeys(u for missing in waits.values() for u in missing))
    if upstream:
        reasons.append(WAITS_GAP_CARDS.format(commands="; ".join(GAP_CARD_COMMAND.format(item=u) for u in upstream)))
    return "; ".join(reasons)


def write_briefs(case_dir, m, *, analyst, items, kind, tier2=None, now=None, selection=None) -> list:
    """Write the brief of the first item set `select` gives (or `selection`, already made for this request);
    returns its path in a list. Refused, with nothing written, when every item is left out (the reason names
    each missing item and its `--gap-card` command), and when the tier-2 file holds what this brief does not
    use: candidates go only in a plan brief, outputs only in a results brief. Before a results brief, once the
    budget and running checks pass (`team_files.check_room`), it applies the after-cap rule to the set's open
    `blocks: later` cards (`team_record.apply_after_cap_later`, which records them as a coach call); it is then
    refused, with that call written, while a card of the set has its last ask due: the call holds the
    `last_ask` the refusal asks the coach to act on."""
    case = _case(case_dir)
    tier2 = _check_tier2(case, tier2)
    if selection is None:
        selection = select(case, m, analyst=analyst, items=items, kind=kind)
    if not selection.groups:
        raise TeamRefused("no item can go in a brief: " + _left_out_reasons(selection))
    reply_kind, group = selection.groups[0]
    unused = "outputs" if reply_kind == "plan" else "candidates"
    if tier2.get(unused):
        raise TeamRefused(f'this request writes a {reply_kind} brief, which takes no tier-2 "{unused}"; '
                          "leave them out of the tier-2 file")
    if reply_kind == "results":  # the after-cap rule for the set's blocks: later cards (spec §5.6)
        team_files.check_room(case, agent_type=PLUGIN_PREFIX + analyst, items=group, now=now)  # refused: no card moves
        plan_briefs = sorted({b.nnn for item in group for b in _plan_briefs(case, item)})
        due = team_record.apply_after_cap_later(case, m, plan_briefs)
        if due:
            raise TeamRefused(LAST_ASK_FIRST.format(keys=", ".join(due), items=", ".join(group)))
    written_at = team_files.utc_stamp(now)
    if reply_kind == "plan":
        body = _plan_body(case, m, group, tier2)
    else:
        body = _results_body(case, m, group, tier2, written_at)
    return [team_files.write_brief(case, agent_type=PLUGIN_PREFIX + analyst, reply_kind=reply_kind, items=group,
                                   body=body, now=written_at)]


def cancel(case_dir, m, nnn: int) -> None:
    """`team-brief --cancel NNN`: cancel the brief; for one that cannot be read, its marker keeps the items the
    map gives the brief's own analyst (`team_files.cancel`'s `owners`)."""
    team_files.cancel(case_dir, nnn, owners={item: spec["owner"] for item, spec in m["items"].items()})
