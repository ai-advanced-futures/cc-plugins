"""`github apply`: one change, one gh call, one write back.

The write back is load-bearing. A page that GitHub holds but that carries no
`github` field is pushed again on the next run, so the repository gets two
issues for one story. Each create therefore writes the number, the node ID,
the URL, the `pushed_hash`, and the `synced` pair before the next change runs.
"""
import json
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timezone
from pathlib import Path

from . import UsageError, ghmodel, ghplan, ghsnapshot
from .ids import resolve
from .lock import held, refresh as refresh_lock, write_lock
from .logbook import append_entries, entry_line
from .page import load_page, write_page
from .textsafe import escape_controls
from .tree import bundle_dir

CREATE_ISSUE = """
mutation($repo: ID!, $title: String!, $body: String!) {
  createIssue(input: {repositoryId: $repo, title: $title, body: $body}) {
    issue { number id url }
  }
}
"""

# replaceParent moves a child that has a parent. A new issue has none, so
# the one mutation serves the create and the update.
ADD_SUB_ISSUE = """
mutation($p: ID!, $c: ID!, $replace: Boolean) {
  addSubIssue(input: {issueId: $p, subIssueId: $c,
                      replaceParent: $replace}) { clientMutationId }
}
"""

REMOVE_SUB_ISSUE = """
mutation($p: ID!, $c: ID!) {
  removeSubIssue(input: {issueId: $p, subIssueId: $c}) { clientMutationId }
}
"""

# The input field names of the two blocked-by mutations are not in a source
# that this build read. The probe runs each one (D37). [inferred]
ADD_BLOCKED_BY = """
mutation($issue: ID!, $blocker: ID!) {
  addBlockedBy(input: {issueId: $issue, blockingIssueId: $blocker}) {
    clientMutationId
  }
}
"""

REMOVE_BLOCKED_BY = """
mutation($issue: ID!, $blocker: ID!) {
  removeBlockedBy(input: {issueId: $issue, blockingIssueId: $blocker}) {
    clientMutationId
  }
}
"""

# The card of an issue on the Project. A Status value and a date need its
# ID, so the create and `add_to_project` both read it from the reply.
ADD_TO_PROJECT = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
    item { id }
  }
}
"""

# The card of one issue on one Project. The add mutation refuses an issue that
# a board workflow already put on the Project, so the card is read instead.
CARD_OF_ISSUE = """
query($content: ID!) {
  node(id: $content) {
    ... on Issue { projectItems(first: 20) { nodes { id project { id } } } }
  }
}
"""

# A Project value is a GraphQL write. Each mutation below is the one GitHub
# holds for that change; none of them can be a placeholder, because a
# placeholder sends the name of the action to the API as a query. [inferred]
SET_STATUS = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item,
      fieldId: $field, value: {singleSelectOptionId: $option}}) {
    projectV2Item { id }
  }
}
"""

SET_DATE = """
mutation($project: ID!, $item: ID!, $field: ID!, $date: Date!) {
  updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item,
      fieldId: $field, value: {date: $date}}) {
    projectV2Item { id }
  }
}
"""

CLEAR_VALUE = """
mutation($project: ID!, $item: ID!, $field: ID!) {
  clearProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item,
      fieldId: $field}) {
    projectV2Item { id }
  }
}
"""

CREATE_FIELD = """
mutation($project: ID!, $name: String!,
         $dataType: ProjectV2CustomFieldType!,
         $options: [ProjectV2SingleSelectFieldOptionInput!]) {
  createProjectV2Field(input: {projectId: $project, name: $name,
      dataType: $dataType, singleSelectOptions: $options}) {
    projectV2Field { ... on ProjectV2SingleSelectField { id } }
  }
}
"""

# GitHub holds no mutation that adds one option. `updateProjectV2Field`
# replaces the whole option list, so the change carries every option and the
# call sends all of them. [inferred]
SET_OPTIONS = """
mutation($field: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  updateProjectV2Field(input: {fieldId: $field,
      singleSelectOptions: $options}) {
    projectV2Field { ... on ProjectV2SingleSelectField { id } }
  }
}
"""


