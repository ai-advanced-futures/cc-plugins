"""Select the roadmap backend of one factory. Never create or import a store."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys


# The time limit of 1 Plan command in seconds, when SOFA_PLAN_TIMEOUT is not set.
DEFAULT_TIMEOUT = 300
STILL_SHARED = "the Plan profile is still shared"


class PlanFailure(Exception):
    pass


def run(args, *, cwd=None, capture=True, env=None):
    """Run without a shell. Stop the process group at the time limit."""
    try:
        limit = float(os.environ.get("SOFA_PLAN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        if not math.isfinite(limit) or limit <= 0:
            raise ValueError
    except ValueError:
        raise PlanFailure("SOFA_PLAN_TIMEOUT must be a number greater than zero") from None
    if args[0] == "git":
        keys = {"GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_OBJECT_DIRECTORY", "GIT_DIR",
                "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
                "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                "GIT_COMMON_DIR", "GIT_NAMESPACE"}
        env = {key: value for key, value in (os.environ if env is None else env).items() if key not in keys}
        env["LC_ALL"] = "C"
    try:
        child = subprocess.Popen(args, cwd=cwd, env=env, text=True, start_new_session=True,
                                 stdout=subprocess.PIPE if capture else None,
                                 stderr=subprocess.PIPE if capture else None)
    except OSError:
        raise PlanFailure("the selected command could not start") from None
    try:
        out, err = child.communicate(timeout=limit)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            child.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            if child.stdout:
                child.stdout.close()
            if child.stderr:
                child.stderr.close()
        raise PlanFailure("the selected command did not end before the time limit") from None
    return child.returncode, out, err


def main_repo(repo, *, allow_plain=False):
    repo = Path(repo).resolve()
    rc, out, err = run(["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"])
    if rc:
        if allow_plain and rc == 128 and err.startswith("fatal: not a git repository"):
            return repo
        raise PlanFailure("cannot find the main repository")
    common = Path(out.strip())
    if common.name == ".git":
        return common.parent.resolve()
    rc, out, _ = run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"])
    if rc:
        raise PlanFailure("cannot find the main repository")
    return Path(out.strip()).resolve()


def selection(repo, *, known_main=False, adlc=None):
    """Read the two selection cells, resolving the profile against the main root."""
    root = Path(repo).resolve() if known_main else main_repo(repo)
    file = Path(adlc).resolve() if adlc is not None else root / "docs/adlc.md"
    values, section = {}, None
    try:
        text = file.read_text(encoding="utf-8") if file.exists() else ""
    except OSError:
        raise PlanFailure("cannot read the roadmap selection") from None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(\d+)", line)
        if heading:
            section = heading[1]
        if section == "1" and line.startswith("|"):
            cells = [x.strip() for x in line.split("|")[1:-1]]
            if len(cells) >= 2 and cells[0] in {"Roadmap backend", "Plan workspace"}:
                if cells[0] in values:
                    raise PlanFailure("the roadmap selection has a repeated row")
                cell = cells[1]
                if cell.startswith("`"):
                    match = re.fullmatch(r"`([^`]+)`", cell)
                    if not match:
                        raise PlanFailure("a roadmap selection cell has an invalid value")
                    cell = match[1]
                values[cells[0]] = cell
    backend = values.get("Roadmap backend", "product")
    if backend not in {"plan", "product"}:
        raise PlanFailure("Roadmap backend must be plan or product")
    if backend == "product":
        return root, backend, None
    value = values.get("Plan workspace")
    if not value or value.startswith("<"):
        raise PlanFailure("Plan workspace is missing; select a local profile before start")
    profile = (root / value).resolve()
    return root, backend, profile


def plan_script(root):
    override = os.environ.get("SOFA_PLAN_ROOT")
    if override:
        candidates = [Path(override) / "scripts/plan.py"]
    else:
        registry = Path.home() / ".claude/plugins/installed_plugins.json"
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            priority = {"local": 0, "project": 1, "user": 2}
            installs = [entry for name, entries in data["plugins"].items() if name.split("@")[0] == "plan"
                        for entry in entries
                        if entry.get("scope") == "user" or (entry.get("scope") in {"project", "local"}
                            and Path(entry.get("projectPath", "")).resolve() == root)]
            candidates = [Path(entry["installPath"]) / "scripts/plan.py"
                          for entry in sorted(installs, key=lambda entry: priority[entry["scope"]])]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            raise PlanFailure("cannot read the installed Plan plugin registry") from None
    script = next((p for p in candidates if p.is_file()), None)
    if script is None:
        raise PlanFailure("the Plan plugin is missing; install it before start")
    if not shutil.which("uv"):
        raise PlanFailure("uv is missing; install it before start")
    return script.resolve()


def still_shared(profile):
    """True when the profile has a `sharing` block of an earlier Plan. It reads the profile JSON and makes no Plan call."""
    try:
        document = json.loads(profile.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(document, dict) and "sharing" in document


class Plan:
    def __init__(self, root, profile, *, env=None):
        self.root, self.profile, self.env = root, profile, env
        if not profile.is_file():
            raise PlanFailure("the Plan workspace profile is missing; no store was created")
        self.command = ["uv", "run", str(plan_script(root)), "--workspace", str(profile)]

    def read(self, command):
        rc, out, _ = run([*self.command, command, "--json"], cwd=self.root, env=self.env)
        if rc:
            raise PlanFailure(f"Plan {command} failed; no Product fallback")
        try:
            return json.loads(out)
        except (ValueError, TypeError):
            raise PlanFailure(f"Plan {command} did not return JSON") from None

    def check_source(self, document=None):
        """Check the selected source without opening or synchronizing the store."""
        if document is None:
            try:
                document = json.loads(self.profile.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise PlanFailure("cannot read the Plan workspace profile") from None
        source = document.get("source_root") if isinstance(document, dict) else None
        if not isinstance(source, str) or not Path(source).is_absolute() or Path(source).resolve() != self.root:
            raise PlanFailure("Plan source_root must be the selected main repository")

    def describe(self):
        description = self.read("describe")
        if not isinstance(description, dict) or description.get("provider") != "plan" or type(description.get("contract_version")) is not int or description.get("contract_version") not in {1, 2}:
            raise PlanFailure("Plan describe returned an unsupported contract")
        self.check_source(description)
        imported = description.get("import_state")
        if imported and (not isinstance(imported, dict) or imported.get("status") != "complete"):
            raise PlanFailure("the Plan import is incomplete; complete it before start")
        return description

    def validate(self, *, require_records=False):
        # Before each Plan call: Plan refuses a shared profile, and the fix is 1 command.
        if still_shared(self.profile):
            raise PlanFailure(f"{STILL_SHARED}; run sofa-plan unshare (see references/planning.md)")
        self.describe()
        check = self.read("check")
        if not isinstance(check, dict) or not isinstance(check.get("errors"), list) or check["errors"]:
            raise PlanFailure("Plan check found errors; correct them before start")
        records = self.read("list")
        if not isinstance(records, list) or any(not isinstance(r, dict) or not isinstance(r.get("fields"), dict) for r in records):
            raise PlanFailure("Plan list did not return a record list")
        if require_records and not any(r["fields"].get("type") in {"Story", "Feature", "Milestone"} for r in records):
            raise PlanFailure("Plan has no roadmap records but the legacy roadmap exists; import it before start")
        return records


def legacy_roadmap(root):
    return any(
        next((root / "docs/product/roadmap" / folder).glob(f"{prefix}-*.md"), None) is not None
        for folder, prefix in (("stories", "STORY"), ("features", "FEATURE"), ("milestones", "MILESTONE")))


def validation_environment(root, settings, *, helper=None, output_style=""):
    """Use App settings for checks without changing the caller's environment."""
    if helper:
        command = [helper] if isinstance(helper, str) else list(helper)
        code, app_settings, _ = run([*command, "settings", "--output-style", output_style], cwd=root)
        if code == 0:
            try:
                settings = json.loads(app_settings)
            except ValueError:
                raise PlanFailure("GitHub App settings are not valid JSON; no Plan validation ran") from None
        elif code != 3:
            raise PlanFailure("the GitHub App setup of the team is broken; no Plan validation ran")
    if not isinstance(settings, dict):
        raise PlanFailure("station settings must be an object")
    environment = settings.get("env", {})
    if not isinstance(environment, dict) or any(not isinstance(value, str) for value in environment.values()):
        raise PlanFailure("station settings env must contain text values")
    return dict(os.environ) | environment


