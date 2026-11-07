"""ingest: write the pages of a run from its session folder and its result file (spec rows 6 and 14).

Every file of a run becomes pages. The page of a merged type (Market, Competitor,
Offer, Source) is found by its key and added to. The other pages belong to one run.
`Run.file_meta[file]` keeps the skeleton of each JSON file: the file with each item
replaced by the marker `@@<page ID>`. The item itself is `record[file]` of its page.
`view` puts the file together again from the skeleton and the records.
"""
from __future__ import annotations

import contextlib
import fnmatch
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cilib import DataError, UsageError, check, logbook, regen, schema, view, writer
from cilib.bundle import DEFAULT_DIR, REGISTRY, bundle_dir, has_entry, inside, page_files, ref
from cilib.ids import fold, next_id
from cilib.issues import ERROR
from cilib.page import parse

CI_DIR = ".competitive-intelligence"
MARK, COMPUTED = view.MARK, view.COMPUTED
NO = object()

# The files that a reader reads. `ingest` writes their pages and keeps the file with the same bytes.
# The last reader story empties this list. Reader stories: STORY-92 (gtm) and STORY-89 (business-case).
READER_FILES = (
    "competitive-ecosystem.json",  # STORY-92
    "swot-analysis.json",  # STORY-92
    "swot-*.json",  # STORY-92
    "jtbd-analysis.json",  # STORY-92
    "results/*.json",  # STORY-89
)
LENSES = ("jtbd-performance", "forces-analysis", "economic-value", "strategic-positioning",
          "technology-disruption", "loss-churn")
QUADRANTS = (("strengths", "strength"), ("weaknesses", "weakness"), ("opportunities", "opportunity"),
             ("threats", "threat"))
REC_LISTS = (("strategic_recommendations", "strategic", "recommendation"),
             ("tactical_actions", "tactical", "action"),
             ("monitoring_recommendations", "monitoring", "what_to_monitor"))
FINDING_ID = re.compile(r"\bf-\d+\b")
PLACEHOLDER_MARKET = "Unnamed market"
# A shared page (MERGED_KEYS) keeps the value of the newest run for each field (STORY-185).
# `field_runs` names the run of each value. The order of 2 ingests does not change the graph.
FIELD_RUNS = writer.FIELD_RUNS
PERSON_RANK = ("\U0010ffff", "")  # a field that a person set (S1): newer than each run

SCOPED_KEYS = {
    "Finding": lambda f: (f.get("competitor"), f.get("item_id") or fold(f.get("title"))),
    "Gap": lambda f: (f.get("competitor"), fold(f.get("title"))),
    "LensResult": lambda f: (f.get("lens"), f.get("competitor")),
    "Moat": lambda f: (f.get("lens_result"), fold(f.get("title"))),
    "SwotItem": lambda f: (f.get("side"), f.get("quadrant"), fold(f.get("title")), f.get("competitor")),
    "Recommendation": lambda f: (f.get("rec_kind"), fold(f.get("title")), f.get("competitor")),
    "Change": lambda f: (f.get("competitor"), fold(f.get("title"))),
    "Threat": lambda f: (f.get("competitor"), fold(f.get("title"))),
    "Response": lambda f: (f.get("threat"), fold(f.get("title"))),
    "Validation": lambda f: (f.get("feature"),),
    "Archetype": lambda f: (f.get("competitor"),),
    "Summary": lambda f: (),
    "BattleCard": lambda f: (f.get("competitor"),),
    "Result": lambda f: ((f.get("aliases") or [None])[0],),
}
MERGED_KEYS = {
    "Market": lambda f: (fold(f.get("name")),),
    "Competitor": lambda f: (fold(f.get("name")), fold(f.get("website") or "")),
    "Offer": lambda f: (fold(f.get("name")), f.get("owner_kind"), f.get("competitor")),
    "Source": lambda f: (fold(f.get("resource")),),
}


class Skip(Exception):
    """A file that this run cannot map. The file stays where it is."""


def started(value) -> str:
    """A start time that sorts. A run with no start time, or with a time that is not ISO 8601, is the oldest."""
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def kept(name) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in READER_FILES)


def clean(text, limit=None) -> str:
    text = " ".join(str(text if text is not None else "").split())
    return text[:limit] if limit else text


def slug(text) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def walk_marks(value, name):
    if isinstance(value, str) and value.startswith(MARK):
        raise DataError(f"{name}: a text starts with {MARK}, which the page store keeps for its own markers: {value[:40]!r}")
    if isinstance(value, dict):
        for item in value.values():
            walk_marks(item, name)
    elif isinstance(value, list):
        for item in value:
            walk_marks(item, name)


class P:
    """A page in memory."""

    def __init__(self, path, type_, fm, body, new):
        self.path, self.type, self.fm, self.body, self.dirty = path, type_, fm, body, new

    @property
    def id(self):
        return self.path.stem


