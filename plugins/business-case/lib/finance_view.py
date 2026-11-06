"""The financial view (finance-view.md): the funder's read-only view of the numbers (spec §6 "What
the funder sees").

Code writes this file and nobody edits it. It is not a judge input: the financial figures file and
finance.json are. Every string here is in the funder's words: the plain grade names, the verdict as
"supported", "not yet determined" or "not supported", "independent review", and no rubric ID, check
number, file name or raw section key (plan 3 Task 17; Task 10 ruling on plain reasons).

Every reason is rendered as its source gives it (settle, finance, basis) and rewritten nowhere (Task 17
fix round 1), so finance.json and the view always say the same. One status keys on a reason: a run
rate (figures.is_run_rate: the extractor's exact reason, or a correction of a run rate) gets
RUN_RATE_STATUS in "What the case leaves out", as finance.json's `run_rate` says (spec 0.4.0 item 1).

Nothing at module level reads an attribute of finance or settle (Global Constraints, ruling P3-04):
every such read happens inside a function.
"""
from __future__ import annotations

import decimal
from decimal import Decimal
from pathlib import Path

from lib import basis, case_files, evidence, figures, finance, paths, settle

GRADE_NAMES = {"primary": "from your own source", "secondary": "from a published source",
               "estimated": "an estimate"}
VERDICT_NAMES = {"supported": "supported", "undetermined": "not yet determined", "not_supported": "not supported"}
ROI_FORMULA = "ROI = (total cash in − total cash out) ÷ total cash out, not discounted"
FUNDER_EXPLAINED = "The funder is the person who decides whether to fund this offering."
COUNTS_SETTLED = ("Each scenario's numbers count only settled figures: figures the person confirmed and, where "
                  "they need it, the funder approved.")
CAUTIOUS = "Counting every recorded cost, and only the income a person settled:"
RUN_RATE_STATUS = "a run rate: a rate the case states at a point in time; it is not cash"
CAUTIOUS_LEFT_OUT = ("These numbers also count, as money going out, every amount marked to leave out that the "
                     "funder has not approved:")
NO_SETTLED = "No settled figures yet, so no numbers are counted for this scenario."
NO_FIGURES_OF_ITS_OWN = ("This scenario has no confirmed figures of its own, so its numbers would be the base "
                         "case's. No numbers are shown for it.")
# Operator decision 2026-10-29: said when the offering's own cash never pays back (finance.own_cash_short).
OWN_CASH_SHORT = ("The offering's own cash, including what it is worth at the end, does not pay back what it "
                  "spends. These numbers do not count value to the rest of the business, such as keeping "
                  "existing customers or drawing them to other products. A funder may still choose to fund it "
                  "for that reason.")
NO_HORIZON = "not computed: the case states no horizon that can be read, so there is no period to add the cash over"
NO_TERMINAL = "none, as no terminal value counts"
NO_FIGURES = "No figure is recorded yet."
NONE_LEFT_OUT = "No figure marks an amount to leave out."
UNCOVERED_HEADING = "## Amounts no figure records"
UNCOVERED_INTRO = ("Each amount below is written in the case, but no figure records it yet, so the numbers above "
                   "do not count it:")
ALL_COVERED = "Every money amount in the case has a recorded figure."
# 0.4.0 items 2 and 4: the marks on an amount no figure records (unreadable, then written twice). An
# unreadable copy takes the unreadable mark only.
WRITTEN_TWICE_MARK = "(written twice in the same words)"
UNREADABLE_MARK = "(code cannot read this amount; rewrite it in the case)"
NPV_NOT_ABOVE_ZERO = "none, as NPV is not above zero"

_HEADER = "Code writes this file from the financial figures file. Do not edit it. Run bc.py compute to rebuild it."
_REVIEW = ("The numbers are the base scenario's. A figure of any scenario that does not count yet keeps the verdict "
           "from reading supported. The independent review reads the case and these numbers and gives the verdict. "
           "It cannot give a verdict higher than the one shown here.")
_CENT = Decimal("0.01")
_TENTH = Decimal("0.1")


