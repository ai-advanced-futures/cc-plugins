"""The financial figures file (figures.jsonl): every figure the finances use, checked when recorded.

Spec §4; rulings P3-05, P3-06, P3-07, P3-14. The file is append-only and hash-chained (chained_log).
A `figure` line records one FIG-NNN; a `confirm` line records the proposer's answer. Status is never
stored: readers replay the lines in file order and re-apply check 1, checks 7 to 10, the session
rules and the supersede rules to each line against the state before it. A line that fails one is
ignored with a named reason (ignored_lines). Checks 2 to 6 read today's case files, check 9 the
live figures, and checks 11 and 12 the figure and the figure it supersedes; checks 11 and 12 run when a
figure is recorded and are never replayed (0.4.0: no older line stops counting). `recheck` re-applies
checks 2 to 6, 9, 11 and 12. Every refusal is FigureRefused; a check's refusal starts `check {n}: `, a
session, supersede or confirm refusal starts `figure: `.
"""
from __future__ import annotations

import decimal
import re
from decimal import Decimal
from pathlib import Path

from lib import amounts, basis, case_doc, case_files, chained_log, clock, paths, register
from lib import evidence as evidence_pages

KINDS = ("revenue", "cost", "cannibalisation", "terminal_value", "booking", "ask", "excluded")
CASH_KINDS = frozenset({"revenue", "cost", "cannibalisation"})
NPV_KINDS = CASH_KINDS | {"terminal_value"}
INFLOW_KINDS = frozenset({"revenue", "terminal_value"})
OUTFLOW_KINDS = frozenset({"cost", "cannibalisation"})
GRID_KINDS = NPV_KINDS | {"booking"}
NON_CASH_KINDS = frozenset({"booking", "ask", "excluded"})
STREAMS = ("new", "expansion")
WRITTEN_AS = ("total", "per_month", "per_quarter", "per_year")
_RATE_MONTHS = {"per_month": 1, "per_quarter": 3, "per_year": 12}  # months a written rate covers
_RATE_WORDS = {"per_month": "a month", "per_quarter": "a quarter", "per_year": "a year"}
SOURCES = ("extractor", "coach", "person")
STATUSES = ("stated", "confirmed", "superseded")
BASE = "base"
TERMINAL_ITEM = "BC-PAYBACK-CASH"
FORECAST_ITEM = "BC-FORECAST-Y1"
RUN_RATE_REASON = "a rate at a point in time, not a cash flow"  # the extractor writes it byte for byte
RUN_RATE_ITEM = "BC-ASSUMPTIONS"

PROPOSAL_KEYS = (("line", "kind", "amount", "written_as", "currency", "scenario", "item_id", "quote", "evidence",
                  "source"),
                 ("stream", "months", "replaces", "parts", "restates", "reason", "supersedes"))
_REQUIRED, _OPTIONAL = PROPOSAL_KEYS

_FIG_ID = re.compile(r"^FIG-([0-9]{3,})$")
_EV_ID = re.compile(r"^EV-[0-9]{3,}$")
# A decimal string: no sign, no thousands separator, no exponent; digit caps keep it exact (basis.CONTEXT).
_AMOUNT = re.compile(r"[0-9]{1,15}(?:\.[0-9]{1,12})?")
_CENT = Decimal("0.01")
_FIGURE_FIELDS = frozenset({"record", "id", *_REQUIRED, *_OPTIONAL, "recorded_by", "date", "prev"})
_CONFIRM_FIELDS = frozenset({"record", "ref", "question", "answer", "role", "name", "date", "prev"})
_QUOTE_FIELDS = frozenset({"section", "sentence", "position"})


class FigureRefused(ValueError):
    """A figure or a confirmation the rules refuse, or a figures file that cannot be read."""


class FiguresFileRefused(FigureRefused):
    """figures.jsonl itself cannot be read or written: a fault in the file, not in a proposal."""


class _Check(Exception):
    """One failed check: (number or "figure", message)."""


def _fail(check, message: str):
    raise _Check(f"check {check}: {message}" if isinstance(check, int) else f"figure: {message}")


def _blank(value) -> bool:
    return not isinstance(value, str) or value.strip() == ""


def _fold(text: str) -> str:
    return " ".join(text.split()).casefold()


def _int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def scenario_key(name: str) -> str:
    """The scenario name case-folded, with every character that is not a letter or a digit dropped."""
    return "".join(c for c in name.casefold() if c.isalnum())


def _number(fig_id: str) -> int:
    return int(_FIG_ID.fullmatch(fig_id).group(1))


# ---- check 1: the figure's own fields ---------------------------------------------------------------

def _quote_problem(quote, what: str) -> str | None:
    if (not isinstance(quote, dict) or set(quote) != _QUOTE_FIELDS or _blank(quote["section"])
            or not isinstance(quote["sentence"], str) or quote["sentence"].strip() == ""
            or not (quote["position"] is None or (_int(quote["position"]) and quote["position"] >= 0))):
        return (f"{what} is {{\"section\", \"sentence\", \"position\"}}: a section key, a non-blank sentence "
                "and a whole number from 0, or null")
    return None