class Ingest:
    def __init__(self, root, actor):
        self.root = Path(root)
        self.dir = bundle_dir(root)
        self.actor = actor
        self.pages: dict[Path, P] = {}
        self.index: dict[tuple, Path] = {}
        self.numbers: dict[str, int] = {}
        self.touched: dict[str, dict] = {}
        self.cids: dict[str, Path] = {}
        self.names: dict[str, Path] = {}
        self.notes: dict[str, str] = {}
        self.market_page = None
        self.run_p = None
        self.run_ref = None
        self.session_id = ""
        self.ranks = {}
        self.start_note = ""
        for path in page_files(self.dir):
            page = parse(path)
            if page.error or not page.type:
                raise DataError(f"{path.name}: {page.error or 'the page has no type'}")
            self.pages[path] = P(path, page.type, page.frontmatter, page.body, False)

    # ---- pages in memory -------------------------------------------------------------------

    def ref(self, page) -> str:
        return ref(self.dir, page.path)

    def key(self, type_, fm):
        if type_ in MERGED_KEYS:
            return (type_, MERGED_KEYS[type_](fm))
        return (type_, self.run_ref) + SCOPED_KEYS[type_](fm)

    def build_index(self):
        for page in self.pages.values():
            if page.type in MERGED_KEYS:
                self.index[(page.type, MERGED_KEYS[page.type](page.fm))] = page.path
            elif page.type in SCOPED_KEYS:
                for run in page.fm.get("run") or []:
                    self.index[(page.type, run) + SCOPED_KEYS[page.type](page.fm)] = page.path

    def allocate(self, type_) -> Path:
        spec = schema.types()[type_]
        if type_ not in self.numbers:
            self.numbers[type_] = int(next_id(self.dir, type_).rsplit("-", 1)[1])
        number = self.numbers[type_]
        self.numbers[type_] += 1
        return self.dir / spec["directory"] / f"{spec['prefix']}-{number:02d}.md"

    def upsert(self, type_, title, desc, *, fields=None, links=None, file=None, item=NO, ident=None, placeholder=None,
               gives=True):
        # A page that a run writes or adds to is a draft until the person accepts it with `learn` (row 6, row 10).
        # `placeholder` is the description of a new page when the file gives none. It never replaces a description.
        # A run gets a `field_runs` entry only for a field that it gives: `gives=False` joins the page and claims none (M1).
        fm = {"type": type_, "title": clean(title),
              "description": clean(desc or placeholder or title, 200) or clean(title, 200), "status": "draft"}
        for slot, value in (fields or {}).items():
            if value is not None and schema.slot_ok(type_, slot, value):
                fm[slot] = value
        for slot, value in (links or {}).items():
            if value not in (None, [], ""):
                fm[slot] = value
        if type_ != "Run" and self.run_ref:
            fm["run"] = [self.run_ref]
        if type_ == "Run":
            key = ("Run", fm["run_id"])
        else:
            key = self.key(type_, fm)
        path = self.index.get(key)
        if path is None:
            path = self.allocate(type_)
            page = P(path, type_, {}, None, True)
            self.pages[path] = page
            self.index[key] = path
            page.fm = fm
            claimed = {slot: self.session_id for slot in fm
                       if gives and slot not in ("type", "status", "run") and (slot != "description" or desc)}
            if type_ in MERGED_KEYS and claimed:
                page.fm[FIELD_RUNS] = claimed
        else:
            page = self.pages[path]
            for slot, value in fm.items():
                if slot == "run":
                    page.fm["run"] = list(dict.fromkeys(list(page.fm.get("run") or []) + value))
                elif type_ not in MERGED_KEYS or slot in ("type", "status"):
                    page.fm[slot] = value
                elif gives and (slot != "description" or desc):
                    self.merge(page, slot, value)
            page.dirty = True
        if type_ == "Competitor":
            self.follow_name(page)
        if file and item is not NO:
            page.fm.setdefault("record", {})[self.record_key(type_, file)] = item
        if file:
            idents = self.touched.setdefault(file, {})
            idents[str(ident if ident is not None else f"item-{len(idents) + 1}")] = self.ref(page)
        return page

    def rank(self, run_id):
        """The order of a run for a shared page: its start time, then its run_id (STORY-185)."""
        if run_id == writer.PERSON_RUN:
            return PERSON_RANK
        return self.ranks.get(str(run_id), ("", str(run_id)))

    def merge(self, page, slot, value):
        """A shared page keeps the value of the newest run. In one run, the later file wins (STORY-185)."""
        runs = page.fm.setdefault(FIELD_RUNS, {})
        earlier = runs.get(slot)
        if earlier is not None and slot in page.fm and self.rank(earlier) > self.rank(self.session_id):
            return
        page.fm[slot] = value
        runs[slot] = self.session_id

    def record_key(self, type_, file) -> str:
        """A shared page holds the item of each run, so its key names the run. Any other page belongs to one run."""
        return f"{self.session_id}/{file}" if type_ in MERGED_KEYS else file

    def mark(self, page) -> str:
        return MARK + page.id

    def run_pages(self, type_):
        return [p for p in self.pages.values() if p.type == type_ and self.run_ref in (p.fm.get("run") or [])]

    def by_item_id(self, type_, ident):
        for page in self.run_pages(type_):
            prefix = f"{self.session_id}/" if type_ in MERGED_KEYS else ""
            records = [r for key, r in (page.fm.get("record") or {}).items()
                       if isinstance(r, dict) and key.startswith(prefix)]
            if ident and (page.fm.get("item_id") == ident or any(r.get("id") == ident for r in records)):
                return page
        return None

    def set_body(self, page, text):
        page.body = f"\n# {page.id}: {page.fm['title']}\n\n{text.strip()}\n"
        page.dirty = True

    def each(self, container, key, fn):
        value = container.get(key)
        if isinstance(value, list):
            container[key] = [fn(item, i) for i, item in enumerate(value)]

    # ---- the run ---------------------------------------------------------------------------

    def start_run(self, run_id, command, session_rel, header, session_data):
        self.session_id = run_id
        run = header.get("run") or {}
        fields = {
            "command": command, "run_id": run_id, "session_folder": session_rel,
            "plugin_version": header.get("plugin_version") or schema.plugin_version(),
            "started_at": run.get("started_at") or session_data.get("started_at"),
            "finished_at": run.get("finished_at"), "mode": run.get("mode") or session_data.get("mode"),
            "subject": run.get("subject"), "case": run.get("case") or session_data.get("case"),
            "answers": run.get("answers"),
        }
        for page in self.pages.values():
            if page.type == "Run" and page.fm.get("run_id") == run_id:
                self.index[("Run", run_id)] = page.path
        title = f"{command} run {run_id}"
        self.run_p = self.upsert("Run", title, run.get("subject") or f"A run of {command}.", fields=fields)
        self.run_ref = self.ref(self.run_p)
        # The rank of each run of the graph (STORY-185). No step of an ingest changes started_at after this line.
        self.ranks = {str(p.fm["run_id"]): (started(p.fm.get("started_at")), str(p.fm["run_id"]))
                      for p in self.pages.values() if p.type == "Run" and p.fm.get("run_id")}
        raw = self.run_p.fm.get("started_at")
        if raw and not started(raw):
            self.start_note = f"note: run {run_id} has no readable started_at ({raw!r}); its values rank oldest"
        self.build_index()
        for page in self.run_pages("Competitor"):
            if page.fm.get("item_id"):
                self.cids[page.fm["item_id"]] = page.path
            self.names[fold(page.fm.get("name"))] = page.path

    def set_run(self, **fields):
        for slot, value in fields.items():
            if value is not None and schema.slot_ok("Run", slot, value):
                self.run_p.fm[slot] = value
        self.run_p.dirty = True

    def market(self, name=None, gives=None):
        """The market page of the run. The run gives the name when it names the market (`name`, or its subject).
        It joins the one market of the graph, and gives no field of it, when it names none (STORY-185)."""
        if self.market_page is None or name:
            given = clean(name or self.run_p.fm.get("subject"))
            name = given or clean(self.only_market())
            self.adopt_placeholder_market(name)
            self.market_page = self.upsert("Market", name, f"The market: {name}", fields={"name": name},
                                           gives=bool(given) if gives is None else gives)
            self.run_p.fm["market"] = self.ref(self.market_page)
            self.run_p.dirty = True
        return self.market_page

    def adopt_placeholder_market(self, name):
        """A run that names its market finds the placeholder that an earlier run with no subject made, and gives it the name."""
        key = ("Market", (fold(name),))
        placeholders = [p for p in self.pages.values() if p.type == "Market" and p.fm.get("name") == PLACEHOLDER_MARKET]
        if name == PLACEHOLDER_MARKET or key in self.index or len(placeholders) != 1:
            return
        page = placeholders[0]
        self.index.pop(("Market", (fold(PLACEHOLDER_MARKET),)), None)
        self.index[key] = page.path
        page.fm["description"] = f"The market: {name}"
        page.body, page.dirty = None, True

    def only_market(self) -> str:
        """The market of a run that names none: the one market of the graph. A graph with no market gets a placeholder,
        and a graph with 2 or more markets gives no way to choose."""
        names = [p.fm.get("name") for p in self.pages.values() if p.type == "Market" and p.fm.get("name")]
        if len(names) > 1:
            raise DataError(f"the run names no market, and the graph holds {len(names)} markets ({', '.join(sorted(names))}): "
                            "ingest a run that names its market first")
        return names[0] if names else PLACEHOLDER_MARKET

    # ---- merged pages ----------------------------------------------------------------------

    def source(self, resource, source_type=None, date=None, accessed_at=None, confidence=None, file=None, item=NO,
               ident=None):
        page = self.upsert("Source", resource, None, file=file, item=item, ident=ident or resource,
                           fields={"resource": resource, "source_type": source_type, "date": date,
                                   "accessed_at": accessed_at, "confidence": confidence})
        # The description follows the kept source_type, so the 2 fields agree (STORY-185). A description that a
        # person wrote stays.
        if (page.fm.get(FIELD_RUNS) or {}).get("description") != writer.PERSON_RUN:
            page.fm["description"] = f"{page.fm.get('source_type') or 'A'} source"
        return page

    def source_item(self, name, entry, ident=None):
        if not isinstance(entry, dict):
            return entry
        resource = next((entry[k] for k in ("url", "file_path", "path", "ref") if isinstance(entry.get(k), str)), None)
        if resource is None:
            return entry
        page = self.source(resource, entry.get("type"), entry.get("date"), entry.get("accessed_at"),
                           entry.get("confidence"), name, entry, ident or entry.get("id"))
        return self.mark(page)

    def competitor(self, name, **fields):
        if not fields.get("website"):
            # No website, so the key (name, website) cannot find the page: use the one page of the graph with this name.
            found = [p for p in self.pages.values() if p.type == "Competitor" and fold(p.fm.get("name")) == fold(name)]
            if len(found) > 1:
                raise DataError(f"{name!r} is the name of {len(found)} competitors ({', '.join(p.id for p in found)}), "
                                "and the file gives no website to choose one")
            if found:
                page = found[0]
                page.fm["run"] = list(dict.fromkeys(list(page.fm.get("run") or []) + [self.run_ref]))
                page.dirty = True
                self.names[fold(name)] = page.path
                self.link_market(page)
                # The run gives the name and the market of the page, so these fields follow the rule (STORY-185).
                for slot, value in (("title", clean(name)), ("name", name), ("market", self.run_p.fm.get("market"))):
                    if value is not None:
                        self.merge(page, slot, value)
                self.follow_name(page)
                return page
        page = self.upsert("Competitor", name, fields.pop("description", None), placeholder=f"A competitor: {name}",
                           fields={"name": name, **fields}, links={"market": self.ref(self.market())})
        self.names[fold(name)] = page.path
        return page

    def link_market(self, page):
        """A run that adds to a competitor of the graph studies the market of that competitor (STORY-185)."""
        link = page.fm.get("market")
        market = next((p for p in self.pages.values() if self.ref(p) == link), None) if link else None
        if self.market_page is None and market is not None:
            self.market(market.fm.get("name"), gives=False)

    def follow_name(self, page):
        """A placeholder description names the kept name, so it does not depend on the order (STORY-185)."""
        text = clean(f"A competitor: {page.fm.get('name')}", 200)
        if (page.fm.get(FIELD_RUNS) or {}).get("description") == writer.PERSON_RUN:
            return
        if fold(page.fm.get("description")) == fold(text):
            page.fm["description"] = text

    def adopt_blank_competitor(self, name, website):
        """A file with a website finds the page that an earlier file with the same name and no website made."""
        key = ("Competitor", (fold(name), fold(website)))
        blanks = [p for p in self.pages.values()
                  if p.type == "Competitor" and fold(p.fm.get("name")) == fold(name) and not p.fm.get("website")]
        if key in self.index or len(blanks) != 1:
            return
        self.index.pop(("Competitor", (fold(name), "")), None)
        self.index[key] = blanks[0].path

    def comp_by_id(self, cid, name=None):
        if cid in self.cids:
            return self.pages[self.cids[cid]]
        if name and fold(name) in self.names:
            return self.pages[self.names[fold(name)]]
        if name:
            return self.competitor(name)
        raise DataError(f"unknown competitor id {cid!r}: no competitor of the run has this id")

    def comp_by_slug(self, text):
        for key, path in self.names.items():
            if slug(key) == text:
                return self.pages[path]
        return None

    def finding_refs(self, *texts):
        found = []
        for text in texts:
            for fid in FINDING_ID.findall(json.dumps(text) if not isinstance(text, str) else text):
                page = self.by_item_id("Finding", fid)
                if page and self.ref(page) not in found:
                    found.append(self.ref(page))
        return found

    # ---- one file --------------------------------------------------------------------------

    def h_metadata(self, name, data):
        skel, ctx = dict(data), data.get("analysis_context") or {}
        self.set_run(trigger=ctx.get("trigger"), scope=ctx.get("scope"), analysis_mode=ctx.get("analysis_mode"),
                     overall_confidence=data.get("overall_confidence"),
                     phases_executed=data.get("phases_executed"), lenses_applied=data.get("lenses_applied"))
        self.each(skel, "data_sources", lambda entry, i: self.source_item(name, entry))
        return skel

    def h_context(self, name, data):
        skel = dict(data)
        if isinstance(data.get("market"), str) and data["market"].strip():
            self.market(data["market"])
        self.set_run(trigger=data.get("trigger"), scope=data.get("scope"), analysis_mode=data.get("analysis_mode"),
                     depth=data.get("depth"), available_data=data.get("available_data"))
        own = data.get("own_offer")
        if isinstance(own, dict) and isinstance(own.get("name"), str):
            page = self.upsert("Offer", own["name"], f"The own offer: {own['name']}", file=name, ident="own_offer",
                               fields={"name": own["name"], "owner_kind": "own", "key_features": own.get("key_features"),
                                       "business_model": own.get("business_model")})
            if view.offer_view(page.fm) == own:
                skel["own_offer"] = self.mark(page)
        return skel

    def h_notes(self, name, text):
        self.notes[name] = text
        return NO

    def competitor_entry(self, name, entry, platform=False):
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            return entry
        fields = {k: entry.get(k) for k in ("website", "threat_level", "stage", "market_overlap", "tech_disruption_risk",
                                              "jtbd_alternative", "job_replaceability", "timeline", "confidence")}
        fields.update(competitor_type="ai_platform" if platform else entry.get("type"), item_id=entry.get("id"))
        if fields["website"]:
            self.adopt_blank_competitor(entry["name"], fields["website"])
        page = self.upsert("Competitor", entry["name"], entry.get("description") or entry.get("capability"),
                           placeholder=f"A competitor: {entry['name']}", fields={"name": entry["name"], **fields},
                           links={"market": self.ref(self.market())}, file=name, item=entry,
                           ident=entry.get("id") or entry["name"])
        self.names[fold(entry["name"])] = page.path
        if entry.get("id"):
            self.cids[entry["id"]] = page.path
        if entry.get("key_features") or entry.get("business_model"):
            self.upsert("Offer", entry["name"], f"The offer of {entry['name']}", links={"competitor": self.ref(page)},
                        fields={"name": entry["name"], "owner_kind": "competitor",
                                "key_features": entry.get("key_features"), "business_model": entry.get("business_model")})
        return self.mark(page)

    def h_ecosystem(self, name, data):
        skel = dict(data)
        self.market()
        self.each(skel, "competitors", lambda e, i: self.competitor_entry(name, e))
        self.each(skel, "ai_platforms", lambda e, i: self.competitor_entry(name, e, platform=True))
        if skel.get("ecosystem_summary") == view.ecosystem_summary(data.get("competitors") or []):
            skel["ecosystem_summary"] = COMPUTED
        return skel

    def h_sources(self, name, data):
        skel = dict(data)
        self.each(skel, "sources", lambda s, i: self.source_item(name, s))
        return skel

    def finding(self, name, comp, f):
        if not isinstance(f, dict) or not isinstance(f.get("finding"), str):
            return f
        sources = [self.ref(self.source(s["url"], s.get("type"), s.get("date")))
                   for s in f.get("sources") or [] if isinstance(s, dict) and isinstance(s.get("url"), str)]
        if not sources:
            # A Finding must link a Source page, and a Source page needs a url. A finding with no url source
            # (`"url": null`, `"sources": []`, no key) becomes a named Gap, so the run still ingests.
            gap = {"description": f"No source url for this finding: {f['finding']}", "type": "no_source"}
            return self.gap(name, comp, gap, f"{f.get('id') or slug(f['finding'])[:60]}-no-source")
        page = self.upsert("Finding", f["finding"], f["finding"], file=name, item=f, ident=f.get("id"),
                           fields={"category": f.get("category"), "confidence": f.get("confidence"),
                                   "triangulation": f.get("triangulation"), "relevance": f.get("relevance"),
                                   "item_id": f.get("id")},
                           links={"competitor": self.ref(comp), "source_pages": list(dict.fromkeys(sources))})
        return self.mark(page)

    def gap(self, name, comp, g, ident=None):
        if not isinstance(g, dict) or not isinstance(g.get("description"), str):
            return g
        page = self.upsert("Gap", g["description"], g["description"], file=name, item=g, ident=g.get("id") or ident,
                           fields={"gap_type": g.get("type"), "item_id": g.get("id")},
                           links={"competitor": self.ref(comp) if comp else None})
        return self.mark(page)

    def h_intel(self, name, data):
        skel = dict(data)
        if isinstance(data.get("competitors"), dict):
            skel["competitors"] = {}
            for cid, block in data["competitors"].items():
                if not isinstance(block, dict):
                    skel["competitors"][cid] = block
                    continue
                comp = self.comp_by_id(cid, block.get("name"))
                out = dict(block)
                self.each(out, "findings", lambda f, i: self.finding(name, comp, f))
                self.each(out, "gaps", lambda g, i: self.gap(name, comp, g, f"{cid}-gap-{i + 1}"))
                skel["competitors"][cid] = out
        if skel.get("summary") == view.intelligence_summary(data):
            skel["summary"] = COMPUTED
        return skel

    def h_gaps(self, name, data):
        skel = dict(data)
        self.each(skel, "gaps", lambda g, i: self.gap(
            name, self.pages.get(self.cids.get(g.get("competitor_id"))) if isinstance(g, dict) else None, g))
        return skel

    def lens_page(self, lens, comp, name, item, ident):
        return self.upsert("LensResult", f"{lens} of {comp.fm['name']}", f"The {lens} lens for {comp.fm['name']}.",
                           fields={"lens": lens}, links={"competitor": self.ref(comp)}, file=name, item=item,
                           ident=ident)

    def lens_list(self, lens, key, extra=None):
        def handler(name, data):
            skel = dict(data)

            def one(item, i):
                if not isinstance(item, dict) or "competitor_id" not in item:
                    return item
                comp = self.comp_by_id(item["competitor_id"])
                page = self.lens_page(lens, comp, name, NO, item["competitor_id"])
                page.fm.setdefault("record", {})[name] = extra(name, item, comp, page) if extra else item
                return self.mark(page)

            self.each(skel, key, one)
            return skel

        return handler

    def moats(self, name, item, comp, lens_page):
        out = dict(item)

        def moat(m, i):
            if not isinstance(m, dict):
                return m
            title = m.get("name") or m.get("type") or m.get("description") or f"Moat {i + 1}"
            page = self.upsert("Moat", title, m.get("description") or title, file=name, item=m, ident=f"{item['competitor_id']}-{i + 1}",
                               links={"competitor": self.ref(comp), "lens_result": self.ref(lens_page)})
            return self.mark(page)

        self.each(out, "moats", moat)
        return out

    def h_technology(self, name, data):
        platforms = [a.get("platform") for a in data.get("ai_platforms") or [] if isinstance(a, dict)]
        comp = next((self.pages[self.names[fold(p)]] for p in platforms if p and fold(p) in self.names), None)
        if comp is None and self.cids:
            comp = self.pages[next(iter(self.cids.values()))]
        if comp is None:
            raise DataError(f"{name}: the run has no competitor to attach the lens to")
        return self.mark(self.lens_page("technology-disruption", comp, name, data, "technology"))

    def h_analysis(self, name, data):
        comp = self.comp_by_id(data.get("competitor_id"), data.get("competitor"))
        skel = dict(data)
        if isinstance(data.get("lenses"), dict):
            skel["lenses"] = {
                key: (self.mark(self.lens_page(key, comp, name, value, key)) if key in LENSES and isinstance(value, dict)
                      else value)
                for key, value in data["lenses"].items()}
        if isinstance(data.get("lens_failures"), dict):
            skel["lens_failures"] = {
                key: self.mark(self.upsert(
                    "Gap", f"The {key} lens failed for {comp.fm['name']}", clean(value) or "The lens failed.",
                    fields={"gap_type": "lens_failure"}, links={"competitor": self.ref(comp)}, file=name, item=value,
                    ident=f"lens_failure:{key}"))
                for key, value in data["lens_failures"].items()}
        return skel

    def swot_item(self, name, item, quadrant, text_key, side, comp, i):
        if isinstance(item, str) and item.strip():
            # The SWOT Format Standard of agents/synthesizer.md writes an item as 1 sentence (STORY-208).
            item = {text_key: item}
        if not isinstance(item, dict) or not isinstance(item.get(text_key), str):
            return item
        text = item[text_key]
        cites = self.finding_refs(item.get("evidence"), item.get("rationale"))
        page = self.upsert("SwotItem", text, item.get("rationale") or text, file=name, item=item, ident=f"{quadrant}-{i + 1}",
                           fields={"quadrant": quadrant, "side": side, "evidence": item.get("evidence"),
                                   "confidence": item.get("confidence"), "relative_to": item.get("relative_to"),
                                   "impact": item.get("impact"), "rationale": item.get("rationale"),
                                   "size": item.get("size"), "timeline": item.get("timeline"),
                                   "item_source": item.get("source"), "severity": item.get("severity"),
                                   "likelihood": item.get("likelihood")},
                           links={"competitor": self.ref(comp) if comp else None, "cites": cites})
        return self.mark(page)

    def swot_block(self, name, block, side, comp):
        out = dict(block)
        for plural, quadrant in QUADRANTS:
            self.each(out, plural, lambda it, i: self.swot_item(name, it, quadrant, quadrant, side, comp, i))
        return out

    def h_swot_market(self, name, data):
        return self.swot_block(name, data, "own", None)

    def h_swot_competitor(self, name, data):
        """The competitor of swot-<competitor>.json is, in this order: competitor_id, the name in competitor (as
        h_analysis reads it), the name in competitor_swot, and the <competitor> part of the file name (STORY-208)."""
        swot = data.get("competitor_swot") if isinstance(data.get("competitor_swot"), dict) else {}
        cid = data.get("competitor_id")
        named = next((v for v in (data.get("competitor"), swot.get("name")) if isinstance(v, str) and v.strip()), None)
        if cid in self.cids or named:
            comp = self.comp_by_id(cid, named)
        else:
            comp = self.comp_by_slug(name[len("swot-"):-len(".json")])
        if comp is None:
            raise DataError(f"{name}: no competitor of the run matches competitor_id, competitor, "
                            "competitor_swot.name or the name of the file")
        skel = dict(data)
        for key, side in (("competitor_swot", "competitor"), ("your_swot", "own")):
            if isinstance(data.get(key), dict):
                skel[key] = self.swot_block(name, data[key], side, comp)
        return skel

    def rec(self, name, item, kind, text_key, comp, i, desc_key="rationale"):
        if not isinstance(item, dict) or not isinstance(item.get(text_key), str):
            return item
        page = self.upsert("Recommendation", item[text_key], item.get(desc_key) or item[text_key], file=name, item=item,
                           ident=f"{kind}-{i + 1}",
                           fields={"rec_kind": kind, "priority": item.get("priority"),
                                   "confidence": item.get("confidence"), "timeline": item.get("timeline")},
                           links={"competitor": self.ref(comp) if comp else None,
                                  "cites": self.finding_refs(item.get("rationale"), item.get("evidence"),
                                                             item.get("answer"))})
        return self.mark(page)

    def h_recommendations(self, name, data):
        comp = self.comp_by_slug(name[len("recommendations-"):-len(".json")]) if name != "recommendations.json" else None
        skel = dict(data)
        for key, kind, text_key in REC_LISTS:
            self.each(skel, key, lambda it, i: self.rec(name, it, kind, text_key, comp, i))
        return skel

    def h_implications(self, name, data):
        skel = dict(data)
        self.each(skel, "implications", lambda it, i: self.rec(name, it, "implication", "question", None, i, "answer"))
        return skel

    def h_monitoring(self, name, data):
        return dict(data)

    def h_changes(self, name, data):
        skel = dict(data)

        def change(item, i):
            if not isinstance(item, dict) or not isinstance(item.get("description"), str):
                return item
            comp = self.comp_by_id(item.get("competitor_id"))
            sources = [self.ref(self.source(s["url"], s.get("type"), s.get("date")))
                       for s in item.get("sources") or [] if isinstance(s, dict) and isinstance(s.get("url"), str)]
            page = self.upsert("Change", item["description"], item["description"], file=name, item=item,
                               ident=item.get("id"),
                               links={"competitor": self.ref(comp), "source_pages": list(dict.fromkeys(sources))})
            return self.mark(page)

        self.each(skel, "changes", change)
        return skel

    def h_threat(self, name, data):
        comp = self.comp_by_id(data.get("competitor_id"))
        change = self.by_item_id("Change", data.get("change_id"))
        page = self.upsert("Threat", data.get("title") or name, data.get("title") or name, file=name, item=data,
                           ident=data.get("id"),
                           links={"competitor": self.ref(comp), "change": self.ref(change) if change else None})
        return self.mark(page)

    def threat_of(self, name, data):
        threat = self.by_item_id("Threat", data.get("threat_id"))
        if threat is None:
            raise DataError(f"{name}: no threat {data.get('threat_id')!r} in the run")
        return threat

    def h_options(self, name, data):
        threat = self.threat_of(name, data)
        skel = dict(data)

        def option(opt, i):
            if not isinstance(opt, dict) or not isinstance(opt.get("name"), str):
                return opt
            page = self.upsert("Response", opt["name"], opt.get("description") or opt["name"], file=name, item=opt,
                               ident=opt.get("id"), fields={"chosen": False}, links={"threat": self.ref(threat)})
            return self.mark(page)

        self.each(skel, "options", option)
        return skel

    def h_plan(self, name, data):
        threat = self.threat_of(name, data)
        for page in self.run_pages("Response"):
            record = (page.fm.get("record") or {}).get(f"response-options-{name[len('response-plan-'):]}")
            if page.fm.get("threat") == self.ref(threat) and isinstance(record, dict):
                page.fm["chosen"] = record.get("id") == data.get("chosen_option")
                page.dirty = True
                if page.fm["chosen"]:
                    steps = "\n".join(f"{s.get('step')}. {s.get('action')} ({s.get('owner')}, {s.get('due')})"
                                      for s in data.get("steps") or [] if isinstance(s, dict))
                    self.set_body(page, f"{data.get('rationale') or ''}\n\n## Plan\n\n{steps}")
        return dict(data)

    def h_validation(self, name, data):
        feature = clean(data.get("feature"))
        if not feature:
            raise DataError(f"{name}: the file has no feature")
        found = self.index.get(("Offer", (fold(data.get("offer")), "own", None)))
        offer = self.pages[found] if found else None
        scan = [c.get("competitor_id") for c in data.get("competitive_scan") or [] if isinstance(c, dict)]
        ids = [c for c in (data.get("competitors") or scan) if isinstance(c, str)]
        comps = [self.ref(self.pages[self.cids[c]]) for c in ids if c in self.cids]
        page = self.upsert("Validation", f"Validation of {feature}", clean(data.get("description") or data.get("reasoning") or feature, 200),
                           file=name, item=data, ident=feature, fields={"feature": feature},
                           links={"offer": self.ref(offer) if offer else None, "competitors": list(dict.fromkeys(comps))})
        return self.mark(page)

    def h_archetype(self, name, data):
        vendor = clean(data.get("vendor_name"))
        if not vendor:
            raise DataError(f"{name}: the file has no vendor_name")
        comp = self.pages[self.names[fold(vendor)]] if fold(vendor) in self.names else self.competitor(vendor)
        sources = []
        if isinstance(data.get("pricing_page_url"), str):
            sources = [self.ref(self.source(data["pricing_page_url"], "pricing_page"))]
        page = self.upsert("Archetype", f"Archetype of {vendor}", f"{vendor} is a {data.get('archetype')} vendor.",
                           file=name, item=data, ident=vendor,
                           links={"competitor": self.ref(comp), "source_pages": sources})
        return self.mark(page)

    def h_summary(self, name, text):
        page = self.upsert("Summary", f"Executive summary of {self.session_id}", clean(text.lstrip("# \n"), 160) or "The summary.")
        self.set_body(page, text)
        self.touched.setdefault(name, {})["summary"] = self.ref(page)
        return NO

    def h_battle_card(self, name, text):
        label = name[len("battle-card-"):-len(".md")]
        comp = self.comp_by_slug(label)
        if comp is None:
            raise Skip(f"{name}: no competitor of the run has the name {label!r}")
        page = self.upsert("BattleCard", f"Battle card for {comp.fm['name']}", clean(text.lstrip("# \n"), 160) or "The card.",
                           links={"competitor": self.ref(comp)})
        self.set_body(page, text)
        self.touched.setdefault(name, {})[label] = self.ref(page)
        return NO

    # ---- the result file -------------------------------------------------------------------

    def about(self, entry):
        kind, label, value = entry.get("kind"), entry.get("label"), entry.get("value")
        if kind in ("competitor", "alternative"):
            names = {fold(label)} | ({fold(value["name"])} if isinstance(value, dict) and value.get("name") else set())
            hits = [p for p in self.run_pages("Competitor") if fold(p.fm.get("name")) in names]
        else:
            type_ = "Finding" if kind == "timing_reason" else "SwotItem"
            hits = [p for p in self.run_pages(type_) if fold(p.fm.get("title")) == fold(label)]
        return hits[0] if len(hits) == 1 else None

    def result_file(self, name, data):
        skel_name = f"results/{name}"
        for gap in data.get("gaps") or []:
            if isinstance(gap, dict):
                label = clean(gap.get("label")) or "A gap"
                self.upsert("Gap", label, gap.get("why") or label, file=skel_name, item=gap, ident=label,
                            fields={"kind": gap.get("kind"), "why": gap.get("why")})
        made, wanted = {}, []
        for entry in data.get("results") or []:
            alias = f"{self.session_id}/{entry['id']}"
            if alias in made:
                raise DataError(f"{name}: the id {entry['id']!r} is in the file twice")
            sources = entry.get("sources") or []
            okf = []
            for source in sources:
                found = self.index.get(("Source", (fold(source.get("ref")),))) if isinstance(source, dict) else None
                if found and source.get("type") in ("published", "customer_data"):
                    okf.append({"id": found.stem, "resource": source["ref"]})
            about = self.about(entry)
            page = self.upsert(
                "Result", entry.get("label"), entry.get("method") or entry.get("label"), file=None, ident=entry["id"],
                fields={"kind": entry.get("kind"), "label": entry.get("label"), "value": entry.get("value"),
                        "unit": entry.get("unit"), "period": entry.get("period"), "result_sources": sources,
                        "sources": okf or None, "method": entry.get("method"), "rests_on_default": entry.get("rests_on_default"),
                        "defaults": entry.get("defaults"), "confidence": entry.get("confidence"), "aliases": [alias]},
                links={"about": self.ref(about) if about else None})
            self.touched.setdefault(skel_name, {})[entry["id"]] = self.ref(page)
            made[alias] = page
            wanted.append((page, entry))
        for page, entry in wanted:
            cites = []
            for cite in entry.get("cites") or []:
                target = made.get(f"{self.session_id}/{cite.get('result_id')}") if isinstance(cite, dict) else None
                if target is None:
                    raise DataError(f"{name}: result {entry['id']!r} cites a result that the file does not hold: {cite!r}")
                cites.append(self.ref(target))
            if cites:
                page.fm["cites"] = cites
                page.dirty = True

    # ---- write -----------------------------------------------------------------------------

    def write_all(self):
        stamp = writer.stamp(self.actor)
        for page in self.pages.values():
            if not page.dirty:
                continue
            page.fm["generated"] = stamp
            body = page.body
            if body is None:
                body = f"\n# {page.id}: {page.fm['title']}\n\n{page.fm['description']}\n"
            try:
                writer.write_page(self.root, page.path, page.fm, body, page.type, regenerate=False)
            except DataError as error:
                raise DataError(f"{page.path.name}: {error}") from error


