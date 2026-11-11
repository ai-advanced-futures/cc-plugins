"""The read of a run of a plugin that has a graph (`graph` in the plugin map: jtbd-market-discovery and
competitive-intelligence).

Such a plugin writes its results as pages of a knowledge graph. `find` reads one run of it through the save
script of that plugin, as a subprocess, and keeps what it read as a state file of the case, a snapshot:

1. `probe` finds the plugin with `scripts/probe-plugin.sh <plugin> <save script>`.
2. `results --run-id <run_id> --case <case folder>` of the save script prints the `Result` pages of the run as
   one document in the shape of a result file (`plugin-result/1`).
3. `pages Run` and `pages Result --run <Run page>` give the `Run` page of the run and the `Result` page of each
   entry. The entry id is the part after the last `/` of the first alias of a `Result` page.
4. The printed `cites.file` of an entry is the path of a `Result` page. `find` writes it as the snapshot path of
   the run of that page, and reads that run the same way when the case has no snapshot of it.
5. The document goes to `team/upstream/<name>` of the case, where `<name>` is the name that the checker gives a
   result file with the same fields. A snapshot is written one time: a later read finds the file and does not
   write it again, because a page of the case and a decision pin its bytes.

`find` gives `(path relative to the git root, document, path, fields)`. The fields are `graph_run`
(`<graph>:/<path of the Run page>`) and `graph_results` (`{"<entry id>": "<graph>:/<path of the Result page>"}`).
It raises `NoGraphRun` when the graph gives no run that passes the checker: no plugin, no graph, no run with this
`run_id` and case, or a document with an error. The text names the graph and the first line of the error. It
raises `TeamRefused` when more than one `Run` page holds the `run_id` and the case.

There is no fallback to `.<plugin>/results/`. This module makes no network call: it starts only the probe and the
save script. It writes only under `team/upstream/` of the case, and `bc.py` calls it under the team lock.

Standard library only. Python 3.9 syntax only.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from lib import paths, plugin_map, plugin_result, team_files

UPSTREAM = "team/upstream"
_PROBE = paths.PLUGIN_ROOT / "scripts" / "probe-plugin.sh"
_REGISTRY = Path(".claude") / "knowledge.json"


class NoGraphRun(team_files.TeamRefused):
    """The graph gives no run that the case can use. The text is the reason of the gap. It is a `TeamRefused`,
    so a caller that does not record a gap prints it as a refusal and not as an unexpected error."""


def graph_of(command: str, m=None):
    """The `graph` object of the plugin of a map command, or None when the plugin has no graph."""
    return plugin_map.graph(plugin_map.load() if m is None else m, command.split(":")[0])


def graph_plugins(m=None) -> list:
    """The name of each map plugin that has a graph."""
    m = plugin_map.load() if m is None else m
    return sorted(name for name in m.get("plugins", {}) if plugin_map.graph(m, name))


def upstream_dir(case_dir) -> Path:
    return Path(case_dir) / UPSTREAM


def probe(plugin: str, save_script: str):
    """The root of the installed plugin that holds the save script, or None."""
    try:
        done = subprocess.run(["bash", str(_PROBE), plugin, save_script], capture_output=True, text=True)
    except OSError:
        return None
    out = done.stdout.strip()
    return Path(out) if done.returncode == 0 and out else None


def runner() -> list:
    """The command that runs a save script. It is `uv run`, as for `bc.py`: the save script gives its own
    Python version and packages in its PEP 723 block. No environment variable chooses the program, because
    the settings of a project can set each variable."""
    return ["uv", "run", "--quiet"]


def _first_line(text: str) -> str:
    """The cause of a failure. A save script prints 1 `ERROR:` line; a traceback ends with the error."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    for line in lines:
        if line.startswith("ERROR:"):
            return line
    return lines[-1] if lines else "no error text"


def _values(value) -> list:
    """The targets of a link field: 1 text or a list of texts."""
    if isinstance(value, str):
        return [value]
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