def _id_order(fig_id: str) -> tuple:
    return (len(fig_id), fig_id)


def _by_number(fig: dict) -> tuple:
    return _id_order(fig["id"])


def _one_line(text) -> str:
    """The text on one line, so a line break in it cannot add a heading or an entry to the view."""
    return " ".join(str(text).split())


def _sentence(text) -> str:
    """The text on one line, ending with a full stop (or ! or ?)."""
    text = _one_line(text)
    return text if text.endswith((".", "!", "?")) else f"{text}."


def money(x: Decimal, currency) -> str:
    """Two decimals, thousands grouped, with the currency code first."""
    with decimal.localcontext(basis.CONTEXT):
        q = Decimal(x).quantize(_CENT, rounding=decimal.ROUND_HALF_UP)
    if q == 0:
        q = Decimal("0.00")
    text = f"{q:,.2f}"
    return f"{currency} {text}" if currency else f"{text} (no currency stated)"


def share(x: Decimal, limit: "Decimal | None" = None) -> str:
    """x as a percentage to one place. Against a limit it never rounds onto the limit: a share
    below it is cut down, and a share above it that would print at or below it takes
    finance.above_percent (the Task 11 rule)."""
    rounding = decimal.ROUND_DOWN if limit is not None and x < limit else decimal.ROUND_HALF_UP
    with decimal.localcontext(basis.CONTEXT):
        shown = (x * 100).quantize(_TENTH, rounding=rounding)
    if limit is not None and x > limit and shown <= limit * 100:
        return finance.above_percent(x, limit)
    return f"{shown}%"


def _grades(total, limit: Decimal) -> str:
    if not total.shares:
        return "no amounts to grade"
    parts = [f"{GRADE_NAMES[g]} {share(total.shares[g], limit if g == 'estimated' else None)}"
             for g in evidence.GRADES if g in total.shares]
    return f"{', '.join(parts)}; lowest grade: {GRADE_NAMES[total.lowest_grade]}"


def _amount_line(name: str, total, currency, limit: Decimal) -> str:
    return f"- {name}: {money(total.value, currency)}. Grades: {_grades(total, limit)}."


def _payback_words(payback) -> str:
    return f"month {payback}" if isinstance(payback, int) else str(payback)


def _payback(res, limit: Decimal) -> str:
    if res.payback is None:
        return f"- Payback: not computed: {res.why_not}."
    grades = f" Grades of the cash in the horizon: {_grades(res.cumulative, limit)}."
    if isinstance(res.payback, int):
        return f"- Payback: month {res.payback}, not discounted.{grades}"
    return f"- Payback: {res.payback}.{grades}"


def _roi(res, limit: Decimal, horizon) -> str:
    if horizon is None:
        return f"- ROI: {NO_HORIZON}. {ROI_FORMULA}."
    if res.roi.value is None:
        return f"- ROI: not computable, as there is no cash out. {ROI_FORMULA}."
    return f"- ROI: {share(res.roi.value)}. {ROI_FORMULA}. Grades: {_grades(res.roi, limit)}."


def _counted(result, name: str) -> list:
    """The cash figures that count in this scenario, as compute counts them."""
    s = result.settlement
    counts = {fig_id for fig_id, st in s.states.items() if st.counts}
    return [f for f in finance.scenario_figures(s.live, name, counts)
            if f["id"] in counts and f["kind"] in figures.NPV_KINDS]


def _terminal(result, name: str, res, limit: Decimal) -> str:
    """The terminal value's share of NPV, or which of its two causes leaves none (review M7)."""
    if res.terminal_share is not None:
        return f"- The terminal value's share of NPV: {share(res.terminal_share, limit)}."
    if not any(f["kind"] == "terminal_value" for f in _counted(result, name)):
        return f"- The terminal value's share of NPV: {NO_TERMINAL}."
    return f"- The terminal value's share of NPV: {NPV_NOT_ABOVE_ZERO}."


