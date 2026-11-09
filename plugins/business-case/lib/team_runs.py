"""The run list, the invocation blocks and `bc.py team-run` (spec §5.0 step 2 and "background", §5.10).

After `team_record.record_call`, `blocks_for_call` turns each command the merged plans name into one run
in `team/runs.json` (the shape is in `team_files`) and one printed entry:

- a command the coach runs gets a new `run_id` and an invocation block: the route's `subagent_type`, then
  the fenced `plugin-run` block. The block's `case` is the case folder relative to the git root, its
  `answers_path` the call's answers file, and its `inputs_from` comes from `inputs_from` below. The block
  is printed only when the standard's `check_invocation()` passes it with the map's commands; otherwise
  its errors are printed and no run is recorded.
- a `coach_runs: false` command (`value-ip:analyze`, `product-finance:cost-coverage`) gets no `run_id` and
  no block: an open person-run
  entry keyed `person:<lowest brief NNN>:<command>`, and the line the coach shows the person.
- a command in `held_commands` gets no block and no run while the card that holds it is open; a later
  call prints its block.

A command that already has an open run (a run_id, or a person-run entry) gets no second run: the new
plans join that run's `briefs`, and STILL_RUNNING_LINE is printed once.

The cards code makes (`team_record`, spec §5.0 step 2, R10-1):

- an open rerun card holds its command, as an open conflict card does: no block. `[No preference]` leaves
  it open. After "use the earlier result" the card's plans join the earlier run's `briefs`, so no block is
  ever printed for them; after "run it again" the command gets its block, with a new `run_id`.
- the case cards are applied first. "use it for this case" (the file's newest case answer) records the
  file as an ended run with no `run_id` of each merged plan whose `runs` name its command and that holds no
  ended run of it, a plan merged after the answer included. "do not use it" turns each ended run of the
  file into a gap, and records a gap for each such plan that has no coach run in flight. That run is the
  plan's open person-run entry when it has one.

`ended_runs_for` names, per command, the newest ended run with a result file of the given plans, counting
the earlier run a rerun card of those plans points at.

A command counts as named by a plan brief until the run list holds a run of it whose `briefs` list that
brief. So one command that several merged plans name is one run, with every brief in `briefs`.

A plan brief names its upstream runs in its body under BODY_UPSTREAM_RUNS: a list of `{command, run_id,
result_file}` (spec §5.0 step 1, "each ended run that a plan for an upstream item named"). `inputs_from`
reads it.

`done` and `status` find the result of a run by its `run_id`. For a plugin that has a `graph` in the plugin map,
`brain_read.find` reads the run from the graph and gives its snapshot in `team/upstream/` of the case; the run
entry then also holds `graph_run` and `graph_results`. For each other plugin they use the glob
`.<plugin>/results/*-<run_id>.json` under the git root (`team_files.repo_root`). A file counts only when its resolved path stays in the git root
(`team_files.inside_root`, the one path rule), its `run.run_id`
equals the run_id and its `run.case` equals the case (C14: the glob also matches `foo-acme-0001`). More
than one such file is refused. The one file must pass `check_result()` and `check_result_file()`.

Python 3.9 syntax only.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from lib import brain_read, digest, plugin_map, plugin_result, team_files, team_record, team_reply
from lib.team_files import TeamRefused

BODY_UPSTREAM_RUNS = "upstream_runs"
SLUG_LIMIT = 40
MISSING_ENTRY_LINE = ("This run has no earlier {dep} result to build on, so it works from your answers alone. "
                      "A run you started yourself cannot feed it: ask me to run {dep} if you want it to.")
STILL_RUNNING_LINE = "{command} is still running from an earlier call; I will use its result when it ends."
HELD_LINE = "{command} gets no block while card {keys} is open"
ROUND_2_LINE = "{command} gets no block until the second plan round of its item set is recorded and its cards asked"
PERSON_RUN_LINE = ("Run {command} yourself, with {inputs}, and tell me when it has finished. "
                   "I will then ask you which case its result belongs to.")
# What each person-run command reads, from its command file (one entry per command the map marks not coach-run)
PERSON_RUN_INPUTS = {
    "value-ip:analyze": "the file to analyse",
    "product-finance:cost-coverage": "pricing's agentic-pricing-diagnosis.json and cost-amplifier-readout.json",
}

_COUNTER = re.compile(r"-([0-9]{4,})$")


@dataclass
class Printed:
    command: str = ""
    subagent_type: str | None = None
    block: dict | None = None
    lines: list = field(default_factory=list)


# -- the run list ---------------------------------------------------------------------------------

def _case(case_dir) -> Path:
    return Path(case_dir).resolve()


load_runs = team_files.load_runs  # team_record reads the run list too, and team_runs imports team_record


def _save_runs(case_dir, runs: list) -> None:
    path = _case(case_dir) / team_files.runs_relpath()
    path.parent.mkdir(exist_ok=True)
    data = (json.dumps({"runs": runs}, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _run(command: str, run_id, briefs: list) -> dict:
    key = run_id if run_id else team_files.person_run_key(min(briefs), command)
    return {"key": key, "command": command, "run_id": run_id, "briefs": sorted(briefs), "state": "open",
            "result_file": None, "finished_at": None, "reason": None}


# -- the run_id -----------------------------------------------------------------------------------

def _slug(case_dir) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _case(case_dir).name.lower()).strip("-")
    return slug[:SLUG_LIMIT].rstrip("-") or "case"


def _next_id(slug: str, runs: list) -> str:
    used = [int(m.group(1)) for r in runs if isinstance(r.get("run_id"), str)
            and r["run_id"].startswith(slug + "-") and (m := _COUNTER.search(r["run_id"]))
            and r["run_id"] == f"{slug}-{m.group(1)}"]
    return f"{slug}-{max(used, default=0) + 1:04d}"


def new_run_id(case_dir) -> str:
    """`<case slug, cut to SLUG_LIMIT, trailing "-" stripped>-<NNNN>`, one past the highest on the run list."""
    return _next_id(_slug(case_dir), load_runs(case_dir))


# -- the plans ------------------------------------------------------------------------------------

def _plan_runs(case: Path, nnn: int) -> list:
    """The `runs` of plan brief NNN's checked reply. Refused when the reply changed since its check."""
    record = team_reply.read_check(case, nnn)
    reply = case / team_files.reply_relpath(nnn)
    try:
        data = reply.read_bytes()
    except OSError:
        raise TeamRefused(f"{team_files.reply_relpath(nnn)} cannot be read") from None
    if record.get("kind") != "plan" or digest.sha256_hex(data) != record.get("reply_sha256"):
        raise TeamRefused(f"{team_files.reply_relpath(nnn)} is not the plan its check record passed")
    runs = json.loads(data.decode("utf-8")).get("runs", [])
    return list(dict.fromkeys(runs))


