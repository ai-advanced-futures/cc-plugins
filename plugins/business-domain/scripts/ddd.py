#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""ddd.py — the one command of the business-domain plugin.

Each subcommand works on the bundle that `.claude/ddd.json` names, below the
root directory. The root is the current directory; --root changes it. The
script never finds the root from its own file location: it ships inside the
plugin and runs against a different repository.

Exit codes: 0 success, 1 an error in the bundle data, 2 wrong input.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# PEP 723 gives `uv run` the packages. With plain python3 a missing package
# must name itself and exit 2, never raise a traceback.
try:
    import yaml  # noqa: F401
except ImportError:
    print("ERROR: the pyyaml package is missing. Run this script with "
          "`uv run`, or install it: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

from dddlib import DataError, UsageError  # noqa: E402
from dddlib import edit, ids, init_bundle, logbook, regen  # noqa: E402
from dddlib import new_page  # noqa: E402
from dddlib import check as check_mod  # noqa: E402
from dddlib import merge as merge_mod  # noqa: E402
from dddlib.bundle import read  # noqa: E402
from dddlib.config import bundle_dir  # noqa: E402
from dddlib.lock import write_lock  # noqa: E402
from dddlib.schema import plugin_actor  # noqa: E402


def _show(root: Path, paths) -> None:
    for path in paths:
        print(path.relative_to(root).as_posix())


def cmd_init(args) -> int:
    with write_lock(args.root):
        written = init_bundle.init(args.root, args.dir)
    _show(args.root, written)
    if not written:
        print("The bundle exists. init changed nothing.")
    return 0


def cmd_new(args) -> int:
    with write_lock(args.root):
        path = new_page.create(args.root, args.type, args.title,
                               args.description, args.status, args.set)
    _show(args.root, [path])
    return 0


def cmd_upgrade(args) -> int:
    from dddlib import standard
    with write_lock(args.root):
        changes = standard.upgrade(args.root)
    print("\n".join(changes) if changes else "the bundle is on the standard: nothing to change")
    return 0


def cmd_regen(args) -> int:
    if args.check:
        stale = regen.differences(read(args.root))
        for path in stale:
            print(f"STALE: {path.relative_to(args.root).as_posix()}")
        return 1 if stale else 0
    with write_lock(args.root):
        _show(args.root, regen.write(args.root))
    return 0


def cmd_check(args) -> int:
    return check_mod.report(args.root, check_mod.run(args.root), args.strict)


def cmd_merge(args) -> int:
    with write_lock(args.root):
        written = merge_mod.merge(args.root, args.source, args.into, args.by)
    _show(args.root, written)
    return 0


def cmd_resolve(args) -> int:
    _show(args.root, [ids.resolve(read(args.root), args.key)])
    return 0


def cmd_log(args) -> int:
    operation = args.operation.capitalize()
    if operation not in logbook.OPERATIONS:
        raise UsageError(f"the log operation is one of "
                         f"{', '.join(logbook.OPERATIONS)}, not {args.operation!r}")
    with write_lock(args.root):
        log = bundle_dir(args.root) / "log.md"
        when = logbook.now()
        logbook.append(log, logbook.entry(operation, args.text, args.by, when), when)
    _show(args.root, [log])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ddd.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="the repository root (default: the current directory)")
    # --root is also accepted after the subcommand. SUPPRESS keeps the value
    # given before the subcommand when none is given after it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", parents=[common], help="make the bundle")
    p.add_argument("--dir", default=None, help="the bundle directory (default: docs/domain)")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("upgrade", parents=[common], help="bring the bundle to the standard")
    p.set_defaults(func=cmd_upgrade)

    p = sub.add_parser("new", parents=[common], help="write a page with the next ID")
    p.add_argument("type")
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--status", default="draft", choices=["draft", "stable"])
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                   help="a type field or an edge; the value is YAML")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("regen", parents=[common], help="write each generated part")
    p.add_argument("--check", action="store_true",
                   help="report each stale part and write nothing")
    p.set_defaults(func=cmd_regen)

    p = sub.add_parser("check", parents=[common], help="the domain linter")
    p.add_argument("--strict", action="store_true", help="make each warning an error")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("merge", parents=[common], help="merge FROM into INTO")
    p.add_argument("source", metavar="FROM")
    p.add_argument("into", metavar="INTO")
    p.add_argument("--by", default=None, help="the actor, as in human:<login>")
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser("resolve", parents=[common], help="print the path of an ID or alias")
    p.add_argument("key", metavar="ID_OR_ALIAS")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("log", parents=[common], help="add one line to log.md")
    p.add_argument("operation", help="Setup, Apply, or Merge")
    p.add_argument("text")
    p.add_argument("--by", default=None, help="the actor, as in human:<login>")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("set", parents=[common], help="change fields of a page")
    p.add_argument("key", metavar="ID_OR_ALIAS")
    p.add_argument("pairs", nargs="+", metavar="KEY=YAML")
    p.add_argument("--by", default=None)
    p.set_defaults(func=lambda a: (_show(a.root, [edit.set_fields(a.root, a.key, a.pairs, a.by)]), 0)[1])

    for name, remove in (("link", False), ("unlink", True)):
        p = sub.add_parser(name, parents=[common], help=f"{name} a typed edge")
        p.add_argument("key", metavar="ID_OR_ALIAS")
        p.add_argument("field")
        p.add_argument("target")
        p.add_argument("--by", default=None)
        p.set_defaults(func=lambda a, r=remove: (_show(a.root, [edit.link(a.root, a.key, a.field, a.target, a.by, r)]), 0)[1])

    p = sub.add_parser("remove", parents=[common], help="delete a page and retire its ID")
    p.add_argument("key", metavar="ID_OR_ALIAS")
    p.add_argument("--by", default=None)
    p.set_defaults(func=lambda a: (_show(a.root, [edit.remove(a.root, a.key, a.by)]), 0)[1])
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.root = args.root.resolve()
    if getattr(args, "by", "") is None:
        args.by = plugin_actor()
    try:
        return args.func(args)
    except UsageError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except DataError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
