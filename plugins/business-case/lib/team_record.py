"""The card record and the answers file, `bc.py team-answers` (spec §5.0 step 2, §5.6 "Reading an answer").

One coach call NNN writes `team/answers-NNN.json`, then `team/cards-NNN.json` (the shapes are defined in
`team_files`). Both are cumulative: each carries every earlier answer of the case's team.

A call first merges every checked plan that no earlier call merged: a plan brief whose reply has a check
record from `team_reply.read_check` that still matches the reply's bytes. While `open_briefs(kind="plan")`
lists a brief, a call merges no plan and refuses an answer to a plan card; it records only the cards
code made. Each plan card is keyed `<brief NNN>:<id>`; a card code makes is keyed `code:<n>`.

Then it records the coach's answers, each the text the card returned (`read_answer`):

- an option label, matched exactly, " (Recommended)" included: the card is answered, `settled_by:
  recommended` for a label ending " (Recommended)" and `person` for any other; its `sets` go to the answers
  file with the card's round;
- an option label that the person typed at the start of the text (`_typed_label`), in any case, with or
  without " (Recommended)", alone or followed by one of NOTE_MARKS: the card is answered, `settled_by:
  person`, and a text that holds more than the label is kept as the person's note;
- `[No preference]`: the card stays open;
- any other text is free text: it is kept with the card, the card stays open, and it sets nothing. The
  entry must say how the coach reads it. With `reading` (an option label), code makes a card headed "Your
  words", and only its exact option READ_YES records that reading, `settled_by: person`; any other answer
  keeps the card open, with the reason it is asked again. With `why`, the card stays open and keeps the
  reason. Free text is never overridden (R7-4).

Every answer passed, of any kind, appends the call to the card's `passed`.

In the answers file, a value of a later call replaces the earlier value of that input, whatever its card
key, except that a `recommended` value never replaces a `person` value. When two cards of one call set one
input of one command to different values, code makes one conflict card with both values as options; it
has no recommended option unless the map gives that input to one item (`plugin_map.input_owner`), whose
plan's value then comes first. A further value for an input whose conflict card is open joins that card
as one more option; the card keeps its MAX_OPTIONS most recent values and names each dropped one in its
question. While a conflict card is open, its input is left out of the answers file. Recommended
picks that disagree raise no conflict over an input that holds a `person` value: the person's value stays.

A plan's round counts every plan brief for its item, cancelled and expired ones included (spec §5.6); a
plan whose round would pass `MAX_PLAN_ROUNDS` is refused.

Code makes three more kinds of card, keyed `code:<n>` and recorded as plan cards are (spec §5.0 step 2,
R10-1). None has a recommended option.

- A rerun card, made inside `record_call` when a newly merged plan names a map command whose run list holds
  an ended run with a `run_id` and a result file, and no open run. One card per command: a later plan that
  names the command while its card is open joins the card's `subject.briefs`. `subject.run` is the key of
  that earlier run. `team_runs` reads the answer.
- A case card, `case_card`, for a result file with no `run.case`, inside the git root.
- A gap card, `gap_card`, for a map item.

`case_card` and `gap_card` each write one call of their own that merges no plan and records no answer. An
open case card for the same file, or an open gap card for the same item, is returned instead of a new one.

The second plan round and the after-cap rule (spec §5.0 step 3, §5.6):

- `needs_round_2`: a merged round-1 plan with one of its own `blocks: now` cards open, or an answered card
  its `follow_up` lists. While its item set's second round is still to come (`round_2_open`), and while a
  second-brief plan is not yet capped (`uncapped_round_2`), together `round_2_due`, `team_runs.held_commands`
  holds its commands and `team_brief.select` gives its item set no results brief.
- `apply_after_cap`, right after `record_call`: an item set caps once the coach has passed an answer for every
  `blocks: now` card of its second-brief plan (at once, when it has none). The rule applies once per such plan,
  which the card record then lists under `capped`; a call that stopped after `record_call` leaves it to the
  next call. The open `blocks: now` plan cards of that plan and of the set's first plan (by brief, never by a
  shared command), and no other card, take their
  recommended option (`settled_by: recommended`), except a card with free text, which stays open, and a
  `hard_to_undo` card, which gets `last_ask`. A card code made never takes an option by itself.
- `apply_after_cap_later`, as `team-brief` writes a set's results brief: the same rule for the set's open
  `blocks: later` cards, written as a new call.
- The next answer passed for a `last_ask` card ends the last ask; an answer that is no option makes it
  `held`. `held_cards` lists the open conflict cards, the plan cards with free text and the held cards;
  `last_ask_cards` the cards whose last ask is due.

Python 3.9 syntax only.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from lib import digest, paths, plugin_map, plugin_result, rubric, team_files, team_reply
from lib.team_files import TeamRefused

NO_PREFERENCE = "[No preference]"
MAX_PLAN_ROUNDS = 2
MAX_OPTIONS = team_reply.MAX_OPTIONS  # AskUserQuestion takes 2 to 4 options
CONFLICT_HEADER = "Conflict"
RECOMMENDED = team_reply.RECOMMENDED

RERUN_HEADER, CASE_HEADER, GAP_HEADER = "Run again?", "Which case?", "Missing"
RUN_AGAIN, USE_EARLIER = "run it again", "use the earlier result"
USE_FOR_CASE, NOT_FOR_CASE = team_files.CASE_ANSWER_LABEL, "do not use it"
GO_ON, WAIT = "go on without it", "wait for it"
READ_HEADER = "Your words"
READ_YES, READ_NO = "yes, record it", "no, ask the card again"
READ_QUESTION = 'On the card "{header}" you wrote: "{text}". Record it as the option "{label}"?'
NOTE_MARKS = ",;:.!?(-\u2013\u2014\n"  # a mark that ends a typed label and starts the note
AGAIN_LAST_ASK = "this choice is hard to undo, so it gets one more ask before the case goes on"
AGAIN_HELD = "this choice is hard to undo, and code picks no option for it"
AGAIN_CODE = "code picks no option for this card, so only your pick closes it"
AGAIN_REJECTED = 'you did not say yes to the reading "{label}" of your words "{text}"'
AGAIN_UNREAD = 'no option fits your words "{text}": {why}'
AGAIN_OLD = 'your words "{text}" name no option'
RERUN_QUESTION = ("{command} already gave a result on {date}. A new run takes time, and the case then uses the "
                  "new result. Run {command} again?")
CASE_QUESTION = ("A result of the {plugin} plugin from {date} does not say which business case it is for "
                 "(file {file}). Only a result for this case can be evidence here. Use it for this case?")
GAP_QUESTION = "Nothing has come in yet for {item}. Go on without it, or wait for it?"
CONFLICT_QUESTION = ("Your answers on the cards headed {headers} give different values for the same setting "
                     "({name} of {command}). The run can use only one. Which value should it use?")
CONFLICT_OPTION = 'On the card "{header}", the answer "{label}" gave this value. This option gives the run that value.'
NOTE_LINE = "To add a note to an option, type the option's label, then a comma, then your note."
NOT_GIVEN = object()  # `record_call` got no `asked`: a direct call that holds answers only keeps its form

CARDS_NAME = re.compile(r"^cards-([0-9]{3}|[1-9][0-9]{3,})\.json$")
ANSWERS_NAME = re.compile(r"^answers-([0-9]{3}|[1-9][0-9]{3,})\.json$")
_CODE_KEY = re.compile(r"^code:([1-9][0-9]*)$")


@dataclass
class Call:
    nnn: int = 0
    merged_plans: list = field(default_factory=list)
    new_cards: list = field(default_factory=list)
    answered: list = field(default_factory=list)  # the cards given an option in this call
    read: list = field(default_factory=list)  # those of them read from typed text or from a reading card


# -- reading an answer ------------------------------------------------------------------------------

def _base(label: str) -> str:
    return label[:-len(RECOMMENDED)] if label.endswith(RECOMMENDED) else label


def _typed_label(card, text):
    """The option label the person typed at the start of `text`, or None: an option label, with or without its
    " (Recommended)" suffix, in any case, alone or followed by spaces and one of NOTE_MARKS. The longest name
    wins, so a label that starts another label never takes its place."""
    typed = text.strip()
    names = sorted(((name, opt["label"]) for opt in card.get("options", []) if opt.get("label")
                    for name in dict.fromkeys((opt["label"], _base(opt["label"])))),
                   key=lambda x: len(x[0]), reverse=True)
    for name, label in names:
        head, rest = typed[:len(name)], typed[len(name):]
        if head.casefold() != name.casefold():
            continue
        if not rest.strip() or rest.lstrip(" \t")[:1] in NOTE_MARKS:
            return label
    return None


def read_answer(card, text) -> tuple:
    """`("option", label, "recommended" | "person")` for an option label returned as it is, `("typed", label,
    "person")` for an option label the person typed (`_typed_label`), with or without a note after it,
    `("open", None, None)` for `[No preference]`, or `("free", text, None)`."""
    if text == NO_PREFERENCE:
        return ("open", None, None)
    for opt in card.get("options", []):
        if opt.get("label") == text:
            return ("option", text, "recommended" if text.endswith(RECOMMENDED) else "person")
    label = _typed_label(card, text)
    if label is not None:
        return ("typed", label, "person")
    return ("free", text, None)


def _add_text(card, text) -> None:
    card["free_text"] = list(card.get("free_text", [])) + [text]


def _note_of(card, text, label) -> bool:
    """Whether the typed `text` holds more than the label: then the whole text is the person's note."""
    return text.strip().rstrip(NOTE_MARKS + " \t").casefold() not in {label.casefold(), _base(label).casefold()}


