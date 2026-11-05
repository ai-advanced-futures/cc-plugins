#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""adr.py: the save code of the adr brain (standard section 8).

It imports the CI scripts from templates/verbatim/scripts, so the hook and the
CI copy run the same code (A15). Exit 0 on success, 1 on a data error, a failed
check, or a stale file, 2 on wrong input.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "templates" / "verbatim" / "scripts"))
import yaml  # noqa: E402

import adr_index  # noqa: E402
import adr_lib  # noqa: E402
import adr_lint  # noqa: E402
import adr_migrate  # noqa: E402
import adr_new  # noqa: E402

GRAPH = "adr"
OPERATIONS = ("Setup", "Learn", "Forget", "Upgrade", "Migrate", "Report")
ID_PATTERNS = {"sequential": r"^\d{4}[-_].+\.md$", "date": r"^\d{4}-\d{2}-\d{2}-.+\.md$"}


class UsageError(Exception):
    pass


class DataError(Exception):
    pass


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def version() -> str:
    return json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text("utf-8"))["version"]


def actor(args) -> str:
    return getattr(args, "by", None) or f"adr/{version()}"


def corpus(root):
    try:
        return adr_lib.load_corpus(root)
    except adr_lib.CorpusError as error:
        raise UsageError(str(error)) from error


def rel(root, path) -> str:
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def log(c, operation, text, who) -> None:
    path = c.dir / "log.md"
    lines = path.read_text("utf-8").splitlines() if path.is_file() else ["# Log"]
    now = stamp()
    entry = f"* **{operation}**: {' '.join(text.split())}, by {who}, at {now}"
    heading = f"## {now[:10]}"
    if heading in lines:
        at = lines.index(heading) + 1
        while at < len(lines) and lines[at].startswith("* "):
            at += 1
        lines.insert(at, entry)
    else:
        lines[1:1] = ["", heading, entry]
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def manifest_fields(c) -> dict:
    folders = ["."] + ([c.archive.name] if c.archive is not None else [])
    register = c.register.name if c.register.parent == c.dir else None
    return {"type": "Manifest", "title": "The adr brain",
            "description": "The architecture decision records of this repository.", "status": "stable",
            "brain": GRAPH, "plugin": "architecture", "plugin_version": version(),
            "ask_skill": {"plugin": "architecture:ask", "skills": "architecture-ask"},
            "install": "claude plugin install architecture@cc-plugins", "save_code": "scripts/adr.py",
            "id_pattern": ID_PATTERNS[c.id_scheme], "id_folders": folders,
            "answers": ["why did we choose X over Y", "which decision binds this change",
                        "is this decision still in force"],
            "required_links": {}, "fixed_pages": [register] if register else [], "retired_ids": [],
            "generated": {"by": f"adr/{version()}", "at": stamp()}}


def write_manifest(c) -> bool:
    path = c.dir / "manifest.md"
    fields = manifest_fields(c)
    if path.is_file():
        old = yaml.safe_load(adr_lib.split_frontmatter(path.read_text("utf-8"))[0])
        fields["retired_ids"] = old.get("retired_ids") or []
        if {k: v for k, v in old.items() if k != "generated"} == {k: v for k, v in fields.items() if k != "generated"}:
            return False
    head = yaml.safe_dump(fields, sort_keys=False, width=1000)
    path.write_text(f"---\n{head}---\n\n# The adr brain\n\nAsk with `/architecture:ask`. Learn with `/architecture:learn`.\n", encoding="utf-8")
    return True


def registry_add(root, path) -> bool:
    file = Path(root) / ".claude" / "knowledge.json"
    data = json.loads(file.read_text("utf-8")) if file.is_file() else {"graphs": {}}
    if data.setdefault("graphs", {}).get(GRAPH) == {"path": path}:
        return False
    data["graphs"][GRAPH] = {"path": path}
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _run_main(module, argv) -> int:
    """Run the main() of a CI script. Each one reads sys.argv."""
    saved = sys.argv
    sys.argv = [module.__name__] + argv
    try:
        return module.main()
    finally:
        sys.argv = saved


def regen_write(root) -> None:
    # No caller may ignore a regen failure (a cycle, exit 1, or an owner index, exit 2): each
    # one would otherwise write the manifest and exit 0 over stale navigation. [inferred]
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = _run_main(adr_index, ["--write", "--nav", "--repo-root", str(root)])
    if code:
        raise DataError(f"adr_index.py --write --nav failed: {err.getvalue().strip() or out.getvalue().strip()}")


def stale(root) -> list[str]:
    c = corpus(root)
    nav = adr_index.build_navigation(c, adr_index.nav_context(c))
    out = [name for name, _state in adr_index.stale_files(c, nav)]  # name is already root-relative [inferred]
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        register_stale = _run_main(adr_index, ["--check", "--repo-root", str(root)]) != 0
    if register_stale and not out:
        out.append(rel(root, c.register))
    return sorted(set(out))