def _id_list_problem(value, name: str) -> str | None:
    if not isinstance(value, list) or not all(isinstance(i, str) for i in value) or len(set(value)) != len(value):
        return f"{name} is a list of distinct FIG-NNN IDs"
    return None


def _check_1(rec: dict) -> None:
    """Spec §4 field and kinds tables: amount, kind, stream, written_as, months, quote, parts, the
    excluded figure's reason, restates only on an excluded figure, the item of a booking and of a
    terminal value."""
    if _blank(rec["line"]):
        _fail(1, "the line (the figure's short name) must not be blank")
    if rec["kind"] not in KINDS:
        _fail(1, f"the kind {rec['kind']!r} is not one of {', '.join(KINDS)}")
    if not isinstance(rec["amount"], str) or not _AMOUNT.fullmatch(rec["amount"]):
        _fail(1, f"the amount {rec['amount']!r} is not a decimal string with no sign and no thousands separator "
                 "(write 1200000, not 1,200,000 or -5); the kind gives the direction")
    kind = rec["kind"]
    if kind in ("revenue", "booking"):
        if rec["stream"] not in STREAMS:
            _fail(1, f"a {kind} figure names its stream, one of {', '.join(STREAMS)}")
    elif rec["stream"] is not None:
        _fail(1, f"a {kind} figure has no stream; only revenue and booking do")
    if rec["written_as"] not in WRITTEN_AS:
        _fail(1, f"written_as {rec['written_as']!r} is not one of {', '.join(WRITTEN_AS)}")
    months = rec["months"]
    if months is not None and (not isinstance(months, dict) or set(months) != {"from", "to"}
                               or not all(_int(months[k]) and months[k] >= 1 for k in ("from", "to"))):
        _fail(1, "months is {\"from\": M, \"to\": M}, whole month numbers from 1, or null")
    if months is None and rec["written_as"] != "total":
        _fail(1, f"a figure written {rec['written_as']} needs its months; with no months it is written total")
    if _blank(rec["currency"]) or _blank(rec["scenario"]) or _blank(rec["item_id"]):
        _fail(1, "the currency, the scenario and the item ID must not be blank")
    if rec["evidence"] is None:  # proposed with no page (ruling, Task 19): the person sees why
        _fail(6, f"no evidence page lists {rec['item_id']}, or none that lists it states this amount or its basis; "
                 "record a page that does, then propose the figure again")
    if not isinstance(rec["evidence"], str) or not _EV_ID.fullmatch(rec["evidence"]):
        _fail(1, f"the evidence {rec['evidence']!r} is not an evidence page ID (EV-001 and up)")
    if rec["source"] not in SOURCES:
        _fail(1, f"the source {rec['source']!r} is not one of {', '.join(SOURCES)}")
    problem = _quote_problem(rec["quote"], "the quote")
    if problem:
        _fail(1, problem)
    parts = rec["parts"]
    if parts is not None:
        if not isinstance(parts, list) or not parts:
            _fail(1, "parts is a non-empty list of {\"quote\", \"amount\"}, or null")
        for n, part in enumerate(parts, 1):
            if not isinstance(part, dict) or set(part) != {"quote", "amount"}:
                _fail(1, f"part {n} is {{\"quote\", \"amount\"}}")
            problem = _quote_problem(part["quote"], f"part {n}'s quote")
            if problem:
                _fail(1, problem)
            if part["quote"]["position"] is None:
                _fail(1, f"part {n}'s quote names the position of its amount")
            if not isinstance(part["amount"], str) or not _AMOUNT.fullmatch(part["amount"]):
                _fail(1, f"part {n}'s amount {part['amount']!r} is not a decimal string with no sign")
    problem = _id_list_problem(rec["replaces"], "replaces")
    if problem:
        _fail(1, problem)
    if kind == "excluded":
        if _blank(rec["reason"]):
            _fail(1, "an excluded figure needs a reason, not blank")
        if rec["restates"] is not None:
            problem = _id_list_problem(rec["restates"], "restates") or (
                None if rec["restates"] else "restates names at least one figure, or is null")
            if problem:
                _fail(1, problem)
    elif rec["restates"] is not None:
        _fail(1, f"restates is only for an excluded figure, not a {kind} figure")
    if kind == "booking" and rec["item_id"] != FORECAST_ITEM:
        _fail(1, f"a booking feeds {FORECAST_ITEM} only, not {rec['item_id']}")
    if kind == "terminal_value" and rec["item_id"] != TERMINAL_ITEM:
        _fail(1, f"a terminal value feeds {TERMINAL_ITEM} only, not {rec['item_id']}")


# ---- the session and supersede rules --------------------------------------------------------------

def _check_session(rec: dict, automated: bool) -> None:
    """Ruling P3-06: `person` and `coach` need a named person; an automated session records only
    `extractor`."""
    if automated and rec["source"] != "extractor":
        _fail("figure", f"an automated session may not record source {rec['source']}: no person is present; "
                        "an automated session records only source extractor")