def reading_card_of(cards: dict, key: str):
    """The key of the open reading card that asks about card `key`, or None."""
    return next((k for k, c in cards.items() if c.get("made_by") == "reading" and c.get("answer") is None
                 and c.get("subject", {}).get("card") == key), None)


def again_because(card) -> str | None:
    """Why an open card that was asked before is asked again, or None when it is not asked again (a plan card
    the person skipped waits for the cap)."""
    if card.get("answer") is not None or not card.get("passed"):
        return None
    if card.get("again_because"):
        return card["again_because"]
    if card.get("last_ask"):
        return AGAIN_LAST_ASK
    if card.get("made_by") == "plan" and card.get("held"):
        return AGAIN_HELD
    if card.get("made_by") in ("conflict", "rerun", "case", "gap"):
        return AGAIN_CODE
    if card.get("free_text"):  # a card record written before again_because existed
        return AGAIN_OLD.format(text=card["free_text"][-1])
    return None


# -- the files on disk ------------------------------------------------------------------------------

def _team(case_dir) -> Path:
    return Path(case_dir).resolve() / paths.TEAM_DIR


def _numbers(folder: Path, pattern) -> list:
    if not paths.stat_is_dir(folder):
        return []
    return sorted(int(m.group(1)) for p in folder.iterdir() if (m := pattern.match(p.name)))


def _next_call(case: Path) -> int:
    """One past the highest number of any card record or answers file. An answers file left without its card
    record (the card write failed, or the process stopped between the two) keeps its number, so it never blocks
    a later call (final re-review N1)."""
    folder = case / paths.TEAM_DIR
    return max(_numbers(folder, CARDS_NAME) + _numbers(folder, ANSWERS_NAME), default=0) + 1


