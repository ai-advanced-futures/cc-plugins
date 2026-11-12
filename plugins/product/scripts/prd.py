#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""prd.py — the one command of the product plugin.

Every subcommand works on docs/product/ below the root directory. The root is
the current directory; --root changes it. The script never finds the root from
its own file location: it ships inside the plugin and runs against a different
repository. The only path it takes from its own location is its own shipped
schema file.
"""
import argparse
import functools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# PEP 723 gives `uv run` the packages. With plain python3 a missing package must
# name itself and exit 2, never raise a traceback that a skill cannot read.
# jsonschema is not probed here: prdlib.schema imports it when a subcommand
# validates, and raises the same message as a UsageError, which also exits 2.
try:
    import yaml  # noqa: F401
except ImportError:
    print(
        "ERROR: the pyyaml package is missing. Run this script with "
        "`uv run`, or install it: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(2)

from prdlib import DataError, UsageError  # noqa: E402
from prdlib import check as check_mod  # noqa: E402
from prdlib import claims  # noqa: E402
from prdlib import drift as drift_mod  # noqa: E402
from prdlib import edit  # noqa: E402
from prdlib import ids  # noqa: E402
from prdlib import init_bundle  # noqa: E402
from prdlib import listing  # noqa: E402
from prdlib import migrate_blocks  # noqa: E402
from prdlib import migrate_build  # noqa: E402
from prdlib import migrate_finish  # noqa: E402
from prdlib import migrate_map  # noqa: E402
from prdlib import migrate_scan  # noqa: E402
from prdlib import new_page  # noqa: E402
from prdlib import page as page_mod  # noqa: E402
from prdlib import readycmd  # noqa: E402
from prdlib import regen as regen_mod  # noqa: E402
from prdlib import registry  # noqa: E402
from prdlib import runs as runs_mod  # noqa: E402
from prdlib import stage as stage_mod  # noqa: E402
from prdlib import statecmd  # noqa: E402
from prdlib import tree  # noqa: E402
from prdlib.graph import own_target  # noqa: E402
from prdlib.hashing import body_hash  # noqa: E402
from prdlib.textsafe import escape_controls  # noqa: E402


def _shown(path: Path, root: Path) -> str:
    """The path of a page for a line of output, below the root. A file name
    can hold a line break or an ESC, so each control character is escaped."""
    return escape_controls(path.relative_to(root))


def needs_bundles(fn):
    """Every subcommand except `init` exits 2 when the bundles are absent."""

    @functools.wraps(fn)
    def wrapper(args):
        tree.require_bundles(args.root)
        return fn(args)

    return wrapper


@needs_bundles
def cmd_check(args) -> int:
    bundles = tree.BUNDLES if args.bundle == "all" else (args.bundle,)
    return check_mod.report(check_mod.run(args.root, bundles),
                            args.strict, args.format)


@needs_bundles
def cmd_list(args) -> int:
    for line in listing.rows(args.root, args.type, args.where, args.fields):
        print(line)
    return 0


@needs_bundles
def cmd_stage(args) -> int:
    for line in stage_mod.rows(args.root, args.ids):
        print(line)
    return 0


@needs_bundles
def cmd_hash(args) -> int:
    for identifier in args.ids:
        path = ids.resolve(args.root, identifier)
        print(f"{escape_controls(path.stem)} "
              f"{body_hash(page_mod.load_page(path).body, path.stem)}")
    return 0


@needs_bundles
def cmd_resolve(args) -> int:
    print(_shown(ids.resolve(args.root, args.id), args.root))
    return 0


@needs_bundles
def cmd_new(args) -> int:
    links = list(args.link)
    if args.discovered_from:
        # The protocol gives an ID. The page stores a bundle-relative path.
        source = ids.resolve(args.root, args.discovered_from)
        links.append(f"discovered_from={own_target(args.root, source)}")
    notes: list[str] = []
    path = new_page.create(
        args.root, args.type, args.title, args.description,
        status=args.status, body=args.body, traces=args.traces,
        links=links, sets=args.set, notes=notes)
    print(path.relative_to(args.root))
    # stdout holds the path only: each skill reads the path from it.
    for note in notes:
        print(f"note: {path.stem}: {note}", file=sys.stderr)
    return 0


@needs_bundles
def cmd_set(args) -> int:
    print(_shown(edit.set_fields(args.root, args.key, args.pairs, args.actor),
                 args.root))
    return 0


@needs_bundles
def cmd_link(args) -> int:
    path = edit.link(args.root, args.key, args.field, args.target, args.actor,
                     remove=args.subcommand == "unlink")
    print(_shown(path, args.root))
    return 0


@needs_bundles
def cmd_remove(args) -> int:
    print("removed " + _shown(edit.remove(args.root, args.key, args.actor),
                              args.root))
    return 0


@needs_bundles
def cmd_log(args) -> int:
    edit.log(args.root, args.operation, args.text, args.bundle, args.actor)
    return 0


@needs_bundles
def cmd_regen(args) -> int:
    if args.check:
        # One walk of the tree: require_readable wants the broken pages and
        # differences wants the readable ones, and read_tree gives both.
        pages, broken = regen_mod.read_tree(args.root)
        regen_mod.require_readable(args.root, broken)
        found = regen_mod.differences(args.root, pages)
        for path in sorted(found):
            print(f"STALE: {_shown(path, args.root)}")
        return 1 if found else 0
    for path in regen_mod.write(args.root):
        print(_shown(path, args.root))
    return 0


@needs_bundles
def cmd_drift(args) -> int:
    if args.accept:
        if not args.actor:
            raise UsageError("--accept needs --actor human:<login>")
        item, target = args.accept
        path = drift_mod.accept(args.root, item, target, args.actor)
        print(_shown(path, args.root))
        return 0
    if args.show:
        # Text for a person. It is not a verdict, so it exits 0.
        for line in drift_mod.show(args.root, *args.show):
            print(line)
        return 0
    if not args.all and not args.ids:
        raise UsageError("give --all, --ids <ID>..., --show <ITEM> <TARGET>, "
                         "or --accept <ITEM> <TARGET>")
    found = drift_mod.scan(args.root, args.ids)
    for path, target in found:
        print(f"{escape_controls(path.stem)}\t{escape_controls(target)}")
    if args.write:
        drift_mod.write_flags(args.root, found)
    # The exit code is the verdict, so a skill never parses this stdout.
    return 1 if found else 0


@needs_bundles
def cmd_claim(args) -> int:
    # One line for each path, in the shape of cmd_expire: one spec covers one
    # Story or more, and the caller reads the lines it got.
    for path in claims.claim(args.root, args.id, args.actor, args.lease):
        print(_shown(path, args.root))
    return 0


@needs_bundles
def cmd_heartbeat(args) -> int:
    print(_shown(claims.heartbeat(args.root, args.id, args.actor, args.lease),
                 args.root))
    return 0


@needs_bundles
def cmd_release(args) -> int:
    print(_shown(claims.release(args.root, args.id, args.actor), args.root))
    return 0


@needs_bundles
def cmd_expire(args) -> int:
    for path in claims.expire(args.root, args.actor):
        print(_shown(path, args.root))
    return 0


@needs_bundles
def cmd_ready(args) -> int:
    for row in readycmd.rows(args.root, args.milestone, args.type):
        print(row)
    return 0


@needs_bundles
def cmd_run_checks(args) -> int:
    path, outcome, failures = runs_mod.run_checks(
        args.root, args.id, args.actor, args.spec, args.pr)
    print(path.relative_to(args.root))
    for failure in failures:
        print(failure, file=sys.stderr)
    # The exit code is the verdict. The work skill reads it, not this text.
    return 1 if outcome == runs_mod.FAILED else 0


@needs_bundles
def cmd_github(args) -> int:
    """The three legs of the round trip. `--snapshot` reads a recorded file,
    so the command calls no GitHub API and a person can replay a plan."""
    from prdlib import gh, ghapply, ghplan, ghpull, ghsnapshot
    if (args.github_command == "apply" and args.snapshot
            and not args.dry_run):
        # A recorded snapshot can be old, and a push planned from it can make
        # a second issue for a page that GitHub already holds.
        raise UsageError(
            "`github apply --snapshot` needs --dry-run. A snapshot is a "
            "recorded read, so apply reads GitHub itself before it pushes. "
            "Run `github apply` with no --snapshot.")
    context = None
    if args.snapshot:
        snapshot = ghsnapshot.load(args.snapshot)
        client = None
    else:
        client = gh.Gh()
        context = gh.preconditions(args.root, client)
        snapshot = ghsnapshot.fetch(client, context)
    if args.github_command == "pull":
        report = ghpull.pull(args.root, snapshot,
                             login=(context.login if context
                                    else snapshot.get("login", "unknown")),
                             adopt=args.adopt)
        print(ghpull.render(report, args.format))
        return 0
    plan = ghplan.build(args.root, snapshot, keep=args.keep or ())
    if args.github_command == "plan":
        print(ghplan.render(plan, args.format))
        return 1 if plan.blocked else 0
    if args.github_command == "apply":
        if plan.blocked:
            print(ghplan.render(plan, args.format))
            return 1
        if args.dry_run:
            print(ghplan.render(plan, args.format, prefix="would "))
            return 0
        for line in ghapply.apply(args.root, snapshot, plan, client):
            print(line)
        for line in plan.conflicts:
            print(f"CONFLICT: {line}")
    return 0


@needs_bundles
def cmd_state(args) -> int:
    print(statecmd.change(args.root, args.id, args.state, args.actor,
                          approved_by=args.approved_by))
    return 0


def cmd_migrate(args) -> int:
    """The four modes carry their own preconditions: --scan, --dry-run, and
    the main run need the bundles to be absent; --finish needs them to be
    there, because it runs after the tree moves."""
    if args.finish:
        tree.require_bundles(args.root)
        return migrate_finish.finish(args.root)
    tree.require_no_bundles(args.root)
    mapping = migrate_map.load_map(args.map) if args.map else None
    report = migrate_scan.scan(args.root, mapping, args.hash_recipe)
    if args.scan:
        for line in report.lines:
            print(line)
        print(report.verdict())
        return report.exit_code()
    return migrate_build.run(args.root, report, mapping,
                             dry_run=args.dry_run,
                             accept_unmarked=args.accept_unmarked_drift)


def cmd_init(args) -> int:
    """The one subcommand that does not need the bundles to exist."""
    for path in init_bundle.init(args.root, args.title, args.description):
        print(path.relative_to(args.root))
    return 0


def cmd_upgrade(args) -> int:
    from prdlib import standard
    tree.require_bundles(args.root)
    changes = standard.upgrade(args.root)
    print("\n".join(changes) if changes else "the bundles are on the standard: nothing to change")
    return 0


def _add(sub, name, run, **kwargs):
    """One parser, with the function that runs it. The name and the handler
    are written in one place, so a subcommand cannot reach argparse without
    a handler behind it."""
    parser = sub.add_parser(name, **kwargs)
    parser.set_defaults(run=run)
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prd.py")
    parser.add_argument("--root", default=".", type=Path,
                        help="the repository that holds docs/product/")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    check_parser = _add(sub, "check", run=cmd_check,
                   help="OKF, schema, and graph rules")
    check_parser.add_argument("--bundle", choices=["prd", "roadmap", "all"],
                              default="all")
    check_parser.add_argument("--strict", action="store_true",
                              help="a warning is an error")
    check_parser.add_argument("--format", choices=["text", "json"],
                              default="text")
    hash_parser = _add(sub, "hash", run=cmd_hash,
                  help="print the body hash of a page")
    hash_parser.add_argument("ids", nargs="+")
    resolve_parser = _add(sub, "resolve", run=cmd_resolve,
                     help="print the path of an ID or alias")
    resolve_parser.add_argument("id")
    init_parser = _add(sub, "init", run=cmd_init,
                  help="write the two empty bundles")
    init_parser.add_argument("--title")
    init_parser.add_argument("--description")
    _add(sub, "upgrade", run=cmd_upgrade,
         help="bring the bundles to the brain standard")
    new_parser = _add(sub, "new", run=cmd_new,
                 help="write one page with the next ID")
    new_parser.add_argument("type", metavar="TYPE",
                            choices=sorted(registry.TYPES))
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--description", required=True)
    new_parser.add_argument("--status")
    new_parser.add_argument("--body")
    new_parser.add_argument("--traces", action="append", default=[])
    new_parser.add_argument("--link", action="append", default=[],
                            metavar="FIELD=TARGET",
                            help="a relationship. TARGET is a bundle-relative "
                                 "path that starts with /, such as "
                                 "/needs/NEED-01.md. A target in the other "
                                 "bundle starts with prd:/, such as "
                                 "prd:/capabilities/CAPABILITY-01.md.")
    new_parser.add_argument("--discovered-from", metavar="ID",
                            help="the work item this one came out of")
    new_parser.add_argument("--set", action="append", default=[],
                            metavar="FIELD=YAML")
    set_parser = _add(sub, "set", run=cmd_set,
                 help="change fields of a page")
    set_parser.add_argument("key")
    set_parser.add_argument("pairs", nargs="+", metavar="FIELD=YAML")
    set_parser.add_argument("--actor")
    for name in ("link", "unlink"):
        link_parser = _add(sub, name, run=cmd_link, help=f"{name} a typed link")
        link_parser.add_argument("key")
        link_parser.add_argument("field")
        link_parser.add_argument("target")
        link_parser.add_argument("--actor")
    remove_parser = _add(sub, "remove", run=cmd_remove,
                    help="delete a page and retire its ID")
    remove_parser.add_argument("key")
    remove_parser.add_argument("--actor")
    log_parser = _add(sub, "log", run=cmd_log, help="write one log.md entry")
    log_parser.add_argument("operation", choices=["Learn", "Forget", "Upgrade", "Report"])
    log_parser.add_argument("text")
    log_parser.add_argument("--bundle", choices=["prd", "roadmap"], default="prd")
    log_parser.add_argument("--actor")
    list_parser = _add(sub, "list", run=cmd_list,
                  help="one line for each page of a type")
    list_parser.add_argument("type", metavar="TYPE",
                             choices=sorted(registry.TYPES))
    list_parser.add_argument("--where", action="append", default=[],
                             metavar="KEY=VALUE")
    list_parser.add_argument("--fields", default="title")
    stage_parser = _add(sub, "stage", run=cmd_stage,
                        help="early or mature for each capability: mature "
                             "when a done or released work item traces to it")
    stage_parser.add_argument("ids", nargs="*", metavar="ID",
                              help="a capability ID or alias. None means "
                                   "every capability")
    regen_parser = _add(sub, "regen", run=cmd_regen,
                   help="write every generated block")
    regen_parser.add_argument("--check", action="store_true",
                              help="write nothing and name the stale files")
    drift_parser = _add(sub, "drift", run=cmd_drift,
                   help="check the stored trace hashes")
    drift_parser.add_argument("--all", action="store_true")
    drift_parser.add_argument("--ids", nargs="+", default=[])
    drift_parser.add_argument("--write", action="store_true",
                              help="add each drifted target to `drifted`")
    drift_parser.add_argument("--accept", nargs=2, metavar=("ITEM", "TARGET"))
    drift_parser.add_argument("--show", nargs=2, metavar=("ITEM", "TARGET"),
                              help="the text of the target at the last "
                                   "accept, from Git, and a diff to now")
    drift_parser.add_argument("--actor")
    migrate_parser = _add(sub, "migrate", run=cmd_migrate,
                     help="the v3 files to the bundles")
    mode = migrate_parser.add_mutually_exclusive_group()
    mode.add_argument("--scan", action="store_true",
                      help="report and write nothing")
    mode.add_argument("--dry-run", action="store_true",
                      help="build the tree and delete it")
    mode.add_argument("--finish", action="store_true",
                      help="store the hashes after the skill step")
    migrate_parser.add_argument("--map", type=Path, metavar="FILE")
    migrate_parser.add_argument("--hash-recipe",
                                choices=list(migrate_blocks.RECIPES))
    migrate_parser.add_argument("--accept-unmarked-drift", action="store_true")
    state_parser = _add(sub, "state", run=cmd_state,
                   help="the one write path for state")
    state_parser.add_argument("id")
    state_parser.add_argument("state", choices=list(registry.STATES))
    state_parser.add_argument("--actor", required=True)
    state_parser.add_argument(
        "--approved-by",
        help="the approval of an agent change: a PR URL or #<n>, a D-id, "
             "an ANSWER id, a hitl card link, or another URL")
    claim_parser = _add(sub, "claim", run=cmd_claim,
                   help="take one ready work item, or every Story of one spec; all or none")
    claim_parser.add_argument("id", nargs="+",
                              help="one ID, or every ID of one spec")
    claim_parser.add_argument("--actor", required=True)
    claim_parser.add_argument("--lease", default=claims.DEFAULT_LEASE,
                              help="45s, 30m, or 2h. The default is 30m.")
    beat_parser = _add(sub, "heartbeat", run=cmd_heartbeat,
                                 help="move the lease of a claim forward")
    beat_parser.add_argument("id")
    beat_parser.add_argument("--actor", required=True)
    beat_parser.add_argument("--lease", default=claims.DEFAULT_LEASE,
                             help="45s, 30m, or 2h. The default is 30m.")
    release_parser = _add(sub, "release", run=cmd_release,
                     help="give one claimed item back")
    release_parser.add_argument("id")
    release_parser.add_argument("--actor", required=True)
    expire_parser = _add(sub, "expire", run=cmd_expire,
                    help="release each lease that is over")
    expire_parser.add_argument("--actor", required=True)
    ready_parser = _add(sub, "ready", run=cmd_ready,
                   help="the work an agent may take")
    ready_parser.add_argument("--milestone", metavar="ID")
    ready_parser.add_argument("--type", metavar="TYPE",
                              choices=list(registry.WORK_ITEMS))
    checks_parser = _add(
        sub, "run-checks", run=cmd_run_checks,
        help="run the declared checks and write one Run")
    checks_parser.add_argument("id")
    checks_parser.add_argument("--actor", required=True)
    checks_parser.add_argument("--spec", help="the spec the work follows")
    checks_parser.add_argument("--pr", help="the pull request URL")
    # The two shared flags go on a parent parser, and each leg takes it. A
    # flag on the `github` parser itself parses only before the leg name, and
    # every skill line and every test writes it after.
    github_common = argparse.ArgumentParser(add_help=False)
    github_common.add_argument("--snapshot", type=Path,
                               help="a recorded snapshot file. With it the "
                                    "command calls no GitHub API.")
    github_common.add_argument("--format", choices=["text", "json"],
                               default="text")
    github_parser = _add(sub, "github", run=cmd_github,
                         help="the GitHub round trip")
    github_sub = github_parser.add_subparsers(dest="github_command",
                                              required=True)
    # A page did not change, so its hash matches and the plan sends nothing
    # for it. --keep sends its values over the edit a person made in GitHub.
    keep_common = argparse.ArgumentParser(add_help=False)
    keep_common.add_argument("--keep", action="append", metavar="ID",
                             help="send the bundle values of this page over "
                                  "an edit in GitHub. Give it once for each "
                                  "page.")
    github_sub.add_parser("plan", parents=[github_common, keep_common],
                          help="print the change set, write nothing")
    apply_parser = github_sub.add_parser(
        "apply", parents=[github_common, keep_common],
        help="execute the change set")
    apply_parser.add_argument("--dry-run", action="store_true",
                              help="print each change and call nothing")
    pull_parser = github_sub.add_parser("pull", parents=[github_common],
                                        help="read GitHub back")
    pull_parser.add_argument("--adopt", action="store_true",
                             help="make a page for an issue on the "
                                  "Project that has none")
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