def _years(res, currency, limit: Decimal) -> list:
    if not res.years:
        return ["- Revenue by year: no full year in the horizon."]
    out = ["- Revenue by year:"]
    for n, (total, grow) in enumerate(zip(res.years, res.growth), 1):
        if n == 1:
            why = "growth: none, as it is the first year"
        elif grow is None:
            why = "growth: not computable, as the year before has no revenue"
        else:
            why = f"growth: {share(grow)}"
        out.append(f"  - Year {n}: {money(total.value, currency)}; {why}. Grades: {_grades(total, limit)}.")
    return out


def _cautious(result) -> "str | None":
    """The base scenario's cautious NPV and payback (ceiling rule 1), when they differ from the
    counted ones (review I1), so a verdict they decide sits beside them."""
    cautious, base = result.cautious, result.scenarios[figures.BASE]
    if cautious.npv is None:
        return None
    if base.npv is not None and (cautious.npv.value, cautious.payback) == (base.npv.value, base.payback):
        return None
    currency, limit = result.settlement.basis.currency, result.limit
    left_out = finance.cautious_exclusions(result.settlement)
    named = f" {CAUTIOUS_LEFT_OUT} {_ids(sorted(left_out, key=_id_order))}." if left_out else ""
    return (f"- {CAUTIOUS} NPV {money(cautious.npv.value, currency)}, payback {_payback_words(cautious.payback)}."
            f"{named} Grades: {_grades(cautious.npv, limit)}.")


def _scenario(result, name: str, res) -> str:
    lines = [f"## Scenario: {_one_line(name)}", ""]
    base = name == figures.BASE
    if not _counted(result, name):
        lines.append(NO_SETTLED if base else NO_FIGURES_OF_ITS_OWN)
        cautious = _cautious(result) if base else None
        if cautious:
            lines.append(cautious)
        return "\n".join(lines)
    if not base and not any(f["scenario"] == name for f in _counted(result, name)):
        lines.append(NO_FIGURES_OF_ITS_OWN)
        return "\n".join(lines)
    currency, limit, horizon = result.settlement.basis.currency, result.limit, result.settlement.basis.horizon
    if res.npv is None:
        lines.append(f"- NPV: not computed: {res.why_not}.")
    else:
        lines.append(_amount_line("NPV", res.npv, currency, limit))
        lines.append(_terminal(result, name, res, limit))
    lines.append(_payback(res, limit))
    if horizon is None:
        lines.append(f"- Cumulative net cash: {NO_HORIZON}.")
    else:
        lines.append(_amount_line("Cumulative net cash", res.cumulative, currency, limit))
    lines.append(_roi(res, limit, horizon))
    lines.extend(_years(res, currency, limit))
    if base:
        cautious = _cautious(result)
        if cautious:
            lines.append(cautious)
    return "\n".join(lines)


def _basis_block(result) -> str:
    b = result.settlement.basis
    lines = ["## The basis", ""]
    if b.complete:
        lines.append(f"Discount rate: {share(b.rate)} a year. Horizon: {b.horizon} months. Currency: {b.currency}. "
                     f"Start month: {b.start_month}.")
    else:
        lines.append("The financial basis is incomplete:")
        lines.extend(f"- {_one_line(r)}" for r in b.unparsed)
    return "\n".join(lines)


def _counts_block(result) -> str:
    s = result.settlement
    n = sum(1 for st in s.states.values() if not st.settled)
    if not s.states:
        return f"{COUNTS_SETTLED} {NO_FIGURES}"
    if n == 0:
        return f"{COUNTS_SETTLED} Every figure is settled."
    figs = "1 figure does" if n == 1 else f"{n} figures do"
    return f"{COUNTS_SETTLED} {figs} not count yet; see “Figures that do not count yet”."


def _why(result, fig_id: str) -> str:
    return finance.plain_reason(result.settlement.states[fig_id].reason)


def _verdict(result) -> str:
    lines = ["## The verdict", "", _REVIEW, "",
             f"How high the verdict can go: {VERDICT_NAMES[result.ceiling]}, because "
             f"{_one_line(result.ceiling_reason)}."]
    if finance.own_cash_short(result):
        lines += ["", OWN_CASH_SHORT]
    return "\n".join(lines)


