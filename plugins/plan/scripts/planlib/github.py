"""Publish a fixed Plan source to GitHub. The caller holds the workspace lock.

No Product files are read or written. GitHub is a view, never a work-state source.
A shared caller holds its gate across these functions and publication of checkpoints.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass

from . import PlanError, model
from .shared import SharedCommandError, capture

MAX_PAGES = 100
WORK = set(model.WORK_TYPES)
DATES = {"planned_start_date": "Planned start", "planned_end_date": "Planned end",
         "actual_start_date": "Actual start", "actual_end_date": "Actual end"}
CLOSED = {"done", "released", "cancelled"}
LOGIN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*(?:\[bot\])?")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")

RIGHTS = '''query PlanRights($owner:String!, $name:String!, $board:String!, $number:Int!) {
 viewer { login }
 repository(owner:$owner,name:$name) { id viewerCanCreateIssues }
 repositoryOwner(login:$board) { ... on ProjectV2Owner {
  projectV2(number:$number) { id viewerCanUpdate fields(first:100) { totalCount nodes {
   ... on ProjectV2Field { id name dataType }
   ... on ProjectV2SingleSelectField { id name dataType options { id name } }
   ... on ProjectV2IterationField { id name dataType }
  } } }
 } }
}'''
ISSUES = '''query PlanIssues($owner:String!, $name:String!, $after:String, $firstPage:Boolean!) {
 repository(owner:$owner,name:$name) {
  labels(first:100) @include(if:$firstPage) { totalCount nodes { name } }
  issueTypes(first:20) @include(if:$firstPage) { totalCount nodes { id name } }
  issues(first:100,after:$after,states:[OPEN,CLOSED]) {
   totalCount pageInfo { hasNextPage endCursor } nodes {
    id number url title body state stateReason viewerCanUpdate viewerCanType
    issueType { id name } milestone { number } parent { id }
    labels(first:100) { totalCount nodes { name } }
    assignees(first:100) { totalCount nodes { login } }
    blockedBy(first:100) { totalCount nodes { id } }
    subIssues(first:100) { totalCount nodes { id } }
   }
  }
 }
}'''


@dataclass
class Completed:
    returncode: int
    stdout: str
    stderr: str = ""


def _run(args, payload=None):
    try:
        result = capture(["gh", *args], cwd=None, env=None,
                         stdin=json.dumps(payload) if payload is not None else None)
    except SharedCommandError as exc:
        if isinstance(exc.__cause__, OSError):
            raise PlanError("GitHub CLI could not start; no result was confirmed") from None
        raise PlanError("GitHub CLI did not end before the time limit; inspect the publication before retry") from None
    return Completed(result.returncode, result.stdout)


def _nodes(connection, name):
    if not isinstance(connection, dict) or not isinstance(connection.get("nodes"), list):
        raise PlanError(f"GitHub returned an invalid {name} list")
    nodes = connection["nodes"]
    if type(connection.get("totalCount")) is not int or connection["totalCount"] != len(nodes):
        raise PlanError(f"GitHub {name} list is incomplete; publication is blocked")
    return nodes


class Gh:
    """Run the gh on PATH, including the Sofa App shim. Never print its errors."""
    def __init__(self, runner=None):
        self.runner = runner or _run

    def request(self, path, method="GET", data=None):
        args = ["api", path, "--method", method]
        if data is not None:
            args += ["--input", "-"]
        result = self.runner(args, data)
        if result.returncode:
            raise PlanError("GitHub request failed; its outcome is not confirmed")
        try:
            return json.loads(result.stdout) if result.stdout.strip() else None
        except (ValueError, TypeError):
            raise PlanError("GitHub returned invalid JSON; its outcome is not confirmed") from None

    def graphql(self, query, **variables):
        reply = self.request("graphql", "POST", {"query": query, "variables": variables})
        if not isinstance(reply, dict) or reply.get("errors") or not isinstance(reply.get("data"), dict):
            raise PlanError("GitHub GraphQL request failed; its outcome is not confirmed")
        return reply["data"]

    def cli_json(self, args):
        result = self.runner(args, None)
        if result.returncode:
            raise PlanError("GitHub Project read failed")
        try:
            return json.loads(result.stdout)
        except (ValueError, TypeError):
            raise PlanError("GitHub Project read returned invalid JSON") from None

    def snapshot(self, config):
        owner, name = config["repo"].split("/")
        rights = self.graphql(RIGHTS, owner=owner, name=name, board=config["owner"], number=config["number"])
        repository = rights.get("repository") or {}
        project = (rights.get("repositoryOwner") or {}).get("projectV2") or {}
        if repository.get("viewerCanCreateIssues") is not True or project.get("viewerCanUpdate") is not True:
            raise PlanError("GitHub requires Issues: write and Projects: write permissions")
        login = (rights.get("viewer") or {}).get("login")
        if not isinstance(login, str) or not LOGIN.fullmatch(login) or not repository.get("id") or not project.get("id"):
            raise PlanError("GitHub did not identify the viewer, repository and Project")
        issues, seen, cursor, total = [], set(), None, None
        labels, types = [], {}
        for _ in range(MAX_PAGES):
            data = self.graphql(ISSUES, owner=owner, name=name, after=cursor, firstPage=total is None).get("repository") or {}
            if total is None:
                labels = [x["name"] for x in _nodes(data.get("labels"), "repository labels")]
                types = {x["name"]: x["id"] for x in _nodes(data.get("issueTypes"), "issue types")}
            connection = data.get("issues") or {}
            page = connection.get("nodes")
            if not isinstance(page, list) or type(connection.get("totalCount")) is not int:
                raise PlanError("GitHub returned an invalid issues page")
            if total is not None and total != connection["totalCount"]:
                raise PlanError("GitHub issues changed during pagination; read again")
            total = connection["totalCount"]
            issues.extend(page)
            info = connection.get("pageInfo") or {}
            if info.get("hasNextPage") is False:
                break
            cursor = info.get("endCursor")
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise PlanError("GitHub issue pagination did not advance")
            seen.add(cursor)
        else:
            raise PlanError("GitHub issue pagination exceeds the supported page limit")
        if len(issues) != total or len({x["id"] for x in issues}) != len(issues):
            raise PlanError("GitHub issues read is incomplete or has duplicate identities")
        fields = _nodes(project.get("fields"), "Project fields")
        field_map = {}
        for field in fields:
            if field["name"] in field_map:
                raise PlanError("GitHub Project has duplicate field names")
            field_map[field["name"]] = {"id": field["id"], "type": field["dataType"],
                                        "options": {x["name"]: x["id"] for x in field.get("options") or []}}
        cards_reply = self.cli_json(["project", "item-list", str(config["number"]), "--owner", config["owner"], "--format", "json", "--limit", "1000"])
        cards = cards_reply.get("items") or []
        if type(cards_reply.get("totalCount")) is not int or cards_reply["totalCount"] != len(cards):
            raise PlanError("GitHub Project items read is incomplete; at most 1000 items are supported")
        by_issue = {}
        for card in cards:
            content = card.get("content") or {}
            if content.get("type") != "Issue" or content.get("repository") != config["repo"]:
                continue
            number = content["number"]
            if number in by_issue:
                raise PlanError("GitHub Project has duplicate cards for one issue")
            by_issue[number] = {**card, "Status": card.get("status")}
        normalized = []
        for issue in issues:
            normalized.append({**issue, "labels": [x["name"] for x in _nodes(issue.get("labels"), "issue labels")],
                               "assignees": [x["login"] for x in _nodes(issue.get("assignees"), "issue assignees")],
                               "blocked_by": [x["id"] for x in _nodes(issue.get("blockedBy"), "issue blockers")],
                               "sub_issues": [x["id"] for x in _nodes(issue.get("subIssues"), "sub-issues")],
                               "parent": (issue.get("parent") or {}).get("id"),
                               "milestone": (issue.get("milestone") or {}).get("number"),
                               "card": by_issue.get(issue["number"])})
        milestones = []
        for page_number in range(1, MAX_PAGES + 1):
            page = self.request(f"repos/{config['repo']}/milestones?state=all&per_page=100&page={page_number}")
            if not isinstance(page, list):
                raise PlanError("GitHub returned an invalid milestones list")
            milestones.extend(page)
            if len(page) < 100:
                break
        else:
            raise PlanError("GitHub milestone pagination exceeds the supported page limit")
        return {"login": login, "repo_id": repository["id"], "project_id": project["id"], "fields": field_map,
                "labels": labels, "issue_types": types, "issues": normalized, "milestones": milestones}

    def create(self, config, snapshot, record, body):
        fields = record["fields"]
        if fields["type"] == "Milestone":
            return self.request(f"repos/{config['repo']}/milestones", "POST", {"title": _title(record), "description": body})
        result = self.graphql('''mutation PlanCreate($repositoryId:ID!,$title:String!,$body:String!){
          createIssue(input:{repositoryId:$repositoryId,title:$title,body:$body}){issue{id number url}}
        }''', repositoryId=snapshot["repo_id"], title=_title(record), body=body)
        return result["createIssue"]["issue"]

    def update(self, config, issue, payload, milestone=False):
        endpoint = "milestones" if milestone else "issues"
        return self.request(f"repos/{config['repo']}/{endpoint}/{issue['number']}", "PATCH", payload)

    def relation(self, operation, issue, target):
        key = "blockingIssueId" if "BlockedBy" in operation else "subIssueId"
        data = self.graphql(f'''mutation PlanRelation($issue:ID!,$target:ID!){{
          {operation}(input:{{issueId:$issue,{key}:$target}}){{clientMutationId}}
        }}''', issue=issue, target=target)
        if operation not in data:
            raise PlanError("GitHub did not confirm the relationship operation")

    def card(self, project, issue):
        data = self.graphql('''mutation PlanCard($project:ID!,$issue:ID!){
          addProjectV2ItemById(input:{projectId:$project,contentId:$issue}){item{id}}
        }''', project=project, issue=issue)
        return data["addProjectV2ItemById"]["item"]["id"]

    def field(self, project, item, field, value):
        if value is None:
            query = '''mutation PlanField($project:ID!,$item:ID!,$field:ID!){
              clearProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field}){projectV2Item{id}}
            }'''
            self.graphql(query, project=project, item=item, field=field)
        else:
            query = '''mutation PlanField($project:ID!,$item:ID!,$field:ID!,$value:ProjectV2FieldValue!){
              updateProjectV2ItemFieldValue(input:{projectId:$project,itemId:$item,fieldId:$field,value:$value}){projectV2Item{id}}
            }'''
            self.graphql(query, project=project, item=item, field=field, value=value)

    def issue_type(self, config, issue, type_name):
        result = self.update(config, issue, {"type": type_name})
        if not isinstance(result, dict) or (result.get("type") or {}).get("name") != type_name:
            raise PlanError("GitHub did not confirm the native issue type; push access is required")


def _project(records):
    projects = [r for r in records if r["fields"]["type"] == "Project"]
    if len(projects) != 1:
        raise PlanError("GitHub publication requires exactly one Plan Project")
    return projects[0]


def _config(records):
    github = _project(records)["fields"].get("github") or {}
    if not isinstance(github, dict):
        raise PlanError("Project github must be an object")
    if not REPO.fullmatch(str(github.get("repo", ""))) or not LOGIN.fullmatch(str(github.get("owner", ""))):
        raise PlanError("configure the Project github.repo and github.owner before publication")
    if type(github.get("number")) is not int or github["number"] <= 0 or not LOGIN.fullmatch(str(github.get("writer", ""))):
        raise PlanError("configure the Project github.number and named github.writer before publication")
    if github.get("type_mode") not in {"labels", "issue_types"}:
        raise PlanError("configure Project github.type_mode as labels or issue_types")
    return copy.deepcopy(github)


def _save(workspace, records, record, github, event=None):
    candidate = copy.deepcopy(record)
    candidate["fields"]["github"] = copy.deepcopy(github)
    event = event or {"operation": "github-binding", "actor": workspace.actor, "at": model.timestamp()}
    saved = workspace.commit(candidate, records, event)
    records[:] = [saved if r["id"] == record["id"] else r for r in records]
    return saved


def configure(workspace, repo, owner, number, writer, client=None, type_mode=None):
    """Bind the existing Project. Caller holds the write lock; no network writes."""
    records = workspace.records()
    project = _project(records)
    current = project["fields"].get("github") or {}
    config = {**current, "repo": repo, "owner": owner, "number": number, "writer": writer,
              "type_mode": type_mode or current.get("type_mode", "labels")}
    candidate = copy.deepcopy(project)
    candidate["fields"]["github"] = config
    _config([candidate])
    for key in ("repo", "owner", "number", "writer", "type_mode"):
        if current.get(key) is not None and current[key] != config[key]:
            raise PlanError(f"Project github.{key} is already configured; changing it requires a separate agreed migration")
    snapshot = (client or Gh()).snapshot(config)
    if current.get("node_id") and current["node_id"] != snapshot["project_id"]:
        raise PlanError("configured Project identity differs from GitHub")
    config["node_id"] = snapshot["project_id"]
    if config != current:
        _save(workspace, records, project, config)
    return {"configured": True, "project": project["id"], "repo": repo, "owner": owner, "number": number, "writer": writer}


def _source(records):
    # Publication checkpoints change revisions and bindings, not planning content.
    return model.digest([{ "id": r["id"], "path": r.get("path"), "body": r.get("body", ""),
                          "fields": {k: v for k, v in r["fields"].items() if k != "github"},
                          "board": ({k: v for k, v in (r["fields"].get("github") or {}).items()
                                     if k in {"repo", "owner", "number", "writer", "type_mode"}}
                                    if r["fields"]["type"] == "Project" else None)}
                         for r in sorted(records, key=lambda x: x["id"])])


def _title(record):
    return f"{record['id']}: {record['fields'].get('title', record['id'])}"


def _marker(workspace, record):
    return f"<!-- plan:{workspace.id}:{record['id']} -->"


def _body(workspace, record, current="", criteria=()):
    marker = _marker(workspace, record)
    start, end = marker.replace(" -->", ":start -->"), marker.replace(" -->", ":end -->")
    if current.count(start) != current.count(end) or current.count(start) > 1:
        raise PlanError(f"{record['id']}: issue has an invalid managed section")
    fields = record["fields"]
    text = record.get("body", "").strip()
    description = fields.get("description", "").strip()
    if record.get("path"):
        legacy = re.compile(r"<!--\s*okf:\s*" + re.escape(record["path"]) + r"\s*-->")
        text, description = legacy.sub("", text).strip(), legacy.sub("", description).strip()
    parts = [description] if description and description != text else []
    parts.append(text)
    if (fields.get("owner") or "").startswith("agent:"):
        parts.append(f"Plan owner: `{fields['owner']}`")
    if criteria:
        parts.append("## Acceptance criteria\n\n" + "\n".join(f"- [ ] {identifier}: {title}" for identifier, title in criteria))
    # These are source fields, never credentials or a claim token.
    if fields.get("traces"):
        parts.append("## Traces\n\n" + "\n".join(f"- {entry['to']}" for entry in fields["traces"]))
    content = "\n\n".join(x for x in parts if x)
    if re.search(r"<!--\s*plan:", content):
        raise PlanError(f"{record['id']}: source text contains a publisher marker")
    managed = start + "\n" + content + "\n" + marker + "\n" + end
    if start in current:
        before, _, rest = current.partition(start)
        old, _, after = rest.partition(end)
        if end in before or start in old:
            raise PlanError(f"{record['id']}: issue has an invalid managed section")
        return before + managed + after
    # Adopt an existing identity-only marker without copying it a second time.
    current = current.replace(marker, "")
    return current.rstrip() + ("\n\n" if current.strip() else "") + managed + "\n"


def _find(workspace, record, snapshot):
    milestone = record["fields"]["type"] == "Milestone"
    collection = snapshot["milestones"] if milestone else snapshot["issues"]
    marker = _marker(workspace, record)
    legacy = record.get("path")
    markers = [marker]
    if legacy:
        markers += [f"<!-- okf: {legacy} -->"]
    matches = []
    for issue in collection:
        body = issue.get("description" if milestone else "body") or ""
        hits = sum(body.count(m) for m in markers)
        if hits > 1 and not (body.count(marker) == 1 and len(markers) > 1 and body.count(markers[1]) == 1):
            raise PlanError(f"{record['id']}: duplicate issue markers")
        if hits:
            matches.append(issue)
    binding = record["fields"].get("github") or {}
    if binding.get("number"):
        matches += [x for x in collection if x["number"] == binding["number"]]
        if not any(x["number"] == binding["number"] for x in collection):
            raise PlanError(f"{record['id']}: bound GitHub identity is missing; refusing replacement")
    unique = {x["number"]: x for x in matches}
    if len(unique) > 1:
        raise PlanError(f"{record['id']}: issue binding and markers are ambiguous")
    issue = next(iter(unique.values()), None)
    if issue and binding.get("node_id") and binding["node_id"] != (issue.get("node_id") or issue.get("id")):
        raise PlanError(f"{record['id']}: bound GitHub node identity changed")
    if issue:
        body = issue.get("description" if milestone else "body") or ""
        identities = re.findall(r"<!--\s*plan:([^\s<>]+)\s*-->", body)
        expected = f"{workspace.id}:{record['id']}"
        if any(x not in {expected, expected + ":start", expected + ":end"} for x in identities):
            raise PlanError(f"{record['id']}: bound issue holds another Plan identity")
        card_id = binding.get("project_item_id")
        if card_id and (issue.get("card") or {}).get("id") != card_id:
            raise PlanError(f"{record['id']}: bound Project item identity is missing or changed")
    return issue


def _selection(workspace, records, snapshot, config):
    selected = [r for r in records if r["fields"]["type"] in WORK | {"Milestone"}]
    found, by_number = {}, {}
    for record in selected:
        binding = record["fields"].get("github") or {}
        if binding.get("repo") and binding["repo"] != config["repo"]:
            raise PlanError(f"{record['id']}: issue binding belongs to another repository")
        issue = _find(workspace, record, snapshot)
        if issue:
            key = (record["fields"]["type"] == "Milestone", issue["number"])
            if key in by_number:
                raise PlanError("two Plan records bind the same GitHub identity")
            by_number[key] = record["id"]
        found[record["id"]] = issue
    if config.get("node_id") and config["node_id"] != snapshot["project_id"]:
        raise PlanError("configured Project node identity changed")
    return selected, found


def _desired(workspace, records, selected, found, snapshot, config):
    records = model.Records(records)
    criteria_by_item = {}
    for record in records:
        fields = record["fields"]
        if fields["type"] == "AcceptanceCriterion" and fields.get("item"):
            item = model.resolve(records, fields["item"])["id"]
            criteria_by_item.setdefault(item, []).append((record["id"], fields.get("title", record["id"])))
    desired = {}
    for record in selected:
        fields, identifier = record["fields"], record["id"]
        issue = found[identifier]
        milestone = fields["type"] == "Milestone"
        if fields.get("protected"):
            raise PlanError(f"{identifier}: protected work cannot be published automatically")
        if milestone:
            desired[identifier] = {"title": _title(record), "description": _body(workspace, record, (issue or {}).get("description") or ""),
                                   "due_on": fields.get("target_date") + "T00:00:00Z" if fields.get("target_date") else None}
            continue
        if issue and issue.get("viewerCanUpdate") is not True:
            raise PlanError(f"{identifier}: GitHub does not permit issue updates")
        state = model.effective_state(record, records) or "backlog"
        option = state.replace("_", " ").capitalize()
        status = snapshot["fields"].get("Status") or {}
        if option not in status.get("options", {}):
            raise PlanError(f"{identifier}: Project Status lacks the {option} option")
        board = {"Status": option}
        managed_dates = (fields.get("github") or {}).get("plan_dates") or []
        for key, name in DATES.items():
            if fields.get(key) is not None or name in managed_dates:
                field = snapshot["fields"].get(name) or {}
                if field.get("type") != "DATE":
                    raise PlanError(f"{identifier}: Project date field {name} is missing or unsupported")
                board[name] = fields.get(key)
        parent = model.resolve(records, fields["parent"])["id"] if fields.get("parent") else None
        if parent and parent not in found:
            raise PlanError(f"{identifier}: issue parent is not publishable work")
        blockers = [model.resolve(records, x)["id"] for x in fields.get("blocked_by") or []]
        if any(x not in found or model.resolve(records, x)["fields"]["type"] not in WORK for x in blockers):
            raise PlanError(f"{identifier}: a blocker is not publishable work")
        milestone_id = model.resolve(records, fields["milestone"])["id"] if fields.get("milestone") else None
        owner = fields.get("owner")
        if owner:
            model.require_actor(owner)
            if owner.startswith("human:") and not LOGIN.fullmatch(owner[6:]):
                raise PlanError(f"{identifier}: owner has no GitHub human login; assignment cannot be omitted")
        labels = set((issue or {}).get("labels") or [])
        previous = set((fields.get("github") or {}).get("plan_labels") or [])
        wanted = set(fields.get("tags") or [])
        if config["type_mode"] == "labels":
            wanted.add("type:" + fields["type"].lower())
            foreign = {x for x in labels if x.startswith("type:")} - wanted
            if foreign:
                raise PlanError(f"{identifier}: live type labels conflict with Plan")
            if issue and fields.get("github", {}).get("pushed_hash") and "type:" + fields["type"].lower() not in labels:
                raise PlanError(f"{identifier}: a published type label was removed")
        elif fields["type"] not in snapshot["issue_types"] or (issue and issue.get("viewerCanType") is not True):
            raise PlanError(f"{identifier}: configured native issue type is unavailable or cannot be assigned")
        if wanted - set(snapshot["labels"]):
            raise PlanError(f"{identifier}: required labels are missing in GitHub; configure them before publication")
        criteria = sorted(criteria_by_item.get(identifier, []))
        payload = {"title": _title(record), "body": _body(workspace, record, (issue or {}).get("body") or "", criteria),
                   "state": "closed" if state in CLOSED else "open",
                   "state_reason": "not_planned" if state == "cancelled" else "completed" if state in CLOSED else "reopened",
                   "assignees": [owner[6:]] if owner and owner.startswith("human:") else [], "labels": sorted((labels - previous) | wanted)}
        desired[identifier] = {"issue": payload, "board": board, "parent": parent, "blockers": sorted(blockers),
                               "milestone": milestone_id, "type": fields["type"], "managed_labels": sorted(wanted)}
    nodes = {identifier: (issue["id"] if issue else "plan:" + identifier)
             for identifier, issue in found.items() if identifier in desired and "parent" in desired[identifier]}
    parents = {issue["id"]: issue.get("parent") for issue in snapshot["issues"]}
    for identifier, node in nodes.items():
        parent = desired[identifier]["parent"]
        parents[node] = nodes[parent] if parent else None
    counts = {}
    for parent in parents.values():
        if parent:
            counts[parent] = counts.get(parent, 0) + 1
    if any(counts.get(node, 0) > 100 for node in nodes.values()):
        raise PlanError("GitHub permits at most 100 sub-issues per parent; publication is blocked")
    managed = set(nodes.values())
    foreign_children = {issue["id"] for issue in snapshot["issues"]
                        if set(issue.get("sub_issues") or []) - set(parents)}
    for node in parents:
        seen, current = set(), node
        while current and current in parents:
            if current in seen:
                raise PlanError("GitHub issue hierarchy has a cycle")
            seen.add(current)
            current = parents[current]
        if seen & managed and seen & foreign_children:
            raise PlanError("a related cross-repository sub-issue graph cannot be checked; publication is blocked")
        if seen & managed and (len(seen) > 8 or current is not None):
            raise PlanError("GitHub issue hierarchy exceeds depth 8 or has an unreadable ancestor")
    return desired


def _read(workspace, client):
    records = model.Records(workspace.records())
    config = _config(records)
    snapshot = client.snapshot(config)
    publication = copy.deepcopy(workspace.control().get("github_publication") or {})
    active = publication.get("active")
    active = _active_records(records, active) if active else None
    intent = (active or {}).get("binding_intent")
    effective = records
    if intent:
        # Preview the checked binding intent without committing it or old source text.
        bound = copy.deepcopy(model.resolve(records, intent["id"]))
        bound["fields"]["github"] = copy.deepcopy(intent["github"])
        effective = model.Records(bound if record["id"] == bound["id"] else record for record in records)
    selected, found = _selection(workspace, effective, snapshot, config)
    desired = _desired(workspace, effective, selected, found, snapshot, config)
    return records, config, snapshot, selected, found, desired, publication, active


def _comparable(key, value):
    if key == "state":
        return str(value).lower()
    if key in {"labels", "assignees", "blockers"}:
        return sorted(value or [])
    return value


def _changes(record, issue, wanted, found, snapshot, config):
    """Public field differences. Hash free text rather than print record content."""
    changes = {}

    def compare(key, before, after):
        if key in {"body", "description", "title"}:
            before, after = model.digest(before), model.digest(after)
        before, after = _comparable(key, before), _comparable(key, after)
        if before != after:
            changes[key] = {"before": before, "after": after}

    issue = issue or {}
    if record["fields"]["type"] == "Milestone":
        for key, value in wanted.items():
            compare(key, issue.get(key), value)
        return changes
    for key, value in wanted["issue"].items():
        if key == "state_reason":
            if wanted["issue"]["state"] == "closed":
                compare(key, str(issue.get("stateReason", "")).lower(), value)
        else:
            compare(key, issue.get(key), value)
    for key, value in wanted["board"].items():
        compare(key, (issue.get("card") or {}).get(key), value)
    for key, attribute in (("parent", "id"), ("milestone", "number")):
        target = wanted[key]
        expected = ((found[target] or {}).get(attribute) or "plan:" + target) if target else None
        compare(key, issue.get(key), expected)
    compare("blockers", issue.get("blocked_by"), [(found[target] or {}).get("id") or "plan:" + target for target in wanted["blockers"]])
    if not issue.get("card"):
        compare("Project", None, snapshot["project_id"])
    if config["type_mode"] == "issue_types":
        compare("type", (issue.get("issueType") or {}).get("id"), snapshot["issue_types"][wanted["type"]])
    return changes


def preview(workspace, client=None):
    """Read a source and live board. No mutation and no token-bearing record output."""
    records, config, snapshot, selected, found, desired, _publication, active = _read(workspace, client or Gh())
    source = _source(records)
    revisions = {r["id"]: r.get("revision", 0) for r in records}
    fingerprint = _fingerprint(source, revisions, snapshot, desired, active)
    same_source = active and _same_source(active, source, revisions)
    return {"mode": "preview", "fingerprint": fingerprint, "source_revision": active["source_revision"] if same_source else model.digest(revisions),
            "source": source, "writer": config["writer"], "items": [
                {"id": r["id"], "action": ("update" if changes else "check") if found[r["id"]] else "create",
                 "number": (found[r["id"]] or {}).get("number"), "changes": changes}
                for r in selected
                for changes in [_changes(r, found[r["id"]], desired[r["id"]], found, snapshot, config)]],
            "warnings": ["GitHub changes cannot be atomic with the Plan store; incomplete publication blocks success"]}


def _checkpoint(workspace, publication, active):
    publication["active"] = copy.deepcopy(active)
    control = workspace.control()
    control["github_publication"] = copy.deepcopy(publication)
    workspace.save_control(control)


def _same_source(active, source, revisions):
    return active.get("source") == source and active.get("revisions") == revisions


def _fingerprint(source, revisions, snapshot, desired, active=None):
    if active and _same_source(active, source, revisions):
        return active["fingerprint"]
    inputs = {"source": source, "revisions": revisions, "live": snapshot, "desired": desired}
    if active:
        # A replacement preview must also accept the retained recovery evidence.
        inputs["resume"] = active
    return model.digest(inputs)


def _binding_identity(record):
    return model.digest({key: record.get(key) for key in ("id", "path", "native_id", "schema_version", "workspace_id")}
                        | {"type": record["fields"]["type"]})


def _edited_after_intent(current, intent, applied):
    """Check an unchanged binding and history prefix followed by Plan operations."""
    evidence = intent.get("history")
    if not evidence or _binding_identity(current) != evidence["identity"]:
        return False
    count = evidence["count"] + int(applied)
    revision = intent["before_revision"] + int(applied)
    events = current.get("events", [])
    extra = current.get("revision", 0) - revision
    side = "after" if applied else "before"
    return (extra > 0 and len(events) == count + extra
            and model.digest(events[:count]) == evidence[side + "_events"]
            and model.digest(current["fields"].get("github")) == evidence[side + "_binding"]
            and all(event.get("action") and event.get("result", {}).get("id") == current["id"]
                    and event["result"].get("revision") == revision + offset
                    for offset, event in enumerate(events[count:], 1)))


def _active_records(records, active):
    """Resolve a binding intent without accepting a changed binding or history."""
    active = copy.deepcopy(active)
    if set(active["pending_creates"]) - {r["id"] for r in records}:
        raise PlanError("a pending GitHub create has no Plan record; inspect before recovery")
    intent = active.get("binding_intent")
    if intent:
        current = model.resolve(records, intent["id"])
        digest = model.digest(current)
        before_revision = intent["before_revision"]
        if active["revisions"].get(intent["id"]) != before_revision:
            raise PlanError("publication binding intent has an inconsistent source revision")
        if ((current.get("revision", 0) == before_revision and digest == intent["before"])
                or _edited_after_intent(current, intent, False)):
            if "github" in intent:
                if model.digest(intent["github"]) != intent["history"]["after_binding"]:
                    raise PlanError("publication binding differs from its recorded publisher intent; inspect before recovery")
                return active  # Apply the checked binding before replacing its managed-field evidence.
        elif ((current.get("revision") == before_revision + 1 and digest == intent["after"])
              or _edited_after_intent(current, intent, True)):
            active["revisions"][intent["id"]] = before_revision + 1
        else:
            raise PlanError("publication binding differs from its recorded publisher intent; inspect before recovery")
        active.pop("binding_intent")
    return active


def _binding(workspace, records, record, github, publication, active):
    event = {"operation": "github-binding", "publication": active["fingerprint"],
             "actor": workspace.actor, "at": model.timestamp()}
    expected = copy.deepcopy(record)
    expected["fields"]["github"] = copy.deepcopy(github)
    expected["revision"] = record.get("revision", 0) + 1
    expected["schema_version"], expected["workspace_id"] = 1, workspace.id
    expected["native_id"] = record.get("native_id") or workspace.native_id(record["id"])
    expected.setdefault("events", []).append(event)
    active["binding_intent"] = {"id": record["id"], "before_revision": record.get("revision", 0),
                                "before": model.digest(record), "after": model.digest(expected), "github": copy.deepcopy(github),
                                "history": {"identity": _binding_identity(expected), "count": len(record.get("events", [])),
                                            "before_events": model.digest(record.get("events", [])),
                                            "after_events": model.digest(expected["events"]),
                                            "before_binding": model.digest(record["fields"].get("github")),
                                            "after_binding": model.digest(github)}}
    _checkpoint(workspace, publication, active)
    _save(workspace, records, record, github, event)
    active["revisions"] = {r["id"]: r.get("revision", 0) for r in records}
    active.pop("binding_intent")
    _checkpoint(workspace, publication, active)


def _identity(issue):
    number = issue.get("number")
    node = issue.get("node_id") or issue.get("id")
    if type(number) is not int or number <= 0 or not isinstance(node, str) or not node:
        raise PlanError("GitHub did not return a checked issue identity; inspect before retry")
    return {"number": number, "node_id": node, "url": issue.get("url") or issue.get("html_url")}


def apply(workspace, fingerprint, writer, client=None):
    """Publish one preview. Caller holds the write gate until checkpoints are published."""
    client = client or Gh()
    records, config, snapshot, selected, found, desired, publication, active = _read(workspace, client)
    records = list(records)  # Binding commits replace records; keep the read index immutable.
    if writer != config["writer"] or snapshot["login"] != config["writer"]:
        raise PlanError("only the configured writer authenticated as the actual GitHub viewer can publish")
    source = _source(records)
    revisions = {r["id"]: r.get("revision", 0) for r in records}
    if active:
        if fingerprint != _fingerprint(source, revisions, snapshot, desired, active):
            raise PlanError("publication fingerprint changed; preview again before writing")
        if not _same_source(active, source, revisions):
            # Keep uncertain creates and durable bindings; replace only the accepted source.
            active.update(fingerprint=fingerprint, source=source, revisions=revisions,
                          source_revision=model.digest(revisions))
        intent = active.get("binding_intent")
        if intent:
            current = model.resolve(records, intent["id"])
            _binding(workspace, records, current, intent["github"], publication, active)
        elif active != publication["active"]:
            _checkpoint(workspace, publication, active)
    else:
        expected = model.digest({"source": source, "revisions": revisions, "live": snapshot, "desired": desired})
        last = publication.get("last") or {}
        replay = (last.get("fingerprint") == fingerprint and last.get("source") == source and last.get("revisions") == revisions)
        if fingerprint != expected and not replay:
            raise PlanError("publication fingerprint changed; preview again before writing")
        if replay and any(_changes(r, found[r["id"]], desired[r["id"]], found, snapshot, config) for r in selected):
            raise PlanError("GitHub changed after publication; preview again before writing")
        active = {"fingerprint": fingerprint, "source": source, "revisions": revisions, "pending_creates": [],
                  "source_revision": last["source_revision"] if replay else model.digest(revisions)}
        _checkpoint(workspace, publication, active)
    for record in selected:
        identifier = record["id"]
        issue = found[identifier]
        if not issue:
            if identifier in active["pending_creates"]:
                raise PlanError(f"{identifier}: a prior create has an unknown outcome; inspect GitHub before recovery")
            active["pending_creates"].append(identifier)
            _checkpoint(workspace, publication, active)
            try:
                created = client.create(config, snapshot, record, desired[identifier].get("description") or desired[identifier]["issue"]["body"])
            except PlanError:
                # A failed reply is not proof that GitHub did not create the issue.
                refreshed = client.snapshot(config)
                issue = _find(workspace, record, refreshed)
                if issue is None:
                    raise PlanError(f"{identifier}: create outcome is unknown; no duplicate create will be retried") from None
            else:
                # Persist a confirmed identity before any further GitHub operation.
                current = model.resolve(records, identifier)
                binding = {**(current["fields"].get("github") or {}), **_identity(created)}
                _binding(workspace, records, current, binding, publication, active)
                issue = created
            found[identifier] = issue
        current = model.resolve(records, identifier)
        binding = {**(current["fields"].get("github") or {}), **_identity(issue)}
        if binding != current["fields"].get("github"):
            _binding(workspace, records, current, binding, publication, active)
        if identifier in active["pending_creates"]:
            active["pending_creates"].remove(identifier)
            _checkpoint(workspace, publication, active)
    # All identities are durable before any relationship or Project write.
    snapshot = client.snapshot(config)
    selected, found = _selection(workspace, records, snapshot, config)
    if any(found[r["id"]] is None for r in selected):
        raise PlanError("a created identity cannot be read back; inspect before retry")
    desired = _desired(workspace, records, selected, found, snapshot, config)
    # Free every obsolete placement before any insertion, including a swap at the child limit.
    for record in selected:
        if record["fields"]["type"] == "Milestone":
            continue
        identifier = record["id"]
        issue, wanted = found[identifier], desired[identifier]
        parent = found[wanted["parent"]]["id"] if wanted["parent"] else None
        if issue.get("parent") and issue["parent"] != parent:
            client.relation("removeSubIssue", issue["parent"], issue["id"])
            issue["parent"] = None
        blockers = {found[x]["id"] for x in wanted["blockers"]}
        for blocker in sorted(set(issue.get("blocked_by") or []) - blockers):
            client.relation("removeBlockedBy", issue["id"], blocker)
            issue["blocked_by"].remove(blocker)
    for record in selected:
        identifier = record["id"]
        issue = found[identifier]
        wanted = desired[identifier]
        milestone = record["fields"]["type"] == "Milestone"
        if milestone:
            patch = {key: value for key, value in wanted.items() if (issue.get(key) or None) != (value or None)}
            if patch:
                client.update(config, issue, patch, milestone=True)
            continue
        payload = copy.deepcopy(wanted["issue"])
        payload["milestone"] = found[wanted["milestone"]]["number"] if wanted["milestone"] else None
        patch = {}
        for key, value in payload.items():
            if key == "state_reason":
                continue
            if _comparable(key, issue.get(key)) != _comparable(key, value):
                patch[key] = value
        if payload["state"] == "closed" and str(issue.get("stateReason", "")).lower() != payload["state_reason"]:
            patch["state"] = "closed"
        if "state" in patch:
            patch["state_reason"] = payload["state_reason"]
        if patch:
            client.update(config, issue, patch)
        if config["type_mode"] == "issue_types" and (issue.get("issueType") or {}).get("id") != snapshot["issue_types"][wanted["type"]]:
            client.issue_type(config, issue, wanted["type"])
        parent = found[wanted["parent"]]["id"] if wanted["parent"] else None
        if parent and issue.get("parent") != parent:
            client.relation("addSubIssue", parent, issue["id"])
        blockers = {found[x]["id"] for x in wanted["blockers"]}
        for blocker in sorted(blockers - set(issue.get("blocked_by") or [])):
            client.relation("addBlockedBy", issue["id"], blocker)
        fresh = snapshot
        card = issue.get("card")
        if not card:
            try:
                client.card(snapshot["project_id"], issue["id"])
            except PlanError:
                pass  # A board workflow can add it before this mutation.
            fresh = client.snapshot(config)
            card = (_find(workspace, record, fresh) or {}).get("card")
            if not card:
                raise PlanError(f"{identifier}: Project membership could not be confirmed")
        for name, value in wanted["board"].items():
            if card.get(name) == value:
                continue
            field = fresh["fields"][name]
            typed = ({"singleSelectOptionId": field["options"][value]} if name == "Status" else {"date": value}) if value is not None else None
            client.field(snapshot["project_id"], card["id"], field["id"], typed)
    # A checkpoint is a success only after the affected values are read back.
    verified = client.snapshot(config)
    for record in selected:
        identifier, wanted = record["id"], desired[record["id"]]
        issue = _find(workspace, record, verified)
        if not issue:
            raise PlanError(f"{identifier}: issue is missing at verification")
        milestone = record["fields"]["type"] == "Milestone"
        if milestone:
            if any((issue.get(key) or None) != (value or None) for key, value in wanted.items()):
                raise PlanError(f"{identifier}: milestone verification failed; no publication success checkpoint")
            continue
        payload = wanted["issue"]
        for key in ("title", "body", "state", "assignees", "labels"):
            if _comparable(key, issue.get(key)) != _comparable(key, payload[key]):
                raise PlanError(f"{identifier}: GitHub {key} verification failed; no publication success checkpoint")
        if payload["state"] == "closed" and str(issue.get("stateReason", "")).lower() != payload["state_reason"]:
            raise PlanError(f"{identifier}: close reason verification failed")
        if issue.get("milestone") != (found[wanted["milestone"]]["number"] if wanted["milestone"] else None):
            raise PlanError(f"{identifier}: milestone membership verification failed")
        if issue.get("parent") != (found[wanted["parent"]]["id"] if wanted["parent"] else None):
            raise PlanError(f"{identifier}: parent verification failed")
        if set(issue.get("blocked_by") or []) != {found[x]["id"] for x in wanted["blockers"]}:
            raise PlanError(f"{identifier}: blocker verification failed")
        if config["type_mode"] == "issue_types" and (issue.get("issueType") or {}).get("id") != verified["issue_types"][wanted["type"]]:
            raise PlanError(f"{identifier}: native issue type verification failed")
        if not issue.get("card") or any(issue["card"].get(key) != value for key, value in wanted["board"].items()):
            raise PlanError(f"{identifier}: Project field verification failed")
        current = model.resolve(records, identifier)
        binding = {**(current["fields"].get("github") or {}), "project_item_id": issue["card"]["id"],
                   "plan_labels": wanted["managed_labels"], "plan_dates": [x for x in wanted["board"] if x != "Status"],
                   "pushed_hash": model.digest(wanted)}
        if binding != current["fields"].get("github"):
            _binding(workspace, records, current, binding, publication, active)
    publication["last"] = {"fingerprint": fingerprint, "source": source,
                           "source_revision": active["source_revision"],
                           "revisions": {r["id"]: r.get("revision", 0) for r in records},
                           "at": model.timestamp(), "items": len(selected)}
    _checkpoint(workspace, publication, None)
    return {"published": True, "fingerprint": fingerprint, "source_revision": active["source_revision"], "items": len(selected)}
