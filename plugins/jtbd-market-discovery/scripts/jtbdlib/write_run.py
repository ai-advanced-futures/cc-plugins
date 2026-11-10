"""write-run: write the pages of one run from its session folder and its result file (spec rows 6, 7, 13 and 14).

One process writes every page of the run. A run adds new pages and changes no page of an earlier run.
A value that a Result page holds is not written on the page of its item (spec "Design", field map).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from jtbdlib import DataError, UsageError, check, logbook, regen, schema, writer
from jtbdlib.bundle import DEFAULT_DIR, Bundle, bundle_dir, has_entry, read, ref
from jtbdlib.ids import fold, next_id
from jtbdlib.issues import ERROR
from jtbdlib.page import dump, ordered, write_text
from jtbdlib.rules import RESULT_ABOUT, moved_fields

# A step text that starts with its number: "7. Check ...", "7) Check ...", "7: Check ...", "Step 7: Check ..." (STORY-278).
LEADING_STEP = re.compile(r"\s*(?:step\s*)?(\d+)\s*[.):]\s+(\S.*)", re.IGNORECASE | re.DOTALL)

SCORE_LISTS = ("top_opportunities", "scored_needs", "all_needs", "needs", "opportunities", "scores")


def clean(text, limit=None) -> str:
    text = " ".join(str(text if text is not None else "").split())
    return text[:limit] if limit else text


def number(value):
    """A number from a number or from a text that holds one, else None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        parsed = float(str(value).strip().rstrip("%"))
    except ValueError:
        return None
    return int(parsed) if parsed == int(parsed) else parsed


def section(value):
    """A section of a phase file when it is an object, else {}. An agent writes a word such as "deferred" for a part it skipped."""
    return value if isinstance(value, dict) else {}


def pick(source, *names):
    for name in names:
        value = (source or {}).get(name)
        if value not in (None, "", [], {}):
            return value
    return None


def load_json(path, required=False):
    path = Path(path)
    if not path.is_file():
        if required:
            raise UsageError(f"{path} does not exist")
        return None
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read {path}: {error}") from error
    if not isinstance(data, dict):
        raise UsageError(f"{path} is not a JSON object")
    return data


def survey_answers(session_dir):
    """The number of WTP survey answers that run_phase_9.py read in this session (STORY-193), else None."""
    data = load_json(Path(session_dir) / "wtp-results.json") if session_dir else None
    size = section(section(data).get("validation")).get("sample_size")
    return size if isinstance(size, int) and not isinstance(size, bool) and size > 0 else None


def holds_survey_value(fields) -> bool:
    return any(fields.get(name) not in (None, "", []) for name in schema.WTP_SURVEY_FIELDS)


class Draft:
    def __init__(self, type_, path, title, description, fields, body=None):
        self.type, self.path = type_, path
        self.title, self.description = clean(title), clean(description, 200) or clean(title, 200)
        self.fields = fields
        self.body = body

    @property
    def id(self):
        return self.path.stem


class Writer:
    """The pages of one run, in memory until every page is made."""

    def __init__(self, root, actor):
        self.root, self.actor = Path(root), actor
        self.dir = bundle_dir(root) if has_entry(root) else Path(root) / DEFAULT_DIR
        self.pages: list[Draft] = []
        self.numbers: dict[str, int] = {}
        self.warnings: list[str] = []

    def allocate(self, type_):
        spec = schema.types()[type_]
        if type_ not in self.numbers:
            self.numbers[type_] = int(next_id(self.dir, type_).rsplit("-", 1)[1])
        number_ = self.numbers[type_]
        self.numbers[type_] += 1
        return self.dir / spec["directory"] / f"{spec['prefix']}-{number_:02d}.md"

    def make(self, type_, title, description, fields=None, links=None, body=None) -> Draft:
        data = {}
        for slot, value in (fields or {}).items():
            if value in (None, "", [], {}):
                continue
            if schema.slot_ok(type_, slot, value):
                data[slot] = value
            else:
                self.warnings.append(f"{type_} {clean(title, 40)!r}: the value of {slot} is not valid and is left out")
        for slot, value in (links or {}).items():
            if value not in (None, [], ""):
                data[slot] = value
        page = Draft(type_, self.allocate(type_), title, description, data, body)
        self.pages.append(page)
        return page

    def ref(self, page) -> str:
        return ref(self.dir, page.path)

    def frontmatter(self, page) -> dict:
        data = {"type": page.type, "title": page.title, "description": page.description, "status": "draft"}
        data.update(page.fields)
        data["generated"] = writer.stamp(self.actor)
        return ordered(data, schema.types()[page.type]["key_order"])

    def text(self, page) -> str:
        body = page.body if page.body is not None else f"\n# {page.id}: {page.title}\n\n{page.description}\n"
        return dump(self.frontmatter(page), body)

    def flush(self) -> None:
        problems = []
        for page in self.pages:
            problems += [f"{page.id}: {problem}" for problem in schema.validate(page.type, self.frontmatter(page))]
        if problems:
            raise DataError("a page is not valid, so nothing is written: " + "; ".join(problems))
        for page in self.pages:
            write_text(page.path, self.text(page))