@dataclass
class _Run:
    """What one apply learns as it goes. A later change reads the number,
    the node ID, or the card ID that an earlier change of the run made."""
    # page ID -> the issue as the snapshot read it: the live values that an
    # update compares with the page.
    issues: dict
    numbers: dict
    node_ids: dict
    item_ids: dict
    criteria: dict
    tree: dict | None
    # page ID -> the path a write resolved, so `_log` names the same file
    # again with no second walk of the tree for each page.
    pushed: dict = dataclass_field(default_factory=dict)


def apply(root: Path, snapshot: dict, plan: ghplan.Plan, client,
          now: datetime | None = None) -> list[str]:
    """Execute the change set. Returns one line for each change it ran."""
    if plan.blocked:
        raise UsageError("the plan holds a refusal. Nothing was pushed:\n" +
                         "\n".join(plan.refusals))
    now = now or datetime.now(timezone.utc)
    # `plan` already walked the tree, and its walk travels on the plan.
    # `_write_back` needs the criteria of one page, and a walk for each change
    # would read the tree one time for each item, inside the write lock.
    tree = plan.tree or None
    stored = ghplan.numbers_of(ghplan.work_items(root, tree))
    issues = ghsnapshot.issues_by_page(snapshot, stored)
    run = _Run(
        issues=issues,
        # `refs` holds the milestones as well as the issues. A map of the
        # issues alone loses the number of a milestone that GitHub already
        # holds, so the new issue gets no milestone and its hash never
        # computes.
        numbers=dict(ghsnapshot.refs(snapshot, stored)),
        # A GitHub node ID is opaque: it cannot be built from an issue
        # number. The create gives it, and the sub-issue mutation needs it.
        # [inferred]
        node_ids={page: issue["node_id"] for page, issue in issues.items()},
        item_ids={page: issue["project_item"]["id"]
                  for page, issue in issues.items()
                  if (issue.get("project_item") or {}).get("id")},
        criteria=ghplan.criteria_of(root, tree),
        tree=tree)
    done = []
    with write_lock(root) as lock:
        try:
            for change in plan.changes:
                done.append(_run(root, snapshot, change, client, run))
                # Each change is a call to GitHub. A lock older than 60
                # seconds reads as stale, so a push of many issues would have
                # its lock deleted under it and a second prd.py would write
                # beside it.
                refresh_lock(lock)
        finally:
            # A change that fails stops the run, but each page written before
            # it is already changed. Its Sync line goes into the log all the
            # same, or the Event log misses a change that a page holds. A
            # lock that another process took is the one case with no write:
            # that process may be writing the log now.
            if run.pushed and held(lock):
                _log(root, run.pushed, now)
    return [line for line in done if line]


