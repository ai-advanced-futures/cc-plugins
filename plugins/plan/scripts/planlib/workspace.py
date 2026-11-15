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
    def __init__(self, profile: Path, binary: str = "bd", actor: str = "agent:plan"):
        self.profile = profile.resolve()
        try:
            self.config = json.loads(self.profile.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PlanError("cannot read workspace profile; run plan setup with an explicit profile") from exc
        required = {"schema_version", "workspace_id", "control_id", "beads_dir", "source_root"}
        if not isinstance(self.config, dict) or set(self.config) != required or self.config.get("schema_version") != 1:
            raise PlanError("unsupported workspace profile format")
        for field in required - {"schema_version"}:
            if not isinstance(self.config[field], str) or not self.config[field]:
                raise PlanError(f"workspace profile has an invalid {field}")
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

    def lock(self):
        self.backend.validate_local()
        return store_lock(self.beads_dir)

    def control(self) -> dict:
        issue = self.backend.get(self.control_id)
        data = _metadata(issue).get("plan_workspace")
        if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("id") != self.id:
            raise PlanError("selected store identity does not match the profile; no fallback was selected")
        return copy.deepcopy(data)

    def save_control(self, data: dict) -> None:
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
