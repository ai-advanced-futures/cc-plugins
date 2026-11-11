#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""ux_graph.py: the save code and the brain check of the ux-hci-design graph.

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

from uxlib import DataError, UsageError, check, regen, writer  # noqa: E402
from uxlib.bundle import DEFAULT_DIR, shown  # noqa: E402
from uxlib.issues import report  # noqa: E402


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
    print(f"made {shown(args.root, writer.init(args.root, args.dir, args.by, args.git == 'yes'))}")
    if args.git == "no":
        print(f"The UX brain is in {args.dir}/, and git does not keep it. Run /ux-hci-design:setup to change this.")
    return 0


def add_init(parser) -> None:
    parser.add_argument("--dir", default=DEFAULT_DIR)
    parser.add_argument("--git", choices=("yes", "no"), default="yes",
                        help="no: the registry entry gets git false, and git keeps the folder out of this clone")
    parser.add_argument("--by", help="the actor")


def cmd_upgrade(args) -> int:
    changes = writer.upgrade(args.root, args.dir, None if args.git is None else args.git == "yes")
    print("\n".join(changes) if changes else "the bundle is on the standard: nothing to change")
    return 0


def add_upgrade(parser) -> None:
    parser.add_argument("--dir", help="the bundle folder (default: the registry entry)")
    parser.add_argument("--git", choices=("yes", "no"), default=None,
                        help="the git answer; without it the answer of the registry entry stays")


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
    parser.add_argument("key", help="a Run page: an ID, an alias, or a bundle path")
    parser.add_argument("--by", required=True, help="human:<login>, because only a person confirms a run")


def cmd_resolve(args) -> int:
    print(shown(args.root, writer.resolve_key(args.root, args.key)))
    return 0


def add_key(parser) -> None:
    parser.add_argument("key")
    parser.add_argument("--by", help="the actor")


def cmd_ingest(args) -> int:
    from uxlib import ingest

    for line in ingest.run(args.root, args.output_dir, args.phase, args.by, args.new_run):
        print(line)
    return 0


def add_ingest(parser) -> None:
    parser.add_argument("output_dir", help="the output folder of the run, for example .ux-artifacts")
    parser.add_argument("--phase", required=True, choices=("empathize", "define", "ideate", "prototype", "test"))
    parser.add_argument("--by", help="the actor")
    parser.add_argument("--new-run", action="store_true",
                        help="start a new Run page, also when pages.json names a run that is a draft")


def cmd_remove_questions(args) -> int:
    from uxlib import questions

    print(questions.remove(args.root, args.output_dir, args.reviewer))
    return 0


def add_remove_questions(parser) -> None:
    from uxlib.questions import REVIEWERS

    parser.add_argument("output_dir", help="the output folder of the run, for example .ux-artifacts")
    parser.add_argument("--reviewer", choices=REVIEWERS,
                        help="remove the file of this reviewer, in <output_dir>/reviews/<reviewer>/")


def cmd_view(args) -> int:
    from uxlib import view

    print(view.show(args.root, args.run, args.file, args.out), end="")
    return 0


def add_view(parser) -> None:
    parser.add_argument("run", help="a RUN ID, an alias, or latest (the latest run that holds the file)")
    parser.add_argument("file", help="the name of an output file, for example evaluation_report.json")
    parser.add_argument("--out", metavar="PATH", help="write the text to this file under <output folder of the run>/inputs/")


def cmd_pages(args) -> int:
    from uxlib import read

    print(json.dumps(read.pages(args.root, args.type, args.run), indent=2, ensure_ascii=False))
    return 0


def add_pages(parser) -> None:
    parser.add_argument("type")
    parser.add_argument("--run", metavar="KEY", help="only the pages of this run")


def cmd_behavior(args) -> int:
    from uxlib import read

    print(json.dumps(read.behavior(args.root, args.run), indent=2, ensure_ascii=False))
    return 0


def add_behavior(parser) -> None:
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
    ("check", add_check, cmd_check, "run the brain check of ux-hci-design"),
    ("log", add_log, cmd_log, "write one log.md entry"),
    ("ingest", add_ingest, cmd_ingest, "write the pages of one phase of a run from its output files"),
    ("remove-questions", add_remove_questions, cmd_remove_questions,
     "remove the open-questions.md file of an agent before the skill starts it again"),
    ("view", add_view, cmd_view, "print an output file of a run, built from the pages"),
    ("pages", add_pages, cmd_pages, "print the pages of one type as JSON"),
    ("behavior", add_behavior, cmd_behavior, "print the behavior results as a JSON list for the PRD"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ux_graph.py", description=__doc__.split("\n\n")[0])
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
