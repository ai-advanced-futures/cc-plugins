"""ingest: write the pages of one phase of a ux-design run from its output files (STORY-257, rows 7 and 9).

The output folder holds the files of the phases. `pages.json` there names the Run page of the run, so each
later phase joins the same run while that run is a draft. A run that a person confirmed, or a save with
`new_run`, starts a new Run page. The pages that the earlier runs made stay known, so a page is not made twice. The pages are made in a temporary copy of the bundle. The code runs `regen` and the brain check in
that copy, and moves the copy in only when the check has no error. Only then does it remove the files that it
read. A failed step removes no file and changes no page.

A JSON file is put together again by `view`: `Run.file_meta[file]` is the file with each document replaced by
`@@<page ID>`, and the page holds the document as `record["<RUN ID>/<file>"]`. A page that has child pages
(a screen has its states) holds its document with the child markers in place.
"""
from __future__ import annotations

import contextlib
import json
import shutil
import tempfile
from pathlib import Path

from uxlib import DataError, UsageError, check, logbook, regen, schema, writer
from uxlib.bundle import REGISTRY, bundle_dir, page_files, ref
from uxlib.ids import fold, next_id
from uxlib.issues import ERROR
from uxlib.page import parse

MARK = "@@"
ARTIFACTS = ".ux-artifacts"
PAGES_FILE = "pages.json"
PHASES = {
    "empathize": ("research_findings.json",),
    "define": ("personas.json", "journey_maps.json", "mental_models.mmd"),
    "ideate": ("design_concepts.json",),
    "prototype": ("wireframes.json", "interaction_patterns.json", "user_flows.mmd"),
    "test": ("evaluation_report.json",),
}
OUTPUT_FILES = tuple(name for files in PHASES.values() for name in files)
DIAGRAMS = {"mental_models.mmd": "mental-model", "user_flows.mmd": "user-flow"}
# The pages that later runs reuse, and the field that is the key (a pattern is a key only with pattern_kind: pattern).
MERGED = {"Persona": "name", "Screen": "wireframe_id", "Concept": "concept_id", "InteractionRule": "pattern_id"}
FINDING_LISTS = (("key_findings", "key_finding"), ("pain_points", "pain_point"), ("opportunities", "opportunity"),
                 ("accessibility_findings", "accessibility"), ("ai_interaction_findings", "ai_interaction"),
                 ("implementation_handoff", "implementation_handoff"))
LIMIT_TITLE, LIMIT_DESCRIPTION = 120, 200


def clean(text, limit=None) -> str:
    text = " ".join(str(text if text is not None else "").split())
    return text[:limit].rstrip() if limit else text


def first_text(*values) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return ""


def as_names(value) -> list[str]:
    """The names or IDs that a field holds, whether it is a text, a list, or a list of objects."""
    items = value if isinstance(value, list) else [value]
    out = []
    for item in items:
        if isinstance(item, dict):
            item = item.get("name") or item.get("segment_id") or item.get("persona_id") or item.get("id")
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def walk_marks(value, name) -> None:
    if isinstance(value, str) and value.startswith(MARK):
        raise DataError(f"{name}: a text starts with {MARK}, which the page store keeps for its own markers: {value[:40]!r}")
    if isinstance(value, dict):
        for item in value.values():
            walk_marks(item, name)
    elif isinstance(value, list):
        for item in value:
            walk_marks(item, name)


def read_json(path):
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(f"{Path(path).name}: cannot read the file as JSON: {error}") from error


def fence_for(text) -> str:
    longest = run = 0
    for char in text:
        run = run + 1 if char == "`" else 0
        longest = max(longest, run)
    return "`" * max(3, longest + 1)


class P:
    """A page in memory."""

    def __init__(self, path, type_, fm, body, new):
        self.path, self.type, self.fm, self.body, self.dirty = path, type_, fm, body, new

    @property
    def id(self):
        return self.path.stem


