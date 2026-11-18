"""Explicit local workspace binding and serialized Beads record changes."""
from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from . import PlanError
from . import model
from .beads import Beads, BeadsError
from .proc import DATA_REF, CommandTimeout, atomic_json, capture, dolt_url, git_environment, scrub, scrub_url

UNSHARE = ("this workspace is from Plan shared mode, which Plan 0.3.0 removed; "
           "run `plan.py unshare --workspace PROFILE` one time")
# Files that shared mode left in the Beads directory.
LEFTOVERS = ("plan-shared-attempt.json", "plan-shared-baseline.json")
_PROFILE = {"schema_version", "workspace_id", "control_id", "beads_dir", "source_root"}
_REMOTE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
# The commands that change content. An automatic backup push follows only these.
# Claim, heartbeat, release, and expire change only the claim, so no push follows them.
CONTENT_OPERATIONS = frozenset({"new", "set", "body", "link", "unlink", "assign", "status", "recover",
                                "migrate", "github-configure", "github-apply"})
# The commands whose store writes make 1 Dolt commit at the end of the lock, not 1 commit for each write (PLAN-STORY-674).
DEFERRED_COMMIT_OPERATIONS = frozenset({"github-apply"})
PART_COMMIT_MESSAGE = "Plan github apply"


def backup_timeout() -> float:
    """Give the time limit of one backup push in seconds: PLAN_BACKUP_TIMEOUT, default 45 (below the 120-second wait for the store lock)."""
    try:
        value = float(os.environ.get("PLAN_BACKUP_TIMEOUT", ""))
    except ValueError:
        return 45.0
    return value if 0 < value <= 3600 else 45.0


def backup_retry() -> float:
    """Give the pause of the automatic push after a failed push in seconds: PLAN_BACKUP_RETRY, default 60.

    A remote that does not answer holds the store lock for the full push limit. Without the pause, each
    write of each session waits for that limit, and the sessions behind it stop with `workspace is busy`.
    """
    try:
        value = float(os.environ.get("PLAN_BACKUP_RETRY", ""))
    except ValueError:
        return 60.0
    return value if 0 <= value <= 3600 else 60.0


LOCK_MARGIN = 20.0  # the lock budget of a content write is this much below the lock wait of another session
MIN_PUSH_SECONDS = 10.0  # an automatic push with less time left in the lock budget is skipped
MAX_PAUSE = 3600.0  # the longest pause after failed pushes in a row
MAX_DOUBLINGS = 12  # the pause stops doubling here: 60 s * 2 ** 12 is above MAX_PAUSE, and `2 **` of a huge count would raise
MAX_FAILURES = 64  # the count of failed pushes in a row stops here, so a state file with a huge value stays safe (issue 3010)
SKIP_PREFIX = "push skipped: "  # the error of a skipped push starts with this; plan.py reads it to word its warning


def pause_after(failures: int) -> float:
    """The pause after `failures` failed pushes in a row: doubles from PLAN_BACKUP_RETRY, up to MAX_PAUSE (D-9251)."""
    if failures <= 0:
        return 0.0
    # The exponent is capped: `2 **` of 1024 or more makes a float that raises OverflowError (issue 3010).
    return min(backup_retry() * 2 ** min(failures - 1, MAX_DOUBLINGS), MAX_PAUSE)


def whole_seconds(value: float) -> str:
    """A time limit as whole seconds for the cause of a push, so the text has no 4 decimals."""
    return str(max(round(value), 1))


def lock_budget() -> float:
    """The longest time that a content write and its automatic push hold the store lock (PLAN-STORY-675, D-9251)."""
    return max(lock_timeout() - LOCK_MARGIN, 0.0)


def one_line(error: BaseException | str) -> str:
    return " ".join(scrub(str(error)).split())[:300]


def lock_timeout() -> float:
    """Give the wait for the store lock in seconds: PLAN_LOCK_TIMEOUT, default 120.

    One command holds the lock for some seconds on a large store, so the sessions of a team wait in a line.
    A wait of 20 seconds let only about 5 parallel commands pass on a store of 762 records.
    """
    try:
        value = float(os.environ.get("PLAN_LOCK_TIMEOUT", ""))
    except ValueError:
        return 120.0
    return value if 0 < value <= 3600 else 120.0