_HOLDS = ("conflict", "rerun", "plan")


def _holds(card: dict, command: str) -> bool:
    """Whether `card` holds `command`: it is open, and it is a conflict, rerun or plan card that names the
    command or sets one of its inputs. A plan card that sets an input holds its command until the record
    holds an option for it, whether it is not yet asked, skipped, answered in free text or held (spec §5.6)."""
    return card.get("made_by") in _HOLDS and card.get("answer") is None \
        and (card.get("subject", {}).get("command") == command
             or any(command in o.get("sets", {}) for o in card.get("options", [])))


def held_commands(case_dir, plans) -> set:
    """The commands that get no block now: each command an open card holds (`holding_cards`), and every map
    command a plan among `plans` names while it waits for its item set's second plan round
    (`team_record.round_2_due`)."""
    held = set()
    for card in team_record.latest_cards(case_dir).values():
        if card.get("made_by") in _HOLDS and card.get("answer") is None:
            command = card.get("subject", {}).get("command")
            if command:
                held.add(command)
            for option in card.get("options", []):
                held.update(option.get("sets", {}))
    for nnn in plans:
        if team_record.round_2_due(case_dir, nnn):
            held.update(_plan_runs(_case(case_dir), nnn))
    return held


def holding_cards(case_dir, command: str) -> list:
    """The keys of the open cards that hold `command`, in record order."""
    return [key for key, card in team_record.latest_cards(case_dir).items() if _holds(card, command)]


