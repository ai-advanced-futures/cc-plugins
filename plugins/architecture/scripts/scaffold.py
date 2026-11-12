#!/usr/bin/env python3
"""Deterministic scaffolder for the architecture plugin.

Writes the corpus directory (--dir, docs/adr by default), .claude/adr.json,
and a pointer block in the target repo's CLAUDE.md. It vendors the
scripts/schemas/tests trees only for an explicit deterministic CI gate. A
fresh run calls `adr_index.py --write --nav` one time, so the new corpus
starts with navigation on. It never runs `adr_lint.py` -- that stays an
explicit, separate step run by the caller, the architecture:setup skill, or this
plugin's own test suite.

Write safety. If any manifest target already exists, a fresh run refuses
and writes nothing, following knowledge/scripts/scaffold.py. Three exceptions,
each idempotent, are reached only via --refresh or --adopt (and the repo
CLAUDE.md one via --router-only): the repo
CLAUDE.md router block (replaced between its markers), the vendored
scripts/schemas/tests trees, and the register (seeded only when absent;
adr_index.py --write owns the generated block otherwise).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import claude_md_router  # noqa: E402  (same directory)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = PLUGIN_ROOT / "templates"
VERBATIM = TEMPLATES / "verbatim"

sys.path.insert(0, str(VERBATIM / "scripts"))
import adr_lib  # noqa: E402

TOKEN_NAMES = ("DIR", "REGISTER", "TODAY")

# Repo-root-relative destinations. The vendored trees sit beside {{DIR}}, never
# inside it, so Discovery's non-recursive glob never has to exclude them.
VENDOR_DEST = {"scripts": "scripts/adr", "schemas": "schemas/adr", "tests": "tests/adr"}

VERBATIM_FILES = [
    "scripts/adr_lib.py", "scripts/adr_new.py", "scripts/adr_index.py",
    "scripts/adr_lint.py", "scripts/adr_migrate.py", "requirements.txt",
    "schemas/adr.schema.json",
    "tests/conftest.py", "tests/test_adr_lib.py", "tests/test_adr_new.py",
    "tests/test_adr_index.py", "tests/test_adr_lint.py", "tests/test_adr_migrate.py",
]
RENDERED_FILES = {"{{DIR}}/README.md": "register-seed.md"}

DEFAULT_GATE = {"deterministic": False, "model": False, "proposed_verdict": "error"}
GATE_TEMPLATE = TEMPLATES / "gate" / "adr-gate.yml"
GATE_DEST = ".github/workflows/adr-gate.yml"
GATE_JOB_MARKERS = {
    "deterministic": ("# ADR-GATE:DETERMINISTIC:BEGIN", "# ADR-GATE:DETERMINISTIC:END"),
    "model": ("# ADR-GATE:MODEL:BEGIN", "# ADR-GATE:MODEL:END"),
}


class ScaffoldError(Exception):
    pass


def dest_for(rel: str) -> str:
    """Map a VERBATIM_FILES entry to its repo-root-relative destination.

    scripts/x -> scripts/adr/x, requirements.txt -> scripts/adr/requirements.txt,
    schemas/x -> schemas/adr/x, tests/x -> tests/adr/x.
    """
    if "/" in rel:
        top, rest = rel.split("/", 1)
        if top in VENDOR_DEST:
            return f"{VENDOR_DEST[top]}/{rest}"
        return rel
    # a bare top-level file, e.g. requirements.txt, lands beside the scripts
    return f"{VENDOR_DEST['scripts']}/{rel}"


def render(text: str, tokens: dict) -> str:
    for name, value in tokens.items():
        text = text.replace("{{" + name + "}}", value)
    return text


def normalize_dir(raw: str) -> str:
    """Repo-root-relative, never absolute, never escaping the target."""
    d = raw.strip().strip("/")
    if not d:
        raise ScaffoldError("--dir must not be empty")
    parts = [p for p in d.split("/") if p]
    if any(p in ("..", ".") for p in parts):
        raise ScaffoldError(f"--dir must not escape the target repo: {raw!r}")
    return "/".join(parts)


def gate_rows(gate: dict) -> list:
    """The CI gate paths this script writes: the vendored scripts only when the
    config asks for the deterministic tier, and adr-gate.yml whenever either
    tier is requested. An unrelated project's adr-gate.yml is never touched
    unless a tier is asked for."""
    gate = gate or {}
    rows = []
    if gate.get("deterministic"):
        rows += [dest_for(rel) for rel in VERBATIM_FILES]
    if gate.get("deterministic") or gate.get("model"):
        rows.append(GATE_DEST)
    return rows


def manifest(dir_: str, register: str, gate: dict = None) -> list:
    """Every repo-relative path this script writes for a fresh (non-refresh,
    non-adopt) run. A greenfield corpus starts with navigation on, so the 2
    generated files are part of the manifest (section 13.2)."""
    return [register, ".claude/adr.json",
            f"{dir_}/index.md", f"{dir_}/links.tsv"] + gate_rows(gate)


def plugin_version() -> str:
    path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    with open(path) as f:
        return json.load(f)["version"]


def write_config(path: Path, dir_: str, register: str, id_scheme: str, gate: dict,
                 *, exclude=(), schema=None, rules=None, extra_corpora=()) -> None:
    payload = {
        "dir": dir_,
        "register": {"path": register, "exclude": list(exclude)},
        "id_scheme": id_scheme,
        "gate": dict(gate),
        "archive_dir": "archive",
        "schema": schema,
        "rules": rules,
        "extra_corpora": list(extra_corpora),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_if_changed(path: Path, text: str) -> bool:
    """Write text only when it differs from what is already on disk. Returns
    True when the file was written. A file with non-UTF-8 bytes counts as
    different, so a corrupted or hand-edited file gets rewritten cleanly
    instead of raising."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == text:
                return False
        except UnicodeDecodeError:
            pass
    path.write_text(text, encoding="utf-8")
    return True


