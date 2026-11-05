"""Navigation: the neighbors of one page in every graph (spec section 7.3)."""
from __future__ import annotations

import json
from dataclasses import dataclass

from knowledgelib import DataError, links, okf, registry
from knowledgelib.okf import oneline


@dataclass(frozen=True)
class Edge:
    direction: str
    field: str
    node: str
    type: str
    title: str
    description: str
    state: str

    def row(self) -> str:
        return "\t".join([self.direction, self.field, self.node, self.type or "-",
                          self.title or "-", self.description or "-", self.state])


def details(file) -> tuple[str, str, str]:
    if file is None:
        return "", "", ""
    data = okf.read_page(file).frontmatter or {}
    return oneline(data.get("type")), oneline(data.get("title")), oneline(data.get("description"))


def links_out(root, graphs, node, cache_only=False) -> list[Edge]:
    target = links.resolve(root, graphs, "", node, cache_only)
    if target.file is None:
        raise DataError(f"{node} does not resolve ({target.state})")
    page = okf.read_page(target.file)
    bundle = links.bundle_dir(root, graphs[target.graph], cache_only)
    pairs = okf.frontmatter_links(page.frontmatter)
    pairs += [("body", link) for link in okf.body_links(target.file, bundle, page.body)]
    edges, seen = [], set()
    for field, value in pairs:
        found = links.resolve(root, graphs, target.graph, value, cache_only)
        if found.node == target.node or found.node in seen:
            continue
        seen.add(found.node)
        edges.append(Edge("out", field, found.node, *details(found.file), found.state))
    return edges


def graph_pages(root, graphs, name):
    bundle = links.bundle_dir(root, graphs[name], cache_only=True)
    if bundle is None or not bundle.is_dir():
        return []
    return [(okf.bundle_path(bundle, file), file, okf.read_page(file)) for file in okf.bundle_pages(bundle)]


def links_in(root, graphs, node, cache_only=False) -> list[Edge]:
    target = links.resolve(root, graphs, "", node, cache_only)
    edges = []
    for name in graphs:
        for path, file, page in graph_pages(root, graphs, name):
            for field, value in okf.frontmatter_links(page.frontmatter):
                found = links.resolve(root, graphs, name, value, cache_only=True)
                if found.node != target.node and not (found.file and target.file and found.file == target.file):
                    continue
                edges.append(Edge("in", field, f"{name}:{path}", *details(file), "found"))
    return edges


def neighbors(root, graphs, node, cache_only=False) -> list[Edge]:
    return links_out(root, graphs, node, cache_only) + links_in(root, graphs, node, cache_only)


def cmd_neighbors(args) -> int:
    for edge in neighbors(args.root, registry.read(args.root), args.node, args.cache_only):
        print(edge.row())
    return 0


def cmd_pages(args) -> int:
    graphs = registry.read(args.root)
    registry.require(graphs, args.graph)
    out = []
    for path, _file, page in graph_pages(args.root, graphs, args.graph):
        data = page.frontmatter or {}
        if args.type and data.get("type") != args.type:
            continue
        out.append({"path": path, "type": data.get("type"), "title": data.get("title"),
                    "description": data.get("description"), "frontmatter": data})
    print(json.dumps(out, indent=2, default=str))
    return 0


def register(sub) -> None:
    parser = sub.add_parser("neighbors", help="list the neighbors of one page")
    parser.add_argument("node", help="<graph>:/<path>")
    parser.add_argument("--cache-only", action="store_true")
    parser.set_defaults(run=cmd_neighbors)
    pages = sub.add_parser("pages", help="list the pages of one graph as JSON")
    pages.add_argument("graph")
    pages.add_argument("--type")
    pages.set_defaults(run=cmd_pages)
