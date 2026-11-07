"""Read the graphs of jtbd-market-discovery and competitive-intelligence.

gtm reads each graph through the save code of its writer, as a subprocess. It
never reads a file in the folder of another plugin. read_graphs(root) runs the
read operations, writes the JSON that each one prints into a snapshot file
under <root>/.gtm/upstream/<graph>/, and returns the snapshot paths. It also
writes the note lines to <root>/.gtm-graph-notes.txt.

This module writes only into <root>/.gtm/upstream/ and that one notes file. The
read operations of the writers write no page.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PROBE = Path(__file__).resolve().parent / "probe-plugin.sh"
UPSTREAM = Path(".gtm") / "upstream"
# Outside .gtm on purpose: when .gtm or .gtm/upstream is a link, the person still gets the lines.
NOTES_FILE = Path(".gtm-graph-notes.txt")
DISCOVER = "jtbd-market-discovery:discover"
JTBD_LENS = "jtbd-performance"
CI_TYPES = ("Competitor", "Offer", "SwotItem", "LensResult")


class _Stop(Exception):
    """A read of one graph ends here. The text is the line for stderr."""


def _last_line(text: str) -> str:
    """The cause of a failure: a Python traceback ends with the error, and its first line does not name it."""
    lines = text.strip().splitlines()
    return lines[-1].strip() if lines else ""


def _graph_is_missing(cause: str) -> bool:
    """Whether an exit 2 says that the graph or its folder is absent. Only then does the person make the graph."""
    return "is not in " in cause or "does not exist" in cause


def _write_file(path: Path, text: str) -> None:
    """Write a new file and move it over the target. os.replace puts the file in place of a link
    and does not write through it, so a link at the target never changes the file it points to."""
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def _unsafe_upstream(root: Path) -> str:
    """Why this module may not write under <root>/.gtm/upstream/, or "" when it may.

    <root>/.gtm and <root>/.gtm/upstream must be real folders inside the root, or absent.
    A link there would send each write and the rmtree to a place outside the project.
    """
    for rel in (Path(".gtm"), UPSTREAM):
        path = root / rel
        if not os.path.lexists(path):
            continue
        if path.is_symlink() or not path.is_dir() or not path.resolve().is_relative_to(root):
            return f"{rel.as_posix()} is a link or is not a folder inside the project, so gtm writes nothing there."
    return ""


def _python() -> list[str]:
    """The Python that runs a save script: GTM_GRAPH_PYTHON, then uv, then python3."""
    chosen = os.environ.get("GTM_GRAPH_PYTHON")
    if chosen:
        return [chosen]
    if shutil.which("uv"):
        return ["uv", "run", "--quiet"]
    return ["python3"]


def _probe(plugin: str, script: str) -> Path | None:
    try:
        result = subprocess.run(["bash", str(PROBE), plugin, f"scripts/{script}"],
                                capture_output=True, text=True)
    except OSError:
        return None
    out = result.stdout.strip()
    return Path(out) if result.returncode == 0 and out else None


class _Graph:
    def __init__(self, root: Path, key: str, graph: str, plugin: str, script: str, fix: str):
        self.root = root
        self.key = key  # the key of plugin_inputs
        self.graph = graph
        self.plugin = plugin
        self.script = script
        self.fix = fix  # what the person runs to make the graph
        self.plugin_root: Path | None = None

    @property
    def folder(self) -> Path:
        return self.root / UPSTREAM / self.graph

    def _continues(self) -> str:
        return f"gtm continues with no {self.graph} input."

    def no_graph(self, why: str, fix: str = "") -> _Stop:
        return _Stop(f"NO-GRAPH: {self.graph}: {why} {self._continues()}" + (f" {fix}" if fix else ""))

    def prepare(self) -> None:
        if self.folder.is_symlink():
            self.folder.unlink()  # remove the link itself: rmtree and mkdir would go through it
        shutil.rmtree(self.folder, ignore_errors=True)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.plugin_root = _probe(self.plugin, self.script)
        if self.plugin_root is None:
            raise self.no_graph(f"gtm found no {self.plugin} plugin that saves a graph.")

    def read(self, *args: str):
        """Run one read operation. It gives the JSON that the save script prints."""
        label = " ".join(args)
        script = self.plugin_root / "scripts" / self.script
        try:
            result = subprocess.run([*_python(), str(script), "--root", str(self.root), *args],
                                    capture_output=True, text=True)
        except OSError as error:
            raise _Stop(f"GRAPH-READ-FAILED: {self.graph}: {label} did not start: {error}. "
                        f"{self._continues()}") from error
        cause = _last_line(result.stderr)
        if result.returncode == 2:
            raise self.no_graph(f"the project has no {self.graph} graph ({cause}).",
                                self.fix if _graph_is_missing(cause) else "")
        if result.returncode != 0:
            raise _Stop(f"GRAPH-READ-FAILED: {self.graph}: {label} exited {result.returncode}: "
                        f"{cause}. {self._continues()}")
        try:
            return json.loads(result.stdout)
        except ValueError as error:
            raise _Stop(f"GRAPH-READ-FAILED: {self.graph}: {label} exited 0: "
                        f"stdout is not JSON ({error}). {self._continues()}") from error

    def write(self, name: str, data) -> Path:
        path = self.folder / f"{name}.json"
        _write_file(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return path


def _jtbd(root: Path) -> _Graph:
    return _Graph(root, "jtbd", "jtbd", "jtbd-market-discovery", "jtbd_graph.py",
                  "Run /jtbd-market-discovery:discover to make the graph.")


def _ci(root: Path) -> _Graph:
    return _Graph(root, "competitive_intelligence", "competitive-intelligence",
                  "competitive-intelligence", "ci_graph.py",
                  "Run /competitive-intelligence:discover or /competitive-intelligence:analyze "
                  "to make the graph.")


def _read_jtbd(graph: _Graph) -> list[Path]:
    """The newest finished discover run: its Run page, Outcome, Segment and Result pages."""
    runs = [page for page in graph.read("pages", "Run")
            if page["frontmatter"].get("command") == DISCOVER and page["frontmatter"].get("finished_at")]
    if not runs:
        raise graph.no_graph("the jtbd graph has no finished discover run.")
    newest = max(runs, key=lambda page: (str(page["frontmatter"]["finished_at"]), page["path"]))
    key = Path(newest["path"]).stem
    written = [graph.write("Run", [newest])]
    for type_name in ("Outcome", "Segment"):
        pages = graph.read("pages", type_name, "--run", key)
        if pages:
            written.append(graph.write(type_name, pages))
    results = graph.read("results", "--run", key)
    if results.get("results"):
        written.append(graph.write("results", results))
    return written


def _read_ci(graph: _Graph) -> list[Path]:
    """Each Competitor, Offer, SwotItem page, and the LensResult pages of the jtbd lens."""
    written = []
    for type_name in CI_TYPES:
        pages = graph.read("pages", type_name)
        if type_name == "LensResult":
            pages = [page for page in pages if page["frontmatter"].get("lens") == JTBD_LENS]
        if pages:
            written.append(graph.write(type_name, pages))
    if not written:
        raise graph.no_graph("the graph has no competitor, offer, SWOT or lens page.")
    return written


def read_graphs(root) -> tuple[dict[str, list[str]], list[str]]:
    """Read both graphs. It gives (inputs, notes).

    inputs holds a key only when its graph gave 1 or more snapshot files. notes
    is the list of the lines for stderr. The same lines go to NOTES_FILE in the
    root, 1 line for each note, and the file is empty when there is no note. It is
    written on each read, also when .gtm is a link, so /gtm:run shows the lines
    from the file and never shows the lines of an older run.
    """
    root = Path(root).resolve()
    inputs: dict[str, list[str]] = {}
    notes: list[str] = []
    unsafe = _unsafe_upstream(root)
    if unsafe:
        for graph in (_jtbd(root), _ci(root)):
            notes.append(f"GRAPH-READ-FAILED: {graph.graph}: {unsafe} {graph._continues()}")
    else:
        for graph, reader in ((_jtbd(root), _read_jtbd), (_ci(root), _read_ci)):
            try:
                graph.prepare()
                paths = reader(graph)
            except _Stop as stop:
                notes.append(str(stop))
                continue
            if paths:
                inputs[graph.key] = [str(path) for path in paths]
    _write_file(root / NOTES_FILE, "".join(f"{note}\n" for note in notes))
    return inputs, notes
