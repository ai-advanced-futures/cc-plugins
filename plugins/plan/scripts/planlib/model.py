"""Product planning semantics, with no filesystem or Beads writes.

The compatibility reference is Product's registry, roadmap-model, statecmd,
claims, and hashing modules. Contract tests protect this independent copy.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from . import PlanError

SCHEMA_VERSION = 1
WORK_TYPES = ("Epic", "Feature", "Story", "Task")
TYPES = ("Project", "Milestone", *WORK_TYPES, "AcceptanceCriterion", "Run")
PREFIXES = dict(zip(TYPES, ("PROJECT", "MILESTONE", "EPIC", "FEATURE", "STORY", "TASK", "CRITERION", "RUN")))
FOLDERS = dict(zip(TYPES, ("projects", "milestones", "epics", "features", "stories", "tasks", "criteria", "runs")))
LEVELS = {kind: index for index, kind in enumerate(WORK_TYPES)}
STATES = ("backlog", "ready", "claimed", "in_progress", "in_review", "blocked", "done", "released", "cancelled")
CLOSED = {"done", "released", "cancelled"}
DELIVERED = {"done", "released"}
LIFECYCLES = {"draft", "stable", "deprecated"}
FREE_MOVES = {("ready", "claimed"), ("claimed", "in_progress"), ("in_progress", "in_review"), ("claimed", "ready"), ("in_progress", "ready")}
ACTOR = re.compile(r"(?:human|agent):[A-Za-z0-9._-]+\Z")
RELATIONS = {"parent", "milestone", "blocked_by", "discovered_from", "item", "traces"}
SINGLE_RELATIONS = RELATIONS - {"blocked_by", "traces"}
GENERATED = re.compile(r"<!--\s*(LINKS|STATUS):START.*?-->.*?<!--\s*\1:END\s*-->", re.S)
APPROVALS = tuple((kind, re.compile(pattern)) for kind, pattern in (
    ("card", r"https://[a-z0-9.-]+\.slack\.com/archives/[A-Z0-9]+/p\d+(\?\S*)?"),
    ("pr", r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+([/?#]\S*)?"),
    ("issue", r"#\d+"), ("decision", r"D-\d{3,}"),
    ("answer", r"ANSWER:[A-Za-z0-9._-]+"), ("url", r"https?://\S+"),
))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def timestamp(now: datetime | None = None) -> str:
    return (now or utcnow()).astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_time(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def body_hash(body: str, identifier: str) -> str:
    text = GENERATED.sub(" ", body)
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        heading = lines[0][2:].strip()
        if heading == identifier or heading.startswith(identifier + ":"):
            lines.pop(0)
    normalized = re.sub(r"\s+", " ", "\n".join(lines)).strip()
    return hashlib.sha256(normalized.encode()).hexdigest()[:6]


def type_name(value: str) -> str:
    key = value.replace("-", "").replace("_", "").lower()
    for kind in TYPES:
        if key in {kind.lower(), PREFIXES[kind].lower()}:
            return kind
    raise PlanError(f"unknown type {value!r}; use project, milestone, epic, feature, story, task, criterion, or run")


def state_name(value: str) -> str:
    value = value.replace("-", "_").replace(" ", "_")
    if value not in STATES:
        raise PlanError(f"unknown work state {value!r}; use {', '.join(STATES)}")
    return value


def require_actor(actor: str) -> None:
    if not isinstance(actor, str) or not ACTOR.fullmatch(actor):
        raise PlanError("actor must be human:<name> or agent:<id>")


def owner_name(owner: str) -> str | None:
    if owner in {"", "-"}:
        return None
    owner = owner if ":" in owner else "human:" + owner
    require_actor(owner)
    return owner


def approval_kind(value: str | None) -> str | None:
    if value is None:
        return None
    for kind, pattern in APPROVALS:
        if pattern.fullmatch(value):
            return kind
    raise PlanError("approval must be a PR URL, #number, D-id, ANSWER id, card link, or URL")


def record_type(record: dict) -> str:
    return record["fields"]["type"]


def reference_id(value: str) -> str:
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise PlanError("a reference must be nonempty text without control characters")
    return PurePosixPath(value).stem if "/" in value or value.endswith(".md") else value


class Records(list):
    """One read snapshot, indexed once for graph walks. Do not mutate it."""
    def __init__(self, records):
        super().__init__(records)
        self.by_name = {}
        self.by_number = {}
        for record in self:
            kind = record_type(record)
            logical_names = {record["id"], *(record["fields"].get("aliases") or [])}
            for name in logical_names | {record.get("native_id", "")}:
                self.by_name.setdefault(name, []).append(record)
            pattern = rf"(?:PLAN-)?{PREFIXES.get(kind, '')}-(\d+)\Z"
            numbers = {int(match[1]) for name in logical_names if (match := re.fullmatch(pattern, name))}
            for number in numbers:
                self.by_number.setdefault((kind, number), []).append(record)


def resolve(records: list[dict], value: str, kind: str | None = None) -> dict:
    wanted_type = type_name(kind) if kind else None
    identifier = reference_id(value)
    index = records if isinstance(records, Records) else Records(records)
    if wanted_type and identifier.isdecimal() and wanted_type != "Run":
        found = index.by_number.get((wanted_type, int(identifier)), [])
    else:
        found = list(index.by_name.get(identifier, []))
        if identifier.upper() != identifier:
            found.extend(record for record in index.by_name.get(identifier.upper(), []) if record not in found)
        if wanted_type:
            found = [record for record in found if record_type(record) == wanted_type]
    if len(found) != 1:
        reason = "not found" if not found else "ambiguous"
        raise PlanError(f"{kind + ' ' if kind else ''}{value!r} is {reason}")
    return found[0]


def next_id(records: list[dict], kind: str, retired: list[str] = ()) -> str:
    prefix = PREFIXES[kind]
    pattern = re.compile(rf"(?:PLAN-)?{prefix}-(\d+)\Z")
    values = [name for record in records for name in [record["id"], *(record["fields"].get("aliases") or [])]] + list(retired)
    numbers = [int(match[1]) for value in values if (match := pattern.fullmatch(value))]
    return f"PLAN-{prefix}-{max(numbers, default=0) + 1:02d}"


def live_claim(record: dict, now: datetime | None = None) -> bool:
    claim = record["fields"].get("claim")
    end = parse_time(claim.get("lease_expires_at")) if isinstance(claim, dict) else None
    return bool(end and end > (now or utcnow()))


def lease_end(value: str, now: datetime | None = None) -> str:
    match = re.fullmatch(r"([1-9]\d*)([smh])", value)
    if not match:
        raise PlanError("lease must be a positive duration such as 45s, 30m, or 2h")
    seconds = int(match[1]) * {"s": 1, "m": 60, "h": 3600}[match[2]]
    try:
        return timestamp((now or utcnow()) + timedelta(seconds=seconds))
    except OverflowError as exc:
        raise PlanError("lease duration is too large") from exc


def effective_state(record: dict, records: list[dict]) -> str | None:
    state = record["fields"].get("state")
    if state not in {"ready", "blocked"}:
        return state
    for target in record["fields"].get("blocked_by") or []:
        if resolve(records, target)["fields"].get("state") not in CLOSED:
            return "blocked"
    return "ready"


def change_state(record: dict, wanted: str, actor: str, approved_by: str | None,
                 source_root: Path, records: list[dict], now: datetime | None = None) -> dict:
    """Apply Product's permission, blocker, specification, and date rules."""
    require_actor(actor)
    wanted = state_name(wanted)
    if record_type(record) not in WORK_TYPES:
        raise PlanError(f"{record_type(record)} has no work state")
    now = now or utcnow()
    result = copy.deepcopy(record)
    fields = result["fields"]
    old = effective_state(record, records) or "backlog"
    given = approval_kind(approved_by)
    if actor.startswith("agent:") and (old, wanted) not in FREE_MOVES:
        if given is None:
            raise PlanError(f"agent transition {old} -> {wanted} needs --approved-by")
        if (wanted == "cancelled" or (old in DELIVERED and wanted not in CLOSED)) and given not in {"card", "decision"}:
            raise PlanError("agent cancellation or reopening delivered work needs a card link or D-id")
        if record_type(record) == "Story" and old == "backlog" and wanted in {"ready", "blocked"}:
            spec = fields.get("spec")
            if not isinstance(spec, str) or spec in {"", "none"}:
                raise PlanError("Story promotion needs an existing specification file")
            base = source_root.resolve()
            path = (base / spec).resolve()
            if not path.is_relative_to(base) or not path.is_file():
                raise PlanError("Story specification must be a file inside the source root")
    fields["state"] = wanted
    if wanted in {"ready", "blocked"}:
        fields["state"] = effective_state(result, records)
    new = fields["state"]
    if new == "in_progress" and not fields.get("actual_start_date"):
        fields["actual_start_date"] = now.strftime("%Y-%m-%d")
    if new in DELIVERED and old not in DELIVERED:
        fields["actual_end_date"] = now.strftime("%Y-%m-%d")
    elif old in DELIVERED and new not in DELIVERED:
        fields.pop("actual_end_date", None)
    return result