def build_gate_workflow(gate: dict, tokens: dict):
    """Render adr-gate.yml with only the job(s) `gate` asks for. Returns None
    when neither tier is requested, so the caller writes nothing."""
    wanted = [name for name in ("deterministic", "model") if (gate or {}).get(name)]
    if not wanted:
        return None
    lines = render(GATE_TEMPLATE.read_text(encoding="utf-8"), tokens).splitlines()
    header_end = next(i for i, line in enumerate(lines) if line.strip() == "jobs:")
    body = []
    for name in wanted:
        begin, end = GATE_JOB_MARKERS[name]
        start = next(i for i, line in enumerate(lines) if begin in line)
        stop = next(i for i, line in enumerate(lines) if end in line)
        body.extend(lines[start:stop + 1])
    return "\n".join(lines[:header_end + 1] + body) + "\n"


def write_gate_workflow(target: Path, gate: dict, tokens: dict):
    """Write .github/workflows/adr-gate.yml when the config asks for at least
    one tier. Returns the repo-relative path when the file was written or
    changed, or None when the config asked for no tier or the file is already
    current."""
    text = build_gate_workflow(gate, tokens)
    if text is None:
        return None
    if write_if_changed(target / GATE_DEST, text):
        return GATE_DEST
    return None


def copy_vendored(target: Path) -> list:
    """Copy every VERBATIM_FILES entry whose bytes differ from what is on
    disk. Returns the list of repo-relative destinations actually written."""
    written = []
    for rel in VERBATIM_FILES:
        src = VERBATIM / rel
        dst = target / dest_for(rel)
        src_bytes = src.read_bytes()
        if dst.is_file() and dst.read_bytes() == src_bytes:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src_bytes)
        written.append(dest_for(rel))
    return written


def adopt_manifest(gate: dict) -> list:
    """Files adoption writes without modifying an existing corpus."""
    return [".claude/adr.json"] + gate_rows(gate)


def exclusion_candidates(target: Path, dir_: str, register: str) -> list:
    """Return ADR-directory markdown files not linked by the register."""
    register_path = target / register
    linked = set()
    if register_path.is_file():
        linked = {match.group(1) for match in re.finditer(
            r"\]\(\./(?:archive/)?([^)]+\.md)\)",
            register_path.read_text(encoding="utf-8"),
        )}
    skipped = {Path(register).name, "README.md", "CLAUDE.md"}
    return sorted(path.name for path in (target / dir_).glob("*.md")
                  if path.name not in skipped and path.name not in linked
                  and not adr_lib.is_generated_index(path))


