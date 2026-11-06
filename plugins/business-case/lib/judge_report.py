"""The judge report: validate the judge's reply against its brief, assign finding IDs, save it.

The reply is the judge's JSON at the reply_path its brief names (ADR-006). Code checks it against
the brief's manifest, the case's rubric and scope, the evidence pages and, for a judge reply, the
receipt of the judge's Write. Code, not the judge, assigns each finding's ID, from the job, the
target kind and an anchor code derives: the item ID for a missing item, the paragraph's text for a
claim, the ref or key for a whole-plan target. The item is not in the ID (ADR-008). Code also adds a
whole-plan finding for each absent category, unsupported condition and orphaned condition, and,
from the finances (finance.code_findings), an `amount` finding for each uncovered money amount and an
`investment` finding for each total whose share from estimates is above the limit. The saved report is judge/report-NNN.json, marked "written_by": "judge", or "coach-copy" for the fallback.

Rule 5 has one exception (spec §7): a met on an item the rubric marks computed cites finance.json,
plus the evidence pages its met test asks for (only an item that also needs inputs stated, as
BC-SCENARIOS' sensitivity inputs), each checked as any cited page. The brief must have included
finance.json, and code's result must hold what the met test names (finance.computed_item_problem).
No other item may cite finance.json.

Rule 10, the verdict: the reply's investment_verdict is at or below the ceiling code computes again
here (finance.compute, with decisions.jsonl and figures.jsonl cut where the brief read them; a
stored ceiling, finance.json's included, is never read), and verdict_rests_on names its reasons. A reply with neither key reads as undetermined with no
reasons and saves in the v0.2.0 shape, so a report saved before 0.3.0 keeps counting (spec §8).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from lib import (
    case_doc,
    case_files,
    clock,
    conditions,
    digest,
    evidence,
    finance,
    judge_brief,
    judge_receipt,
    paths,
    register,
    rubric,
)

JOBS = ("evidence", "completeness", "whole_plan", "investment")
TARGET_KINDS = ("claim", "missing_item", "register_entry", "condition", "category", "note", "plan", "amount", "total")
JOB_TARGETS = {"evidence": ("claim",), "completeness": ("missing_item", "amount"),
               "whole_plan": ("register_entry", "condition", "category", "note", "plan"), "investment": ("total",)}
ITEM_TARGETS = frozenset({"claim", "missing_item", "amount"})
# Only code adds a finding on these (finance.code_findings); a reply that gives one is refused.
CODE_ONLY_TARGETS = frozenset({"amount", "total"})
# The whole-plan tests a finding about the plan as a whole names (ruling N-2).
PLAN_REFS = ("rumelt-goals", "rumelt-fluff", "rumelt-no-focus", "martin-opposite", "eliminates-work")
STATUSES = ("met", "not_met")
WRITTEN_BY = ("judge", "coach-copy")
# A literal, never read from finance at import time (the import cycle, ruling P3-04); a test pins it
# equal to finance.CEILING_ORDER.
VERDICTS = ("supported", "undetermined", "not_supported")
VERDICT_KEYS = frozenset({"investment_verdict", "verdict_rests_on"})
NO_VERDICT = "undetermined"  # what a reply with neither verdict key reads as (spec §8)
_VERDICT_FIELDS = ("investment_verdict", "verdict_rests_on", "investment_ceiling")

# The fixed summaries of the findings code adds (ruling N-1).
REQUIRED_SUMMARIES = {
    "category": "The register has no stated or confirmed entry in the category {title}.",
    "unsupported": "Condition {ref} is marked unsupported: no evidence shows that it holds.",
    "orphaned": "Condition {ref} supports {supports}, which is superseded, so it supports no live choice.",
}

NO_REPLY = "no judge reply"
RUN_JUDGE_AGAIN = "run the judge again with a new brief"
COPY_IN_CASE = "is inside a business-case folder"
SESSION_NOT_CURRENT = "the judge's reply is from another session"
# A strategy file that cannot be read: the problem comes first, and the refusal never says to run
# the judge again, since a new run cannot pass until the file is repaired (rulings I-3, N-5).
STRATEGY_FILE_BROKEN = "a strategy file cannot be read"
# A file the finances read that cannot be read (figures.jsonl, an evidence page, business-case.md or
# decisions.jsonl): the same rule, and this problem comes first (review I9).
FIGURES_FILE_BROKEN = "a file the numbers come from cannot be read"
REPAIR_FILE = "repair the file, then write a new brief"
# A report saved before 0.3.0 lists no finance.json in its manifest: no funding decision rests on it.
READ_NO_FINANCE = f"the latest independent review read no {paths.FINANCE}"
REPAIR_STRATEGY_FILE = REPAIR_FILE
_BROKEN = (FIGURES_FILE_BROKEN, STRATEGY_FILE_BROKEN)  # in the order a refusal names them

_TOP_KEYS = frozenset({"manifest_digest", "items", "findings"})
_ITEM_KEYS = frozenset({"status", "evidence", "met_test_id"})
_FINDING_KEYS = frozenset({"job", "item_id", "target", "summary"})
_REF_KEYS = frozenset({"kind", "ref"})
_TARGET_KEYS = dict({"claim": frozenset({"kind", "section", "paragraph"})},
                    **{kind: _REF_KEYS for kind in TARGET_KINDS if kind != "claim"})
_NOT_A_PAGE = object()  # a cited ID that is not an evidence page of this case
_REPORT_NAME = re.compile(rf"^report-({judge_brief.NNN})\.json$")


class ReplyRefused(ValueError):
    """A judge reply or coach copy the rules refuse. The message names every problem."""

    def __init__(self, message: str, problems: list = None):
        super().__init__(message)
        self.problems = list(problems) if problems else [message]


def finding_id(job: str, target_kind: str, anchor: str) -> str:
    """The item is not in the ID: the judge's pick of an item for a claim does not change it."""
    return "F-" + hashlib.sha256("|".join((job, target_kind, anchor)).encode("utf-8")).hexdigest()[:10]


