"""Beads CLI adapter. Supported release: bd 1.3.4 (7ef2fd05e)."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


class BeadsError(RuntimeError):
    """A Beads command failed or returned invalid data."""


class Beads:
    """Use one explicit Beads directory; shared transport needs an outer Git gate."""

    def __init__(self, beads_dir: Path, binary: str = "bd", actor: str = "agent:plan", timeout: float = 60):
        self.beads_dir = Path(beads_dir).expanduser().resolve()
        self.binary = str(binary)
        self.actor = actor
        self.timeout = timeout
        self.shared_active: bool = False
        self.shared_git_env: dict[str, str] | None = None
        self.shared_checkpoint: Callable[[], object] | None = None

    def _environment(self) -> dict[str, str]:
        # Do not let another workspace or session redirect this store.
        from .shared import git_environment
        env = {key: value for key, value in git_environment().items()
               if not key.startswith(("BEADS_", "BD_", "DOLT_", "GT_")) and key != "CLAUDE_SESSION_ID"}
        if self.shared_git_env is not None:
            env.update({key: value for key, value in self.shared_git_env.items() if key.startswith("GIT_")})
        if "GIT_SSH_COMMAND" not in env:
            env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"
        env.update({"BEADS_DIR": str(self.beads_dir), "BD_NO_REMOTE_ADOPT": "1",
                    "BD_DISABLE_METRICS": "1", "BD_DISABLE_EVENT_FLUSH": "1",
                    "BD_IMPORT_AUTO": "false", "BD_LAST_TOUCHED_FALLBACK": "0",
                    "BEADS_DB": "", "BD_DB": "", "BEADS_DOLT_SERVER_DATABASE": "",
                    "BEADS_DOLT_SERVER_MODE": "0", "BEADS_DOLT_SHARED_SERVER": "0",
                    "BD_DOLT_SHARED_SERVER": "false", "NO_COLOR": "1"})
        return env

    def _check_layout(self) -> None:
        if not self.beads_dir.is_dir():
            raise BeadsError("Beads directory does not exist; initialize the selected workspace first")
        redirect = self.beads_dir / "redirect"
        if redirect.exists() or redirect.is_symlink():
            raise BeadsError("Beads redirects are not supported; select the actual local store directory")
        metadata = self.beads_dir / "metadata.json"
        try:
            if metadata.is_symlink():
                raise BeadsError("Beads metadata must be a local file, not a symbolic link")
            data = json.loads(metadata.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise BeadsError("Cannot read local Beads metadata; initialize the selected store with bd 1.3.4") from exc
        if not isinstance(data, dict) or data.get("backend") != "dolt" or data.get("dolt_mode") != "embedded":
            raise BeadsError("Plan supports only a local embedded Dolt store; server and proxy layouts are not supported")
        if data.get("database") != "dolt" or data.get("dolt_data_dir"):
            raise BeadsError("Beads database path aliases and custom data directories are not supported")
        for name in ("embeddeddolt", "dolt"):
            if not (self.beads_dir / name).resolve().is_relative_to(self.beads_dir):
                raise BeadsError("Beads data directory must stay inside the selected store")

    def validate_local(self) -> None:
        """Check the layout and pinned tool before the caller creates a lock."""
        self._check_layout()
        try:
            result = subprocess.run([self.binary, "--version"], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=self.timeout,
                                    cwd=self.beads_dir.parent, env=self._environment(), check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BeadsError("Cannot check Beads version; install the pinned bd 1.3.4 release") from exc
        if result.returncode or result.stdout.strip() != "bd version 1.3.4 (7ef2fd05e)":
            raise BeadsError("Plan requires bd 1.3.4 (7ef2fd05e); no store command was run")

    def _run(self, *args: str, stdin: str | None = None, jsonl: bool = False):
        self._check_layout()
        command = [self.binary, "--sandbox", "--json", "--actor", self.actor,
                   "--dolt-auto-commit=on", *args]
        try:
            if getattr(self, "shared_active", False):
                from .shared import capture
                result = capture(command, stdin=stdin, cwd=self.beads_dir.parent,
                                 env=self._environment(), timeout=self.timeout)
            else:
                result = subprocess.run(command, input=stdin, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace", timeout=self.timeout,
                                        cwd=self.beads_dir.parent, env=self._environment(), check=False)
        except subprocess.TimeoutExpired as exc:
            raise BeadsError(f"bd {args[0]} exceeded {self.timeout:g} seconds; check the store before retrying") from exc
        except OSError as exc:
            raise BeadsError(f"Cannot run Beads: {str(exc)[:600]}") from exc
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()[:1200]
            raise BeadsError(f"bd {args[0]} failed (exit {result.returncode}): {detail}")
        try:
            if jsonl:
                data = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            else:
                data = json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise BeadsError(f"bd {args[0]} returned invalid JSON") from exc
        if args[0] in {"create", "update", "import", "batch"} and self.shared_checkpoint is not None:
            self.shared_checkpoint()
        return data

    @staticmethod
    def _id(value: object) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
            raise BeadsError("Invalid Beads issue ID")
        return value

    @staticmethod
    def _object(value, operation: str) -> dict:
        if not isinstance(value, dict):
            raise BeadsError(f"bd {operation} did not return an object")
        return value

    @staticmethod
    def _list(value, operation: str) -> list[dict]:
        # bd emits null for some empty result sets.
        if value is None:
            return []
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise BeadsError(f"bd {operation} did not return an issue list")
        return value

    def info(self) -> dict:
        return self._object(self._run("info", "--schema"), "info")

    def _shared_command(self, *args, json_result=True):
        from .shared import capture
        self._check_layout()
        command = [self.binary, "--sandbox", "--json", "--actor", self.actor,
                   "--dolt-auto-commit=on", *args]
        result = capture(command, cwd=self.beads_dir.parent, env=self._environment(), timeout=self.timeout)
        if result.returncode:
            raise BeadsError("shared Beads command failed; its effect was not confirmed; retain the gate")
        if not json_result:
            return result.stdout
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise BeadsError("shared Beads command returned invalid JSON; retain the gate") from exc

    def shared_remote(self, name: str, url: str, *, add=False):
        remotes = self._list(self._shared_command("dolt", "remote", "list"), "remote list")
        selected = [row for row in remotes if row.get("name") == name]
        if not selected and add and not remotes:
            self._shared_command("dolt", "remote", "add", name, url)
            return self.shared_remote(name, url)
        if (len(selected) != 1 or selected[0].get("url") != url or selected[0].get("sql_url") != url
                or selected[0].get("status") != "ok"):
            raise BeadsError("Beads must use the same Git remote as the Plan gate; no remote was changed")

    def shared_clean(self):
        # The pinned embedded API supports WORKING here even though SQL and
        # dirty-table status are unavailable. Detect issue-row metadata too.
        raw = self._shared_command("diff", "HEAD", "WORKING", json_result=False)
        # Pinned bd prints this text instead of JSON for an empty diff.
        if raw.strip() == "No changes between HEAD and WORKING":
            return
        try:
            changes = self._list(json.loads(raw), "diff")
        except ValueError as exc:
            raise BeadsError("Beads did not confirm a clean working set") from exc
        if changes:
            raise BeadsError("Beads has uncommitted issue changes; no shared sync was started")

    def shared_sync(self, remote: str, *, initial=False):
        if initial:
            self._shared_command("dolt", "push", "--no-adopt", "--remote=" + remote, json_result=False)
            return
        result = self._shared_command("sync", "--no-adopt", "--remote=" + remote, "--attempts=1")
        if not isinstance(result, dict) or result.get("status") != "ok" or result.get("pushed") is not True:
            raise BeadsError("Beads did not confirm shared publication; retain the gate")

    def shared_storage_digest(self):
        """Detect any local storage change since the last confirmed operation.

        Embedded bd has no SQL or dirty-table read. A byte digest is deliberately
        strict: even a history-only change requires a stopped-owner review.
        """
        self._check_layout()
        paths = [self.beads_dir / name for name in ("metadata.json", "config.yaml", "config.local.yaml")]
        for directory in (self.beads_dir / "embeddeddolt", self.beads_dir / "dolt"):
            if directory.exists():
                paths.extend(directory.rglob("*"))
        digest = hashlib.sha256()
        count = 0
        for path in sorted(paths):
            if path.is_symlink():
                raise BeadsError("shared Beads storage cannot contain symbolic links")
            if not path.is_file() or path.name in {"LOCK", ".lock"} or "temptf" in path.parts:
                continue
            count += 1
            digest.update(str(path.relative_to(self.beads_dir)).encode() + b"\0")
            before = path.stat()
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise BeadsError("Beads storage changed during the shared baseline check")
        if not count:
            raise BeadsError("shared Beads storage has no native state")
        return digest.hexdigest()

    def shared_remote_digest(self, url: str):
        """Read published issue data through a fresh, separate native clone."""
        from .shared import capture, issue_digest
        with tempfile.TemporaryDirectory(prefix="plan-remote-read-") as temporary:
            root = Path(temporary)
            env = self._environment()
            # Scratch init makes local-only setup commits. Keep an App identity
            # when present; use this fallback only when no session identity exists.
            for key, value in {"GIT_AUTHOR_NAME": "Plan", "GIT_AUTHOR_EMAIL": "plan@example.invalid",
                               "GIT_COMMITTER_NAME": "Plan", "GIT_COMMITTER_EMAIL": "plan@example.invalid"}.items():
                env.setdefault(key, value)
            result = capture(["git", "-c", "core.hooksPath=/dev/null", "init", "-q", str(root)],
                             cwd=root, env=env, timeout=self.timeout)
            if result.returncode:
                raise BeadsError("cannot prepare an independent remote read; retain the gate")
            other = Beads(root / ".beads", binary=self.binary, actor=self.actor, timeout=self.timeout)
            env = other._environment() | {key: value for key, value in env.items() if key.startswith("GIT_")}
            # init --remote clones the native data. It does not run sync or push.
            result = capture([self.binary, "--sandbox", "--actor", self.actor, "init", "--skip-hooks",
                              "--skip-agents", "--non-interactive", "--remote=" + url],
                             cwd=root, env=env, timeout=self.timeout)
            if result.returncode:
                raise BeadsError("cannot independently read the published Beads data; retain the gate")
            return issue_digest(other.issues())

    def deterministic_id(self, key: str) -> str:
        """Make a repeat-safe ID with the prefix of the selected database."""
        info = self.info()
        prefix = info.get("schema", {}).get("config", {}).get("issue_prefix")
        if not isinstance(prefix, str) or not prefix:
            raise BeadsError("Beads did not report its issue prefix")
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
        return self._id(f"{prefix}-plan{digest}")

    def issues(self) -> list[dict]:
        # Export bulk-loads full outgoing edges. Its owner filters cannot be
        # disabled, so compare IDs with the unfiltered list before using it.
        exported = self._list(self._run("export", "--all", "--no-memories", jsonl=True), "export")
        listed = self._list(self._run("list", "--all", "--limit=0", "--include-infra",
                                      "--include-gates", "--include-templates", "--include-ephemeral"), "list")
        try:
            export_ids = {self._id(row["id"]) for row in exported}
            list_ids = {self._id(row["id"]) for row in listed}
        except KeyError as exc:
            raise BeadsError("Beads export or list returned an issue without an ID") from exc
        if export_ids != list_ids or len(export_ids) != len(exported) or len(list_ids) != len(listed):
            raise BeadsError("Beads export and list disagree; remove export owner filters or retry a changed store")
        for row in exported:
            edges = self._list(row.get("dependencies"), "export dependencies")
            if any(edge.get("issue_id") != row["id"] for edge in edges):
                raise BeadsError("Beads export returned a dependency for another source issue")
            row["dependencies"] = edges
        return exported

    def get(self, issue_id: str) -> dict:
        rows = self._list(self._run("show", self._id(issue_id)), "show")
        if len(rows) != 1 or rows[0].get("id") != issue_id:
            raise BeadsError("Beads did not return the requested issue")
        return rows[0]

    @staticmethod
    def _content_file(directory: Path, name: str, content: str) -> str:
        path = directory / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o600)
        return str(path)

    def _fields(self, fields: dict, *, create: bool, directory: Path) -> list[str]:
        mapping = {"title": "title", "description": "description", "issue_type": "type",
                   "priority": "priority", "status": "status", "assignee": "assignee",
                   "parent": "parent", "notes": "notes", "design": "design",
                   "acceptance_criteria": "acceptance", "external_ref": "external-ref",
                   "metadata": "metadata"}
        if create:
            mapping["id"] = "id"
        else:
            mapping.update({"if_status": "if-status", "if_assignee": "if-assignee"})
        booleans = set() if create else {"claim", "force_close"}
        unknown = fields.keys() - mapping.keys() - booleans - {"labels"}
        if unknown:
            raise BeadsError("Unsupported Beads fields: " + ", ".join(sorted(unknown)))
        if fields.get("force_close"):
            if fields.get("status") != "closed" or "assignee" in fields or "claim" in fields:
                raise BeadsError("force_close requires status=closed and no assignee or claim field")
        args = []
        for key, value in fields.items():
            if key in booleans:
                if not isinstance(value, bool):
                    raise BeadsError(f"Beads {key} must be true or false")
                if value:
                    args.append("--force" if key == "force_close" else "--" + key)
            elif key == "labels":
                if not isinstance(value, list) or any(not isinstance(label, str) or "," in label for label in value):
                    raise BeadsError("Beads labels must be a list of strings with no comma")
                args.append("--" + ("labels" if create else "set-labels") + "=" + ",".join(value))
            elif key == "metadata":
                if not isinstance(value, dict):
                    raise BeadsError("Beads metadata must be an object")
                content = json.dumps(value, ensure_ascii=False, allow_nan=False)
                args.append("--metadata=@" + self._content_file(directory, "metadata.json", content))
            elif key == "description":
                if not isinstance(value, str):
                    raise BeadsError("Beads description must be text")
                args.append("--body-file=" + self._content_file(directory, "description.txt", value))
                if not value:
                    args.append("--allow-empty-description")
            else:
                if key in {"id", "parent"} and value:
                    self._id(value)
                if not isinstance(value, (str, int)) or isinstance(value, bool):
                    raise BeadsError(f"Invalid value for Beads {key}")
                args.append("--" + mapping[key] + "=" + str(value))
        return args

    def create(self, issue: dict) -> dict:
        with tempfile.TemporaryDirectory(prefix="plan-beads-") as directory:
            args = self._fields(issue, create=True, directory=Path(directory))
            return self._object(self._run("create", *args), "create")

    def update(self, issue_id: str, fields: dict) -> dict:
        issue_id = self._id(issue_id)
        fields = dict(fields)
        if "id" in fields and fields.pop("id") != issue_id:
            raise BeadsError("Beads update ID does not match the requested issue")
        if not fields:
            raise BeadsError("A Beads update needs at least one field")
        with tempfile.TemporaryDirectory(prefix="plan-beads-") as directory:
            args = self._fields(fields, create=False, directory=Path(directory))
            result = self._run("update", issue_id, *args)
        rows = self._list(result, "update")
        if len(rows) != 1 or rows[0].get("id") != issue_id:
            raise BeadsError("Beads did not return the updated issue")
        return rows[0]

    def import_issues(self, issues: list[dict]) -> dict:
        """Import JSONL. Beads can commit a partial import; callers must preflight."""
        if not isinstance(issues, list) or any(not isinstance(row, dict) for row in issues):
            raise BeadsError("Beads import needs a list of issue objects")
        data = "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in issues)
        return self._object(self._run("import", "-", stdin=data), "import")

    def dependencies(self, issue_id: str) -> list[dict]:
        rows = self._list(self._run("dep", "list", self._id(issue_id), "--direction=down"), "dep list")
        try:
            # Native dep list returns target issues, not the export edge shape.
            return [{"issue_id": issue_id, "depends_on_id": self._id(row["id"]),
                     "type": row["dependency_type"]} for row in rows]
        except KeyError as exc:
            raise BeadsError("bd dep list returned an invalid dependency") from exc

    def set_dependencies(self, issue_id: str, desired: list[dict]) -> None:
        """Replace outgoing edges in one native Beads batch transaction."""
        issue_id = self._id(issue_id)
        edges = set()
        targets = set()
        for edge in desired:
            target = self._id(edge.get("depends_on_id"))
            kind = edge.get("type", "blocks")
            if not isinstance(kind, str) or not re.fullmatch(r"[a-z][a-z-]*", kind):
                raise BeadsError("Invalid Beads dependency type")
            if target in targets:
                raise BeadsError("Each Beads dependency target must occur once")
            targets.add(target)
            edges.add((target, kind))
        current = {(self._id(edge["depends_on_id"]), edge["type"])
                   for edge in self.dependencies(issue_id)}
        lines = [f"dep remove {issue_id} {target}" for target, _ in sorted(current - edges)]
        lines += [f"dep add {issue_id} {target} {kind}" for target, kind in sorted(edges - current)]
        if lines:
            self._object(self._run("batch", stdin="\n".join(lines) + "\n"), "batch")
