#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Read the jtbd graph and the competitive-intelligence graph for pricing.

usage: uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" <operation> --root <git root> [options]

Operations:
  wtp       the willingness-to-pay results of the newest jtbd run that holds any.
            --run-id R --case C   read the one jtbd run with that run_id and case, as it is
            --out DIR             write the printed document as a result file under DIR
                                  (DIR must be inside <root>/.pricing/)
  outcomes  the outcomes of the newest jtbd run that has outcome pages, best score first
  moats     the moats of the newest competitive-intelligence run that has moat pages
  status    0, 1 or 2 plain lines for the session-start hook

Each operation prints 1 JSON object (status prints lines). The object has `graph` and `found`.
When `found` is false it has `cause` and `why`: the `why` is plain text for the person.
Exit 0 when the script printed its object. Exit 1 when `--out` was given and a snapshot could
not be written. Exit 2 for wrong arguments.

The script reads a graph only through the save script of its writer plugin (`jtbd_graph.py`,
`ci_graph.py`), which it finds with `probe-plugin.sh`. It reads no page file. It writes only
under <root>/.pricing/. Standard library only; Python 3.9 syntax, because the hook runs it with
the python3 of the system.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
# `python3 -I` does not put the folder of this script on sys.path. Add this folder only,
# never the current folder: the project can hold a planted module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from result_name import result_name  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PYTHON_VAR = "PRICING_GRAPH_PYTHON"
CALL_TIMEOUT = 60  # seconds for one call of a save script
PROBE_TIMEOUT = 30  # seconds for the search of a writer plugin
STATUS_TIMEOUT = 7  # seconds for all calls of `status` (the hook has timeout 10)

GRAPHS = {
    "jtbd": {"plugin": "jtbd-market-discovery", "script": "scripts/jtbd_graph.py",
             "command": "/jtbd-market-discovery:discover"},
    "competitive-intelligence": {"plugin": "competitive-intelligence", "script": "scripts/ci_graph.py",
                                 "command": "/competitive-intelligence:analyze"},
}
WTP = "willingness_to_pay"
OPPORTUNITY = "opportunity_score"
_PAGE = re.compile(r"(/[^/]+/[^/]+\.md)\Z")


class Failure(Exception):
    """A read that cannot give data. `cause` is a word, `why` is the text for the person."""

    def __init__(self, cause, why):
        Exception.__init__(self, why)
        self.cause = cause
        self.why = why