ROUTER_MARKERS = ("<!-- adr:router start -->", "<!-- adr:router end -->")


def check_root_markers(target: Path) -> None:
    """Raise ValueError when the repo CLAUDE.md holds a broken adr marker pair.
    Run it before any write, so a broken pair leaves no half-written corpus."""
    claude_md_router.merge(claude_md_router.read_text(target / "CLAUDE.md"), "adr", "")


def append_root_block(target: Path, dir_: str, register: str, tokens: dict) -> str:
    """Write the rendered root block into the repo CLAUDE.md between the
    `<!-- adr:router start/end -->` markers (claude_md_router.py). A marked
    block is replaced in place; a block from an earlier version, found by the
    rendered corpus-CLAUDE.md link when no marker is present, is kept as it
    is. When <dir>/CLAUDE.md does not exist (an adopted corpus), the block
    leaves out the line that links to it. Returns 'wrote' (a fresh CLAUDE.md
    had to be created), 'appended', 'replaced', or 'already present'. Raises
    ValueError on a broken marker pair."""
    claude_md_path = target / "CLAUDE.md"
    body = render((TEMPLATES / "claude-md-root-block.md").read_text(encoding="utf-8"), tokens)
    legacy = f"[`{dir_}/CLAUDE.md`]({dir_}/CLAUDE.md)"
    if not (target / dir_ / "CLAUDE.md").is_file():
        body = "".join(line for line in body.splitlines(keepends=True) if legacy not in line)
    existed = claude_md_path.exists()
    existing_text = claude_md_router.read_text(claude_md_path)
    marked = any(m in existing_text for m in ROUTER_MARKERS)
    if legacy in existing_text and not marked:
        return "already present"
    new_text = claude_md_router.merge(existing_text, "adr", claude_md_router.render("adr", body))
    if new_text == existing_text:
        return "already present"
    claude_md_router.write_text(claude_md_path, new_text)
    if marked:
        return "replaced"
    return "appended" if existed else "wrote"


def router_only(target: Path, config_path: Path) -> int:
    """Write only the repo CLAUDE.md router block, from the stored config."""
    if not config_path.is_file():
        print(f"ERROR: {config_path} does not exist; run setup first", file=sys.stderr)
        return 1
    config = json.loads(config_path.read_text(encoding="utf-8"))
    dir_ = config.get("dir")
    raw_register = config.get("register")
    register = raw_register.get("path") if isinstance(raw_register, dict) else raw_register
    if not isinstance(dir_, str) or not dir_ or not isinstance(register, str) or not register:
        print("ERROR: config needs a dir and a register path", file=sys.stderr)
        return 1
    tokens = {"DIR": dir_, "REGISTER": register, "TODAY": ""}
    try:
        result = append_root_block(target, dir_, register, tokens)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    status = "unchanged" if result == "already present" else "written"
    print(f"CLAUDE.md router: {status} {target / 'CLAUDE.md'}")
    return 0


def gate_flags_passed(args) -> list:
    """Return the gate flags the user explicitly passed. --refresh reads the
    gate from the config, so any of these on the command line is a conflict."""
    passed = []
    if args.gate_deterministic:
        passed.append("--gate-deterministic")
    if args.gate_model:
        passed.append("--gate-model")
    if args.proposed_verdict != "error":
        passed.append("--proposed-verdict")
    return passed


