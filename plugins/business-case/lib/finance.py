"""The finance engine: NPV, payback, ROI, revenue by year, growth and grade shares (spec §6).

Pure functions over figures as `figures.figures` gives them. Nothing here reads a file: the
caller chooses which figures count. Money is `decimal.Decimal` under `basis.CONTEXT`; nothing is
rounded here.

- A flow is one figure's amount in one month: `basis.spread` over its months, signed by kind
  (cash in positive, cash out negative). A terminal value sits at the last horizon month.
- NPV sums each month's signed flows first (a terminal value joins the last month's net), then
  discounts each month's net once, end of month: net_m / (1 + i) ** m, with i the monthly rate
  (1 + annual) ** (1/12) - 1.
- Payback, cumulative net cash and ROI are undiscounted and leave out the terminal value.
- Grade shares are gross: each grade's share of the summed absolute per-figure, per-month
  amounts, discounted for NPV.

`compute` reads the case through `settle` and decides the verdict ceiling (§6 rules 1 to 4). The
numbers are the base scenario's. A figure of any scenario that does not count yet keeps the verdict
from reading supported. `compute` is the one function here that reads files, and it lets out no read
error but FinanceRefused. Every sum runs in `basis.CONTEXT`, whatever context the caller set.
"""
from __future__ import annotations

import contextlib
import decimal
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from . import (
    basis,
    case_doc,
    case_files,
    decision_record,
    digest,
    evidence,
    figures,
    judge_report,
    paths,
    rubric,
    settle,
)

NO_OUTFLOW = "no outflow to pay back"
NOT_WITHIN = "not within the horizon"
NOT_COMPUTABLE = "not computable"
UNPARSED = "NPV and payback need a parsed discount rate, horizon and start month"

CEILING_ORDER = ("supported", "undetermined", "not_supported")
TOTAL_NAMES = {"npv": "NPV", "cumulative_net_cash": "cumulative net cash", "roi": "ROI"}
TOTALS = ("npv", "cumulative_net_cash", "roi")
# The item an uncovered money amount is a finding on (rubric 1.1.0); a rubric without it gets none.
AMOUNT_ITEM = "BC-FIGURES-COMPLETE"
# The summaries of the findings code adds for money (Task 11). Plain words: the section by its heading.
AMOUNT_SUMMARY = "The {section} section states {written} in a sentence no confirmed figure covers: {sentence}"
TOTAL_SUMMARY = "In the {scenario} scenario, {share} of {total_name} rests on estimates, above the {limit} limit."
# The funder reads these in finance-view.md: plain words, no rubric ID, totals by TOTAL_NAMES.
CEILING_REASONS = {
    "cautious_npv": "even counting every recorded cost and only the income a person settled, NPV is below zero",
    "cautious_payback": "even counting every recorded cost and only the income a person settled, the cash never "
                        "pays back within the horizon",
    "basis": "the financial basis is incomplete: {causes}",
    "unsettled": "{id} is not settled: {reason}",
    "uncovered": "a money amount in {section} is not covered by a settled figure: {written}",
    "written_twice": "a money amount in {section} is written twice in the same words: {written}",
    "unreadable": "a money amount in {section} cannot be read by code: {written}",
    "not_computable": "NPV or payback cannot be computed: {why}",
    "no_outflow": "there is no outflow to pay back",
    "estimated_share": "the share of {total_name} that rests on estimates is above the limit",
    "terminal_share": "the terminal value's share of NPV is above the limit",
    "npv": "NPV is below zero",
    "payback": "payback is not within the horizon",
    "supported": "every figure is settled and the numbers allow it",
}

# settle's reasons in the funder's words (ruling: no rubric ID, check number or section key reaches
# the funder). Keyed by settle.REASONS; a re-check failure is named by its check number.
UNSETTLED_WORDS = {
    "unconfirmed": "the person has not confirmed it",
    "estimate_unproposed": "it is not yet proposed to the funder as an estimate",
    "estimate_pending": "it is an estimate the funder has not approved",
    "estimate_rejected": "it is an estimate the funder rejected",
    "exclusion_unproposed": "it is not yet proposed to the funder",
    "exclusion_pending": "the funder has not approved leaving it out",
    "exclusion_rejected": "the funder rejected leaving it out",
    "recheck": "the case no longer supports it: {why}",
}
RECHECK_WORDS = {
    2: "its currency is not the case's currency",
    3: "its months are not on the case's month grid",
    4: "the sentence it quotes is no longer in the case",
    5: "the amount it quotes is no longer written there",
    6: "its evidence no longer supports it",
    9: "a figure it replaces or restates has changed",
    11: "it is a run rate whose shape the rules do not allow",
    12: "it replaces a total whose parts still count",
}
RECHECK_OTHER = "it no longer matches the case"
_CHECK = re.compile(r"check ([0-9]+):")