def steps_of(p2):
    """The job steps of p2: (number, phase, description) for a list `job_steps` or a map `phases`."""
    out = []
    if isinstance(p2.get("job_steps"), list):
        for index, item in enumerate(p2["job_steps"], 1):
            out.append((number(pick(item, "step_id", "step")) or index, item.get("phase"), pick(item, "description", "step_description")))
    elif isinstance(p2.get("phases"), dict):
        for phase, items in p2["phases"].items():
            for item in items or []:
                out.append((number(pick(item, "step", "step_id")), phase, pick(item, "description")))
        out.sort(key=lambda row: (row[0] is None, row[0] or 0))
        out = [(n if n is not None else i, phase, text) for i, (n, phase, text) in enumerate(out, 1)]
    return [row for row in out if row[2]]


def score_items(p6):
    """Every scored need of p6, by need_id: the lists of p6 are merged."""
    merged = {}
    for name in SCORE_LISTS:
        for index, item in enumerate(p6.get(name) or [], 1):
            if not isinstance(item, dict):
                continue
            key = str(item.get("need_id") or fold(item.get("need")))
            entry = merged.setdefault(key, {})
            entry.update({k: v for k, v in item.items() if v is not None})
            if name == "top_opportunities" and "rank" not in item:
                entry["rank"] = index
    return merged


def need_keys(item):
    """The keys of a need: its id and its folded text. A text item is both."""
    if isinstance(item, str):
        return [item, fold(item)]
    keys = []
    if item.get("need_id") is not None:
        keys.append(str(item["need_id"]))
    if item.get("need"):
        keys.append(fold(item["need"]))
    return keys