class Ingest:
    def __init__(self, root, actor, known):
        self.root = Path(root)
        self.dir = bundle_dir(root)
        self.actor = actor
        self.known = known  # pages.json "files": file -> ident -> page ref, from the earlier phases of this run
        self.joined = False  # True when this save joins the run that pages.json names
        self.pages: dict[Path, P] = {}
        self.index: dict[tuple, Path] = {}
        self.numbers: dict[str, int] = {}
        self.touched: dict[str, dict] = {}
        self.skeletons: dict[str, object] = {}
        self.run_p = None
        self.run_ref = ""
        for path in page_files(self.dir):
            page = parse(path)
            if page.error or not page.type:
                raise DataError(f"{path.name}: {page.error or 'the page has no type'}")
            self.pages[path] = P(path, page.type, page.frontmatter, page.body, False)
            self.index_page(self.pages[path])

    # ---- pages in memory -----------------------------------------------------------------------

    def key_of(self, type_, fm):
        field = MERGED.get(type_)
        if field is None or not fm.get(field):
            return None
        if type_ == "InteractionRule" and fm.get("pattern_kind") != "pattern":
            return None
        return (type_, fold(fm[field]))

    def index_page(self, page) -> None:
        key = self.key_of(page.type, page.fm)
        if key:
            self.index[key] = page.path

    def at(self, page_ref):
        return self.pages.get(self.dir / page_ref.lstrip("/"))

    def ref(self, page) -> str:
        return ref(self.dir, page.path)

    def allocate(self, type_) -> Path:
        spec = schema.types()[type_]
        if type_ not in self.numbers:
            self.numbers[type_] = int(next_id(self.dir, type_).rsplit("-", 1)[1])
        number = self.numbers[type_]
        self.numbers[type_] += 1
        return self.dir / spec["directory"] / f"{spec['prefix']}-{number:02d}.md"

    @property
    def record_prefix(self) -> str:
        return Path(self.run_ref).stem

    def record_key(self, file) -> str:
        return f"{self.record_prefix}/{file}"

    def upsert(self, type_, title, desc, *, file=None, ident=None, fields=None, links=None, item=None, body=None,
               replace_body=False):
        """Make or update the page of one item. `ident` is the place of the item in the file."""
        if file and ident is not None and str(ident) in self.touched.get(file, {}):
            raise DataError(f"{file}: 2 items have the same place {ident}, so one would replace the other")
        fm = {"type": type_, "title": clean(title, LIMIT_TITLE) or type_,
              "description": clean(desc, LIMIT_DESCRIPTION) or clean(title, LIMIT_DESCRIPTION) or type_, "status": "draft"}
        for slot, value in (fields or {}).items():
            if value not in (None, "", []) and schema.slot_ok(type_, slot, value):
                fm[slot] = value
        for slot, value in (links or {}).items():
            if value not in (None, "", []):
                fm[slot] = value
        if type_ != "Run":
            fm["run"] = [self.run_ref]
        page = None
        key = self.key_of(type_, fm)
        if key and key in self.index:
            page = self.pages[self.index[key]]
        # `known` holds only the places that an earlier phase of this run saved: a new run starts with none, so it makes
        # its own Evaluation, finding and other pages. The types of MERGED are found by key above (spec row 9).
        elif file and ident is not None and ident in (self.known.get(file) or {}):
            page = self.at(self.known[file][ident])
        if page is None:
            path = self.allocate(type_)
            page = P(path, type_, fm, None, True)
            page.body = body if body is not None else f"\n# {page.id}: {fm['title']}\n\n{fm['description']}\n"
            self.pages[path] = page
        else:
            if page.fm.get("protected") is True:
                fm = {"run": fm.get("run")} if fm.get("run") else {}
            old_runs = list(page.fm.get("run") or [])
            page.fm.update({slot: value for slot, value in fm.items() if slot != "run"})
            if "run" in fm:
                page.fm["run"] = list(dict.fromkeys(old_runs + fm["run"]))
            page.dirty = True
            if replace_body and body is not None:
                page.body = body
        self.index_page(page)
        if file:
            if item is not None:
                page.fm.setdefault("record", {})[self.record_key(file)] = item
            idents = self.touched.setdefault(file, {})
            place = str(ident if ident is not None else f"item-{len(idents) + 1}")
            if self.ref(page) in idents.values():
                raise DataError(f"{file}: 2 items give the page {page.id}, so one would replace the other: "
                                f"{[k for k, v in idents.items() if v == self.ref(page)][0]} and {place}")
            idents[place] = self.ref(page)
        return page

    def find(self, type_, field, value):
        """A page of this type whose field is the value; a page of this run comes first."""
        wanted = fold(value)
        hits = [p for p in self.pages.values() if p.type == type_ and fold(p.fm.get(field) or "") == wanted]
        hits.sort(key=lambda p: self.run_ref not in (p.fm.get("run") or []))
        return hits[0] if hits else None

    def link_to(self, type_, field, values) -> list[str]:
        out = []
        for value in values:
            page = self.find(type_, field, value) or (self.find(type_, "name", value) if field != "name" else None)
            if page and self.ref(page) not in out:
                out.append(self.ref(page))
        return out

    # ---- the run ----------------------------------------------------------------------------------

    def start_run(self, phase, out_rel, run_ref, context, new_run=False) -> None:
        if run_ref:
            page = self.at(run_ref)
            if page is None or page.type != "Run":
                raise DataError(f"{PAGES_FILE} names {run_ref}, which is not a Run page of the bundle. "
                                f"Remove {PAGES_FILE} to start a new run.")
            phases = list(page.fm.get("phases") or [])
            # A later phase joins the run only while the run is a draft, and only when the caller does not ask for a new
            # run. A run that a person confirmed is over, and its status stays: this save starts a new run (PR 1357).
            if page.fm.get("status") == "draft" and not new_run:
                self.run_p, self.run_ref = page, run_ref
                self.joined = True
                page.fm["phases"] = phases + ([phase] if phase not in phases else [])
                page.dirty = True
                return
        path = self.allocate("Run")
        now = logbook.stamp()
        fm = {"type": "Run", "title": f"UX design run of {now[:10]}",
              "description": f"The run of the ux-design skill that started at {now}.", "status": "draft",
              "phases": [phase], "output_dir": out_rel, "started_at": now, "plugin_version": schema.plugin_version()}
        if context:
            fm["project_context"] = context
        page = P(path, "Run", fm, f"\n# {path.stem}: {fm['title']}\n\n{fm['description']}\n", True)
        self.pages[path] = page
        self.run_p, self.run_ref = page, ref(self.dir, path)

    # ---- the files --------------------------------------------------------------------------------

    def split(self, name, data, item_key):
        """Return the documents of a file and a function that puts the markers back into its shape."""
        if isinstance(data, list):
            if not all(isinstance(doc, dict) for doc in data):
                raise DataError(f"{name}: each entry of the list must be a JSON object")
            return data, lambda marks: marks
        if not isinstance(data, dict):
            raise DataError(f"{name}: the file must be a JSON object or a list of objects")
        if item_key in data:
            return [data], lambda marks: marks[0]
        wrappers = [key for key, value in data.items() if isinstance(value, list) and value
                    and all(isinstance(doc, dict) and item_key in doc for doc in value)]
        if len(wrappers) != 1:
            raise DataError(f"{name}: the file has no {item_key!r} object, and no list of documents that have one")
        key = wrappers[0]
        return data[key], lambda marks: {**data, key: marks}

    def documents(self, name, data, item_key, make):
        docs, rebuild = self.split(name, data, item_key)
        marks = []
        for number, doc in enumerate(docs):
            if not isinstance(doc.get(item_key), dict):
                raise DataError(f"{name}: document {number + 1} has no {item_key!r} object")
            page = make(doc, f"#{number + 1}")
            marks.append(MARK + page.id)
        self.skeletons[name] = rebuild(marks)

    def h_personas(self, name, data):
        def make(doc, ident):
            item = doc["persona"]
            if not first_text(item.get("name")):
                raise DataError(f"{name}: a persona has no name, and the name is the key of the page")
            links = {"segments": self.link_to("Segment", "name", as_names(item.get("segments")))
                     or self.link_to("Segment", "item_id", as_names(item.get("segments")))}
            return self.upsert("Persona", item["name"], first_text(item.get("tagline"), item.get("quote")), file=name,
                               ident=item["name"], fields={"name": item["name"]}, links=links, item=doc,
                               body=self.persona_body(item))
        self.documents(name, data, "persona", make)

    def h_journeys(self, name, data):
        def make(doc, ident):
            item = doc["journey_map"]
            who = item.get("persona")
            who = who.get("name") if isinstance(who, dict) else who
            persona = self.link_to("Persona", "name", [who] if who else [])
            return self.upsert("Journey", first_text(item.get("title"), "Journey map"), item.get("description"), file=name,
                               ident=ident, fields={"persona_name": who if isinstance(who, str) else None},
                               links={"persona": persona[0] if persona else None}, item=doc,
                               body=self.list_body(item, "Stages", "stages", ("stage_name", "description")))
        self.documents(name, data, "journey_map", make)

    def h_concepts(self, name, data):
        def make(doc, ident):
            item = doc["concept"]
            if not first_text(item.get("concept_id")):
                raise DataError(f"{name}: a concept has no concept_id, and the id is the key of the page")
            selected = item.get("selected", doc.get("selected"))
            return self.upsert("Concept", first_text(item.get("title"), item["concept_id"]),
                               first_text(item.get("tagline"), item.get("description")), file=name, ident=item["concept_id"],
                               fields={"concept_id": item["concept_id"], "selected": selected if isinstance(selected, bool) else None},
                               item=doc)
        self.documents(name, data, "concept", make)

    def h_patterns(self, name, data):
        def make(doc, ident):
            item = doc["pattern"]
            if not first_text(item.get("pattern_id")):
                raise DataError(f"{name}: a pattern has no pattern_id, and the id is the key of the page")
            return self.upsert("InteractionRule", first_text(item.get("name"), item["pattern_id"]), item.get("description"),
                               file=name, ident=item["pattern_id"],
                               fields={"pattern_kind": "pattern", "pattern_id": item["pattern_id"]}, item=doc)
        self.documents(name, data, "pattern", make)

    def h_wireframes(self, name, data):
        def make(doc, ident):
            item = doc["wireframe"]
            if not first_text(item.get("wireframe_id")):
                raise DataError(f"{name}: a wireframe has no wireframe_id, and the id is the key of the page")
            meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
            concept = meta.get("concept_reference") or item.get("design_concept_id")
            concept = concept.get("concept_id") or concept.get("id") if isinstance(concept, dict) else concept
            found = self.link_to("Concept", "concept_id", [concept] if isinstance(concept, str) else [])
            screen = self.upsert("Screen", first_text(item.get("screen_name"), item["wireframe_id"]),
                                 first_text(item.get("description"), item.get("purpose")), file=name,
                                 ident=item["wireframe_id"], fields={"wireframe_id": item["wireframe_id"]},
                                 links={"concept": found[0] if found else None},
                                 body=self.list_body(item, "Components", "components", ("component_id", "label")))
            screen_ref, place = self.ref(screen), item["wireframe_id"]
            copy = {**doc, "wireframe": dict(item)}
            wire = copy["wireframe"]
            for key, kind in (("error_states", "error"), ("loading_states", "loading")):
                if key in item:
                    wire[key] = self.children(name, item[key], key, place, screen_ref, "StateRule", kind)
            components = []
            for number, component in enumerate(item.get("components") or []):
                component = dict(component) if isinstance(component, dict) else component
                # The plain state "default" is no rule: it stays in the record of the screen, and `view` gives it back.
                state = component.get("state") if isinstance(component, dict) else None
                if state and not (isinstance(state, str) and state.strip().casefold() == "default"):
                    label = first_text(component.get("component_id"), component.get("label"), f"component {number + 1}")
                    page = self.upsert("StateRule", f"{item['wireframe_id']}: {label} state", self.state_text(component["state"]),
                                       file=name, ident=f"{place}/components/{number}", item=component["state"],
                                       fields={"state_kind": "component"}, links={"screen": screen_ref})
                    component["state"] = MARK + page.id
                components.append(component)
            if "components" in item:
                wire["components"] = components
            if "interactions" in item:
                wire["interactions"] = self.children(name, item["interactions"], "interactions", place, screen_ref,
                                                     "InteractionRule", "screen_interaction")
            screen.fm.setdefault("record", {})[self.record_key(name)] = copy
            return screen
        self.documents(name, data, "wireframe", make)

    def children(self, file, items, key, place, screen_ref, type_, kind):
        """Make the child pages of a list of the wireframe, and return the list with each entry a marker."""
        if not isinstance(items, list):
            return items
        out = []
        for number, entry in enumerate(items):
            if not isinstance(entry, dict):
                out.append(entry)
                continue
            if type_ == "StateRule":
                fields = {"state_kind": kind}
                title = f"{place}: {first_text(entry.get('error_type'), entry.get('trigger'), f'{kind} state {number + 1}')}"
                desc = first_text(entry.get("recovery_action"), entry.get("loading_pattern"), title)
                links = {"screen": screen_ref}
            else:
                fields = {"pattern_kind": kind}
                title = f"{place}: {first_text(entry.get('interaction_id'), f'interaction {number + 1}')}"
                desc = first_text(entry.get("description"), title)
                links = {"screens": [screen_ref]}
            page = self.upsert(type_, title, desc, file=file, ident=f"{place}/{key}/{number}", fields=fields, links=links,
                               item=entry)
            out.append(MARK + page.id)
        return out

    @staticmethod
    def state_text(state) -> str:
        return state if isinstance(state, str) and state.strip() else json.dumps(state, ensure_ascii=False)

    def h_research(self, name, data):
        if not isinstance(data, dict):
            raise DataError(f"{name}: the file must be a JSON object")
        skeleton = dict(data)
        for key, type_, field in (("user_segments", "Segment", "segment_id"), ("mental_models", "MentalModel", "model_id")):
            skeleton[key] = self.each(name, data.get(key), key, type_, field)
        for key, kind in FINDING_LISTS:
            skeleton[key] = self.each(name, data.get(key), key, "ResearchFinding", None, kind)
        self.skeletons[name] = {key: value for key, value in skeleton.items() if key in data}

    def each(self, name, items, key, type_, id_field, kind=None):
        if not isinstance(items, list):
            return items
        out = []
        for number, item in enumerate(items):
            if not isinstance(item, dict):
                out.append(item)
                continue
            item_id = first_text(item.get(id_field) if id_field else None,
                                 item.get("finding_id"), item.get("pain_point_id"), item.get("opportunity_id"),
                                 item.get("decision_id"))
            ident = f"{key}/{item_id or '#' + str(number + 1)}"
            if type_ == "Segment":
                page = self.upsert(type_, first_text(item.get("name"), item_id, "Segment"),
                                   first_text(item.get("description"), "; ".join(map(str, item.get("characteristics") or []))),
                                   file=name, ident=ident, fields={"item_id": item_id, "name": item.get("name")}, item=item)
            elif type_ == "MentalModel":
                persona = item.get("persona_reference") or item.get("persona")
                found = self.link_to("Persona", "name", as_names(persona))
                page = self.upsert(type_, first_text(item.get("name"), item_id, "Mental model"), item.get("description"),
                                   file=name, ident=ident, fields={"item_id": item_id, "name": item.get("name")},
                                   links={"persona": found[0] if found else None}, item=item)
            else:
                text = first_text(item.get("description"), item.get("decision"), item.get("category"))
                segments = self.link_to("Segment", "item_id", as_names(item.get("affected_segments"))) \
                    or self.link_to("Segment", "name", as_names(item.get("affected_segments")))
                evidence = item.get("evidence")
                page = self.upsert(type_, first_text(item.get("title"), item.get("decision"), text, item_id, kind), text,
                                   file=name, ident=ident,
                                   fields={"finding_kind": kind, "item_id": item_id or None,
                                           "severity": str(item["severity"]) if item.get("severity") is not None else None,
                                           "confidence": str(item.get("confidence") or item.get("potential_impact") or "") or None,
                                           "evidence": [str(e) for e in evidence] if isinstance(evidence, list) else None},
                                   links={"segments": segments}, item=item, body=self.finding_body(item, text))
            out.append(MARK + page.id)
        return out

    def h_evaluation(self, name, data):
        def make(doc, ident):
            ev = doc["evaluation"]
            holder = ev if ("findings" in ev or "recommendations" in ev or "findings" not in doc) else doc
            title = first_text(ev.get("title"), ev.get("description"), "Evaluation")
            page = self.upsert("Evaluation", title, first_text(ev.get("description"), title), file=name, ident=ident,
                               fields={"ux_health_score": ev.get("ux_health_score") or doc.get("ux_health_score")})
            page_ref = self.ref(page)
            copy = {**doc, "evaluation": dict(ev)}
            target = copy["evaluation"] if holder is ev else copy
            finding_refs = {}
            if isinstance(holder.get("findings"), list):
                marks = []
                for number, finding in enumerate(holder["findings"]):
                    if not isinstance(finding, dict):
                        marks.append(finding)
                        continue
                    item_id = first_text(finding.get("finding_id"))
                    text = first_text(finding.get("title"), finding.get("issue"), finding.get("description"), item_id, "Finding")
                    child = self.upsert("EvalFinding", text, first_text(finding.get("description"), finding.get("issue"), text),
                                        file=name, ident=f"{ident}/findings/{item_id or '#' + str(number + 1)}",
                                        fields={"item_id": item_id or None,
                                                "severity": str(finding["severity"]) if finding.get("severity") is not None else None},
                                        links={"evaluation": page_ref}, item=finding)
                    if item_id:
                        finding_refs[item_id] = self.ref(child)
                    marks.append(MARK + child.id)
                target["findings"] = marks
            if isinstance(holder.get("recommendations"), list):
                marks = []
                for number, rec in enumerate(holder["recommendations"]):
                    if not isinstance(rec, dict):
                        marks.append(rec)
                        continue
                    text = first_text(rec.get("recommendation"), rec.get("title"), rec.get("description"), "Recommendation")
                    affected = [finding_refs[i] for i in as_names(rec.get("affected_findings")) if i in finding_refs]
                    child = self.upsert("Recommendation", text, first_text(rec.get("rationale"), text), file=name,
                                        ident=f"{ident}/recommendations/#{number + 1}",
                                        links={"evaluation": page_ref, "findings": affected}, item=rec)
                    marks.append(MARK + child.id)
                target["recommendations"] = marks
            page.fm.setdefault("record", {})[self.record_key(name)] = copy
            return page
        self.documents(name, data, "evaluation", make)

    def h_diagram(self, name, text):
        newlines = len(text) - len(text.rstrip("\n"))
        core = text.rstrip("\n")
        fence = fence_for(core)
        kind = DIAGRAMS[name]
        title = "Mental model diagram" if kind == "mental-model" else "User flow diagram"
        journeys = [p for p in self.pages.values() if p.type == "Journey" and self.run_ref in (p.fm.get("run") or [])]
        page = self.upsert("Diagram", title, f"The Mermaid text of {name}.", file=name, ident="text",
                           fields={"diagram_kind": kind}, links={"journey": self.ref(journeys[0]) if len(journeys) == 1 else None},
                           item={"trailing_newlines": newlines}, replace_body=True,
                           body=f"\n# DIAGRAM: {title}\n\n{fence}mermaid\n{core}\n{fence}\n")
        page.body = page.body.replace("# DIAGRAM:", f"# {page.id}:", 1)
        self.skeletons[name] = MARK + page.id

    # ---- the body text ----------------------------------------------------------------------------

    @staticmethod
    def list_body(item, heading, key, name_keys) -> str | None:
        rows = []
        for entry in item.get(key) or []:
            if isinstance(entry, dict):
                label = first_text(*(entry.get(k) for k in name_keys[:1]))
                detail = first_text(*(entry.get(k) for k in name_keys[1:]))
                if label:
                    rows.append(f"- {clean(label, 80)}" + (f": {clean(detail, 120)}" if detail else ""))
        return ("\n## " + heading + "\n\n" + "\n".join(rows[:30]) + "\n") if rows else None

    @staticmethod
    def persona_body(item) -> str | None:
        rows = []
        for label, key in (("Goals", "goals"), ("Pain points", "pain_points"), ("Needs", "needs")):
            value = item.get(key)
            if isinstance(value, list) and value:
                parts = [v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) for v in value[:5]]
                rows.append(f"- {label}: " + "; ".join(clean(part, 80) for part in parts))
        return ("\n## Summary\n\n" + "\n".join(rows) + "\n") if rows else None

    @staticmethod
    def finding_body(item, text) -> str | None:
        quotes = item.get("quotes")
        if isinstance(quotes, list) and quotes:
            return "\n## Quotes\n\n" + "\n".join(f"> {clean(q, 300)}" for q in quotes[:10]) + "\n"
        return None

    # ---- write ------------------------------------------------------------------------------------

    def finish_bodies(self) -> None:
        for page in self.pages.values():
            if page.dirty and page.body is not None and not page.body.startswith("\n# "):
                # A body from a helper has no heading yet: put the heading and the description before it.
                page.body = f"\n# {page.id}: {page.fm['title']}\n\n{page.fm['description']}\n" + page.body

    def write_all(self) -> None:
        self.finish_bodies()
        for page in self.pages.values():
            if page.dirty:
                page.fm["generated"] = writer.stamp(self.actor)
                writer.write_page(self.root, page.path, page.fm, page.body, page.type, regenerate=False)