class _Graph:
    """One graph of the project, read through the save script of its plugin."""

    def __init__(self, case: Path, root: Path, plugin: str, graph: dict):
        self.case, self.root, self.plugin = case, root, plugin
        self.name, self.save_script = graph["name"], graph["save_script"]
        self._script = None
        self._bundle = None
        self._runs = None
        self._results = None

    def miss(self, why: str) -> NoGraphRun:
        return NoGraphRun(f"the {self.name} graph gives no run: {why}")

    def read(self, *args: str):
        """The JSON that one read operation of the save script prints."""
        if self._script is None:
            found = probe(self.plugin, self.save_script)
            if found is None:
                raise self.miss(f"no installed {self.plugin} plugin holds {self.save_script}")
            self._script = Path(found) / self.save_script
        label = " ".join(args)
        try:
            done = subprocess.run([*runner(), str(self._script), "--root", str(self.root), *args],
                                  capture_output=True, text=True)
        except OSError as exc:
            raise self.miss(f"{label} did not start ({exc})") from None
        if done.returncode != 0:
            raise self.miss(f"{label} exited {done.returncode}: {_first_line(done.stderr)}")
        try:
            return json.loads(done.stdout)
        except ValueError:
            raise self.miss(f"{label} printed no JSON") from None

    def bundle(self) -> str:
        """The folder of the graph, relative to the git root, from `.claude/knowledge.json`."""
        if self._bundle is None:
            try:
                registry = json.loads((self.root / _REGISTRY).read_text(encoding="utf-8"))
                folder = registry["graphs"][self.name]["path"]
            except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
                raise self.miss(f"{_REGISTRY.as_posix()} names no graph {self.name}") from None
            if not isinstance(folder, str) or not folder.strip():
                raise self.miss(f"{_REGISTRY.as_posix()} gives no folder for the graph {self.name}")
            self._bundle = folder.strip("/")
        return self._bundle

    def in_bundle(self, shown: str) -> str:
        """`/<path in the bundle>` of a page that the save script names by its path from the git root."""
        prefix = self.bundle() + "/"
        text = str(shown).replace("\\", "/")
        if not text.startswith(prefix):
            raise self.miss(f"the page {shown} is not in the folder {self.bundle()} of the graph")
        return "/" + text[len(prefix):]

    def ref(self, shown: str) -> str:
        return f"{self.name}:{self.in_bundle(shown)}"

    def runs(self) -> list:
        if self._runs is None:
            pages = self.read("pages", "Run")
            self._runs = [p for p in pages if isinstance(p, dict) and isinstance(p.get("frontmatter"), dict)
                          and isinstance(p.get("path"), str)] if isinstance(pages, list) else []
        return self._runs

    def all_results(self) -> list:
        if self._results is None:
            pages = self.read("pages", "Result")
            self._results = [p for p in pages if isinstance(p, dict) and isinstance(p.get("frontmatter"), dict)
                             and isinstance(p.get("path"), str)] if isinstance(pages, list) else []
        return self._results

    def run_of_result(self, shown: str):
        """The `Run` page of the run that wrote a `Result` page."""
        page = next((p for p in self.all_results() if p["path"] == shown), None)
        if page is None:
            raise self.miss(f"an entry cites {shown}, and the graph holds no such Result page")
        targets = _values(page["frontmatter"].get("run"))
        for run in self.runs():
            if self.in_bundle(run["path"]) in targets:
                return run
        raise self.miss(f"the cited page {shown} names no Run page of the graph")

    # -- the snapshot of one run -------------------------------------------------------------------

    def snapshot(self, run_page: dict, doc, seen: frozenset = frozenset()):
        """Write the document of a run as its snapshot, when the case has none. Gives (rel, doc, path, fields)."""
        key = Path(run_page["path"]).stem
        if key in seen:
            raise self.miss(f"the entries of {key} cite each other in a circle")
        if not isinstance(doc, dict):
            raise self.miss(f"results of {key} printed no JSON object")
        run = doc.get("run") if isinstance(doc.get("run"), dict) else {}
        try:
            name = plugin_result.CHECK.result_file_name(run["finished_at"], doc["command"], run["subject"],
                                                        run.get("run_id"))
        except (KeyError, TypeError, AttributeError, ValueError):
            problems = plugin_result.check_result(doc) or ["the run has no finished_at, command or subject"]
            raise self.miss(f"the document of {key} fails the checker: " + "; ".join(problems)) from None
        if Path(name).name != name or name in (".", ".."):
            # command and run_id go into the name unchanged (STORY-264): a `/` or a `..` names a file outside
            # team/upstream/, so the read stops before it opens a file.
            raise self.miss(f"the snapshot name {name!r} of {key} is not 1 file name: its command or run_id "
                            "holds a / or ..")
        path = upstream_dir(self.case) / name
        rel = team_files.inside_root(self.root, path)
        if rel is None:
            raise self.miss(f"{UPSTREAM} of the case is not a folder inside the git root")
        fields = {"graph_run": self.ref(run_page["path"]), "graph_results": self._result_refs(key)}
        if paths.stat_is_file(path):
            try:
                return rel, json.loads(path.read_text(encoding="utf-8")), path, fields
            except (OSError, UnicodeDecodeError, ValueError):
                raise self.miss(f"the snapshot {rel} of the case is not JSON; move it away, then read the run "
                                "again") from None
        self._rewrite_cites(doc, seen | {key})
        problems = plugin_result.check_result(doc)
        if problems:
            raise self.miss(f"the document of {key} fails the checker: " + "; ".join(problems))
        _write_new(path, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        return rel, doc, path, fields

    def _result_refs(self, key: str) -> dict:
        out = {}
        pages = self.read("pages", "Result", "--run", key)
        for page in pages if isinstance(pages, list) else []:
            if not isinstance(page, dict) or not isinstance(page.get("path"), str):
                continue
            front = page.get("frontmatter") if isinstance(page.get("frontmatter"), dict) else {}
            aliases = _values(front.get("aliases"))
            entry_id = (aliases[0] if aliases else Path(page["path"]).stem).rsplit("/", 1)[-1]
            out[entry_id] = self.ref(page["path"])
        return out

    def _rewrite_cites(self, doc: dict, seen: frozenset) -> None:
        """Each `cites.file` that names a `Result` page becomes the snapshot path of the run of that page."""
        for result in doc.get("results") or []:
            for cite in (result.get("cites") or []) if isinstance(result, dict) else []:
                shown = cite.get("file") if isinstance(cite, dict) else None
                if not isinstance(shown, str) or not shown.strip():
                    continue
                run_page = self.run_of_result(shown)
                key = Path(run_page["path"]).stem
                cite["file"] = self.snapshot(run_page, self.read("results", "--run", key), seen)[0]


def _write_new(path: Path, text: str) -> None:
    """Write a new file and move it into place, so a reader never finds a part of it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temp, str(path))
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def find(case_dir, run: dict, m=None):
    """The snapshot of the run of a graph plugin: (path relative to the git root, document, path, fields)."""
    case = Path(case_dir).resolve()
    plugin = run["command"].split(":")[0]
    spec = graph_of(run["command"], m)
    if spec is None:
        raise ValueError(f"{plugin} has no graph in the plugin map")
    root = team_files.repo_root(case)
    run_id, want_case = run["run_id"], team_files.repo_relative(case, case)
    graph = _Graph(case, root, plugin, spec)
    pages = [p for p in graph.runs()
             if p["frontmatter"].get("run_id") == run_id and p["frontmatter"].get("case") == want_case]
    if len(pages) > 1:  # before `results`, which can refuse 2 pages with an error that reads as "no run"
        raise team_files.TeamRefused(f"more than one Run page of the {graph.name} graph holds run_id {run_id}: "
                          f"{', '.join(graph.ref(p['path']) for p in pages)}; ask the person which page the run "
                          "wrote and to remove the other with the forget skill of the knowledge plugin, then run "
                          f"bc.py team-run --status; or record the run as a gap with bc.py team-run --fail "
                          f"{run.get('key') or run_id}")
    doc = graph.read("results", "--run-id", run_id, "--case", want_case)
    if not pages:
        raise graph.miss(f"no Run page holds run_id {run_id} and the case {want_case}")
    return graph.snapshot(pages[0], doc)
