"""view: put an output file of a run together again from the pages (STORY-257, rows 7 and 8).

`Run.file_meta[file]` is the file with each document replaced by `@@<page ID>`. A page holds its document as
`record["<RUN ID>/<file>"]`, and a document can hold markers of child pages. A `.mmd` file is the body of its
`Diagram` page. `--out` writes the text under `<output folder of the run>/inputs/`, and nowhere else.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from uxlib import DataError, UsageError, regen
from uxlib import read as reading
from uxlib.bundle import read
from uxlib.ingest import DIAGRAMS, MARK, OUTPUT_FILES


def resolve(value, name, pages, run_stem):
    if isinstance(value, str) and value.startswith(MARK):
        page = pages.get(value[len(MARK):])
        if page is None:
            raise DataError(f"{name}: the marker {value} names a page that is not in the bundle")
        record = page.frontmatter.get("record") or {}
        key = f"{run_stem}/{name}"
        if key not in record:
            raise DataError(f"{name}: {page.id} holds no record of this file for {run_stem}")
        return resolve(record[key], name, pages, run_stem)
    if isinstance(value, dict):
        return {key: resolve(item, name, pages, run_stem) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, name, pages, run_stem) for item in value]
    return value


def diagram_text(page, name, run_stem) -> str:
    record = (page.frontmatter.get("record") or {}).get(f"{run_stem}/{name}")
    if not isinstance(record, dict):
        raise DataError(f"{name}: {page.id} holds no record of this file for {run_stem}")
    body = regen.strip_generated(page.body)
    match = re.search(r"^(`{3,})mermaid\n(.*?)\n\1$", body, re.DOTALL | re.MULTILINE)
    if not match:
        raise DataError(f"{name}: {page.id} has no mermaid block in its text")
    return match.group(2) + "\n" * int(record.get("trailing_newlines") or 0)


def build(bundle, run_page, name):
    meta = run_page.frontmatter.get("file_meta") or {}
    if name not in meta:
        raise DataError(f"{run_page.id} has no file {name}. Files: {', '.join(sorted(meta)) or 'none'}")
    pages = {path.stem: page for path, page in bundle.pages.items() if page.frontmatter}
    run_stem = run_page.path.stem
    if name in DIAGRAMS:
        page = pages.get(str(meta[name])[len(MARK):])
        if page is None:
            raise DataError(f"{name}: the marker {meta[name]} names a page that is not in the bundle")
        return diagram_text(page, name, run_stem)
    return resolve(meta[name], name, pages, run_stem)


def text_of(data) -> str:
    return data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def find(bundle, run_key, name):
    """The Run page: an ID, an alias, or latest (the latest run that holds the file)."""
    if run_key != "latest":
        return reading.find_run(bundle, run_key)
    holding = [item for item in reading.runs(bundle) if name in (item[1].frontmatter.get("file_meta") or {})]
    if not holding:
        raise DataError(f"no run holds the file {name}")
    return reading.latest(holding)


def inputs_path(root, run_page, out) -> Path:
    base = (Path(root).resolve() / str(run_page.frontmatter.get("output_dir") or "") / "inputs").resolve()
    target = Path(out)
    target = (target if target.is_absolute() else Path(root) / target).resolve()
    if base not in target.parents:
        raise UsageError(f"--out must name a file under {base.relative_to(Path(root).resolve()).as_posix()}/ "
                         f"(the folder of the run for the inputs of the agents): {out!r}")
    return target


def show(root, run_key, name, out=None) -> str:
    if name not in OUTPUT_FILES:
        raise UsageError(f"{name} is not an output file of ux-hci-design. Files: {', '.join(OUTPUT_FILES)}")
    bundle = read(root)
    run_page = find(bundle, run_key, name)
    text = text_of(build(bundle, run_page, name))
    if out is None:
        return text
    target = inputs_path(root, run_page, out)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return f"wrote {target.relative_to(Path(root).resolve()).as_posix()}\n"