HANDLERS = {"research_findings.json": "h_research", "personas.json": "h_personas", "journey_maps.json": "h_journeys",
            "design_concepts.json": "h_concepts", "wireframes.json": "h_wireframes",
            "interaction_patterns.json": "h_patterns", "evaluation_report.json": "h_evaluation"}


@contextlib.contextmanager
def lock(root):
    folder = Path(root) / ARTIFACTS
    folder.mkdir(exist_ok=True)
    with open(folder / ".ingest.lock", "a") as handle:
        try:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX)
        except ImportError:  # no flock on this system: the run goes on without a lock
            pass
        yield


def temp_root(root):
    folder = bundle_dir(root)
    tmp = Path(tempfile.mkdtemp(prefix="ingest-", dir=Path(root) / ARTIFACTS))
    (tmp / ".claude").mkdir()
    shutil.copy(Path(root) / REGISTRY, tmp / REGISTRY)
    shutil.copytree(folder, tmp / folder.relative_to(root))
    return tmp


def swap(root, tmp) -> None:
    folder = bundle_dir(root)
    fresh, old = folder.with_name(folder.name + ".new"), folder.with_name(folder.name + ".old")
    # A `.new` or `.old` folder of an earlier stop would make the move put the new folder inside it.
    for stale in (fresh, old):
        if stale.exists():
            shutil.rmtree(stale)
    shutil.move(tmp / folder.relative_to(root), fresh)
    folder.rename(old)
    try:
        fresh.rename(folder)
    except OSError:
        old.rename(folder)  # the second rename failed: put the bundle back
        raise
    shutil.rmtree(old)


