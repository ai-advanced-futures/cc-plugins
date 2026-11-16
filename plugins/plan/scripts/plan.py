#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///
"""Plan: explicit Beads workspaces with Product-compatible planning rules."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

from planlib import PlanError, model
from planlib.beads import BeadsError
from planlib.migration import apply as import_snapshot, preview
from planlib.service import Service
from planlib.sources import PRD, _json_value, snapshot
from planlib.workspace import Workspace


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--workspace", type=Path, default=os.environ.get("PLAN_WORKSPACE"), help="explicit profile path; no cwd store discovery")
    root.add_argument("--bd", default=os.environ.get("PLAN_BD", "bd"), help="Beads executable")
    root.add_argument("--actor", default=os.environ.get("PLAN_ACTOR"), help="human:<name> or agent:<id>")
    root.add_argument("--json", action="store_true", help="emit compact JSON (all output is structured)")
    root.add_argument("--version", action="version", version="plan 0.2.0")
    commands = root.add_subparsers(dest="command", required=True)

    def command(name, help_text, mutation=False):
        result = commands.add_parser(name, help=help_text)
        for flag, extra in (("--workspace", {"type": Path}), ("--bd", {}), ("--actor", {}), ("--json", {"action": "store_true"})):
            result.add_argument(flag, default=argparse.SUPPRESS, **extra)
        if mutation:
            result.add_argument("--expected-revision", type=int)
            result.add_argument("--request-id", help="repeat-safe identity for this exact operation")
        return result

    setup = command("setup", "bind a profile to an explicitly initialized local Beads workspace")
    setup.add_argument("--beads-dir", type=Path, required=True)
    setup.add_argument("--source-root", type=Path, required=True)
    setup.add_argument("--shared", action="store_true", help="join an existing shared control after Beads bootstrap")
    setup.add_argument("--remote", default="origin", help="Git remote of the shared workspace")
    share = command("share", "enable guarded shared writes after every writer stops and upgrades")
    share.add_argument("--remote", default="origin")
    share.add_argument("--writers-paused", action="store_true", help="confirm all existing writers are stopped")
    share.add_argument("--clients-upgraded", action="store_true", help="confirm all clients support shared Plan")
    command("sync", "verify and refresh the shared store through its coordination gate")
    command("describe", "show selected store identity and supported operations")
    prd = command("prd", "read Product requirements without running Product")
    prd.add_argument("id", nargs="?")
    listing = command("list", "list work records from Beads")
    listing.add_argument("--type")
    listing.add_argument("--milestone")
    for name in ("show", "history"):
        cmd = command(name, "read one record by ID or TYPE NUMBER")
        cmd.add_argument("target", nargs="+")
    new = command("new", "create one typed record in backlog")
    new.add_argument("--request-id", help="repeat-safe identity for this exact operation")
    new.add_argument("type")
    new.add_argument("--title", required=True)
    new.add_argument("--description", default="")
    new.add_argument("--body-file", type=Path)
    for key in ("parent", "milestone", "item", "target-date", "spec", "size"):
        new.add_argument("--" + key)
    new.add_argument("--trace", action="append", default=[])
    new.add_argument("--link", action="append", default=[], metavar="FIELD=TARGET")
    new.add_argument("--set", action="append", default=[], metavar="FIELD=YAML")
    setter = command("set", "change a checked non-state field", mutation=True)
    setter.add_argument("id")
    setter.add_argument("field")
    setter.add_argument("value")
    setter.add_argument("--claim-token")
    body = command("body", "replace record text without writing a Markdown file", mutation=True)
    body.add_argument("id")
    body.add_argument("--file", type=Path, required=True)
    body.add_argument("--claim-token")
    for name in ("link", "unlink"):
        cmd = command(name, "change one typed relationship", mutation=True)
        cmd.add_argument("id")
        cmd.add_argument("relation", choices=sorted(model.RELATIONS))
        cmd.add_argument("target")
        cmd.add_argument("--claim-token")
    assign = command("assign", "assign work: TYPE NUMBER OWNER or ID OWNER", mutation=True)
    assign.add_argument("target", nargs="+")
    status = command("status", "read or change work state: TYPE NUMBER [STATE]", mutation=True)
    status.add_argument("target", nargs="+")
    status.add_argument("--approved-by")
    status.add_argument("--claim-token")
    for name in ("claim", "heartbeat", "release", "expire"):
        cmd = command(name, "manage a single-item local claim; release does not mark released", mutation=True)
        cmd.add_argument("target", nargs="+")
        cmd.add_argument("--lease", default="30m")
        cmd.add_argument("--claim-token")
    ready = command("ready", "list eligible work using Product state and spec rules")
    ready.add_argument("--type")
    ready.add_argument("--milestone")
    command("check", "validate the work graph and its requirement traces")
    recover = command("recover", "finish recorded incomplete writes; never take over another machine's gate")
    recover.add_argument("--previous-writer-stopped", action="store_true",
                         help="confirm the prior writer stopped before recovering this machine's saved shared attempt")
    migrate = command("migrate", "preview or copy a fixed roadmap snapshot; never modify source")
    migrate.add_argument("--source", type=Path)
    migrate.add_argument("--revision", help="source Git commit/ref; defaults to HEAD for Git sources")
    migrate.add_argument("--fingerprint", help="refuse when the preview fingerprint changed")
    migrate.add_argument("--apply", action="store_true", help="copy into the selected empty/incomplete workspace")
    github = command("github", "publish a Plan view to the configured GitHub Project")
    board_commands = github.add_subparsers(dest="github_command", required=True)
    configure = board_commands.add_parser("configure", help="check and save the existing board and named publisher")
    configure.add_argument("--repo", required=True, help="GitHub owner/repository")
    configure.add_argument("--owner", required=True, help="GitHub Project owner")
    configure.add_argument("--number", type=int, required=True, help="existing Project number")
    configure.add_argument("--writer", required=True, help="GitHub login authorized to publish")
    configure.add_argument("--type-mode", choices=("labels", "issue_types"))
    board_preview = board_commands.add_parser("preview", help="read a fixed Plan and board view without publishing")
    board_apply = board_commands.add_parser("apply", help="apply the accepted preview as the configured publisher")
    board_apply.add_argument("--fingerprint", required=True)
    board_apply.add_argument("--writer", required=True)
    for leaf in (configure, board_preview, board_apply):
        for flag, extra in (("--workspace", {"type": Path}), ("--bd", {}), ("--actor", {}),
                            ("--json", {"action": "store_true"})):
            leaf.add_argument(flag, default=argparse.SUPPRESS, **extra)
        leaf.add_argument("--request-id")
    return root


def target(parts):
    if len(parts) == 1:
        return parts[0], None
    if len(parts) == 2:
        return parts[1], model.type_name(parts[0])
    raise PlanError("target must be ID or TYPE NUMBER")


def value(text):
    try:
        return _json_value(yaml.safe_load(text))
    except yaml.YAMLError as exc:
        raise PlanError("value is not valid YAML/JSON") from exc


def require_profile(args):
    if not args.workspace:
        raise PlanError("select --workspace PROFILE or PLAN_WORKSPACE; no store was selected automatically")
    return Path(args.workspace)


def execute(args):
    profile = require_profile(args)
    if args.command == "setup":
        return Workspace.setup(profile, args.beads_dir, args.source_root, args.bd,
                               shared=args.shared, remote=args.remote), 0
    if args.command == "migrate":
        # Preview reads only source files and local configuration, not Beads.
        source = args.source
        if source is None:
            config = json.loads(profile.read_text(encoding="utf-8"))
            source = Path(config["source_root"]) / "docs/product/roadmap"
        data = snapshot(source, args.revision)
        if not args.apply:
            return preview(data), 0
        workspace = Workspace(profile, binary=args.bd, actor=args.actor or "agent:plan-migrate",
                              operation="migrate", request_id=getattr(args, "request_id", None))
        return import_snapshot(workspace, data, args.fingerprint), 0
    operation = args.command if args.command != "github" else "github-" + args.github_command
    workspace = Workspace(profile, binary=args.bd, actor=args.actor or "agent:plan",
                          operation=operation, request_id=getattr(args, "request_id", None))
    service = Service(workspace, args.actor)
    command = args.command
    if command == "share":
        return workspace.share(remote=args.remote, paused=args.writers_paused,
                               upgraded=args.clients_upgraded), 0
    if command == "sync":
        if not workspace.shared:
            raise PlanError("sync requires a shared workspace; local work was not published")
        with workspace.lock():
            workspace.control()
        return {"workspace_id": workspace.id, "synced": True, "saved": "shared"}, 0
    if command == "github":
        from planlib import github
        if args.github_command in {"configure", "apply"} and not args.actor:
            raise PlanError("GitHub configuration and publication require --actor or PLAN_ACTOR")
        with workspace.lock():
            if args.github_command == "configure":
                result = github.configure(workspace, args.repo, args.owner, args.number,
                                          args.writer, type_mode=args.type_mode)
            elif args.github_command == "preview":
                result = github.preview(workspace)
            else:
                result = github.apply(workspace, args.fingerprint, args.writer)
        return {**result, "saved": "shared" if workspace.shared else "local"}, 0
    if command == "describe":
        with workspace.lock():
            control = workspace.control()
        return {"provider": "plan", "contract_version": 2, "workspace_id": workspace.id,
                "beads_dir": str(workspace.beads_dir), "source_root": str(workspace.source_root),
                "import_state": control.get("import_state"), "shared": workspace.shared,
                "writes": "guarded shared Plan callers" if workspace.shared else "single-machine Plan callers",
                "operations": ["list", "show", "new", "set", "body", "link", "unlink", "assign", "status", "claim", "heartbeat", "release", "expire", "ready", "check", "migrate", "recover", "share", "sync", "github"],
                "group_claims": False, "distributed_claims": workspace.shared,
                "automatic_publish": workspace.shared, "factory_activated": False}, 0
    if command == "prd":
        reader = PRD(workspace.source_root)
        if args.id:
            return reader.get(args.id), 0
        return [{"id": page["id"], "path": page["path"], "type": page["fields"].get("type"),
                 "title": page["fields"].get("title"), "description": page["fields"].get("description"),
                 "hash": page["hash"]} for page in reader.pages()], 0
    if command == "list":
        return service.list(args.type, args.milestone), 0
    if command in {"show", "history"}:
        identifier, kind = target(args.target)
        record = service.show(identifier, kind)
        return (record["events"] if command == "history" else record), 0
    if command == "ready":
        return service.ready(args.type, args.milestone), 0
    if command == "check":
        result = service.check()
        return result, int(bool(result["errors"]))
    if command == "recover":
        if args.previous_writer_stopped:
            if not args.actor:
                raise PlanError("shared attempt recovery requires --actor or PLAN_ACTOR")
            return workspace.recover_shared(previous_writer_stopped=True), 0
        with workspace.lock():
            fixed = workspace.recover()
        return {"recovered": fixed, "saved": "shared" if workspace.shared else "local"}, 0
    if command == "new":
        links = {key: [getattr(args, key)] for key in ("parent", "milestone", "item") if getattr(args, key)}
        for item in args.link:
            key, separator, val = item.partition("=")
            if not separator:
                raise PlanError("--link requires FIELD=TARGET")
            links.setdefault(key, []).append(val)
        values = {}
        for item in args.set:
            key, separator, raw = item.partition("=")
            if not separator:
                raise PlanError("--set requires FIELD=YAML")
            values[key] = value(raw)
        for key in ("target_date", "spec", "size"):
            if getattr(args, key):
                values[key] = getattr(args, key)
        body = args.body_file.read_text(encoding="utf-8") if args.body_file else None
        return service.new(args.type, args.title, args.description, body, links, args.trace, values, args.request_id), 0
    common = {"expected": args.expected_revision, "request_id": args.request_id}
    if command in {"set", "body"}:
        field = args.field if command == "set" else "body"
        data = value(args.value) if command == "set" else args.file.read_text(encoding="utf-8")
        return service.edit(args.id, field, data, claim_token=args.claim_token, **common), 0
    if command in {"link", "unlink"}:
        return service.link(args.id, args.relation, args.target, remove=command == "unlink", claim_token=args.claim_token, **common), 0
    if command == "assign":
        if len(args.target) < 2:
            raise PlanError("assign requires ID OWNER or TYPE NUMBER OWNER")
        identifier, kind = target(args.target[:-1])
        return service.assign(identifier, args.target[-1], kind, **common), 0
    if command == "status":
        if len(args.target) == 1 or (len(args.target) == 2 and args.target[0].lower() in {name.lower() for name in model.TYPES}):
            identifier, kind = target(args.target)
            return service.show(identifier, kind), 0
        identifier, kind = target(args.target[:-1])
        if not args.actor:
            raise PlanError("a state change requires --actor or PLAN_ACTOR")
        return service.status(identifier, args.target[-1], kind, args.approved_by, claim_token=args.claim_token, **common), 0
    if command in {"claim", "heartbeat", "release", "expire"}:
        identifier, kind = target(args.target)
        if not args.actor:
            raise PlanError("a claim operation requires a distinct --actor or PLAN_ACTOR")
        if command == "claim":
            return service.claim(identifier, kind, args.lease, **common), 0
        if command == "heartbeat":
            return service.heartbeat(identifier, kind, args.lease, args.claim_token, **common), 0
        return service.release(identifier, kind, args.claim_token, expired=command == "expire", **common), 0
    raise PlanError("unsupported operation")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result, code = execute(args)
    except (PlanError, BeadsError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "success": False}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
