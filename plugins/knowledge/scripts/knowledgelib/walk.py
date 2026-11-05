"""The walk state of one ask run (D24): the waiting nodes, the done nodes, and the facts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from knowledgelib import UsageError, navigate, registry


def _load(path) -> dict:
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read the walk state {path}: {error}") from error


def _save(path, state) -> None:
    Path(path).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def start(path, question, nodes) -> None:
    if Path(path).exists():
        raise UsageError(f"the walk state {path} exists. Use another file, or delete it.")
    _save(path, {"question": question, "waiting": list(dict.fromkeys(nodes)), "done": [], "facts": []})


def next_node(path) -> str | None:
    state = _load(path)
    if not state["waiting"]:
        return None
    node = state["waiting"].pop(0)
    state["done"].append(node)
    _save(path, state)
    return node


def candidates(root, graphs, path, node, cache_only=False):
    state = _load(path)
    seen = set(state["waiting"]) | set(state["done"])
    out = []
    for edge in navigate.neighbors(root, graphs, node, cache_only):
        if edge.state == "found" and edge.node not in seen:
            seen.add(edge.node)
            out.append(edge)
    return out


def keep(path, nodes) -> list[str]:
    state = _load(path)
    added = []
    for node in nodes:
        if node not in state["waiting"] and node not in state["done"]:
            state["waiting"].append(node)
            added.append(node)
    _save(path, state)
    return added


def add_fact(path, node, text) -> None:
    state = _load(path)
    state["facts"].append({"node": node, "text": " ".join(text.split())})
    _save(path, state)


def show(path) -> dict:
    return _load(path)


def cmd_walk(args) -> int:
    if args.walk_command == "start":
        start(args.state, args.question, args.nodes)
    elif args.walk_command == "next":
        node = next_node(args.state)
        if node is None:
            print("no node is waiting", file=sys.stderr)
            return 1
        print(node)
    elif args.walk_command == "candidates":
        for edge in candidates(args.root, registry.read(args.root), args.state, args.node, args.cache_only):
            print(edge.row())
    elif args.walk_command == "keep":
        keep(args.state, args.nodes)
    elif args.walk_command == "fact":
        add_fact(args.state, args.node, args.text)
    else:
        print(json.dumps(show(args.state), indent=2))
    return 0


def register(sub) -> None:
    parser = sub.add_parser("walk", help="the walk state of an ask run")
    wsub = parser.add_subparsers(dest="walk_command", required=True)
    for name in ("start", "next", "candidates", "keep", "fact", "show"):
        command = wsub.add_parser(name)
        command.add_argument("--state", required=True, help="the walk state file")
        if name == "start":
            command.add_argument("--question", required=True)
            command.add_argument("nodes", nargs="+")
        elif name == "keep":
            command.add_argument("nodes", nargs="+")
        elif name in ("candidates", "fact"):
            command.add_argument("node")
            if name == "fact":
                command.add_argument("text")
            else:
                command.add_argument("--cache-only", action="store_true")
        command.set_defaults(run=cmd_walk)