HANDLERS = (
    ("metadata.json", "h_metadata"), ("context-config.json", "h_context"), ("context-notes.md", "h_notes"),
    ("competitive-ecosystem.json", "h_ecosystem"), ("ecosystem-notes.md", "h_notes"), ("sources.json", "h_sources"),
    ("intelligence-data.json", "h_intel"), ("gaps.json", "h_gaps"),
    ("jtbd-analysis.json", ("lens_list", "jtbd-performance", "competitor_performance")),
    ("forces-analysis.json", ("lens_list", "forces-analysis", "competitors")),
    ("value-analysis.json", ("lens_list", "economic-value", "competitors")),
    ("strategic-analysis.json", ("lens_list", "strategic-positioning", "competitors", "moats")),
    ("technology-disruption.json", "h_technology"),
    ("loss-churn-analysis.json", ("lens_list", "loss-churn", "win_loss_patterns")),
    ("analysis-*.json", "h_analysis"), ("swot-analysis.json", "h_swot_market"), ("swot-*.json", "h_swot_competitor"),
    ("recommendations.json", "h_recommendations"), ("recommendations-*.json", "h_recommendations"),
    ("strategic-implications.json", "h_implications"), ("monitoring-*.json", "h_monitoring"),
    ("changes-*.json", "h_changes"), ("threat-*.json", "h_threat"), ("response-options-*.json", "h_options"),
    ("response-plan-*.json", "h_plan"), ("validation-*.json", "h_validation"),
    ("vendor-archetype-classification.json", "h_archetype"), ("executive-summary.md", "h_summary"),
    ("battle-card-*.md", "h_battle_card"),
)