def find(root, key) -> Path:
    c = corpus(root)
    name = key.lstrip("/").rsplit("/", 1)[-1]
    name = name if name.endswith(".md") else f"{name}.md"
    for folder in [c.dir] + ([c.archive] if c.archive is not None else []):
        if (folder / name).is_file():
            return folder / name
    raise UsageError(f"no ADR is named {key}")


def load(path):
    front, body = adr_lib.split_frontmatter(path.read_text(encoding="utf-8"))
    if front is None:
        raise UsageError(f"{path.name} has no frontmatter. Run /architecture:migrate first.")
    return adr_lib.load_frontmatter(front), body


def _unresolved_bundle_link(c, value) -> bool:
    """True for an old repo-root-style `/` link that does not resolve inside this
    bundle (D18): migrate_lifecycle's discover() and the general check's bundle-
    relative resolution disagree on scope, so a legacy value like
    `/docs/architecture/x.md` is never a real link to this corpus. [inferred]"""
    if not isinstance(value, str) or not value.startswith("/") or ".md" not in value:
        return False
    return not (c.dir / value.split("#", 1)[0].lstrip("/")).is_file()


def _delink(c, value):
    return value[1:] if _unresolved_bundle_link(c, value) else value


def save(root, path, meta, body, who) -> None:
    meta["generated"] = {"by": who, "at": stamp()}
    if meta.get("lifecycle") in adr_lib.OKF_STATUS_OF:
        meta["status"] = adr_lib.OKF_STATUS_OF[meta["lifecycle"]]
    path.write_text("---\n" + adr_lib.dump_frontmatter(meta) + "---\n" + body, encoding="utf-8")
    regen_write(root)


def parse_pair(item):
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), yaml.safe_load(value) if value.strip() else ""


def cmd_init(args) -> int:
    c = corpus(args.root)
    if not c.dir.is_dir():
        raise UsageError(f"{c.dir} does not exist. Run /architecture:setup first.")
    if not (c.dir / "log.md").exists():
        log(c, "Setup", f"made the bundle {rel(args.root, c.dir)}", actor(args))
    regen_write(args.root)
    write_manifest(c)
    registry_add(args.root, rel(args.root, c.dir))
    print(f"made {rel(args.root, c.dir)}")
    return 0


def cmd_upgrade(args) -> int:
    c = corpus(args.root)
    changes = []
    with redirect_stdout(io.StringIO()) as out:
        adr_migrate.migrate_lifecycle(c, apply=True)
    if not out.getvalue().startswith("0 ADRs"):
        changes.append("moved the ADR lifecycle to `lifecycle`")
    # relationship_corpus parses every path into a record (discover/discover_archived give Path
    # objects), and it also walks a nested archive folder that discover_archived does not. [inferred]
    for record in adr_lib.relationship_corpus(c).values():
        if record.source != "frontmatter":
            continue
        meta, body = load(record.path)
        before = dict(meta)
        # migrate_lifecycle walks discover()/discover_archived(), which drop a
        # register.exclude file; this record came from relationship_corpus, so it
        # still sees a legacy status here and moves it the same way (A14). [inferred]
        if meta.get("lifecycle") is None and meta.get("status") in adr_lib.LIFECYCLES:
            lifecycle = meta["status"]
            meta["status"] = adr_lib.OKF_STATUS_OF[lifecycle]
            meta["lifecycle"] = lifecycle
        for key in adr_lib.RELATIONS:
            value = meta.get(key)
            if isinstance(value, list):
                meta[key] = [_delink(c, item) for item in value]
            elif value is not None:
                meta[key] = _delink(c, value)
        meta.setdefault("generated", {"by": "process:adr-upgrade", "at": f"{record.date or stamp()[:10]}T00:00:00Z"})
        if not meta.get("description"):
            meta["description"] = adr_lib.description_draft(body)
        if meta != before:
            record.path.write_text("---\n" + adr_lib.dump_frontmatter(meta) + "---\n" + body, encoding="utf-8")
            changes.append(f"updated {record.filename}")
    register = c.register
    if register.is_file() and not register.read_text("utf-8").startswith("---"):
        seed = (PLUGIN_ROOT / "templates" / "register-seed.md").read_text("utf-8")
        head = seed.split("---\n", 2)[1].replace("{{TODAY}}", stamp()[:10])
        register.write_text(f"---\n{head}---\n\n" + register.read_text("utf-8"), encoding="utf-8")
        changes.append("added the register frontmatter")
    if not (c.dir / "log.md").exists():
        (c.dir / "log.md").write_text("# Log\n", encoding="utf-8")
        changes.append("added log.md")
    regen_write(args.root)
    if write_manifest(c):
        changes.append("wrote manifest.md")
    if registry_add(args.root, rel(args.root, c.dir)):
        changes.append("wrote the registry entry adr")
    if changes:
        log(c, "Upgrade", f"brought the corpus to the brain standard ({len(changes)} changes)", "process:adr-upgrade")
    print("\n".join(changes) if changes else "the corpus is on the standard: nothing to change")
    return 0


