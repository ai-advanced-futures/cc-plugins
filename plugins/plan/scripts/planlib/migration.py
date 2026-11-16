"""Copy a fixed Product snapshot into an inactive Beads plan."""
from __future__ import annotations

import copy
import uuid
from collections import Counter

from . import PlanError, model


def content(record):
    return {key: copy.deepcopy(record[key]) for key in ("id", "path", "fields", "body")}


def preview(data, workspace=None):
    edges = Counter(relation for record in data["records"] for relation, _target in model.relations(record))
    mappings = []
    for record in data["records"]:
        mapping = {"source_id": record["id"], "source_path": record["path"], "plan_id": record["id"]}
        if workspace is not None:
            mapping["beads_id"] = workspace.native_id(record["id"])
        mappings.append(mapping)
    return {"mode": "preview", "fingerprint": data["fingerprint"], "source_revision": data["source_revision"],
            "records": len(data["records"]), "types": dict(Counter(model.record_type(r) for r in data["records"])),
            "relationships": dict(sorted(edges.items())), "retired_ids": data["retired_ids"],
            "mappings": mappings, "warnings": data["warnings"], "source_changed": False, "github_bindings": "inert"}


def apply(workspace, data, expected_fingerprint=None):
    if workspace.shared:
        raise PlanError("apply migration to an inactive local workspace before share; shared import was not started")
    if expected_fingerprint and data["fingerprint"] != expected_fingerprint:
        raise PlanError("source changed since preview; no import started")
    with workspace.lock():
        control = workspace.control()
        checkpoint = control.get("import_state")
        existing = workspace.records(allow_incomplete=True)
        if checkpoint and checkpoint.get("fingerprint") != data["fingerprint"]:
            raise PlanError("workspace already has another import snapshot; use a separate inactive workspace")
        if existing and not checkpoint:
            raise PlanError("migration requires an empty Plan workspace; existing work was not overwritten")
        expected = {record["id"]: content(record) for record in data["records"]}
        target_ids = {workspace.native_id(identifier) for identifier in expected}
        owned_ids = {record["native_id"] for record in existing}
        native_by_id = {issue["id"]: issue for issue in workspace.backend.issues()}
        for issue in native_by_id.values():
            if issue["id"] in target_ids and issue["id"] not in owned_ids:
                raise PlanError("native ID collision; existing Beads work was not overwritten")
        for record in existing:
            if record["native_id"] != workspace.native_id(record["id"]):
                raise PlanError("native ID collision; imported identity does not match its checkpoint")
            if (record.get("pending") or expected.get(record["id"]) != content(record)
                    or workspace.field_differences(record, native_by_id[record["native_id"]])):
                raise PlanError(f"{record['id']}: destination differs from the import snapshot; no overwrite allowed")
        if checkpoint and checkpoint.get("status") == "complete":
            if {r["id"] for r in existing} != set(expected):
                raise PlanError("completed import no longer matches its record set")
            workspace.records()  # Confirm ordinary reads and projections still pass.
            return {**preview(data, workspace), "mode": "already-imported", "saved": "local", "replayed": True}
        if not checkpoint:
            checkpoint = {"fingerprint": data["fingerprint"], "source_revision": data["source_revision"],
                          "started_at": model.timestamp(), "status": "incomplete", "records": len(expected)}
        control["import_state"] = checkpoint
        control["retired_ids"] = data["retired_ids"]
        # Retain historical evidence in Beads, not in a second writable file.
        control["source_manifest"] = data["source_manifest"]
        control["source_log"] = data["source_log"]
        workspace.save_control(control)
        records = []
        existing_by_id = {record["id"]: record for record in existing}
        for original in data["records"]:
            record = copy.deepcopy(original)
            record.update(schema_version=1, workspace_id=workspace.id,
                          native_id=workspace.native_id(record["id"]), import_fingerprint=data["fingerprint"])
            if record["fields"].get("claim"):
                # Product has no attempt token. Give each new copy a token, but
                # keep the saved token when resuming a partially written copy.
                saved = existing_by_id.get(record["id"])
                record["claim_token"] = saved.get("claim_token") if saved else uuid.uuid4().hex
            records.append(record)
        records = model.Records(records)
        native = []
        for record in records:
            if record["native_id"] in owned_ids:
                continue
            issue = workspace._native(record)
            issue["created_at"] = checkpoint["started_at"]
            issue["updated_at"] = checkpoint["started_at"]
            issue["dependencies"] = [{"issue_id": issue["id"], **edge} for edge in workspace.native_edges(record, records)]
            native.append(issue)
        # The target stays unavailable even if bd commits only a prefix.
        result = workspace.backend.import_issues(native) if native else {}
        if isinstance(result, dict) and any(result.get(key) for key in ("skipped_dependencies", "errors", "stale_skipped_ids", "tie_kept_local_ids")):
            raise PlanError("Beads reported skipped or conflicting import data; workspace remains inactive")
        observed = workspace.records(allow_incomplete=True)
        if {r["id"]: content(r) for r in observed} != expected:
            raise PlanError("import comparison failed; workspace remains inactive")
        native_by_id = {issue["id"]: issue for issue in workspace.backend.issues()}
        for record in observed:
            issue = native_by_id[record["native_id"]]
            if workspace.field_differences(record, issue):
                raise PlanError(f"{record['id']}: native field comparison failed; workspace remains inactive")
            if not workspace.edges_match(record, observed, issue.get("dependencies", [])):
                # A failed native import can leave nodes without their edges.
                # Existing nodes are not reimported: equal timestamps can conflict.
                workspace.backend.set_dependencies(record["native_id"], workspace.native_edges(record, observed))
                workspace.check_edges(record, observed, workspace.backend.dependencies(record["native_id"]))
        checkpoint["status"] = "complete"
        control["import_state"] = checkpoint
        workspace.save_control(control)
        workspace.records()
        return {**preview(data, workspace), "mode": "imported", "saved": "local", "replayed": False,
                "factory_activated": False, "workspace_id": workspace.id}