def _run(root, snapshot, change, client, run) -> str:
    page, detail = change.page, change.detail
    if change.action == "create_issue":
        issue = _create_issue(snapshot, change, client)
        run.numbers[page] = issue["number"]
        run.node_ids[page] = issue["id"]
        # The number goes onto the page before any other call. A call that
        # fails after the create would otherwise leave an issue that no page
        # names, and the next run would make a second one.
        _write_ids(root, page, issue, run)
        _finish_issue(snapshot, change, client, issue, run.numbers)
        _relate(client, run, change, issue["id"], live={})
        run.item_ids[page] = _add_to_project(snapshot, client, issue["id"],
                                             page)
        client.text(_status_argv(snapshot, run.item_ids[page], page,
                                 detail["option"]))
        _set_dates(snapshot, client, run.item_ids[page], page, detail, live={})
        synced = {"state": detail["state"]}
        if detail.get("assignee"):
            client.text(["issue", "edit", str(issue["number"]),
                         "--add-assignee", detail["assignee"]])
            synced["owner"] = f"human:{detail['assignee']}"
        # Each value is in GitHub now, so the hash and the synced pair name
        # values that GitHub holds.
        _write_back(root, change, snapshot, run, synced=synced)
        return (f"created #{escape_controls(issue['number'])} for "
                f"{escape_controls(page)}")
    if change.action == "update_issue":
        _update_issue(snapshot, change, client, run.numbers)
        live = run.issues.get(page) or {}
        _relate(client, run, change, detail["node_id"], live)
        _set_dates(snapshot, client, run.item_ids.get(page), page, detail,
                   live.get("project_item") or {})
        # An update sends the push-only values. `synced` names the two-
        # direction values, which `set_status` and `set_assignee` send, so
        # the update leaves it alone.
        _write_back(root, change, snapshot, run)
        return (f"updated #{escape_controls(detail['number'])} for "
                f"{escape_controls(page)}")
    if change.action == "add_to_project":
        run.item_ids[page] = _add_to_project(snapshot, client,
                                             detail["node_id"], page)
        return (f"put #{escape_controls(detail['number'])} on the Project "
                f"for {escape_controls(page)}")
    if change.action == "set_status":
        client.text(_status_argv(
            snapshot, detail.get("item_id") or run.item_ids.get(page), page,
            detail["option"]))
        _store_synced(root, page, "state", detail["state"], run)
        return f"set_status {escape_controls(page)}"
    if change.action == "set_assignee":
        client.text(_argv(snapshot, change))
        _store_synced(root, page, "owner", detail["owner"], run)
        return f"set_assignee {escape_controls(page)}"
    if change.action == "create_milestone":
        found = client.json(
            ["api", f"repos/{snapshot['repo']['full']}/milestones",
             *_milestone_args(detail)])
        run.numbers[page] = found["number"]
        return f"made the milestone {escape_controls(detail['title'])}"
    if change.action == "reread_fields":
        # The probe has not answered whether an option ID survives a change of
        # the option set (D37). Read the field list again and take the new IDs.
        snapshot["project"]["fields"] = ghsnapshot.fetch_fields(client,
                                                               snapshot)
        return "read the Project fields again"
    client.text(_argv(snapshot, change))
    return f"{change.action} {escape_controls(page) if page else ''}".strip()


def _add_to_project(snapshot, client, node_id, page) -> str:
    """The ID of the card. An issue that is already on the board is done:
    a board workflow can put an issue there before this run, and GitHub then
    refuses the add with "Content already exists in this project". The card
    it has is the one to use. [inferred]"""
    args = ["api", "graphql", "-f", f"query={ADD_TO_PROJECT}",
            "-f", f"project={snapshot['project']['node_id']}",
            "-f", f"content={node_id}"]
    try:
        result = client.json(args)
        if not _already_on_board(result):
            return _mutation(result, "addProjectV2ItemById", "item", page)["id"]
    except UsageError as error:
        if not _already_on_board(str(error)):
            raise
    card = _card_on_board(snapshot, client, node_id)
    if not card:
        raise UsageError(
            f"addProjectV2ItemById says {escape_controls(page)} is on the "
            f"Project, but its "
            f"card was not found. Each change before it is on its page. "
            f"Correct the cause and run `github plan` again.")
    return card


def _already_on_board(reply) -> bool:
    text = reply if isinstance(reply, str) else json.dumps(reply or {})
    return "already exists in this project" in text.lower()


def _card_on_board(snapshot, client, node_id) -> str | None:
    result = client.json(["api", "graphql", "-f", f"query={CARD_OF_ISSUE}",
                          "-f", f"content={node_id}"])
    nodes = ((((result or {}).get("data") or {}).get("node") or {})
             .get("projectItems") or {}).get("nodes") or []
    project = snapshot["project"]["node_id"]
    return next((node["id"] for node in nodes
                 if (node.get("project") or {}).get("id") == project), None)


def _create_issue(snapshot, change, client):
    result = client.json(["api", "graphql",
                          "-f", f"query={CREATE_ISSUE}",
                          "-f", f"repo={snapshot['repo']['node_id']}",
                          "-f", f"title={change.detail['title']}",
                          "-f", f"body={change.detail['body']}"])
    return _mutation(result, "createIssue", "issue", change.page)