def _pending(case: Path, m, runs: list) -> dict:
    """Map command -> the merged plan briefs that name it and that no run of it lists yet, in brief order.
    A name in a plan's `runs` that is no map command is a tier-2 skill: the coach runs it in the main
    session, with no block and no run."""
    known = plugin_map.commands(m)
    out = {}
    for nnn in sorted(team_record.latest_merged(case)):
        for command in _plan_runs(case, nnn):
            if command in known and not any(r.get("command") == command and nnn in r.get("briefs", []) for r in runs):
                out.setdefault(command, []).append(nnn)
    return out


# -- inputs_from ----------------------------------------------------------------------------------

def _named_run_ids(case: Path, briefs) -> set:
    named = set()
    for nnn in briefs:
        body = team_files.read_brief(case / team_files.brief_relpath(nnn)).body
        for entry in body.get(BODY_UPSTREAM_RUNS, []) or []:
            if isinstance(entry, dict) and isinstance(entry.get("run_id"), str) and entry["run_id"]:
                named.add((entry.get("command"), entry["run_id"]))
    return named


def inputs_from(case_dir, m, command, briefs) -> list:
    """For each command in `command`'s `reads_from`, the newest ended run of it that has a `run_id` and a
    result file, among the runs the `briefs` name: at most one entry each. A gap run, and a run with no
    `run_id`, never enter."""
    case = _case(case_dir)
    named = _named_run_ids(case, briefs)
    runs = load_runs(case)
    out = []
    for dep in plugin_map.reads_from(m, command):
        found = [(r.get("finished_at") or "", i, r) for i, r in enumerate(runs)
                 if r.get("command") == dep and r.get("state") == "ended" and r.get("run_id")
                 and r.get("result_file") and (dep, r["run_id"]) in named]
        if found:
            newest = max(found, key=lambda x: (x[0], x[1]))[2]
            out.append({"plugin": dep.split(":")[0], "run_id": newest["run_id"],
                        "result_file": newest["result_file"]})
    return out


# -- the blocks -----------------------------------------------------------------------------------

def _case_plans(case: Path, runs: list, command: str, *, open_too: bool) -> list:
    """The merged plans whose `runs` name `command` and that hold no ended run of it; with `open_too`, also
    none that holds an open run of it with a run_id (a coach run in flight)."""
    def holds(nnn, r):
        return r.get("command") == command and nnn in r.get("briefs", []) and (
            r.get("state") == "ended" or (open_too and r.get("state") == "open" and r.get("run_id")))
    return [nnn for nnn in sorted(team_record.latest_merged(case)) if command in _plan_runs(case, nnn)
            and not any(holds(nnn, r) for r in runs)]


def _record_case_run(runs: list, command: str, plans: list, **state) -> None:
    """Set `state` on the plans' run of `command` with no run_id: their open person-run entry, else the entry
    keyed by the lowest plan, else a new one."""
    entry = next((r for r in runs if r.get("command") == command and not r.get("run_id")
                  and r.get("state") == "open" and set(r.get("briefs", [])) & set(plans)), None) \
        or next((r for r in runs if r.get("key") == team_files.person_run_key(min(plans), command)), None)
    if entry is None:
        entry = _run(command, None, plans)
        runs.append(entry)
    entry["briefs"] = sorted(set(entry.get("briefs", [])) | set(plans))
    entry.update(state)