class FinanceRefused(ValueError):
    """A file the finances read cannot be read. The message names the file."""


# The read errors compute turns into FinanceRefused; any other exception is a bug and is not caught.
# A function, not a module-level tuple: decision_record and judge_report import this module while they
# load, so no attribute of decision_record may be read at import time (Global Constraints, P3-04).
def _read_errors() -> tuple:
    return (figures.FigureRefused, evidence.EvidenceRefused, case_doc.CaseDocError, rubric.RubricError,
            case_files.CaseRefused, OSError, UnicodeDecodeError, decision_record.DecisionRefused)


_CASE_FILES = (paths.CASE_DOC, paths.FIGURES, paths.DECISIONS, paths.RUBRIC_COPY, paths.SCOPE, paths.CASE_META)


def _file_of() -> tuple:
    """The file a cause names when its message names none; read at call time, as _read_errors."""
    return ((decision_record.DecisionRefused, paths.DECISIONS), (figures.FigureRefused, paths.FIGURES),
            (evidence.EvidenceRefused, paths.EVIDENCE_DIR), (case_doc.CaseDocError, paths.CASE_DOC),
            (rubric.RubricError, paths.RUBRIC_COPY), (case_files.CaseRefused, paths.SCOPE))



@dataclass(frozen=True)
class Flow:
    figure: str
    kind: str
    grade: str
    month: int
    amount: Decimal  # signed: cash in positive, cash out negative


@dataclass(frozen=True)
class Total:
    value: "Decimal | None"
    shares: dict
    lowest_grade: "str | None"
    why_not: "str | None"


@dataclass(frozen=True)
class ScenarioResult:
    npv: "Total | None"
    terminal_share: "Decimal | None"
    cumulative: Total
    roi: Total
    payback: "int | str | None"
    years: list
    growth: list
    why_not: "str | None"


def _order(fig: dict) -> tuple:
    return (len(fig["id"]), fig["id"])


def scenario_figures(live: dict, scenario: str, counts=None) -> list:
    """The base figures; for another scenario, the base figures less those its own figures
    replace, plus its own. In ID order. `counts` is the set of figure IDs that count; only a
    figure in it replaces anything, so an unsettled scenario figure leaves the base figure in place
    (Task 15 ruling). None: every figure counts."""
    base = [f for f in live.values() if f["scenario"] == figures.BASE]
    if scenario == figures.BASE:
        return sorted(base, key=_order)
    own = [f for f in live.values() if f["scenario"] == scenario]
    replaced = {ref for f in own if counts is None or f["id"] in counts for ref in f.get("replaces") or ()}
    return sorted([f for f in base if f["id"] not in replaced] + own, key=_order)


def flows(figs: list, grades: dict, horizon: int) -> list:
    """One Flow per figure and month, for the cash and terminal kinds only. `grades` maps a
    figure ID to its grade."""
    out = []
    for fig in figs:
        kind = fig["kind"]
        if kind not in figures.NPV_KINDS:
            continue
        amount = Decimal(fig["amount"])
        if kind == "terminal_value":
            months = {horizon: amount}
        else:
            months = basis.spread(amount, fig["months"]["from"], fig["months"]["to"])
        sign = 1 if kind in figures.INFLOW_KINDS else -1
        with decimal.localcontext(basis.CONTEXT):
            out.extend(Flow(fig["id"], kind, grades[fig["id"]], m, sign * a) for m, a in sorted(months.items()))
    return out


def shares(parts: list) -> dict:
    """Grade -> its share of the summed absolute amounts, over the grades with a non-zero part."""
    with decimal.localcontext(basis.CONTEXT):
        by_grade = {}
        for grade, amount in parts:
            if amount != 0:
                by_grade[grade] = by_grade.get(grade, Decimal(0)) + abs(amount)
        whole = sum(by_grade.values(), Decimal(0))
        return {g: v / whole for g, v in by_grade.items()} if whole else {}


def lowest(parts: list) -> "str | None":
    """The lowest grade among the non-zero parts, in evidence.GRADES; None when every part is zero."""
    present = {grade for grade, amount in parts if amount != 0}
    return max(present, key=evidence.GRADES.index) if present else None


def _total(value, parts: list, why_not=None) -> Total:
    return Total(value, shares(parts), lowest(parts), why_not)