def _check_supersede(rec: dict, state: "_State", automated: bool) -> None:
    """register._check_supersede's rules: a supersede needs a reason; it names a recorded, live
    figure; an automated session never supersedes a confirmed figure. Its change source is the
    superseding figure's own `source`, which check 1 already requires (there is no change_source
    key). A reason with no supersede belongs only to an excluded figure."""
    if rec["supersedes"] is None:
        if rec["reason"] is not None and rec["kind"] != "excluded":
            _fail("figure", "a reason is given only with supersedes, or on an excluded figure")
        return
    try:
        register._check_supersede(rec["supersedes"], rec["reason"], rec["source"],
                                  categories=dict.fromkeys(state.figures), superseded_by=state.superseded_by,
                                  confirmed=state.confirmed, category=None, automated=automated,
                                  refused=FigureRefused)
    except FigureRefused as exc:
        _fail("figure", str(exc))


# ---- checks 2 to 6: today's case files ---------------------------------------------------------

def occurrences(fig: dict) -> list:
    """(section, sentence, position) of the quote and of each part; a quote with no position is none."""
    quotes = [fig["quote"]] + [part["quote"] for part in (fig.get("parts") or [])]
    return [(q["section"], q["sentence"], q["position"]) for q in quotes if q["position"] is not None]


def _written_at(sections: dict, quote: dict, currency: str):
    """The value written at the quote's position: the money scan's reading where it found an amount
    there (a table cell takes its header's scale), else the written form there; None when neither
    reads one. An unreadable amount is None."""
    section, sentence, position = quote["section"], quote["sentence"], quote["position"]
    for m in amounts.money_amounts({section: sections[section]}, currency):
        if m.sentence == sentence and m.position == position:
            return m.value
    w = amounts.amount_at(sentence, position, currency)
    return None if w is None else w.value


def _check_2(rec: dict, case_basis) -> None:
    if case_basis.currency is None:
        _fail(2, "the case states no currency the code can read; fill in the Currency line first")
    if rec["currency"] != case_basis.currency:
        _fail(2, f"the currency {rec['currency']} is not the case's currency, {case_basis.currency}")


def _check_3(rec: dict, case_basis) -> None:
    """Spec §4 check 3 binds the grid kinds only; an ask or an excluded figure may sit off the grid.
    The one predicate for record time and recheck."""
    if rec["kind"] not in GRID_KINDS:
        return
    months = rec["months"]
    if months is None:
        _fail(3, f"a {rec['kind']} figure needs its months on the case's month grid")
    if case_basis.horizon is None:
        _fail(3, "the case states no horizon the code can read; fill in the Horizon line first")
    horizon = case_basis.horizon
    if months["from"] > months["to"]:
        _fail(3, f"months run from {months['from']} to {months['to']}: from must not be after to")
    if months["to"] > horizon:
        _fail(3, f"month {months['to']} is outside the horizon of {horizon} months")
    if rec["kind"] == "terminal_value" and not months["from"] == months["to"] == horizon:
        _fail(3, f"a terminal value sits in the last horizon month: months from {horizon} to {horizon}")


def _check_4(rec: dict, sections: dict) -> None:
    for n, quote in enumerate([rec["quote"]] + [p["quote"] for p in (rec["parts"] or [])]):
        what = "the quote" if n == 0 else f"part {n}'s quote"
        if quote["section"] not in sections:
            _fail(4, f"{what} names section {quote['section']!r}, which the case does not have")
        if quote["sentence"] not in amounts.sentences(sections[quote["section"]]):
            _fail(4, f"{what} is not one whole sentence or table row of section {quote['section']} "
                     f"as the case reads today: {quote['sentence']!r}")


def _names(sentence: str, name: str) -> bool:
    """`name` appears in `sentence` as a whole word or words, ignoring letter case and spacing."""
    words = _fold(name)
    return bool(words) and re.search(rf"(?<!\w){re.escape(words)}(?!\w)", _fold(sentence)) is not None


