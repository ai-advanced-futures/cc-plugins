"""The general check: the rules of the brain standard (standard section 9)."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from knowledgelib import DataError, UsageError, links, manifest, okf, probe, registry
from knowledgelib.issues import ERROR, SKIP, WARN, Issue, report
from knowledgelib.okf import shown

RULES = {
    "K-registry": "ERROR", "K-manifest": "WARN, ERROR", "K-root-index": "ERROR",
    "K-dir-index": "ERROR", "K-log": "ERROR", "K-links-tsv": "ERROR", "K-okf": "ERROR",
    "K-fields": "ERROR", "K-provenance": "ERROR", "K-id": "ERROR", "K-links-block": "ERROR",
    "K-fresh": "ERROR, SKIP", "K-link": "ERROR, SKIP", "K-remote-link": "WARN, SKIP",
    "K-unknown-graph": "WARN", "K-size": "WARN",
}
ACTOR_RE = re.compile(r"^(human:[A-Za-z0-9._-]+|process:[A-Za-z0-9._-]+|[A-Za-z0-9._-]+/[A-Za-z0-9._-]+)$")
TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")
DATE_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
STATUSES = ("draft", "stable", "deprecated")
MAX_LINES, MAX_WORDS = 100, 600


def line_of(text, key) -> int:
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(f"{key}:"):
            return number
    return 1


def stamp_problem(value) -> str | None:
    if not isinstance(value, dict) or set(value) != {"by", "at"}:
        return "must hold by and at, and nothing else"
    if not ACTOR_RE.match(str(value["by"])):
        return f"by {value['by']!r} is not an actor: use human:<login>, <plugin>/<version>, or process:<id>"
    if not TIME_RE.match(str(value["at"])):
        return f"at {value['at']!r} is not a time with a UTC offset"
    return None


def check_structure(root, bundle) -> list[Issue]:
    issues = []
    index = bundle / "index.md"
    if not index.is_file():
        issues.append(Issue(ERROR, "K-root-index", "the bundle has no root index.md", shown(root, index)))
    else:
        page = okf.read_page(index)
        if page.error or set(page.frontmatter or {}) != {"okf_version"}:
            issues.append(Issue(ERROR, "K-root-index", "the root index.md frontmatter must hold okf_version only", shown(root, index)))
    for sub_index in sorted(bundle.rglob("index.md")):
        rel = sub_index.relative_to(bundle)
        if sub_index == index or any(part.startswith(".") for part in rel.parts):
            continue
        if okf.FRONTMATTER_RE.match(okf.read_text(sub_index)):
            issues.append(Issue(ERROR, "K-dir-index", "a directory index.md has no frontmatter", shown(root, sub_index)))
    log = bundle / "log.md"
    if not log.is_file():
        issues.append(Issue(ERROR, "K-log", "the bundle has no log.md", shown(root, log)))
    else:
        text = okf.read_text(log)
        if okf.FRONTMATTER_RE.match(text):
            issues.append(Issue(ERROR, "K-log", "log.md has no frontmatter", shown(root, log)))
        dates = []
        for number, line in enumerate(text.splitlines(), 1):
            if line.startswith("## "):
                match = DATE_HEADING_RE.match(line)
                if match:
                    dates.append((match.group(1), number))
                else:
                    issues.append(Issue(ERROR, "K-log", f"the heading {line!r} is not ## YYYY-MM-DD", shown(root, log), number))
        for (earlier, _), (later, number) in zip(dates, dates[1:]):
            if later > earlier:
                issues.append(Issue(ERROR, "K-log", f"{later} comes after {earlier}: write the newest date first", shown(root, log), number))
    tsv = bundle / "links.tsv"
    if not tsv.is_file():
        issues.append(Issue(ERROR, "K-links-tsv", "the bundle has no links.tsv", shown(root, tsv)))
    elif okf.read_text(tsv).split("\n", 1)[0].split("\t")[:3] != ["source", "relation", "target"]:
        issues.append(Issue(ERROR, "K-links-tsv", "links.tsv must start with the columns source, relation, target", shown(root, tsv)))
    return issues


def check_page(root, bundle, data, file) -> list[Issue]:
    rel = file.relative_to(bundle).as_posix()
    where = shown(root, file)
    text = okf.read_text(file)
    page = okf.parse_text(file, text)
    if page.error:
        return [Issue(ERROR, "K-okf", page.error, where)]
    fm = page.frontmatter
    if not isinstance(fm.get("type"), str) or not fm["type"].strip():
        return [Issue(ERROR, "K-okf", "the page has no type", where)]
    issues = []

    def add(rule, key, message, level=ERROR):
        issues.append(Issue(level, rule, message, where, line_of(text, key)))

    if not isinstance(fm.get("title"), str) or not fm["title"].strip():
        add("K-fields", "title", "the page has no title")
    description = fm.get("description")
    if not isinstance(description, str) or not description.strip():
        add("K-fields", "description", "the page has no description")
    elif "\n" in description.strip():
        add("K-fields", "description", "the description must be one line")
    if "status" in fm and fm["status"] not in STATUSES:
        add("K-fields", "status", f"status {fm['status']!r} is not draft, stable, or deprecated")
    if "protected" in fm and not isinstance(fm["protected"], bool):
        add("K-fields", "protected", "protected must be true or false")
    if "generated" not in fm:
        add("K-provenance", "type", "the page has no generated: {by, at}")
    elif (problem := stamp_problem(fm["generated"])):
        add("K-provenance", "generated", f"generated {problem}")
    if "verified" in fm:
        if not isinstance(fm["verified"], list):
            add("K-provenance", "verified", "verified must be a list")
        else:
            for item in fm["verified"]:
                if (problem := stamp_problem(item)):
                    add("K-provenance", "verified", f"verified {problem}")
    folder = rel.split("/")[0] if "/" in rel else "."
    if not manifest.is_fixed(data, rel):
        if folder not in data["id_folders"]:
            add("K-id", "type", f"the page is not in a folder of id_folders ({', '.join(data['id_folders'])})")
        elif not manifest.id_matches(data, rel):
            add("K-id", "type", f"the file name does not match id_pattern {data['id_pattern']}")
    if okf.frontmatter_links(fm) and okf.LINKS_START not in page.body:
        add("K-links-block", "type", "the page has links and no LINKS block. Run the regen of the brain.")
    lines, words = okf.size_of(text)
    if lines >= MAX_LINES or words >= MAX_WORDS:
        issues.append(Issue(WARN, "K-size", f"the page has {lines} lines and {words} words. Move long text to a linked page.", where, 1))
    return issues


def check_bundle(root, bundle) -> list[Issue]:
    bundle = Path(bundle)
    where = shown(root, bundle / manifest.NAME)
    try:
        data = manifest.read(bundle)
    except DataError as error:
        return [Issue(ERROR, "K-manifest", str(error), where)]
    if data is None:
        return [Issue(WARN, "K-manifest", "not on the standard yet: the bundle has no manifest.md", where)]
    issues = [Issue(ERROR, "K-manifest", problem, where) for problem in manifest.problems(data)]
    if issues:
        return issues
    issues += check_structure(root, bundle)
    for file in okf.bundle_pages(bundle):
        issues += check_page(root, bundle, data, file)
    return issues


def body_line(text, value) -> int:
    for number, line in enumerate(text.splitlines(), 1):
        if value.lstrip("/") in line:
            return number
    return 1


def not_in_clone(root, graph) -> bool:
    """True for a local graph that git does not keep and whose folder is absent in this clone."""
    return graph is not None and not graph.remote and not graph.git and not (Path(root) / graph.path).is_dir()


def check_links(root, graphs, name, bundle, cache_only) -> list[Issue]:
    issues = []
    for file in okf.bundle_pages(bundle):
        text = okf.read_text(file)
        page = okf.parse_text(file, text)
        if page.error:
            continue
        pairs = okf.frontmatter_links(page.frontmatter)
        pairs += [("body", link) for link in okf.body_links(file, bundle, page.body)]
        where = shown(root, file)
        for field, value in pairs:
            try:
                target = links.resolve(root, graphs, name, value, cache_only)
            except UsageError:
                continue
            number = body_line(text, value) if field == "body" else line_of(text, field)
            if target.state == links.MISSING and not_in_clone(root, graphs.get(target.graph)):
                issues.append(Issue(SKIP, "K-link", f"{where}: {value} is in the graph {target.graph}, which is not in this clone: git does not keep it"))
            elif target.state == links.MISSING:
                issues.append(Issue(ERROR, "K-link", f"{field}: {value} does not resolve", where, number))
            elif target.state == links.UNKNOWN:
                issues.append(Issue(WARN, "K-unknown-graph", f"{field}: {value} names the graph {target.graph}, which is not in .claude/knowledge.json", where, number))
            elif target.state == links.REMOTE_MISSING:
                issues.append(Issue(WARN, "K-remote-link", f"{field}: {value} does not resolve in the remote graph {target.graph}", where, number))
            elif target.state == links.NO_CACHE:
                issues.append(Issue(SKIP, "K-remote-link", f"{where}: {value} is in the remote graph {target.graph}, which has no cache. Run: knowledge.py fetch {target.graph}"))
    return issues


def check_fresh(root, name, bundle, data, probe_find) -> list[Issue]:
    try:
        found = probe.locate(data["plugin"], data["save_code"], probe_find)
    except DataError as error:
        return [Issue(ERROR, "K-fresh", f"{name}: {error}", shown(root, bundle / manifest.NAME))]
    if found is None:
        return [Issue(SKIP, "K-fresh", f"{name}: the plugin {data['plugin']} is not installed, so the generated files are not checked")]
    save_code = found[1]
    command = [sys.executable, str(save_code), "--root", str(root), "regen", "--check"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return []
    if result.returncode != 1:
        return [Issue(ERROR, "K-fresh", f"regen --check of {data['plugin']} failed: {(result.stderr or result.stdout).strip()}", shown(root, bundle / manifest.NAME))]
    issues = []
    for line in result.stdout.splitlines():
        if not line.startswith("STALE: "):
            continue
        rel = line[len("STALE: "):].strip()
        try:
            (Path(root) / rel).resolve().relative_to(bundle.resolve())
        except ValueError:
            continue
        issues.append(Issue(ERROR, "K-fresh", f"the generated file is stale. Run the regen of {data['plugin']}.", rel))
    return issues


def check_graph(root, graphs, name, cache_only=False, probe_find=None) -> list[Issue]:
    probe_find = probe_find or probe.find
    graph = graphs[name]
    if graph.remote:
        bundle = links.bundle_dir(root, graph, cache_only)
        if bundle is None:
            return [Issue(SKIP, "K-remote-link", f"{name}: the remote graph has no cache. Run: knowledge.py fetch {name}")]
        try:
            data = manifest.read(bundle)
        except DataError as error:
            return [Issue(ERROR, "K-manifest", str(error), f"{name}:/manifest.md")]
        return [] if data else [Issue(WARN, "K-manifest", f"not on the standard yet: the remote graph {name} has no manifest.md", f"{name}:/manifest.md")]
    bundle = Path(root) / graph.path
    if not bundle.is_dir():
        if not graph.git:
            return [Issue(WARN, "K-registry", f"{name} is not in this clone: git does not keep {graph.path}. "
                          f"To fix it: 1. Run the setup skill of the brain {name} in this clone. When it asks if git "
                          f"keeps the brain, choose the choice of this project, out of git. It makes an empty brain "
                          f"in {graph.path}. 2. Or, if the folder is in another place, change the path of {name} in "
                          f"{registry.REGISTRY}. Then run this check again.", str(registry.REGISTRY))]
        return [Issue(ERROR, "K-registry", f"the path of {name} is not a folder: {graph.path}", str(registry.REGISTRY))]
    issues = check_bundle(root, bundle)
    if any(issue.rule == "K-manifest" for issue in issues):
        return issues
    data = manifest.read(bundle)
    issues += check_links(root, graphs, name, bundle, cache_only)
    issues += check_fresh(root, name, bundle, data, probe_find)
    return issues


def check_all(root, names=(), cache_only=False, probe_find=None) -> list[Issue]:
    graphs = registry.read(root)
    if not graphs:
        return [Issue(ERROR, "K-registry", "the project has no .claude/knowledge.json. Run the setup skill of a brain.", str(registry.REGISTRY))]
    for name in names:
        registry.require(graphs, name)
    issues = []
    for name in names or list(graphs):
        issues += check_graph(root, graphs, name, cache_only, probe_find)
    return issues


def cmd_check(args) -> int:
    return report(check_all(args.root, args.graph or (), args.cache_only), strict=args.strict)


def cmd_brain_root(args) -> int:
    """Print the root of the plugin that a graph names. Exit 1 with no output when it is not installed."""
    graphs = registry.read(args.root)
    graph = graphs.get(args.graph)
    if graph is None:
        raise DataError(f"the graph {args.graph!r} is not in the registry")
    bundle = links.bundle_dir(args.root, graph, True)
    if bundle is None:
        raise DataError(f"{args.graph} is a remote graph with no cache. Run: knowledge.py fetch {args.graph}")
    data = manifest.read(bundle)
    if data is None:
        raise DataError(f"{args.graph} has no manifest.md")
    found = probe.locate(data.get("plugin"), data.get("save_code"))
    if found is None:
        return 1
    print(found[0])
    return 0


def cmd_brain_check(args) -> int:
    """Run the brain check of each named graph, one time for each pair of plugin and save_code.

    The skill `checking` runs this command, so its grant names only a script of this plugin (STORY-282).
    The output and the exit code of each save code go through. A graph with no brain check gives one
    `SKIP: brain-check (...)` line and exit 1, so the caller never reports a pass for it.
    """
    graphs = registry.read(args.root)
    seen, worst = set(), 0
    for name in args.graph:
        try:
            graph = graphs.get(name)
            if graph is None:
                raise DataError(f"the graph {name!r} is not in the registry")
            bundle = links.bundle_dir(args.root, graph, True)
            if bundle is None:
                raise DataError(f"{name} is a remote graph with no cache. Run: knowledge.py fetch {name}")
            data = manifest.read(bundle)
            if data is None:
                raise DataError(f"{name} has no manifest.md")
            pair = (data.get("plugin"), data.get("save_code"))
            if pair in seen:
                continue
            seen.add(pair)
            found = probe.locate(*pair)
            if found is None:
                raise DataError(f"the plugin {pair[0]} of {name} is not installed")
        except DataError as error:
            print(f"SKIP: brain-check ({error})", flush=True)
            worst = max(worst, 1)
            continue
        result = subprocess.run([sys.executable, str(found[1]), "--root", str(args.root), "check"],
                                capture_output=True, text=True)
        sys.stdout.write(result.stdout)
        sys.stdout.flush()
        sys.stderr.write(result.stderr)
        worst = max(worst, abs(result.returncode))
    return worst


def _root_option(parser) -> None:
    """Let `--root` come after the command name, so a grant can name the command first (STORY-282)."""
    parser.add_argument("--root", default=argparse.SUPPRESS, help="the project root (also valid before the command)")


def register(sub) -> None:
    brain_root = sub.add_parser("brain-root", help="print the root of the plugin that a graph names")
    brain_root.add_argument("--graph", required=True, help="the name of a graph")
    brain_root.set_defaults(run=cmd_brain_root)
    brain_check = sub.add_parser("brain-check", help="run the check of the save code of each named graph")
    brain_check.add_argument("--graph", action="append", required=True, help="the name of a changed graph (repeat for more)")
    _root_option(brain_check)
    brain_check.set_defaults(run=cmd_brain_check)
    parser = sub.add_parser("check", help="run the general check of the standard")
    parser.add_argument("--graph", action="append", help="check this graph only (repeat for more)")
    parser.add_argument("--strict", action="store_true", help="exit 1 on a warning")
    parser.add_argument("--cache-only", action="store_true", help="never clone a remote graph (hook mode)")
    _root_option(parser)
    parser.set_defaults(run=cmd_check)
