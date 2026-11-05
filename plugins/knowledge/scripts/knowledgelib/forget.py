"""The forget plan (standard section 11): the tree, the references, and the stops."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from knowledgelib import DataError, UsageError, links, manifest, okf, probe, registry

ID_RE = re.compile(r"^(?:[A-Z]+-\d{2,}|\d{4}-.+)$")


@dataclass
class Plan:
    target: str
    tree: list = field(default_factory=list)
    unlinks: list = field(default_factory=list)
    mentions: list = field(default_factory=list)
    remote: list = field(default_factory=list)
    stops: list = field(default_factory=list)

    def lines(self) -> list[str]:
        out = [f"TARGET {self.target}"]
        out += [f"REMOVE {node}" for node in self.tree]
        out += [f"UNLINK {g}:{p} {f} {v}" for g, p, f, v in self.unlinks]
        out += [f"EDIT {g}:{p}:{n} {t}" for g, p, n, t in self.mentions]
        out += [f"REMOTE {g} {r}" for g, r in self.remote]
        out += [f"STOP {s}" for s in self.stops]
        return out


def all_pages(root, graphs):
    pages = []
    for name, graph in graphs.items():
        bundle = links.bundle_dir(root, graph)
        if bundle is None or not bundle.is_dir():
            continue
        for file in okf.bundle_pages(bundle):
            pages.append((name, bundle, file, okf.read_page(file)))
    return pages


def mentions(root, graphs, pages, node_of, tree, files):
    targets = [(node.split(":", 1)[0], node.split(":", 1)[1], files[node]) for node in tree]
    found = []
    for name, bundle, file, page in pages:
        if node_of[file.resolve()] in tree or page.error:
            continue
        text = okf.read_text(file)
        offset = text[: len(text) - len(page.body)].count("\n")
        for number, line in enumerate(okf.strip_links_block(page.body).splitlines(), offset + 1):
            for graph, path, target_file in targets:
                stem = Path(path).stem
                hit = f"{graph}:{path}" in line
                if not hit and ID_RE.match(stem):
                    pattern = (rf"(?<![\w:/-]){re.escape(stem)}(?![\w-])" if name == graph
                               else rf"(?<![\w-]){re.escape(graph)}:{re.escape(stem)}(?![\w-])")
                    hit = re.search(pattern, line) is not None
                if not hit:
                    for link in okf.body_links(file, bundle, line):
                        resolved = links.resolve(root, graphs, name, link, cache_only=True)
                        hit = hit or (resolved.file is not None and resolved.file.resolve() == target_file)
                if hit:
                    found.append((name, okf.bundle_path(bundle, file), number, line.strip()))
    return list(dict.fromkeys(found))


def plan(root, graphs, link, probe_find=None) -> Plan:
    probe_find = probe_find or probe.find
    target = links.resolve(root, graphs, "", link)
    if target.state != links.FOUND:
        raise UsageError(f"{link} does not resolve ({target.state})")
    result = Plan(target.node)
    if graphs[target.graph].remote:
        result.stops.append(f"{target.node} is in a remote graph. Forget it in its own repository.")
        return result
    pages = all_pages(root, graphs)
    cache = {}

    def manifest_of(name):
        if name not in cache:
            bundle = links.bundle_dir(root, graphs[name])
            try:
                cache[name] = manifest.read(bundle) if bundle else None
            except DataError:
                cache[name] = None
        return cache[name]

    node_of = {file.resolve(): f"{name}:{okf.bundle_path(bundle, file)}" for name, bundle, file, _ in pages}
    files = {target.node: target.file.resolve()}
    result.tree.append(target.node)
    refs = []
    index = 0
    while index < len(result.tree):
        target_file = files[result.tree[index]]
        index += 1
        for name, bundle, file, page in pages:
            source = node_of[file.resolve()]
            if source in result.tree or page.error:
                continue
            for name_of_field, value in okf.frontmatter_links(page.frontmatter):
                resolved = links.resolve(root, graphs, name, value, cache_only=True)
                if resolved.file is None or resolved.file.resolve() != target_file:
                    continue
                required = ((manifest_of(name) or {}).get("required_links") or {}).get(page.type) or []
                if name_of_field in required:
                    result.tree.append(source)
                    files[source] = file.resolve()
                    break
                refs.append((name, okf.bundle_path(bundle, file), name_of_field, value))
    result.unlinks = [ref for ref in dict.fromkeys(refs) if f"{ref[0]}:{ref[1]}" not in result.tree]
    result.mentions = mentions(root, graphs, pages, node_of, result.tree, files)
    for node in result.tree:
        if (okf.read_page(files[node]).frontmatter or {}).get("protected") is True:
            result.stops.append(f"{node} is protected. Only a person can remove protected: true.")
    involved = {n.split(":", 1)[0] for n in result.tree} | {u[0] for u in result.unlinks} | {m[0] for m in result.mentions}
    for name in sorted(involved):
        graph = graphs[name]
        if graph.remote:
            result.remote.append((name, graph.repo))
        data = manifest_of(name)
        if data is None:
            entry = {"path": graph.path, **({"repo": graph.repo} if graph.repo else {})}
            owner = f"The owner of {graph.repo} must do this." if graph.remote else "Then run forget again."
            result.stops.append(f"the graph {name} has no manifest.md (registry entry {json.dumps(entry)}). "
                                f"Update the plugin of that brain and run its setup, which writes the manifest. {owner}")
        elif probe_find(data["plugin"], data["save_code"]) is None:
            result.stops.append(f"the plugin {data['plugin']} of the graph {name} is not installed. Install it: {data['install']}")
    return result


def cmd_plan(args) -> int:
    result = plan(args.root, registry.read(args.root), args.link)
    if args.format == "json":
        print(json.dumps(asdict(result), indent=2))
    else:
        print("\n".join(result.lines()))
    return 1 if result.stops else 0


def register(sub) -> None:
    parser = sub.add_parser("forget-plan", help="show what forget removes, and why it stops")
    parser.add_argument("link", help="<graph>:/<path> of the page to forget")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.set_defaults(run=cmd_plan)