def _factors(rate: Decimal, months) -> dict:
    with decimal.localcontext(basis.CONTEXT):
        step = 1 + basis.monthly_rate(rate)
        return {m: step ** m for m in months}


def npv(flows: list, rate: Decimal, horizon: int) -> Total:
    """Σ net_m / (1 + i) ** m over the months, each month's signed flows summed first."""
    net = {}
    with decimal.localcontext(basis.CONTEXT):
        for f in flows:
            net[f.month] = net.get(f.month, Decimal(0)) + f.amount
        factor = _factors(rate, net)
        value = sum((net[m] / factor[m] for m in sorted(net)), Decimal(0))
        parts = [(f.grade, abs(f.amount) / factor[f.month]) for f in flows]
    return _total(value, parts)


def terminal_share(flows: list, rate: Decimal, horizon: int, npv_total: "Decimal | None") -> "Decimal | None":
    """PV(terminal value) / NPV; None when NPV is not above zero or there is no terminal value."""
    terminal = [f for f in flows if f.kind == "terminal_value"]
    if not terminal or npv_total is None or npv_total <= 0:
        return None
    with decimal.localcontext(basis.CONTEXT):
        factor = _factors(rate, [horizon])[horizon]
        present = sum((f.amount for f in terminal), Decimal(0)) / factor
        return present / npv_total


def _cash(flows: list) -> list:
    return [f for f in flows if f.kind != "terminal_value"]


def cumulative_net_cash(flows: list) -> Total:
    cash = _cash(flows)
    with decimal.localcontext(basis.CONTEXT):
        value = sum((f.amount for f in cash), Decimal(0))
    return _total(value, [(f.grade, f.amount) for f in cash])


def roi(flows: list) -> Total:
    """(cash in - cash out) / cash out, undiscounted; not computable with no cash out."""
    cash = _cash(flows)
    with decimal.localcontext(basis.CONTEXT):
        cash_in = sum((f.amount for f in cash if f.amount > 0), Decimal(0))
        cash_out = -sum((f.amount for f in cash if f.amount < 0), Decimal(0))
        if cash_out == 0:
            return Total(None, {}, None, NOT_COMPUTABLE)
        value = (cash_in - cash_out) / cash_out
    return _total(value, [(f.grade, f.amount) for f in cash])


def payback(flows: list, horizon: int) -> "int | str":
    """The first month m where cumulative cash was below zero in some month before m, and is
    zero or above in m and every later month of the horizon. Undiscounted, no terminal value."""
    net = {}
    running, last_below = Decimal(0), None
    with decimal.localcontext(basis.CONTEXT):
        for f in _cash(flows):
            net[f.month] = net.get(f.month, Decimal(0)) + f.amount
        for m in range(1, horizon + 1):
            running += net.get(m, Decimal(0))
            if running < 0:
                last_below = m
    if last_below is None:
        return NO_OUTFLOW
    if last_below == horizon:
        return NOT_WITHIN
    return last_below + 1