@contextmanager
def store_lock(beads_dir: Path, timeout: float | None = None):
    """Aliases of the same resolved workspace share one process lock."""
    if timeout is None:
        timeout = lock_timeout()
    path = beads_dir.resolve() / "plan.lock"
    if not beads_dir.is_dir():
        raise PlanError("selected Beads directory does not exist; initialize it explicitly first")
    if path.is_symlink():
        raise PlanError("workspace lock cannot be a symbolic link")
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    started = time.monotonic()
    try:
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() - started >= timeout:
                    # The first sentence is matched by `sofa-publish` (its word `busy`): keep it as it is.
                    raise PlanError("workspace is busy; no operation started. The store lock is held by another process;"
                                    " run lsof on the file plan.lock in the Beads directory to find it")
                time.sleep(0.05)
        yield descriptor
    finally:
        # Unlock first: it frees the lock for each process that holds the descriptor, so a normal end leaves no holder.
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _write_profile(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".plan-profile-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Existing profiles are checked by setup before this function runs.
        os.link(temporary, path)
    except FileExistsError as exc:
        raise PlanError("workspace profile already exists; it was not overwritten") from exc
    finally:
        Path(temporary).unlink(missing_ok=True)


def _metadata(issue: dict) -> dict:
    value = issue.get("metadata") or {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as exc:
            raise PlanError("Beads returned invalid metadata") from exc
    if not isinstance(value, dict):
        raise PlanError("Beads metadata must be an object")
    return value


class Workspace:
    def __init__(self, profile: Path, binary: str = "bd", actor: str = "agent:plan", *,
                 operation: str = "operation", request_id: str | None = None):
        self.profile, self.config = self._read_profile(profile)
        if self.config["schema_version"] != 1:
            raise PlanError(UNSHARE)
        self.beads_dir = Path(self.config["beads_dir"]).resolve()
        self.source_root = Path(self.config["source_root"]).resolve()
        if not self.beads_dir.is_dir() or not self.source_root.is_dir():
            raise PlanError("workspace store or source root is missing; no fallback was selected")
        self.id = self.config["workspace_id"]
        self.control_id = self.config["control_id"]
        self.backend = Beads(self.beads_dir, binary=binary, actor=actor)
        self.actor = actor
        self.operation, self.request_id = operation, request_id
        self._locked = False
        self._control = None
        self._wrote = False
        # The result of the automatic push of the last lock, or None when no push was due.
        self.backup_result = None
        # The result of the 1 Dolt commit at the end of a lock of a deferred-commit operation, or None when none was due.
        self.commit_result: dict | None = None

    @staticmethod
    def _read_profile(profile: Path) -> tuple[Path, dict]:
        """Read a profile. Schema 2 is the removed shared form; only unshare accepts it."""
        if profile.is_symlink():
            raise PlanError("workspace profile cannot be a symbolic link")
        profile = profile.resolve()
        try:
            config = json.loads(profile.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PlanError("cannot read workspace profile; run plan setup with an explicit profile") from exc
        version = config.get("schema_version") if isinstance(config, dict) else None
        if type(version) is not int or version not in {1, 2}:
            raise PlanError("unsupported workspace profile format")
        if set(config) - {"backup"} != _PROFILE | ({"sharing"} if version == 2 else set()):
            raise PlanError("unsupported workspace profile format")
        if "backup" in config:
            block = config["backup"]
            if (version != 1 or not isinstance(block, dict) or set(block) != {"remote", "auto"}
                    or type(block["auto"]) is not bool or not isinstance(block["remote"], str)
                    or not _REMOTE.fullmatch(block["remote"])):
                raise PlanError("workspace profile has an invalid backup block")
        for field in _PROFILE - {"schema_version"}:
            if not isinstance(config[field], str) or not config[field]:
                raise PlanError(f"workspace profile has an invalid {field}")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]+", config["control_id"]):
            raise PlanError("workspace control ID is invalid")
        return profile, config

    @classmethod
    def setup(cls, profile: Path, beads_dir: Path, source_root: Path, binary: str = "bd") -> dict:
        profile, beads_dir, source_root = profile.resolve(), beads_dir.resolve(), source_root.resolve()
        if not source_root.is_dir() or not beads_dir.is_dir():
            raise PlanError("source root and initialized Beads directory must exist")
        protected = (source_root / "docs/product").resolve()
        if profile.is_relative_to(protected) or beads_dir.is_relative_to(protected):
            raise PlanError("workspace files cannot be placed inside the read-only Product bundles")
        if profile.exists():
            existing = cls(profile, binary=binary)
            if existing.beads_dir != beads_dir or existing.source_root != source_root:
                raise PlanError("profile already selects another store or source; use a separate profile")
            with existing.lock():
                existing.control()
            return existing.config
        backend = Beads(beads_dir, binary=binary, actor="agent:plan-setup")
        backend.validate_local()
        with store_lock(beads_dir):
            backend.info()
            controls = [issue for issue in backend.issues() if "plan_workspace" in _metadata(issue)]
            if len(controls) > 1:
                raise PlanError("multiple Plan workspace controls exist; selection is ambiguous")
            if controls:
                control = controls[0]
                data = _metadata(control)["plan_workspace"]
                # A store from shared mode has schema 2. Setup binds it; unshare converts it.
                if (not isinstance(data, dict) or type(data.get("schema_version")) is not int
                        or data["schema_version"] not in {1, 2} or not isinstance(data.get("id"), str)):
                    raise PlanError("unsupported Plan workspace control")
            else:
                data = {"schema_version": 1, "id": uuid.uuid4().hex, "retired_ids": [], "import_state": None}
                control = backend.create({"title": "Plan workspace", "issue_type": "chore", "status": "open",
                                          "description": "Plan workspace identity and import checkpoints; not executable work.",
                                          "labels": ["plan:workspace"], "metadata": {"plan_workspace": data}})
            config = {"schema_version": 1, "workspace_id": data["id"], "control_id": control["id"],
                      "beads_dir": str(beads_dir), "source_root": str(source_root)}
            _write_profile(profile, config)
            return config

    @classmethod
    def unshare(cls, profile: Path, binary: str = "bd") -> dict:
        """Convert a profile and a store from the removed shared mode to local, one time.

        This makes no network call and no Git call. Each step is safe to repeat,
        so a stopped run converges on the next run.
        """
        profile, config = cls._read_profile(profile)
        beads_dir = Path(config["beads_dir"]).resolve()
        if not beads_dir.is_dir():
            raise PlanError("workspace store is missing; no fallback was selected")
        backend = Beads(beads_dir, binary=binary, actor="agent:plan-unshare")
        backend.validate_local()
        changed = []
        with store_lock(beads_dir):
            data = _metadata(backend.get(config["control_id"])).get("plan_workspace")
            if (not isinstance(data, dict) or data.get("id") != config["workspace_id"]
                    or type(data.get("schema_version")) is not int or data["schema_version"] not in {1, 2}):
                raise PlanError("selected store identity does not match the profile; nothing was changed")
            if data["schema_version"] != 1 or "sharing" in data:
                local = {key: value for key, value in data.items() if key != "sharing"}
                local["schema_version"] = 1
                backend.update(config["control_id"], {"metadata": {"plan_workspace": local}})
                if _metadata(backend.get(config["control_id"])).get("plan_workspace") != local:
                    raise PlanError("workspace control did not match its read-back; run unshare again")
                changed.append("control")
            if config["schema_version"] != 1:
                remote = config["sharing"].get("remote") if isinstance(config.get("sharing"), dict) else None
                config = {**{key: config[key] for key in _PROFILE}, "schema_version": 1}
                changed.append("profile")
                if isinstance(remote, str) and _REMOTE.fullmatch(remote):
                    # The shared remote becomes the backup remote, with the automatic push on.
                    config["backup"] = {"remote": remote, "auto": True}
                    changed.append("backup")
                atomic_json(profile, config)
            for name in LEFTOVERS:
                leftover = beads_dir / name
                if leftover.exists() or leftover.is_symlink():
                    leftover.unlink()
                    changed.append(name)
        return {"workspace_id": config["workspace_id"], "control_id": config["control_id"],
                "unshared": True, "changed": changed, "saved": "local"}

    @property
    def _state_path(self) -> Path:
        return self.profile.with_name(self.profile.stem + ".backup.json")

    def backup_state(self) -> dict:
        """Read the result of the last push from the state file beside the profile."""
        state = {"pending": False, "last_push_at": None, "last_error": None}
        try:
            saved = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return state
        if isinstance(saved, dict):
            state.update({key: saved[key] for key in state if key in saved})
        if isinstance(state["last_error"], str):
            # A state file of an older push can hold a secret: scrub at read too (issue 2994).
            state["last_error"] = one_line(state["last_error"])
        return state

    def _hidden(self) -> dict:
        """The 2 keys of the state file that `describe` does not show: `failed_at` and `failures`."""
        try:
            saved = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return {key: saved[key] for key in ("failed_at", "failures") if isinstance(saved, dict) and saved.get(key)}

    def _failed_at(self):
        """Give the time of the last failed push, or None."""
        return model.parse_time(self._hidden().get("failed_at"))

    def _failures(self) -> int:
        """Give the count of failed pushes in a row. A state file of 0.6.2 has `failed_at` and no count: 1 failure."""
        hidden = self._hidden()
        count = hidden.get("failures")
        if isinstance(count, int) and not isinstance(count, bool) and count > 0:
            return min(count, MAX_FAILURES)
        return 1 if hidden.get("failed_at") else 0

    def backup_status(self) -> dict:
        block = self.config.get("backup") or {}
        return {"remote": block.get("remote"), "auto": bool(block.get("auto")), **self.backup_state()}

    def _save_state(self, **changes) -> None:
        state = {**self.backup_state(), **self._hidden(), **changes}
        atomic_json(self._state_path, {key: value for key, value in state.items()
                                       if key not in {"failed_at", "failures"} or value})

    def _remote_url(self, remote: str, env: dict, timeout: float) -> tuple[str, bool]:
        """Give the address that Beads saved for the remote. Add the remote when Beads has none."""
        if not isinstance(remote, str) or not _REMOTE.fullmatch(remote):
            raise PlanError("backup remote name is invalid")
        url = self.backend.remotes(timeout=timeout).get(remote)
        added = url is None
        if added:
            # Beads has no remote of this name. Use the address of the same Git remote of the source.
            found = capture(["git", "-C", str(self.source_root), "remote", "get-url", "--all", remote],
                            cwd=self.source_root, env=env, timeout=timeout)
            rows = found.stdout.splitlines()
            if found.returncode or len(rows) != 1:
                raise PlanError("backup remote " + remote + " is not a Beads remote and not one Git remote of the source; nothing was pushed")
            url = dolt_url(rows[0])
            self.backend.add_remote(remote, url)
        if not isinstance(url, str) or not url.startswith("git+"):
            raise PlanError("backup needs a Git remote; nothing was pushed")
        return url, added

    def _push(self, remote: str, *, confirm: bool, limit: float | None = None) -> dict:
        """Commit and push one time, inside the time limit. The caller holds the lock."""
        limit = backup_timeout() if limit is None else limit
        deadline = time.monotonic() + limit

        def left() -> float:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CommandTimeout("backup reached its time limit; the push is not confirmed")
            return remaining
        tracked = (self.config.get("backup") or {}).get("remote") == remote
        try:
            env = git_environment()
            env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
            url, added = self._remote_url(remote, env, left())
            if tracked:
                # A push that stops without an answer stays visible as pending.
                self._save_state(pending=True)
            committed = self.backend.commit_pending(timeout=left())
            self.backend.push(remote, timeout=left())
            commit = None
            if confirm:
                # Read the pushed ref from the address that Beads saved.
                seen = capture(["git", "ls-remote", "--refs", url[4:], DATA_REF],
                               cwd=self.source_root, env=env, timeout=left())
                rows = [row.split() for row in seen.stdout.splitlines()]
                if seen.returncode or len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != DATA_REF:
                    raise PlanError("backup push was not confirmed; the remote has no readable " + DATA_REF)
                commit = rows[0][0]
        except (PlanError, BeadsError, OSError, ValueError) as exc:
            error = exc
            if isinstance(exc, CommandTimeout):
                # bd writes no error text before the stop, so Plan writes the cause (PLAN-STORY-675, E3).
                last = self.backup_state()["last_push_at"] or "none"
                error = PlanError(f"push reached its time limit of {whole_seconds(limit)} seconds; the last good push: {last}; "
                                  "a push of all the pending data can need more time: run backup --timeout SECONDS")
            if tracked:
                try:
                    self._save_state(pending=True, last_error=one_line(error), failed_at=model.timestamp(),
                                     failures=min(self._failures() + 1, MAX_FAILURES))
                except (PlanError, OSError):
                    pass
            if error is exc:
                raise
            raise error from exc
        if tracked:
            self._save_state(pending=False, last_push_at=model.timestamp(), last_error=None, failed_at=None,
                             failures=None)
        # The address of a remote can hold a user and a password (issue 2995). The user's own path stays.
        return {"remote": remote, "url": scrub_url(url), "remote_added": added, "committed": committed,
                "data_commit": commit}

    def backup(self, remote: str | None = None, timeout: float | None = None) -> dict:
        """Commit pending Dolt changes and push the data to one Git remote, one time."""
        remote = remote or (self.config.get("backup") or {}).get("remote")
        if not remote:
            raise PlanError("backup has no remote; give --remote NAME, or save one with backup --remote NAME --auto on")
        if not isinstance(remote, str) or not _REMOTE.fullmatch(remote):
            raise PlanError("backup remote name is invalid")
        with self.lock():
            self.control()
            # A manual push has its own limit (`--timeout`), and no lock budget: it is a step of a person.
            done = self._push(remote, confirm=True, limit=timeout)
        return {"workspace_id": self.id, "backed_up": True, "remote": remote, "url": done["url"],
                "remote_added": done["remote_added"], "committed": done["committed"], "data_ref": DATA_REF,
                "data_commit": done["data_commit"], "saved": "local"}

    def configure_backup(self, remote: str | None, auto: bool) -> dict:
        """Save the backup remote and the automatic push setting in the profile. No push."""
        remote = remote or (self.config.get("backup") or {}).get("remote")
        if remote is not None and (not isinstance(remote, str) or not _REMOTE.fullmatch(remote)):
            raise PlanError("backup remote name is invalid")
        if remote is None and auto:
            raise PlanError("backup has no remote; give --remote NAME with --auto on")
        with self.lock():
            self.control()
            if remote is not None:
                if auto:
                    env = git_environment()
                    self._remote_url(remote, env, self.backend.timeout)
                config = {**self.config, "backup": {"remote": remote, "auto": auto}}
                if config != self.config:
                    atomic_json(self.profile, config)
                    self.config = config
        return {"workspace_id": self.id, "configured": True, "backup": self.backup_status(), "saved": "local"}

    def _after_write(self, failed: bool) -> None:
        """Push after a content write when the profile says so. A failed push never fails the write."""
        block = self.config.get("backup")
        if not (self._wrote and self.operation in CONTENT_OPERATIONS and block and block["auto"]):
            return
        if failed:
            # The command stopped after a write. Record it; the next push sends it.
            try:
                self._save_state(pending=True)
            except (PlanError, OSError):
                pass
            return
        failed, failures = self._failed_at(), self._failures()
        pause = pause_after(failures)
        if failed is not None and 0 <= (model.utcnow() - failed).total_seconds() < pause:
            # Do not hold the lock for 1 more failure; a later push sends all the data.
            self._skipped(block, f"{failures} failed push(es) in a row, the last one less than "
                                 f"{pause:g} seconds ago; a later push sends the data")
            return
        budget = lock_budget()
        held = time.monotonic() - self._locked_at
        if budget - held < MIN_PUSH_SECONDS:
            # The write and its push must free the lock inside the wait of another session (PLAN-STORY-675).
            self._skipped(block, f"the write held the store lock for {held:.0f} seconds, and less than "
                                 f"{MIN_PUSH_SECONDS:g} seconds of the lock budget ({budget:g} seconds) are left; "
                                 "a later push sends the data")
            return
        try:
            self._push(block["remote"], confirm=False, limit=min(backup_timeout(), budget - held))
            self.backup_result = {"pushed": True, "remote": block["remote"]}
        except (PlanError, BeadsError, OSError, ValueError) as exc:
            self.backup_result = {"pushed": False, "remote": block["remote"], "error": one_line(exc),
                                  **self._stale()}

    def _stale(self) -> dict:
        """The 2 keys that make a stale backup visible in a write result (D-9251)."""
        state = self.backup_state()
        return {"pending": state["pending"], "last_push_at": state["last_push_at"]}

    def _skipped(self, block: dict, detail: str) -> None:
        """A skip is not a failed push: it saves `pending` only, and its error starts with SKIP_PREFIX."""
        try:
            self._save_state(pending=True)
        except (PlanError, OSError):
            pass
        self.backup_result = {"pushed": False, "remote": block["remote"], "error": SKIP_PREFIX + detail,
                              **self._stale()}

    @contextmanager
    def lock(self):
        """Serialize the sessions of this machine on one store."""
        self.backend.validate_local()
        with store_lock(self.beads_dir) as descriptor:
            leftover = self.beads_dir / LEFTOVERS[0]
            if leftover.exists() or leftover.is_symlink():
                raise PlanError(UNSHARE)
            self._locked, self._control, self._wrote = True, None, False
            self._locked_at = time.monotonic()  # the start of the lock budget (PLAN-STORY-675)
            # Each bd child holds the lock: it stays held until the last process of a stopped command ends.
            self.backend.lock_fd = descriptor
            deferred = self.operation in DEFERRED_COMMIT_OPERATIONS
            if deferred:
                self.backend.auto_commit = "off"
            try:
                yield
            except BaseException as exc:
                # An error commits the writes that the call made. A stop (an interrupt, an exit) ends at once: its writes
                # stay in the working set, and the next commit of any Plan command records them.
                if deferred and isinstance(exc, Exception):
                    self._commit_deferred()
                self._after_write(failed=True)
                raise
            else:
                if deferred:
                    self._commit_deferred()
                # The push runs inside the lock: bd lets 1 process use the store at a time, so a push outside the lock
                # would make the next call wait in bd, past its own limit (PLAN-STORY-675, E1 and E2).
                self._after_write(failed=False)
            finally:
                self._locked, self._control, self._wrote = False, None, False
                self.backend.lock_fd = None
                self.backend.auto_commit = "on"

    def _commit_deferred(self) -> None:
        """Make the 1 Dolt commit of a deferred-commit lock. A failed commit never fails the operation: each write is
        durable in the working set, and the next commit of any Plan command (or the backup push) records it."""
        self.commit_result = None
        self.backend.auto_commit = "on"  # the backup push after it runs as in each other command
        if not self._wrote:
            return
        try:
            self.commit_result = {"committed": self.backend.commit_pending(message=PART_COMMIT_MESSAGE)}
        except (PlanError, BeadsError, OSError, ValueError) as exc:
            self.commit_result = {"committed": False, "error": one_line(exc)}

    def control(self) -> dict:
        # Each Plan writer holds the store lock, so one read is valid until the lock ends.
        if self._locked and self._control is not None:
            return copy.deepcopy(self._control)
        issue = self.backend.get(self.control_id)
        data = _metadata(issue).get("plan_workspace")
        if isinstance(data, dict) and data.get("id") == self.id and (data.get("schema_version") == 2 or "sharing" in data):
            raise PlanError(UNSHARE)
        if (not isinstance(data, dict) or type(data.get("schema_version")) is not int
                or data.get("schema_version") != 1 or data.get("id") != self.id):
            raise PlanError("selected store identity does not match the profile; no fallback was selected")
        if self._locked:
            self._control = copy.deepcopy(data)
        return copy.deepcopy(data)

    def save_control(self, data: dict) -> None:
        self._control, self._wrote = None, True
        self.backend.update(self.control_id, {"metadata": {"plan_workspace": data}})
        if self.control() != data:
            raise PlanError("workspace checkpoint did not match its read-back; outcome is not confirmed")

    def records(self, allow_incomplete: bool = False, *, issues: list[dict] | None = None) -> list[dict]:
        """Read and check each record. `issues` is one store read that the caller made in the same lock."""
        control = self.control()
        importing = control.get("import_state")
        if not allow_incomplete and importing and importing.get("status") != "complete":
            raise PlanError("roadmap import is incomplete; resume the same migration before using this workspace")
        result = []
        if issues is None:
            issues = self.backend.issues()
        by_id = {issue["id"]: issue for issue in issues}
        for issue in issues:
            record = _metadata(issue).get("plan")
            if record is None:
                continue
            if not isinstance(record, dict) or record.get("schema_version") != 1 or record.get("workspace_id") != self.id:
                raise PlanError("a Plan record belongs to an unsupported or different workspace")
            record = copy.deepcopy(record)
            errors = model.shape_errors([record])
            if errors:
                raise PlanError("invalid Plan record: " + "; ".join(errors))
            record["native_id"] = issue["id"]
            if not allow_incomplete and record.get("pending"):
                raise PlanError(f"{record.get('id')}: a write is incomplete; run recover before further work")
            if not allow_incomplete:
                if different := self.field_differences(record, issue):
                    raise PlanError(f"{record.get('id')}: native {different[0]} differs from Plan data; use recover to restore the recorded projection")
            result.append(record)
        result = model.Records(sorted(result, key=lambda record: record["id"]))
        if not allow_incomplete:
            errors, _warnings = model.validate(result, control.get("retired_ids") or [])
            if errors:
                raise PlanError("workspace graph is invalid: " + "; ".join(errors))
            for record in result:
                self.check_edges(record, result, by_id[record["native_id"]].get("dependencies", []))
        return result

    def native_id(self, logical_id: str) -> str:
        # The workspace control was allocated by Beads, so it supplies the native
        # prefix rather than guessing that the caller's repository uses 'plan'.
        prefix, separator, _suffix = self.control_id.rpartition("-")
        if not separator or not prefix:
            raise PlanError("cannot determine the selected store's native ID prefix")
        token = hashlib.sha256((self.id + "\0" + logical_id).encode()).hexdigest()[:16]
        return prefix + "-" + token

    @staticmethod
    def projection(record: dict) -> dict:
        fields = record["fields"]
        kind = fields["type"]
        state = fields.get("state", "backlog")
        native_type = kind.lower() if kind in {*model.WORK_TYPES, "Milestone"} else "task"
        status = "closed" if state in model.CLOSED or fields.get("status") == "deprecated" else (
            "blocked" if state == "blocked" else "in_progress" if state in {"claimed", "in_progress", "in_review"} else "open")
        return {"title": fields["title"], "issue_type": native_type, "status": status,
                "assignee": fields.get("owner") or "", "description": record["body"]}

    def field_differences(self, record: dict, issue: dict) -> list[str]:
        return [field for field, wanted in self.projection(record).items()
                if (issue.get(field) or ("" if field in {"description", "assignee"} else None)) != wanted]

    def native_edges(self, record: dict, records: list[dict]) -> list[dict]:
        # Beads permits one edge per target and gives native blockers different
        # rules. Keep exact typed edges in Plan metadata, and a browseable native
        # hierarchy plus non-blocking links. Plan computes all readiness rules.
        targets = {}
        for relation, target in model.relations(record):
            if relation == "traces":
                continue
            other = model.resolve(records, target)
            native_id = other.get("native_id") or self.native_id(other["id"])
            if native_id not in targets or relation == "parent":
                targets[native_id] = "parent-child" if relation == "parent" else "related"
        return [{"depends_on_id": target, "type": kind} for target, kind in sorted(targets.items())]

    def _native(self, record: dict) -> dict:
        data = copy.deepcopy(record)
        data.pop("native_id", None)
        data["schema_version"] = 1
        data["workspace_id"] = self.id
        return {"id": record.get("native_id") or self.native_id(record["id"]), **self.projection(record),
                "metadata": {"plan": data}, "labels": ["plan:item", "plan:type:" + record["fields"]["type"].lower()]}

    def _update_native(self, native: dict) -> None:
        fields = {key: value for key, value in native.items() if key not in {"id", "labels"}}
        closing = fields.get("status") == "closed"
        if closing:
            fields.pop("status")
        self.backend.update(native["id"], fields)
        if closing:
            # Product permits parent completion with open children as a warning.
            # Never combine this close override with an ownership change.
            self.backend.update(native["id"], {"status": "closed", "force_close": True})

    def commit(self, record: dict, records: list[dict], event: dict, *, creating: bool = False) -> dict:
        """Save a recoverable intent, project its edges, then record completion.

        The caller holds the workspace lock. A failed projection remains
        visible as pending; no ordinary operation can treat it as accepted work.
        """
        self._wrote = True
        candidate = copy.deepcopy(record)
        candidate["revision"] = record.get("revision", 0) + 1
        candidate["pending"] = event
        candidate["schema_version"] = 1
        candidate["workspace_id"] = self.id
        candidate["native_id"] = record.get("native_id") or self.native_id(record["id"])
        native = self._native(candidate)
        if creating:
            self.backend.create(native)
        else:
            self._update_native(native)
        desired = [candidate if other["id"] == candidate["id"] else other for other in records]
        if creating:
            desired.append(candidate)
        return self.finish(candidate, desired)

    def edges_match(self, record: dict, records: list[dict], actual: list[dict]) -> bool:
        wanted = {(edge["depends_on_id"], edge["type"]) for edge in self.native_edges(record, records)}
        try:
            observed = {(edge["depends_on_id"], edge["type"]) for edge in actual}
        except (KeyError, TypeError) as exc:
            raise PlanError("Beads returned invalid relationships") from exc
        return observed == wanted

    def check_edges(self, record: dict, records: list[dict], actual: list[dict]) -> None:
        if not self.edges_match(record, records, actual):
            raise PlanError(f"{record['id']}: native relationships differ from Plan data; use recover to restore them")

    def finish(self, record: dict, records: list[dict]) -> dict:
        self._wrote = True
        records = records if isinstance(records, model.Records) else model.Records(records)
        unchanged = self.backend.set_dependencies(record["native_id"], self.native_edges(record, records))
        # After a change, read the edges again. Without a change, check the edges that Beads reported.
        actual = unchanged if unchanged is not None else self.backend.dependencies(record["native_id"])
        self.check_edges(record, records, actual)
        finished = copy.deepcopy(record)
        event = finished.pop("pending", None)
        if event:
            finished.setdefault("events", []).append(event)
        native = self._native(finished)
        self._update_native(native)
        observed_issue = self.backend.get(finished["native_id"])
        observed = _metadata(observed_issue).get("plan")
        expected = native["metadata"]["plan"]
        if different := self.field_differences(finished, observed_issue):
            raise PlanError(f"Beads read-back of {different[0]} did not match; outcome is not confirmed")
        if observed != expected:
            raise PlanError("Beads read-back did not match the operation; outcome is not confirmed")
        return finished

    def recover(self) -> list[str]:
        records = self.records(allow_incomplete=True)
        importing = self.control().get("import_state")
        if importing and importing.get("status") != "complete":
            raise PlanError("resume migrate --apply for an incomplete import; recover does not guess missing source data")
        by_id = {issue["id"]: issue for issue in self.backend.issues()}
        fixed = []
        for record in records:
            issue = by_id[record["native_id"]]
            # Repair only a record with an unfinished write or a changed native projection.
            if (record.get("pending") or self.field_differences(record, issue)
                    or not self.edges_match(record, records, issue.get("dependencies", []))):
                self.finish(record, records)
                fixed.append(record["id"])
        return fixed