def _mutation(result, name, key, page=None):
    """The value one mutation gave back. GraphQL reports an error as data
    with exit code 0, so an absent value stops the run here, with the
    message, and not later on a KeyError that names no page."""
    found = (((result or {}).get("data") or {}).get(name) or {}).get(key)
    if not found:
        errors = "; ".join(escape_controls(error.get("message", ""))
                           for error in (result or {}).get("errors") or [])
        shown = escape_controls(page) if page else ""
        raise UsageError(
            f"{name} gave no {key}{f' for {shown}' if page else ''}: "
            f"{errors or 'the reply was empty'}. Each change before it is "
            f"on its page. Correct the cause and run `github plan` again.")
    return found


def _finish_issue(snapshot, change, client, issue, numbers):
    """The create mutation carries the title and the body only. Every other
    value the plan computed needs its own call, or it never reaches GitHub
    and the next `pull` reports a false difference on the page. [inferred]"""
    detail = change.detail
    number = str(issue["number"])
    labels = detail.get("labels") or []
    if labels:
        client.text(["issue", "edit", number, *_label_args(labels)])
    _patch_issue(snapshot, detail, client, number, numbers)


def _patch_issue(snapshot, detail, client, number, numbers):
    """The milestone and the issue type, which `gh issue edit` does not take.
    An update runs it as well: both values are in the pushed hash, so a push
    that left them out would store the hash of a value GitHub never got."""
    patch = []
    milestone = detail.get("milestone_page")
    if milestone and milestone in numbers:
        patch += ["-F", f"milestone={numbers[milestone]}"]
    type_name = detail.get("type") or ""
    if type_name and not type_name.startswith("type:"):
        # A user-owned repository has no issue type, and its type travels as
        # the `type:` label. [inferred]
        patch += ["-f", f"type={type_name}"]
    if patch:
        client.text(["api",
                     f"repos/{snapshot['repo']['full']}/issues/{number}",
                     "-X", "PATCH", *patch])


def _update_issue(snapshot, change, client, numbers):
    detail = change.detail
    number = str(detail["number"])
    payload = detail.get("payload")
    args = ["issue", "edit", number]
    if payload:
        # An absent payload means the plan could not resolve a relationship,
        # so it holds no body. Sending an empty one would erase the issue
        # text and the OKF marker with it, and the next run would make a
        # second issue for this page.
        if payload.get("title"):
            args += ["--title", payload["title"]]
        args += ["--body", payload.get("body", "")]
    args += _label_args(detail.get("labels") or [])
    args += [arg for name in detail.get("remove_labels") or []
             for arg in ("--remove-label", name)]
    if len(args) > 3:
        client.text(args)
    _patch_issue(snapshot, detail, client, number, numbers)


def _label_args(labels) -> list:
    return [arg for name in labels for arg in ("--add-label", name)]


def _milestone_args(detail) -> list:
    """A milestone date is a whole day, which the API takes as a timestamp."""
    return ["-f", f"title={detail['title']}",
            "-f", f"description={detail['description']}",
            *(["-f", f"due_on={detail['due_on']}T00:00:00Z"]
              if detail.get("due_on") else [])]