def ready(records: list[dict], kind: str | None = None, milestone: str | None = None,
          now: datetime | None = None) -> list[dict]:
    records = records if isinstance(records, Records) else Records(records)
    found = []
    selected = type_name(kind) if kind else None
    selected_milestone = resolve(records, milestone)["id"] if milestone else None
    for record in records:
        fields = record["fields"]
        if record_type(record) not in WORK_TYPES or (selected and record_type(record) != selected):
            continue
        if fields.get("status") == "deprecated" or effective_state(record, records) != "ready" or live_claim(record, now):
            continue
        if record_type(record) == "Story" and fields.get("spec") in (None, "", "none"):
            continue
        container = resolve(records, fields["milestone"]) if fields.get("milestone") else None
        if selected_milestone and (not container or container["id"] != selected_milestone):
            continue
        date = container["fields"].get("target_date") if container else None
        found.append(((0, str(date)) if date else (1, ""), record["id"], record))
    return [r for _date, _id, r in sorted(found, key=lambda item: item[:2])]


def relations(record: dict) -> list[tuple[str, str]]:
    result = []
    fields = record["fields"]
    for field in SINGLE_RELATIONS:
        if fields.get(field):
            result.append((field, fields[field]))
    result.extend(("blocked_by", target) for target in fields.get("blocked_by") or [])
    result.extend(("traces", entry.get("to", "")) for entry in fields.get("traces") or [] if isinstance(entry, dict))
    return sorted(result)


