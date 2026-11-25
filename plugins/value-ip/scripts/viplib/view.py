"""view: read the pages of one run, and a person's confirmation of a run."""
from __future__ import annotations

from pathlib import Path

from viplib import DataError, UsageError, schema, writer
from viplib.bundle import read, ref
from viplib.ids import resolve
from viplib.regen import strip_generated

KINDS = {"Differentiator": "differentiators", "Verdict": "verdicts", "Gap": "gaps"}


def _entry(root, path, page):
    return {"path": Path(path).relative_to(root).as_posix(), "id": page.id, "status": page.frontmatter.get("status"),
            "verified": page.frontmatter.get("verified") or [], "frontmatter": page.frontmatter,
            "body": strip_generated(page.body).strip("\n")}


def latest_run(bundle):
    """The Run page with the latest `started_at`; a run without one sorts first. Ties go to the higher ID."""
    runs = [(path, page) for path, page in bundle.pages.items() if page.type == "Run" and not page.error]
    if not runs:
        raise DataError("the graph holds no Run page. Run /value-ip:learn on a result file first.")
    return max(runs, key=lambda item: (str(item[1].frontmatter.get("started_at") or ""), item[0].stem))


def results(root, key=None) -> dict:
    """The pages of one run as plain data: the run, its differentiators, its verdicts and its gaps."""
    bundle = read(root)
    if key:
        path = resolve(bundle, key)
        page = bundle.pages.get(path)
        if page is None or page.type != "Run":
            raise UsageError(f"{key} is not a Run page")
    else:
        path, page = latest_run(bundle)
    run_ref = ref(bundle.dir, path)
    out = {"run": _entry(root, path, page), "differentiators": [], "verdicts": [], "gaps": []}
    for other, item in sorted(bundle.pages.items()):
        if item.error or item.type not in KINDS:
            continue
        if run_ref in schema.edge_values(item.frontmatter, "run"):
            out[KINDS[item.type]].append(_entry(root, other, item))
    return out


def verify_run(root, key, by) -> list[Path]:
    """A person confirms a run: the Run page and each page of the run get `status: stable` and a `verified` entry."""
    writer._need_person(by)
    bundle = read(root)
    path = resolve(bundle, key)
    page = bundle.pages.get(path)
    if page is None or page.type != "Run":
        raise UsageError(f"verify-run takes a Run page, and {key} is not one")
    run_ref = ref(bundle.dir, path)
    pages = [(path, page)] + [(other, item) for other, item in sorted(bundle.pages.items())
                              if not item.error and run_ref in schema.edge_values(item.frontmatter, "run")]
    return writer._confirm(root, bundle, pages, by, f"{run_ref} and the {len(pages) - 1} pages of that run")


RESULTS_DIR = ".value-ip/results"


def pending(root) -> list:
    """Each result file of `.value-ip/results/`, oldest first, and the Run page that holds it (null when none)."""
    bundle = read(root)
    held = {page.frontmatter.get("result_file"): ref(bundle.dir, path)
            for path, page in bundle.pages.items() if page.type == "Run" and not page.error}
    folder = Path(root) / RESULTS_DIR
    files = sorted(p for p in folder.glob("*.json") if p.is_file() and not p.is_symlink()) if folder.is_dir() else []
    return [{"file": f"{RESULTS_DIR}/{p.name}", "run": held.get(f"{RESULTS_DIR}/{p.name}")} for p in files]