def _apply_case_answers(case: Path, call) -> None:
    """Record the case cards in the run list (see the module text). A "do not use it" answered in `call`
    turns each ended run of its file into a gap, and records a gap for each plan with no ended run and no
    coach run in flight. Then every file whose newest case answer is "use it for this case" is recorded as
    an ended run of each plan with no ended run of its command, plans merged since the answer included."""
    cards = team_record.latest_cards(case)
    for key in call.answered:
        card = cards.get(key, {})
        if card.get("made_by") != "case" or card["answer"]["label"] != team_record.NOT_FOR_CASE:
            continue
        command, rel = card["subject"].get("command"), card["subject"].get("result_file")
        runs = load_runs(case)
        reason = f"the person chose not to use {rel} (card {key})"
        for r in runs:
            if not r.get("run_id") and r.get("state") == "ended" and r.get("result_file") == rel:
                r.update(state="gap", result_file=None, finished_at=None, reason=reason)
        plans = _case_plans(case, runs, command, open_too=True)
        if plans:
            _record_case_run(runs, command, plans, state="gap", result_file=None, finished_at=None, reason=reason)
        _save_runs(case, runs)
    used = {}  # result file -> the subject of a case card for it answered "use it for this case"
    for card in cards.values():
        if card.get("made_by") == "case" and (card.get("answer") or {}).get("label") == team_record.USE_FOR_CASE:
            used.setdefault(card["subject"].get("result_file"), card["subject"])
    for rel, subject in used.items():
        if team_reply.newest_case_answer(case, rel) != team_record.USE_FOR_CASE:
            continue
        runs = load_runs(case)
        plans = _case_plans(case, runs, subject.get("command"), open_too=False)
        if plans:
            _record_case_run(runs, subject.get("command"), plans, state="ended", result_file=rel,
                             finished_at=subject.get("finished_at"), reason=None)
            _save_runs(case, runs)


def _use_earlier(case: Path, runs: list, command: str, briefs: list) -> list:
    """Join each of `briefs` that a rerun card answered "use the earlier result" covers to that card's
    earlier run; returns the briefs left."""
    for card in team_record.latest_cards(case).values():
        subject = card.get("subject", {})
        if card.get("made_by") != "rerun" or subject.get("command") != command \
                or (card.get("answer") or {}).get("label") != team_record.USE_EARLIER:
            continue
        covered = [b for b in briefs if b in subject.get("briefs", [])]
        earlier = next((r for r in runs if r.get("key") == subject.get("run")), None)
        if covered and earlier is not None:
            earlier["briefs"] = sorted(set(earlier.get("briefs", [])) | set(covered))
            _save_runs(case, runs)
            briefs = [b for b in briefs if b not in covered]
    return briefs


def blocks_for_call(case_dir, m, call) -> list:
    """Record a run for each command the merged plans name and no run lists yet, and return what to print
    for each (see the module text). `call` is the `team_record.Call` just recorded."""
    case = _case(case_dir)
    _apply_case_answers(case, call)
    runs = load_runs(case)
    pending = _pending(case, m, runs)
    if not pending:
        return []
    held = held_commands(case, sorted({n for briefs in pending.values() for n in briefs}))
    known = plugin_map.commands(m)
    answers_path = str(case / team_files.answers_relpath(call.nnn))
    case_rel = team_files.repo_relative(case, case)
    printed = []
    for command, briefs in pending.items():
        briefs = _use_earlier(case, runs, command, briefs)
        if not briefs:
            continue
        running = next((r for r in runs if r.get("command") == command and r.get("state") == "open"), None)
        if running is not None:  # one open run per command: this plan shares it
            running["briefs"] = sorted(set(running.get("briefs", [])) | set(briefs))
            _save_runs(case, runs)
            printed.append(Printed(command=command, lines=[STILL_RUNNING_LINE.format(command=command)]))
            continue
        if command in held:
            keys = ", ".join(holding_cards(case, command))
            line = HELD_LINE.format(command=command, keys=keys) if keys else ROUND_2_LINE.format(command=command)
            printed.append(Printed(command=command, lines=[line]))
            continue
        if not plugin_map.coach_runs(m, command):
            runs.append(_run(command, None, briefs))
            _save_runs(case, runs)
            printed.append(Printed(command=command, lines=[PERSON_RUN_LINE.format(command=command, inputs=PERSON_RUN_INPUTS[command])]))
            continue
        run_id = new_run_id(case)
        block = {"command": command, "automated": True, "answers_path": answers_path, "case": case_rel,
                 "run_id": run_id, "inputs_from": inputs_from(case, m, command, briefs)}
        errors = plugin_result.check_invocation(block, known)
        if errors:
            printed.append(Printed(command=command, lines=list(errors)))
            continue
        got = {entry["plugin"] for entry in block["inputs_from"]}
        lines = [MISSING_ENTRY_LINE.format(dep=dep) for dep in plugin_map.reads_from(m, command)
                 if dep.split(":")[0] not in got]
        runs.append(_run(command, run_id, briefs))
        _save_runs(case, runs)
        printed.append(Printed(command=command, subagent_type=plugin_map.route(m, command), block=block,
                               lines=lines))
    return printed


