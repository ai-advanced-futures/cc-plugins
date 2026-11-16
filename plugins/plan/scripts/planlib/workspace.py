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
from .beads import Beads
from .shared import COORDINATION_REF, DATA_REF, GitGate, SharedCommandError, atomic_json, issue_digest

SHARING = {"protocol": 1, "coordination_ref": COORDINATION_REF, "data_ref": DATA_REF}


@contextmanager
def store_lock(beads_dir: Path, timeout: float = 20):
    """Aliases of the same resolved workspace share one process lock."""
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
                    raise PlanError("workspace is busy; no operation started")
                time.sleep(0.05)
        yield
    finally:
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
        if profile.is_symlink():
            raise PlanError("workspace profile cannot be a symbolic link")
        self.profile = profile.resolve()
        try:
            self.config = json.loads(self.profile.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PlanError("cannot read workspace profile; run plan setup with an explicit profile") from exc
        required = {"schema_version", "workspace_id", "control_id", "beads_dir", "source_root"}
        version = self.config.get("schema_version") if isinstance(self.config, dict) else None
        if type(version) is not int or version not in {1, 2}:
            raise PlanError("unsupported workspace profile format")
        self.shared = version == 2
        expected = required | ({"sharing"} if self.shared else set())
        if set(self.config) != expected:
            raise PlanError("unsupported workspace profile format")
        if self.shared:
            sharing = self.config["sharing"]
            if (not isinstance(sharing, dict) or set(sharing) != {"remote", *SHARING}
                    or any(sharing.get(key) != val for key, val in SHARING.items())
                    or type(sharing.get("protocol")) is not int
                    or not isinstance(sharing.get("remote"), str)
                    or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", sharing["remote"])):
                raise PlanError("unsupported shared workspace profile")
        for field in required - {"schema_version"}:
            if not isinstance(self.config[field], str) or not self.config[field]:
                raise PlanError(f"workspace profile has an invalid {field}")
        if self.shared and any(not Path(self.config[key]).is_absolute() for key in ("beads_dir", "source_root")):
            raise PlanError("shared workspace paths must be absolute")
        self.beads_dir = Path(self.config["beads_dir"]).resolve()
        self.source_root = Path(self.config["source_root"]).resolve()
        if not self.beads_dir.is_dir() or not self.source_root.is_dir():
            raise PlanError("workspace store or source root is missing; no fallback was selected")
        self.id = self.config["workspace_id"]
        self.control_id = self.config["control_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]+", self.control_id):
            raise PlanError("workspace control ID is invalid")
        self.backend = Beads(self.beads_dir, binary=binary, actor=actor)
        self.actor = actor
        self.operation, self.request_id = operation, request_id
        self._shared_gate = None
        self.backend.shared_active = self.shared

    @classmethod
    def setup(cls, profile: Path, beads_dir: Path, source_root: Path, binary: str = "bd", *,
              shared: bool = False, remote: str = "origin") -> dict:
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
            if shared and (not existing.shared or existing.config["sharing"]["remote"] != remote):
                raise PlanError("existing profile is not this shared workspace; enable share explicitly first")
            with existing.lock():
                existing.control()
            return existing.config
        backend = Beads(beads_dir, binary=binary, actor="agent:plan-setup")
        backend.validate_local()
        if shared:
            return cls._join(profile, beads_dir, source_root, binary, backend, remote)
        with store_lock(beads_dir):
            if (beads_dir / "plan-shared-attempt.json").exists():
                raise PlanError("a shared attempt is incomplete; local setup cannot bypass its gate")
            backend.info()
            controls = [issue for issue in backend.issues() if "plan_workspace" in _metadata(issue)]
            if len(controls) > 1:
                raise PlanError("multiple Plan workspace controls exist; selection is ambiguous")
            if controls:
                control = controls[0]
                data = _metadata(control)["plan_workspace"]
                if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("id"), str):
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
    def _join(cls, profile, beads_dir, source_root, binary, backend, remote):
        with store_lock(beads_dir):
            gate = GitGate(source_root, remote, actor="agent:plan-setup", operation="join", state_dir=beads_dir)
            state = gate.observe()
            if state is None or state["status"] != "unlocked":
                raise PlanError("shared workspace has no available published control; no independent Plan was created")
            backend.shared_active = True
            backend.shared_git_env = gate.env
            backend.shared_clean()
            backend.shared_remote(remote, gate.transport_url, add=True)
            # Joining is permitted only from the already cloned published data.
            # Never merge a separately initialized Plan control into this store.
            if issue_digest(backend.issues()) != state["digest"]:
                raise PlanError("join needs an exact clone of the published Beads data; no local data was merged")
            config = {"schema_version": 2, "workspace_id": state["workspace_id"], "control_id": state["control_id"],
                      "beads_dir": str(beads_dir), "source_root": str(source_root), "sharing": {**SHARING, "remote": remote}}
            # Save the verified clone and profile before acquiring shared ownership,
            # so a failed join has the same recovery path as every shared operation.
            atomic_json(beads_dir / "plan-shared-baseline.json",
                        {"workspace_id": state["workspace_id"], "control_id": state["control_id"],
                         "storage_digest": backend.shared_storage_digest(), "digest": state["digest"],
                         "published_data_ref": state["published_data_ref"]})
            _write_profile(profile, config)
        workspace = cls(profile, binary=binary, actor="agent:plan-setup", operation="join")
        with workspace.lock():
            workspace.records()
        return config

    def _gate(self, remote=None, operation=None):
        gate = GitGate(self.source_root, remote or self.config["sharing"]["remote"], self.id, self.control_id,
                       actor=self.actor, operation=operation or self.operation, request_id=self.request_id,
                       state_dir=self.beads_dir, timeout=self.backend.timeout if hasattr(self.backend, "timeout") else 60)
        self.backend.shared_git_env = gate.env
        return gate

    @property
    def _baseline_path(self):
        return self.beads_dir / "plan-shared-baseline.json"

    def _check_local_baseline(self):
        attempt = self.beads_dir / "plan-shared-attempt.json"
        if attempt.exists() or attempt.is_symlink():
            raise PlanError("an earlier shared attempt has an unknown outcome; retain its token; no automatic recovery")
        try:
            if self._baseline_path.is_symlink():
                raise PlanError("shared baseline cannot be a symbolic link")
            baseline = json.loads(self._baseline_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PlanError("shared local baseline is missing or invalid; no automatic recovery") from exc
        expected = {"workspace_id", "control_id", "storage_digest", "digest", "published_data_ref"}
        if not isinstance(baseline, dict) or set(baseline) != expected or baseline["workspace_id"] != self.id or baseline["control_id"] != self.control_id:
            raise PlanError("shared local baseline belongs to another workspace")
        if self.backend.shared_storage_digest() != baseline["storage_digest"]:
            raise PlanError("local Beads state has unowned, dirty, or incomplete changes; no sync or automatic recovery")

    def _checkpoint(self):
        gate = self._shared_gate
        if gate is None:
            raise PlanError("shared checkpoint has no owned gate")
        digest = issue_digest(self.backend.issues())
        owned = {"digest": digest, "storage_digest": self.backend.shared_storage_digest()}
        gate.save_attempt(owned_local=owned)
        return owned

    def _note_publication(self, gate, digest, previous_ref, *, initial=False, phase="publishing"):
        self._checkpoint()
        gate.save_attempt(phase=phase, publication={"expected_digest": digest, "previous_ref": previous_ref,
                                                   "initial": initial})

    def _record_baseline(self, gate, published, digest):
        owned = self._checkpoint()
        atomic_json(self._baseline_path, {"workspace_id": self.id, "control_id": self.control_id,
                                         "storage_digest": owned["storage_digest"], "digest": digest,
                                         "published_data_ref": published})

    def _release_unchanged(self, gate, before, published):
        # Release only a local validation refusal, never an unknown command.
        # The file digest includes native history and the entire working set.
        if self.backend.shared_storage_digest() != before["storage_digest"] or gate.remote_ref(DATA_REF) != published:
            return False
        self.backend.shared_clean()
        if issue_digest(self.backend.issues()) != before["digest"]:
            return False
        if self.backend.shared_remote_digest(gate.transport_url) != before["digest"] or gate.remote_ref(DATA_REF) != published:
            return False
        gate.check_owner()
        self._record_baseline(gate, published, before["digest"])
        gate.release(published, before["digest"])
        return True

    def _publish(self, gate, *, initial=False):
        gate.check_owner()
        self.backend.shared_clean()
        expected = issue_digest(self.backend.issues())
        before = gate.remote_ref(DATA_REF)
        if not initial and before != gate.state["published_data_ref"]:
            raise PlanError("shared data changed outside its gate; no publication started")
        self._note_publication(gate, expected, before, initial=initial)
        self.backend.shared_sync(gate.remote, initial=initial)
        if issue_digest(self.backend.issues()) != expected:
            raise PlanError("shared sync changed the operation result; outcome is not confirmed; retain the gate")
        self._checkpoint()
        published = gate.remote_ref(DATA_REF)
        if not published:
            raise PlanError("shared publication has no data ref; retain the gate")
        if self.backend.shared_remote_digest(gate.transport_url) != expected:
            raise PlanError("published Beads data does not match the operation; retain the gate")
        if gate.remote_ref(DATA_REF) != published:
            raise PlanError("published Beads data changed during verification; retain the gate")
        gate.check_owner()
        self._record_baseline(gate, published, expected)
        gate.release(published, expected)

    def share(self, *, remote="origin", paused=False, upgraded=False):
        if paused is not True or upgraded is not True:
            raise PlanError("share requires all writers paused and all participating machines upgraded")
        if self.shared:
            raise PlanError("workspace is already shared; no second workspace was created")
        with store_lock(self.beads_dir):
            if (self.beads_dir / "plan-shared-attempt.json").exists():
                raise PlanError("an earlier share attempt is incomplete; use recover after its writer stops")
            self.backend.validate_local()
            self.backend.shared_clean()
            self.records()
            gate = self._gate(remote, "share")
            # Check local remote configuration before any shared gate is created.
            self.backend.shared_remote(remote, gate.transport_url, add=True)
            published = gate.remote_ref(DATA_REF)
            digest = issue_digest(self.backend.issues())
            if published is not None and self.backend.shared_remote_digest(gate.transport_url) != digest:
                raise PlanError("existing remote Beads data differs from this local workspace; no gate was acquired")
            # This checkpoint also covers a lost acquire reply with a schema 1 profile.
            atomic_json(self._baseline_path, {"workspace_id": self.id, "control_id": self.control_id,
                                             "storage_digest": self.backend.shared_storage_digest(),
                                             "digest": digest, "published_data_ref": published})
            gate.acquire(bootstrap=True)
            self.backend.shared_active = True
            self._shared_gate = gate
            self.backend.shared_checkpoint = self._checkpoint
            try:
                if gate.state["observed_data_ref"] != published:
                    raise PlanError("remote data changed during share preparation; retain the gate")
                gate.state["published_data_ref"] = published
                self._note_publication(gate, digest, published, initial=published is None, phase="operation")
                self._upgrade_shared_profile(gate)
                self._publish(gate, initial=published is None)
            finally:
                self.backend.shared_checkpoint = None
                self._shared_gate = None
            return self.config

    def _upgrade_shared_profile(self, gate):
        """Complete the owned local upgrade, including a stopped first share."""
        control = _metadata(self.backend.get(self.control_id)).get("plan_workspace")
        if (not isinstance(control, dict) or control.get("id") != self.id
                or type(control.get("schema_version")) is not int
                or control["schema_version"] not in {1, 2}
                or (control["schema_version"] == 2 and control.get("sharing") != SHARING)):
            raise PlanError("share recovery found an unsupported workspace control")
        if control["schema_version"] == 1:
            control.update({"schema_version": 2, "sharing": dict(SHARING)})
            self.backend.update(self.control_id, {"metadata": {"plan_workspace": control}})
        config = {**self.config, "schema_version": 2, "sharing": {**SHARING, "remote": gate.remote}}
        atomic_json(self.profile, config)
        self.config, self.shared = config, True
        self.control()

    @contextmanager
    def lock(self):
        if not self.shared:
            self.backend.validate_local()
            with store_lock(self.beads_dir):
                if (self.beads_dir / "plan-shared-attempt.json").exists():
                    raise PlanError("a shared attempt is incomplete; local operations cannot bypass its gate")
                yield
            return
        if self._shared_gate is not None:
            raise PlanError("nested shared workspace operations are not supported")
        with store_lock(self.beads_dir):
            # This runs before even version/info reads can open the native store.
            self._check_local_baseline()
            self.backend.validate_local()
            gate = self._gate()
            gate.acquire()
            self._shared_gate = gate
            self.backend.shared_checkpoint = self._checkpoint
            try:
                self._checkpoint()
                self.backend.shared_remote(gate.remote, gate.transport_url)
                if gate.remote_ref(DATA_REF) != gate.state["published_data_ref"]:
                    raise PlanError("shared data changed outside its gate; retain the gate")
                self._note_publication(gate, gate.state["digest"], gate.state["published_data_ref"], phase="read-sync")
                self.backend.shared_sync(gate.remote)
                if issue_digest(self.backend.issues()) != gate.state["digest"]:
                    raise PlanError("shared read is stale, diverged, or changed outside Plan; retain the gate")
                self._checkpoint()
                # Fresh remote export is required before the authoritative read.
                published = gate.remote_ref(DATA_REF)
                if self.backend.shared_remote_digest(gate.transport_url) != gate.state["digest"] or gate.remote_ref(DATA_REF) != published:
                    raise PlanError("cannot confirm the remote read baseline; retain the gate")
                gate.state["published_data_ref"] = published
                before = self._checkpoint()
                gate.save_attempt(phase="operation", publication={"expected_digest": before["digest"],
                                                                  "previous_ref": published, "initial": False})
                try:
                    yield
                except SharedCommandError:
                    raise
                except PlanError as exc:
                    if not self._release_unchanged(gate, before, published):
                        raise PlanError(str(exc) + "; state changed or was not confirmed; gate retained") from exc
                    raise
                else:
                    self._publish(gate)
            finally:
                # Unknown commands and changed data keep the durable owner token.
                self.backend.shared_checkpoint = None
                self._shared_gate = None

    def _initial_remote_baseline_matches(self, journal, published, digest):
        if journal["operation"] != "share" or journal["gate_state"]["digest"] is not None:
            return False
        try:
            if self._baseline_path.is_symlink():
                raise PlanError("initial sharing baseline cannot be a symbolic link")
            baseline = json.loads(self._baseline_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PlanError("initial sharing baseline is missing or invalid; retain the gate") from exc
        return (isinstance(baseline, dict)
                and set(baseline) == {"workspace_id", "control_id", "storage_digest", "digest", "published_data_ref"}
                and baseline["workspace_id"] == self.id and baseline["control_id"] == self.control_id
                and baseline["published_data_ref"] == published == journal["gate_state"]["observed_data_ref"]
                and journal["publication"]["previous_ref"] == published and baseline["digest"] == digest)

    def recover_shared(self, *, previous_writer_stopped=False) -> dict:
        """Resume only this machine's saved attempt after an operator stops it.

        Finish roadmap migration locally before share. This method refuses an
        incomplete import; it does not resume an import into a shared store.
        """
        if previous_writer_stopped is not True:
            raise PlanError("shared recovery requires explicit confirmation that the previous writer stopped")
        bootstrap = not self.shared
        if self._shared_gate is not None:
            raise PlanError("shared recovery cannot run inside another operation")
        with store_lock(self.beads_dir):
            remote = None
            if bootstrap:
                path = self.beads_dir / "plan-shared-attempt.json"
                try:
                    if path.is_symlink():
                        raise PlanError("shared recovery journal cannot be a symbolic link")
                    attempt = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    raise PlanError("shared recovery needs a schema 2 workspace or this machine's saved share attempt") from exc
                if (not isinstance(attempt, dict) or attempt.get("operation") != "share"
                        or not isinstance(attempt.get("remote"), str) or not attempt["remote"]):
                    raise PlanError("local recovery requires a saved initial share attempt")
                remote = attempt["remote"]
            gate = self._gate(remote=remote, operation="recover")
            current = gate.restore_attempt()
            journal = gate.journal
            if bootstrap and current["status"] != "locked":
                raise PlanError("local share recovery requires its original held gate")
            self.backend.shared_active = True
            receipt = {"actor": self.actor, "attempt": journal["attempt"], "operation": journal["operation"],
                       "previous_actor": journal["gate_state"]["actor"]}
            owned = journal["owned_local"]
            if owned is None and journal["phase"] == "acquiring":
                try:
                    if self._baseline_path.is_symlink():
                        raise PlanError("recovery baseline cannot be a symbolic link")
                    baseline = json.loads(self._baseline_path.read_text(encoding="utf-8"))
                    if baseline["workspace_id"] != self.id or baseline["control_id"] != self.control_id:
                        raise PlanError("recovery baseline belongs to another workspace")
                    if bootstrap and baseline["published_data_ref"] != current["observed_data_ref"]:
                        raise PlanError("share recovery baseline differs from the acquired data ref")
                    owned = {key: baseline[key] for key in ("digest", "storage_digest")}
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    raise PlanError("recovery has no confirmed local checkpoint; no gate was cleared") from exc
            if (not isinstance(owned, dict) or set(owned) != {"digest", "storage_digest"}
                    or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in owned.values())):
                raise PlanError("recovery local checkpoint is invalid; no gate was cleared")
            # Do not open bd before unknown local changes have been excluded.
            if self.backend.shared_storage_digest() != owned["storage_digest"]:
                raise PlanError("local state differs from the saved owned checkpoint; unknown changes cannot be recovered automatically")
            self.backend.validate_local()
            self.backend.shared_remote(gate.remote, gate.transport_url)
            self.backend.shared_clean()
            if issue_digest(self.backend.issues()) != owned["digest"]:
                raise PlanError("local recovery data does not match the owned checkpoint")
            publication = journal["publication"]
            if publication is None and journal["phase"] == "acquiring":
                publication = ({"expected_digest": owned["digest"], "previous_ref": current["observed_data_ref"],
                                "initial": current["observed_data_ref"] is None} if bootstrap else
                               {"expected_digest": current["digest"], "previous_ref": current["published_data_ref"], "initial": False})
            if (not isinstance(publication, dict) or set(publication) != {"expected_digest", "previous_ref", "initial"}
                    or not isinstance(publication["expected_digest"], str)
                    or not re.fullmatch(r"[0-9a-f]{64}", publication["expected_digest"])
                    or type(publication["initial"]) is not bool):
                raise PlanError("recovery publication intent is missing or invalid")
            previous = publication["previous_ref"]
            if previous is not None and (not isinstance(previous, str) or not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", previous)):
                raise PlanError("recovery publication baseline is invalid")
            if gate.unpublished_attempt:
                published = gate.remote_ref(DATA_REF)
                if (published != previous or (published is not None
                        and self.backend.shared_remote_digest(gate.transport_url) != publication["expected_digest"])):
                    raise PlanError("unpublished acquisition has a changed remote baseline; retain the local attempt")
                if (gate.remote_ref(DATA_REF) != published or gate.remote_ref(COORDINATION_REF) != gate.tip
                        or self.backend.shared_storage_digest() != owned["storage_digest"]):
                    raise PlanError("unpublished acquisition changed during verification; retain the local attempt")
                # No operation ran. Keep the local baseline and make no remote write.
                (self.beads_dir / "plan-shared-attempt.json").unlink()
                return {"recovered": [], "saved": "unchanged", "workspace_id": self.id,
                        "already_published": False, "not_acquired": True, "recovery": receipt}
            if gate.confirmed_release is not None:
                released = gate.confirmed_release
                if (released["digest"] != publication["expected_digest"] or released["digest"] != owned["digest"]
                        or self.backend.shared_storage_digest() != owned["storage_digest"]):
                    raise PlanError("confirmed release does not match the saved local publication")
                # Confirm only this past operation. Later owners keep their gate and data;
                # the next ordinary read synchronizes from that later shared state.
                atomic_json(self._baseline_path, {"workspace_id": self.id, "control_id": self.control_id,
                                                 "storage_digest": owned["storage_digest"], "digest": released["digest"],
                                                 "published_data_ref": released["published_data_ref"]})
                (self.beads_dir / "plan-shared-attempt.json").unlink()
                return {"recovered": [], "saved": "shared", "workspace_id": self.id,
                        "already_published": True, "recovery": receipt}
            published = gate.remote_ref(DATA_REF)
            if published is None:
                if not publication["initial"] or previous is not None or current["status"] != "locked":
                    raise PlanError("published Beads data is missing; no recovery push was started")
                remote_digest = None
            else:
                remote_digest = self.backend.shared_remote_digest(gate.transport_url)
                saved = journal["gate_state"]
                baseline_matches = published in {previous, saved["published_data_ref"]} and remote_digest == saved["digest"]
                if not baseline_matches and remote_digest != publication["expected_digest"]:
                    baseline_matches = self._initial_remote_baseline_matches(journal, published, remote_digest)
                if not baseline_matches and remote_digest != publication["expected_digest"]:
                    raise PlanError("remote data is neither the saved baseline nor the saved publication; no recovery push was started")
                if gate.remote_ref(DATA_REF) != published:
                    raise PlanError("remote data changed during recovery verification; retain the gate")
            self._shared_gate = gate
            try:
                gate.check_owner()
                self.backend.shared_checkpoint = self._checkpoint
                if bootstrap:
                    self._note_publication(gate, owned["digest"], published, initial=published is None, phase="operation")
                    self._upgrade_shared_profile(gate)
                elif journal["phase"] in {"acquiring", "read-sync"}:
                    if remote_digest is None:
                        raise PlanError("an incomplete shared bootstrap has no read baseline")
                    self._note_publication(gate, remote_digest, published, phase="read-sync")
                    self.backend.shared_sync(gate.remote)
                    if issue_digest(self.backend.issues()) != remote_digest:
                        raise PlanError("recovery sync did not restore the verified remote baseline")
                    published = gate.remote_ref(DATA_REF)
                    self._checkpoint()
                # Pending Plan projections can be completed, but an unfinished
                # import still needs its original source and is refused here.
                fixed = self.recover()
                self.records()
                gate.state["published_data_ref"] = published
                self._publish(gate, initial=published is None)
                return {"recovered": fixed, "saved": "shared", "workspace_id": self.id,
                        "already_published": False, "recovery": receipt}
            finally:
                self.backend.shared_checkpoint = None
                self._shared_gate = None

    def _require_gate(self):
        if self.shared and self._shared_gate is None:
            raise PlanError("shared Plan data must be read or changed inside workspace.lock()")

    def control(self) -> dict:
        self._require_gate()
        issue = self.backend.get(self.control_id)
        data = _metadata(issue).get("plan_workspace")
        version = 2 if self.shared else 1
        if (not isinstance(data, dict) or type(data.get("schema_version")) is not int
                or data.get("schema_version") != version or data.get("id") != self.id
                or (self.shared and (data.get("sharing") != SHARING
                                     or type(data["sharing"].get("protocol")) is not int))):
            raise PlanError("selected store identity or sharing schema does not match the profile; no fallback was selected")
        return copy.deepcopy(data)

    def save_control(self, data: dict) -> None:
        self._require_gate()
        self.backend.update(self.control_id, {"metadata": {"plan_workspace": data}})
        if self.control() != data:
            raise PlanError("workspace checkpoint did not match its read-back; outcome is not confirmed")

    def records(self, allow_incomplete: bool = False) -> list[dict]:
        control = self.control()
        importing = control.get("import_state")
        if not allow_incomplete and importing and importing.get("status") != "complete":
            raise PlanError("roadmap import is incomplete; resume the same migration before using this workspace")
        result = []
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
        self._require_gate()
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

        Caller holds the shared workspace lock. A failed projection remains
        visible as pending; no ordinary operation can treat it as accepted work.
        """
        self._require_gate()
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
        self._require_gate()
        records = records if isinstance(records, model.Records) else model.Records(records)
        self.backend.set_dependencies(record["native_id"], self.native_edges(record, records))
        self.check_edges(record, records, self.backend.dependencies(record["native_id"]))
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
        fixed = []
        for record in records:
            self.finish(record, records)
            fixed.append(record["id"])
        return fixed