def shape_errors(records: list[dict]) -> list[str]:
    """Reject malformed values before graph traversal or native writes."""
    errors = []
    text_fields = {"type", "title", "description", "status", "state", "size", "spec", "owner",
                   "check_declared_by", "target_date", "planned_start_date", "planned_end_date",
                   "actual_start_date", "actual_end_date", "resource", "stale_after", *SINGLE_RELATIONS}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("fields"), dict):
            errors.append("record and fields must be objects")
            continue
        identifier = record.get("id")
        fields = record["fields"]
        if not isinstance(identifier, str) or not isinstance(fields.get("type"), str):
            errors.append("record identity and type must be text")
        for key in text_fields & fields.keys():
            if not isinstance(fields[key], str):
                errors.append(f"{identifier}: {key} must be text")
        for key in {"aliases", "tags", "blocked_by", "check", "drifted"} & fields.keys():
            values = fields[key]
            if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
                errors.append(f"{identifier}: {key} must be a list of nonempty text values")
        if "traces" in fields and (not isinstance(fields["traces"], list)
                                   or any(not isinstance(value, dict) for value in fields["traces"])):
            errors.append(f"{identifier}: traces must be a list of objects")
        if "sources" in fields and (not isinstance(fields["sources"], list)
                                    or any(not isinstance(value, dict) for value in fields["sources"])):
            errors.append(f"{identifier}: sources must be a list of objects")
        if "protected" in fields and not isinstance(fields["protected"], bool):
            errors.append(f"{identifier}: protected must be true or false")
        if "usage_window" in fields and not isinstance(fields["usage_window"], dict):
            errors.append(f"{identifier}: usage_window must be an object")
        if "revision" in record and (type(record["revision"]) is not int or record["revision"] < 0):
            errors.append(f"{identifier}: revision must be a nonnegative integer")
        if not isinstance(record.get("events", []), list) or any(not isinstance(event, dict) for event in record.get("events", [])):
            errors.append(f"{identifier}: events must be a list of objects")
        if "pending" in record and not isinstance(record["pending"], dict):
            errors.append(f"{identifier}: pending operation must be an object")
    return errors