def output_folder(root, value) -> Path:
    """The output folder of the run: inside the project root, and not the root itself."""
    root = Path(root).resolve()
    given = Path(str(value))
    target = (given if given.is_absolute() else root / given).resolve()
    if root not in target.parents:
        raise UsageError(f"the output folder must be inside the project root, and not the root itself: {value!r}")
    if not target.is_dir():
        raise UsageError(f"{value} is not a folder")
    return target


def read_pages_file(folder):
    path = folder / PAGES_FILE
    if not path.is_file():
        return None, {}
    data = read_json(path)
    run_ref = data.get("run") if isinstance(data, dict) else None
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(run_ref, str) or not isinstance(files, dict):
        raise DataError(f"{PAGES_FILE} is not a pages file: it needs a run text and a files object. Remove it to start a new run.")
    return run_ref, files


def read_context(folder):
    path = folder / ".ux-config.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def run(root, output, phase, actor=None, new_run=False) -> list[str]:
    root = Path(root).resolve()
    actor = actor or schema.plugin_actor()
    if phase not in PHASES:
        raise UsageError(f"{phase!r} is not a phase: use {', '.join(PHASES)}")
    folder = output_folder(root, output)
    present = [name for name in PHASES[phase] if (folder / name).is_file()]
    if not present:
        raise DataError(f"{folder.name} has no file of the phase {phase}: {', '.join(PHASES[phase])}")
    # Read and check each file before the lock, so a file that is not valid stops here with nothing changed.
    data = {}
    for name in present:
        if name in DIAGRAMS:
            try:
                data[name] = (folder / name).read_bytes().decode("utf-8")
            except UnicodeDecodeError as error:
                raise DataError(f"{name}: the file is not UTF-8 text: {error}") from error
        else:
            data[name] = read_json(folder / name)
            walk_marks(data[name], name)
    lines = []
    with lock(root):
        run_ref, known = read_pages_file(folder)
        tmp = temp_root(root)
        try:
            ing = Ingest(tmp, actor, known)
            ing.start_run(phase, folder.relative_to(root).as_posix(), run_ref, read_context(folder), new_run)
            if not ing.joined:
                # A new Run page: the places of the earlier run are not its places, and pages.json gets only its own.
                known = ing.known = {}
            for name in present:
                if name in DIAGRAMS:
                    ing.h_diagram(name, data[name])
                else:
                    getattr(ing, HANDLERS[name])(name, data[name])
            meta = dict(ing.run_p.fm.get("file_meta") or {})
            meta.update(ing.skeletons)
            ing.run_p.fm["file_meta"] = meta
            ing.run_p.dirty = True
            ing.write_all()
            regen.write(ing.root)
            logbook.append(ing.dir / "log.md", "Ingest",
                           f"ingested the phase {phase} as {ing.run_ref}: {len(present)} files, "
                           f"{sum(1 for p in ing.pages.values() if p.dirty)} pages", actor)
            issues = check.run(ing.root)
            errors = [i for i in issues if i.level == ERROR]
            if errors:
                raise DataError("the check failed, so nothing was written and no file was removed:\n"
                                + "\n".join(i.text() for i in errors[:20]))
            swap(root, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    # A file that no page holds stays where it is, so no data goes with no trace.
    no_page = [name for name in present if name not in ing.touched]
    removed = [name for name in present if name in ing.touched]
    for name in removed:
        (folder / name).unlink()
    shutil.rmtree(folder / "inputs", ignore_errors=True)
    files = {**known, **ing.touched}
    (folder / PAGES_FILE).write_text(json.dumps({"run": ing.run_ref, "files": files}, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    lines += [f"NO PAGE: {name}: no page holds an item of the file, so ingest did not remove it" for name in no_page]
    lines.append(f"ingested the phase {phase} as {ing.run_ref}: {len(present)} files, removed {len(removed)}"
                 + (f", no page {len(no_page)}" if no_page else ""))
    warnings = [i.text() for i in issues if i.level != ERROR]
    lines += warnings[:10] + ([f"... and {len(warnings) - 10} more warnings"] if len(warnings) > 10 else [])
    return lines
