"""The general check: the rules of the brain standard (standard section 9)."""
from __future__ import annotations

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
    "K-fresh": "ERROR, SKIP", "K-link": "ERROR", "K-remote-link": "WARN, SKIP",
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
            if target.state == links.MISSING:
                issues.append(Issue(ERROR, "K-link", f"{field}: {value} does not resolve", where, number))
            elif target.state == links.UNKNOWN:
                issues.append(Issue(WARN, "K-unknown-graph", f"{field}: {value} names the graph {target.graph}, which is not in .claude/knowledge.json", where, number))
            elif target.state == links.REMOTE_MISSING:
                issues.append(Issue(WARN, "K-remote-link", f"{field}: {value} does not resolve in the remote graph {target.graph}", where, number))
            elif target.state == links.NO_CACHE:
                issues.append(Issue(SKIP, "K-remote-link", f"{where}: {value} is in the remote graph {target.graph}, which has no cache. Run: knowledge.py fetch {target.graph}"))
    return issues


def check_fresh(root, name, bundle, data, probe_find) -> list[Issue]:
    plugin_root = probe_find(data["plugin"], data["save_code"])
    if plugin_root is None:
        return [Issue(SKIP, "K-fresh", f"{name}: the plugin {data['plugin']} is not installed, so the generated files are not checked")]
    command = [sys.executable, str(Path(plugin_root) / data["save_code"]), "--root", str(root), "regen", "--check"]
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


def register(sub) -> None:
    parser = sub.add_parser("check", help="run the general check of the standard")
    parser.add_argument("--graph", action="append", help="check this graph only (repeat for more)")
    parser.add_argument("--strict", action="store_true", help="exit 1 on a warning")
    parser.add_argument("--cache-only", action="store_true", help="never clone a remote graph (hook mode)")
    parser.set_defaults(run=cmd_check)