class Build:
    """Map one session and its result file to pages (not yet written)."""

    def __init__(self, w: Writer, session_dir, result, state, bundle):
        self.w, self.session, self.result, self.state, self.bundle = w, session_dir, result or {}, state or {}, bundle
        self.p = {n: (load_json(session_dir / f"p{n}.json") if session_dir else None) for n in range(1, 10)}
        self.outcomes: dict[str, Draft] = {}
        self.steps: dict[int, Draft] = {}
        self.segments: dict[str, Draft] = {}
        self.wtp: dict[str, Draft] = {}
        self.results: dict[str, Draft] = {}
        self.job = self.run = None
        self.input_run = None
        self.input_p7 = None

    # ---- the run ---------------------------------------------------------------------------------

    def run_fields(self):
        info, p5, p7, p9 = self.result.get("run") or {}, self.p[5] or {}, self.p[7] or {}, self.p[9] or {}
        session_id = self.state.get("session_id") or (self.session.name if self.session else None)
        run_id = pick(info, "run_id") or self.state.get("run_id")
        fields = {
            "command": self.result.get("command") or "jtbd-market-discovery:discover",
            "subject": pick(info, "subject") or pick(self.p[1] or {}, "market_area", "job_statement", "job"),
            "session_id": session_id, "run_id": run_id,
            "case": pick(info, "case") or self.state.get("case"),
            "mode": pick(info, "mode"), "answers": pick(info, "answers"),
            "started_at": pick(info, "started_at") or self.state.get("started_at"),
            "finished_at": pick(info, "finished_at"),
            "plugin_version": self.result.get("plugin_version") or schema.plugin_version(),
            "ratings_source": pick(p5.get("assumption_sources"), "ratings_source") or pick(p5, "method"),
            "evc_inputs": p7.get("assumptions"), "wtp_verdict": pick(p9, "validation_result"),
            "wtp_sample_size": survey_answers(self.session),
            "gaps": self.result.get("gaps"),
        }
        return fields, session_id or run_id

    def make_run(self):
        fields, ident = self.run_fields()
        title = f"{fields['command']} run {ident or 'without id'}: {clean(fields.get('subject')) or 'no subject'}"
        text = f"Run of {fields['command'].split(':')[-1]} for {clean(fields.get('subject'), 80) or 'no subject'}"
        if fields.get("finished_at"):
            text += f", finished {fields['finished_at']}"
        links = {}
        if self.input_run:
            links["input_run"] = self.input_run
        self.run = self.w.make("Run", title, text, fields, links)
        self.run_ref = self.w.ref(self.run)

    # ---- the item pages --------------------------------------------------------------------------

    def make_job(self):
        p1, p4 = self.p[1], self.p[4] or {}
        if not p1:
            return
        statement = pick(p1, "job_statement", "job")
        freq = p4.get("frequency")
        freq_value = pick(freq, "value") if isinstance(freq, dict) else freq
        base = p4.get("time_baseline") if isinstance(p4.get("time_baseline"), dict) else {}
        fields = {"market_area": p1.get("market_area"), "validation": p1.get("validation"),
                  "frequency": pick(p1, "frequency") if not isinstance(p1.get("frequency"), dict) else freq_value,
                  "frequency_per_year": number(pick(freq, "numeric")) if isinstance(freq, dict) else None,
                  "importance_estimate": number(p1.get("importance_estimate")),
                  "time_baseline_minutes": number(base.get("total_minutes")), "time_by_phase": base.get("breakdown")}
        if fields["frequency"] is None:
            fields["frequency"] = freq_value
        lines = [f"- Frequency: {fields['frequency']} ({clean(freq.get('source'))})"] if isinstance(freq, dict) and freq.get("source") and fields["frequency"] else []
        if base.get("source"):
            lines.append(f"- Time baseline: {base.get('total_minutes')} minutes ({clean(base.get('source'))})")
        title = clean(statement) or "Job"
        self.job = self.w.make("Job", title, f"The job of run {self.state.get('session_id') or ''}: {clean(p1.get('market_area'), 80) or title}".strip(),
                               fields, {"run": self.run_ref})
        if lines:
            self.job.body = f"\n# {self.job.id}: {self.job.title}\n\n{self.job.description}\n\n" + "\n".join(lines) + "\n"

    def make_steps(self):
        p2 = self.p[2]
        if not p2:
            return
        if self.job is None:
            raise DataError("p2.json is there but p1.json is not: a JobStep needs the Job page of its run")
        for order, phase, text in steps_of(p2):
            page = self.w.make("JobStep", text, f"Step {order} of the job map ({phase or 'no phase'}): {clean(text, 100)}",
                               {"phase": phase}, {"job": self.w.ref(self.job), "run": self.run_ref})
            self.steps[order] = page

    def step_for(self, need):
        order = number(pick(need, "step_id", "step"))
        if order in self.steps:
            return self.steps[order]
        step = need.get("step") if isinstance(need.get("step"), str) else ""
        lead = LEADING_STEP.match(step)
        texts = [fold(step)] + ([fold(lead.group(2))] if lead else [])
        for text in filter(None, texts):
            for page in self.steps.values():
                if fold(page.title) == text:
                    return page
        if lead and int(lead.group(1)) in self.steps:
            return self.steps[int(lead.group(1))]
        raise DataError(f"the need {need.get('need_id') or clean(need.get('need'), 40)!r} names no step of p2.json")

    def make_outcomes(self):
        p3 = self.p[3]
        if not p3:
            return
        scores = score_items(self.p[6] or {})
        evc = {}
        for item in (self.p[7] or {}).get("top_evc_opportunities") or []:
            for key in need_keys(item):
                evc[key] = item
        for need in p3.get("needs") or []:
            statement = pick(need, "need")
            if not statement:
                continue
            score = next((scores[k] for k in need_keys(need) if k in scores), {})
            value = next((evc[k] for k in need_keys(need) if k in evc), {})
            breakdown = value.get("evc_breakdown")
            fields = {"need_id": str(need["need_id"]) if need.get("need_id") is not None else None,
                      "action": need.get("action"), "variable": need.get("variable"),
                      "rank": number(score.get("rank")), "importance": number(score.get("importance")),
                      "satisfaction": number(score.get("satisfaction")),
                      "gap": number(pick(score, "importance_satisfaction_gap", "gap")),
                      "opportunity_score": number(score.get("opportunity_score")),
                      "opportunity_category": pick(score, "category", "opportunity_category"),
                      "annual_evc": number(value.get("total_annual_evc")),
                      "evc_breakdown": breakdown if isinstance(breakdown, dict) else None}
            page = self.w.make("Outcome", statement, f"Desired outcome {fields['need_id'] or ''}: {clean(statement, 140)}".replace(" :", ":"),
                               fields, {"step": self.w.ref(self.step_for(need)), "run": self.run_ref})
            for key in need_keys(need):
                self.outcomes[key] = page
        for dropped in scores:
            if dropped not in self.outcomes:
                self.w.warnings.append(f"p6.json scores the need {dropped!r}, which p3.json does not list: no Outcome page")

    def outcome_of(self, item):
        return next((self.outcomes[k] for k in need_keys(item) if k in self.outcomes), None)

    def make_segments(self):
        p8 = self.p[8]
        if not p8:
            return
        if self.job is None:
            raise DataError("p8.json is there but p1.json is not: a Segment needs the Job page of its run")
        compare = p8.get("segment_comparison") or {}
        for index, item in enumerate(p8.get("segments") or [], 1):
            name = pick(item, "name")
            if not name:
                continue
            tops = [self.w.ref(page) for page in (self.outcome_of(n) for n in item.get("top_needs") or []) if page]
            priority = pick(item, "strategic_priority") or next(
                (label for label, key in (("primary", "primary_target"), ("secondary", "secondary_target"), ("tertiary", "tertiary"))
                 if fold(name) in fold(compare.get(key) or "")), None)
            economics = item.get("economics") if isinstance(item.get("economics"), dict) else {}
            fields = {"segment_id": str(item["segment_id"]) if item.get("segment_id") is not None else str(index),
                      "size_percent": number(item.get("size_percent")), "size_count": number(item.get("size_count")),
                      "characteristics": item.get("behavioral_profile"), "demographics": item.get("demographics"),
                      "strategic_priority": priority, "annual_evc": number(economics.get("avg_evc"))}
            page = self.w.make("Segment", name, f"Customer segment {name}: {item.get('size_percent', '?')} percent of the market",
                               fields, {"job": self.w.ref(self.job), "top_outcomes": tops, "run": self.run_ref})
            self.segments[fold(name)] = page

    def segment_pool(self):
        """The Segment pages that a WtpValidation of this run can name: this run, or the input run."""
        if not self.input_run:
            return {k: self.w.ref(p) for k, p in self.segments.items()}
        return {fold(page.title): ref(self.bundle.dir, path) for path, page in self.bundle.pages.items()
                if page.type == "Segment" and self.input_run in schema.edge_values(page.frontmatter, "run")}

    def make_wtp(self):
        p9 = self.p[9]
        if not p9:
            return
        pool = self.segment_pool()
        verdict = pick(p9, "validation_result", "verdict")
        for item in p9.get("segments") or []:
            name = pick(item, "name")
            if not name:
                continue
            target = pool.get(fold(name))
            if target is None and pool:
                raise DataError(f"p9.json segment {name!r} has no Segment page in the run that it reads")
            if target is None:
                self.w.warnings.append(f"p9.json segment {name!r}: the run that it reads has no Segment page, "
                                       "so the WtpValidation page has no segment link")
            analysis, west = section(item.get("wtp_analysis")), section(item.get("van_westendorp"))
            econ, bench = section(item.get("value_economics")), section(item.get("competitive_benchmark"))
            conf = item.get("confidence_score") if isinstance(item.get("confidence_score"), dict) else {}
            fields = {"confidence_level": pick(conf, "confidence_level") or pick(item, "confidence_level", "confidence") or pick(p9, "confidence_level", "confidence"),
                      "sample_size": number(analysis.get("sample_size")), "cleaned_median": number(analysis.get("cleaned_median")),
                      "cleaned_mean": number(analysis.get("cleaned_mean")), "optimal_price_point": number(west.get("optimal_price_point")),
                      "acceptable_range": west.get("acceptable_range"), "validated_wtp": number(item.get("validated_wtp")),
                      "wtp_range": item.get("wtp_range"), "annual_wtp": number(econ.get("annual_wtp")),
                      "annual_evc": number(econ.get("annual_evc")), "wtp_to_evc_ratio": number(econ.get("wtp_to_evc_ratio")),
                      "competitor_avg": number(bench.get("competitor_avg")), "verdict": pick(item, "verdict") or verdict}
            page = self.w.make("WtpValidation", f"Willingness to pay of {name}", f"Willingness to pay of the segment {name}, after the validation layers",
                               fields, {"segment": target, "run": self.run_ref} if target else {"run": self.run_ref})
            self.wtp[fold(name)] = page
        answers = survey_answers(self.session)
        if answers and not any(holds_survey_value(page.fields) for page in self.wtp.values()):
            raise DataError(f"wtp-results.json has {answers} survey answers, but no segment of p9.json holds a survey value "
                            f"({', '.join(schema.WTP_SURVEY_FIELDS)}). Write the numbers of wtp-results.json into p9.json, "
                            "then run write-run again. No page was written.")

    # ---- the Result pages ------------------------------------------------------------------------

    def about_of(self, entry):
        kind, value = entry.get("kind"), entry.get("value")
        value = value if isinstance(value, dict) else {}
        if kind == "job":
            return self.job
        if kind == "job_step":
            return self.steps.get(number(value.get("order")))
        if kind == "opportunity_score":
            return self.outcome_of({"need": value.get("need"), "need_id": value.get("need_id")})
        if kind == "customer_value":
            return self.value_outcome()
        if kind == "customer_segment":
            return self.segments.get(fold(value.get("name") or entry.get("label") or ""))
        if kind == "willingness_to_pay":
            return self.wtp.get(fold(value.get("segment") or ""))
        return None

    def value_outcome(self):
        """The Outcome that p7 ranks first: a page of this run, or of the input run (a Draft or a bundle path)."""
        p7 = (self.p[7] if self.p[7] else self.input_p7) or {}
        top = next((i for i in p7.get("top_evc_opportunities") or [] if number(i.get("rank")) == 1), None)
        pool = self.outcomes
        if top:
            page = next((pool[k] for k in need_keys(top) if k in pool), None)
            if page is not None:
                return page
        ranked = [p for p in {id(p): p for p in pool.values()}.values() if p.fields.get("rank") == 1]
        if ranked:
            return ranked[0]
        return self.input_outcome(top)

    def input_outcome(self, top):
        """The Outcome of the input run (a bundle path) for the customer_value result of a wtp-check run."""
        if not self.input_run:
            return None
        outcomes = [(path, page) for path, page in self.bundle.pages.items()
                    if page.type == "Outcome" and self.input_run in schema.edge_values(page.frontmatter, "run")]
        keys = set(need_keys(top)) if top else set()
        for path, page in outcomes:
            fm = page.frontmatter
            if keys & {str(fm.get("need_id")), fold(page.title)}:
                return ref(self.bundle.dir, path)
        for path, page in outcomes:
            if page.frontmatter.get("rank") == 1:
                return ref(self.bundle.dir, path)
        return None

    def cited(self, cite):
        wanted = str(cite.get("result_id") or "")
        runs = [self.input_run] if self.input_run else []
        for path, page in self.bundle.pages.items():
            if page.type != "Result" or not set(schema.edge_values(page.frontmatter, "run")) & set(runs):
                continue
            if any(a.split("/", 1)[-1] == wanted for a in page.frontmatter.get("aliases") or []):
                return ref(self.bundle.dir, path)
        page = self.results.get(wanted)
        return self.w.ref(page) if page else None

    def make_results(self, ident):
        entries = [e for e in self.result.get("results") or [] if isinstance(e, dict)]
        for entry in entries:
            kind = entry.get("kind")
            about = self.about_of(entry) if kind in RESULT_ABOUT else None
            about_ref = self.w.ref(about) if isinstance(about, Draft) else about
            if about_ref is None:
                self.w.warnings.append(f"the result {entry.get('id')!r} (kind {kind}) has no page to be about")
            cites = []
            for cite in entry.get("cites") or []:
                target = self.cited(cite) if isinstance(cite, dict) else None
                if target:
                    cites.append(target)
                else:
                    self.w.warnings.append(f"the result {entry.get('id')!r} cites {cite!r}, which names no Result page")
            fields = {"kind": kind, "label": entry.get("label"), "value": entry.get("value"), "unit": entry.get("unit"),
                      "period": entry.get("period"), "result_sources": entry.get("sources"), "method": entry.get("method"),
                      "rests_on_default": bool(entry.get("rests_on_default")), "defaults": entry.get("defaults"),
                      "confidence": entry.get("confidence"), "aliases": [f"{ident}/{entry.get('id')}"]}
            page = self.w.make("Result", entry.get("label") or str(entry.get("id")), f"Result {entry.get('id')} ({kind}): {clean(entry.get('label'), 120)}",
                               fields, {"run": self.run_ref, "about": about_ref, "cites": cites})
            self.results[str(entry.get("id"))] = page
            if isinstance(about, Draft):
                for name in moved_fields(kind):
                    about.fields.pop(name, None)

    def top_outcomes(self):
        ranked = sorted({id(p): p for p in self.outcomes.values() if p.fields.get("rank")}.values(), key=lambda p: p.fields["rank"])
        tops = [self.w.ref(p) for p in ranked[:3]]
        if tops:
            self.run.fields["top_outcomes"] = tops