def report_relpath(nnn: int) -> str:
    return f"{paths.JUDGE_DIR}/report-{nnn:03d}.json"


def _case_sections(case_dir) -> dict:
    try:
        return case_doc.parse_sections((Path(case_dir) / paths.CASE_DOC).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, case_doc.CaseDocError) as exc:
        raise ReplyRefused(f"cannot read the case's sections: {exc}") from exc


def _once(read):
    """read(), called on the first use only; a refusal it raises is raised again on every use."""
    memo = []

    def get():
        if not memo:
            try:
                memo.append((read(), None))
            except ReplyRefused as exc:
                memo.append((None, exc))
        value, refused = memo[0]
        if refused is not None:
            raise refused
        return value
    return get


def claim_anchor(case_dir, section: str, paragraph: int, sections=None) -> str:
    """The anchor of the 1-based paragraph in a section of business-case.md. `sections`, when
    given, is a callable returning the parsed sections, so a caller with many claims parses once."""
    if not isinstance(section, str):
        raise ReplyRefused(f"claim section {section!r} is not a section key")
    sections = sections() if sections is not None else _case_sections(case_dir)
    if section not in sections:
        raise ReplyRefused(f"claim section {section!r} is not a section of business-case.md")
    found = case_doc.paragraphs(sections[section])
    if isinstance(paragraph, bool) or not isinstance(paragraph, int) or not 1 <= paragraph <= len(found):
        raise ReplyRefused(f"claim paragraph {paragraph!r} is not a paragraph of section {section} "
                           f"(it has {len(found)})")
    return case_doc.paragraph_anchor(section, found[paragraph - 1])


def _key_problems(obj: dict, allowed: frozenset, where: str) -> list:
    out = []
    missing, extra = sorted(allowed - set(obj)), sorted(set(obj) - allowed)
    if extra:
        out.append(f"{where} has key(s) beyond the reply shape: {', '.join(map(str, extra))}")
    if missing:
        out.append(f"{where} is missing key(s): {', '.join(missing)}")
    return out


def _brief_parts(case_dir, brief_path) -> tuple:
    """(resolved case dir, NNN, manifest, reply path) for a brief of this case."""
    case_dir = Path(case_dir).resolve()
    try:
        nnn = judge_brief.brief_number(brief_path)
        brief_case, manifest, reply_path = judge_brief.read_brief(brief_path)
    except (OSError, ValueError) as exc:
        raise ReplyRefused(f"the brief cannot be read: {exc}") from exc
    if Path(brief_case).resolve() != case_dir or Path(brief_path).resolve().parent != case_dir / paths.JUDGE_DIR:
        raise ReplyRefused(f"{brief_path} is not a brief of the case at {case_dir}")
    return case_dir, nnn, manifest, Path(reply_path)


class _Strategy:
    """What the whole-plan rules read from the three strategy files, read once per check."""

    def __init__(self, case_dir: Path):
        self.entries = register.entries(case_dir)
        self.note_ids = {n["id"] for n in register.notes(case_dir)}
        self.absent = register.absent_categories(case_dir)
        self.conditions = conditions.conditions(case_dir)
        self.required = conditions.required_states(case_dir)


def _read_strategy(case_dir: Path) -> tuple:
    """(_Strategy or None, problems). A file that cannot be read is one problem that starts with
    STRATEGY_FILE_BROKEN; it never raises out of the check."""
    try:
        return _Strategy(case_dir), []
    except register.RegisterRefused as exc:
        return None, [f"{STRATEGY_FILE_BROKEN}: {exc}"]
    except conditions.ConditionRefused as exc:
        return None, [f"{STRATEGY_FILE_BROKEN}: {exc}"]


def _named(ref) -> str:
    return ref if isinstance(ref, str) else repr(ref)


