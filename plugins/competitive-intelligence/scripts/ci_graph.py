#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""ci_graph.py: the save code and the brain check of the competitive-intelligence graph.

Every write of the graph goes through this script (standard section 8). Exit 0
on success, 1 on a data error, a failed check, or a stale file, 2 on wrong input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cilib import DataError, UsageError, check, regen, writer  # noqa: E402
from cilib.bundle import DEFAULT_DIR, shown  # noqa: E402
from cilib.issues import report  # noqa: E402


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
    print(f"made {shown(args.root, writer.init(args.root, args.dir, args.by))}")
    return 0


def add_init(parser) -> None:
    parser.add_argument("--dir", default=DEFAULT_DIR)
    parser.add_argument("--by", help="the actor")


def cmd_upgrade(args) -> int:
    changes = writer.upgrade(args.root, args.dir)
    print("\n".join(changes) if changes else "the bundle is on the standard: nothing to change")
    return 0


def add_upgrade(parser) -> None:
    parser.add_argument("--dir", help="the bundle folder (default: the registry entry)")


def cmd_log(args) -> int:
    writer.log(args.root, args.operation, args.text, args.by)
    return 0


def add_log(parser) -> None:
    parser.add_argument("operation", help="Setup, Learn, Ingest, Forget, Upgrade, or Report")
    parser.add_argument("text")
    parser.add_argument("--by", help="the actor")


def cmd_new(args) -> int:
    print(shown(args.root, writer.new(args.root, args.type, args.title, args.description, args.set, args.by)))
    return 0


def add_new(parser) -> None:
    parser.add_argument("type")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=YAML")
    parser.add_argument("--by", help="the actor")


def cmd_set(args) -> int:
    print(shown(args.root, writer.set_fields(args.root, args.key, args.pairs, args.by)))
    return 0


def add_set(parser) -> None:
    parser.add_argument("key", help="an ID, an alias, or a bundle path")
    parser.add_argument("pairs", nargs="+", metavar="KEY=YAML")
    parser.add_argument("--by", help="the actor")


def cmd_body(args) -> int:
    try:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise UsageError(f"cannot read {args.file}: {error}") from error
    print(shown(args.root, writer.body(args.root, args.key, text, args.append, args.by)))
    return 0


def add_body(parser) -> None:
    parser.add_argument("key")
    parser.add_argument("--file", required=True, metavar="PATH", help="the text to write; - reads standard input")
    parser.add_argument("--append", action="store_true", help="add the text after the current text")
    parser.add_argument("--by", help="the actor")


def cmd_link(args) -> int:
    print(shown(args.root, writer.link(args.root, args.key, args.field, args.target, args.by)))
    return 0


def cmd_unlink(args) -> int:
    print(shown(args.root, writer.unlink(args.root, args.key, args.field, args.target, args.by)))
    return 0


def add_link(parser) -> None:
    parser.add_argument("key")
    parser.add_argument("field")
    parser.add_argument("target")
    parser.add_argument("--by", help="the actor")


def cmd_remove(args) -> int:
    print(f"removed {shown(args.root, writer.remove(args.root, args.key, args.by))}")
    return 0


def cmd_verify(args) -> int:
    for path in writer.verify(args.root, args.key, args.by):
        print(shown(args.root, path))
    return 0


def cmd_verify_run(args) -> int:
    for path in writer.verify_run(args.root, args.key, args.by):
        print(shown(args.root, path))
    return 0


def add_verify(parser) -> None:
    parser.add_argument("key", help="an ID, an alias, or a bundle path")
    parser.add_argument("--by", required=True, help="human:<login>, because only a person confirms a page")


def add_verify_run(parser) -> None:
    parser.add_argument("key", help="a Run page: an ID, an alias, a bundle path, or the session id (run_id)")
    parser.add_argument("--by", required=True, help="human:<login>, because only a person confirms a run")


