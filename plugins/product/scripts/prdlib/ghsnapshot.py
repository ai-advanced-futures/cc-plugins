"""One read of GitHub, as a plain dictionary.

`github plan` is a pure function of the pages and this dictionary. A test
therefore drives a recorded file and needs no network. `fetch` is the only
part that talks to GitHub. It makes one GraphQL call for each 100 issues,
one REST call, and three `gh project` calls.
"""
import json
from pathlib import Path

from . import UsageError
from .ghmodel import marker_target, page_id_of

# The API rejects a query that declares a variable it does not use, with
# `variableNotUsed`. The Project number is not part of this query, so it is
# not a variable of it. [inferred]
ISSUE_QUERY = """
query($owner: String!, $name: String!, $after: String,
      $firstPage: Boolean = true) {
  repository(owner: $owner, name: $name) {
    id
    labels(first: 100) @include(if: $firstPage) { totalCount nodes { name } }
    issueTypes(first: 20) @include(if: $firstPage) {
      totalCount nodes { id name }
    }
    issues(first: 100, after: $after, states: [OPEN, CLOSED]) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        number id url title body state stateReason
        issueType { name }
        milestone { number }
        labels(first: 50) { nodes { name } }
        assignees(first: 10) { nodes { login } }
        parent { number id }
        blockedBy(first: 50) { totalCount nodes { number id } }
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes { ... on ClosedEvent { actor { __typename login } } }
        }
      }
    }
  }
}
"""

# The issues page, one query for each 100. The labels, the issue types and
# the milestones do not page yet. A list that comes back full is a snapshot
# that misses a pushed page, and `plan` would make a second issue for it, so
# the read refuses instead. [inferred]
PAGE_SIZE = {"labels": 100, "issueTypes": 20, "milestones": 100}
# The blockers of one issue. The field name and its connection shape come
# from the spec table, and the probe checks them (D37). [inferred]
BLOCKERS_PAGE = 50


def load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def issues_by_page(data: dict, stored: dict | None = None) -> dict:
    """page ID -> the issue record. The OKF marker is the key, not the title:
    a person can rename an issue and the link must survive it.

    `_issue` reads the marker out of the body one time, into `okf`, so that
    key is the only source of the marker here. A second read of the body
    would make `okf: null` unreachable, and Task 17 needs it to tell a stray
    issue from a page. [inferred]

    `stored` maps an issue number to the page whose `github` field names it.
    An adopted page has the number, but its issue has no marker until the
    next apply sends the body, so the number finds the issue. With no
    number match, `plan` would make a second issue for that page. The marker
    wins: it is what GitHub holds."""
    found = {}
    issues = data.get("issues") or []
    for issue in issues:
        target = issue.get("okf")
        if target:
            found[page_id_of(target)] = issue
    for issue in issues:
        page = (stored or {}).get(issue["number"])
        if page and not issue.get("okf") and page not in found:
            found[page] = issue
    return found


def refs(data: dict, stored: dict | None = None) -> dict:
    """page ID -> GitHub number, for issues and for milestones."""
    numbers = {page: issue["number"]
               for page, issue in issues_by_page(data, stored).items()}
    for milestone in data.get("milestones") or []:
        target = milestone.get("okf")
        if target:
            numbers[page_id_of(target)] = milestone["number"]
    return numbers


def fetch(client, context) -> dict:
    """Read GitHub for one snapshot. Every later step reads this
    dictionary."""
    owner, name = context.repo.split("/", 1)
    repo, issue_nodes = _read_repository(client, owner, name)
    # `gh api` sends a POST when it gets a `-f` field and no method. The
    # milestone list is a read, so the call names GET and the fields become
    # query parameters.
    milestones = client.json(
        ["api", f"repos/{context.repo}/milestones", "--method", "GET",
         "-f", "state=all", "-f", f"per_page={PAGE_SIZE['milestones']}"]) or []
    _refuse_full("milestones", len(milestones))
    # `gh project field-list` gives no Project node ID, so the ID comes from
    # `gh project view`. Its default limit is 30, so the field read names its
    # own. [inferred]
    view = client.json(
        ["project", "view", str(context.project_number),
         "--owner", context.project_owner, "--format", "json"]) or {}
    fields = _field_list(client, context.project_owner, context.project_number)
    cards = _cards(_read_items(client, context.project_owner,
                               context.project_number))
    return {
        "repo": {"full": context.repo, "node_id": context.repo_node_id,
                 "owner_is_org": context.owner_is_org,
                 "owner_node_id": context.owner_node_id},
        # An issue type needs the `admin:org` scope. Without it the
        # plan takes the `type:` label path.
        "org_write": context.org_write,
        # The fallback actor of a pulled state change. A pull that replays
        # this file then names the same person as the live pull.
        "login": context.login,
        "project": {"owner": context.project_owner,
                    "number": context.project_number,
                    "node_id": view.get("id", ""),
                    "fields": fields},
        "issue_types": {node["name"]: node["id"] for node
                        in _checked("issueTypes", repo.get("issueTypes"))},
        "labels": [node["name"] for node
                   in _checked("labels", repo.get("labels"))],
        "milestones": [_milestone(item) for item in milestones],
        "issues": [_issue(node, cards)
                   for node in issue_nodes],
    }