# The handlers whose file the Run page holds by design: in Run fields (metadata, context), in the Run body (notes),
# or only in `file_meta` (monitoring, plan). Such a file can give no item page, and ingest still removes it (STORY-217).
RUN_PAGE_HANDLERS = ("h_metadata", "h_context", "h_notes", "h_monitoring", "h_plan")


def handler_for(ing, spec):
    if isinstance(spec, str):
        return getattr(ing, spec)
    _, lens, key, *more = spec
    return ing.lens_list(lens, key, ing.moats if more else None)


def read_json(path):
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DataError(f"{Path(path).name}: cannot read the file as JSON: {error}") from error


def first_anchor(ing, value):
    """The first page of a scoped type with a record slot that the skeleton names."""
    if isinstance(value, str) and value.startswith(MARK) and value != COMPUTED:
        page = ing.pages.get(ing.dir / schema.types()[schema.by_prefix()[value[len(MARK):].rsplit("-", 1)[0]]]["directory"]
                             / f"{value[len(MARK):]}.md")
        return page if page and page.type in SCOPED_KEYS and schema.slot_ok(page.type, "record", {}) else None
    items = value.values() if isinstance(value, dict) else value if isinstance(value, list) else ()
    return next((found for found in map(lambda item: first_anchor(ing, item), items) if found), None)