def _whole_plan_problem(strategy: _Strategy, kind: str, ref) -> str | None:
    """Rule 7c: the problem with a whole-plan target's ref, or None. The anchor is the ref."""
    if kind in ("register_entry", "condition"):
        found = strategy.entries if kind == "register_entry" else strategy.conditions
        if not isinstance(ref, str) or ref not in found:
            what = "an entry of the register" if kind == "register_entry" else "a condition of the conditions list"
            return f"{_named(ref)} is not {what}"
        successor = found[ref]["superseded_by"]
        if successor is not None:
            return f"{ref} is superseded by {successor}; a finding targets a live one"
        return None
    if kind == "note":
        return None if isinstance(ref, str) and ref in strategy.note_ids else f"{_named(ref)} is not a note code counts"
    if kind == "plan":
        return None if ref in PLAN_REFS else f"plan ref {ref!r} is not one of {', '.join(PLAN_REFS)}"
    if ref not in register.CATEGORY_KEYS:  # a category, by its key
        key = next((k for k, title in register.CATEGORIES if title == ref), None)
        return f"{ref!r} is not a category key; " + (f"give the key {key}" if key else
                                                     f"the keys are {', '.join(register.CATEGORY_KEYS)}")
    if ref not in strategy.absent:
        return (f"category {ref} has a stated or confirmed entry; a category finding targets only "
                "a category with none")
    return None


def _required_findings(strategy: _Strategy) -> list:
    """Rule 6b: the whole-plan findings code adds, always, whatever the judge gave (ruling N-1).
    Each anchor carries the state, so a judge finding on the same target has another ID."""
    titles = dict(register.CATEGORIES)
    out = []
    for key in strategy.absent:
        out.append(("category", key, f"{key}|absent", REQUIRED_SUMMARIES["category"].format(title=titles[key])))
    for ref in sorted(strategy.required, key=lambda c: int(c.split("-", 1)[1])):
        state = strategy.required[ref]
        summary = REQUIRED_SUMMARIES[state].format(ref=ref, supports=strategy.conditions[ref]["supports"])
        out.append(("condition", ref, f"{ref}|{state}", summary))
    return [{"job": "whole_plan", "item_id": None, "target": {"kind": kind, "ref": ref}, "summary": summary,
             "anchor": anchor, "id": finding_id("whole_plan", kind, anchor)}
            for kind, ref, anchor, summary in out]


def _article(word: str) -> str:
    """The article for `word`: "an" before a vowel letter, else "a" (final review M5)."""
    return "an" if word[:1] in "aeiou" else "a"