def render(printed: list) -> list:
    """The lines `team-answers` prints for each entry: `subagent_type: <route>`, the fenced block, then its
    lines for the person."""
    out = []
    for p in printed:
        if p.subagent_type and p.block is not None:
            out += [f"subagent_type: {p.subagent_type}", "```plugin-run",
                    json.dumps(p.block, ensure_ascii=False), "```"]
        out += list(p.lines)
    return out


# -- finding a result file -------------------------------------------------------------------------

def _find(case: Path, run: dict):
    """(relative path, doc, path, graph fields) of the run's one result file; None when there is none;
    refused for two. The run of a plugin that has a graph comes from the graph, as a snapshot of the case:
    `brain_read.NoGraphRun` when the graph gives none. The graph fields are empty for a result file."""
    if brain_read.graph_of(run["command"]) is not None:
        return brain_read.find(case, run)
    root = team_files.repo_root(case)
    run_id, want_case = run["run_id"], team_files.repo_relative(case, case)
    folder = root / f".{run['command'].split(':')[0]}" / "results"
    found = []
    for path in sorted(folder.glob(f"*-{run_id}.json")) if folder.is_dir() else []:
        rel = team_files.inside_root(root, path)
        if rel is None or not path.is_file():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        meta = doc.get("run") if isinstance(doc, dict) else None
        if isinstance(meta, dict) and meta.get("run_id") == run_id and meta.get("case") == want_case:
            found.append((rel, doc, path, {}))
    if len(found) > 1:
        raise TeamRefused(f"more than one result file holds run_id {run_id}: "
                          f"{', '.join(f[0] for f in found)}; ask the person which file the run wrote and to move "
                          "the other out of its results folder, then run bc.py team-run --status; or record the "
                          f"run as a gap with bc.py team-run --fail {run.get('key') or run_id}")
    return found[0] if found else None


def _problems(doc, path: Path) -> list:
    return list(plugin_result.check_result(doc)) + list(plugin_result.check_result_file(path))


def _entry(runs: list, key: str) -> dict:
    for run in runs:
        if run.get("key") == key:
            return run
    raise TeamRefused(f"no run {key} in {team_files.runs_relpath()}")


def done(case_dir, run_id) -> dict:
    """The route's dispatch for `run_id` has ended: record the run as ended with its result file, or as a
    gap when no file passes. Returns the run. Refused for a run that is not open."""
    case = _case(case_dir)
    runs = load_runs(case)
    run = _entry(runs, run_id)
    if not run.get("run_id"):
        raise TeamRefused(f"{run_id} has no run_id; a person's run ends by its case card or team-run --fail")
    if run.get("state") != "open":
        raise TeamRefused(f"run {run_id} has already ended ({run.get('state')})")
    try:
        found = _find(case, run)
    except brain_read.NoGraphRun as miss:
        run.update(state="gap", reason=str(miss))
        _save_runs(case, runs)
        return dict(run)
    if found is None:
        run.update(state="gap", reason=f"no result file of this case holds run_id {run_id}")
    else:
        rel, doc, path, graph = found
        problems = _problems(doc, path)
        if problems:
            run.update(state="gap", reason=f"{rel} fails the checker: " + "; ".join(problems))
        else:
            run.update(state="ended", result_file=rel, finished_at=doc["run"]["finished_at"], **graph)
    _save_runs(case, runs)
    return dict(run)