def build_parser() -> argparse.ArgumentParser:
    # allow_abbrev=False so `--gate-mo` is not silently accepted for --gate-model,
    # which would slip past gate_flags_passed() and get dropped in --refresh.
    parser = argparse.ArgumentParser(description="Scaffold an ADR corpus into a target repo",
                                     allow_abbrev=False)
    parser.add_argument("--target", required=True)
    parser.add_argument("--dir", default="docs/adr")
    parser.add_argument("--register")
    parser.add_argument("--id-scheme", default="sequential", choices=("sequential", "date"))
    parser.add_argument("--today")
    parser.add_argument("--adopt", action="store_true",
                        help="write config + vendored tooling, touch no existing ADR")
    parser.add_argument("--refresh", action="store_true",
                        help="idempotently refresh the four write-safety exceptions")
    parser.add_argument("--dry-run", action="store_true", help="print the manifest, write nothing")
    parser.add_argument("--router-only", action="store_true",
                        help="write only the repo CLAUDE.md router block, from .claude/adr.json")
    parser.add_argument("--gate-deterministic", action="store_true",
                        help="write the deterministic-tier CI gate job")
    parser.add_argument("--gate-model", action="store_true",
                        help="write the model-tier CI gate job")
    parser.add_argument("--proposed-verdict", default="error",
                        choices=("error", "warning", "off"),
                        help="how the gate treats an ADR still `proposed` in a changed file")
    return parser


def stage_corpus_files(target: Path, register: str, tokens: dict, verb: str) -> list:
    """Seed the register when absent."""
    written = []

    register_path = target / register
    if register_path.is_file():
        print(f"already present: {register}")
    else:
        register_path.parent.mkdir(parents=True, exist_ok=True)
        register_path.write_text(
            render((TEMPLATES / "register-seed.md").read_text(encoding="utf-8"), tokens),
            encoding="utf-8")
        print(f"{verb} {register}")
        written.append(register)

    return written


def stage_gate(target: Path, gate: dict, tokens: dict, verb: str) -> list:
    """Vendor deterministic tooling when the deterministic tier is requested,
    and write adr-gate.yml whenever either tier (deterministic or model) is
    requested."""
    written = []
    if gate.get("deterministic"):
        for rel in copy_vendored(target):
            print(f"{verb} {rel}")
            written.append(rel)
    gate_result = write_gate_workflow(target, gate, tokens)
    if gate_result:
        print(f"{verb} {gate_result}")
        written.append(gate_result)
    return written