def _check_5(rec: dict, sections: dict, currency: str, live: dict) -> None:
    amount = Decimal(rec["amount"])
    quote, parts = rec["quote"], rec["parts"]
    if amount == 0 and rec["replaces"] and quote["position"] is None and not parts:
        # No zero is written as an amount (a written $0 is matched below like any amount): the
        # sentence names the scenario or a replaced line, and the person's confirmation is the guard.
        zeros = [m for m in amounts.money_amounts({quote["section"]: sections[quote["section"]]}, currency)
                 if m.sentence == quote["sentence"] and m.value == 0]
        if zeros:  # re-review N2: the null form would leave that zero uncovered for good
            _fail(5, f"the sentence writes a zero amount, {zeros[0].written}, at position {zeros[0].position}: "
                     "a figure whose amount is 0 gives that position")
        names = [rec["scenario"]] + [live[i]["line"] for i in rec["replaces"] if i in live]
        if not any(_names(quote["sentence"], name) for name in names):
            _fail(5, f"a replacing figure whose amount is 0 and whose quote gives no position quotes a sentence "
                     f"that names its scenario ({rec['scenario']}) or a line it replaces, as a whole word")
        return
    if parts:
        written = Decimal(0)
        for n, part in enumerate(parts, 1):
            value = _written_at(sections, part["quote"], currency)
            if value is None or value != Decimal(part["amount"]):
                _fail(5, f"part {n}'s amount {part['amount']} is not the amount written at position "
                         f"{part['quote']['position']} of its sentence")
            written += value
        if quote["position"] is not None and (quote["section"], quote["sentence"], quote["position"]) not in [
                (p["quote"]["section"], p["quote"]["sentence"], p["quote"]["position"]) for p in parts]:
            _fail(5, "the quote of a figure built from parts has no position, or the position of one part")
    else:
        if quote["position"] is None:
            _fail(5, "the quote names no position; give the position of the amount in the sentence")
        written = _written_at(sections, quote, currency)
        if written is None:
            _fail(5, f"no amount the code can read is written at position {quote['position']} of the sentence "
                     f"(a number is matched whole: 12 is never read inside 2012)")
    months = rec["months"]
    with decimal.localcontext(basis.CONTEXT):
        if rec["written_as"] == "total":
            expected, how = written, "the written amount"
        else:
            n = months["to"] - months["from"] + 1
            per = written * n / _RATE_MONTHS[rec["written_as"]]
            expected = per.quantize(_CENT, rounding=decimal.ROUND_HALF_EVEN)
            how = (f"the written amount {written} {_RATE_WORDS[rec['written_as']]} over {n} months, to the cent")
        if amount != expected:
            _fail(5, f"the amount {rec['amount']} is not {how}: {expected}")


def _check_6(case_dir: Path, rec: dict, applicable: list) -> None:
    if rec["item_id"] not in applicable:
        _fail(6, f"the item {rec['item_id']} does not apply to this case's scope")
    try:
        page = evidence_pages.read_page(case_dir, rec["evidence"])
    except evidence_pages.EvidenceRefused as exc:
        _fail(6, str(exc))
    if rec["item_id"] not in page["item_ids"]:
        _fail(6, f"evidence page {rec['evidence']} does not list {rec['item_id']}")


# ---- checks 7 to 10: the other figures ------------------------------------------------------------

def _check_7(rec: dict, live: dict) -> None:
    """An occurrence holds at most one live cash figure and at most one live `ask` or `booking`; a
    live `excluded` figure holds its occurrence alone (final review I1: its amount is not a new cash
    flow, so no cash figure may sit on it). Here a cash figure is one that enters NPV (NPV_KINDS,
    spec §6: terminal_value for NPV only), so one amount never enters NPV twice."""
    cash = rec["kind"] in NPV_KINDS
    mine = set(occurrences(rec))
    for other in live.values():
        if other["id"] == rec["supersedes"]:
            continue
        if (other["kind"] in NPV_KINDS) != cash and "excluded" not in (rec["kind"], other["kind"]):
            continue
        shared = mine & set(occurrences(other))
        if shared:
            _, sentence, position = sorted(shared)[0]
            what = ("an amount to leave out" if other["kind"] == "excluded"
                    else "a cash figure" if other["kind"] in NPV_KINDS else "a figure that is not cash")
            _fail(7, f"{other['id']} already quotes the amount at position {position} of {sentence!r} as {what}")


