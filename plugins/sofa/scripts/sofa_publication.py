"""Optional factory publication. Approval is local; Plan owns targets and bindings."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from sofa_plan import PlanFailure, run, validation_environment


SCRIPTS = Path(__file__).resolve().parent
STATE_FILE = "github-publication.json"
TARGET_KEYS = ("repo", "owner", "number", "writer", "type_mode", "node_id")


def now():
    return datetime.now(timezone.utc).isoformat()


def state_path(root):
    return root / ".sofa" / STATE_FILE


def read_state(root):
    path = state_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "enabled": False}
    except (OSError, ValueError):
        raise PlanFailure("cannot read publication approval; run /sofa:setup") from None
    if (not isinstance(data, dict) or data.get("schema_version") != 1
            or type(data.get("enabled")) is not bool
            or (data["enabled"] and not isinstance(data.get("target"), dict))
            or not isinstance(data.get("last_attempt", {}), dict)
            or data.get("last_attempt", {}).get("status", "ready") not in {"ready", "verified", "partial", "failed"}):
        raise PlanFailure("invalid publication approval; run /sofa:setup")
    return data


def write_state(root, data):
    path = state_path(root)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix="publication-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def publication_lock(root):
    """Serialize enable, disable, and apply on this machine, without waiting."""
    folder = root / ".sofa"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(folder / "github-publication.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise PlanFailure("publication is busy; try again after the current operation") from None
        yield
    finally:
        os.close(fd)


def app_identity(root):
    """Read only public App identifiers, never the private-key location."""
    path = root / ".sofa/state.db"
    try:
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            rows = dict(db.execute("SELECT key, value FROM kv WHERE key IN (?, ?, ?)",
                                  tuple("machine.github-app." + key for key in ("app-id", "installation-id", "slug"))))
    except sqlite3.Error:
        raise PlanFailure("factory GitHub App is not configured; run /sofa:setup") from None
    identity = {key: rows.get("machine.github-app." + key) for key in ("app-id", "installation-id", "slug")}
    if any(not isinstance(value, str) or not value for value in identity.values()):
        raise PlanFailure("factory GitHub App is incomplete; run /sofa:setup")
    return identity


def app_environment(root):
    helper = [str(SCRIPTS / "sofa-github"), "--db", str(root / ".sofa/state.db")]
    code, out, _ = run([*helper, "check"], cwd=root)
    if code:
        raise PlanFailure("factory GitHub App access check failed; no personal-login fallback")
    permissions = next((line.removeprefix("permissions: ") for line in out.splitlines()
                        if line.startswith("permissions: ")), "").split()
    if not {"issues=write", "organization_projects=write"}.issubset(permissions):
        raise PlanFailure("factory App needs Issues and Organization projects read and write permissions")
    code, out, _ = run([*helper, "settings"], cwd=root)
    try:
        settings = json.loads(out) if code == 0 else None
        if "env" not in settings:
            raise ValueError
        environment = validation_environment(root, settings)
    except (ValueError, KeyError, TypeError, PlanFailure):
        raise PlanFailure("factory GitHub App settings failed; no personal-login fallback") from None
    # Only the shim can supply credentials to Plan's gh child.
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_HOST"):
        environment.pop(key, None)
    return environment


def plan_json(plan, arguments, environment=None):
    code, out, _ = run([*plan.command, *arguments, "--json"], cwd=plan.root, env=environment)
    try:
        result = json.loads(out)
    except (ValueError, TypeError):
        raise PlanFailure("Plan publication command failed or did not return JSON; inspect before retry") from None
    if code:
        raise PlanFailure("Plan publication check failed; inspect the selected workspace and GitHub access")
    return code, result


def target(plan):
    description = plan.describe(error_details=True)
    records = plan.read("list", "--type", "Project", error_details=True)
    if not isinstance(records, list):
        raise PlanFailure("Plan did not return work records")
    projects = [r for r in records if isinstance(r, dict) and r.get("fields", {}).get("type") == "Project"]
    if len(projects) != 1:
        raise PlanFailure("publication requires exactly one Plan Project")
    config = projects[0]["fields"].get("github")
    if not isinstance(config, dict) or any(config.get(key) in (None, "") for key in TARGET_KEYS):
        raise PlanFailure("configure the existing GitHub Project through Plan before enabling publication")
    identity = app_identity(plan.root)
    if config["writer"] != identity["slug"] + "[bot]":
        raise PlanFailure("Plan writer differs from the factory App; publication is blocked")
    if not description.get("workspace_id"):
        raise PlanFailure("Plan did not return a workspace identity")
    return {"workspace_id": description["workspace_id"], "project": projects[0]["id"],
            "github": {key: config[key] for key in TARGET_KEYS}, "app": identity}


def status(plan):
    saved = read_state(plan.root)
    result = {"enabled": saved["enabled"], "status": "disabled", "last_verified": saved.get("last_verified")}
    if saved["enabled"]:
        try:
            if target(plan) != saved["target"]:
                raise PlanFailure("publication target changed; run /sofa:setup before writing")
            result["status"] = saved.get("last_attempt", {}).get("status", "ready")
        except PlanFailure as exc:
            result.update(status="blocked", reason=str(exc))
    return result


def checked_preview(plan):
    environment = app_environment(plan.root)
    before = target(plan)
    _, preview = plan_json(plan, ["github", "preview"], environment)
    if (not isinstance(preview, dict) or preview.get("mode") != "preview"
            or not isinstance(preview.get("fingerprint"), str)
            or not isinstance(preview.get("items"), list) or preview.get("writer") != before["github"]["writer"]):
        raise PlanFailure("Plan returned an unsupported publication preview")
    if target(plan) != before:
        raise PlanFailure("publication target changed during preview; preview again")
    approval = hashlib.sha256(json.dumps({"target": before, "preview": preview["fingerprint"]},
                                        sort_keys=True).encode()).hexdigest()
    return {"target": before, "approval_fingerprint": approval, "preview": preview}


def disable(root):
    """Stop future writes even when the Plan profile or App is unavailable."""
    with publication_lock(root):
        saved = read_state(root)
        saved["enabled"] = False
        write_state(root, saved)
    return {"enabled": False, "status": "disabled"}


def configure_publication(plan, arguments):
    parser = argparse.ArgumentParser(prog="sofa-plan publication", allow_abbrev=False)
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("status", "preview", "disable"):
        commands.add_parser(name, allow_abbrev=False)
    enable = commands.add_parser("enable", allow_abbrev=False)
    enable.add_argument("--fingerprint", required=True, help="approval fingerprint of the checked preview")
    args = parser.parse_args(arguments)
    if args.action == "status":
        return status(plan)
    if args.action == "preview":
        return checked_preview(plan)
    if args.action == "disable":
        return disable(plan.root)
    with publication_lock(plan.root):
        previous = read_state(plan.root)
        checked = checked_preview(plan)
        if args.fingerprint != checked["approval_fingerprint"]:
            raise PlanFailure("setup preview changed; obtain approval of a new preview")
        # A new approval is ready, not evidence that a publication succeeded.
        saved = {"schema_version": 1, "enabled": True, "target": checked["target"],
                 "approved_at": now(), "approval_fingerprint": args.fingerprint,
                 "last_attempt": {"status": "ready", "at": now()}}
        if previous.get("target") == checked["target"] and previous.get("last_verified"):
            saved["last_verified"] = previous["last_verified"]
        write_state(plan.root, saved)
    return {"enabled": True, "status": "ready"}


def command_words(arguments):
    """Find Plan command words, including its accepted global option prefixes."""
    words = []
    i = 0
    while i < len(arguments) and len(words) < 2:
        arg = arguments[i]
        if arg.startswith("--"):
            flag = arg.split("=", 1)[0]
            matches = [name for name in ("--actor", "--bd", "--json", "--help", "--version") if name.startswith(flag)]
            if len(matches) != 1:
                raise PlanFailure("use complete Plan global option names before the command")
            if matches[0] in {"--actor", "--bd"} and "=" not in arg:
                i += 1
        elif arg == "-h":
            return words
        else:
            words.append(arg)
            if words[0] not in {"github", "publication"}:
                return words
        i += 1
    return words


def guarded_run(plan, arguments, *, limit=None, runner=None):
    """Run GitHub commands with factory controls; retain Plan's reply and timeout type."""
    runner = runner or run
    words = command_words(arguments)
    args = [*arguments] if "--json" in arguments else [*arguments, "--json"]

    def execute():
        environment = app_environment(plan.root)
        return runner([*plan.command, *args], cwd=plan.root, env=environment, limit=limit)

    if words != ["github", "apply"]:
        return execute()
    with publication_lock(plan.root):
        saved = read_state(plan.root)
        if not saved["enabled"]:
            raise PlanFailure("publication is disabled; enable it through /sofa:setup")
        try:
            if target(plan) != saved["target"]:
                raise PlanFailure("publication target changed; run /sofa:setup before writing")
            code, out, err = execute()
            try:
                result = json.loads(out)
            except (ValueError, TypeError):
                result = None
            valid = (isinstance(result, dict) and type(result.get("published")) is bool
                     and type(result.get("complete")) is bool)
            verified = valid and code == 0 and result["published"] and result["complete"]
            partial = valid and not verified and code in (0, 1)
            saved["last_attempt"] = {"status": "verified" if verified else "partial" if partial else "failed", "at": now()}
            if verified:
                saved["last_verified"] = {"at": now(), "fingerprint": result.get("fingerprint")}
            write_state(plan.root, saved)
            # The batch publisher classifies raw errors and retry details. Do not replace them.
            return code, out, err
        except PlanFailure:
            saved["last_attempt"] = {"status": "failed", "at": now()}
            write_state(plan.root, saved)
            raise


def github_command(plan, arguments, leaf):
    """Run the guarded command through the public Plan wrapper."""
    import sys

    code, out, err = guarded_run(plan, arguments)
    if leaf == "apply" and code == 0:
        try:
            result = json.loads(out)
        except (ValueError, TypeError):
            result = None
        if not isinstance(result, dict) or type(result.get("published")) is not bool or type(result.get("complete")) is not bool:
            raise PlanFailure("Plan returned an unsupported publication result; inspect before retry")
    sys.stdout.write(out or "")
    sys.stderr.write(err or "")
    return code if code >= 0 else 128 - code