def _read_repository(client, owner: str, name: str) -> tuple[dict, list]:
    """The first page of the repository read, and the issue nodes of every
    page. Only the first page reads the labels and the issue types. A read
    with fewer issues than the first page counts is refused, as a full list
    is: `plan` would make a second issue for each missing one. [inferred]"""
    first, nodes, cursor, seen = None, [], None, set()
    while True:
        args = ["api", "graphql", "-f", f"query={ISSUE_QUERY}",
                "-f", f"owner={owner}", "-f", f"name={name}"]
        if cursor:
            # `-f`, not `-F`: a cursor is a string, and `-F` changes a
            # value such as `true` or `@file`.
            args += ["-f", f"after={cursor}", "-F", "firstPage=false"]
        result = client.json(args)
        repo = ((result or {}).get("data") or {}).get("repository") or {}
        first = repo if first is None else first
        issues = repo.get("issues") or {}
        nodes += _nodes(issues)
        info = issues.get("pageInfo") or {}
        cursor = info.get("endCursor")
        if not (info.get("hasNextPage") and cursor) or cursor in seen:
            break
        seen.add(cursor)
    total = (first.get("issues") or {}).get("totalCount", 0)
    if len(nodes) < total or info.get("hasNextPage"):
        raise UsageError(
            f"this repository holds {total} issues, and the read got "
            f"{len(nodes)}. The snapshot would be short, and the plan would "
            f"make a second issue for a page that GitHub already holds. Run "
            f"the command again.")
    return first, nodes


def _nodes(value):
    return ((value or {}).get("nodes")) or []


def _checked(name, value):
    """The nodes of a list that did not truncate. [inferred]"""
    _refuse_full(name, (value or {}).get("totalCount", 0))
    return _nodes(value)


def _refuse_full(name, total):
    """Refuse a truncated read. A missing issue reads as a page GitHub does
    not hold, and `plan` would make a second issue for it. [inferred]"""
    if total >= PAGE_SIZE[name]:
        raise UsageError(
            f"this repository holds {total} {name}, and one read takes "
            f"{PAGE_SIZE[name]}. The snapshot would be short, and the plan "
            f"would make a second issue for a page that GitHub already "
            f"holds. Add paging to ghsnapshot.fetch before you sync this "
            f"repository.")


# `gh project field-list` gives the GraphQL type name, not the short name the
# plan compares against. [inferred]
FIELD_TYPES = {"ProjectV2SingleSelectField": "SINGLE_SELECT",
               "ProjectV2Field": "TEXT", "ProjectV2IterationField": "ITERATION"}


def _fields(project: dict) -> dict:
    out = {}
    for field in project.get("fields") or []:
        data_type = field.get("type", "")
        out[field["name"]] = {
            "id": field["id"],
            "data_type": FIELD_TYPES.get(data_type, data_type),
            "options": {option["name"]: option["id"]
                        for option in field.get("options") or []},
        }
    return out


# The most cards that one `gh project item-list` call reads. [inferred]
ITEM_LIMIT = 1000


def _item_list(client, owner: str, number) -> dict:
    return client.json(
        ["project", "item-list", str(number), "--owner", owner,
         "--format", "json", "--limit", str(ITEM_LIMIT)]) or {}