def _relate(client, run, change, node_id, live):
    """The parent and the blockers, as links between two node IDs. A node
    ID is opaque, so it comes from a create of this run or from the
    snapshot, never from an issue number. [inferred]

    `live` is the issue as the snapshot read it, or {} for a new issue. A
    page that a later change of this run creates is not linked here: its
    hash does not compute, and the next run sends the link (P3-7)."""
    detail = change.detail
    parent = detail.get("parent_page")
    if parent and parent in run.node_ids:
        if run.numbers.get(parent) != live.get("parent"):
            client.text(["api", "graphql", "-f", f"query={ADD_SUB_ISSUE}",
                         "-f", f"p={run.node_ids[parent]}",
                         "-f", f"c={node_id}", "-F", "replace=true"])
    elif not parent and live.get("parent_id"):
        client.text(["api", "graphql", "-f", f"query={REMOVE_SUB_ISSUE}",
                     "-f", f"p={live['parent_id']}", "-f", f"c={node_id}"])
    wanted = {str(run.numbers[page]): run.node_ids[page]
              for page in detail.get("blocked_by_pages") or []
              if page in run.numbers and page in run.node_ids}
    have = live.get("blocked_by_ids") or {}
    for number in sorted(set(wanted) - set(have)):
        client.text(["api", "graphql", "-f", f"query={ADD_BLOCKED_BY}",
                     "-f", f"issue={node_id}", "-f",
                     f"blocker={wanted[number]}"])
    for number in sorted(set(have) - set(wanted)):
        client.text(["api", "graphql", "-f", f"query={REMOVE_BLOCKED_BY}",
                     "-f", f"issue={node_id}", "-f",
                     f"blocker={have[number]}"])


def _set_dates(snapshot, client, item_id, page, detail, live):
    """The two planned dates on the Project card. A date that the page no
    longer holds is cleared, because an old date would read as a person's
    edit on the next pull."""
    project = snapshot["project"]
    for key, name in zip(("planned_start", "planned_end"), ghplan.DATE_FIELDS):
        wanted = detail.get(key)
        if wanted == live.get(key):
            continue
        if not item_id:
            raise UsageError(
                f"{escape_controls(page)} has no card on the Project, so "
                f"its {name} date "
                f"cannot be set. Run `github plan` again.")
        args = ["-f", f"project={project['node_id']}", "-f", f"item={item_id}",
                "-f", f"field={_field(project, name)['id']}"]
        if wanted:
            # -f keeps the date a string: -F would read some values as a
            # number.
            client.text(["api", "graphql", "-f", f"query={SET_DATE}", *args,
                         "-f", f"date={wanted}"])
        else:
            client.text(["api", "graphql", "-f", f"query={CLEAR_VALUE}",
                         *args])


def _argv(snapshot, change) -> list:
    """The gh argv of a change that needs no answer."""
    detail = change.detail
    repo = snapshot["repo"]["full"]
    if change.action == "close_issue":
        return ["issue", "close", str(detail["number"]),
                "--reason", "not planned" if detail["reason"] == "NOT_PLANNED"
                else "completed"]
    if change.action == "reopen_issue":
        return ["issue", "reopen", str(detail["number"])]
    if change.action == "set_assignee":
        return ["issue", "edit", str(detail["number"]),
                "--add-assignee", detail["login"],
                *[arg for login in detail.get("remove_logins") or []
                  for arg in ("--remove-assignee", login)]]
    if change.action == "create_label":
        return ["label", "create", detail["name"], "--force"]
    if change.action == "create_issue_type":
        # An issue type belongs to the organization, which owns the
        # repository: the plan takes this path only when the owner is an
        # organization. `is_enabled` is required. -F sends it as a boolean.
        # [inferred]
        return ["api", f"orgs/{repo.split('/', 1)[0]}/issue-types",
                "-f", f"name={detail['name']}", "-F", "is_enabled=true"]
    if change.action == "update_milestone":
        return ["api", f"repos/{repo}/milestones/{detail['number']}",
                "-X", "PATCH", *_milestone_args(detail)]
    project = snapshot["project"]
    if change.action == "create_field":
        return ["api", "graphql", "-f", f"query={CREATE_FIELD}",
                "-f", f"project={project['node_id']}",
                "-f", f"name={detail['name']}",
                "-f", f"dataType={detail['data_type']}",
                *_option_args(detail)]
    if change.action == "create_option":
        return ["api", "graphql", "-f", f"query={SET_OPTIONS}",
                "-f", f"field={_field(project, detail['field'])['id']}",
                *_option_args(detail)]
    raise UsageError(f"{change.action} has no gh call")