def revenue_by_year(flows: list, horizon: int) -> list:
    """Revenue for each full year of the horizon (months 1-12, 13-24, ...)."""
    out = []
    for year in range(horizon // 12):
        first, last = 12 * year + 1, 12 * year + 12
        rev = [f for f in flows if f.kind == "revenue" and first <= f.month <= last]
        with decimal.localcontext(basis.CONTEXT):
            value = sum((f.amount for f in rev), Decimal(0))
        out.append(_total(value, [(f.grade, f.amount) for f in rev]))
    return out


def growth(years: list) -> list:
    """(year n / year n-1) - 1; None for year 1 and for a year that follows a year with no revenue."""
    out = [None] if years else []
    with decimal.localcontext(basis.CONTEXT):
        for before, now in zip(years, years[1:]):
            out.append(None if before.value == 0 else now.value / before.value - 1)
    return out


def _result(cash: list, case_basis: "basis.Basis") -> ScenarioResult:
    """Every total from one scenario's flows. NPV and payback need a parsed rate, horizon and start
    month; without them they are None and `why_not` says so."""
    horizon = case_basis.horizon
    years = [] if horizon is None else revenue_by_year(cash, horizon)
    cumulative, ret = cumulative_net_cash(cash), roi(cash)
    if case_basis.rate is None or horizon is None or case_basis.start_month is None:
        return ScenarioResult(None, None, cumulative, ret, None, years, growth(years), UNPARSED)
    value = npv(cash, case_basis.rate, horizon)
    return ScenarioResult(value, terminal_share(cash, case_basis.rate, horizon, value.value), cumulative, ret,
                          payback(cash, horizon), years, growth(years), None)


def scenario_result(figs: list, grades: dict, case_basis: "basis.Basis") -> ScenarioResult:
    """Every total for one scenario's figures. With no horizon, a terminal value has no month and
    is left out."""
    horizon = case_basis.horizon
    if horizon is None:
        return _result(flows([f for f in figs if f["kind"] != "terminal_value"], grades, 0), case_basis)
    return _result(flows(figs, grades, horizon), case_basis)


# -- the verdict ceiling (spec §6, base scenario) -----------------------------------------------


def estimate_limit(rub: dict) -> Decimal:
    """The rubric's float read through str, so 0.3 is exactly Decimal("0.3")."""
    return Decimal(str(rub["estimated_share_threshold"]))


def _outflow(fig: dict, grade: str, first: int, last: int, horizon: "int | None") -> list:
    """The figure's whole amount as cash out over months first..last, clipped to the grid."""
    if horizon is not None:
        first, last = min(first, horizon), min(last, horizon)
    first, last = min(first, last), max(first, last)
    with decimal.localcontext(basis.CONTEXT):
        months = basis.spread(Decimal(fig["amount"]), first, last)
        return [Flow(fig["id"], fig["kind"], grade, m, -a) for m, a in sorted(months.items())]


def cautious_flows(settlement: "settle.Settlement", horizon: "int | None") -> list:
    """§6 rule 1 (ruling C-1): every live base outflow whatever its state, at face value over its
    months clipped to the grid (ruling P3-16); every amount cautious_exclusions names (a judgment
    exclusion that is not settled; never a run rate), as cash out over its months, or in month 1 when
    it has none, unless a live base outflow figure quotes the same amount (that outflow already counts);
    and the base inflows that count. With no horizon a terminal value has no month."""
    out, base = [], scenario_figures(settlement.live, figures.BASE)
    left_out = set(cautious_exclusions(settlement))
    for fig in base:
        state, kind = settlement.states[fig["id"]], fig["kind"]
        if kind in figures.INFLOW_KINDS:
            if state.counts and (horizon is not None or kind != "terminal_value"):
                out.extend(flows([fig], {fig["id"]: state.grade}, horizon))
        elif kind in figures.OUTFLOW_KINDS:
            out.extend(_outflow(fig, state.grade, fig["months"]["from"], fig["months"]["to"], horizon))
        elif fig["id"] in left_out:
            months = fig["months"] or {"from": 1, "to": 1}
            out.extend(_outflow(fig, state.grade, months["from"], months["to"], horizon))
    return out


def cautious_exclusions(settlement: "settle.Settlement") -> list:
    """The IDs, in figure order, of the amounts proposed for leaving out but not yet approved that
    rule 1 counts as cash out: each live base judgment exclusion (figures.is_judgment_exclusion, so
    never a run rate) that is not settled, unless a live base outflow quotes the same amount.
    cautious_flows and the funder's view both read this one list (Task 17 carry)."""
    base = scenario_figures(settlement.live, figures.BASE)
    # Only an outflow: rule 1 counts it whatever its state. An inflow may not count, so it never
    # removes an exclusion (re-review N1).
    cash_at = {o for f in base if f["kind"] in figures.OUTFLOW_KINDS for o in figures.occurrences(f)}
    return [f["id"] for f in base
            if figures.is_judgment_exclusion(f, settlement.recorded()) and not settlement.states[f["id"]].settled
            and not cash_at & set(figures.occurrences(f))]  # an outflow already counts its amount


def plain_reason(reason: str) -> str:
    """settle's reason for a figure that is not settled, in the funder's words. Raw re-check text
    never passes through."""
    for key, text in settle.REASONS.items():
        if key != "recheck" and reason == text:
            return UNSETTLED_WORDS[key]
    m = _CHECK.search(reason)
    return UNSETTLED_WORDS["recheck"].format(why=RECHECK_WORDS.get(int(m.group(1)), RECHECK_OTHER) if m
                                             else RECHECK_OTHER)


def _above(share: "Decimal | None", limit: Decimal) -> bool:
    return share is not None and share > limit


def _covers(terminal: "Decimal | None", result: ScenarioResult) -> bool:
    """The payback exemption (ruling I1): a terminal value at least the cash still owed at the end of
    the horizon."""
    with decimal.localcontext(basis.CONTEXT):
        return terminal is not None and result.cumulative.value + terminal >= 0


def _terminal(settlement: "settle.Settlement") -> "Decimal | None":
    """The base scenario's counted terminal value, or None when none counts."""
    counted = [Decimal(f["amount"]) for f in scenario_figures(settlement.live, figures.BASE)
               if f["kind"] == "terminal_value" and settlement.states[f["id"]].counts]
    return sum(counted, Decimal(0)) if counted else None  # settled = counted for a cash kind


def own_cash_short(result: "FinanceResult") -> bool:
    """True when the ceiling is not_supported and the case's own numbers, every live base cash and
    terminal figure as stated (settled or not), never pay back: payback not within the horizon, with
    the terminal value not covering what is still owed (Task 10 ruling I1; Task 21 ruling N1: the
    payback test only, as a negative NPV has its own ceiling reason). Never the
    cautious cash: unsettled income and unapproved exclusions have their own reasons (Task 21 fix
    round 1, ruling C1). The view's own-cash sentence is keyed on this, never on a reason's wording."""
    if result.ceiling != "not_supported":
        return False
    s = result.settlement
    stated = [f for f in scenario_figures(s.live, figures.BASE) if f["kind"] in figures.NPV_KINDS]
    own = scenario_result(stated, {i: st.grade for i, st in s.states.items()}, s.basis)
    if own.npv is None:
        return False
    tvs = [Decimal(f["amount"]) for f in stated if f["kind"] == "terminal_value"]
    with decimal.localcontext(basis.CONTEXT):
        terminal = sum(tvs, Decimal(0)) if tvs else None
        return own.payback == NOT_WITHIN and not _covers(terminal, own)


def ceiling_of(settlement: "settle.Settlement", base: ScenarioResult, cautious: ScenarioResult,
               limit: Decimal, headings: "dict | None" = None) -> tuple:
    """(ceiling, reason): rules 1 to 4 in §6's order; the first that fires gives the reason, and
    inside rule 2 the first condition in §6's order. Rule 2 reads every live figure that is not
    settled, base figures first, then the other scenarios', each by ID; then the first amount no
    figure records, named as written twice when it is a copy. `headings` maps a section key to the
    heading the person reads."""
    reasons = CEILING_REASONS
    terminal = _terminal(settlement)
    if cautious.npv is not None:  # rule 1, only when cautious cash can be computed
        if cautious.npv.value < 0:
            return "not_supported", reasons["cautious_npv"]
        if cautious.payback == NOT_WITHIN and not _covers(terminal, cautious):
            return "not_supported", reasons["cautious_payback"]
    if not settlement.basis.complete:  # rule 2
        return "undetermined", reasons["basis"].format(causes="; ".join(settlement.basis.unparsed))
    ordered = sorted(settlement.live.values(), key=lambda f: (f["scenario"] != figures.BASE, _order(f)))
    for fig in ordered:
        state = settlement.states[fig["id"]]
        if not state.settled:
            return "undetermined", reasons["unsettled"].format(id=fig["id"], reason=plain_reason(state.reason))
    missed = settle.amounts_no_figure_records(settlement.amounts, settlement.live)
    if missed:
        first = missed[0]
        section = (headings or {}).get(first.section, "the case")
        # an unreadable amount takes its own key, as the view's mark does: no figure can cover it
        key = ("unreadable" if first.unreadable else
               "written_twice" if id(first) in settle.written_twice(settlement.amounts) else "uncovered")
        return "undetermined", reasons[key].format(section=section, written=first.written)
    if base.npv is None or base.payback is None:
        return "undetermined", reasons["not_computable"].format(why=base.why_not)
    if base.payback == NO_OUTFLOW:
        return "undetermined", reasons["no_outflow"]
    for key, total in (("npv", base.npv), ("cumulative_net_cash", base.cumulative)):
        if _above(total.shares.get("estimated"), limit):
            return "undetermined", reasons["estimated_share"].format(total_name=TOTAL_NAMES[key])
    if base.npv.value > 0 and _above(base.terminal_share, limit):
        return "undetermined", reasons["terminal_share"]
    if base.npv.value < 0:  # rule 3
        return "not_supported", reasons["npv"]
    if base.payback == NOT_WITHIN and not _covers(terminal, base):
        return "not_supported", reasons["payback"]
    return "supported", reasons["supported"]  # rule 4


@dataclass(frozen=True)
class FinanceResult:
    settlement: "settle.Settlement"
    scenarios: dict          # scenario name -> ScenarioResult, base first, then the others sorted
    cautious: ScenarioResult  # the base scenario's cautious cash (rule 1)
    ceiling: str
    ceiling_reason: str
    limit: Decimal
    decisions_bytes: int     # the length of decisions.jsonl read
    headings: dict           # section key -> the heading the person reads
    figures_bytes: "int | None" = None  # the length of figures.jsonl read; None: the whole file


def _file_named(exc: BaseException) -> str:
    """The case file the message names first; else an OSError's file; else the cause's own file."""
    text = str(exc)
    found = sorted((text.index(name), name) for name in _CASE_FILES if name in text)
    if found:
        return found[0][1]
    if isinstance(exc, OSError) and exc.filename:
        return Path(str(exc.filename)).name
    return next((name for cls, name in _file_of() if isinstance(exc, cls)), "a case file")


@contextlib.contextmanager
def _reading(name: "str | None"):
    """Turn a read error into FinanceRefused naming `name`, or the file the error names."""
    try:
        yield
    except _read_errors() as exc:
        file = name or _file_named(exc)
        text = str(exc)  # a message that already starts with the file name is not prefixed again (review M5)
        raise FinanceRefused(text if text.startswith(f"{file}: ") else f"{file}: {text}") from exc


def compute(case_dir, *, decisions_upto: "int | None" = None, figures_upto: "int | None" = None) -> FinanceResult:
    """Every scenario's totals from the figures that count, the base scenario's cautious cash, and
    the verdict ceiling, with decisions.jsonl cut at `decisions_upto` bytes (None: the whole file,
    its length taken once and used for every read) and figures.jsonl cut at `figures_upto` bytes
    (None: the whole file)."""
    case_dir = Path(case_dir)
    with _reading(paths.RUBRIC_COPY):
        limit = estimate_limit(rubric.load_rubric(case_dir / paths.RUBRIC_COPY))
    with _reading(paths.DECISIONS):
        size = (case_dir / paths.DECISIONS).stat().st_size
    upto = size if decisions_upto is None else min(decisions_upto, size)
    with _reading(None):
        settlement = settle.settle(case_dir, decisions_upto=upto, figures_upto=figures_upto)
    with _reading(paths.CASE_DOC):
        headings = case_doc.headings((case_dir / paths.CASE_DOC).read_text(encoding="utf-8"))
    grades = {fig_id: state.grade for fig_id, state in settlement.states.items()}
    others = sorted({f["scenario"] for f in settlement.live.values()} - {figures.BASE})
    counts = {fig_id for fig_id, state in settlement.states.items() if state.counts}
    scenarios = {}
    for name in [figures.BASE] + others:
        counted = [f for f in scenario_figures(settlement.live, name, counts) if f["id"] in counts]
        scenarios[name] = scenario_result(counted, grades, settlement.basis)
    cautious = _result(cautious_flows(settlement, settlement.basis.horizon), settlement.basis)
    level, reason = ceiling_of(settlement, scenarios[figures.BASE], cautious, limit, headings)
    return FinanceResult(settlement, scenarios, cautious, level, reason, limit, upto, headings, figures_upto)


def largest_revenue(result: FinanceResult) -> "str | None":
    """The ID of the base scenario's largest revenue figure that counts, by its total over the horizon as
    `flows` spreads it; on a tie the lowest figure ID; None when no revenue figure counts. The review
    reads it from finance.json and never ranks figures itself (Task 23b)."""
    s = result.settlement
    best, most = None, None
    for fig in scenario_figures(s.live, figures.BASE):
        if fig["kind"] != "revenue" or not s.states[fig["id"]].counts:
            continue
        with decimal.localcontext(basis.CONTEXT):
            total = sum((f.amount for f in flows([fig], {fig["id"]: None}, s.basis.horizon or 0)), Decimal(0))
        if most is None or total > most:
            best, most = fig["id"], total
    return best


# -- the findings code adds (Task 11; ADR-008) --------------------------------------------------


def amount_anchors(found) -> list:
    """The anchor of each money amount, in scan order: `MoneyAmount.anchor`, with `|n` added for the
    n-th copy (n >= 2) of a repeated sentence, so two copies of one sentence are two anchors."""
    seen, out = {}, []
    for m in found:
        base = m.anchor
        seen[base] = seen.get(base, 0) + 1
        out.append(base if seen[base] == 1 else f"{base}|{seen[base]}")
    return out


def percent(x: Decimal) -> str:
    """x as an exact percentage with no trailing zeros: 0.3 -> "30%", 0.255 -> "25.5%"."""
    with decimal.localcontext(basis.CONTEXT):
        return f"{(x * 100).normalize():f}%"


def above_percent(share: Decimal, limit: Decimal) -> str:
    """The share as a percentage cut (never rounded up) at the fewest places, from none, that still
    read above the limit, so the text never shows a share equal to the limit it is above (review M2).
    `share` is above `limit`."""
    with decimal.localcontext(basis.CONTEXT):
        whole, bound = share * 100, limit * 100
        for places in range(basis.CONTEXT.prec):
            cut = whole.quantize(Decimal(1).scaleb(-places), rounding=decimal.ROUND_DOWN)
            if cut > bound:
                return f"{cut:f}%"
        return f"{whole:f}%"


def _finding(job: str, item_id, kind: str, ref: str, anchor: str, summary: str) -> dict:
    return {"job": job, "item_id": item_id, "target": {"kind": kind, "ref": ref}, "summary": summary,
            "anchor": anchor, "id": judge_report.finding_id(job, kind, anchor)}


def code_findings(result: FinanceResult, rub: dict, applicable: set) -> list:
    """The findings code adds from the finances, whatever the review gave: one `amount` finding per
    money amount no confirmed figure covers, when AMOUNT_ITEM applies; one `investment` finding per
    scenario and total whose estimated share is above the rubric's limit (item None, ruling P3-23).
    Each anchor carries the state: the amount's sentence, or the share."""
    out = []
    if AMOUNT_ITEM in applicable:
        uncovered = {id(m) for m in result.settlement.uncovered_confirmed}
        for m, anchor in zip(result.settlement.amounts, amount_anchors(result.settlement.amounts)):
            if id(m) in uncovered:
                summary = AMOUNT_SUMMARY.format(section=result.headings.get(m.section, m.section),
                                                written=m.written, sentence=m.sentence)
                out.append(_finding("completeness", AMOUNT_ITEM, "amount", anchor, anchor, summary))
    limit = estimate_limit(rub)
    for scenario, res in result.scenarios.items():
        for total, value in zip(TOTALS, (res.npv, res.cumulative, res.roi)):
            share = value.shares.get("estimated") if value is not None else None
            if not _above(share, limit):
                continue
            summary = TOTAL_SUMMARY.format(scenario=scenario, share=above_percent(share, limit),
                                           total_name=TOTAL_NAMES[total], limit=percent(limit))
            out.append(_finding("investment", None, "total", f"{scenario}|{total}",
                                 f"{scenario}|{total}|{share:.4f}", summary))
    return out


# -- the items code computes (Task 15; spec §7 "What a computed item cites") -------------------

PAYBACK_ITEM = "BC-PAYBACK-CASH"
SCENARIOS_ITEM = "BC-SCENARIOS"


def _npv_and_payback(res: ScenarioResult) -> bool:
    return res.npv is not None and res.npv.value is not None and res.payback is not None


def computed_item_problem(result: FinanceResult, item_id: str) -> "str | None":
    """Why `result` does not hold what the met test of a computed item names; None when it does.
    BC-PAYBACK-CASH: a base-case payback month, or not within the horizon (no outflow does not
    count). BC-SCENARIOS: NPV and payback, any payback result, for the base case and at least one
    other scenario that has a cash figure of its own (figures.NPV_KINDS) that counts (ruling I1).
    BC-FIGURES-COMPLETE: no money amount that no confirmed figure covers, so code adds no `amount`
    finding (code wins over a met from the review; Task 11 carry)."""
    base = result.scenarios[figures.BASE]
    if item_id == PAYBACK_ITEM:
        if base.payback is None:
            return f"code computed no base-case payback: {base.why_not}"
        if base.payback == NO_OUTFLOW:
            return "the base case has no outflow to pay back"
        return None
    if item_id == SCENARIOS_ITEM:
        if not _npv_and_payback(base):
            return f"code computed no NPV and payback for the base case: {base.why_not}"
        settlement = result.settlement
        # Only a CASH figure of its own (figures.NPV_KINDS) changes a scenario's numbers: a booking
        # or an exclusion leaves them the base's (Task 15 carry). settle never counts a non-cash
        # figure; the kind test states the rule here rather than lean on that.
        own_counts = {f["scenario"] for f in settlement.live.values()
                      if f["kind"] in figures.NPV_KINDS and settlement.states[f["id"]].counts}
        if not any(_npv_and_payback(res) for name, res in result.scenarios.items()
                   if name != figures.BASE and name in own_counts):
            return "code computed NPV and payback for the base case only, and for no other scenario"
        return None
    if item_id == AMOUNT_ITEM:
        n = len(result.settlement.uncovered_confirmed)
        if n == 0:
            return None
        return f"{n} money amount{' is' if n == 1 else 's are'} not covered by a confirmed figure"
    return f"{item_id} is not an item code computes"


# -- finance.json: what `bc.py brief` gives the review (Task 13; spec §6 "Module", "Freshness") ---


def _money(x) -> "str | None":
    return None if x is None else f"{x:f}"


def _total_json(t: "Total | None") -> "dict | None":
    if t is None:
        return None
    return {"value": _money(t.value), "shares": {g: _money(v) for g, v in t.shares.items()},
            "lowest_grade": t.lowest_grade, "why_not": t.why_not}


def _scenario_json(r: ScenarioResult) -> dict:
    return {"npv": _total_json(r.npv), "terminal_share": _money(r.terminal_share),
            "cumulative_net_cash": _total_json(r.cumulative), "roi": _total_json(r.roi),
            "payback": r.payback, "revenue_by_year": [_total_json(t) for t in r.years],
            "growth": [_money(g) for g in r.growth], "why_not": r.why_not}


def _input_digests(result: FinanceResult, manifest: dict) -> dict:
    """POSIX relative path -> {"sha256", "bytes"} of each file the numbers were read from, as the
    manifest taken before compute recorded it; None for a file the manifest does not list."""
    rels = [paths.FIGURES, paths.CASE_DOC, paths.RUBRIC_COPY, paths.SCOPE]
    rels += [evidence.relpath(ev) for ev in result.settlement.pages]
    return {rel: manifest.get(rel) for rel in rels}


def _manifest(case_dir: Path) -> dict:
    with _reading(None):
        return digest.build_manifest(case_dir)


def to_json_bytes(result: FinanceResult, case_dir, *, manifest: "dict | None" = None) -> bytes:
    """finance.json's bytes: sorted keys, no timestamp, money as strings, so the same files always
    give the same bytes. `inputs` comes from `manifest` (the judge-input digests taken before compute;
    None: taken now). The review reads it. It is never an input to the arithmetic: save-report and
    rederive compute everything again; other code reads it only to check it is current or to copy it
    into the funding snapshot."""
    case_dir = Path(case_dir)
    manifest = _manifest(case_dir) if manifest is None else manifest
    with _reading(paths.RUBRIC_COPY):
        rub = rubric.load_rubric(case_dir / paths.RUBRIC_COPY)
    with _reading(paths.SCOPE):
        applicable = set(case_files.read_scope(case_dir)["applicable_item_ids"])
    s, b = result.settlement, result.settlement.basis
    anchors = {id(m): a for m, a in zip(s.amounts, amount_anchors(s.amounts))}
    data = {
        "inputs": _input_digests(result, manifest),
        "decisions_bytes": result.decisions_bytes,
        "basis": {"rate": _money(b.rate), "horizon": b.horizon, "currency": b.currency,
                  "start_month": b.start_month, "cost_assumptions": b.cost_assumptions,
                  "complete": b.complete, "unparsed": list(b.unparsed)},
        "figures": {fig_id: {"state": s.live[fig_id]["status"], "counts": st.counts, "settled": st.settled,
                             "grade": st.grade, "reason": None if st.reason is None else plain_reason(st.reason),
                             "run_rate": figures.is_run_rate(s.live[fig_id], s.recorded())}
                    for fig_id, st in s.states.items()},
        "scenarios": {name: _scenario_json(r) for name, r in result.scenarios.items()},
        "cautious": _scenario_json(result.cautious),
        "ceiling": {"value": result.ceiling, "reason": result.ceiling_reason},
        "code_findings": [{k: f[k] for k in ("id", "job", "anchor", "target", "item_id")}
                          for f in code_findings(result, rub, applicable)],
        "uncovered_amounts": [{"anchor": anchors[id(m)], "section": m.section, "sentence": m.sentence,
                               "written": m.written} for m in s.uncovered_settled],
        "largest_revenue": largest_revenue(result),
    }
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write_finance_json(case_dir) -> Path:
    """Take the judge-input manifest, compute on the live case with decisions.jsonl and figures.jsonl
    cut at the manifest's lengths, and write finance.json atomically, its `inputs` from that manifest.
    Only the judge's inputs are read. Only `bc.py brief` calls this, under the decisions lock (ruling
    P3-03); write_brief then refuses when its own manifest differs from what finance.json records, so
    a change made during or after compute is caught."""
    case_dir = Path(case_dir)
    manifest = _manifest(case_dir)
    decisions = manifest.get(paths.DECISIONS, {}).get("bytes", 0)
    figs = manifest.get(paths.FIGURES, {}).get("bytes", 0)
    result = compute(case_dir, decisions_upto=decisions, figures_upto=figs)
    data = to_json_bytes(result, case_dir, manifest=manifest)
    path = case_dir / paths.FINANCE
    with _reading(paths.FINANCE):
        case_files._atomic_write(path, data)
    return path