def store_skeleton(ing, name, skeleton):
    """Keep the skeleton of a file where the page stays small: in the Run page, on the first page of the
    file, or, for a file with no page, as one line of compact JSON."""
    meta = ing.run_p.fm.setdefault("file_meta", {})
    if len(json.dumps(skeleton, indent=1).splitlines()) <= 6:
        # A short skeleton is one line of compact JSON, so that the Run page stays under 100 lines.
        meta[name] = skeleton if isinstance(skeleton, str) else "json:" + json.dumps(skeleton, separators=(",", ":"), ensure_ascii=False)
        return
    anchor = first_anchor(ing, skeleton)
    if anchor is not None:
        anchor.fm.setdefault("record", {})[name + "#"] = skeleton
        anchor.dirty = True
        meta[name] = f"{MARK}{anchor.id}#"
    else:
        meta[name] = "json:" + json.dumps(skeleton, separators=(",", ":"), ensure_ascii=False)


def process(ing, files, result):
    """Map each file to pages. Return the names of the files that were ingested."""
    done, notes = [], []
    claimed = set()
    for pattern, spec in HANDLERS:
        for path in files:
            if path.name in claimed or not fnmatch.fnmatch(path.name, pattern):
                continue
            claimed.add(path.name)
            is_json = path.suffix == ".json"
            data = read_json(path) if is_json else path.read_text("utf-8")
            if is_json:
                if not isinstance(data, dict):
                    raise DataError(f"{path.name}: the file is not a JSON object")
                walk_marks(data, path.name)
            try:
                skeleton = handler_for(ing, spec)(path.name, data)
            except Skip as skip:
                notes.append(f"SKIP: {skip}")
                continue
            if skeleton is not NO:
                store_skeleton(ing, path.name, skeleton)
            done.append(path.name)
            if spec in RUN_PAGE_HANDLERS:
                ing.touched.setdefault(path.name, {})  # so pages.json names the file
    if result is not None:
        ing.result_file(result[0], result[1])
    return done, notes