def _overlap(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return a["from"] <= b["to"] and b["from"] <= a["to"]


def _check_8(rec: dict, live: dict) -> None:
    for other in live.values():
        if other["id"] == rec["supersedes"] or other["scenario"] != rec["scenario"]:
            continue
        if _fold(other["line"]) == _fold(rec["line"]) and _overlap(other["months"], rec["months"]):
            _fail(8, f"{other['id']} in scenario {rec['scenario']} has the same line, {other['line']!r}, "
                     "over months that overlap")
    if rec["kind"] == "terminal_value":
        held = [o["id"] for o in live.values() if o["kind"] == "terminal_value" and o["id"] != rec["supersedes"]
                and (o["scenario"] == rec["scenario"]
                     or (o["scenario"] == BASE and rec["scenario"] != BASE and o["id"] not in rec["replaces"]))]
        if held:
            _fail(8, f"scenario {rec['scenario']} already has a terminal value, {held[0]}; a scenario has at "
                     "most one, and a scenario's own terminal value replaces the base one")
        target = live.get(rec["supersedes"]) if rec["supersedes"] is not None else None
        correction = target is not None and target["kind"] == "terminal_value" and target["scenario"] == BASE
        if rec["scenario"] == BASE and not correction:  # a supersede of the base one is a correction (ruling)
            own = [o for o in live.values() if o["kind"] == "terminal_value" and o["scenario"] != BASE
                   and o["id"] != rec["supersedes"]]
            if own:
                _fail(8, f"scenario {own[0]['scenario']} has its own terminal value, {own[0]['id']}, and would "
                         "inherit this base one too; record the base terminal value first, or supersede "
                         f"{own[0]['id']}")


def _check_9(rec: dict, live: dict) -> None:
    if rec["replaces"] and rec["scenario"] == BASE:
        _fail(9, "a base figure replaces nothing; only a scenario figure replaces base figures")
    for fig_id in rec["replaces"]:
        other = live.get(fig_id)
        if other is None or other["scenario"] != BASE:
            _fail(9, f"replaces names {fig_id}, which is not a live base figure")
    if rec["restates"]:
        total = Decimal(0)
        for fig_id in rec["restates"]:
            other = live.get(fig_id)
            if other is None:
                _fail(9, f"restates names {fig_id}, which is not a live figure")
            if other["kind"] not in CASH_KINDS | {"booking"}:
                why = ("a terminal value is a valuation" if other["kind"] == "terminal_value"
                       else f"{'an' if other['kind'][0] in 'aeiou' else 'a'} {other['kind']} figure is not a cash flow")
                _fail(9, f"restates names {fig_id}: a restatement sums cash flows; {why}. It names only revenue, "
                         "cost, cannibalisation and booking figures")
            if other["scenario"] != rec["scenario"]:
                _fail(9, f"restates names {fig_id} of scenario {other['scenario']}, not {rec['scenario']}")
            with decimal.localcontext(basis.CONTEXT):
                total += Decimal(other["amount"])
        if total != Decimal(rec["amount"]):
            _fail(9, f"the restated figures sum to {total}, not {rec['amount']}")


def _check_10(rec: dict, scenarios: set) -> None:
    key = scenario_key(rec["scenario"])
    if not key:
        _fail(10, f"the scenario {rec['scenario']!r} has no letter or digit")
    for name in sorted(scenarios | {BASE}):
        if name != rec["scenario"] and scenario_key(name) == key:
            _fail(10, f"the scenario {rec['scenario']!r} differs from {name!r} only in letter case, spacing "
                      f"or punctuation; write {name!r}")


# ---- checks 11 and 12: a run rate's shape, and a superseded total (record time and recheck only) ---

def is_run_rate(fig: dict, recorded: dict | None = None) -> bool:
    """An `excluded` figure whose reason is RUN_RATE_REASON exactly (a paraphrase is not a run rate),
    or an `excluded` figure on RUN_RATE_ITEM that supersedes a run rate: a correction keeps the status
    (final review I1). `recorded` maps every recorded figure, live or superseded, by ID; without it
    only the reason counts."""
    seen = set()
    while fig is not None and fig["kind"] == "excluded" and fig.get("id") not in seen:
        if fig.get("reason") == RUN_RATE_REASON:
            return True
        if fig.get("item_id") != RUN_RATE_ITEM or recorded is None:
            return False
        seen.add(fig.get("id"))
        fig = recorded.get(fig.get("supersedes"))
    return False


def is_judgment_exclusion(fig: dict, recorded: dict | None = None) -> bool:
    """An `excluded` figure with no `restates` that is not a run rate: leaving it out is a judgment,
    so the funder must approve it. A run rate and a restating total settle on confirmation alone."""
    return fig["kind"] == "excluded" and not fig.get("restates") and not is_run_rate(fig, recorded)


def _check_11(rec: dict, recorded: dict) -> None:
    """Spec 0.4.0 item 1: a run rate is on RUN_RATE_ITEM, written total, with no months and no
    restates. The first wrong part is named. `recorded` is as for is_run_rate."""
    if not is_run_rate(rec, recorded):
        return
    if rec["item_id"] != RUN_RATE_ITEM:
        _fail(11, f"a run rate is on {RUN_RATE_ITEM}, not {rec['item_id']}")
    if rec["written_as"] != "total":
        _fail(11, f"a run rate is written total, not {rec['written_as']}")
    if rec["months"] is not None:
        _fail(11, "a run rate has no months")
    if rec["restates"] is not None:
        _fail(11, "a run rate restates nothing")


def _and(ids: list) -> str:
    return ids[0] if len(ids) == 1 else f"{', '.join(ids[:-1])} and {ids[-1]}"


def _now(fig_id: str, superseded_by: dict) -> str:
    """The figure that now stands for `fig_id`: follow superseded_by to its end (seen-guard)."""
    seen = set()
    while fig_id in superseded_by and fig_id not in seen:
        seen.add(fig_id)
        fig_id = superseded_by[fig_id]
    return fig_id


def _check_12(rec: dict, recorded: dict, live: dict, superseded_by: dict) -> None:
    """Spec 0.4.0 item 3 (controller ruling, fix round 1): a figure that enters NPV is refused when
    the figures it supersedes, directly or through earlier supersedes, include an `excluded` figure
    with `restates` while any figure that one restates still counts (it would count twice). A
    restated figure still counts when the figure that now stands for it, through its corrections, is
    live and enters NPV (final review I2). `recorded` maps every figure the walk may meet, live or
    superseded, by ID; `superseded_by` maps each superseded figure to the one that superseded it."""
    if rec["kind"] not in NPV_KINDS:
        return
    seen, target = set(), recorded.get(rec["supersedes"])
    while target is not None and target["id"] not in seen:
        seen.add(target["id"])
        if target["kind"] == "excluded" and target.get("restates"):
            now = {i: _now(i, superseded_by) for i in target["restates"]}
            counted = [i for i, n in now.items()
                       if n in live and n != rec["id"] and live[n]["kind"] in NPV_KINDS]
            if counted:
                moved = [now[i] for i in counted]
                _fail(12, f"{_and(counted)}, which {target['id']} repeats, already "
                          f"{'counts' if len(counted) == 1 else 'count'} this amount"
                          f"{'' if moved == counted else ' as ' + _and(moved)}; correct those figures "
                          "instead of making the total a cost")
        target = recorded.get(target.get("supersedes"))


# ---- the derived state ----------------------------------------------------------------------------

class _State:
    """The file derived from its lines: counted figures, confirmations, supersedes, reasons."""

    def __init__(self) -> None:
        self.figures: dict = {}
        self.confirmed: dict = {}
        self.superseded_by: dict = {}
        self.ignored: list = []
        self.last_number = 0

    def live(self) -> dict:
        return {i: f for i, f in self.figures.items() if i not in self.superseded_by}

    def figure_problem(self, rec: dict, case=None) -> str | None:
        """Why the figure line does not count, or None. `case` (case_dir, basis, sections, applicable)
        adds checks 2 to 6, 11 and 12, for a figure being recorded; a reader passes none, so a line
        recorded before checks 11 and 12 existed still counts and only its re-check names them."""
        extra = sorted(set(rec) - _FIGURE_FIELDS)
        missing = sorted(_FIGURE_FIELDS - set(rec) - {"prev"})
        if extra or missing:
            parts = ([f"unknown field(s) {', '.join(extra)}"] if extra else []) + (
                [f"missing field(s) {', '.join(missing)}"] if missing else [])
            return "check 1: the line has " + " and ".join(parts)
        if not isinstance(rec["id"], str) or not _FIG_ID.fullmatch(rec["id"]) or rec["id"] in self.figures:
            return f"check 1: the figure ID {rec['id']!r} is not a new FIG-NNN"
        if _blank(rec["recorded_by"]) or _blank(rec["date"]):
            return "figure: recorded_by and date must not be blank"
        automated = register.is_automated(rec["recorded_by"])
        live = self.live()
        try:
            _check_1(rec)
            _check_session(rec, automated)
            _check_supersede(rec, self, automated)
            if case is not None:
                case_dir, case_basis, sections, applicable = case
                _check_2(rec, case_basis)
                _check_3(rec, case_basis)
                _check_4(rec, sections)
                _check_5(rec, sections, case_basis.currency, live)
                _check_6(case_dir, rec, applicable)
            _check_7(rec, live)
            _check_8(rec, live)
            _check_9(rec, live)
            _check_10(rec, {f["scenario"] for f in self.figures.values()})
            if case is not None:
                _check_11(rec, self.figures)
                _check_12(rec, self.figures, live, self.superseded_by)
        except _Check as exc:
            return str(exc)
        return None

    def confirm_problem(self, rec: dict) -> str | None:
        extra = sorted(set(rec) - _CONFIRM_FIELDS)
        missing = sorted(_CONFIRM_FIELDS - set(rec) - {"prev"})
        if extra or missing:
            return f"figure: the confirmation has the wrong fields ({', '.join(extra + missing)})"
        if _blank(rec["name"]) or _blank(rec["question"]) or _blank(rec["answer"]) or _blank(rec["date"]):
            return "figure: a confirmation's name, question, answer and date must not be blank"
        if register.is_automated(rec["name"]):
            return "figure: the confirmation names automated; only a named person confirms a figure"
        if rec["role"] != "proposer":
            return f"figure: the role {rec['role']!r} is not proposer; only the proposer confirms a figure"
        ref = rec["ref"]
        if not isinstance(ref, str) or ref not in self.figures:
            return f"figure: {ref!r} is not a recorded figure"
        if ref in self.superseded_by:
            return f"figure: {ref} is superseded by {self.superseded_by[ref]}; confirm {self.superseded_by[ref]} instead"
        if ref in self.confirmed:
            return f"figure: {ref} is already confirmed"
        return None

    def count(self, n: int, rec: dict) -> None:
        kind = rec.get("record")
        if kind == "figure":
            m = _FIG_ID.fullmatch(rec["id"]) if isinstance(rec.get("id"), str) else None
            if m:
                self.last_number = max(self.last_number, int(m.group(1)))
            problem = self.figure_problem(rec)
        elif kind == "confirm":
            problem = self.confirm_problem(rec)
        else:
            problem = f"figure: the record kind {kind!r} is not figure or confirm"
        if problem:
            self.ignored.append(f"{paths.FIGURES} line {n}: {problem}; the line does not count")
            return
        if kind == "figure":
            self.figures[rec["id"]] = rec
            if rec["supersedes"] is not None:
                self.superseded_by[rec["supersedes"]] = rec["id"]
        else:
            self.confirmed[rec["ref"]] = rec


def _derive(case_dir: Path, upto: int | None = None) -> _State:
    """The file's state from its lines, cut at `upto` bytes (None: the whole file)."""
    try:
        lines = chained_log.read(Path(case_dir) / paths.FIGURES, upto)
    except chained_log.LogRefused as exc:
        raise FiguresFileRefused(str(exc)) from exc
    state = _State()
    for n, rec in enumerate(lines, 1):
        state.count(n, rec)
    return state


def _append(case_dir: Path, build) -> dict:
    try:
        return chained_log.append(Path(case_dir) / paths.FIGURES, build)
    except chained_log.LogRefused as exc:
        raise FiguresFileRefused(str(exc)) from exc


def _case_today(case_dir: Path) -> tuple:
    """(case_dir, basis, sections, applicable item IDs) as the files read today."""
    try:
        text = (case_dir / paths.CASE_DOC).read_text(encoding="utf-8")
        sections = case_doc.parse_sections(text)
    except (OSError, UnicodeDecodeError, case_doc.CaseDocError) as exc:
        raise FigureRefused(f"check 4: cannot read {paths.CASE_DOC}: {exc}") from exc
    try:
        applicable = case_files.read_scope(case_dir)["applicable_item_ids"]
    except case_files.CaseRefused as exc:
        raise FigureRefused(f"check 6: {exc}") from exc
    return case_dir, basis.read_basis(case_dir), sections, applicable


def record_figure(case_dir, proposal: dict) -> dict:
    """Check a proposed figure and record it as the next FIG-NNN, `stated`. Returns the stored line.
    Needs a session. Refused, naming the check, when any check fails."""
    case_dir = Path(case_dir)
    if not isinstance(proposal, dict):
        raise FigureRefused("check 1: a proposal is a JSON object")
    extra = sorted(set(proposal) - set(_REQUIRED) - set(_OPTIONAL))
    missing = sorted(set(_REQUIRED) - set(proposal))
    if extra or missing:
        parts = ([f"unknown key(s) {', '.join(extra)}"] if extra else []) + (
            [f"missing key(s) {', '.join(missing)}"] if missing else [])
        raise FigureRefused("check 1: the proposal has " + " and ".join(parts))
    try:
        recorded_by = register.session_recorded_by(case_dir)
    except case_files.CaseRefused as exc:
        raise FigureRefused(f"figure: {exc}") from exc
    case = _case_today(case_dir)

    def build() -> dict:  # under the log's lock, so the number and the checks follow the lines on file
        state = _derive(case_dir)
        rec = {"record": "figure", "id": f"FIG-{state.last_number + 1:03d}"}
        for key in _REQUIRED + _OPTIONAL:
            rec[key] = proposal.get(key)
        if rec["replaces"] is None:
            rec["replaces"] = []
        rec.update(recorded_by=recorded_by, date=clock.today())
        problem = state.figure_problem(rec, case)
        if problem:
            raise FigureRefused(problem)
        return rec
    return _append(case_dir, build)


LABEL_KEY = "label"
REFERENCE_KEYS = ("replaces", "restates", "supersedes")
_LABEL = re.compile(r"P[1-9][0-9]*")
_LABEL_SHAPE = re.compile(r"[Pp][0-9]+")  # what a model writes when it means a label


class Labels:
    """Proposal-local labels for one proposals file (controller rulings, Task 19). A proposal may carry
    `label` (P1, P2, ...); a later proposal names it in `replaces`, `restates` or `supersedes` (the
    last is deliberate: a re-extraction may correct its own earlier proposal), and the label is
    resolved to the FIG-NNN code gave that proposal, never by its position. Every proposal's
    references are resolved, labelled or not. Refused, naming the cause: a reference to a refused
    proposal, to a label no earlier proposal carries, to a label more than one proposal carries,
    to a FIG-NNN this same file's run gave (name it by its label), or a reference shaped like a
    label that is not one (`p1`, `P01`). A FIG-NNN given before this run passes through unchanged."""

    def __init__(self) -> None:
        self._ids: dict = {}  # label -> FIG-NNN, or None when its proposal was refused
        self._repeated: set = set()  # labels carried by more than one proposal: never resolved
        self._given: set = set()  # FIG-NNN this run recorded
        self._pending = None

    def resolve(self, proposal):
        """The proposal without its label, each label reference replaced by its FIG-NNN."""
        self._pending = None
        if not isinstance(proposal, dict):
            return proposal
        out = {k: v for k, v in proposal.items() if k != LABEL_KEY}
        if LABEL_KEY in proposal:
            label = proposal[LABEL_KEY]
            if not isinstance(label, str) or not _LABEL.fullmatch(label):
                raise FigureRefused(f"figure: the label {label!r} is not P1, P2 and so on")
            if label in self._ids or label in self._repeated:
                self._repeated.add(label)
                raise FigureRefused(f"figure: the label {label} is carried by an earlier proposal; "
                                    "a later reference to it is refused")
            self._pending = label
        for key in REFERENCE_KEYS:
            value = out.get(key)
            if isinstance(value, list):
                out[key] = [self._id(key, ref) for ref in value]
            elif value is not None:
                out[key] = self._id(key, value)
        return out

    def _id(self, key: str, ref):
        if not isinstance(ref, str):
            return ref
        if ref in self._given:
            raise FigureRefused(f"figure: {key} names {ref}, which this file's proposals were given; "
                                "name one of your own proposals by its label")
        if not _LABEL.fullmatch(ref):
            if _LABEL_SHAPE.fullmatch(ref):
                raise FigureRefused(f"figure: {key} names {ref}, which is not a label: a label is P1, P2 and "
                                    "so on, with a capital P and no leading zero")
            return ref
        if ref in self._repeated:
            raise FigureRefused(f"figure: {key} names {ref}, a label carried by more than one proposal")
        if ref not in self._ids:
            raise FigureRefused(f"figure: {key} names {ref}, which no earlier proposal carries as its label")
        if self._ids[ref] is None:
            raise FigureRefused(f"figure: {key} names {ref}, a proposal that was refused; it is refused too")
        return self._ids[ref]

    def done(self, fig_id) -> None:
        """Record the outcome of the proposal last resolved: its FIG-NNN, or None when refused."""
        if fig_id is not None:
            self._given.add(fig_id)
        if self._pending is not None:
            self._ids[self._pending] = fig_id
        self._pending = None


def confirm_figure(case_dir, figure_id, *, question, answer) -> dict:
    """Record the proposer's confirmation of a live, unconfirmed figure, with the answer verbatim.
    Needs a named person: an automated session is refused."""
    case_dir = Path(case_dir)
    try:
        name = case_files.current_name(case_dir)
    except case_files.CaseRefused as exc:
        raise FigureRefused(f"figure: {exc}; only a named person confirms a figure") from exc
    if _blank(question) or _blank(answer):
        raise FigureRefused("figure: the question and the person's answer must not be blank")
    rec = {"record": "confirm", "ref": figure_id, "question": question, "answer": answer, "role": "proposer",
           "name": name, "date": clock.today()}

    def build() -> dict:  # under the log's lock, so the check reads the lines on file
        problem = _derive(case_dir).confirm_problem(rec)
        if problem:
            raise FigureRefused(problem)
        return rec
    return _append(case_dir, build)


def _status(state: _State, fig_id: str) -> str:
    if fig_id in state.superseded_by:
        return "superseded"
    return "confirmed" if fig_id in state.confirmed else "stated"


def figures(case_dir, upto: int | None = None) -> dict:
    """The counted figures by ID, each with its derived `status` and `superseded_by`, from the file
    cut at `upto` bytes (None: the whole file)."""
    state = _derive(Path(case_dir), upto)
    return {fig_id: dict({k: v for k, v in rec.items() if k != "prev"}, status=_status(state, fig_id),
                         superseded_by=state.superseded_by.get(fig_id))
            for fig_id, rec in state.figures.items()}


def live_figures(case_dir) -> list:
    """The figures not superseded, in ID order."""
    return sorted((f for f in figures(case_dir).values() if f["status"] != "superseded"),
                  key=lambda f: _number(f["id"]))


def ignored_lines(case_dir) -> tuple:
    """One reason per line of figures.jsonl that the readers do not count."""
    return tuple(_derive(Path(case_dir)).ignored)


def check_file(case_dir) -> None:
    """Raise FigureRefused, naming the file and the line, for a file that cannot be read or holds a
    line that does not count."""
    ignored = ignored_lines(case_dir)
    if ignored:
        raise FigureRefused("; ".join(ignored))


def recheck(case_dir, fig: dict, *, live: dict, superseded: dict, basis: "basis.Basis",
            sections: dict) -> str | None:
    """Checks 2 to 6, 9, 11 and 12 against today's files: the failing check's message, or None.
    Check 3 applies to a grid kind only (a terminal value's month must still be the last horizon
    month). `live` maps each live figure's ID to the figure, `superseded` each superseded one's (check
    12 walks back through the figures this one supersedes); `sections` is business-case.md's sections."""
    case_dir = Path(case_dir)
    try:
        try:
            applicable = case_files.read_scope(case_dir)["applicable_item_ids"]
        except case_files.CaseRefused as exc:
            _fail(6, str(exc))
        _check_2(fig, basis)
        _check_3(fig, basis)
        _check_4(fig, sections)
        _check_5(fig, sections, basis.currency, live)
        _check_6(case_dir, fig, applicable)
        _check_9(fig, live)
        _check_11(fig, {**superseded, **live})
        _check_12(fig, {**superseded, **live}, live,
                  {i: f["superseded_by"] for i, f in superseded.items()})
    except _Check as exc:
        return str(exc)
    return None


def grade(case_dir, fig: dict) -> str:
    """The figure's grade: `estimated` for a terminal value and for a page whose source names
    business-case.md (the proposer's own text is never evidence for a number); else the page's grade."""
    if fig["kind"] == "terminal_value":
        return "estimated"
    try:
        page = evidence_pages.read_page(Path(case_dir), fig["evidence"])
    except evidence_pages.EvidenceRefused as exc:
        raise FigureRefused(f"check 6: {exc}") from exc
    source = page.get("source")
    if isinstance(source, str) and paths.CASE_DOC in evidence_pages.case_files_named(source):
        return "estimated"
    return page["grade"]