def run_generator(target: Path) -> int:
    """Run the plugin copy of adr_index.py on the new corpus.

    A greenfield corpus starts with navigation on, so the 2 generated files,
    `index.md` and `links.tsv`, are the generator output and the first lint
    reports no drift. A greenfield corpus has no archive directory, so the
    generator writes no archive index.
    """
    result = subprocess.run(
        [sys.executable, str(VERBATIM / "scripts" / "adr_index.py"),
         "--write", "--nav", "--repo-root", str(target)],
        capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


def sweep_leftover_tokens(target: Path, rendered_paths) -> list:
    """The rendered rows are the only files a token can survive in -- the
    vendored files are copied byte for byte and may legitimately mention a
    token name, e.g. adr_lib.py's own docstring describing '{{DIR}}/*.md'
    Discovery."""
    leftover = []
    for rel in rendered_paths:
        path = target / rel
        if path.is_file() and re.search(r"\{\{(?:DIR|REGISTER|TODAY)\}\}",
                                        path.read_text(encoding="utf-8", errors="replace")):
            leftover.append(rel)
    return leftover


def main() -> int:
    args = build_parser().parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: --target '{target}' is not a directory", file=sys.stderr)
        return 1
    if args.router_only:
        return router_only(target, target / ".claude" / "adr.json")

    try:
        dir_ = normalize_dir(args.dir)
    except ScaffoldError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    register = args.register or f"{dir_}/README.md"
    today = args.today

    tokens = {"DIR": dir_, "REGISTER": register, "TODAY": today or ""}
    config_path = target / ".claude" / "adr.json"
    gate = {"deterministic": args.gate_deterministic, "model": args.gate_model,
            "proposed_verdict": args.proposed_verdict}

    if args.dry_run:
        rows = adopt_manifest(gate) if args.adopt else manifest(dir_, register, gate)
        for rel in rows:
            print(f"  {rel}")
        if not args.adopt:
            print("  CLAUDE.md  (router block between <!-- adr:router start/end --> markers)")
            print(f"{len(rows) + 1} manifest rows ({len(rows)} files + 1 append)")
        else:
            for candidate in exclusion_candidates(target, dir_, register):
                print(f"register.exclude candidate: {candidate}")
            print(f"{len(rows)} manifest rows ({len(rows)} file{'s' if len(rows) != 1 else ''})")
        return 0

    if args.refresh:
        stray = gate_flags_passed(args)
        if stray:
            print(f"ERROR: --refresh reads the gate from .claude/adr.json; drop {', '.join(stray)}",
                  file=sys.stderr)
            return 1
        if not config_path.is_file():
            print(f"ERROR: {config_path} does not exist; run without --refresh first",
                 file=sys.stderr)
            return 1
        config = json.loads(config_path.read_text(encoding="utf-8"))
        dir_ = config["dir"]
        raw_register = config["register"]
        if isinstance(raw_register, str):
            register = {"path": raw_register, "exclude": []}
        elif isinstance(raw_register, dict) and isinstance(raw_register.get("path"), str):
            register = raw_register
        else:
            print("ERROR: config register must be a path string or an object with path",
                  file=sys.stderr)
            return 1
        register_path = register["path"]
        tokens = {"DIR": dir_, "REGISTER": register_path, "TODAY": today or ""}
        try:
            check_root_markers(target)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        stage_corpus_files(target, register_path, tokens, verb="refreshed")
        stage_gate(target, config.get("gate") or {}, tokens, verb="refreshed")
        root_result = append_root_block(target, dir_, register_path, tokens)
        print(f"CLAUDE.md {root_result}")
        return 0

    if args.adopt:
        if config_path.exists():
            print(f"ERROR: {config_path} already exists; refusing to overwrite", file=sys.stderr)
            return 1
        write_config(config_path, dir_, register, args.id_scheme, gate)
        print(f"wrote {config_path.relative_to(target).as_posix()}")
        stage_gate(target, gate, tokens, verb="wrote")
        # Navigation is always on (spec 9.1, D2), also for an adopted corpus.
        if run_generator(target) != 0:
            print("ERROR: the index generator failed; the corpus is not complete",
                  file=sys.stderr)
            return 1
        for candidate in exclusion_candidates(target, dir_, register):
            print(f"register.exclude candidate: {candidate}")
        print("adopted: no existing ADR was modified")
        return 0

    # Fresh, greenfield run.
    rows = manifest(dir_, register, gate)
    existing = [rel for rel in rows if (target / rel).exists()]
    if existing:
        print("ERROR: refusing to overwrite existing files:", file=sys.stderr)
        for rel in existing:
            print(f"  {rel}", file=sys.stderr)
        return 1

    if not today:
        print("ERROR: --today is required for a fresh run", file=sys.stderr)
        return 1

    try:
        check_root_markers(target)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    (target / dir_).mkdir(parents=True, exist_ok=True)
    written = stage_corpus_files(target, register, tokens, verb="wrote")
    written.extend(stage_gate(target, gate, tokens, verb="wrote"))
    write_config(config_path, dir_, register, args.id_scheme, gate)
    print("wrote .claude/adr.json")
    written.append(".claude/adr.json")
    root_result = append_root_block(target, dir_, register, tokens)

    if run_generator(target) != 0:
        print("ERROR: the index generator failed; the corpus is not complete",
              file=sys.stderr)
        return 1
    written.extend([f"{dir_}/index.md", f"{dir_}/links.tsv"])

    missing = [rel for rel in rows if not (target / rel).exists()]
    if missing:
        print("ERROR: scaffold finished but these manifest files are missing:", file=sys.stderr)
        for rel in missing:
            print(f"  {rel}", file=sys.stderr)
        return 1

    rendered_paths = [f"{dir_}/CLAUDE.md", register, "CLAUDE.md"]
    if (target / GATE_DEST).is_file():
        rendered_paths.append(GATE_DEST)
    leftover = sweep_leftover_tokens(target, rendered_paths)
    if leftover:
        print("ERROR: unrendered '{{...}}' token survives in:", file=sys.stderr)
        for rel in leftover:
            print(f"  {rel}", file=sys.stderr)
        return 1

    print(f"CLAUDE.md {root_result}")
    print(f"{len(written)} files written, CLAUDE.md {root_result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