class Reader:
    """Calls the save script of one graph. `deadline` (seconds from the epoch) is optional."""

    def __init__(self, graph, root, offline=False, deadline=None):
        self.graph = graph
        self.root = root
        self.offline = offline
        self.deadline = deadline
        self.info = GRAPHS[graph]
        self.plugin_root = None

    def find(self):
        if self.plugin_root is not None:
            return self.plugin_root
        probe = PLUGIN_ROOT / "scripts" / "probe-plugin.sh"
        # cwd is the pricing plugin: the probe runs python3 -c, which imports from the current
        # folder, and the project folder can hold a planted json.py.
        # CLAUDE_PROJECT_DIR is the plugin folder, not the project: the probe tries
        # <project>/.claude/plugins/<name> as a candidate, and the save script of a project that was
        # just opened must not run with no prompt.
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(PLUGIN_ROOT))
        timeout = PROBE_TIMEOUT if self.deadline is None else max(1, min(PROBE_TIMEOUT, self.deadline - time.time()))
        try:
            done = subprocess.run(["bash", str(probe), self.info["plugin"], self.info["script"]],
                                  cwd=str(PLUGIN_ROOT), env=env, capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            done = None
        found = done.stdout.strip() if done is not None and done.returncode == 0 else ""
        if not found:
            raise Failure("no-plugin", "The %s plugin is not installed, so pricing has no %s data. "
                          "To install it, run: claude plugin install %s@cc-plugins"
                          % (self.info["plugin"], self.graph, self.info["plugin"]))
        self.plugin_root = Path(found)
        return self.plugin_root

    def interpreter(self):
        python = os.environ.get(PYTHON_VAR)
        if python:
            return [python]
        if shutil.which("uv"):
            return ["uv", "run", "--quiet"] + (["--offline"] if self.offline else [])
        if shutil.which("python3"):
            return ["python3"]
        raise Failure("no-python", "Pricing cannot run the %s save script: uv and python3 are not on PATH."
                      % self.graph)

    def call(self, *args, skip_exit_1=False):
        """Run the save script with --root and `args`. Return the parsed JSON. With
        skip_exit_1, return None when the script exits 1 (a run with no result pages)."""
        plugin_root = self.find()
        command = self.interpreter() + [str(plugin_root / self.info["script"]), "--root", str(self.root)] + list(args)
        timeout = CALL_TIMEOUT
        if self.deadline is not None:
            timeout = min(timeout, self.deadline - time.time())
            if timeout <= 0:
                raise Failure("failed", "Pricing cannot read the %s graph: the time limit passed." % self.graph)
        try:
            done = subprocess.run(command, cwd=str(plugin_root), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise Failure("failed", "Pricing cannot read the %s graph: the time limit passed." % self.graph)
        except OSError as error:
            raise Failure("failed", "Pricing cannot read the %s graph: %s." % (self.graph, error))
        if done.returncode == 2:
            raise Failure("no-graph", "The project has no %s graph. Run %s first."
                          % (self.graph, self.info["command"]))
        if done.returncode == 1 and skip_exit_1:
            return None
        if done.returncode != 0:
            raise Failure("failed", "Pricing cannot read the %s graph: %s."
                          % (self.graph, first_line(done.stderr or done.stdout)))
        try:
            return json.loads(done.stdout)
        except ValueError:
            raise Failure("failed", "Pricing cannot read the %s graph: the save script printed no JSON." % self.graph)

    # ------------------------------------------------------------------ runs

    def runs(self):
        """The Run pages, newest finished_at first. A page with no finished_at is left out."""
        found = []
        for page in self.call("pages", "Run"):
            fm = page.get("frontmatter") or {}
            if fm.get("finished_at"):
                found.append((str(fm["finished_at"]), Path(page["path"]).stem, fm))
        found.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return found

    def all_runs(self):
        return [(Path(page["path"]).stem, page.get("frontmatter") or {}) for page in self.call("pages", "Run")]

    def results(self, run_key):
        return self.call("results", "--run", run_key, skip_exit_1=True)


def first_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip().rstrip(".")[:200]
    return "the save script gave no message"


def bundle_path(path):
    """`docs/jtbd/runs/RUN-01.md` -> `/runs/RUN-01.md`."""
    match = _PAGE.search("/" + path.replace("\\", "/").lstrip("/"))
    return match.group(1) if match else path


def run_page(graph, key):
    return "%s:/runs/%s.md" % (graph, key)


def missing(graph, what):
    label = GRAPHS[graph]["plugin"] if graph == "competitive-intelligence" else graph
    return Failure("no-data", "The %s graph holds no run with %s." % (label, what))


# ---------------------------------------------------------------------- wtp


def has_wtp(document):
    return any(isinstance(item, dict) and item.get("kind") == WTP for item in (document or {}).get("results") or [])


def wtp_run(reader, run_id, case):
    matches = [(key, fm) for key, fm in reader.all_runs() if fm.get("run_id") == run_id and fm.get("case") == case]
    if not matches:
        raise Failure("no-run", "The jtbd graph has no run %s in case %s." % (run_id, case))
    if len(matches) > 1:
        raise Failure("many-runs", "The jtbd graph has %d runs %s in case %s: %s."
                      % (len(matches), run_id, case, ", ".join(run_page("jtbd", key) for key, _ in matches)))
    key = matches[0][0]
    document = reader.results(key)
    if document is None:
        raise Failure("failed", "Pricing cannot read the jtbd graph: the run %s has no result pages." % key)
    return key, document


def wtp_newest(reader):
    for _stamp, key, _fm in reader.runs():
        document = reader.results(key)
        if has_wtp(document):
            return key, document
    raise missing("jtbd", "a willingness-to-pay result")


def op_wtp(root, args):
    reader = Reader("jtbd", root)
    try:
        if args.run_id:
            key, document = wtp_run(reader, args.run_id, args.case)
        else:
            key, document = wtp_newest(reader)
        out = {"graph": "jtbd", "found": True, "run_page": run_page("jtbd", key), "run": document.get("run") or {},
               "result": document, "snapshot": None}
        if args.out:
            out["snapshot"], out["unresolved_cites"] = write_snapshots(reader, root, Path(args.out), key, document)
            if not out["unresolved_cites"]:
                del out["unresolved_cites"]
        return out, 0
    except Failure as failure:
        return not_found("jtbd", failure), 0
    except SnapshotError as error:
        return {"graph": "jtbd", "found": True, "error": str(error), "snapshot": None}, 1


class SnapshotError(Exception):
    pass


def snapshot_name(document):
    run = document.get("run") or {}
    try:
        return result_name(str(run.get("finished_at") or ""), str(document.get("command") or ""),
                           str(run.get("subject") or ""), run.get("run_id"))
    except ValueError as error:
        raise SnapshotError("the result file has no valid name: %s" % error)


def write_text(path, document):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as error:
        raise SnapshotError("cannot write %s: %s" % (path, error))


def write_snapshots(reader, root, folder, key, document):
    """Write the document of run `key`, and the document of each run that it cites, under `folder`.
    Each cites.file in a written document becomes the snapshot path of the cited run. Return the
    snapshot path (relative to the root) and the list of cites that did not resolve."""
    folder = root / folder  # a join keeps an absolute `folder` as it is
    written = {}  # run key -> snapshot path relative to root
    unresolved = []
    cited_pages = None

    def snapshot_of(run_key, doc):
        nonlocal cited_pages
        if run_key in written:
            return written[run_key]
        path = folder / snapshot_name(doc)
        written[run_key] = path.relative_to(root).as_posix()
        for item in doc.get("results") or []:
            for cite in item.get("cites") or []:
                if cited_pages is None:
                    cited_pages = {page["path"]: page for page in reader.call("pages", "Result")}
                target = resolve_cite(cite.get("file"), cited_pages)
                if target is None:
                    unresolved.append(cite.get("file"))
                    continue
                if target == run_key:
                    cite["file"] = written[run_key]
                    continue
                other = reader.results(target)
                if other is None:
                    unresolved.append(cite.get("file"))
                    continue
                cite["file"] = snapshot_of(target, other)
        write_text(path, doc)
        return written[run_key]

    return snapshot_of(key, document), unresolved


def resolve_cite(file, pages):
    """The key of the run that holds the cited Result page, or None."""
    page = pages.get(file)
    if page is None:
        return None
    links = (page.get("frontmatter") or {}).get("run")
    links = [links] if isinstance(links, str) else list(links or [])
    match = re.search(r"/runs/([^/]+)\.md\Z", links[0]) if links else None
    return match.group(1) if match else None


# ----------------------------------------------------------------- outcomes


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def op_outcomes(root, _args):
    reader = Reader("jtbd", root)
    try:
        for _stamp, key, _fm in reader.runs():
            pages = reader.call("pages", "Outcome", "--run", key)
            if pages:
                break
        else:
            raise missing("jtbd", "outcome scores")
        document = reader.results(key) or {}
        scored = {}
        for item in document.get("results") or []:
            if item.get("kind") == OPPORTUNITY and isinstance(item.get("value"), dict):
                scored[str(item["value"].get("need"))] = item["value"]
        outcomes = []
        for page in pages:
            fm = page.get("frontmatter") or {}
            title = fm.get("title")
            value = scored.get(str(title), {})
            outcomes.append({
                "need": title, "rank": fm.get("rank"),
                "importance": number(value.get("importance", fm.get("importance"))),
                "satisfaction": number(value.get("satisfaction", fm.get("satisfaction"))),
                "opportunity_score": number(value.get("score", fm.get("opportunity_score"))),
                "opportunity_category": fm.get("opportunity_category"),
                "page": bundle_path(page["path"]),
            })
        outcomes.sort(key=lambda o: (o["opportunity_score"] is None, -(o["opportunity_score"] or 0),
                                     o["rank"] if isinstance(o["rank"], int) else 10 ** 6))
        return {"graph": "jtbd", "found": True, "run_page": run_page("jtbd", key), "outcomes": outcomes}, 0
    except Failure as failure:
        return not_found("jtbd", failure), 0


# -------------------------------------------------------------------- moats


def moat_fields(fm):
    record = fm.get("record")
    entry = next((v for v in record.values() if isinstance(v, dict)), {}) if isinstance(record, dict) else {}
    return {"kind": entry.get("type") or fm.get("title"), "strength": entry.get("strength"),
            "description": entry.get("description") or fm.get("description")}


def op_moats(root, _args):
    reader = Reader("competitive-intelligence", root)
    try:
        for _stamp, key, _fm in reader.runs():
            moats = reader.call("pages", "Moat", "--run", key)
            if moats:
                break
        else:
            raise missing("competitive-intelligence", "competitor moats")
        competitors = []
        by_page = {}
        for page in reader.call("pages", "Competitor", "--run", key):
            fm = page.get("frontmatter") or {}
            entry = {"name": fm.get("name") or fm.get("title"), "page": bundle_path(page["path"]), "moats": []}
            competitors.append(entry)
            by_page[entry["page"]] = entry
        for page in moats:
            fm = page.get("frontmatter") or {}
            moat = dict(moat_fields(fm), page=bundle_path(page["path"]))
            owner = by_page.get(str(fm.get("competitor")))
            if owner is not None:
                owner["moats"].append(moat)
        return {"graph": "competitive-intelligence", "found": True,
                "run_page": run_page("competitive-intelligence", key), "competitors": competitors}, 0
    except Failure as failure:
        return not_found("competitive-intelligence", failure), 0


# ------------------------------------------------------------------- status


def registered(root):
    """The graph names in <root>/.claude/knowledge.json. Nothing on any error."""
    try:
        data = json.loads((root / ".claude" / "knowledge.json").read_text(encoding="utf-8"))
        graphs = data.get("graphs")
        return set(graphs) if isinstance(graphs, dict) else set()
    except (OSError, ValueError):
        return set()


def op_status(root, _args):
    names = registered(root)
    deadline = time.time() + STATUS_TIMEOUT
    lines = []
    try:
        if "jtbd" in names:
            wtp_newest(Reader("jtbd", root, offline=True, deadline=deadline))
            lines.append("PRICING: the jtbd graph holds a willingness-to-pay result.")
    except Failure:
        pass
    try:
        if "competitive-intelligence" in names:
            reader = Reader("competitive-intelligence", root, offline=True, deadline=deadline)
            for _stamp, key, _fm in reader.runs():
                if reader.call("pages", "Moat", "--run", key):
                    lines.append("PRICING: the competitive-intelligence graph holds competitor moats. "
                                 "Use them for the MOAT_MULTIPLIER questions.")
                    break
    except Failure:
        pass
    return lines, 0


def not_found(graph, failure):
    return {"graph": graph, "found": False, "cause": failure.cause, "why": failure.why}


# --------------------------------------------------------------------- main


def build_parser():
    parser = argparse.ArgumentParser(prog="brain_read.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("operation", choices=["wtp", "outcomes", "moats", "status"])
    parser.add_argument("--root", required=True, help="the git root of the project")
    parser.add_argument("--run-id", help="wtp: the run_id of the jtbd run")
    parser.add_argument("--case", help="wtp: the case of the jtbd run")
    parser.add_argument("--out", help="wtp: the folder for the result file; it must be inside <root>/.pricing/")
    return parser


def usage_error(parser, message):
    parser.error(message)  # prints to stderr and exits 2


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        usage_error(parser, "--root is not a folder: %s" % args.root)
    root = root.resolve()
    if args.operation != "wtp" and (args.run_id or args.case or args.out):
        usage_error(parser, "--run-id, --case and --out are for wtp only")
    if bool(args.run_id) != bool(args.case):
        usage_error(parser, "--run-id and --case go together")
    if args.run_id and args.out:
        usage_error(parser, "--out is not allowed with --run-id")
    if args.out:
        out = Path(args.out)
        resolved = Path(os.path.realpath(str(out if out.is_absolute() else root / out)))
        base = Path(os.path.realpath(str(root / ".pricing")))
        if base != root / ".pricing" or resolved == base or base not in resolved.parents:
            usage_error(parser, "--out must be a folder inside %s" % (root / ".pricing"))
        args.out = str(resolved)
    operations = {"wtp": op_wtp, "outcomes": op_outcomes, "moats": op_moats, "status": op_status}
    result, code = operations[args.operation](root, args)
    if args.operation == "status":
        for line in result:
            print(line)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