def _check(case_dir: Path, nnn: int, manifest: dict, reply, *, check_current: bool = True) -> tuple:
    """(normalized report or None, problems). Applies the validation rules in order. With
    check_current False, rule 1 does not ask that the brief's inputs be unchanged (rederive)."""
    if not isinstance(reply, dict):
        return None, ["the reply is not a JSON object"]
    problems = _key_problems(reply, _TOP_KEYS | (VERDICT_KEYS & set(reply)), "the reply")  # rule 9, top level
    notes = []

    # Rule 1: written for this brief, and the brief's inputs are unchanged.
    want_digest = judge_brief.manifest_digest(manifest)
    if reply.get("manifest_digest") != want_digest:
        problems.append(f"manifest_digest {reply.get('manifest_digest')!r} is not this brief's ({want_digest}): "
                        "the reply was not written for this brief")
    current, stale = digest.is_current(manifest, case_dir) if check_current else (True, [])
    if not current:
        problems.append(f"the brief's inputs are no longer current; changed since the brief: {', '.join(stale)}")

    try:
        rub = rubric.load_rubric(case_dir / paths.RUBRIC_COPY)
        applicable = set(case_files.read_scope(case_dir)["applicable_item_ids"])
    except (OSError, ValueError, KeyError) as exc:
        return None, problems + [f"cannot read the case's rubric or scope: {exc}"]
    known = {i["id"]: i for i in rub["items"]}
    statement_ids = rubric.statement_item_ids(rub)
    computed_ids = rubric.computed_item_ids(rub)
    computed_mets = []  # met items code computes; their result is checked once compute has run
    strategy, strategy_problems = _read_strategy(case_dir)
    problems.extend(strategy_problems)
    sections = _once(lambda: _case_sections(case_dir))
    pages = {}  # evidence ID -> _cited_page's answer; each page is read once

    items = reply.get("items")
    if not isinstance(items, dict):
        problems.append("items is not an object")
        items = {}
    findings = reply.get("findings")
    if not isinstance(findings, list):
        problems.append("findings is not a list")
        findings = []

    # Rules 2 and 3 on item keys: unknown is refused, inapplicable is dropped with a note.
    kept_items = {}
    for iid, entry in items.items():
        if iid not in known:
            problems.append(f"item {iid} is not in the case's rubric")
        elif iid not in applicable:
            notes.append(f"dropped item {iid}: it does not apply to this case's scope")
        else:
            kept_items[iid] = entry

    # Rules 2 and 3 on findings, with the finding's own shape (rule 9). Rule 7b: a claim or a
    # missing item names its item; a whole-plan target names none, so the scope never drops it.
    kept_findings = []
    for n, f in enumerate(findings, 1):
        where = f"finding {n}"
        if not isinstance(f, dict):
            problems.append(f"{where} is not an object")
            continue
        problems.extend(_key_problems(f, _FINDING_KEYS, where))
        iid = f.get("item_id")
        target = f.get("target")
        kind = target.get("kind") if isinstance(target, dict) else None
        if kind in CODE_ONLY_TARGETS:
            problems.append(f"{where} targets {_article(kind)} {kind}: code adds those findings")
        elif kind in TARGET_KINDS and kind not in ITEM_TARGETS:
            if iid is not None:
                problems.append(f"{where} targets {_article(kind)} {kind}: its item_id must be null, not {iid!r}")
            else:
                kept_findings.append((n, f))
        elif iid is None and isinstance(target, dict) and kind not in TARGET_KINDS:  # the kind is wrong, not the item
            problems.append(f"{where} target kind {kind!r} is not one of {', '.join(TARGET_KINDS)}")
        elif iid is None:
            named = kind if kind in ITEM_TARGETS else "claim or missing_item"
            problems.append(f"{where} has no item_id; a {named} finding names its item")
        elif not isinstance(iid, str) or iid not in known:
            problems.append(f"{where} names item {iid!r}, which is not in the case's rubric")
        elif iid not in applicable:
            notes.append(f"dropped {where} ({f.get('job')} on {iid}): {iid} does not apply to this case's scope")
        else:
            kept_findings.append((n, f))

    # Rule 4: every applicable item has a status.
    for iid in sorted(applicable - set(items)):
        problems.append(f"applicable item {iid} has no entry in items")

    # Rule 5, with each item's shape (rule 9).
    out_items = {}
    for iid in sorted(kept_items):
        entry, where = kept_items[iid], f"item {iid}"
        if not isinstance(entry, dict):
            problems.append(f"{where} is not an object")
            continue
        problems.extend(_key_problems(entry, _ITEM_KEYS, where))
        status, cited, met_test_id = entry.get("status"), entry.get("evidence"), entry.get("met_test_id")
        if status not in STATUSES:
            problems.append(f"{where} status {status!r} is not one of {', '.join(STATUSES)}")
            continue
        if not isinstance(cited, list) or not all(isinstance(e, str) for e in cited):
            problems.append(f"{where} evidence is not a list of evidence IDs")
            continue
        if met_test_id is not None and not isinstance(met_test_id, str):
            problems.append(f"{where} met_test_id is not a string or null")
            continue
        page_ids = cited
        if status == "met" and iid in computed_ids:
            # Spec §7: a met on an item code computes cites finance.json, plus the evidence pages its
            # met test asks for: an item that also needs inputs stated (needs_code_arithmetic, the
            # sensitivity inputs of BC-SCENARIOS) may cite pages, each checked as any cited page.
            page_ids = [c for c in cited if c != paths.FINANCE]
            if cited.count(paths.FINANCE) != 1 or (page_ids and not known[iid]["needs_code_arithmetic"]):
                rest = " and the evidence pages its met test asks for" if known[iid]["needs_code_arithmetic"] \
                    else " and nothing else"
                problems.append(f"{where} is computed by code: a met cites {paths.FINANCE}{rest}")
                page_ids = []
            elif paths.FINANCE not in manifest:
                problems.append(f"{where} is met on {paths.FINANCE}, which the brief did not include")
            else:
                computed_mets.append(iid)
        elif status == "met" and not cited:
            problems.append(f"{where} is met but cites no evidence page")
        if status == "met":
            for ev_id in page_ids:
                if ev_id == paths.FINANCE:
                    problems.append(f"{where} cites {paths.FINANCE}: only an item code computes is met on "
                                    f"{paths.FINANCE}")
                    continue
                if ev_id not in pages:
                    pages[ev_id] = _cited_page(case_dir, ev_id)
                page = pages[ev_id]
                if page is _NOT_A_PAGE:
                    problems.append(f"{where} cites {ev_id}, which is not an evidence page of this case")
                    continue
                if isinstance(page, evidence.EvidenceRefused):
                    problems.append(f"{FIGURES_FILE_BROKEN}: {where} cites {ev_id}: {page}")
                    continue
                if not isinstance(page, dict) or iid not in (page.get("item_ids") or []):
                    problems.append(f"{where} cites {ev_id}, which does not list {iid}")
                    continue
                problem = evidence.case_source_problem(case_dir, page, statement_ids)
                if problem:
                    problems.append(f"{where} cites {ev_id}: {problem}")
            want_test = known[iid]["met_test"]["id"]
            if met_test_id != want_test:
                problems.append(f"{where} met_test_id {met_test_id!r} is not the rubric's {want_test}")
        out_items[iid] = {"status": status, "evidence": list(cited), "met_test_id": met_test_id}

    # The findings code adds from the finances, with decisions.jsonl and figures.jsonl cut where the
    # brief read them (0 bytes for a file the manifest lacks, as on a v0.2.0 brief), so a later answer
    # or figure never changes them (rederive gives the same). A file that cannot be read is one
    # problem that starts with FIGURES_FILE_BROKEN.
    decisions_upto = manifest.get(paths.DECISIONS, {}).get("bytes", 0)
    figures_upto = manifest.get(paths.FIGURES, {}).get("bytes", 0)
    try:
        result = finance.compute(case_dir, decisions_upto=decisions_upto, figures_upto=figures_upto)
        money = finance.code_findings(result, rub, applicable)
    except finance.FinanceRefused as exc:
        result, money = None, []
        problems.append(f"{FIGURES_FILE_BROKEN}: {exc}")

    # Rule 5 for the items code computes: the result the met test names is in what code computes
    # here, the same numbers as the finance.json the brief included. Code wins over the review: a
    # met on BC-FIGURES-COMPLETE beside a code-added `amount` finding is refused (Task 11 carry).
    for iid in computed_mets if result is not None else ():
        problem = finance.computed_item_problem(result, iid)
        if problem:
            problems.append(f"item {iid} is met, but {paths.FINANCE} does not hold its result: {problem}")

    # Rule 6: a not_met item has at least one finding, of either job, the code-added ones included
    # (ruling P3-43).
    on_item = {f.get("item_id") for _, f in kept_findings} | {f["item_id"] for f in money}
    on_item -= {None}  # a key-less finding is named by rule 9
    for iid, entry in out_items.items():
        if entry["status"] == "not_met" and iid not in on_item:
            problems.append(f"item {iid} is not_met and has no finding")

    # Rule 7: jobs and targets; code derives each anchor and ID.
    out_findings = []
    kept_ids = {}  # the 1-based number of a reply finding the save keeps -> its ID
    for n, f in kept_findings:
        where, iid, job, target = f"finding {n}", f.get("item_id"), f.get("job"), f.get("target")
        ok = True
        if job not in JOBS:
            problems.append(f"{where} job {job!r} is not one of {', '.join(JOBS)}")
            ok = False
        summary = f.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            problems.append(f"{where} summary is blank")
            ok = False
        if not isinstance(target, dict):
            problems.append(f"{where} target is not an object")
            continue
        kind = target.get("kind")
        if kind not in TARGET_KINDS:
            problems.append(f"{where} target kind {kind!r} is not one of {', '.join(TARGET_KINDS)}")
            continue
        if job in JOBS and kind not in JOB_TARGETS[job]:  # rule 7a
            problems.append(f"{where}: the {job} job does not take target kind {kind}; "
                            f"it takes {', '.join(JOB_TARGETS[job])}")
            continue
        shape = _key_problems(target, _TARGET_KEYS[kind], f"{where} target")
        if shape:
            problems.extend(shape)
            continue
        if kind == "missing_item":
            if target["ref"] != iid:
                problems.append(f"{where} missing_item ref {target['ref']!r} is not its item_id {iid}")
                continue
            anchor, clean_target = iid, {"kind": kind, "ref": iid}
        elif kind == "claim":
            try:
                anchor = claim_anchor(case_dir, target["section"], target["paragraph"], sections)
            except ReplyRefused as exc:
                problems.append(f"{where}: {exc}")
                continue
            clean_target = {"kind": kind, "section": target["section"], "paragraph": target["paragraph"]}
        else:
            if strategy is None:
                continue  # the strategy file problem is already named
            problem = _whole_plan_problem(strategy, kind, target["ref"])  # rule 7c
            if problem:
                problems.append(f"{where}: {problem}")
                continue
            anchor, clean_target = target["ref"], {"kind": kind, "ref": target["ref"]}
        if ok:
            out_findings.append({"job": job, "item_id": iid, "target": clean_target, "summary": summary,
                                 "anchor": anchor, "id": finding_id(job, kind, anchor)})
            kept_ids[n] = out_findings[-1]["id"]

    if strategy is not None:
        out_findings.extend(_required_findings(strategy))
    out_findings.extend(money)

    # Rule 8: no two findings share an ID, so one finding per job, target kind and anchor.
    seen = set()
    for f in out_findings:
        if f["id"] in seen:
            problems.append(f"two findings have the same ID {f['id']} ({f['job']} on {f['target']['kind']}, "
                            f"anchor {f['anchor']})")
        seen.add(f["id"])

    verdict, verdict_problems = _verdict(reply, result, kept_ids, money, len(findings))  # rule 10
    problems.extend(verdict_problems)

    report = {"brief": judge_brief.brief_relpath(nnn), "manifest_digest": want_digest,
              "manifest": manifest, "rubric_version": rub["version"], "notes": notes,
              "items": out_items, "findings": out_findings}
    report.update(verdict or {})
    return report, problems