def validate(records: list[dict], retired: list[str] = ()) -> tuple[list[str], list[str]]:
    errors, warnings = shape_errors(records), []
    if errors:
        return errors, warnings
    records = records if isinstance(records, Records) else Records(records)
    names = {}
    for record in records:
        identifier = record.get("id")
        fields = record.get("fields", {})
        kind = fields.get("type")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", identifier):
            errors.append("record has an invalid logical ID")
            continue
        if kind not in TYPES:
            errors.append(f"{identifier}: unsupported type {kind!r}")
            continue
        if not isinstance(fields.get("title"), str) or not fields["title"].strip():
            errors.append(f"{identifier}: title is required")
        if not isinstance(record.get("body"), str):
            errors.append(f"{identifier}: body must be text")
        if fields.get("status", "draft") not in LIFECYCLES:
            errors.append(f"{identifier}: invalid lifecycle status")
        if kind in WORK_TYPES and fields.get("state", "backlog") not in STATES:
            errors.append(f"{identifier}: invalid work state")
        if kind not in WORK_TYPES and "state" in fields:
            errors.append(f"{identifier}: {kind} has no work state")
        aliases = fields.get("aliases") or []
        for name in [identifier, *aliases]:
            if name in names:
                errors.append(f"{identifier}: identity {name!r} is duplicated")
            names[name] = identifier
            if name in retired:
                errors.append(f"{identifier}: identity {name!r} is retired")
        if fields.get("owner") is not None and not ACTOR.fullmatch(str(fields["owner"])):
            errors.append(f"{identifier}: owner must be an actor")
        claim = fields.get("claim")
        if claim is not None and (kind not in WORK_TYPES or not isinstance(claim, dict)
                                  or not ACTOR.fullmatch(str(claim.get("by", "")))
                                  or parse_time(claim.get("at")) is None
                                  or parse_time(claim.get("lease_expires_at")) is None):
            errors.append(f"{identifier}: invalid claim")
        if kind != "Story" and any(key in fields for key in ("spec", "size")) and kind != "Run":
            errors.append(f"{identifier}: spec and size belong to Stories")
        if fields.get("size") is not None and fields["size"] not in {"S", "M", "L"}:
            errors.append(f"{identifier}: size must be S, M, or L")
        if kind in {"AcceptanceCriterion", "Run"} and not fields.get("item"):
            errors.append(f"{identifier}: item is required")
        if kind == "AcceptanceCriterion" and "check" in fields:
            command = fields["check"]
            if not isinstance(command, list) or not command or any(not isinstance(x, str) for x in command):
                errors.append(f"{identifier}: check must be a nonempty argv list")
            declarer = fields.get("check_declared_by", "")
            if not declarer.startswith("human:") or not ACTOR.fullmatch(declarer):
                errors.append(f"{identifier}: a declared check needs a human check_declared_by")
        for field in SINGLE_RELATIONS:
            target = fields.get(field)
            if target is None:
                continue
            try:
                other = resolve(records, target)
                target_kind = record_type(other)
                if field == "parent" and (kind not in LEVELS or target_kind not in LEVELS or LEVELS[target_kind] >= LEVELS[kind]):
                    errors.append(f"{identifier}: parent must be a higher-level work item")
                if field == "milestone" and (kind not in WORK_TYPES or target_kind != "Milestone"):
                    errors.append(f"{identifier}: milestone must link work to a Milestone")
                if field == "discovered_from" and (kind not in WORK_TYPES or target_kind not in WORK_TYPES):
                    errors.append(f"{identifier}: discovered_from must link work items")
                if field == "discovered_from" and other["id"] == identifier:
                    errors.append(f"{identifier}: discovered_from cannot link work to itself")
                if field == "item" and (kind not in {"AcceptanceCriterion", "Run"} or target_kind not in WORK_TYPES):
                    errors.append(f"{identifier}: item must link a Criterion or Run to work")
            except PlanError as exc:
                errors.append(f"{identifier}: {field}: {exc}")
        for target in fields.get("blocked_by") or []:
            try:
                other = resolve(records, target)
                if kind not in WORK_TYPES or record_type(other) not in WORK_TYPES:
                    errors.append(f"{identifier}: blocked_by must link work items")
            except PlanError as exc:
                errors.append(f"{identifier}: blocked_by: {exc}")
        traces = fields.get("traces") or []
        for trace in traces:
            if not isinstance(trace.get("to"), str) or not trace["to"].startswith("prd:/") or not re.fullmatch(r"[0-9a-f]{6}", str(trace.get("hash", ""))):
                errors.append(f"{identifier}: trace needs a prd:/ target and six-character hash")
        if kind in {"Milestone", "Epic", "Feature"} and not traces:
            warnings.append(f"{identifier}: no requirement trace")
    if errors:
        return errors, warnings
    projects = [r for r in records if record_type(r) == "Project"]
    if len(projects) > 1:
        errors.append("a workspace has at most one Project")
    if records and not projects:
        warnings.append("workspace has no Project")
    children_by_parent = {}
    for record in records:
        if record["fields"].get("parent"):
            parent_id = resolve(records, record["fields"]["parent"])["id"]
            children_by_parent.setdefault(parent_id, []).append(record)
    visiting, visited = set(), set()

    def walk(record):
        identifier = record["id"]
        if identifier in visiting:
            errors.append(f"{identifier}: dependency cycle")
            return
        if identifier in visited:
            return
        visiting.add(identifier)
        for target in record["fields"].get("blocked_by") or []:
            walk(resolve(records, target))
        visiting.remove(identifier)
        visited.add(identifier)

    for record in records:
        walk(record)
        fields = record["fields"]
        children = children_by_parent.get(record["id"], [])
        if fields.get("state") in DELIVERED and any(r["fields"].get("state") not in CLOSED for r in children):
            warnings.append(f"{record['id']}: delivered parent has open children")
        if record_type(record) == "Story" and fields.get("parent"):
            parent = resolve(records, fields["parent"])
            wanted = parent["fields"].get("milestone")
            # A bare ID and a /milestones/ path name 1 milestone, so compare the resolved records (PLAN-STORY-620).
            if wanted and (not fields.get("milestone")
                           or resolve(records, wanted)["id"] != resolve(records, fields["milestone"])["id"]):
                warnings.append(f"{record['id']}: milestone differs from its parent")
    return errors, warnings