def session_state(session_dir):
    return load_json(Path(session_dir) / "state.json") or {}


def find_result_file(session_dir, state):
    """The result file of the discover run of a session, in `results/` beside the session folder."""
    folder = session_dir.parent / "results"
    run_id = state.get("run_id")
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            data = json.loads(path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        info = (data or {}).get("run") or {}
        if not str(data.get("command", "")).endswith(":discover"):
            continue
        if (run_id and info.get("run_id") == run_id) or (not run_id and info.get("started_at") == state.get("started_at")):
            return data
    return None


def input_folder(session_dir, state, result):
    """The session folder of the discover run that a wtp-check run read, or None."""
    p9 = load_json(session_dir / "p9.json") or {}
    value = state.get("input_dir") or p9.get("input_dir")
    if value:
        return sibling_session(session_dir, session_dir / str(value))
    for entry in (result or {}).get("results") or []:
        if isinstance(entry, dict) and entry.get("kind") == "customer_value" and entry.get("detail"):
            parent = (session_dir.parent.parent / str(entry["detail"])).parent
            if parent.is_dir() and parent.resolve() != session_dir:
                return sibling_session(session_dir, parent)
    return None


def sibling_session(session_dir, path) -> Path:
    """The input session folder. It must be a folder beside the session folder, so a file value cannot reach another place."""
    path = Path(path).resolve()
    if path.parent != session_dir.parent or path == session_dir:
        raise UsageError(f"the input session must be a folder beside the session folder, in {session_dir.parent.name}/: {path}")
    return path


def ensure_input(root, session_dir, state, result, actor, lines):
    """Return (Run page path, p7 data) of the input run, writing that run first when it is not a page yet."""
    folder = input_folder(session_dir, state, result)
    if folder is None:
        return None, None
    if not folder.is_dir():
        raise DataError(f"the input session {folder.name} is not a folder")
    if not (folder / "state.json").is_file() and not any(folder.glob("p*.json")):
        raise DataError(f"the input session {folder.name} holds no state.json and no p*.json file. No page was written.")
    input_state = session_state(folder)
    page = input_state.get("run_page")
    if not page or not has_entry(root) or not (bundle_dir(root) / str(page).lstrip("/")).is_file():
        earlier = find_result_file(folder, input_state)
        if earlier is None:
            raise DataError(f"no result file of the discover run {input_state.get('run_id') or folder.name} is in "
                            f"{folder.parent.name}/results/. No page was written, because the Run page would have no Result page.")
        write_one(root, folder, earlier, actor, lines, "jtbd-market-discovery:discover")
        page = session_state(folder)["run_page"]
    return page, load_json(folder / "p7.json")


def write_one(root, session_dir, result, actor, lines, command=None):
    """Write the pages of 1 run. Return the mapping of the source items to bundle paths."""
    session_dir = Path(session_dir).resolve() if session_dir else None
    if session_dir and not session_dir.is_dir():
        raise DataError(f"the session folder {session_dir.name} is not a folder. No page was written.")
    state = session_state(session_dir) if session_dir else {}
    page = state.get("run_page")
    if page and has_entry(root) and (bundle_dir(root) / str(page).lstrip("/")).is_file():
        raise DataError(f"this session is already written as {page}. Run remove on that Run page (it removes the other pages of the run too) before write-run writes it again.")
    result = dict(result or {})
    if command and not result.get("command"):
        result["command"] = command
    if has_entry(root):
        writer.upgrade(root)
    w = Writer(root, actor)
    bundle = read(root) if has_entry(root) else Bundle(Path(root), w.dir, {})
    build = Build(w, session_dir, result, state, bundle)
    if session_dir and str(result.get("command", "")).endswith(":wtp-check"):
        build.input_run, build.input_p7 = ensure_input(root, session_dir, state, result, actor, lines)
        if build.input_run:
            build.bundle = read(root)
            w.dir = build.bundle.dir
    build.make_run()
    ident = build.run_fields()[1] or "run"
    build.make_job()
    build.make_steps()
    build.make_outcomes()
    build.make_segments()
    build.make_wtp()
    build.make_results(ident)
    build.top_outcomes()
    if not has_entry(root):
        writer.init(root, DEFAULT_DIR, actor)
        lines.append(f"INIT: {DEFAULT_DIR}/")
        w.dir = bundle_dir(root)
    w.flush()
    run_ref = w.ref(build.run)
    if session_dir:
        state["run_page"] = run_ref
        (session_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    regen.write(root, w.dir)
    where = session_dir.name if session_dir else "a result file"
    logbook.append(w.dir / "log.md", "Ingest", f"wrote {run_ref} and {len(w.pages) - 1} more pages from {where}", actor)
    mapping = {"run": run_ref}
    if build.job:
        mapping["job"] = w.ref(build.job)
    mapping["steps"] = {str(k): w.ref(p) for k, p in build.steps.items()}
    mapping["outcomes"] = {p.fields.get("need_id") or p.title: w.ref(p) for p in set(build.outcomes.values())}
    mapping["segments"] = {p.fields.get("segment_id") or p.title: w.ref(p) for p in build.segments.values()}
    mapping["wtp"] = {p.title: w.ref(p) for p in build.wtp.values()}
    mapping["results"] = {k: w.ref(p) for k, p in build.results.items() if p is not None}
    mapping["warnings"] = w.warnings
    return mapping


def run(root, session_dir, result_file, actor=None):
    """Write the pages of a run. Return (lines to print, error lines)."""
    root = Path(root).resolve()
    actor = actor or schema.plugin_actor()
    result = load_json(result_file, required=True)
    if not isinstance(result.get("results"), list):
        raise UsageError(f"{result_file} has no results list")
    lines: list[str] = []
    mapping = write_one(root, session_dir, result, actor, lines)
    lines.append(json.dumps(mapping, indent=2, ensure_ascii=False))
    errors = [i.text() for i in check.run(root) if i.level == ERROR]
    return lines, errors
