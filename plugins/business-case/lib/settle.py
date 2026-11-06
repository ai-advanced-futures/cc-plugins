"""Which figures count, which are settled, and which money amounts no figure covers.

Spec §4 "When a figure counts", "Exclusions" and "Complete"; §6 ceiling rule 2. Nothing here is
stored: every state is derived from figures.jsonl and decisions.jsonl (each cut at a byte length) and
today's business-case.md and evidence pages.

A cash or terminal figure counts when it is confirmed, it passes its re-check (checks 2 to 6, 9,
11 and 12) against today's files, and it is not an estimate, or the funder approved its (item, page) pair.
It is settled when it counts. A non-cash figure never counts; it is settled when it is confirmed
and passes its re-check, and a judgment exclusion (figures.is_judgment_exclusion: an excluded
figure with no restates that is not a run rate) also needs the funder's approval. A run rate is
never cash and settles on the person's confirmation alone.

Coverage is per occurrence: a figure quotes (section, sentence, position), and that occurrence
covers ONE money amount, the first in the case with that position in that sentence (Task 5 carry).
A sentence written twice in the same words in one section is a copy (`written_twice`): its second
copy stays uncovered until the person removes or rewords one copy, and code never guesses which.
An unreadable amount is never covered. `amounts_no_figure_records` is the one public list of the
amounts no figure records.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from lib import amounts, basis, case_doc, figures, loop_end, paths

# An "unproposed" reason: no valid proposal exists yet, so the funder was never asked (Task 17).
REASONS = {
    "unconfirmed": "not confirmed",
    "estimate_unproposed": "an estimate not yet proposed to the funder",
    "estimate_pending": "an estimate the funder has not approved",
    "estimate_rejected": "an estimate the funder rejected",
    "exclusion_unproposed": "an exclusion not yet proposed to the funder",
    "exclusion_pending": "an exclusion the funder has not approved",
    "exclusion_rejected": "an exclusion the funder rejected",
    "recheck": "no longer supported by the case: {cause}",
}


@dataclass(frozen=True)
class FigureState:
    id: str
    counts: bool
    settled: bool
    grade: str
    reason: str | None


@dataclass(frozen=True)
class Settlement:
    basis: basis.Basis
    live: dict                  # figure ID -> the live figure, as figures.figures gives it
    states: dict                # figure ID -> FigureState, for every live figure
    amounts: tuple              # every MoneyAmount in the money sections, in the scan's order
    uncovered_confirmed: tuple  # amounts no confirmed figure covers (a judgment exclusion only when approved)
    uncovered_settled: tuple    # amounts no settled figure covers
    pages: tuple                # the evidence IDs of the live figures, sorted: the pages read to grade and re-check
    superseded: dict            # figure ID -> each superseded figure, under the same figures cut as `live`

    def recorded(self) -> dict:
        """Every recorded figure by ID, live or superseded: what figures.is_run_rate walks back through."""
        return {**self.superseded, **self.live}


def _read_case(case_dir: Path) -> tuple:
    """business-case.md's text and its sections; a file that cannot be read is check 4's refusal."""
    try:
        text = (case_dir / paths.CASE_DOC).read_text(encoding="utf-8")
        return text, case_doc.parse_sections(text)
    except (OSError, UnicodeDecodeError, case_doc.CaseDocError) as exc:
        raise figures.FigureRefused(f"check 4: cannot read {paths.CASE_DOC}: {exc}") from exc


def _sections(case_dir: Path) -> dict:
    return _read_case(case_dir)[1]


def _grade(case_dir: Path, fig: dict) -> str:
    """The figure's grade. A page that cannot be read already fails the re-check (check 6); its
    grade is then `estimated`, the grade that needs the most."""
    try:
        return figures.grade(case_dir, fig)
    except figures.FigureRefused:
        return "estimated"


def _exclusion_answer(fig_id: str, answers: loop_end.FinanceAnswers) -> str:
    """The funder's recorded answer on an exclusion (`approved`, `rejected` or `pending`), or
    `unproposed` when none was proposed. The one place the default lives."""
    return answers.exclusions.get(fig_id, ("unproposed", None))[0]


def _state(fig: dict, *, grade: str, problem, answers: loop_end.FinanceAnswers,
           exclusion: str, recorded: dict) -> FigureState:
    """Spec §4 and §6 rule 2. `reason` is the first that holds, in REASONS' order of checking.
    `exclusion` is `_exclusion_answer`'s result, worked out once by the caller; `recorded` maps every
    recorded figure by ID (a correction of a run rate is a run rate)."""
    pair = (fig["item_id"], fig["evidence"])
    cash = fig["kind"] in figures.NPV_KINDS
    if fig["status"] != "confirmed":
        reason = REASONS["unconfirmed"]
    elif problem is not None:
        reason = REASONS["recheck"].format(cause=problem)
    elif cash and grade == "estimated" and pair not in answers.approved:
        reason = REASONS["estimate_rejected" if pair in answers.rejected
                         else "estimate_pending" if pair in answers.proposed else "estimate_unproposed"]
    elif figures.is_judgment_exclusion(fig, recorded) and exclusion != "approved":
        reason = REASONS[f"exclusion_{exclusion}"]
    else:
        reason = None
    settled = reason is None
    return FigureState(fig["id"], cash and settled, settled, grade, reason)


def _uncovered(found: list, covered: set) -> tuple:
    """The amounts no occurrence in `covered` covers. Each occurrence covers one amount only."""
    used, out = set(), []
    for m in found:
        key = (m.section, m.sentence, m.position)
        if m.value is not None and key in covered and key not in used:
            used.add(key)
            continue
        out.append(m)
    return tuple(out)


def amounts_no_figure_records(found: Sequence[amounts.MoneyAmount], live: dict) -> tuple:
    """The amounts no occurrence of any live figure covers, in scan order. A figure that does not
    count yet still covers its amount. Pure: it reads no file and no decisions.jsonl."""
    return _uncovered(list(found), {o for f in live.values() for o in figures.occurrences(f)})


def written_twice(found: Sequence[amounts.MoneyAmount]) -> frozenset:
    """The id() of each amount whose (section, sentence, position) an earlier amount in `found` has:
    every copy after the first of a sentence written twice in the same words in one section."""
    seen, out = set(), set()
    for m in found:
        key = (m.section, m.sentence, m.position)
        if key in seen:
            out.add(id(m))
        seen.add(key)
    return frozenset(out)


def left_uncovered(case_dir, refused: set) -> list:
    """What a figure run left uncovered (spec 0.4.0 item 2): `<section heading>: <written>` for each
    amount no live figure records, leaving out a written-twice copy and an unreadable amount (the
    financial view names each), and an amount at an occurrence in `refused` (a refused proposal of
    the run quoted it, and its refusal names it). Raises figures.FigureRefused when business-case.md
    or the figures file cannot be read."""
    case_dir = Path(case_dir)
    text, sections = _read_case(case_dir)
    headings = case_doc.headings(text)
    found = amounts.money_amounts(sections, basis.basis_of_sections(sections).currency)
    live = {i: f for i, f in figures.figures(case_dir).items() if f["status"] != "superseded"}
    copies = written_twice(found)
    return [" ".join(f"{headings.get(m.section, 'the case')}: {m.written}".split())  # one line each
            for m in amounts_no_figure_records(found, live)
            if not m.unreadable and id(m) not in copies and (m.section, m.sentence, m.position) not in refused]


def settle(case_dir, *, decisions_upto: int | None, figures_upto: int | None = None) -> Settlement:
    """The live figures' states and the coverage, with decisions.jsonl cut at `decisions_upto`
    bytes and figures.jsonl at `figures_upto` bytes (None: the whole file). Raises figures.FigureRefused for a figures file or a
    business-case.md that cannot be read; decision_record.DecisionRefused for a decisions file
    that cannot be read."""
    case_dir = Path(case_dir)
    every = figures.figures(case_dir, figures_upto)
    live = {i: f for i, f in every.items() if f["status"] != "superseded"}
    superseded = {i: f for i, f in every.items() if f["status"] == "superseded"}
    sections = _sections(case_dir)
    case_basis = basis.basis_of_sections(sections)
    answers = loop_end.finance_answers(case_dir, decisions_upto, figures_upto)

    states, by_confirmed, by_settled = {}, set(), set()
    for fig_id, fig in live.items():
        problem = figures.recheck(case_dir, fig, live=live, superseded=superseded, basis=case_basis,
                                  sections=sections)
        exclusion = _exclusion_answer(fig_id, answers)
        st = _state(fig, grade=_grade(case_dir, fig), problem=problem, answers=answers, exclusion=exclusion,
                    recorded=every)
        states[fig_id] = st
        occurrences = set(figures.occurrences(fig))
        if fig["status"] == "confirmed" and (exclusion == "approved"
                                             or not figures.is_judgment_exclusion(fig, every)):
            by_confirmed |= occurrences
        if st.settled:
            by_settled |= occurrences

    found = amounts.money_amounts(sections, case_basis.currency)
    return Settlement(case_basis, live, states, tuple(found), _uncovered(found, by_confirmed),
                      _uncovered(found, by_settled), tuple(sorted({f["evidence"] for f in live.values()})),
                      superseded)