def run_notes(ing):
    if ing.notes:
        parts = [f"## {name.rsplit('.', 1)[0].replace('-', ' ').capitalize()}\n\n{text.strip()}"
                 for name, text in sorted(ing.notes.items())]
        ing.set_body(ing.run_p, "\n\n".join(parts))


@contextlib.contextmanager
def lock(root):
    folder = Path(root) / CI_DIR
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
    tmp = Path(tempfile.mkdtemp(prefix="ingest-", dir=Path(root) / CI_DIR))
    (tmp / ".claude").mkdir()
    shutil.copy(Path(root) / REGISTRY, tmp / REGISTRY)
    shutil.copytree(folder, tmp / folder.relative_to(root))
    return tmp


def swap(root, tmp):
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


def inputs(root, path, result_file):
    """Return (session folder or None, content files, result (name, data) or None)."""
    if path is None and result_file is None:
        raise UsageError("give a session folder, a file, or --result FILE")
    session, files = None, []
    if path is not None:
        target = inside(root, path)
        if target.is_dir():
            session, files = target, sorted(inside(root, p.relative_to(root)) for p in target.iterdir() if p.is_file())
        elif target.is_file():
            files = [target]
        else:
            raise UsageError(f"{path} is not a file or a folder")
    result = None
    if result_file is not None:
        target = inside(root, result_file)
        if not target.is_file():
            raise UsageError(f"{result_file} is not a file")
        result = (target.name, read_json(target))
        if not isinstance(result[1], dict) or not isinstance(result[1].get("run"), dict):
            raise DataError(f"{target.name}: the file is not a plugin result file (it has no run object)")
    return session, files, result


