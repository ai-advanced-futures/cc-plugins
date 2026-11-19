"""Checked planning operations over the selected Beads workspace."""
from __future__ import annotations

import copy
import uuid

from . import PlanError, model
from .sources import PRD

EDITABLE = {"title", "description", "status", "tags", "aliases", "protected", "resource", "sources",
            "usage_window", "stale_after", "target_date", "planned_start_date", "planned_end_date",
            "size", "spec", "check", "check_declared_by"}


class Service:
    def __init__(self, workspace, actor: str | None = None):
        self.workspace = workspace
        self.actor = actor or "agent:plan"
        self.prd = PRD(workspace.source_root)

    def _records(self):
        return self.workspace.records()

    def _validate(self, records, changed, previous):
        errors, _warnings = model.validate(records, self.workspace.control().get("retired_ids") or [])
        if errors:
            raise PlanError("change refused: " + "; ".join(errors))
        # Source pages can be removed. Check new traces here so existing broken
        # traces can be removed one at a time. check reports all remaining gaps.
        old_traces = previous["fields"].get("traces", []) if previous else []
        for trace in changed["fields"].get("traces") or []:
            if trace not in old_traces:
                self.prd.trace(trace["to"])

    def view(self, record, records):
        result = copy.deepcopy(record)
        result["effective_state"] = model.effective_state(record, records)
        result["relationships"] = [{"type": relation, "target": target} for relation, target in model.relations(record)]
        membership = "milestone" if model.record_type(record) == "Milestone" else "parent"
        children = [r for r in records if r["fields"].get(membership) and model.resolve(records, r["fields"][membership])["id"] == record["id"]]
        eligible = [r for r in children if r["fields"].get("state") != "cancelled"]
        done = sum(r["fields"].get("state") in model.DELIVERED for r in eligible)
        result["children"] = [r["id"] for r in children]
        result["criteria"] = [r["id"] for r in records if model.record_type(r) == "AcceptanceCriterion" and model.resolve(records, r["fields"]["item"])["id"] == record["id"]]
        result["progress"] = {"done": done, "total": len(eligible), "percent": done * 100 // len(eligible) if eligible else None}
        return result

    def list(self, kind=None, milestone=None):
        with self.workspace.lock():
            records = self._records()
            selected = model.type_name(kind) if kind else None
            target = model.resolve(records, milestone)["id"] if milestone else None
            return [self.view(r, records) for r in records
                    if (not selected or model.record_type(r) == selected)
                    and (not target or (r["fields"].get("milestone") and model.resolve(records, r["fields"]["milestone"])["id"] == target))]

    def show(self, identifier, kind=None):
        with self.workspace.lock():
            records = self._records()
            return self.view(model.resolve(records, identifier, kind), records)

    def ready(self, kind=None, milestone=None):
        with self.workspace.lock():
            records = self._records()
            return [self.view(r, records) for r in model.ready(records, kind, milestone)]

    def check(self):
        with self.workspace.lock():
            control = self.workspace.control()
            issues = self.workspace.backend.issues()  # One store read for the two passes.
            records = self.workspace.records(allow_incomplete=True, issues=issues)
            errors, warnings = model.validate(records, control.get("retired_ids") or [])
            if control.get("import_state") and control["import_state"].get("status") != "complete":
                errors.append("import is incomplete")
            for record in records:
                if record.get("pending"):
                    errors.append(f"{record['id']}: operation is incomplete; run recover")
                for trace in record["fields"].get("traces") or []:
                    try:
                        page = self.prd.trace(trace["to"])
                        # A cancelled item gives no drift warning. The state is read at each check, so a reopened item
                        # shows its drift again (D-9107). A missing page stays an error.
                        if page["hash"] != trace["hash"] and record["fields"].get("state") != "cancelled":
                            warnings.append(f"{record['id']}: requirement drift at {trace['to']}")
                    except PlanError as exc:
                        errors.append(f"{record['id']}: {exc}")
            if not errors:
                try:
                    self.workspace.records(issues=issues)  # Also verify native field projections.
                except PlanError as exc:
                    errors.append(str(exc))
            return {"errors": errors, "warnings": warnings, "records": len(records),
                    "workspace_id": self.workspace.id, "saved": "local"}

    def _request(self, records, action, payload, request_id):
        request_id = request_id or uuid.uuid4().hex
        if not isinstance(request_id, str) or not request_id or len(request_id) > 128 or any(ord(c) < 32 for c in request_id):
            raise PlanError("request ID must be 1 to 128 characters without control characters")
        fingerprint = model.digest({"action": action, "payload": payload, "actor": self.actor})
        for record in records:
            for event in record.get("events", []):
                if event.get("id") == request_id:
                    if event.get("fingerprint") != fingerprint:
                        raise PlanError("request ID was already used for another operation")
                    return request_id, fingerprint, {"record": self.view(record, records), "operation": event, "replayed": True, "saved": "local"}
        return request_id, fingerprint, None

    def _save(self, candidate, records, action, payload, request_id, fingerprint, creating=False):
        model.require_actor(self.actor)
        desired = [candidate if r["id"] == candidate["id"] else r for r in records]
        if creating:
            desired.append(candidate)
        previous = next((record for record in records if record["id"] == candidate["id"]), None)
        self._validate(desired, candidate, previous)
        event = {"id": request_id, "fingerprint": fingerprint, "action": action, "actor": self.actor,
                 "at": model.timestamp(), "payload": payload,
                 "result": {"id": candidate["id"], "revision": candidate.get("revision", 0) + 1,
                            "state": candidate["fields"].get("state"), "owner": candidate["fields"].get("owner"),
                            "claim_token": candidate.get("claim_token")}}
        saved = self.workspace.commit(candidate, records, event, creating=creating)
        desired = [saved if r["id"] == saved["id"] else r for r in desired]
        return {"record": self.view(saved, desired), "operation": event, "replayed": False, "saved": "local"}

    @staticmethod
    def _revision(record, expected):
        if expected is not None and record.get("revision") != expected:
            raise PlanError(f"stale revision: expected {expected}, found {record.get('revision')}")
        if model.record_type(record) == "Run":
            raise PlanError("Run records are immutable")

    @staticmethod
    def _require_claim_token(record, claim_token):
        if not isinstance(claim_token, str) or not claim_token or record.get("claim_token") != claim_token:
            raise PlanError("current claim token is required; this work attempt is stale")

    def _holder(self, record, claim_token=None):
        claim = record["fields"].get("claim")
        if claim is None:
            if claim_token:
                raise PlanError("claim no longer exists; this work attempt is stale")
            return
        if claim.get("by") != self.actor:
            raise PlanError("another actor holds the claim; release or expire it before changing work")
        if not model.live_claim(record):
            raise PlanError("claim expired; renew or expire it before changing work")
        self._require_claim_token(record, claim_token)

    def new(self, kind, title, description="", body=None, links=None, traces=None, values=None, request_id=None):
        kind = model.type_name(kind)
        if kind == "Run":
            raise PlanError("new Run is not a planning operation; import preserves existing Run evidence")
        payload = {"type": kind, "title": title, "description": description, "body": body,
                   "links": links or {}, "traces": traces or [], "values": values or {}}
        with self.workspace.lock():
            records = self._records()
            request_id, fingerprint, replay = self._request(records, "new", payload, request_id)
            if replay:
                return replay
            identifier = model.next_id(records, kind, self.workspace.control().get("retired_ids") or [])
            fields = {"type": kind, "title": title, "description": description, "status": "draft",
                      "generated": {"by": self.actor, "at": model.timestamp()}}
            if kind in model.WORK_TYPES:
                fields["state"] = "backlog"
            for key, value in (values or {}).items():
                if key not in EDITABLE:
                    raise PlanError(f"new cannot set {key}; use the dedicated operation")
                fields[key] = value
            for relation, targets in (links or {}).items():
                if relation not in model.RELATIONS - {"traces"}:
                    raise PlanError(f"unsupported relation {relation}")
                targets = targets if isinstance(targets, list) else [targets]
                resolved = [model.resolve(records, target)["id"] for target in targets]
                if relation in model.SINGLE_RELATIONS:
                    if len(resolved) != 1:
                        raise PlanError(f"{relation} has exactly one target")
                    fields[relation] = resolved[0]
                else:
                    fields[relation] = list(dict.fromkeys(resolved))
            if traces:
                fields["traces"] = [self.prd.trace(target) for target in traces]
            if kind == "Story" and fields.get("parent") and "milestone" not in fields:
                milestone = model.resolve(records, fields["parent"])["fields"].get("milestone")
                if milestone:
                    fields["milestone"] = milestone
            record = {"id": identifier, "path": f"/{model.FOLDERS[kind]}/{identifier}.md", "fields": fields,
                      "body": body if body is not None else description, "revision": 0, "events": []}
            return self._save(record, records, "new", payload, request_id, fingerprint, creating=True)

    def edit(self, identifier, field, value, expected=None, request_id=None, claim_token=None):
        if field == "lifecycle":
            field = "status"
        if field not in EDITABLE and field != "body":
            raise PlanError(f"cannot set {field}; state, owner, claims, and relationships have dedicated operations")
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier)
            payload = {"id": record["id"], "field": field, "value": value, "claim_token": claim_token}
            request_id, fingerprint, replay = self._request(records, "set", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            self._holder(record, claim_token)
            candidate = copy.deepcopy(record)
            if field == "body":
                candidate["body"] = value
            elif value is None:
                candidate["fields"].pop(field, None)
            else:
                candidate["fields"][field] = value
            return self._save(candidate, records, "set", payload, request_id, fingerprint)

    def link(self, identifier, relation, target, remove=False, expected=None, request_id=None, claim_token=None):
        if relation not in model.RELATIONS:
            raise PlanError("relation must be parent, milestone, blocked_by, discovered_from, item, or traces")
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier)
            payload = {"id": record["id"], "relation": relation, "target": target, "remove": remove,
                       "claim_token": claim_token}
            request_id, fingerprint, replay = self._request(records, "link", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            self._holder(record, claim_token)
            if relation == "traces" and remove:
                matches = [entry for entry in record["fields"].get("traces", [])
                           if target == entry["to"] or ("/" not in target and model.reference_id(entry["to"]) == target)]
                if len(matches) != 1:
                    raise PlanError("stored trace is missing or ambiguous; use its exact prd:/ path")
                value = matches[0]
            else:
                value = self.prd.trace(target) if relation == "traces" else model.resolve(records, target)["id"]
            candidate = copy.deepcopy(record)
            fields = candidate["fields"]
            if relation in model.SINGLE_RELATIONS:
                if remove:
                    if fields.get(relation) and model.resolve(records, fields[relation])["id"] != value:
                        raise PlanError("the stored relationship has another target")
                    fields.pop(relation, None)
                else:
                    fields[relation] = value
            else:
                previous = fields.get(relation) or []
                if relation == "traces":
                    if not remove and any(entry["to"] == value["to"] and entry["hash"] != value["hash"] for entry in previous):
                        # A re-link would clear a drift with no approval (PLAN-STORY-620, D-9239).
                        raise PlanError("the item already traces this page with another hash; "
                                        "review the change, then run accept-drift")
                    previous = [entry for entry in previous if entry["to"] != value["to"]]
                else:
                    previous = [entry for entry in previous if model.resolve(records, entry)["id"] != value]
                if not remove:
                    previous.append(value)
                if previous:
                    fields[relation] = previous
                else:
                    fields.pop(relation, None)
            if fields.get("state") in {"ready", "blocked"}:
                fields["state"] = model.effective_state(candidate, records)
            return self._save(candidate, records, "link", payload, request_id, fingerprint)

    def accept_drift(self, identifier, target, approved_by=None, expected=None, request_id=None, claim_token=None):
        """Store the hash of now in 1 trace whose PRD page changed, after a review (PLAN-STORY-620, D-9239)."""
        given = model.approval_kind(approved_by)
        if self.actor.startswith("agent:") and given not in {"card", "decision"}:
            raise PlanError("an agent drift accept needs --approved-by with a card link or a D-id")
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier)
            payload = {"id": record["id"], "target": target, "approved_by": approved_by, "claim_token": claim_token}
            request_id, fingerprint, replay = self._request(records, "accept-drift", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            self._holder(record, claim_token)
            traces = record["fields"].get("traces") or []
            matches = [index for index, entry in enumerate(traces)
                       if target == entry["to"] or ("/" not in target and model.reference_id(entry["to"]) == target)]
            if len(matches) != 1:
                raise PlanError("stored trace is missing or ambiguous; use its exact prd:/ path")
            before = traces[matches[0]]
            page = self.prd.trace(before["to"])
            if page["hash"] == before["hash"]:
                raise PlanError("the trace has no drift; nothing to accept")
            candidate = copy.deepcopy(record)
            candidate["fields"]["traces"][matches[0]] = page
            event = {**payload, "to": before["to"], "hash_before": before["hash"], "hash_after": page["hash"]}
            return self._save(candidate, records, "accept-drift", event, request_id, fingerprint)

    def assign(self, identifier, owner, kind=None, expected=None, request_id=None):
        wanted = model.owner_name(owner)
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier, kind)
            payload = {"id": record["id"], "owner": wanted}
            request_id, fingerprint, replay = self._request(records, "assign", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            if model.record_type(record) not in model.WORK_TYPES:
                raise PlanError("only epics, features, stories, and tasks have an owner")
            if record["fields"].get("claim") and wanted != record["fields"].get("owner"):
                raise PlanError("release or expire the claim before reassigning work")
            candidate = copy.deepcopy(record)
            if wanted:
                candidate["fields"]["owner"] = wanted
            else:
                candidate["fields"].pop("owner", None)
            return self._save(candidate, records, "assign", payload, request_id, fingerprint)

    def status(self, identifier, wanted, kind=None, approved_by=None, expected=None, request_id=None, claim_token=None):
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier, kind)
            wanted = model.state_name(wanted)
            payload = {"id": record["id"], "state": wanted, "approved_by": approved_by, "claim_token": claim_token}
            request_id, fingerprint, replay = self._request(records, "status", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            self._holder(record, claim_token)
            candidate = model.change_state(record, wanted, self.actor, approved_by, self.workspace.source_root, records)
            return self._save(candidate, records, "status", payload, request_id, fingerprint)

    def claim(self, identifier, kind=None, lease="30m", expected=None, request_id=None):
        model.require_actor(self.actor)
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier, kind)
            payload = {"id": record["id"], "lease": lease}
            request_id, fingerprint, replay = self._request(records, "claim", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            if model.live_claim(record):
                raise PlanError("work already has a live claim, even if the actor name is the same")
            if record not in model.ready(records):
                raise PlanError("only eligible ready work can be claimed")
            now = model.utcnow()
            candidate = model.change_state(record, "claimed", self.actor, None, self.workspace.source_root, records, now)
            candidate["fields"]["claim"] = {"by": self.actor, "at": model.timestamp(now), "lease_expires_at": model.lease_end(lease, now)}
            if not candidate["fields"].get("owner"):
                candidate["fields"]["owner"] = self.actor
            candidate["claim_token"] = uuid.uuid4().hex
            return self._save(candidate, records, "claim", payload, request_id, fingerprint)

    def heartbeat(self, identifier, kind=None, lease="30m", claim_token=None, expected=None, request_id=None):
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier, kind)
            payload = {"id": record["id"], "lease": lease, "claim_token": claim_token}
            request_id, fingerprint, replay = self._request(records, "heartbeat", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            claim = record["fields"].get("claim")
            if not claim or claim.get("by") != self.actor:
                raise PlanError("current holder and claim token are required")
            self._require_claim_token(record, claim_token)
            candidate = copy.deepcopy(record)
            now = model.utcnow()
            candidate["fields"]["claim"].update(heartbeat_at=model.timestamp(now), lease_expires_at=model.lease_end(lease, now))
            return self._save(candidate, records, "heartbeat", payload, request_id, fingerprint)

    def release(self, identifier, kind=None, claim_token=None, expected=None, request_id=None, expired=False):
        with self.workspace.lock():
            records = self._records()
            record = model.resolve(records, identifier, kind)
            payload = {"id": record["id"], "claim_token": claim_token, "expired": expired}
            request_id, fingerprint, replay = self._request(records, "expire" if expired else "release", payload, request_id)
            if replay:
                return replay
            self._revision(record, expected)
            held = record["fields"].get("claim")
            if not held:
                raise PlanError("work has no claim")
            if expired:
                if model.live_claim(record):
                    raise PlanError("claim has not expired")
            else:
                if held.get("by") != self.actor:
                    raise PlanError("current holder and claim token are required")
                self._require_claim_token(record, claim_token)
            candidate = copy.deepcopy(record)
            candidate["fields"].pop("claim", None)
            candidate.pop("claim_token", None)
            if candidate["fields"].get("state") in {"claimed", "in_progress"}:
                candidate = model.change_state(candidate, "ready", self.actor, None, self.workspace.source_root, records)
            action = "expire" if expired else "release"
            return self._save(candidate, records, action, payload, request_id, fingerprint)
