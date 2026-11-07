#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""knowledge_graph.py: the save code of the generic graph (standard section 8).

Every write of the knowledge graph goes through this script. Exit 0 on
success, 1 on a graph data error, a stale file, or a file that cannot be read or written after 5 tries
(okf.short_lock), 2 on wrong input.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledgelib import DataError, FileError, UsageError, changes, graph_check, graph_ops, graph_regen, graph_upgrade, rootpath  # noqa: E402
from knowledgelib.graph import DEFAULT_DIR  # noqa: E402
from knowledgelib.issues import report  # noqa: E402
from knowledgelib.okf import shown  # noqa: E402


def cmd_regen(args) -> int:
    if args.check:
        stale = graph_regen.differences(args.root)
        for path in stale:
            print(f"STALE: {shown(args.root, path)}")
        return 1 if stale else 0
    for path in graph_ops.regen(args.root):
        print(f"wrote {shown(args.root, path)}")
    return 0


def add_regen(parser) -> None:
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when a file is stale")


def cmd_init(args) -> int:
    bundle = graph_ops.init(args.root, args.dir, args.by)
    print(f"made {shown(args.root, bundle)}")
    return 0


def cmd_new(args) -> int:
    print(shown(args.root, graph_ops.new(args.root, args.type, args.title, args.description, args.set, args.by,
                                         args.slug)))
    return 0


def cmd_set(args) -> int:
    print(shown(args.root, graph_ops.set_fields(args.root, args.key, args.pairs, args.by)))
    return 0


def cmd_body(args) -> int:
    try:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise UsageError(f"cannot read {args.file}: {error}") from error
    print(shown(args.root, graph_ops.body(args.root, args.key, text, args.append, args.by)))
    return 0


def cmd_link(args) -> int:
    print(shown(args.root, graph_ops.link(args.root, args.key, args.field, args.target, args.by)))
    return 0


def cmd_unlink(args) -> int:
    print(shown(args.root, graph_ops.unlink(args.root, args.key, args.field, args.target, args.by)))
    return 0


def cmd_remove(args) -> int:
    print(f"removed {shown(args.root, graph_ops.remove(args.root, args.key, args.by))}")
    return 0


def cmd_resolve(args) -> int:
    print(shown(args.root, graph_ops.resolve(args.root, args.key)))
    return 0


def cmd_log(args) -> int:
    graph_ops.log(args.root, args.operation, args.text, args.by)
    return 0


def add_init(parser):
    parser.add_argument("--dir", default=DEFAULT_DIR, help="the bundle folder")
    parser.add_argument("--by", help="the actor")


def add_new(parser):
    parser.add_argument("type")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=YAML")
    parser.add_argument("--slug", help="the slug of the page, instead of one made from the title")
    parser.add_argument("--by", help="the actor")


def add_set(parser):
    parser.add_argument("key", help="a slug, an alias, or a bundle path")
    parser.add_argument("pairs", nargs="+", metavar="KEY=YAML")
    parser.add_argument("--by", help="the actor")


def add_body(parser):
    parser.add_argument("key", help="a slug, an alias, or a bundle path")
    parser.add_argument("--file", required=True, metavar="PATH", help="the text to write; - reads standard input")
    parser.add_argument("--append", action="store_true", help="add the text after the current text")
    parser.add_argument("--by", help="the actor")


def add_link(parser):
    parser.add_argument("key")
    parser.add_argument("field")
    parser.add_argument("target")
    parser.add_argument("--by", help="the actor")


def add_key(parser):
    parser.add_argument("key")
    parser.add_argument("--by", help="the actor")


def add_log(parser):
    parser.add_argument("operation", help="Setup, Learn, Forget, Upgrade, or Report")
    parser.add_argument("text")
    parser.add_argument("--by", help="the actor")


def cmd_check(args) -> int:
    return report(graph_check.run(args.root), strict=args.strict)


def add_check(parser):
    parser.add_argument("--strict", action="store_true", help="exit 1 on a warning")


def cmd_upgrade(args) -> int:
    changes = graph_upgrade.upgrade(args.root, args.dir)
    for change in changes:
        print(change)
    if not changes:
        print("the bundle is on the standard: nothing to change")
    return 0


def add_upgrade(parser):
    parser.add_argument("--dir", help="the bundle folder (default: the registry, then .claude/wiki.json)")


def cmd_move(args) -> int:
    print(shown(args.root, graph_ops.move(args.root, args.to, args.by)))
    return 0


def add_move(parser):
    parser.add_argument("--to", required=True, metavar="CONTAINER", help="the new container, for example docs/knowledge/")
    parser.add_argument("--by", help="the actor")


COMMANDS = [
    ("init", add_init, cmd_init, "make a new bundle with the manifest, the log, and the registry entry"),
    ("upgrade", add_upgrade, cmd_upgrade, "bring an existing bundle to the standard"),
    ("move", add_move, cmd_move, "move the container of the graph (AGENTS.md, raw, bundle) to a new folder"),
    ("new", add_new, cmd_new, "make a page with valid frontmatter"),
    ("set", add_set, cmd_set, "change fields of a page"),
    ("body", add_body, cmd_body, "write the text of a page above its LINKS block"),
    ("link", add_link, cmd_link, "add a typed link"),
    ("unlink", add_link, cmd_unlink, "remove a typed link"),
    ("remove", add_key, cmd_remove, "delete a page and retire its slug"),
    ("resolve", add_key, cmd_resolve, "print the path of a page"),
    ("regen", add_regen, cmd_regen, "write the indexes, the LINKS blocks, and links.tsv"),
    ("check", add_check, cmd_check, "run the brain check of the generic graph"),
    ("log", add_log, cmd_log, "write one log.md entry"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knowledge_graph.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=str(Path.cwd()), help="the project root")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, add, run, help_text in COMMANDS:
        command = sub.add_parser(name, help=help_text)
        add(command)
        command.set_defaults(run=run)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.root = rootpath.resolve(args.root)
    try:
        return args.run(args)
    except UsageError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except (DataError, FileError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        changes.flush(args.root)


if __name__ == "__main__":
    sys.exit(main())