def run_identity(session, files, result):
    header = result[1] if result else {}
    run_id = (header.get("run") or {}).get("run_id")
    command = header.get("command")
    session_data = {}
    if session is not None:
        run_id = run_id or session.name
        if (session / "session.json").is_file():
            session_data = read_json(session / "session.json")
        command = command or session_data.get("command")
    elif files:
        digest = hashlib.sha256(files[0].read_bytes()).hexdigest()[:8]
        run_id = run_id or f"{files[0].stem}-{digest}"
        command = command or "competitive-intelligence:vendor-archetype-classify"
    if not run_id:
        raise DataError("the result file has no run.run_id")
    return run_id, command or "competitive-intelligence", header, session_data


def run(root, path=None, result_file=None, actor=None) -> list[str]:
    root = Path(root).resolve()
    actor = actor or schema.plugin_actor()
    session, files, result = inputs(root, path, result_file)
    lines = []
    with lock(root):
        # Inside the lock, because 2 first runs at the same time must not both run init.
        if not has_entry(root):
            writer.init(root, DEFAULT_DIR, actor)
            lines.append(f"INIT: {DEFAULT_DIR}/")
        tmp = temp_root(root)
        try:
            ing = Ingest(tmp, actor)
            run_id, command, header, session_data = run_identity(session, files, result)
            rel = session.relative_to(root).as_posix() if session and root in session.parents else None
            ing.start_run(run_id, command, rel, header, session_data)
            done, notes = process(ing, files, result)
            if not done and ((session is None and files) or result is None):
                names = ", ".join(p.name for p in files) or "the folder"
                raise DataError(f"no file was ingested from {names}: ingest reads no file with this name, or it skipped the file"
                                + "".join(f"\n{note}" for note in notes))
            run_notes(ing)
            ing.write_all()
            regen.write(ing.root)
            writer_log = f"ingested {run_id}: {len(done)} files, {sum(1 for p in ing.pages.values() if p.dirty)} pages"
            logbook.append(ing.dir / "log.md", "Ingest", writer_log, actor)
            issues = check.run(ing.root)
            errors = [i for i in issues if i.level == ERROR]
            if errors:
                raise DataError("the check failed, so nothing was written and no file was removed:\n"
                                + "\n".join(i.text() for i in errors[:20]))
            swap(root, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    # A file that no page holds stays where it is, so no data goes with no trace (STORY-217).
    no_page = [name for name in done if name not in ing.touched]
    removed = [name for name in done if name in ing.touched and not kept(name)]
    for name in removed:
        ((session or files[0].parent) / name).unlink()
    if session is not None:
        pages_path = session / "pages.json"
        known = read_json(pages_path).get("files", {}) if pages_path.is_file() else {}
        known.update(ing.touched)
        pages_path.write_text(json.dumps({"run": ing.run_ref, "files": known}, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
    lines += notes
    lines += [f"NO PAGE: {name}: no page holds an item of the file, so ingest did not remove it" for name in no_page]
    lines += [ing.start_note] if ing.start_note else []
    lines.append(f"ingested {run_id} as {ing.run_ref}: {len(done)} files, removed {len(removed)}, "
                 f"kept {len(done) - len(removed)}" + (f", no page {len(no_page)}" if no_page else ""))
    warnings = [i.text() for i in issues if i.level != ERROR]
    lines += warnings[:10] + ([f"... and {len(warnings) - 10} more warnings"] if len(warnings) > 10 else [])
    return lines
