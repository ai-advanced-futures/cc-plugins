"""view: put a JSON file of a run together again from the pages (spec row 6).

`Run.file_meta[file]` is the file with each item replaced by `@@<page ID>`. The item
is `record[file]` of that page. The counts that the source stored are computed.
"""
from __future__ import annotations

import json

from cilib import DataError
from cilib.bundle import read
from cilib import read as reading

MARK, COMPUTED = "@@", "@@computed"
THREAT_LEVELS = ("high", "medium", "low")
COMPETITOR_TYPES = ("direct", "indirect", "substitute", "potential")
CONFIDENCES = ("high", "medium", "low", "speculative")


def offer_view(fm) -> dict:
    return {key: fm[key] for key in ("name", "key_features", "business_model") if key in fm}


def ecosystem_summary(competitors) -> dict:
    items = [c for c in competitors if isinstance(c, dict)]
    out = {"total_competitors": len(items)}
    out.update({f"{kind}_count": sum(1 for c in items if c.get("type") == kind) for kind in COMPETITOR_TYPES})
    out.update({f"{level}_threat_count": sum(1 for c in items if c.get("threat_level") == level) for level in THREAT_LEVELS})
    return out


def intelligence_summary(data) -> dict:
    blocks = [b for b in (data.get("competitors") or {}).values() if isinstance(b, dict)] \
        if isinstance(data.get("competitors"), dict) else []
    findings = [f for b in blocks for f in b.get("findings") or [] if isinstance(f, dict)]
    gaps = [g for b in blocks for g in b.get("gaps") or [] if isinstance(g, dict)]
    return {"total_findings": len(findings),
            "by_confidence": {level: sum(1 for f in findings if f.get("confidence") == level) for level in CONFIDENCES},
            "critical_gaps": sum(1 for g in gaps if g.get("type") == "critical")}


def resolve(value, name, pages, run_id=None):
    if isinstance(value, str) and value.startswith(MARK) and value != COMPUTED:
        page = pages.get(value[len(MARK):])
        if page is None:
            raise DataError(f"{name}: the marker {value} names a page that is not in the bundle")
        if page.type == "Offer":
            return offer_view(page.frontmatter)
        record = page.frontmatter.get("record") or {}
        key = f"{run_id}/{name}" if f"{run_id}/{name}" in record else name  # a shared page keys its records by run
        if key not in record:
            raise DataError(f"{name}: {page.id} holds no record of this file")
        return resolve(record[key], name, pages, run_id)
    if isinstance(value, dict):
        return {key: resolve(item, name, pages, run_id) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, name, pages, run_id) for item in value]
    return value


def build(bundle, run_page, filename):
    meta = run_page.frontmatter.get("file_meta") or {}
    if filename not in meta:
        raise DataError(f"{run_page.id} has no file {filename}. Files: {', '.join(sorted(meta)) or 'none'}")
    pages = {path.stem: page for path, page in bundle.pages.items() if page.frontmatter}
    skeleton = meta[filename]
    if isinstance(skeleton, str) and skeleton.startswith("json:"):
        skeleton = json.loads(skeleton[len("json:"):])
    elif isinstance(skeleton, str) and skeleton.startswith(MARK) and skeleton.endswith("#"):
        anchor = pages.get(skeleton[len(MARK):-1])
        if anchor is None or filename + "#" not in (anchor.frontmatter.get("record") or {}):
            raise DataError(f"{filename}: the page {skeleton[len(MARK):-1]} holds no skeleton of the file")
        skeleton = anchor.frontmatter["record"][filename + "#"]
    data = resolve(skeleton, filename, pages, run_page.frontmatter.get("run_id"))
    if isinstance(data, dict):
        if data.get("ecosystem_summary") == COMPUTED:
            data["ecosystem_summary"] = ecosystem_summary(data.get("competitors") or [])
        if data.get("summary") == COMPUTED:
            data["summary"] = intelligence_summary(data)
    return data


def show(root, run_key, filename) -> str:
    bundle = read(root)
    run_page = reading.find_run(bundle, run_key)
    return json.dumps(build(bundle, run_page, filename), indent=2, ensure_ascii=False) + "\n"
