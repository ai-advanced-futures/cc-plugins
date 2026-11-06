# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read the jtbd graph for one run, and write what it holds into a result file of this plugin.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_read.py latest --out-dir .product-finance/upstream
       uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_read.py run --run-id <R> --case <C> --out-dir <D>

`latest` is for a person's run: it takes the newest jtbd run that holds a `customer_segment` or a
`willingness_to_pay` result. `run` is for a plugin run: it takes the one jtbd run with that
`run_id` and that `case`. The script finds the jtbd plugin, asks its save code for the pages and
the results, and writes the printed document into `--out-dir`. It reads no file of the jtbd graph
itself, and it writes only into `.product-finance/` of the project.

The last line is `JTBD: <file> jtbd:<Run page>` or `NO-JTBD: <reason>`; both exit 0. A line
`SKIP: ...` before it names a jtbd run that was passed over. Exit 1: the file cannot be written.
Exit 2: wrong arguments. The environment variable PRODUCT_FINANCE_JTBD_PYTHON names the Python
that runs the save code; when it is not set, the save code runs with `uv run`.
Standard library only.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.result_name import result_name  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
JTBD_PLUGIN = "jtbd-market-discovery"
SAVE_SCRIPT = "scripts/jtbd_graph.py"
PYTHON_VARIABLE = "PRODUCT_FINANCE_JTBD_PYTHON"
WORK_FOLDER = ".product-finance"
WANTED_KINDS = ("customer_segment", "willingness_to_pay")
RUN_KEY = re.compile(r"RUN-\d+")
INSTALL_LINE = "the jtbd-market-discovery plugin is not installed. Install it: claude plugin install jtbd-market-discovery@cc-plugins."
NO_GRAPH_LINE = "this project has no jtbd graph. Run /jtbd-market-discovery:discover to make one."


class NoInput(Exception):
    """The read gives no input. The message is the reason, in plain words."""


def find_jtbd_plugin():
    """The root of the jtbd plugin, or None."""
    probe = PLUGIN_ROOT / "scripts" / "probe-plugin.sh"
    try:
        done = subprocess.run(["bash", str(probe), JTBD_PLUGIN, SAVE_SCRIPT], capture_output=True, text=True)
    except OSError:
        return None
    lines = done.stdout.strip().splitlines()
    return Path(lines[-1]) if done.returncode == 0 and lines else None


def save_command(jtbd_root, project_root, *args):
    """The argument list that runs the save code of the jtbd plugin."""
    script = str(Path(jtbd_root) / SAVE_SCRIPT)
    python = os.environ.get(PYTHON_VARIABLE)
    if python:
        return [python, script, "--root", str(project_root), *args]
    if not shutil.which("uv"):
        raise NoInput("uv is not installed, so the jtbd save code cannot run. Install uv, or set %s." % PYTHON_VARIABLE)
    return ["uv", "run", "--quiet", script, "--root", str(project_root), *args]


def first_error_line(text):
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return lines[0] if lines else "no message"


def ask_save_code(jtbd_root, project_root, *args):
    """Run one operation of the save code. Return (exit code, parsed JSON or None, first error line)."""
    try:
        done = subprocess.run(save_command(jtbd_root, project_root, *args), capture_output=True, text=True)
    except OSError as error:
        raise NoInput("the jtbd save script failed: %s" % error)
    data = None
    if done.returncode == 0:
        try:
            data = json.loads(done.stdout)
        except ValueError:
            pass
    return done.returncode, data, first_error_line(done.stderr)


def run_pages(jtbd_root, project_root):
    code, data, error = ask_save_code(jtbd_root, project_root, "pages", "Run")
    if code == 2:
        raise NoInput(NO_GRAPH_LINE)
    if code != 0 or not isinstance(data, list):
        raise NoInput("the jtbd save script failed: %s" % error)
    pages = []
    for page in data:
        if not isinstance(page, dict):
            continue
        key = Path(str(page.get("path", ""))).stem
        frontmatter = page.get("frontmatter")
        if RUN_KEY.fullmatch(key) and isinstance(frontmatter, dict):
            pages.append({"key": key, "link": "jtbd:/runs/%s.md" % key, "frontmatter": frontmatter})
    return pages


def run_results(jtbd_root, project_root, key):
    """The document of one run: (document, reason). The document is None when it cannot be read."""
    code, data, error = ask_save_code(jtbd_root, project_root, "results", "--run", key)
    if code == 0 and isinstance(data, dict):
        return data, ""
    if code in (0, 1):
        return None, error if code else "the save code printed no JSON document"
    raise NoInput("the jtbd save script failed: %s" % error)


def holds_wanted_result(document):
    results = document.get("results")
    return isinstance(results, list) and any(isinstance(item, dict) and item.get("kind") in WANTED_KINDS for item in results)