def cmd_new(args) -> int:
    argv = ["--title", args.title, "--area", args.area, "--repo-root", str(args.root)]
    if args.description:
        argv += ["--description", args.description]
    for key in ("lifecycle", "parent_spec"):
        if getattr(args, key):
            argv += [f"--{key.replace('_', '-')}", getattr(args, key)]
    with redirect_stdout(io.StringIO()) as out:
        code = _run_main(adr_new, argv)
    if code:
        return code
    path = Path(args.root) / out.getvalue().strip().splitlines()[-1]
    meta, body = load(path)
    save(args.root, path, meta, body, actor(args))
    print(rel(args.root, path))
    return 0


def cmd_set(args) -> int:
    path = find(args.root, args.key)
    meta, body = load(path)
    for item in args.pairs:
        key, value = parse_pair(item)
        if key in ("type", "generated", "protected", "status"):
            raise UsageError(f"set does not change {key}. Only a person changes protected; status follows lifecycle.")
        meta[key] = value
    save(args.root, path, meta, body, actor(args))
    print(rel(args.root, path))
    return 0


def cmd_link(args, remove=False) -> int:
    if args.field not in adr_lib.RELATIONS:
        raise UsageError(f"{args.field} is not a link field: use {', '.join(adr_lib.RELATIONS)}")
    path = find(args.root, args.key)
    meta, body = load(path)
    if args.field == "parent_spec":
        if remove and meta.get("parent_spec") != args.target:
            raise UsageError(f"{args.key} has no parent_spec {args.target}")
        meta["parent_spec"] = None if remove else args.target
    else:
        values = adr_lib.refs(meta, args.field)
        if remove and args.target not in values:
            raise UsageError(f"{args.key} has no {args.field} link to {args.target}")
        meta[args.field] = [v for v in values if v != args.target] if remove else values + [args.target]
    save(args.root, path, meta, body, actor(args))
    print(rel(args.root, path))
    return 0


def cmd_remove(args) -> int:
    path = find(args.root, args.key)
    meta, _body = load(path)
    if meta.get("protected") is True:
        print(f"ERROR: {args.key} is protected. Only a person can remove protected: true.", file=sys.stderr)
        return 1
    c = corpus(args.root)
    name = path.name
    path.unlink()
    manifest_path = c.dir / "manifest.md"
    front, body = adr_lib.split_frontmatter(manifest_path.read_text("utf-8"))
    data = yaml.safe_load(front)
    data["retired_ids"] = sorted(set(data.get("retired_ids") or []) | {path.stem})
    manifest_path.write_text("---\n" + yaml.safe_dump(data, sort_keys=False, width=1000) + "---\n" + body, encoding="utf-8")
    log(c, "Forget", f"removed /{name}", actor(args))
    regen_write(args.root)
    print(f"removed {name}")
    return 0


def cmd_resolve(args) -> int:
    print(rel(args.root, find(args.root, args.key)))
    return 0


def cmd_regen(args) -> int:
    if args.check:
        paths = stale(args.root)
        for path in paths:
            print(f"STALE: {path}")
        return 1 if paths else 0
    regen_write(args.root)
    return 0


def cmd_check(args) -> int:
    argv = ["--repo-root", str(args.root)] + (["--strict"] if args.strict else [])
    return _run_main(adr_lint, argv)


def cmd_log(args) -> int:
    if args.operation not in OPERATIONS:
        raise UsageError(f"{args.operation!r} is not an operation: use {', '.join(OPERATIONS)}")
    log(corpus(args.root), args.operation, args.text, actor(args))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adr.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "upgrade"):
        p = sub.add_parser(name)
        p.add_argument("--by")
        p.set_defaults(run=cmd_init if name == "init" else cmd_upgrade)
    p = sub.add_parser("new")
    p.add_argument("--title", required=True)
    p.add_argument("--area", required=True)
    p.add_argument("--description")
    p.add_argument("--lifecycle", choices=list(adr_lib.LIFECYCLES))
    p.add_argument("--parent-spec", dest="parent_spec")
    p.add_argument("--by")
    p.set_defaults(run=cmd_new)
    p = sub.add_parser("set")
    p.add_argument("key")
    p.add_argument("pairs", nargs="+")
    p.add_argument("--by")
    p.set_defaults(run=cmd_set)
    for name, remove in (("link", False), ("unlink", True)):
        p = sub.add_parser(name)
        p.add_argument("key")
        p.add_argument("field")
        p.add_argument("target")
        p.add_argument("--by")
        p.set_defaults(run=lambda a, r=remove: cmd_link(a, r))
    for name, run in (("remove", cmd_remove), ("resolve", cmd_resolve)):
        p = sub.add_parser(name)
        p.add_argument("key")
        p.add_argument("--by")
        p.set_defaults(run=run)
    p = sub.add_parser("regen")
    p.add_argument("--check", action="store_true")
    p.set_defaults(run=cmd_regen)
    p = sub.add_parser("check")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(run=cmd_check)
    p = sub.add_parser("log")
    p.add_argument("operation")
    p.add_argument("text")
    p.add_argument("--by")
    p.set_defaults(run=cmd_log)
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
