"""Publish a fixed Plan source to GitHub. The caller holds the workspace lock.

No Product files are read or written. GitHub is a view, never a work-state source.
"""
from __future__ import annotations

import copy
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from . import PlanError, model
from .proc import CommandError, capture

MAX_PAGES = 100
HOUR = 3600
WRITE_GAP = 1.0        # seconds between the starts of 2 writes
WRITES_PER_HOUR = 400  # writes in each 3,600 seconds; GitHub allows 500 content writes an hour
BATCH = 10             # writes between 2 checkpoints
PART_WRITES = 40       # default writes of 1 part
PART_SECONDS = 90      # the time budget of 1 part, from the start of apply (PLAN-STORY-674)
MAX_WAIT = 60          # the longest wait for a rate limit, in seconds
MARKER_MARGIN = 120    # seconds that a marker read looks before the pending mark, in GitHub time
DATE_BOUND = 86_400    # seconds: a `Date` further than this from the machine clock is not GitHub time (PLAN-STORY-650)
SETTLE = 30            # seconds from the start of an apply to the marker read of a prior create; GitHub ends a request after 10 seconds
RATE_KINDS = {"secondary-rate-limit", "rate-limit"}
SECONDARY = re.compile(r"secondary rate limit|abuse detection|submitted too quickly", re.IGNORECASE)
PRIMARY = re.compile(r"API rate limit (?:already )?exceeded", re.IGNORECASE)
GITHUB_TIMEOUT = re.compile(r"couldn't respond to your request in time", re.IGNORECASE)
NETWORK = re.compile(r"dial tcp|connection (?:reset|refused)|no such host|TLS handshake|i/o timeout|unexpected EOF", re.IGNORECASE)
HTTP_SUFFIX = re.compile(r"\(HTTP (\d{3})\)")
STATUS_LINE = re.compile(r"HTTP/\S+ (\d{3})")
# The IMF-fixdate form of a `Date` header (RFC 9110 section 5.6.7), for example `Tue, 17 Nov 2026 13:06:08 GMT`.
HTTP_DATE = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([0-9]{2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
                       r"([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) GMT", re.ASCII)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
NEXT_PAGE = re.compile(r'<https://api\.github\.com/([^>]+)>;\s*rel="next"')
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
CARDS = '''query PlanCards($board:String!, $number:Int!, $after:String) {
 repositoryOwner(login:$board) { ... on ProjectV2Owner { projectV2(number:$number) {
  items(first:100, after:$after) { totalCount pageInfo { hasNextPage endCursor } nodes {
   id
   content { ... on Issue { number repository { nameWithOwner } } }
   fieldValues(first:100) { totalCount nodes {
    ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
    ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
   } }
  } }
 } } }
}'''
ISSUES = '''query PlanIssues($owner:String!, $name:String!, $after:String, $firstPage:Boolean!) {
 repository(owner:$owner,name:$name) {
  labels(first:100) @include(if:$firstPage) { totalCount nodes { name } }
  issueTypes(first:20) @include(if:$firstPage) { totalCount nodes { id name } }
  issues(first:100,after:$after,states:[OPEN,CLOSED]) {
   totalCount pageInfo { hasNextPage endCursor } nodes {
    id number url title body state stateReason viewerCanUpdate viewerCanType author { login __typename }
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
        result = capture(["gh", *args], cwd=None, env=None, own_group=False,  # stays in the group of Plan: a stop of it stops gh
                         stdin=json.dumps(payload) if payload is not None else None)
    except CommandError as exc:
        if isinstance(exc.__cause__, OSError):
            raise PlanError("GitHub CLI could not start; no result was confirmed") from None
        raise PlanError("GitHub CLI did not end before the time limit; inspect the publication before retry") from None
    return Completed(result.returncode, result.stdout, result.stderr)


def _nodes(connection, name):
    if not isinstance(connection, dict) or not isinstance(connection.get("nodes"), list):
        raise PlanError(f"GitHub returned an invalid {name} list")
    nodes = connection["nodes"]
    if type(connection.get("totalCount")) is not int or connection["totalCount"] != len(nodes):
        raise PlanError(f"GitHub {name} list is incomplete; publication is blocked")
    return nodes


class GhFailure(PlanError):
    """A failed gh call. It holds only parsed values, never the text of gh or of GitHub."""
    def __init__(self, prefix, kind, status=None, retry_after=None, reset=None):
        self.kind, self.status, self.retry_after, self.reset = kind, status, retry_after, reset
        parts = [kind] + ([f"HTTP {status}"] if status else []) + ([f"retry-after {retry_after} s"] if retry_after is not None else [])
        super().__init__(f"{prefix} ({', '.join(parts)}); its outcome is not confirmed")

    def wait(self, now):
        """Seconds to wait before the call runs again."""
        if self.retry_after is not None:
            return self.retry_after
        if self.reset is not None:
            return max(self.reset - now + 30, 0)
        return 60

    def summary(self):
        return {"kind": self.kind, "status": self.status, "retry_after": self.retry_after}


def _created(item):
    try:
        return datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except (KeyError, TypeError, ValueError):
        return None


def _author(item):
    """The login of the account that made an issue (REST `user`, GraphQL `author`) or a milestone (REST `creator`), in the form of
    the configured writer. None when GitHub gives no account (a deleted account)."""
    actor = item.get("user") or item.get("creator") or item.get("author")
    if not isinstance(actor, dict) or not isinstance(actor.get("login"), str):
        return None
    login = actor["login"]
    if actor.get("__typename") == "Bot" and not login.endswith("[bot]"):
        login += "[bot]"  # GraphQL gives the login of an App with no [bot]; REST and the viewer give it with [bot]
    return login


def _by_writer(login, writer):
    """True when the login is the configured writer, with the exact compare that apply uses for the viewer."""
    return isinstance(login, str) and isinstance(writer, str) and login == writer


class RefusedCreate(Exception):
    """A create ends with a proven rate-limit refusal. It is not a PlanError, so the unknown-outcome path does not catch it."""
    def __init__(self, failure):
        super().__init__(failure.kind)
        self.failure = failure


class PartEnd(Exception):
    """The pace ends a call before a write. It is not a PlanError, so no handler of a failed call catches it."""
    def __init__(self, stopped, next_at):
        super().__init__(stopped)
        self.stopped, self.next_at = stopped, next_at


def _utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Pacer:
    """At least WRITE_GAP seconds between 2 writes, at most WRITES_PER_HOUR writes in 3,600 seconds."""
    def __init__(self, clock=None, sleep=None, monotonic=None):
        self.clock = clock or time.time
        self.sleep = sleep or time.sleep
        # Waits are measured with a clock that a change of the machine time cannot move (issue 2900). A caller that gives its own
        # `clock` and no `monotonic` (a test) gets that clock for both.
        self.monotonic = monotonic or (self.clock if clock else time.monotonic)
        self.history, self.limit, self.sent, self.on_batch = [], None, 0, None
        # The end of the part budget on the monotonic clock, or None (no `--part`). A write starts after it only when it is the
        # first write of the call, so each part makes progress.
        self.deadline = None

    def load(self, times):
        floor = self.clock() - HOUR
        self.history = sorted(x for x in times if type(x) in (int, float) and x > floor)

    def times(self):
        floor = self.clock() - HOUR
        return [x for x in self.history if x > floor]

    def before_write(self):
        if self.limit is not None and self.sent >= self.limit:
            raise PartEnd("part-limit", None)
        if self.deadline is not None and self.sent and self.monotonic() >= self.deadline:
            raise PartEnd("part-limit", None)
        self.history = self.times()
        if len(self.history) >= WRITES_PER_HOUR:
            raise PartEnd("hour-budget", _utc(self.history[0] + HOUR))
        if self.history:
            wait = self.history[-1] + WRITE_GAP - self.clock()
            if wait > 0:
                self.sleep(wait)
        self.history.append(self.clock())

    def after_write(self):
        self.sent += 1
        if self.sent % BATCH == 0 and self.on_batch:
            self.on_batch()


def _split(stdout):
    """Split the output of `gh api --include` into (status, headers, body)."""
    start = STATUS_LINE.match(stdout)
    if not start:
        return None, {}, stdout
    blank = re.search(r"\r?\n\r?\n", stdout)
    head, body = (stdout[:blank.start()], stdout[blank.end():]) if blank else (stdout, "")
    headers = {}
    for line in head.splitlines()[1:]:
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()
    return int(start.group(1)), headers, body


def _digits(value):
    """The number of a header value of 1 to 10 ASCII digits, else none. A header comes from GitHub, so it is not trusted."""
    return int(value) if isinstance(value, str) and re.fullmatch(r"[0-9]{1,10}", value) else None


def _github_time(value):
    """The epoch seconds of a `Date` header in the IMF-fixdate form, else none. A header comes from GitHub, so it is not trusted.

    The day and month names come from fixed tables, not from the locale, and the date must be a real calendar date.
    """
    found = HTTP_DATE.fullmatch(value) if isinstance(value, str) else None
    if not found:
        return None
    _day_name, day, month, year, hour, minute, second = found.groups()
    try:
        moment = datetime(int(year), MONTHS.index(month) + 1, int(day), int(hour), int(minute), int(second), tzinfo=timezone.utc)
    except ValueError:
        return None
    return int(moment.timestamp())


def _checked_time(value, now):
    """The epoch seconds of a `Date` header (`_github_time`) when they are within DATE_BOUND seconds of `now`, else none.

    `now` is the machine clock (the wall clock, not the monotonic clock). GitHub sends `Date` and `created_at` from 1 clock, so
    a `Date` far from the machine clock comes from a reply that is not from GitHub (a proxy, a wrong host), and it can hide an
    issue from the marker read (PLAN-STORY-650, issue 2852).
    """
    stamp = _github_time(value)
    return stamp if stamp is not None and abs(stamp - now) <= DATE_BOUND else None


def _classify(prefix, result):
    """Give the kind of a failed call from its head, its body and its stderr. Keep no text of them."""
    status, headers, body = _split(result.stdout)
    try:
        parsed = json.loads(body) if body.strip() else None
    except ValueError:
        parsed = None
    errors = [x for x in (parsed.get("errors") if isinstance(parsed, dict) else None) or [] if isinstance(x, dict)]
    messages = [str(x.get("message", "")) for x in errors]
    if isinstance(parsed, dict) and isinstance(parsed.get("message"), str):
        messages.append(parsed["message"])
    types = [str(x.get("type", "")) for x in errors]
    text = "\n".join([result.stderr or "", *messages])
    if status is None:
        suffix = HTTP_SUFFIX.search(result.stderr or "")
        status = int(suffix.group(1)) if suffix else None
    retry_after, reset = _digits(headers.get("retry-after")), _digits(headers.get("x-ratelimit-reset"))
    if headers.get("x-ratelimit-remaining") == "0" or "RATE_LIMITED" in types:
        kind = "rate-limit"
    elif (status in (403, 429) and "retry-after" in headers) or SECONDARY.search(text):
        kind = "secondary-rate-limit"
    elif PRIMARY.search(text):
        kind = "rate-limit"
    elif GITHUB_TIMEOUT.search(text):
        kind = "timeout"
    elif status and status >= 400:
        kind = "http"
    elif status == 200 and errors:
        kind = "graphql"
    elif status is None and NETWORK.search(result.stderr or ""):
        kind = "network"
    else:
        kind = "other"
    return GhFailure(prefix, kind, status, retry_after, reset)


class Gh:
    """Run the gh on PATH, including the Sofa App shim. Never print its errors."""
    def __init__(self, runner=None, pacer=None):
        self.runner = runner or _run
        self.pacer = pacer or Pacer()
        self.repository_ids = {}
        self.seen = None  # (GitHub epoch seconds, clock of the pacer) of the newest reply with a valid `Date`

    def _repository_id(self, repo):
        """The numeric ID of the repository, read 1 time for each repository."""
        if repo not in self.repository_ids:
            value = self._call(f"repos/{repo}")[1]
            if not isinstance(value, dict) or type(value.get("id")) is not int:
                raise PlanError("GitHub returned an invalid repository")
            self.repository_ids[repo] = value["id"]
        return self.repository_ids[repo]

    def _next_page(self, repo, endpoint, link):
        """The path of the next page. GitHub sends `repositories/<id>/<endpoint>?...`. The path must stay in the repository and in the same list, because the path goes to `gh api` and a path that starts with "-" reads as an option."""
        path = link.group(1)
        if path.startswith(f"repos/{repo}/{endpoint}?"):
            return path
        numbered = re.match(rf"repositories/([0-9]{{1,20}})/{endpoint}\?", path)
        if numbered and int(numbered.group(1)) == self._repository_id(repo):
            return path
        raise PlanError("GitHub returned an unexpected next page link")

    def _exchange(self, path, method, data, graphql):
        prefix = "GitHub GraphQL request failed" if graphql else "GitHub request failed"
        args = ["api", path, "--method", method, "--include"]
        if data is not None:
            args += ["--input", "-"]
        result = self.runner(args, data)
        status, headers, body = _split(result.stdout)
        now = self.pacer.clock()
        stamp = _checked_time(headers.get("date"), now) if status is not None else None
        if stamp is not None:  # a failed reply has a head too; a `Date` out of the bound keeps the older value, as a bad `Date` does
            self.seen = (stamp, now)
        if result.returncode:
            raise _classify(prefix, result)
        if status is None:
            raise GhFailure(prefix, "other")
        try:
            parsed = json.loads(body) if body.strip() else None
        except (ValueError, TypeError):
            raise PlanError("GitHub returned invalid JSON; its outcome is not confirmed") from None
        if graphql and (not isinstance(parsed, dict) or parsed.get("errors") or not isinstance(parsed.get("data"), dict)):
            raise _classify(prefix, result)
        return headers, parsed

    def _call(self, path, method="GET", data=None, retry=True, graphql=False):
        write = method != "GET" and not (graphql and not data["query"].lstrip().startswith("mutation"))

        def once():
            if write:
                self.pacer.before_write()
            reply = self._exchange(path, method, data, graphql)
            if write:
                self.pacer.after_write()
            return reply
        try:
            return once()
        except GhFailure as failure:
            if not retry or failure.kind not in RATE_KINDS:
                raise
            wait = failure.wait(self.pacer.clock())
            if wait > MAX_WAIT:
                raise
            self.pacer.sleep(wait)
            return once()

    def github_now(self):
        """The time of GitHub now, in epoch seconds: the newest valid `Date` plus the seconds that passed on this machine since that reply. None when no reply had one."""
        if self.seen is None:
            return None
        return self.seen[0] + self.pacer.clock() - self.seen[1]

    def request(self, path, method="GET", data=None, retry=True):
        return self._call(path, method, data, retry)[1]

    def graphql(self, query, retry=True, **variables):
        return self._call("graphql", "POST", {"query": query, "variables": variables}, retry, graphql=True)[1]["data"]

    def marker_issue(self, config, marker, since, milestone=False):
        """Find the 1 issue (or milestone) of the configured writer that holds the exact marker. Skip an item of another account. Read the newest issues back to the time of `since`, in GitHub time. With `since` None, read each page."""
        repo = config["repo"]
        path = (f"repos/{repo}/milestones?state=all&per_page=100" if milestone
                else f"repos/{repo}/issues?state=all&sort=created&direction=desc&per_page=100")
        if since is not None and since > self.pacer.clock() + DATE_BOUND:
            since = None  # a mark that an earlier apply saved from a far `Date` (plan 0.10.0 and earlier) is not GitHub time
        found = []
        for _ in range(MAX_PAGES):
            headers, items = self._call(path)
            if not isinstance(items, list):
                raise PlanError("GitHub returned an invalid issue list")
            for item in items:
                created = None if milestone else _created(item)
                if created is not None and since is not None and created < since - MARKER_MARGIN:
                    path = None
                    break
                if "pull_request" in item:
                    continue
                if marker in ((item.get("description" if milestone else "body")) or "") and _by_writer(_author(item), config["writer"]):
                    found.append(item)
            if path is None:
                break
            following = NEXT_PAGE.search(headers.get("link", ""))
            if not following:
                break
            path = self._next_page(repo, "milestones" if milestone else "issues", following)
        else:
            raise PlanError("GitHub issue list exceeds the supported page limit")
        if len({x.get("number") for x in found}) > 1:
            raise PlanError("issue binding and markers are ambiguous")
        return found[0] if found else None

    def _cards(self, config):
        """Read each card of the Project, 100 at a time, with the exact field names. Give {issue number: card}."""
        cards, seen, cursor, total = [], set(), None, None
        for _ in range(MAX_PAGES):
            data = self.graphql(CARDS, board=config["owner"], number=config["number"], after=cursor)
            connection = ((data.get("repositoryOwner") or {}).get("projectV2") or {}).get("items") or {}
            page = connection.get("nodes")
            if not isinstance(page, list) or type(connection.get("totalCount")) is not int:
                raise PlanError("GitHub returned an invalid Project items page")
            if total is not None and total != connection["totalCount"]:
                raise PlanError("GitHub Project items changed during pagination; read again")
            total = connection["totalCount"]
            cards.extend(page)
            info = connection.get("pageInfo") or {}
            if info.get("hasNextPage") is False:
                break
            cursor = info.get("endCursor")
            if not isinstance(cursor, str) or not cursor or cursor in seen:
                raise PlanError("GitHub Project pagination did not advance")
            seen.add(cursor)
        else:
            raise PlanError("GitHub Project pagination exceeds the supported page limit")
        if len(cards) != total:
            raise PlanError("GitHub Project items read is incomplete")
        by_issue = {}
        for card in cards:
            values = card.get("fieldValues") or {}
            if not isinstance(values.get("nodes"), list) or values.get("totalCount") != len(values["nodes"]):
                raise PlanError("GitHub Project item field values are incomplete")
            content = card.get("content") or {}
            number = content.get("number")
            if type(number) is not int or (content.get("repository") or {}).get("nameWithOwner") != config["repo"]:
                continue
            if number in by_issue:
                raise PlanError("GitHub Project has duplicate cards for one issue")
            value = {"id": card["id"], "Status": None}
            for node in values["nodes"]:
                field = (node.get("field") or {}).get("name")
                if field is None:
                    continue
                value[field] = node.get("name") if "name" in node else node.get("date")
            by_issue[number] = value
        return by_issue

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
        by_issue = self._cards(config)
        normalized = []
        for issue in issues:
            normalized.append({**issue, "labels": [x["name"] for x in _nodes(issue.get("labels"), "issue labels")],
                               "assignees": [x["login"] for x in _nodes(issue.get("assignees"), "issue assignees")],
                               "blocked_by": [x["id"] for x in _nodes(issue.get("blockedBy"), "issue blockers")],
                               "sub_issues": [x["id"] for x in _nodes(issue.get("subIssues"), "sub-issues")],
                               "parent": (issue.get("parent") or {}).get("id"),
                               "milestone": (issue.get("milestone") or {}).get("number"),
                               "card": by_issue.get(issue["number"]), "author": _author(issue)})
        milestones = []
        for page_number in range(1, MAX_PAGES + 1):
            page = self.request(f"repos/{config['repo']}/milestones?state=all&per_page=100&page={page_number}")
            if not isinstance(page, list):
                raise PlanError("GitHub returned an invalid milestones list")
            milestones.extend({**x, "author": _author(x)} if isinstance(x, dict) else x for x in page)
            if len(page) < 100:
                break
        else:
            raise PlanError("GitHub milestone pagination exceeds the supported page limit")
        return {"login": login, "repo_id": repository["id"], "project_id": project["id"], "fields": field_map,
                "labels": labels, "issue_types": types, "issues": normalized, "milestones": milestones}

    def create(self, config, snapshot, record, body):
        fields = record["fields"]
        if fields["type"] == "Milestone":
            return self.request(f"repos/{config['repo']}/milestones", "POST", {"title": _title(record), "description": body}, retry=False)
        result = self.graphql('''mutation PlanCreate($repositoryId:ID!,$title:String!,$body:String!){
          createIssue(input:{repositoryId:$repositoryId,title:$title,body:$body}){issue{id number url}}
        }''', retry=False, repositoryId=snapshot["repo_id"], title=_title(record), body=body)
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


def _find(workspace, record, snapshot, writer):
    milestone = record["fields"]["type"] == "Milestone"
    collection = snapshot["milestones"] if milestone else snapshot["issues"]
    marker = _marker(workspace, record)
    legacy = record.get("path")
    markers = [marker]
    if legacy:
        markers += [f"<!-- okf: {legacy} -->"]
    matches = []
    for issue in collection:
        if not _by_writer(issue.get("author"), writer):
            continue  # a marker counts only in an item that the writer made (PLAN-STORY-658)
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
        issue = _find(workspace, record, snapshot, config["writer"])
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


def _view(record, issue, wanted, found, snapshot, config):
    """The (key, board value, wanted value) rows of the check read of 1 item, in the order of the check of 0.6.2. The check read,
    the saved writes of a part and the check of the earlier part use this view (PLAN-STORY-676)."""
    if record["fields"]["type"] == "Milestone":
        return [(key, issue.get(key) or None, value or None) for key, value in wanted.items()]

    def target(name, attribute):
        return ((found[name] or {}).get(attribute) or "plan:" + name) if name else None
    payload, card = wanted["issue"], issue.get("card")
    rows = [(key, _comparable(key, issue.get(key)), _comparable(key, payload[key]))
            for key in ("title", "body", "state", "assignees", "labels")]
    if payload["state"] == "closed":
        rows.append(("state_reason", str(issue.get("stateReason", "")).lower(), payload["state_reason"]))
    rows += [("milestone", issue.get("milestone"), target(wanted["milestone"], "number")),
             ("parent", issue.get("parent"), target(wanted["parent"], "id")),
             ("blockers", sorted(set(issue.get("blocked_by") or [])), sorted({target(x, "id") for x in wanted["blockers"]}))]
    if config["type_mode"] == "issue_types":
        rows.append(("type", (issue.get("issueType") or {}).get("id"), snapshot["issue_types"][wanted["type"]]))
    rows.append(("Project", bool(card), True))
    return rows + [(key, (card or {}).get(key), value) for key, value in wanted["board"].items()]


def _failure(record, key):
    """The error text of the check read of 0.6.2 for 1 key of `_view`."""
    if record["fields"]["type"] == "Milestone":
        return "milestone verification failed; no publication success checkpoint"
    if key in ("title", "body", "state", "assignees", "labels"):
        return f"GitHub {key} verification failed; no publication success checkpoint"
    return {"state_reason": "close reason verification failed", "milestone": "milestone membership verification failed",
            "parent": "parent verification failed", "blockers": "blocker verification failed",
            "type": "native issue type verification failed"}.get(key, "Project field verification failed")


def _written(record, issue, wanted, found, snapshot, config):
    """The keys that the writes of 1 item change: the digest of the board value before the writes and of the written value."""
    return {key: {"before": model.digest(seen), "after": model.digest(want)}
            for key, seen, want in _view(record, issue, wanted, found, snapshot, config) if seen != want}


def _check_earlier(workspace, publication, active, selected, found, desired, snapshot, config, pacer):
    """The check of the earlier part (PLAN-STORY-676). A call that ended before its check read saved, in `unverified`, the keys
    that it wrote. Each saved key is checked once with the start read, and its entry is removed:
    - a new Plan value (the wanted value is not the written value), or the written value on the board: no error;
    - the board value from before the write: GitHub took the write and did not keep it. Save the checkpoint without the entry,
      then raise the error of the check read of 0.6.2. This call writes nothing. The next call writes the item again;
    - another value (a person's edit, or a value that GitHub changed): no error. This call writes the key again and saves it.
    """
    unverified = active.get("unverified") or {}
    for record in selected:
        identifier = record["id"]
        keys, issue = unverified.pop(identifier, None), found[identifier]
        if not keys or not issue:
            continue
        for key, seen, want in _view(record, issue, desired[identifier], found, snapshot, config):
            saved = keys.get(key)
            if saved and seen != want and model.digest(want) == saved["after"] and model.digest(seen) == saved["before"]:
                _checkpoint(workspace, publication, active, pacer.times())
                raise PlanError(f"{identifier}: {_failure(record, key)}")
    active.pop("unverified", None)


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


def _checkpoint(workspace, publication, active, pace=None):
    publication["active"] = copy.deepcopy(active)
    control = workspace.control()
    control["github_publication"] = copy.deepcopy(publication)
    if pace is not None:
        control["github_pace"] = list(pace)
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


def _binding(workspace, records, record, github, publication, active, pace=None, final=True):
    """Save 1 binding between 2 checkpoints. With final=False the second checkpoint is left to the next checkpoint of the call:
    the stored intent then names this binding, and the recovery of `_active_records` accepts its record before or after it."""
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
    _checkpoint(workspace, publication, active, pace)
    _save(workspace, records, record, github, event)
    active["revisions"] = {r["id"]: r.get("revision", 0) for r in records}
    active.pop("binding_intent")
    if final:
        _checkpoint(workspace, publication, active, pace)


def _identity(issue):
    number = issue.get("number")
    node = issue.get("node_id") or issue.get("id")
    if type(number) is not int or number <= 0 or not isinstance(node, str) or not node:
        raise PlanError("GitHub did not return a checked issue identity; inspect before retry")
    return {"number": number, "node_id": node, "url": issue.get("url") or issue.get("html_url")}


def _create(client, workspace, config, snapshot, record, body, active):
    """Create 1 issue or milestone. After a rate-limit refusal, wait, look for the marker, then create 1 more time."""
    pacer = client.pacer
    try:
        return client.create(config, snapshot, record, body)
    except GhFailure as failure:
        if failure.kind not in RATE_KINDS:
            raise
        first = failure
    wait = first.wait(pacer.clock())
    if wait > MAX_WAIT:
        raise RefusedCreate(first)
    pacer.sleep(wait)
    try:
        found = client.marker_issue(config, _marker(workspace, record), active["pending_at"][record["id"]],
                                    record["fields"]["type"] == "Milestone")
        return found if found else client.create(config, snapshot, record, body)
    except PartEnd:
        raise RefusedCreate(first) from None  # the first create was sent, so its outcome stays unknown
    except GhFailure as failure:
        if failure.kind in RATE_KINDS:
            raise RefusedCreate(failure) from None
        raise


def _prior_create(client, workspace, config, record, active, started):
    """Settle a create that an earlier call sent and did not confirm. Wait until SETTLE seconds of this call passed, then read the
    marker. Give the 1 issue (or milestone) of the writer that holds it, or None. Each other result ends the call and keeps the create pending."""
    pacer = client.pacer
    wait = started + SETTLE - pacer.monotonic()
    if wait > 0:
        pacer.sleep(wait)
    try:
        return client.marker_issue(config, _marker(workspace, record), active["pending_at"].get(record["id"]),
                                   record["fields"]["type"] == "Milestone")
    except GhFailure:
        raise  # a rate limit ends the call with `rate-limit`; another failure names its kind
    except PlanError as failure:
        raise PlanError(f"{record['id']}: a prior create has an unknown outcome; inspect GitHub before recovery ({failure})") from None


def _board(client, snapshot, card, wanted, new):
    """Write the board values of 1 card. A new card gets each value that is not null; an old card gets each difference."""
    for name, value in wanted["board"].items():
        if (value is None) if new else (card.get(name) == value):
            continue
        field = snapshot["fields"][name]
        typed = ({"singleSelectOptionId": field["options"][value]} if name == "Status" else {"date": value}) if value is not None else None
        client.field(snapshot["project_id"], card["id"], field["id"], typed)


def apply(workspace, fingerprint, writer, client=None, part=False, max_writes=None):
    """Publish one preview. The caller holds the workspace lock until the checkpoints are saved."""
    client = client or Gh()
    pacer = client.pacer
    started = pacer.monotonic()
    records, config, snapshot, selected, found, desired, publication, active = _read(workspace, client)
    read_time = pacer.monotonic() - started  # the check read starts only when a read of this length ends inside the budget
    records = list(records)  # Binding commits replace records; keep the read index immutable.
    if writer != config["writer"] or snapshot["login"] != config["writer"]:
        raise PlanError("only the configured writer authenticated as the actual GitHub viewer can publish")
    pacer.load(workspace.control().get("github_pace") or [])
    pacer.sent, pacer.limit = 0, ((max_writes or PART_WRITES) if part else None)
    pacer.deadline = started + PART_SECONDS if part else None
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
            _binding(workspace, records, current, intent["github"], publication, active, pacer.times())
        elif active != publication["active"]:
            _checkpoint(workspace, publication, active, pacer.times())
    else:
        expected = model.digest({"source": source, "revisions": revisions, "live": snapshot, "desired": desired})
        last = publication.get("last") or {}
        # A record of a part that ended with complete: false is no proof; a record of 0.6.2 with no `complete` key is complete.
        replay = (last.get("complete", True) is True and last.get("fingerprint") == fingerprint and last.get("source") == source
                  and last.get("revisions") == revisions)
        if fingerprint != expected and not replay:
            raise PlanError("publication fingerprint changed; preview again before writing")
        if replay and any(_changes(r, found[r["id"]], desired[r["id"]], found, snapshot, config) for r in selected):
            raise PlanError("GitHub changed after publication; preview again before writing")
        active = {"fingerprint": fingerprint, "source": source, "revisions": revisions, "pending_creates": [],
                  "source_revision": last["source_revision"] if replay else model.digest(revisions)}
        _checkpoint(workspace, publication, active, pacer.times())
    active.setdefault("refused_creates", [])
    active.setdefault("pending_at", {})
    _check_earlier(workspace, publication, active, selected, found, desired, snapshot, config, pacer)
    before = active.get("progress") or {}
    changed = {r["id"] for r in selected if not found[r["id"]] or _changes(r, found[r["id"]], desired[r["id"]], found, snapshot, config)}
    finished, deferred, made = set(), [], False
    due, bound = None, 0  # the bindings that the check found due (None before it), and the bindings of this call

    def progress():
        return {"writes": before.get("writes", 0) + pacer.sent, "bindings": before.get("bindings", 0) + bound,
                "calls": before.get("calls", 0) + 1, "at": model.timestamp()}

    def save(ended=False):
        active["progress"] = progress()
        if ended:
            # A call that ends normally with complete: false records it (D-9221). Only a complete record can replay.
            publication["last"] = {"complete": False, "fingerprint": fingerprint, "source_revision": active["source_revision"],
                                   "progress": active["progress"], "at": active["progress"]["at"]}
        _checkpoint(workspace, publication, active, pacer.times())

    def save_stored():
        # After an error the stored checkpoint is the proof; change only its progress and the pace.
        control = workspace.control()
        stored = (control.get("github_publication") or {}).get("active")
        if stored is not None:
            stored["progress"] = progress()
        control["github_pace"] = pacer.times()
        workspace.save_control(control)

    def left(stopped, next_at, failure=None):
        bindings_left = None if due is None else len(due) - bound
        result = {"published": False, "complete": False, "fingerprint": fingerprint, "source_revision": active["source_revision"],
                  "writes": pacer.sent, "items_left": len(changed - finished) + (bindings_left or 0), "bindings_left": bindings_left,
                  "stopped": stopped, "next_at": next_at}
        if failure:
            result["github_error"] = failure.summary()
        return result

    pacer.on_batch = save
    error, succeeded = None, False
    try:
        for record in selected:
            identifier = record["id"]
            issue = found[identifier]
            if not issue and identifier in active["pending_creates"]:
                # An earlier call sent this create and got no reply: settle it with the marker read.
                issue = _prior_create(client, workspace, config, record, active, started)
                if issue:
                    made = True
                    found[identifier] = issue
            if not issue:
                if identifier in active["refused_creates"]:
                    active["refused_creates"].remove(identifier)
                if identifier not in active["pending_creates"]:
                    active["pending_creates"].append(identifier)
                active["pending_at"][identifier] = client.github_now()  # GitHub time, or None when no reply of this call had a valid Date
                _checkpoint(workspace, publication, active, pacer.times())
                try:
                    created = _create(client, workspace, config, snapshot, record,
                                      desired[identifier].get("description") or desired[identifier]["issue"]["body"], active)
                except (PartEnd, RefusedCreate) as stop:
                    active["pending_creates"].remove(identifier)
                    active["pending_at"].pop(identifier, None)
                    if isinstance(stop, RefusedCreate):
                        active["refused_creates"].append(identifier)
                        raise stop.failure from None
                    raise
                except PlanError:
                    # A failed reply is not proof that GitHub did not create the issue.
                    refreshed = client.snapshot(config)
                    issue = _find(workspace, record, refreshed, config["writer"])
                    if issue is None:
                        raise PlanError(f"{identifier}: create outcome is unknown; no duplicate create will be retried") from None
                else:
                    # Persist a confirmed identity before any further GitHub operation.
                    current = model.resolve(records, identifier)
                    binding = {**(current["fields"].get("github") or {}), **_identity(created)}
                    _binding(workspace, records, current, binding, publication, active, pacer.times())
                    issue = created
                made = True
                found[identifier] = issue
            current = model.resolve(records, identifier)
            binding = {**(current["fields"].get("github") or {}), **_identity(issue)}
            if binding != current["fields"].get("github"):
                _binding(workspace, records, current, binding, publication, active, pacer.times())
            leaving = [name for name in ("pending_creates", "refused_creates") if identifier in active[name]]
            if leaving:
                for name in leaving:
                    active[name].remove(identifier)
                active["pending_at"].pop(identifier, None)
                _checkpoint(workspace, publication, active, pacer.times())
        # All identities are durable before any relationship or Project write.
        if made:
            snapshot = client.snapshot(config)
        selected, found = _selection(workspace, records, snapshot, config)
        if any(found[r["id"]] is None for r in selected):
            raise PlanError("a created identity cannot be read back; inspect before retry")
        desired = _desired(workspace, records, selected, found, snapshot, config)
        # The values before the writes. An item is saved in `unverified` only when all its writes were sent (PLAN-STORY-676).
        written = {r["id"]: _written(r, found[r["id"]], desired[r["id"]], found, snapshot, config) for r in selected}

        def sent(identifier):
            finished.add(identifier)
            if written[identifier]:
                active.setdefault("unverified", {})[identifier] = written[identifier]
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
                sent(identifier)
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
            card, new = issue.get("card"), False
            if not card:
                try:
                    card, new = {"id": client.card(snapshot["project_id"], issue["id"])}, True
                except PlanError as failure:
                    if isinstance(failure, GhFailure) and failure.kind in RATE_KINDS:
                        raise
                    deferred.append(identifier)  # A board workflow can add it before this mutation.
                    continue
            _board(client, snapshot, card, wanted, new)
            sent(identifier)
        if deferred:
            fresh = client.snapshot(config)
            for record in selected:
                if record["id"] in deferred:
                    card = (_find(workspace, record, fresh, config["writer"]) or {}).get("card")
                    if not card:
                        raise PlanError(f"{record['id']}: Project membership could not be confirmed")
                    _board(client, snapshot, card, desired[record["id"]], True)
                    sent(record["id"])
        # A checkpoint is a success only after the affected values are read back. A call that wrote nothing to GitHub uses its
        # start read: no write of the call changed the board since then.
        wrote = bool(pacer.sent or deferred)
        if pacer.sent and pacer.deadline is not None and pacer.monotonic() + read_time > pacer.deadline:
            raise PartEnd("part-limit", None)  # the next part reads the board at its start and uses that read
        if active.pop("unverified", None) is not None:
            _checkpoint(workspace, publication, active, pacer.times())  # the check read below checks these writes
        verified = client.snapshot(config) if wrote else snapshot
        due = []
        for record in selected:
            identifier, wanted = record["id"], desired[record["id"]]
            issue = _find(workspace, record, verified, config["writer"])
            if not issue:
                raise PlanError(f"{identifier}: issue is missing at verification")
            for key, seen, want in _view(record, issue, wanted, found, verified, config):
                if seen != want:
                    raise PlanError(f"{identifier}: {_failure(record, key)}")
            if record["fields"]["type"] == "Milestone":
                continue
            current = model.resolve(records, identifier)
            binding = {**(current["fields"].get("github") or {}), "project_item_id": issue["card"]["id"],
                       "plan_labels": wanted["managed_labels"], "plan_dates": [x for x in wanted["board"] if x != "Status"],
                       "pushed_hash": model.digest(wanted)}
            if binding != current["fields"].get("github"):
                due.append((identifier, binding))
        longest = 0.0
        for identifier, binding in due:
            # In a part, a binding starts only when the longest binding of this call still ends inside the budget. The first unit
            # of progress of a call (its first GitHub write or its first binding) always starts, so each part makes progress.
            begun = pacer.monotonic()
            if pacer.deadline is not None and (pacer.sent or bound) and begun + longest > pacer.deadline:
                raise PartEnd("part-limit", None)
            _binding(workspace, records, model.resolve(records, identifier), binding, publication, active, pacer.times(), final=False)
            longest = max(longest, pacer.monotonic() - begun)
            bound += 1
        publication["last"] = {"complete": True, "fingerprint": fingerprint, "source": source,
                               "source_revision": active["source_revision"],
                               "revisions": {r["id"]: r.get("revision", 0) for r in records},
                               "at": model.timestamp(), "items": len(selected)}
        _checkpoint(workspace, publication, None, pacer.times())
        succeeded = True
        return {"published": True, "complete": True, "fingerprint": fingerprint, "source_revision": active["source_revision"],
                "items": len(selected), "writes": pacer.sent}
    except PartEnd as end:
        return left(end.stopped, end.next_at)
    except GhFailure as failure:
        if failure.kind in RATE_KINDS:
            return left("rate-limit", _utc(pacer.clock() + failure.wait(pacer.clock())), failure)
        error = failure
        raise
    except BaseException as exc:
        error = exc
        raise
    finally:
        if not succeeded:
            try:
                save(ended=True) if error is None else save_stored()
            except Exception:
                if error is None:
                    raise
