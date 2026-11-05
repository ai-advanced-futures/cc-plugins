#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""system_design.py: the save code and the brain check of the system-design graph.

Every write of the graph goes through this script (standard section 8). Exit 0
on success, 1 on a data error, a failed check, or a stale file, 2 on wrong input.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdlib import DataError, UsageError, check, migrate, regen, writer  # noqa: E402
from sdlib.bundle import DEFAULT_DIR, shown  # noqa: E402
from sdlib.issues import report  # noqa: E402


def cmd_regen(args) -> int:
    if args.check:
        stale = regen.differences(args.root)
        for path in stale:
            print(f"STALE: {shown(args.root, path)}")
        return 1 if stale else 0
    for path in regen.write(args.root):
        print(f"wrote {shown(args.root, path)}")
    return 0


def add_regen(parser) -> None:
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when a file is stale")


def cmd_check(args) -> int:
    return report(check.run(args.root), strict=args.strict)


def add_check(parser) -> None:
    parser.add_argument("--strict", action="store_true", help="exit 1 on a warning")


def cmd_init(args) -> int:
    print(f"made {shown(args.root, writer.init(args.root, args.dir, args.title, args.by))}")
    return 0


def cmd_log(args) -> int:
    writer.log(args.root, args.operation, args.text, args.by)
    return 0


def add_init(parser) -> None:
    parser.add_argument("--dir", default=DEFAULT_DIR)
    parser.add_argument("--title", default="System design")
    parser.add_argument("--by", help="the actor")


def add_log(parser) -> None:
    parser.add_argument("operation", help="Setup, Learn, Settle, Forget, Upgrade, Migrate, or Report")
    parser.add_argument("text")
    parser.add_argument("--by", help="the actor")


def cmd_new(args) -> int:
    print(shown(args.root, writer.new(args.root, args.type, args.title, args.description, args.set, args.by)))
    return 0


def cmd_set(args) -> int:
    print(shown(args.root, writer.set_fields(args.root, args.key, args.pairs, args.by)))
    return 0


def cmd_link(args) -> int:
    print(shown(args.root, writer.link(args.root, args.key, args.field, args.target, args.with_, args.by)))
    return 0


def cmd_unlink(args) -> int:
    print(shown(args.root, writer.unlink(args.root, args.key, args.field, args.target, args.by)))
    return 0


def cmd_remove(args) -> int:
    print(f"removed {shown(args.root, writer.remove(args.root, args.key, args.by))}")
    return 0


def cmd_resolve(args) -> int:
    print(shown(args.root, writer.resolve_key(args.root, args.key)))
    return 0


def add_new(parser) -> None:
    parser.add_argument("type")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=YAML")
    parser.add_argument("--by", help="the actor")


def add_set(parser) -> None:
    parser.add_argument("key", help="an ID, an alias, an area slug, system, or a bundle path")
    parser.add_argument("pairs", nargs="+", metavar="KEY=YAML")
    parser.add_argument("--by", help="the actor")


def add_link(parser) -> None:
    parser.add_argument("key")
    parser.add_argument("field")
    parser.add_argument("target")
    parser.add_argument("--with", dest="with_", action="append", default=[], metavar="KEY=YAML",
                        help="a field of a mapping link, for example style=sync for uses")
    parser.add_argument("--by", help="the actor")


def add_key(parser) -> None:
    parser.add_argument("key")
    parser.add_argument("--by", help="the actor")


def cmd_upgrade(args) -> int:
    changes = migrate.upgrade(args.root, args.dir)
    print("\n".join(changes) if changes else "the bundle is on the standard: nothing to change")
    return 0


def cmd_migrate(args) -> int:
    for line in migrate.migrate(args.root, args.path, args.by):
        print(line)
    return 0


def add_upgrade(parser) -> None:
    parser.add_argument("--dir", help="the bundle folder (default: the registry entry)")


def add_migrate(parser) -> None:
    parser.add_argument("path", help="the old file, for example docs/product/system-design.md")
    parser.add_argument("--by", help="the actor")


COMMANDS = [
    ("init", add_init, cmd_init, "make the bundle, the manifest, the log, and the registry entry"),
    ("upgrade", add_upgrade, cmd_upgrade, "bring an existing bundle to the standard"),
    ("migrate-file", add_migrate, cmd_migrate, "write one page for each item of the old system-design.md"),
    ("new", add_new, cmd_new, "make a page with the next ID"),
    ("set", add_set, cmd_set, "change fields of a page"),
    ("link", add_link, cmd_link, "add a typed link"),
    ("unlink", add_link, cmd_unlink, "remove a typed link"),
    ("remove", add_key, cmd_remove, "delete a page and retire its ID"),
    ("resolve", add_key, cmd_resolve, "print the path of a page"),
    ("regen", add_regen, cmd_regen, "write the indexes, the LINKS blocks, links.tsv, and the system.md blocks"),
    ("check", add_check, cmd_check, "run the brain check of system-design"),
    ("log", add_log, cmd_log, "write one log.md entry"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="system_design.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="the project root")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, add, run, help_text in COMMANDS:
        command = sub.add_parser(name, help=help_text)
        add(command)
        command.set_defaults(run=run)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.root = args.root.resolve()
    try:
        return args.run(args)
    except UsageError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except DataError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