def _verdict(reply: dict, result, kept_ids: dict, money: list, sent: int) -> tuple:
    """Rule 10: (the verdict fields to save, or None for a reply with neither key; problems).
    `result` is finance.compute's, None when a file it reads is broken (that problem is named).
    A reason is a 1-based number of a finding the save keeps, or the anchor of a finding code adds
    from the finances (`money`; never a plan-2 one, ruling P3-22). Each resolves to a finding ID."""
    given = VERDICT_KEYS & set(reply)
    if len(given) == 1:
        (has,), (lacks,) = given, VERDICT_KEYS - given
        return None, [f"the reply gives {has} without {lacks}; give both keys or neither"]
    verdict, rests_on = (reply["investment_verdict"], reply["verdict_rests_on"]) if given else (NO_VERDICT, [])
    problems, ids = [], []
    if verdict not in VERDICTS:
        problems.append(f"investment_verdict {verdict!r} is not one of {', '.join(VERDICTS)}")
    if not isinstance(rests_on, list):
        problems.append("verdict_rests_on is not a list")
        rests_on = []
    anchors = {f["anchor"]: f["id"] for f in money}
    for k, reason in enumerate(rests_on, 1):
        where = f"verdict_rests_on item {k} ({reason!r})"
        if isinstance(reason, bool) or not isinstance(reason, (int, str)):
            problems.append(f"{where} is not a finding number or an anchor")
        elif isinstance(reason, int) and not 1 <= reason <= sent:
            problems.append(f"{where} is not a finding of the reply: it has {sent} "
                            f"finding{'' if sent == 1 else 's'}, counted from 1")
        elif isinstance(reason, int) and reason not in kept_ids:
            problems.append(f"{where} points at finding {reason}, which the save drops or refuses")
        elif isinstance(reason, int):
            ids.append(kept_ids[reason])
        elif reason in anchors:
            ids.append(anchors[reason])
        else:
            problems.append(f"{where} is not the anchor of a finding code adds from the finances")
    if result is None or verdict not in VERDICTS:
        return None, problems
    level, ceiling = VERDICTS.index(verdict), VERDICTS.index(result.ceiling)
    if level < ceiling:
        problems.append(f"investment_verdict {verdict} is above the ceiling {result.ceiling} that code computes: "
                        f"{result.ceiling_reason}")
    elif level > ceiling and not rests_on:
        read = "" if given else " (a reply with neither verdict key reads as undetermined)"
        problems.append(f"investment_verdict {verdict} is below the ceiling {result.ceiling} with no reason{read}: "
                        "verdict_rests_on names no finding")
    if not given:
        return None, problems
    return {"investment_verdict": verdict, "verdict_rests_on": ids,
            "investment_ceiling": {"value": result.ceiling, "reason": result.ceiling_reason}}, problems