def cmd_resolve(args) -> int:
    print(shown(args.root, writer.resolve_key(args.root, args.key)))
    return 0


def add_key(parser) -> None:
    parser.add_argument("key")
    parser.add_argument("--by", help="the actor")


def cmd_ingest(args) -> int:
    from cilib import ingest

    for line in ingest.run(args.root, args.path, args.result, args.by):
        print(line)
    return 0


def add_ingest(parser) -> None:
    parser.add_argument("path", nargs="?", help="the session folder, or the vendor archetype file")
    parser.add_argument("--result", metavar="FILE", help="the result file of the run")
    parser.add_argument("--by", help="the actor")


def cmd_view(args) -> int:
    from cilib import view

    print(view.show(args.root, args.run, args.file), end="")
    return 0


def add_view(parser) -> None:
    parser.add_argument("run", help="a RUN ID, a session id, or latest")
    parser.add_argument("file", help="the name of a session file, for example competitive-ecosystem.json")


def cmd_results(args) -> int:
    from cilib import read

    selected = [name for name in ("run", "run_id", "latest") if getattr(args, name)]
    if len(selected) != 1:
        raise UsageError("results needs one of --run, --run-id and --latest")
    print(json.dumps(read.results(args.root, args.run, args.run_id, args.latest, args.command, args.case),
                     indent=2, ensure_ascii=False))
    return 0


def add_results(parser) -> None:
    parser.add_argument("--run", metavar="KEY", help="a RUN ID or a session id")
    parser.add_argument("--run-id", metavar="ID", help="the run_id of the result file")
    parser.add_argument("--latest", action="store_true", help="the latest run (add --command to take the latest run of one command)")
    parser.add_argument("--command", metavar="C", help="only a run of this command")
    parser.add_argument("--case", metavar="C", help="only a run of this case")


def cmd_pages(args) -> int:
    from cilib import read

    print(json.dumps(read.pages(args.root, args.type, args.run), indent=2, ensure_ascii=False))
    return 0


def add_pages(parser) -> None:
    parser.add_argument("type")
    parser.add_argument("--run", metavar="KEY", help="only the pages of this run")


COMMANDS = [
    ("init", add_init, cmd_init, "make the bundle, the manifest, the log, and the registry entry"),
    ("upgrade", add_upgrade, cmd_upgrade, "bring an existing bundle to the standard"),
    ("new", add_new, cmd_new, "make a page with the next ID"),
    ("set", add_set, cmd_set, "change fields of a page"),
    ("body", add_body, cmd_body, "write the text of a page above its LINKS block"),
    ("link", add_link, cmd_link, "add a typed link"),
    ("unlink", add_link, cmd_unlink, "remove a typed link"),
    ("remove", add_key, cmd_remove, "delete a page and retire its ID"),
    ("resolve", add_key, cmd_resolve, "print the path of a page"),
    ("verify", add_verify, cmd_verify, "a person confirms a page: status stable and one more verified entry"),
    ("verify-run", add_verify_run, cmd_verify_run, "a person confirms a run: its pages get status stable and a verified entry"),
    ("regen", add_regen, cmd_regen, "write the indexes, the LINKS blocks, and links.tsv"),
    ("check", add_check, cmd_check, "run the brain check of competitive-intelligence"),
    ("log", add_log, cmd_log, "write one log.md entry"),
    ("ingest", add_ingest, cmd_ingest, "write the pages of a run from its session folder and result file"),
    ("view", add_view, cmd_view, "print a session file of a run, built from the pages"),
    ("results", add_results, cmd_results, "print the Result pages of a run as a result file"),
    ("pages", add_pages, cmd_pages, "print the pages of one type as JSON"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ci_graph.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="the project root")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    for name, add, run, help_text in COMMANDS:
        command = sub.add_parser(name, help=help_text)
        add(command)
        command.set_defaults(run_command=run)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.root = args.root.resolve()
    try:
        return args.run_command(args)
    except UsageError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except DataError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