def _ids(fig_ids) -> str:
    ids = list(fig_ids)
    return ids[0] if len(ids) == 1 else f"{', '.join(ids[:-1])} and {ids[-1]}"


def _exclusion_status(result, fig: dict) -> str:
    if figures.is_run_rate(fig, result.settlement.recorded()):
        settled = result.settlement.states[fig["id"]].settled
        return f"{RUN_RATE_STATUS}, and {'the person confirmed it' if settled else _why(result, fig['id'])}"
    if not result.settlement.states[fig["id"]].settled:
        return _why(result, fig["id"])
    if fig.get("restates"):
        return f"it repeats {_ids(fig['restates'])}, and the person confirmed it"
    return "the funder approved leaving it out"


def _scenario_note(fig: dict) -> str:
    return "" if fig["scenario"] == figures.BASE else f", {_one_line(fig['scenario'])} scenario"


def _exclusions(result) -> str:
    live = result.settlement.live
    excluded = [f for f in sorted(live.values(), key=_by_number) if f["kind"] == "excluded"]
    lines = ["## What the case leaves out", ""]
    if not excluded:
        lines.append(NONE_LEFT_OUT)
    for f in excluded:
        lines.append(f"- {f['id']} ({_one_line(f['line'])}{_scenario_note(f)}): "
                     f"{money(Decimal(f['amount']), f['currency'])}. Why it is left out: {_sentence(f['reason'])} "
                     f"Status: {_exclusion_status(result, f)}.")
    return "\n".join(lines)


def _not_counting(result) -> str:
    s = result.settlement
    waiting = [f for f in sorted(s.live.values(), key=_by_number) if not s.states[f["id"]].settled]
    lines = ["## Figures that do not count yet", ""]
    if not s.live:
        lines.append(NO_FIGURES)
    elif not waiting:
        lines.append("Every figure is settled.")
    for f in waiting:
        lines.append(f"- {f['id']} ({_one_line(f['line'])}{_scenario_note(f)}): {_why(result, f['id'])}.")
    return "\n".join(lines)


def _uncovered(result) -> str:
    """Every money amount no recorded figure quotes, each with its section's heading and the amount
    as written (final review I3; the verdict names only the first). One definition (re-review N1): an
    amount a live figure quotes shows only under that figure, whose reason routes it, even while the
    figure does not count yet. One occurrence covers one amount, as settle counts coverage. An amount
    code cannot read, and the second copy of a sentence written twice, carry a mark that says so."""
    s = result.settlement
    found = settle.amounts_no_figure_records(s.amounts, s.live)
    lines = [UNCOVERED_HEADING, ""]
    if not found:
        lines.append(ALL_COVERED)
        return "\n".join(lines)
    lines.append(UNCOVERED_INTRO)
    copies = settle.written_twice(s.amounts)
    for m in found:
        heading = _one_line(result.headings.get(m.section, "the case"))
        mark = (f" {UNREADABLE_MARK}" if m.unreadable else f" {WRITTEN_TWICE_MARK}" if id(m) in copies else "")
        lines.append(f"- {heading}: {_one_line(m.written)}, in “{_one_line(m.sentence)}”{mark}")
    return "\n".join(lines)


def render(case_dir, result: "finance.FinanceResult") -> str:
    offering = case_files.offering(Path(case_dir))
    blocks = [f"# Financial view: {_one_line(offering)}", _HEADER, FUNDER_EXPLAINED, _basis_block(result),
              _counts_block(result)]
    blocks += [_scenario(result, name, res) for name, res in result.scenarios.items()]
    blocks += [_verdict(result), _exclusions(result), _not_counting(result), _uncovered(result)]
    return "\n\n".join(blocks) + "\n"


def write_view(case_dir) -> Path:
    """Compute on the whole case and write finance-view.md atomically."""
    case_dir = Path(case_dir)
    path = case_dir / paths.FINANCE_VIEW
    case_files._atomic_write(path, render(case_dir, finance.compute(case_dir, decisions_upto=None)).encode("utf-8"))
    return path