def _cited_page(case_dir, ev_id):
    """The cited page; _NOT_A_PAGE for an ID with no page file (the reply's error); or, for a page
    file read_page refuses (a hand-edited grade, bad JSON), the refusal itself: a file to repair,
    which a new judge run cannot fix."""
    try:
        return evidence.read_page(case_dir, ev_id)
    except evidence.EvidenceRefused as exc:
        try:
            present = evidence.page_path(case_dir, ev_id).is_file()
        except evidence.EvidenceRefused:
            present = False
        return exc if present else _NOT_A_PAGE


def validate_reply(case_dir, brief_path, reply: dict) -> dict:
    """The normalized report for a reply to this brief, or ReplyRefused naming every problem."""
    case_dir, nnn, manifest, _ = _brief_parts(case_dir, brief_path)
    report, problems = _check(case_dir, nnn, manifest, reply)
    if problems:
        raise ReplyRefused("; ".join(problems), problems)
    return report


def _run_again(problems: list) -> ReplyRefused:
    return ReplyRefused("; ".join(problems + [RUN_JUDGE_AGAIN]), problems)


def _refused(problems: list) -> ReplyRefused:
    """The refusal for a reply's problems. A file the numbers come from, then a strategy file, that
    cannot be read comes first and sends the coach to repair it, never to run the judge again: a new
    run cannot pass until the file is repaired (rulings I-3, N-5; review I9)."""
    ordered, broken = broken_first(problems)
    if not broken:
        return _run_again(problems)
    return ReplyRefused("; ".join(ordered + [REPAIR_FILE]), ordered)


def broken_first(problems: list) -> tuple:
    """(problems with every broken-file problem first, in _BROKEN's order; whether there is one)."""
    broken = [p for start in _BROKEN for p in problems if p.startswith(start)]
    return broken + [p for p in problems if p not in broken], bool(broken)


def needs_repair(problem) -> bool:
    """True when a refusal's message starts with a file that cannot be read: the remedy is
    REPAIR_FILE, never a new run (rulings I-3, N-5; review I9)."""
    return isinstance(problem, str) and problem.startswith(_BROKEN)


class _DuplicateKey(ValueError):
    pass


def _no_duplicate_keys(pairs: list) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise _DuplicateKey(key)
        out[key] = value
    return out


def _parse(data: bytes, where: str) -> tuple:
    """(reply, []) or (None, [problem]). A key given twice in one object is refused: plain JSON
    keeps the last one silently, which would hide a second answer from rule 9."""
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicate_keys), []
    except _DuplicateKey as exc:
        return None, [f"{where} repeats the key {exc.args[0]!r} in one object"]
    except (UnicodeDecodeError, ValueError) as exc:
        return None, [f"{where} is not UTF-8 JSON: {exc}"]


def _saved_fields(report: dict, written_by: str, writer) -> dict:
    """Every field of a saved report but saved_at."""
    assert written_by in WRITTEN_BY
    # A reply with the verdict keys saves the verdict, its reasons and the ceiling; one with neither
    # saves the v0.2.0 shape, so a report saved before 0.3.0 re-derives byte-equal (spec §8).
    verdict = {key: report[key] for key in _VERDICT_FIELDS if key in report} or {"investment_verdict": NO_VERDICT}
    return dict({"brief": report["brief"], "manifest_digest": report["manifest_digest"],
                 "manifest": report["manifest"], "rubric_version": report["rubric_version"],
                 "written_by": written_by, "writer": writer},
                **verdict, notes=report["notes"], items=report["items"], findings=report["findings"])