def _status_argv(snapshot, item_id, page, option_name) -> list:
    project = snapshot["project"]
    field = _field(project, ghplan.STATUS_FIELD)
    option = (field.get("options") or {}).get(option_name)
    if not option:
        raise UsageError(
            f"the Project field {ghplan.STATUS_FIELD} has no option "
            f"{option_name}. Run `github plan` again: the option set changed "
            f"after this plan was built.")
    if not item_id:
        raise UsageError(
            f"{escape_controls(page)} has no card on the Project, so its "
            f"Status cannot be set. "
            f"Run `github plan` again.")
    return ["api", "graphql", "-f", f"query={SET_STATUS}",
            "-f", f"project={project['node_id']}",
            "-f", f"item={item_id}",
            "-f", f"field={field['id']}",
            "-f", f"option={option}"]


def _field(project, name):
    field = (project.get("fields") or {}).get(name)
    if not field:
        raise UsageError(
            f"the Project holds no field named {name}. Run `github plan` "
            f"again: the field list changed after this plan was built.")
    return field


def _option_args(detail) -> list:
    """The whole option list, as a GraphQL list of objects. gh builds that
    list from `options[][key]=value` fields, and starts the next object when
    a key repeats. One `-f options=<json>` field sends a string, and the
    input takes no string. The input needs all three keys. A DATE field
    sends no option. [inferred]"""
    return [arg for name in detail.get("options") or []
            for key, value in (("name", name), ("color", "GRAY"),
                               ("description", ""))
            for arg in ("-f", f"options[][{key}]={value}")]


def _write_ids(root, page_id, issue, run):
    path = resolve(root, page_id, run.tree)
    page = load_page(path)
    field = dict(page.frontmatter.get("github") or {})
    field.update(number=issue["number"], node_id=issue["id"],
                 url=issue["url"])
    page.frontmatter["github"] = field
    write_page(page)
    run.pushed[page_id] = path


def _write_back(root, change, snapshot, run, synced=None):
    """The pushed hash, and the synced pair when the caller sent the two-
    direction values. Runs after every call of the change is done."""
    path = resolve(root, change.page, run.tree)
    page = load_page(path)
    field = dict(page.frontmatter.get("github") or {})
    # `plan` already hashed this page against the same refs, so the update
    # path takes that value. It is None only when a relationship was
    # unresolved then, which the create below may since have resolved.
    planned = change.detail.get("pushed_hash")
    try:
        if change.action == "update_issue" and not change.detail.get("payload"):
            # The update sent no title or body, so GitHub holds the values of
            # no hash. With no hash the next plan pushes the page again
            # (P3-7), and a bound page stays bound. The test is on the
            # action: a create has no `payload` key but sent its text.
            field.pop("pushed_hash", None)
        else:
            field["pushed_hash"] = planned or ghmodel.push_hash(
                ghplan.stored_payload(change.page, page.frontmatter,
                                      page.body, snapshot, run.numbers,
                                      run.criteria))
    except ghmodel.Unresolved:
        # A relationship names a page that this same run creates later, so
        # the hash cannot be computed yet. The number is already on the
        # page, which is what stops a second issue for it. The next plan
        # pushes this page again, which rule P3-7 already allows. [inferred]
        field.pop("pushed_hash", None)
    if synced is not None:
        field["synced"] = synced
    page.frontmatter["github"] = field
    write_page(page)
    run.pushed[change.page] = path


def _store_synced(root, page_id, key, value, run):
    """One two-direction value that GitHub now holds."""
    path = resolve(root, page_id, run.tree)
    page = load_page(path)
    field = dict(page.frontmatter.get("github") or {})
    field["synced"] = dict(field.get("synced") or {}, **{key: value})
    page.frontmatter["github"] = field
    write_page(page)
    run.pushed[page_id] = path


def _log(root, pushed, now):
    bundle = bundle_dir(root, "roadmap")
    append_entries(bundle / "log.md", [
        entry_line("Sync", page_id, str(path.relative_to(bundle)),
                   "pushed to GitHub", "process:github", now)
        for page_id, path in sorted(pushed.items())], now)
