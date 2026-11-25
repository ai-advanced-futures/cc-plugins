"""ingest: one result file of value-ip:analyze becomes the pages of one run.

The result file is the record of a run. It stays as it is. `ingest` reads it, makes one Run page, one
Differentiator page for each `differentiator` result, one Verdict page for each `right_to_win` result and one
Gap page for each gap, and links each page to the Run page. Each page is a `draft`: only `verify` makes a
page `stable`, and only a person runs `verify`. `ingest` writes nothing when one page is not valid, and
never reads a file outside the project root.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from viplib import DataError, UsageError, logbook, regen, schema
from viplib.bundle import bundle_dir, read, ref
from viplib.writer import create

RESULT_SCHEMA = "plugin-result/1"
PLUGIN = "value-ip"
RECOMMENDATIONS = ("PASS", "CONDITIONAL", "FAIL")
MEAN = re.compile(r"\bmean (\d+(?:\.\d+)?) of 5\b")
RUN_KEYS = ("subject", "run_id", "mode", "case", "started_at", "finished_at")
PLACEHOLDER_RUN = "/runs/RUN-00.md"


def _line(value, limit=240) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _load(root, file) -> tuple[dict, str]:
    root = Path(root).resolve()
    path = Path(file)
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to(root):
        raise UsageError(f"{file} is outside the project root, so ingest does not read it")
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read the result file {file}: {error}") from error
    if not isinstance(data, dict):
        raise DataError(f"{file} is not a result file: its top level is not an object")
    if data.get("schema") != RESULT_SCHEMA or data.get("plugin") != PLUGIN:
        raise DataError(f"{file} is not a {PLUGIN} result file: schema {data.get('schema')!r}, plugin {data.get('plugin')!r}")
    return data, path.relative_to(root).as_posix()


def _verdict_fields(item) -> dict:
    value = str(item.get("value") or "")
    head, _sep, powers = value.partition(" — ")
    fields = {}
    if head.strip() in RECOMMENDATIONS:  # a value that does not start with a recommendation gets none: no guess
        fields["recommendation"] = head.strip()
    if powers.strip():
        fields["powers"] = powers.strip()
    mean = MEAN.search(str(item.get("method") or ""))
    if mean:
        fields["mean_score"] = float(mean.group(1))
    return fields


def _result_fields(item, where) -> dict:
    sources = item.get("sources") or []
    if not any(isinstance(s, dict) and s.get("type") == "model" for s in sources):
        raise DataError(f"{where} has no model source: a value-ip result is a judgement of the model")
    fields = {"label": item.get("label"), "claim": item.get("value"), "result_id": item.get("id"),
              "method": item.get("method"), "grade": "model", "sources": sources,
              "rests_on_default": bool(item.get("rests_on_default")), "detail": item.get("detail")}
    if item.get("defaults"):
        fields["defaults"] = [str(d) for d in item["defaults"]]
    return {k: v for k, v in fields.items() if v not in (None, "")}


def plan(data, rel) -> list[tuple[str, str, str, dict]]:
    """The pages of one result file: (type, title, description, fields). The Run page is first."""
    run = data.get("run") or {}
    run_fields = {"command": data.get("command") or "value-ip:analyze", "result_file": rel,
                  **{k: run[k] for k in RUN_KEYS if run.get(k) not in (None, "")}}
    if data.get("plugin_version"):
        run_fields["plugin_version"] = str(data["plugin_version"])
    subject = _line(run_fields.get("subject") or "unnamed run", 120)
    run_fields.setdefault("subject", subject)
    pages = [("Run", f"value-ip run: {subject}", f"The run of {run_fields['command']} on {subject}, from {rel}.", run_fields)]
    for index, item in enumerate(data.get("results") or [], 1):
        where = f"results[{index}]"
        if not isinstance(item, dict):
            raise DataError(f"{where} is not an object")
        kind = item.get("kind")
        if kind == "differentiator":
            kind_type = "Differentiator"
            extra = {}
        elif kind == "right_to_win":
            kind_type = "Verdict"
            extra = _verdict_fields(item)
        else:
            raise DataError(f"{where} has the kind {kind!r}: use differentiator or right_to_win")
        fields = {**_result_fields(item, where), **extra, "run": PLACEHOLDER_RUN}
        pages.append((kind_type, str(item.get("label") or kind), _line(item.get("value") or item.get("label")), fields))
    for index, gap in enumerate(data.get("gaps") or [], 1):
        if not isinstance(gap, dict) or not gap.get("why"):
            raise DataError(f"gaps[{index}] has no why")
        fields = {"gap_kind": gap.get("kind"), "label": gap.get("label"), "why": gap.get("why"), "run": PLACEHOLDER_RUN}
        pages.append(("Gap", str(gap.get("label") or gap.get("kind") or "gap"), _line(gap["why"]),
                      {k: v for k, v in fields.items() if v not in (None, "")}))
    return pages


def run(root, file, actor=None) -> list[Path]:
    """Write the pages of one result file. Return the paths, the Run page first."""
    data, rel = _load(root, file)
    bundle = read(root)
    for path, page in bundle.pages.items():
        if (page.frontmatter or {}).get("type") == "Run" and page.frontmatter.get("result_file") == rel:
            raise DataError(f"{rel} is already in the graph: {ref(bundle.dir, path)}")
    pages = plan(data, rel)
    for type_name, title, description, fields in pages:  # check every page first, so a bad one leaves nothing behind
        probe = {"type": type_name, "title": title, "description": description, "status": "draft", **fields,
                 "generated": {"by": actor or schema.plugin_actor(), "at": logbook.stamp()}}
        problems = schema.validate(type_name, probe)
        if problems:
            raise DataError(f"{rel}: the {type_name} page for {title!r} is not valid, so nothing is written: " + "; ".join(problems))
    written = []
    run_ref = None
    for type_name, title, description, fields in pages:
        if "run" in fields:
            fields = {**fields, "run": run_ref}
        written.append(create(root, type_name, title, description, fields, None, actor, regenerate=False))
        if run_ref is None:
            run_ref = ref(bundle_dir(root), written[0])
    counts = {name: sum(1 for p in pages if p[0] == name) for name in ("Differentiator", "Verdict", "Gap")}
    logbook.append(bundle_dir(root) / "log.md", "Learn",
                   f"ingested {rel}: {counts['Differentiator']} differentiators, {counts['Verdict']} verdicts, {counts['Gap']} gaps",
                   actor or schema.plugin_actor())
    regen.write(root)
    return written