def station_settings(repo, settings, adlc=None, *, validation_helper=None, output_style=""):
    root = main_repo(repo, allow_plain=True)
    root, backend, profile = selection(root, known_main=True)
    if adlc is not None:
        if not Path(adlc).is_file():
            raise PlanFailure("cannot read the dispatch ADLC file")
        if selection(root, known_main=True, adlc=adlc) != (root, backend, profile):
            raise PlanFailure("dispatch ADLC differs from the main roadmap selection")
    data = json.loads(settings or "{}")
    if not isinstance(data, dict):
        raise PlanFailure("station settings must be an object")
    if backend == "plan":
        helper = [validation_helper, "--db", str(root / ".sofa/state.db")] if validation_helper else None
        environment = validation_environment(root, data, helper=helper, output_style=output_style)
        main_repo(root)
        Plan(root, profile, env=environment).validate(require_records=legacy_roadmap(root))
        data.setdefault("env", {})["PLAN_WORKSPACE"] = str(profile)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--settings", default="{}")
    parser.add_argument("--adlc")
    parser.add_argument("--validation-helper")
    parser.add_argument("--output-style", default="")
    args = parser.parse_args()
    try:
        print(json.dumps(station_settings(args.repo, args.settings, args.adlc,
                                         validation_helper=args.validation_helper, output_style=args.output_style)))
    except (PlanFailure, ValueError, TypeError) as exc:
        print(f"sofa-plan: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