def _writer(receipt: dict, nnn: int) -> dict:
    return {"agent_id": receipt["agent_id"], "agent_type": receipt["agent_type"],
            "session_id": receipt["session_id"], "receipt": judge_receipt.receipt_relpath(nnn)}


def _write_report(case_dir: Path, nnn: int, report: dict, written_by: str, writer) -> Path:
    """Write judge/report-NNN.json once. The whole file goes to a temp file, then is linked to its
    name; the link fails when a report is there, so a report is never overwritten."""
    full = dict(_saved_fields(report, written_by, writer), saved_at=clock.today())
    path = case_dir / report_relpath(nnn)
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".report-")
        with os.fdopen(fd, "wb") as handle:
            handle.write((json.dumps(full, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        os.link(tmp, path)
    except FileExistsError:
        raise _run_again([f"{report_relpath(nnn)} already exists; a report is never overwritten"]) from None
    except OSError as exc:
        raise _run_again([f"cannot write {report_relpath(nnn)}: {exc}"]) from None
    finally:
        if tmp is not None:
            os.unlink(tmp)
    return path


def _refuse_if_saved(case_dir: Path, nnn: int) -> None:
    if (case_dir / report_relpath(nnn)).exists():
        raise _run_again([f"{report_relpath(nnn)} already exists; a report is never overwritten"])


def _judge_reply(case_dir: Path, nnn: int, manifest: dict, reply_path: Path, reply_rel: str, *,
                 any_recorded_session: bool = False, check_current: bool = True) -> tuple:
    """(report or None, receipt or None, problems) for the judge's reply. May raise OSError."""
    problems = []
    receipt = None
    try:
        receipt = judge_receipt.verify_receipt(case_dir, nnn, any_recorded_session=any_recorded_session)
    except judge_receipt.ReceiptRefused as exc:
        problems.append(str(exc))
    data = reply_path.read_bytes()
    if receipt is not None and digest.sha256_hex(data) != receipt["sha256"]:
        problems.append("the reply's bytes changed while it was read")
    reply, parse_problems = _parse(data, reply_rel)
    problems.extend(parse_problems)
    report = None
    if reply is not None:
        report, check_problems = _check(case_dir, nnn, manifest, reply, check_current=check_current)
        problems.extend(check_problems)
    return report, receipt, problems


def _refuse_if_other_session(case_dir: Path, nnn: int) -> None:
    """Ruling FR-I3: a receipt from a session that is not the case's current one is refused with
    that cause and the command that fixes it. The reply may be good, so this refusal never sends
    the coach to run the judge again."""
    receipted = judge_receipt.receipt_session(case_dir, nnn)
    try:
        current = case_files.current_session(case_dir)["id"]
    except case_files.CaseRefused:
        return  # verify_receipt names this
    if receipted is not None and receipted != current:
        raise ReplyRefused(f"{SESSION_NOT_CURRENT} ({receipted}); this case's current session is {current}. "
                           "Run bc.py session --id with your own session ID and --name with your name "
                           "(--automated for an automated run) to make your session current, "
                           "then run save-report again. No new judge run is needed")


def save_report(case_dir, brief_path) -> Path:
    """Validate the judge's reply at the reply_path the brief names, check its receipt, and save
    the report marked "written_by": "judge"."""
    try:
        case_dir, nnn, manifest, reply_path = _brief_parts(case_dir, brief_path)
    except ReplyRefused as exc:
        raise _run_again(exc.problems) from None
    _refuse_if_saved(case_dir, nnn)
    reply_rel, receipt_rel = judge_brief.reply_relpath(nnn), judge_receipt.receipt_relpath(nnn)
    if not reply_path.is_file():
        if paths.stat_exists(case_dir / receipt_rel):  # a coach copy would be refused too: never point to it
            raise _run_again([f"{receipt_rel} exists but {reply_rel} does not: the judge's reply was removed"])
        raise ReplyRefused(f"{NO_REPLY} at {reply_rel}: if the judge returned its JSON, write it to a file "
                           f"outside the case and run bc.py save-report --brief {brief_path} --coach-copy FILE")
    _refuse_if_other_session(case_dir, nnn)
    try:
        report, receipt, problems = _judge_reply(case_dir, nnn, manifest, reply_path, reply_rel)
    except OSError as exc:  # a file vanished or cannot be read: refused with the problem named
        raise _run_again([f"cannot read the judge's files: {exc}"]) from None
    if problems:
        raise _refused(problems)
    return _write_report(case_dir, nnn, report, "judge", _writer(receipt, nnn))


def rederive(case_dir, nnn: int) -> dict:
    """Every field but saved_at of the report that save_report would save from the judge's reply
    NNN now, by save_report's own checks (rulings FR-I2, FR-I2b); ReplyRefused names every problem.
    Loop end counts a saved report as the judge's only when it equals this. The receipt may name any
    session the case recorded, since the report was saved in its own session. The one check left
    out is that the brief's inputs are unchanged, so a stale report is re-derived too. The checks
    read today's files: when an edit moved a paragraph a claim finding points at, the result
    differs, and the stale report does not count."""
    brief_path = Path(case_dir) / judge_brief.brief_relpath(nnn)
    case_dir, nnn, manifest, reply_path = _brief_parts(case_dir, brief_path)
    try:
        report, receipt, problems = _judge_reply(case_dir, nnn, manifest, reply_path, judge_brief.reply_relpath(nnn),
                                                 any_recorded_session=True, check_current=False)
    except OSError as exc:
        raise ReplyRefused(f"cannot read the judge's files: {exc}") from None
    if problems:
        ordered, _ = broken_first(problems)
        raise ReplyRefused("; ".join(ordered), ordered)
    return _saved_fields(report, "judge", _writer(receipt, nnn))


def save_coach_copy(case_dir, brief_path, copy_path) -> Path:
    """The fallback: save the coach's copy of the judge's JSON, marked "written_by": "coach-copy".
    Refused while a judge reply exists for the brief, and for a copy anywhere in a case folder."""
    try:
        case_dir, nnn, manifest, reply_path = _brief_parts(case_dir, brief_path)
    except ReplyRefused as exc:
        raise _run_again(exc.problems) from None
    _refuse_if_saved(case_dir, nnn)
    copy_path = Path(copy_path)
    if judge_receipt.in_case_folder(copy_path.resolve()):
        raise ReplyRefused(f"the coach copy {copy_path} {COPY_IN_CASE}; write it to a file outside "
                           "the case and give that file")
    if paths.stat_exists(reply_path) or paths.stat_exists(case_dir / judge_receipt.receipt_relpath(nnn)):
        raise _run_again([f"a judge reply exists for this brief at {judge_brief.reply_relpath(nnn)}; "
                          "a judge reply is never overridden by a copy"])
    try:
        data = copy_path.read_bytes()
    except OSError as exc:
        raise _run_again([f"cannot read the coach copy {copy_path}: {exc}"]) from None
    reply, problems = _parse(data, str(copy_path))
    report = None
    if reply is not None:
        try:
            report, check_problems = _check(case_dir, nnn, manifest, reply)
        except OSError as exc:
            raise _run_again([f"cannot read the case's files: {exc}"]) from None
        problems.extend(check_problems)
    if problems:
        raise _refused(problems)
    return _write_report(case_dir, nnn, report, "coach-copy", None)


def _reports(case_dir) -> list:
    """(NNN, path) of every saved report, newest first."""
    folder = Path(case_dir) / paths.JUDGE_DIR
    found = []
    for p in folder.glob("report-*.json"):
        m = _REPORT_NAME.match(p.name)
        if m:
            found.append((int(m.group(1)), p))
    return sorted(found, reverse=True)


def report_number(rel: str) -> int:
    """NNN of a saved report's relpath, judge/report-NNN.json."""
    if not is_report_relpath(rel):
        raise ReplyRefused(f"{rel} is not a saved report's name")
    return int(_REPORT_NAME.match(rel.rpartition("/")[2]).group(1))


def is_report_relpath(rel) -> bool:
    """True for a saved report's name, judge/report-NNN.json; nothing else is a saved report."""
    if not isinstance(rel, str):
        return False
    parent, _, name = rel.rpartition("/")
    return parent == paths.JUDGE_DIR and _REPORT_NAME.match(name) is not None


def saved_reports(case_dir) -> list:
    """The relpath of every saved report, newest first."""
    return [report_relpath(nnn) for nnn, _ in _reports(case_dir)]


def latest_report(case_dir) -> tuple | None:
    """(relpath, report) of the newest saved report, coach copies included; None when there is none.
    Raises ReplyRefused, naming the report, when the newest one cannot be read."""
    for nnn, p in _reports(case_dir):
        try:
            return report_relpath(nnn), json.loads(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReplyRefused(f"cannot read {report_relpath(nnn)}: {exc}") from exc
    return None


def read_report(path):
    """A saved report's JSON, or None when it cannot be read or parsed."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None


def finance_read_by(report) -> dict | None:
    """The digest of finance.json in the report's manifest, or None when the report is not an object,
    its manifest is not an object, or it holds no valid digest for finance.json."""
    manifest = report.get("manifest") if isinstance(report, dict) else None
    read = manifest.get(paths.FINANCE) if isinstance(manifest, dict) else None
    return read if digest._is_digest(read) else None


def parsed_reports(case_dir) -> list:
    """(relpath, report or None) of every saved report, newest first."""
    return [(report_relpath(nnn), read_report(p)) for nnn, p in _reports(case_dir)]


def find_finding(case_dir, finding_id_: str, parsed: list = None) -> tuple | None:
    """(relpath, finding) from the newest report holding that finding ID; None when no report does.
    A report that cannot be read or parsed holds no findings. `parsed` is parsed_reports(case_dir),
    passed by a caller that looks up many findings."""
    for rel, report in parsed if parsed is not None else parsed_reports(case_dir):
        findings = report.get("findings") if isinstance(report, dict) else None
        for f in findings if isinstance(findings, list) else []:
            if isinstance(f, dict) and f.get("id") == finding_id_:
                return rel, f
    return None