def choose_latest(jtbd_root, project_root, pages, skips):
    """Newest run with a segment or a price. Two such runs that end together give no input."""
    dated = sorted((page for page in pages if page["frontmatter"].get("finished_at")),
                   key=lambda page: (page["frontmatter"]["finished_at"], page["key"]), reverse=True)
    chosen = None
    for page in dated:
        if chosen is not None and page["frontmatter"]["finished_at"] != chosen[1]["frontmatter"]["finished_at"]:
            break
        document, reason = run_results(jtbd_root, project_root, page["key"])
        if document is None:
            skips.append("SKIP: %s: %s" % (page["link"], reason))
            continue
        if not holds_wanted_result(document):
            continue
        if chosen is None:
            chosen = (document, page)
            continue
        first, second = sorted((chosen[1]["link"], page["link"]))
        raise NoInput("2 jtbd runs ended at %s: %s and %s. product-finance reads neither."
                      % (page["frontmatter"]["finished_at"], first, second))
    if chosen is None:
        raise NoInput("the jtbd graph has no run with a customer segment or a willingness to pay result.")
    return chosen


def choose_run(jtbd_root, project_root, pages, run_id, case):
    """The one run with this run_id and this case."""
    hits = [page for page in pages if page["frontmatter"].get("run_id") == run_id and page["frontmatter"].get("case") == case]
    if not hits:
        raise NoInput("the jtbd graph has no run %s in case %s." % (run_id, case))
    if len(hits) > 1:
        raise NoInput("the jtbd graph has %d runs %s in case %s: %s." % (len(hits), run_id, case, ", ".join(page["link"] for page in hits)))
    document, _reason = run_results(jtbd_root, project_root, hits[0]["key"])
    if document is None:
        raise NoInput("the jtbd run %s in case %s has no result pages." % (run_id, case))
    return document, hits[0]


def file_name(document):
    run = document.get("run") if isinstance(document.get("run"), dict) else {}
    if not run.get("finished_at") or not isinstance(document.get("command"), str):
        raise NoInput("the jtbd run has no finish time or no command, so the file has no name.")
    if not run.get("subject"):
        raise NoInput("the jtbd run %s in case %s has no subject." % (run.get("run_id"), run.get("case")))
    try:
        return result_name(run["finished_at"], document["command"], run["subject"], run.get("run_id"))
    except ValueError as error:
        raise NoInput("the jtbd run has a value that cannot be part of a file name: %s" % error)


def inside_work_folder(project_root, out_dir):
    """The resolved --out-dir, when it is inside `.product-finance/` of the project; else None."""
    target = (Path(project_root) / out_dir).resolve()
    allowed = (Path(project_root) / WORK_FOLDER).resolve()
    return target if target == allowed or allowed in target.parents else None


def git_root():
    try:
        done = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    except OSError:
        return Path.cwd()
    return Path(done.stdout.strip()) if done.returncode == 0 and done.stdout.strip() else Path.cwd()


def build_parser():
    parser = argparse.ArgumentParser(prog="jtbd_read.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", help="the project root (default: the git root of the working folder)")
    sub = parser.add_subparsers(dest="mode", required=True)
    latest = sub.add_parser("latest", help="a person's run: the newest jtbd run with a segment or a price")
    latest.add_argument("--out-dir", required=True)
    run = sub.add_parser("run", help="a plugin run: the jtbd run with this run_id and case")
    run.add_argument("--run-id", required=True)
    run.add_argument("--case", required=True)
    run.add_argument("--out-dir", required=True)
    return parser


def read_and_write(args, project_root, out_dir, skips):
    """Return the last line, or raise NoInput. Write the file when there is input."""
    jtbd_root = find_jtbd_plugin()
    if jtbd_root is None:
        raise NoInput(INSTALL_LINE)
    pages = run_pages(jtbd_root, project_root)
    if args.mode == "latest":
        document, page = choose_latest(jtbd_root, project_root, pages, skips)
    else:
        document, page = choose_run(jtbd_root, project_root, pages, args.run_id, args.case)
    name = file_name(document)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / name
    target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "JTBD: %s %s" % (target.relative_to(project_root.resolve()).as_posix(), page["link"])


def main(argv):
    args = build_parser().parse_args(argv)
    project_root = Path(args.root).resolve() if args.root else git_root().resolve()
    out_dir = inside_work_folder(project_root, args.out_dir)
    if out_dir is None:
        sys.stderr.write("--out-dir must be inside %s/ of the project: %r\n" % (WORK_FOLDER, args.out_dir))
        return 2
    skips = []
    try:
        last = read_and_write(args, project_root, out_dir, skips)
    except NoInput as reason:
        last = "NO-JTBD: %s" % reason
    except OSError as error:
        sys.stderr.write("cannot write the file: %s\n" % error)
        return 1
    for line in skips:
        print(line)
    print(last)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