def _read_json(path: Path, what: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise TeamRefused(f"{what} cannot be read") from None


def _latest_record(case_dir) -> dict:
    calls = _numbers(_team(case_dir), CARDS_NAME)
    if not calls:
        return {}
    record = _read_json(_team(case_dir) / f"cards-{calls[-1]:03d}.json", team_files.cards_relpath(calls[-1]))
    if not isinstance(record, dict) or not isinstance(record.get("cards"), dict):
        raise TeamRefused(f"{team_files.cards_relpath(calls[-1])} is not a card record")
    return record


def latest_cards(case_dir) -> dict:
    """The cards of the newest card record, by key; {} before the first call."""
    return _latest_record(case_dir).get("cards", {})


def latest_merged(case_dir) -> list:
    """The plan briefs the newest card record has merged, in order; [] before the first call."""
    return list(_latest_record(case_dir).get("merged", []))


def latest_answers_path(case_dir):
    """The newest answers file's absolute path, the one beside the newest card record; None before the first
    call."""
    calls = _numbers(_team(case_dir), CARDS_NAME)
    return Path(case_dir).resolve() / team_files.answers_relpath(calls[-1]) if calls else None


def latest_answers(case_dir) -> dict:
    """The newest answers file; {} before the first call."""
    path = latest_answers_path(case_dir)
    if path is None:
        return {}
    rel = f"{paths.TEAM_DIR}/{path.name}"
    doc = _read_json(path, rel)
    if not isinstance(doc, dict):
        raise TeamRefused(f"{rel} is not an answers file")
    return doc


def open_cards(case_dir) -> list:
    """The keys of the cards with no answer, in record order."""
    return [key for key, card in latest_cards(case_dir).items() if card.get("answer") is None]


def free_text(case_dir, item) -> list:
    """The free text kept with every card of `item`: a plan card whose brief names the item, or a card
    code made whose subject names it."""
    case = Path(case_dir).resolve()
    out = []
    for card in latest_cards(case).values():
        brief = card.get("brief")
        if isinstance(brief, int) and not isinstance(brief, bool):
            items = team_files.read_brief(case / team_files.brief_relpath(brief)).items
        else:
            items = [card.get("subject", {}).get("item")]
        if item in items:
            out += list(card.get("free_text", []))
    return out


def _write_atomic(path: Path, doc) -> None:
    data = _encoded(doc)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# -- merging plans ----------------------------------------------------------------------------------

def _plan_briefs(case: Path) -> list:
    """Every brief of the case, in NNN order (`team_files.all_briefs`); callers keep the plan briefs."""
    return team_files.all_briefs(case)


def _checked_plan(case: Path, nnn: int):
    """The plan reply of brief NNN when it has a passing check that matches its bytes; else None."""
    try:
        record = team_reply.read_check(case, nnn)
    except TeamRefused:
        return None
    reply = case / team_files.reply_relpath(nnn)
    if record.get("kind") != "plan" or not reply.is_file():
        return None
    data = reply.read_bytes()
    if digest.sha256_hex(data) != record.get("reply_sha256"):
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None


def _round(plan_briefs: list, brief) -> int:
    """The plan round of a plan brief: how many plan briefs, up to and including it, name its first item."""
    first = brief.items[0] if brief.items else None
    return sum(1 for b in plan_briefs if b.nnn <= brief.nnn and first in b.items)


def _plan_card(brief_nnn: int, rnd: int, card: dict) -> dict:
    because = card.get("because", "").strip()  # a plan checked before 0.11.0 has none: it keeps its question
    question = f"{because} {card['question']}" if because else card["question"]
    return {"brief": brief_nnn, "id": card["id"], "made_by": "plan", "round": rnd, "blocks": card["blocks"],
            "hard_to_undo": card["hard_to_undo"], "header": card["header"], "question": question,
            "options": [dict(o) for o in card["options"]], "answer": None, "free_text": [], "passed": [],
            "last_ask": False, "held": False, "subject": {}}


# -- recording a call -------------------------------------------------------------------------------

def _value_text(value) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _conflict_option(command: str, name: str, key: str, value, source: dict, recommended: bool = False) -> dict:
    """One option of a conflict card. `source` is the card whose answer gave `value`: the description names its
    header and the answer on it. One form for each option, because an exact pick of the recommended label and the
    after-cap rule both record `settled_by: recommended`, so code cannot tell them apart."""
    label = f"{_value_text(value)}, from card {key}" + (RECOMMENDED if recommended else "")
    answer = (source.get("answer") or {}).get("label", "")
    return {"label": label,
            "description": CONFLICT_OPTION.format(header=source.get("header", ""), label=_base(answer)),
            "sets": {command: {name: value}}}


def _same(a, b) -> bool:
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _open_conflict(cards: dict, command: str, name: str):
    """The key of the open conflict card on this input, or None."""
    for key, card in cards.items():
        if card.get("made_by") == "conflict" and card.get("answer") is None \
                and any(name in o.get("sets", {}).get(command, {}) for o in card.get("options", [])):
            return key
    return None


def _cap_options(card: dict) -> None:
    """Keep the MAX_OPTIONS most recent options; name each dropped value in the question, so the person
    can still type it."""
    dropped, card["options"] = card["options"][:-MAX_OPTIONS], card["options"][-MAX_OPTIONS:]
    for opt in dropped:
        label = _base(opt["label"])
        card["question"] += f" Also given, not shown as an option: {label}."


def _headers_text(cards: dict, keys: list) -> str:
    """The distinct headers of the cards `keys`, in order, each in quotes: "A", "B" and "C"."""
    headers = list(dict.fromkeys(f'"{cards[k].get("header", "")}"' for k in keys))
    return headers[0] if len(headers) == 1 else ", ".join(headers[:-1]) + " and " + headers[-1]


def _conflict_card(m, command: str, name: str, picks: list, plan_items: dict, cards: dict) -> dict:
    """One conflict card over `picks`: [(card key, value, round)], one per distinct value, in call order.
    `cards` holds the cards that gave the picks: the question and each option name them."""
    owner = plugin_map.input_owner(m, command, name)
    owned = [p for p in picks if owner is not None and owner in plan_items.get(p[0], ())]
    first = owned[0] if owned else None
    subject = {"command": command}
    if owner is not None:
        subject["item"] = owner
    card = {"brief": None, "id": None, "made_by": "conflict", "round": max(p[2] for p in picks),
            "blocks": "now", "hard_to_undo": False, "header": CONFLICT_HEADER,
            "question": CONFLICT_QUESTION.format(headers=_headers_text(cards, [p[0] for p in picks]),
                                                 name=name, command=command),
            "options": [_conflict_option(command, name, p[0], p[1], cards[p[0]], p is first) for p in picks],
            "answer": None, "free_text": [], "passed": [], "last_ask": False, "held": False, "subject": subject}
    _cap_options(card)  # in call order, so the newest values stay
    card["options"].sort(key=lambda o: not o["label"].endswith(RECOMMENDED))  # the owner's value first
    return card


def _check_answers_list(answers) -> list:
    if not isinstance(answers, list):
        raise TeamRefused("the answers must be a list of {key, answer}")
    for i, entry in enumerate(answers, 1):
        if not (isinstance(entry, dict) and {"key", "answer"} <= set(entry) <= {"key", "answer", "reading", "why"}
                and all(isinstance(v, str) for v in entry.values()) and not {"reading", "why"} <= set(entry)):
            raise TeamRefused(f"answer {i} must be an object with a text key and a text answer, and at most one "
                              "of a text reading and a text why, and nothing else")
    keys = [e["key"] for e in answers]
    repeated = sorted({k for k in keys if keys.count(k) > 1})
    if repeated:
        raise TeamRefused(f"card {', '.join(repeated)} has more than one answer in this call; pass one per card")
    return answers


def _with_skips(answers: list, asked) -> list:
    """`answers` and a `[No preference]` entry for each card in `asked` with no answer: the result of the
    question tool leaves out a card that the person skipped. `NOT_GIVEN` adds nothing. Refused for an `asked`
    that is not a list of keys, and for an answer to a card that is not in `asked`."""
    if asked is NOT_GIVEN:
        return answers
    if not (isinstance(asked, list) and all(isinstance(k, str) for k in asked)):
        raise TeamRefused("`asked` must be a list of card keys")
    given = [e["key"] for e in answers]
    not_asked = [k for k in given if k not in asked]
    if not_asked:
        raise TeamRefused(f"card {', '.join(not_asked)} has an answer but is not in `asked`; put in `asked` the key "
                          "of each card that you asked in the call")
    return answers + [{"key": k, "answer": NO_PREFERENCE} for k in dict.fromkeys(asked) if k not in given]


def record_call(case_dir, m, answers: list, asked=NOT_GIVEN) -> Call:
    """Record one coach call: merge the checked plans no earlier call merged (none while a plan brief is
    open), record `answers` ([{"key", "answer"}]), make any conflict card, and write `answers-NNN.json`
    then `cards-NNN.json`. `asked` lists the key of each card that the coach asked in the call: each one with
    no answer is recorded as `[No preference]`, a skip. Refused, with nothing written, for an unknown card key
    (in `answers` or in `asked`) or an answer to a plan card while a plan brief is open."""
    case = Path(case_dir).resolve()
    answers = _with_skips(_check_answers_list(answers), asked)
    record = _latest_record(case)
    cards = {k: dict(v) for k, v in record.get("cards", {}).items()}
    merged_before = list(record.get("merged", []))
    previous = latest_answers(case)
    nnn = _next_call(case)

    open_plans = team_files.open_briefs(case, kind="plan")
    briefs = _plan_briefs(case)
    plan_items = _plan_items(briefs, cards)  # card key -> the items of its brief
    merged = []
    named = []  # (brief NNN, round, the plan's runs) of each plan merged now
    if not open_plans:
        plan_list = [b for b in briefs if b.reply_kind == "plan"]
        for b in plan_list:
            if b.nnn in merged_before:
                continue
            reply = _checked_plan(case, b.nnn)
            if reply is None:
                continue
            rnd = _round(plan_list, b)
            if rnd > MAX_PLAN_ROUNDS:
                raise TeamRefused(f"plan brief {b.nnn:03d} would be plan round {rnd} for item "
                                  f"{', '.join(b.items)}; an item gets at most {MAX_PLAN_ROUNDS} plan rounds, "
                                  "cancelled and expired briefs included")
            for card in reply.get("cards", []):
                key = f"{b.nnn:03d}:{card['id']}"
                cards[key] = _plan_card(b.nnn, rnd, card)
                plan_items[key] = b.items
            merged.append(b.nnn)
            named.append((b.nnn, rnd, reply.get("runs", [])))
    new_cards = _rerun_cards(case, m, cards, named)

    unknown = [e["key"] for e in answers if e["key"] not in cards]
    if unknown:
        raise TeamRefused(f"no card {', '.join(unknown)} in the card record")
    if open_plans:
        plan_keys = [e["key"] for e in answers if cards[e["key"]].get("made_by") == "plan"]
        if plan_keys:
            raise TeamRefused(f"plan brief {', '.join(f'{n:03d}' for n in open_plans)} has no reply yet; "
                              f"answers to plan cards ({', '.join(plan_keys)}) wait until it has one, or it is "
                              "cancelled")

    for entry in answers:  # every check before the first change (done item 3: no reading from a claim)
        key, card = entry["key"], cards[entry["key"]]
        waits = reading_card_of(cards, key)
        if waits is not None:
            raise TeamRefused(f"card {key} waits for the reading card {waits}: pass the answer to {waits}, not "
                              f"to {key}")
        kind = read_answer(card, entry["answer"])[0]
        if card.get("made_by") == "reading" or kind != "free":
            continue
        if "reading" not in entry and "why" not in entry:
            raise TeamRefused(f"card {key} got free text: give `reading`, the option label you read it as, or "
                              "`why`, the reason no option fits it")
        if "reading" in entry and entry["reading"] not in [o.get("label") for o in card.get("options", [])]:
            raise TeamRefused(f"the reading {entry['reading']!r} of card {key} is not one of its option labels")

    picks = {}  # (command, input) -> [(key, value, round, settled_by)]
    answered = []

    read = []  # the cards given an option from typed text or from a reading card

    def pick(key, card, label, settled_by, typed=False):
        if typed:
            read.append(key)
        card["answer"] = {"label": label, "settled_by": settled_by}
        card["again_because"] = None
        card["held"] = False
        answered.append(key)
        chosen = next(o for o in card["options"] if o["label"] == label)
        for command, inputs in chosen.get("sets", {}).items():
            for name, value in inputs.items():
                picks.setdefault((command, name), []).append((key, value, card["round"], settled_by))

    for entry in answers:
        key = entry["key"]
        card = cards[key]
        card["passed"] = list(card.get("passed", [])) + ([nnn] if nnn not in card.get("passed", []) else [])
        kind, label, settled_by = read_answer(card, entry["answer"])
        if card.get("made_by") == "reading":
            _read_reading(cards, key, card, kind, label, entry["answer"], pick)
            continue
        card["again_because"] = None
        if card.get("last_ask"):  # this was the one extra ask after the cap
            card["last_ask"] = False
            card["held"] = kind not in ("option", "typed")
        if kind == "free":
            _add_text(card, label)
            if "reading" in entry:
                rkey = _next_code_key(cards)
                cards[rkey] = _code_card(
                    "reading", READ_HEADER, READ_QUESTION.format(header=card.get("header", ""), text=label,
                                                                 label=entry["reading"]),
                    [(READ_YES, f"Record \"{entry['reading']}\" as your answer, with your words as a note."),
                     (READ_NO, "Record nothing; the card is asked again on its own.")],
                    {"card": key, "label": entry["reading"], "text": label}, card.get("round", 1))
                new_cards.append(rkey)
            else:
                card["again_because"] = AGAIN_UNREAD.format(text=label, why=entry["why"])
        elif kind in ("option", "typed"):
            if kind == "typed" and _note_of(card, entry["answer"], label):
                _add_text(card, entry["answer"])
            pick(key, card, label, settled_by, typed=kind == "typed")

    out = _fold(m, cards, previous, picks, plan_items, new_cards)
    (case / paths.TEAM_DIR).mkdir(exist_ok=True)
    _write_call(case, nnn, merged_before + merged, cards, out, list(record.get("capped", [])))
    return Call(nnn=nnn, merged_plans=merged, new_cards=new_cards, answered=answered, read=read)


def _read_reading(cards: dict, key: str, card: dict, kind: str, label, text: str, pick) -> None:
    """Close the reading card `key`. Only its exact READ_YES label records the reading on the card it asks
    about, `settled_by: person`; any other answer leaves that card open with the reason it is asked again,
    and keeps text typed here with that card."""
    subject = card["subject"]
    target_key = subject["card"]
    target = cards[target_key]
    yes = kind == "option" and label == READ_YES
    card["answer"] = {"label": READ_YES if yes else READ_NO, "settled_by": "person"}
    if kind == "free" or (kind == "typed" and _note_of(card, text, label)):
        _add_text(card, text)
        _add_text(target, text)
    if target.get("answer") is not None:
        return
    if yes and subject["label"] in [o.get("label") for o in target.get("options", [])]:
        pick(target_key, target, subject["label"], "person", typed=True)
        return
    target["again_because"] = AGAIN_REJECTED.format(label=subject["label"], text=subject["text"])


def _plan_items(briefs: list, cards: dict) -> dict:
    """Card key -> the items of its plan brief."""
    out = {}
    for b in briefs:
        if b.reply_kind == "plan":
            for key, card in cards.items():
                if card.get("brief") == b.nnn:
                    out[key] = b.items
    return out


def _encoded(doc) -> bytes:
    return (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _write_call(case: Path, nnn: int, merged: list, cards: dict, answers: dict, capped: list,
                replace: bool = False) -> None:
    """Write call NNN's answers file, then its card record. A new call creates both (final review I1): when
    either number is taken, another team call wrote it, and this one is refused with nothing left behind.
    `replace` rewrites the call just recorded in this same command (`apply_after_cap`)."""
    record = {"call": nnn, "merged": merged, "capped": capped, "cards": cards}
    if replace:
        _write_atomic(case / team_files.answers_relpath(nnn), answers)
        _write_atomic(case / team_files.cards_relpath(nnn), record)
        return
    taken = "{name} already exists: another team call wrote call {nnn:03d} at the same time; run this command again"
    answers_path = case / team_files.answers_relpath(nnn)
    if not team_files._create_new(answers_path, _encoded(answers)):
        raise TeamRefused(taken.format(name=answers_path.name, nnn=nnn))
    cards_path = case / team_files.cards_relpath(nnn)
    if not team_files._create_new(cards_path, _encoded(record)):
        os.unlink(answers_path)
        raise TeamRefused(taken.format(name=cards_path.name, nnn=nnn))


def _fold(m, cards: dict, previous: dict, picks: dict, plan_items: dict, new_cards: list) -> dict:
    """The answers file after `picks` ((command, input) -> [(key, value, round, settled_by)]) land on
    `previous`: a later value replaces an earlier one, a recommended value never replaces a person value, and
    two values of one call make a conflict card (added to `cards` and `new_cards`). Refused when the result
    would fail the checker."""
    out = {command: dict(inputs) for command, inputs in previous.items()}
    code_numbers = [int(mt.group(1)) for k in cards if (mt := _CODE_KEY.match(k))]
    for (command, name), found in picks.items():
        distinct = []
        for pick in found:
            if not any(_same(pick[1], d[1]) for d in distinct):
                distinct.append(pick)
        earlier = out.get(command, {}).get(name)
        held_by_person = isinstance(earlier, dict) and earlier.get("settled_by") == "person"
        if held_by_person and all(p[3] == "recommended" for p in found):
            continue  # a recommended value never replaces a person value, through a conflict or otherwise
        folded = _open_conflict(cards, command, name)
        if folded is not None:
            card = cards[folded]
            for pick in found:
                if not any(_same(pick[1], o["sets"][command][name]) for o in card["options"]):
                    card["options"] = card["options"] + [
                        _conflict_option(command, name, pick[0], pick[1], cards[pick[0]])]
            _cap_options(card)
            continue
        if len(distinct) > 1:
            n = max(code_numbers, default=0) + 1
            code_numbers.append(n)
            key = f"code:{n}"
            cards[key] = _conflict_card(m, command, name, distinct, plan_items, cards)
            new_cards.append(key)
            continue
        settled = "person" if any(p[3] == "person" for p in found) else "recommended"
        rnd = max(p[2] for p in found)
        out.setdefault(command, {})[name] = {"value": distinct[0][1], "settled_by": settled, "round": rnd}

    for card in cards.values():  # an open conflict card keeps its input out
        if card.get("made_by") == "conflict" and card.get("answer") is None:
            for command, inputs in card["options"][0].get("sets", {}).items():
                for name in inputs:
                    out.get(command, {}).pop(name, None)
    out = {command: inputs for command, inputs in out.items() if inputs}
    errors = plugin_result.check_answers(out)
    if errors:
        raise TeamRefused("the answers file would fail the checker: " + "; ".join(errors))
    return out


# -- the cards code makes -----------------------------------------------------------------------------

def _next_code_key(cards: dict) -> str:
    return f"code:{max((int(mt.group(1)) for k in cards if (mt := _CODE_KEY.match(k))), default=0) + 1}"


def _code_card(made_by: str, header: str, question: str, options: list, subject: dict, rnd: int = 1) -> dict:
    return {"brief": None, "id": None, "made_by": made_by, "round": rnd, "blocks": "now", "hard_to_undo": False,
            "header": header, "question": question,
            "options": [{"label": label, "description": text} for label, text in options],
            "answer": None, "free_text": [], "passed": [], "last_ask": False, "held": False, "subject": subject}


def _newest_coach_run(runs: list, command: str):
    """The newest ended run of `command` with a run_id and a result file, or None."""
    found = [(r.get("finished_at") or "", i, r) for i, r in enumerate(runs) if r.get("command") == command
             and r.get("state") == "ended" and r.get("run_id") and r.get("result_file")]
    return max(found, key=lambda x: (x[0], x[1]))[2] if found else None


def _rerun_cards(case: Path, m, cards: dict, named: list) -> list:
    """Make one rerun card per map command the plans merged now name that has an ended run with a run_id and
    a file and no open run; returns the new keys. A plan naming a command whose rerun card is open joins it."""
    if not named:
        return []
    runs = team_files.load_runs(case)
    known = plugin_map.commands(m)
    made = []
    for nnn, rnd, commands in named:
        for command in dict.fromkeys(commands):
            if command not in known or any(r.get("command") == command and r.get("state") == "open" for r in runs):
                continue  # one open run per command: a plan joins it, and no card asks
            earlier = _newest_coach_run(runs, command)
            if earlier is None:
                continue
            key = next((k for k, c in cards.items() if c.get("made_by") == "rerun" and c.get("answer") is None
                        and c.get("subject", {}).get("command") == command), None)
            if key is not None:
                subject = dict(cards[key]["subject"])
                subject["briefs"] = sorted(set(subject.get("briefs", [])) | {nnn})
                cards[key] = dict(cards[key], subject=subject)
                continue
            key = _next_code_key(cards)
            date = (earlier.get("finished_at") or "")[:10]
            cards[key] = _code_card(
                "rerun", RERUN_HEADER, RERUN_QUESTION.format(command=command, date=date),
                [(RUN_AGAIN, f"Run {command} again. It takes time, and the case uses the new result once it ends."),
                 (USE_EARLIER, f"Do not run {command} again. The case keeps the result from {date}.")],
                {"command": command, "run": earlier["key"], "briefs": [nnn]}, rnd)
            made.append(key)
    return made


def _add_code_card(case: Path, card: dict) -> str:
    """Write one call that adds `card` and changes nothing else; returns its key."""
    record = _latest_record(case)
    cards = {k: dict(v) for k, v in record.get("cards", {}).items()}
    previous = latest_answers(case)
    nnn = _next_call(case)
    key = _next_code_key(cards)
    cards[key] = card
    (case / paths.TEAM_DIR).mkdir(exist_ok=True)
    _write_call(case, nnn, list(record.get("merged", [])), cards, previous, list(record.get("capped", [])))
    return key


def _open_code_card(case: Path, made_by: str, name: str, value) -> str | None:
    return next((k for k, c in latest_cards(case).items() if c.get("made_by") == made_by and c.get("answer") is None
                 and c.get("subject", {}).get(name) == value), None)


def case_card(case_dir, result_file) -> str:
    """Make a case card for `result_file`, a plugin result with no `run.case` inside the git root; returns
    its key. Refused for a file outside the git root (symlinks and `..` resolved), one that fails the
    checker, or one that names its case."""
    case = Path(case_dir).resolve()
    root = team_files.repo_root(case)
    given = Path(result_file)
    rel = team_files.inside_root(root, given if given.is_absolute() else root / given)  # as team_reply reads it
    if rel is None:
        raise TeamRefused(f"{result_file} is outside the git root {root}")
    path = root / rel
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise TeamRefused(f"{rel} cannot be read as a result file") from None
    problems = list(plugin_result.check_result(doc)) + list(plugin_result.check_result_file(path))
    if problems:
        raise TeamRefused(f"{rel} fails the checker: " + "; ".join(problems))
    run = doc["run"]
    if "case" in run:
        raise TeamRefused(f"{rel} names its case in run.case ({run['case']!r}); a case card is for a file with "
                          "no run.case")
    found = _open_code_card(case, "case", "result_file", rel)
    if found is not None:
        return found
    return _add_code_card(case, _code_card(
        "case", CASE_HEADER,
        CASE_QUESTION.format(plugin=doc["command"].split(":", 1)[0], date=run["finished_at"][:10], file=rel),
        [(USE_FOR_CASE, "Use the result as evidence for this case. It is the run to use."),
         (NOT_FOR_CASE, "Do not use the result for this case. The case leaves this file out.")],
        {"result_file": rel, "command": doc["command"], "finished_at": run["finished_at"]}))


def gap_card(case_dir, item) -> str:
    """Make a gap card for the map item `item`; returns its key."""
    case = Path(case_dir).resolve()
    if item not in plugin_map.load().get("items", {}):
        raise TeamRefused(f"{item} is not an item of the plugin map")
    found = _open_code_card(case, "gap", "item", item)
    if found is not None:
        return found
    try:  # the person reads the title, never the item ID
        title = rubric.item(rubric.load_rubric(case / paths.RUBRIC_COPY), item)["title"]
    except rubric.RubricError as exc:
        raise TeamRefused(f"cannot read the title of {item} from the rubric copy of the case: {exc}") from None
    return _add_code_card(case, _code_card(
        "gap", GAP_HEADER, GAP_QUESTION.format(item=title),
        [(GO_ON, f"Go on with the work that needs {title}, without its result."),
         (WAIT, f"Wait until {title} has a result.")],
        {"item": item}))


# -- the second plan round and the after-cap rule (spec §5.0 step 3, §5.6) ------------------------------

def _plan_list(case: Path) -> list:
    return [b for b in _plan_briefs(case) if b.reply_kind == "plan"]


def _set_of(plan_list: list, brief) -> list:
    """The plan briefs of `brief`'s item set, in order: every plan brief naming its first item (item sets are
    kept whole, spec §5.0 step 1)."""
    first = brief.items[0] if brief.items else None
    return [b for b in plan_list if first in b.items]


def _brief(plan_list: list, nnn):
    return next((b for b in plan_list if b.nnn == nnn), None)


def _now_cards(cards: dict, nnn: int) -> list:
    return [c for c in cards.values() if c.get("made_by") == "plan" and c.get("brief") == nnn
            and c.get("blocks") == "now"]


def needs_round_2(case_dir, plan) -> bool:
    """Whether merged plan brief `plan`, of plan round 1, needs a second plan round: one of its own `blocks:
    now` cards is open, or the person answered a card its plan lists in `follow_up` (spec §5.0 step 3)."""
    case = Path(case_dir).resolve()
    plan_list = _plan_list(case)
    brief = _brief(plan_list, plan)
    if brief is None or plan not in latest_merged(case) or _round(plan_list, brief) >= MAX_PLAN_ROUNDS:
        return False
    cards = latest_cards(case)
    if any(c.get("answer") is None for c in _now_cards(cards, plan)):
        return True
    follow_up = (_checked_plan(case, plan) or {}).get("follow_up", [])
    return any(cards.get(f"{plan:03d}:{cid}", {}).get("answer") is not None for cid in follow_up)


def _capped(cards: dict, merged: list, brief) -> bool:
    """Whether merged round-2 plan `brief` is ready for the after-cap rule: the coach has passed an answer for
    every one of its `blocks: now` cards."""
    return brief.nnn in merged and all(c.get("passed") for c in _now_cards(cards, brief.nnn))


def _cap_done(case: Path, brief) -> bool:
    """Whether the after-cap rule has run for round-2 plan `brief`: the card record's `capped` lists it."""
    return brief.nnn in _latest_record(case).get("capped", [])


def round_2_open(case_dir, plan) -> bool:
    """Whether the second plan round of merged round-1 plan brief `plan`'s item set is still to come: no second
    plan brief yet, or one that is open, or answered and not merged, or merged and not yet capped. A second
    plan brief cancelled or expired before it was merged yields no plan, and ends it (spec §5.6)."""
    case = Path(case_dir).resolve()
    plan_list = _plan_list(case)
    brief = _brief(plan_list, plan)
    merged = latest_merged(case)
    if brief is None or plan not in merged or _round(plan_list, brief) >= MAX_PLAN_ROUNDS:
        return False
    later = [b for b in _set_of(plan_list, brief) if b.nnn > plan]
    if not later:
        return True
    if later[0].nnn in merged:
        return not _cap_done(case, later[0])
    return team_files.state_of(case, later[0]) not in ("cancelled", "expired")


def uncapped_round_2(case_dir, plan) -> bool:
    """Whether `plan` is a merged second-brief plan whose cards the coach has not all been passed an answer
    for yet: the after-cap rule has not applied, so its cards go through step 2 before any command runs."""
    case = Path(case_dir).resolve()
    plan_list = _plan_list(case)
    brief = _brief(plan_list, plan)
    merged = latest_merged(case)
    return brief is not None and plan in merged and _round(plan_list, brief) >= MAX_PLAN_ROUNDS \
        and not _cap_done(case, brief)


def round_2_due(case_dir, plan) -> bool:
    """Whether merged plan brief `plan` waits for its item set's second plan round: a round-1 plan that
    `needs_round_2` while that round is still to come (`round_2_open`), or a second-brief plan not yet
    capped (`uncapped_round_2`). Its commands get no block (`team_runs.held_commands`), and its item set
    gets no results brief (`team_brief.select`), until then (spec §5.0 step 3)."""
    return (needs_round_2(case_dir, plan) and round_2_open(case_dir, plan)) or uncapped_round_2(case_dir, plan)


def round_2_step(case_dir, plan):
    """What the second plan round of merged plan brief `plan`'s item set waits for, when `round_2_due`:
    ("unwritten", None, []) no second plan brief yet; ("unanswered", NNN, []) it has no merged reply;
    ("cards", NNN, keys) its `blocks: now` cards not yet passed; ("cap", NNN, keys) every card passed, and the
    after-cap rule not yet run (a call stopped after `record_call`), keys being the set's open `blocks: now`
    cards. None when it waits for nothing."""
    case = Path(case_dir).resolve()
    if not round_2_due(case, plan):
        return None
    plan_list = _plan_list(case)
    brief = _brief(plan_list, plan)
    members = _set_of(plan_list, brief)
    second = next((b for b in members if _round(plan_list, b) == MAX_PLAN_ROUNDS), None)
    if second is None:
        return ("unwritten", None, [])
    if second.nnn not in latest_merged(case):
        return ("unanswered", second.nnn, [])
    cards = latest_cards(case)
    keys = [k for k, c in cards.items() if c.get("made_by") == "plan" and c.get("brief") == second.nnn
            and c.get("blocks") == "now" and not c.get("passed")]
    if keys:
        return ("cards", second.nnn, keys)
    nnns = {b.nnn for b in members}
    return ("cap", second.nnn, [k for k, c in cards.items() if c.get("made_by") == "plan" and c.get("brief") in nnns
                                and c.get("blocks") == "now" and c.get("answer") is None])


def _set_cards(cards: dict, set_briefs: list, items: list) -> list:
    """The keys of the cards of one item set: each card of its own plan briefs, and each card code made whose
    subject names one of its items or briefs. Never a card reached through a command: two item sets may
    name the same command, and one set's cap leaves the other's cards as they are (spec §5.6)."""
    out = []
    for key, card in cards.items():
        subject = card.get("subject") or {}
        if card.get("brief") is not None:
            if card.get("brief") in set_briefs:
                out.append(key)
        elif subject.get("item") in items or set(subject.get("briefs", [])) & set(set_briefs):
            out.append(key)
    return out


def _cap(cards: dict, keys: list, blocks: str) -> tuple:
    """Apply the after-cap rule to the open `blocks` cards among `keys`: a plan card with no free text and no
    `hard_to_undo` takes its recommended option; a `hard_to_undo` one gets its last ask; a held card, a card
    with free text, and every card code made stay as they are. Returns (keys settled, picks)."""
    settled, picks = [], {}
    for key in keys:
        card = cards[key]
        if card.get("answer") is not None or card.get("blocks") != blocks or card.get("made_by") != "plan" \
                or card.get("free_text") or card.get("held"):
            continue
        if card.get("hard_to_undo"):
            card["last_ask"] = True
            continue
        chosen = next((o for o in card.get("options", []) if o.get("label", "").endswith(RECOMMENDED)), None)
        if chosen is None:
            continue
        card["answer"] = {"label": chosen["label"], "settled_by": "recommended"}
        settled.append(key)
        for command, inputs in chosen.get("sets", {}).items():
            for name, value in inputs.items():
                picks.setdefault((command, name), []).append((key, value, card["round"], "recommended"))
    return settled, picks


def apply_after_cap(case_dir, m, call) -> list:
    """Apply the after-cap rule (spec §5.6) for each item set whose second-brief plan is capped (the coach has
    passed an answer for every one of its `blocks: now` cards, or it has none) and that the record's `capped`
    list does not yet name. So the rule applies once, in the call that caps the plan, or in the next call
    when a call stopped after `record_call`. It applies to the open `blocks: now` cards of that plan and of
    the set's first plan, and to no other card. Rewrites the files of `call`, the newest call; returns the
    keys it settled."""
    case = Path(case_dir).resolve()
    record = _latest_record(case)
    if record.get("call") != call.nnn:
        raise TeamRefused(f"call {call.nnn:03d} is not the newest coach call; the after-cap rule applies only "
                          "right after it")
    cards = {k: dict(v) for k, v in record.get("cards", {}).items()}
    merged = list(record.get("merged", []))
    capped = list(record.get("capped", []))
    plan_list = _plan_list(case)
    settled, picks = [], {}
    for brief in plan_list:
        if brief.nnn in capped or _round(plan_list, brief) < MAX_PLAN_ROUNDS \
                or not _capped(cards, merged, brief):
            continue
        capped.append(brief.nnn)
        set_briefs = [b.nnn for b in _set_of(plan_list, brief)]
        done, more = _cap(cards, _set_cards(cards, set_briefs, brief.items), "now")
        settled += done
        for pick, found in more.items():
            picks.setdefault(pick, []).extend(found)
    if capped == list(record.get("capped", [])):
        return []
    out = _fold(m, cards, latest_answers(case), picks, _plan_items(_plan_briefs(case), cards), [])
    _write_call(case, call.nnn, merged, cards, out, capped, replace=True)
    return [key for key in cards if key in settled]


def apply_after_cap_later(case_dir, m, plans) -> list:
    """Apply the after-cap rule to the open `blocks: later` cards of the plan briefs `plans`, one item set's,
    as `team-brief` writes that set's results brief (spec §5.6); a changed card record is written as a new call.
    Returns the keys of the set's cards whose last ask is due: the results brief waits for them."""
    case = Path(case_dir).resolve()
    record = _latest_record(case)
    cards = {k: dict(v) for k, v in record.get("cards", {}).items()}
    plans = sorted(plans)
    _cap(cards, [key for key, card in cards.items() if card.get("brief") in plans], "later")
    if cards != record.get("cards", {}):
        nnn = _next_call(case)
        _write_call(case, nnn, list(record.get("merged", [])), cards, latest_answers(case),
                    list(record.get("capped", [])))
    return [key for key, card in cards.items() if card.get("brief") in plans and card.get("answer") is None
            and card.get("last_ask")]


def held_cards(case_dir) -> list:
    """The keys of the open cards code never fills (spec §5.6): a conflict card, a plan card with free text,
    and a `hard_to_undo` card skipped or answered in free text on its last ask. Record order."""
    return [key for key, card in latest_cards(case_dir).items() if card.get("answer") is None and (
        card.get("made_by") == "conflict" or (card.get("made_by") == "plan"
                                              and (card.get("free_text") or card.get("held"))))]


def last_ask_cards(case_dir) -> list:
    """The keys of the open `hard_to_undo` cards whose one extra ask after the cap is due. Record order."""
    return [key for key, card in latest_cards(case_dir).items() if card.get("answer") is None and card.get("last_ask")]
