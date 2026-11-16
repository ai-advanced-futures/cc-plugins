#!/usr/bin/env python3
"""Build and check invented, filesystem-only ask datasets. No model calls are made."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import posixpath
import re
import sys
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.dont_write_bytecode = True
BUNDLE_DIR = "docs/knowledge/bundle"
TYPE_FOLDERS = {"Source": "sources", "Entity": "entities", "Concept": "concepts",
                "Synthesis": "synthesis", "OpenQuestion": "open-questions"}


def load_save_code():
    """Load the graph writer only for builds; checks use the standard library."""
    global graph, graph_check, graph_ops, graph_regen, okf
    sys.path.insert(0, str(SCRIPTS))
    from knowledgelib import graph, graph_check, graph_ops, graph_regen, okf


DATASETS = Path(__file__).resolve().parent / "datasets"
SHAPES = ("correction", "conflict", "open", "absent", "paraphrase", "multi-page", "conditional")
PINNED_DATE = "2042-02-03T00:00:00Z"
GRAPH_VERSION = "1.8.0"
ACTOR = "process:synthetic-dataset-builder"
SPECS = {
    "smoke-1": {"pages": 50, "questions": 12, "organization": "Mossglass Gardens", "base": 20,
                "areas": ["Amber", "Birch", "Clover", "Dew"],
                "objects": ["seed dryer", "water cart", "soil sieve"],
                "roles": ["seed keeper", "water steward", "bed warden"],
                "stores": ["potting shed", "north glasshouse", "tool porch"]},
    "tuning-1": {"pages": 120, "questions": 36, "organization": "Copperfin Repair House", "base": 70,
                 "areas": ["Brass", "Cobalt", "Flint", "Ivory", "Slate", "Tin"],
                 "objects": ["wheel stand", "pump bench", "lamp cradle", "gear press", "valve rack", "cable jig"],
                 "roles": ["bench coordinator", "parts custodian", "safety checker"],
                 "stores": ["parts loft", "repair hall", "loading room"]},
    "benchmark-1": {"pages": 340, "questions": 60, "organization": "Velvet Horizon Observatory", "base": 130,
                    "areas": ["Aster", "Beacon", "Comet", "Drift", "Ember", "Frost", "Halo", "Lumen", "Nova", "Orbit"],
                    "objects": ["lens carrier", "clock mount", "mirror frame", "shutter drive", "sensor tray", "filter drum"],
                    "roles": ["night coordinator", "optics custodian", "instrument checker"],
                    "stores": ["dome store", "calibration room", "east annex"]},
}


class FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2042, 2, 3, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


def fact(text, path):
    return {"text": text, "evidence": [{"node": "knowledge:" + path, "quote": text}]}


def case_data(dataset, spec, number):
    """Return three related records and one question, before paths are assigned."""
    shape = SHAPES[number % len(SHAPES)]
    subject = f"{spec['areas'][number // len(spec['objects'])]} {spec['objects'][number % len(spec['objects'])]}"
    org = spec["organization"]
    role = spec["roles"][number % 3]
    store = spec["stores"][(number + 1) % 3]
    n = spec["base"] + number * 3
    shared = [f"The {subject} belongs to {org}.", f"The {role} keeps the records for the {subject}."]
    a, b, key, context, forbidden = [], [], [], [], []
    if shape == "correction":
        a = [f"The first service card gives the inspection interval for the {subject} as {n + 9} days.",
             "The first service card was issued on 4 January 2041."]
        b = [f"The inspection interval for the {subject} is {n} days.",
             f"The notice of 8 February 2041 replaces the first service card for the {subject}.",
             f"The {n + 9}-day interval on the first service card is a copying error.",
             f"The first service card for the {subject} is no longer valid."]
        question = f"How often must {org} inspect the {subject}, and is the first service card still valid?"
        key = [(b[0], 1), (b[3], 1)]
        context = [(a[0], 0), (b[1], 1), (b[2], 1)]
        forbidden = [f"The inspection interval for the {subject} is {n + 9} days."]
        summary = f"Use the replacement notice, not the old service card, for the {subject}."
    elif shape == "conflict":
        a = [f"The day-shift ledger lists {n} spare seals for the {subject}.",
             f"The day-shift count for the {subject} was made on 12 April 2041."]
        b = [f"The night-shift ledger lists {n + 7} spare seals for the {subject}.",
             f"The night-shift count for the {subject} was made on 12 April 2041."]
        question = f"How many spare seals does {org} hold for the {subject}, and can we use one confirmed count?"
        key = [(a[0], 0), (b[0], 1), (f"Neither ledger for the {subject} has been checked against the store.", 2)]
        context = [(a[1], 0), (b[1], 1)]
        forbidden = [f"The confirmed spare seal count for the {subject} is {n}.",
                     f"The confirmed spare seal count for the {subject} is {n + 7}."]
        summary = f"Neither ledger for the {subject} has been checked against the store."
    elif shape == "open":
        a = [f"The {subject} needs a replacement safety cover.",
             f"The repair request for the {subject} was filed on 6 May 2041."]
        b = [f"The {role} proposed a cover supplier for the {subject}.",
             f"The committee deferred the supplier decision for the {subject} until a load test is complete."]
        summary = f"No supplier has been approved for the safety cover of the {subject}."
        question = f"Who has been approved to supply the safety cover for the {subject}, and what is blocking the choice?"
        key = [(summary, 2), (b[1], 1)]
        context = [(a[0], 0), (b[0], 1)]
        forbidden = [f"The {role}'s proposed supplier is approved for the {subject}."]
    elif shape == "absent":
        a = [f"The asset sheet records the storage location and custodian of the {subject}.",
             f"The {subject} is stored in the {store}."]
        b = [f"The inventory review found no purchase price for the {subject} in these records.",
             f"The inventory review for the {subject} covers the asset sheet and the receipt register."]
        summary = f"The purchase price of the {subject} is not recorded in this graph."
        question = f"What did {org} pay to buy the {subject}? What information is actually available?"
        key = [(summary, 2), (a[1], 0)]
        context = [(b[0], 1), (b[1], 1)]
        forbidden = [f"The purchase price of the {subject} was zero.",
                     f"The purchase price of the {subject} can be calculated from its storage location."]
    elif shape == "paraphrase":
        a = [f"A return-to-service check is required after the {subject} is moved between buildings.",
             f"The return-to-service check for the {subject} takes {n} minutes."]
        b = [f"The {role} must sign the return-to-service check for the {subject}.",
             f"The movement log for the {subject} is kept in the {store}."]
        summary = f"The {subject} cannot be used until its return-to-service check is signed."
        question = f"After we take the {subject} to another building, what must happen before we use it, how long does it take, and who signs?"
        key = [(a[0], 0), (a[1], 0), (b[0], 1)]
        context = [(summary, 2), (b[1], 1)]
        forbidden = [f"The {subject} can be used immediately after it is moved."]
    elif shape == "multi-page":
        a = [f"Before transporting the {subject}, fasten the two transit clips.",
             f"The transit clips for the {subject} are kept in the {store}."]
        b = [f"After transporting the {subject}, run the alignment check.",
             f"Only the {role} can release the {subject} after the alignment check.",
             f"Remove the transit clips from the {subject} before its alignment check."]
        summary = f"The transport record for the {subject} must include both the departure check and the arrival check."
        question = f"Give the steps before and after transporting the {subject}, including who can release it."
        key = [(a[0], 0), (b[2], 1), (b[0], 1), (b[1], 1)]
        context = [(a[1], 0), (summary, 2)]
        forbidden = [f"Leave the transit clips attached when using the {subject}."]
    else:
        a = [f"The normal inspection interval for the {subject} is {n} days.",
             f"The normal interval for the {subject} applies only in a dry room."]
        b = [f"If room humidity exceeds {55 + number % 15} percent, inspect the {subject} every {n - 6} days.",
             f"The shorter interval for the {subject} ends after two consecutive dry readings."]
        summary = f"The {role} records room humidity for the {subject} each morning."
        question = f"How does the inspection interval for the {subject} change in high humidity, and when can the normal interval resume?"
        key = [(a[0], 0), (b[0], 1), (b[1], 1)]
        context = [(a[1], 0), (summary, 2)]
        forbidden = [f"The {n}-day interval for the {subject} applies at all humidity levels."]
    third_kind = "OpenQuestion" if shape in {"open", "absent", "conflict"} else "Synthesis" if shape in {"multi-page", "correction"} else "Concept"
    titles = [f"{subject} operating record", f"{subject} review record", f"{subject} operating limits"]
    pages = [
        {"kind": "Source", "title": titles[0], "sentences": a + shared},
        {"kind": "Source" if number % 2 == 0 else "Entity", "title": titles[1], "sentences": b + shared},
        {"kind": third_kind, "title": titles[2], "sentences": [summary] + shared},
    ]
    retrieval_case = {"kind": "direct"}
    if dataset != "smoke-1" and number % 2 == 0:
        prefix = "CF" if dataset == "tuning-1" else "VH"
        code = f"{prefix}-{410 + number * 17}"
        terms = {"inspection interval": "time between checks", "spare seals": "reserve gaskets",
                 "supplier": "vendor", "purchase price": "acquisition cost",
                 "return-to-service check": "restart check", "transporting": "moving",
                 "transit clips": "shipping locks", "alignment check": "position test"}

        def coded(text):
            text = text.replace(subject, code)
            for original, replacement in terms.items():
                text = text.replace(original, replacement)
            return text

        for index in (0, 1):
            pages[index]["title"] = f"{code} {'service ledger' if index == 0 else 'review file'}"
            pages[index]["sentences"] = [coded(text) for text in (a if index == 0 else b)]
            pages[index]["sentences"].append(f"File this record under internal equipment code {code}.")
        pages[2]["sentences"].append(f"The public name {subject} maps to internal equipment code {code}.")
        key = [(coded(text) if index < 2 else text, index) for text, index in key]
        context = [(coded(text) if index < 2 else text, index) for text, index in context]
        retrieval_case = {"kind": "alias-link", "public_name": subject, "code": code}
    return pages, {"id": f"{dataset}-q{number + 1:03}", "shape": shape, "question": question,
                   "key": key, "context": context, "forbidden_claims": forbidden,
                   "retrieval_case": retrieval_case}


def distractor(spec, number):
    """Related work records with several different purposes, not empty count padding."""
    areas, objects = spec["areas"], spec["objects"]
    subject = f"{areas[number % len(areas)]} {objects[(number // len(areas)) % len(objects)]}"
    role = spec["roles"][number % 3]
    store = spec["stores"][number % 3]
    n = spec["base"] + number
    variants = [
        ("Source", "packing trial", [f"Packing trial {number + 1} used {n} paper pads around the {subject}.",
                                      "The pads stopped side movement but did not stop vertical movement.",
                                      "The trial team recommended a top brace before the next transport test."]),
        ("Entity", "storage bin", [f"Storage bin {number + 1} in the {store} holds adapters for the {subject}.",
                                   f"The {role} checks the bin label at the start of each month.",
                                   f"The bin has room for {n + 4} adapters; damaged adapters go in a separate red box."]),
        ("Concept", "cleaning rule", [f"Cleaning rule {number + 1} applies to the handles of the {subject}.",
                                       "Use a damp cloth, then dry the surface before storage.",
                                       "Do not apply this rule to lenses, wiring, bearings, or sealed housings."]),
        ("Synthesis", "training exercise", [f"Training exercise {number + 1} teaches safe handling of the {subject}.",
                                            f"The exercise takes {n + 2} minutes in the {store}.",
                                            "A trainee must identify the lifting points and show the stop signal before passing."]),
        ("OpenQuestion", "waste review", [f"Waste review {number + 1} has not selected a recycling route for worn pads from the {subject}.",
                                           "One route accepts clean paper only; another route has not confirmed collection dates.",
                                           f"The {role} must obtain written acceptance before any collection is booked."]),
        ("Source", "noise survey", [f"Noise survey {number + 1} placed the {subject} on a rubber mat in the {store}.",
                                     f"The test lasted {n + 3} minutes with the door closed.",
                                     "The survey measured room noise, not equipment wear; it does not change the service interval."]),
        ("Concept", "label scheme", [f"Label scheme {number + 1} uses a green triangle on the case of the {subject}.",
                                     "The triangle marks the approved carrying side, not inspection status.",
                                     "An unreadable triangle must be replaced before the case leaves storage."]),
        ("Entity", "practice kit", [f"Practice kit {number + 1} for the {subject} contains {n + 5} wooden spacers.",
                                     f"The kit stays in the {store} and the {role} signs it out.",
                                     "The wooden spacers are for training only and must not be installed on working equipment."]),
    ]
    kind, title, sentences = variants[number % len(variants)]
    subject_index = (number % len(areas)) * len(objects) + (number // len(areas)) % len(objects)
    # A second operational detail varies independently of the report purpose.
    observations = [
        f"Keep the {subject} clear of the marked aisle by at least {20 + number % 21} centimetres.",
        f"The handling team for the {subject} must include {2 + number % 3} trained operators.",
        f"Record the {subject} case temperature after {5 + number % 17} minutes indoors.",
        f"Use tray {1 + number % 11} for loose parts removed from the {subject}.",
        f"Keep the {subject} at least {30 + number % 19} centimetres from the drying rack.",
    ]
    sentences.append(observations[(number // len(variants)) % len(observations)])
    return {"kind": kind, "title": f"{subject} {title} {number + 1}", "sentences": sentences,
            "subject_index": subject_index}


def write_page(root, item):
    sets = ["status=stable"]
    if item["kind"] == "Source":
        sets += ["source_kind=report", "source_published='2041-12-01'",
                 f"resource=raw/{graph_ops.slugify(item['title'])}.md"]
    file = graph_ops.new(root, item["kind"], item["title"], item["sentences"][0], sets, ACTOR)
    path = "/" + file.relative_to(root / graph.DEFAULT_DIR).as_posix()
    graph_ops.body(root, path, f"# {item['title']}\n\n" + "\n\n".join(item["sentences"]), actor=ACTOR)
    return path


def build_dataset(destination, dataset):
    load_save_code()
    spec = SPECS[dataset]
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"{destination} is not empty; build into an empty folder")
    root = destination / "workspace"
    root.mkdir(parents=True, exist_ok=True)
    questions, all_paths = [], []
    # These are the library entrypoints used by knowledge_graph.py. Suppress only its
    # automatic full-graph regen while writing; validation and page writes still run.
    with (patch.object(graph, "datetime", FixedClock),
          patch.object(graph, "plugin_version", return_value=GRAPH_VERSION),
          patch.object(graph_ops, "regen", return_value=[])):
        graph_ops.init(root, actor=ACTOR)
        for number in range(spec["questions"]):
            pages, question = case_data(dataset, spec, number)
            paths = [write_page(root, item) for item in pages]
            if question["retrieval_case"]["kind"] == "alias-link":
                case = question["retrieval_case"]
                case.update(entry_node="knowledge:" + paths[2],
                            record_nodes=["knowledge:" + path for path in paths[:2]])
                equivalent = f"The public name {case['public_name']} maps to internal equipment code {case['code']}."
                question["equivalences"] = [equivalent]
                question["equivalence_evidence"] = [{"node": case["entry_node"], "quote": equivalent}]
            graph_ops.link(root, paths[2], "sources", paths[0], ACTOR)
            graph_ops.link(root, paths[2], "sources", paths[1], ACTOR)
            if pages[1]["kind"] != "Source":
                graph_ops.link(root, paths[1], "sources", paths[0], ACTOR)
            for group in ("key", "context"):
                question[group] = [dict(id=f"{group}-{i + 1}", **fact(text, paths[index]))
                                   for i, (text, index) in enumerate(question[group])]
            question["reference_answer"] = (" ".join(item["text"] for item in question["key"])
                                            + "\n\nContext:\n"
                                            + " ".join(item["text"] for item in question["context"]))
            questions.append(question)
            all_paths.extend(paths)
        for number in range(spec["pages"] - len(all_paths)):
            item = distractor(spec, number)
            path = write_page(root, item)
            subject_start = 3 * item["subject_index"]
            if item["kind"] != "Source":
                graph_ops.link(root, path, "sources", all_paths[subject_start], ACTOR)
            graph_ops.link(root, all_paths[subject_start + 2], "sources", path, ACTOR)
            all_paths.append(path)
        graph_regen.write(root)
    errors = [issue.text() for issue in graph_check.run(root) if issue.level == "ERROR"]
    require(not errors, "graph check errors: " + "; ".join(errors))
    payload = {"schema_version": 1, "dataset": dataset, "content_pages": spec["pages"],
               "provenance": {"synthetic": True, "organization": spec["organization"],
                              "generated_at": PINNED_DATE, "graph_version": GRAPH_VERSION,
                              "builder": "build_datasets.py",
                              "source": "Invented records; no real people, organizations, or source data."},
               "questions": questions}
    (destination / "questions.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_rendered_graph(root, expected_count):
    """Check this builder's rendered format, not arbitrary YAML, without extra packages.

    Builds also run the save code's full schema and regeneration checks. Here the
    emitted type, clock, source edges, and generated edge table can be read directly.
    """
    registry = json.loads((root / ".claude/knowledge.json").read_text("utf-8"))
    require(registry == {"graphs": {"knowledge": {"path": BUNDLE_DIR}}}, "unexpected graph registry")
    bundle = root / BUNDLE_DIR
    pages, types, edges = {}, Counter(), set()
    for kind, folder in TYPE_FOLDERS.items():
        for file in (bundle / folder).glob("*.md"):
            if file.name == "index.md":
                continue
            path = "/" + file.relative_to(bundle).as_posix()
            parts = file.read_text("utf-8").split("---\n", 2)
            require(len(parts) == 3 and not parts[0], f"unreadable page: {path}")
            front, body = parts[1:]
            require(re.search(rf"^type: {kind}$", front, re.MULTILINE), f"wrong page type: {path}")
            require(re.search(rf"^  at: ['\"]?{re.escape(PINNED_DATE)}['\"]?$", front, re.MULTILINE),
                    f"wrong generation date: {path}")
            pages[path] = body
            types[kind] += 1
            for target in re.findall(r"^  resource: (.+)$", front, re.MULTILINE):
                target = target.strip("'\"")
                edges.add((path, "sources", target))
    require(len(pages) == expected_count, f"wrong content page count: {len(pages)} != {expected_count}")
    require(set(types) == set(TYPE_FOLDERS), "missing graph page type")
    require(all(count >= 2 for count in types.values()), "graph page types are not balanced")
    for source, _, target in edges:
        require(target in pages, f"broken graph edge: {source} -> {target}")
    lines = (bundle / "links.tsv").read_text("utf-8").splitlines()
    require(lines and lines[0] == "source\trelation\ttarget", "wrong graph edge table header")
    table = [tuple(line.split("\t")) for line in lines[1:]]
    require(len(table) == len(set(table)) and set(table) == edges, "stale graph edge table")
    for path, body in pages.items():
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", body):
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target.split("#")[0]))
            require(resolved in pages, f"broken body edge: {path} -> {target}")
    return pages


def check_dataset(destination: Path, dataset: str) -> dict:
    """Return the checked questions payload; use no extra packages and write no files."""
    spec = SPECS[dataset]
    destination = Path(destination)
    root = destination / "workspace"
    payload = json.loads((destination / "questions.json").read_text("utf-8"))
    require(payload.get("schema_version") == 1 and payload.get("dataset") == dataset, "wrong dataset schema or name")
    require(payload.get("content_pages") == spec["pages"], "wrong declared content page count")
    provenance = payload.get("provenance", {})
    require(provenance.get("synthetic") is True and provenance.get("generated_at") == PINNED_DATE,
            "missing synthetic provenance or fixed generation date")
    pages = read_rendered_graph(root, spec["pages"])
    questions = payload.get("questions", [])
    require(len(questions) == spec["questions"], "wrong question count")
    shapes, ids, texts = Counter(), set(), set()
    for question in questions:
        for field in ("id", "shape", "question", "key", "context", "reference_answer", "forbidden_claims"):
            require(question.get(field), f"missing question field: {field}")
        qid, text = question["id"], question["question"]
        require(isinstance(qid, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", qid), "invalid question ID")
        require(isinstance(text, str) and text.strip(), "empty question text")
        require(qid not in ids and text.casefold() not in texts, "duplicate question ID or text")
        ids.add(qid)
        texts.add(text.casefold())
        require(question["shape"] in SHAPES, "unknown question shape")
        shapes[question["shape"]] += 1
        require("knowledge:/" not in text and not any(Path(path).stem in text for path in pages), "question reveals page ID")
        key_limit = 4 if question["shape"] == "multi-page" else 3
        for group, low, high in (("key", 2, key_limit), ("context", 2, 4)):
            facts = question[group]
            require(low <= len(facts) <= high, f"wrong {group} fact count: {qid}")
            fact_ids = set()
            for item in facts:
                require(item.get("id") and item["id"] not in fact_ids, "missing or duplicate fact ID")
                fact_ids.add(item["id"])
                require(isinstance(item.get("text"), str) and item["text"].strip(), "empty fact")
                require(isinstance(item.get("evidence"), list) and item["evidence"], "missing evidence")
                for evidence in item["evidence"]:
                    node, quote = evidence.get("node", ""), evidence.get("quote", "")
                    require(node.startswith("knowledge:/") and node[len("knowledge:"):] in pages, f"missing evidence node: {node}")
                    require(isinstance(quote, str) and quote.strip() and quote in pages[node[len("knowledge:"):]],
                            f"missing evidence quote: {qid}: {quote}")
        reference = question["reference_answer"]
        require(isinstance(reference, str) and "Context:" in reference, "reference answer has no context section")
        normalized_reference = " ".join(reference.split())
        require(all(" ".join(item["text"].split()) in normalized_reference
                    for item in question["key"] + question["context"]),
                "reference answer omits a key or context fact")
        retrieval = question.get("retrieval_case", {})
        require(retrieval.get("kind") in {"direct", "alias-link"}, "missing retrieval case")
        if retrieval["kind"] == "alias-link":
            name, code = retrieval.get("public_name", ""), retrieval.get("code", "")
            entry = retrieval.get("entry_node", "").removeprefix("knowledge:")
            records = [node.removeprefix("knowledge:") for node in retrieval.get("record_nodes", [])]
            require(name and code and entry in pages and len(records) == 2 and all(node in pages for node in records),
                    "invalid alias-link record mapping")
            require(code not in text and name in text, "alias-link question reveals its code or omits its public name")
            require(name in pages[entry] and code in pages[entry], "missing public-name to code mapping")
            equivalent = f"The public name {name} maps to internal equipment code {code}."
            require(question.get("equivalences") == [equivalent], "missing or incorrect grader equivalence")
            require(question.get("equivalence_evidence") == [{"node": "knowledge:" + entry, "quote": equivalent}]
                    and equivalent in pages[entry], "missing equivalence bridge evidence")
            entry_text = pages[entry].split("<!-- LINKS:START", 1)[0]
            hidden_fact = False
            for node in records:
                # Generated reverse links can name the public page; authored text must not.
                authored = (root / BUNDLE_DIR / node.lstrip("/")).read_text("utf-8").split("<!-- LINKS:START", 1)[0]
                require(name not in authored and code in authored, "coded record repeats its public equipment name")
                hidden_fact |= any(e["node"] == "knowledge:" + node and e["quote"] not in entry_text
                                   for item in question["key"] + question["context"] for e in item["evidence"])
            require(hidden_fact, "alias-link facts are repeated in the public entry page")
        require(isinstance(question["forbidden_claims"], list) and all(isinstance(s, str) and s.strip() for s in question["forbidden_claims"]),
                "empty forbidden claim")
    require(set(shapes) == set(SHAPES) and max(shapes.values()) - min(shapes.values()) <= 1,
            "missing or unbalanced question shapes")
    for file in root.rglob("*"):
        if not file.is_file():
            continue
        relative = file.relative_to(root).as_posix()
        require(relative == ".claude/knowledge.json" or relative.startswith(BUNDLE_DIR + "/"),
                f"unexpected workspace file: {relative}")
        content = file.read_text("utf-8")
        require(not any(q["question"] in content or q["id"] in content for q in questions), "questions leaked into workspace")
        require('"reference_answer"' not in content and '"forbidden_claims"' not in content, "gold leaked into workspace")
    return payload


def check_all(directory: Path = DATASETS) -> list[str]:
    ids, questions, facts = set(), set(), set()
    summaries = []
    for dataset in SPECS:
        payload = check_dataset(Path(directory) / dataset, dataset)
        for question in payload["questions"]:
            require(question["id"] not in ids and question["question"].casefold() not in questions,
                    "duplicate question across datasets")
            ids.add(question["id"])
            questions.add(question["question"].casefold())
            for item in question["key"] + question["context"]:
                # Context can repeat within a dataset, but not across independent datasets.
                require(item["text"] not in facts, "shared fact across datasets")
        facts.update(item["text"] for q in payload["questions"] for item in q["key"] + q["context"])
        summaries.append(f"{dataset}: {payload['content_pages']} content pages, {len(payload['questions'])} questions")
    return summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build", action="store_true", help="build all datasets into an empty output folder")
    action.add_argument("--check", action="store_true", help="check datasets without writing files")
    parser.add_argument("--output", type=Path, default=DATASETS)
    args = parser.parse_args(argv)
    try:
        if args.build:
            for dataset in SPECS:
                build_dataset(args.output / dataset, dataset)
        for line in check_all(args.output):
            print(line)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