def fail(case_dir, key) -> dict:
    """Record the open run or person-run entry `key` as a gap. Returns it."""
    case = _case(case_dir)
    runs = load_runs(case)
    run = _entry(runs, key)
    if run.get("state") != "open":
        raise TeamRefused(f"run {key} has already ended ({run.get('state')})")
    run.update(state="gap", reason="recorded as a gap by team-run --fail")
    _save_runs(case, runs)
    return dict(run)


def status(case_dir) -> list:
    """End each open run whose result file now exists and passes; returns every run that was open, as it
    now stands. A person-run entry has no run_id, so nothing finds its file: it stays open. A run with
    more than one matching file stays open, and its entry carries `refused`, naming the files. A run that
    its graph does not give yet stays open."""
    case = _case(case_dir)
    runs = load_runs(case)
    out = []
    changed = False
    for run in runs:
        if run.get("state") != "open":
            continue
        if run.get("run_id"):
            try:
                found = _find(case, run)
            except brain_read.NoGraphRun:
                found = None  # the graph does not hold the run yet: the run stays open
            except TeamRefused as exc:
                out.append(dict(run, refused=str(exc)))  # two files: the run stays open, and says why
                continue
            if found is not None and not _problems(found[1], found[2]):
                run.update(state="ended", result_file=found[0], finished_at=found[1]["run"]["finished_at"],
                           **found[3])
                changed = True
        out.append(dict(run))
    if changed:
        _save_runs(case, runs)
    return out


def due_later_cards(case_dir, m, plan) -> list:
    """The open `blocks: later` cards of plan brief `plan`, once every map command it named has a run that
    has ended (with a file or as a gap) or is held; else []. A tier-2 skill has no run."""
    case = _case(case_dir)
    runs = load_runs(case)
    held = held_commands(case, [plan])
    known = plugin_map.commands(m)
    for command in _plan_runs(case, plan):
        if command in held or command not in known:
            continue
        if not any(r.get("command") == command and plan in r.get("briefs", []) and r.get("state") in ("ended", "gap")
                   for r in runs):
            return []
    return [key for key, card in team_record.latest_cards(case).items()
            if card.get("brief") == plan and card.get("blocks") == "later" and card.get("answer") is None]


def ended_runs_for(case_dir, plans) -> dict:
    """Per command the plans' checked replies name, the newest ended run of it with a result file among the
    runs whose `briefs` hold one of `plans`, or that a rerun card of those plans points at as its earlier
    run. A run with no `run_id` (a person's run) counts; a gap never does."""
    case = _case(case_dir)
    plans = set(plans)
    runs = load_runs(case)
    pointed = set()  # (command, run key) of each earlier run a rerun card of these plans points at
    for card in team_record.latest_cards(case).values():
        subject = card.get("subject", {})
        if card.get("made_by") == "rerun" and plans & set(subject.get("briefs", [])):
            pointed.add((subject.get("command"), subject.get("run")))
    out = {}
    for nnn in sorted(plans):
        for command in _plan_runs(case, nnn):
            found = [(r.get("finished_at") or "", i, r) for i, r in enumerate(runs)
                     if r.get("command") == command and r.get("state") == "ended" and r.get("result_file")
                     and (plans & set(r.get("briefs", [])) or (command, r.get("key")) in pointed)]
            if found and command not in out:
                out[command] = dict(max(found, key=lambda x: (x[0], x[1]))[2])
    return out