def _read_items(client, owner: str, number) -> dict:
    """The Project items, refused when the read is short (#182).

    `gh project item-list` can exit 0 with fewer items than `totalCount`, or
    with 0 items and a `totalCount` of 0, for a Project that holds cards. The
    plan would then read each issue as "not on the Project" and add it a
    second time. So a read with fewer items than its count is refused, and an
    empty read is read again: two empty reads are an empty Project. [inferred]"""
    items = _item_list(client, owner, number)
    if not (items.get("items") or []):
        items = _item_list(client, owner, number)
    count = len(items.get("items") or [])
    total = items.get("totalCount", count)
    if total > ITEM_LIMIT:
        raise UsageError(
            f"the Project holds {total} items, and one read takes "
            f"{ITEM_LIMIT}. The plan would add the cards it did not read a "
            f"second time. Add paging to ghsnapshot._read_items before you "
            f"sync this Project.")
    if count < total:
        raise UsageError(
            f"the Project holds {total} items, and the read got {count}. "
            f"The plan would add the cards it did not read a second time. "
            f"A GitHub rate limit can cause a short read: wait, then run the "
            f"command again.")
    return items


def _cards(items: dict) -> dict:
    """The Project card of each issue, keyed by the issue number. Tasks 9, 11,
    15, and 16 all read this value, so `fetch` must fill it. [inferred]"""
    out = {}
    for item in items.get("items") or []:
        number = (item.get("content") or {}).get("number")
        if number is None:
            continue
        out[number] = {
            "id": item.get("id", ""),
            "status": item.get("status"),
            # `item-list` gives no actor. The probe question `status-actor`
            # is what answers where to read it, so the pull falls back to the
            # gh login until then (D37). [inferred]
            "status_actor": None,
            "planned_start": item.get("Planned start"),
            "planned_end": item.get("Planned end"),
        }
    return out


def _milestone(item: dict) -> dict:
    return {"number": item["number"], "title": item.get("title", ""),
            "due_on": (item.get("due_on") or "")[:10] or None,
            "state": item.get("state", "open"),
            "okf": marker_target(item.get("description") or "")}


def _actor_login(actor: dict | None) -> str | None:
    """The login of a GraphQL actor, in the form of REST. For a GitHub App,
    GraphQL gives `__typename: Bot` and the slug with no `[bot]`, and REST
    gives `<slug>[bot]`. The pull reads the `[bot]` ending to tell an agent
    from a person, so the reader adds it here, in the one place that reads an
    actor."""
    actor = actor or {}
    login = actor.get("login")
    if login and actor.get("__typename") == "Bot" and not login.endswith("[bot]"):
        return f"{login}[bot]"
    return login


def _issue(node: dict, cards: dict | None = None) -> dict:
    closed = _nodes(node.get("timelineItems"))
    blockers = node.get("blockedBy") or {}
    if blockers.get("totalCount", 0) >= BLOCKERS_PAGE:
        raise UsageError(
            f"issue #{node['number']} has {blockers['totalCount']} blockers, "
            f"and one read takes {BLOCKERS_PAGE}. The plan would remove the "
            f"blockers it did not read. Add paging to ghsnapshot.fetch "
            f"before you sync this repository.")
    parent = node.get("parent") or {}
    return {
        "number": node["number"], "node_id": node["id"],
        "url": node.get("url", ""), "title": node.get("title", ""),
        "body": node.get("body") or "",
        "type": (node.get("issueType") or {}).get("name"),
        "parent": parent.get("number"),
        # removeSubIssue names the old parent by its node ID.
        "parent_id": parent.get("id"),
        "blocked_by": sorted(item["number"] for item in _nodes(blockers)),
        # removeBlockedBy names a blocker by its node ID. The key is a
        # string, so a snapshot file keeps the same map.
        "blocked_by_ids": {str(item["number"]): item["id"]
                           for item in _nodes(blockers)},
        "milestone": (node.get("milestone") or {}).get("number"),
        "labels": [item["name"] for item in _nodes(node.get("labels"))],
        "assignees": [item["login"] for item in _nodes(node.get("assignees"))],
        "state": node.get("state", "OPEN"),
        "state_reason": node.get("stateReason"),
        "okf": marker_target(node.get("body") or ""),
        "closed_by": _actor_login(closed[-1].get("actor")) if closed else None,
        "project_item": (cards or {}).get(node["number"]),
    }


def _field_list(client, owner: str, number) -> dict:
    """The Project field list. `fetch` and `fetch_fields` both read it, and
    `apply` compares the two, so the request must be the one request: a
    --limit raised here alone would make the second read see fields the
    first did not."""
    project = client.json(
        ["project", "field-list", str(number), "--owner", owner,
         "--format", "json", "--limit", "100"]) or {}
    return _fields(project)


def fetch_fields(client, snapshot: dict) -> dict:
    """Read the Project field list again. apply calls this after any change of
    the Status options, because an option ID may not survive it (D37)."""
    return _field_list(client, snapshot["project"]["owner"],
                       snapshot["project"]["number"])
