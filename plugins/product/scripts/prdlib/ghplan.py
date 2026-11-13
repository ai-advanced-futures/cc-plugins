"""`github plan`: the pages plus one snapshot give one change set.

The function is pure: it reads the tree and the snapshot and writes nothing.
`github apply` executes the change set, and `/product:roadmap-sync` shows it to a
person first. A change names a page, never a GitHub number that the run has
not created yet, so the set stays readable when nothing is pushed.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import UsageError, ghmodel, ghsnapshot
from .graph import find_cycle
from .regen import collect, read_tree, require_readable
from .registry import TYPES, WORK_ITEMS
from .textsafe import escape_controls

# The documented GitHub limits. The probe has not run (D37), so `plan` refuses
# a change set that goes over them instead of letting the API refuse it.
MAX_SUB_ISSUES = 100
MAX_LEVELS = 8

STATUS_FIELD = "Status"
DATE_FIELDS = ("Planned start", "Planned end")

CLOSE_REASON = {"done": "COMPLETED", "released": "COMPLETED",
                "cancelled": "NOT_PLANNED"}
OPTION_STATE = ghmodel.OPTION_STATE


@dataclass(frozen=True)
class Change:
    action: str
    page: str | None
    detail: dict
    reason: str


@dataclass
class Plan:
    changes: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    refusals: list = field(default_factory=list)
    # The walk of the bundle this plan was built from. `apply` takes the
    # criteria and the page paths from it, so it neither reads the tree a
    # second time nor works from pages that changed after the plan was made.
    tree: dict = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        """A refusal stops the whole apply. A conflict does not: apply writes
        nothing for that one field and reports it."""
        return bool(self.refusals)


def work_items(root: Path, tree: dict | None = None) -> dict:
    """page ID -> (frontmatter, body), for each Epic, Feature, Story, Task,
    in level order and then by ID. A parent is planned before its child.

    `tree` is the read_tree() map, when the caller already holds one."""
    pages = {}
    for path, (bundle, frontmatter, body) in _tree(root, tree).items():
        if bundle == "roadmap" and frontmatter.get("type") in WORK_ITEMS:
            pages[path.stem] = (frontmatter, body)
    return dict(sorted(pages.items(), key=lambda item: (
        TYPES[item[1][0]["type"]].level, item[0])))


def numbers_of(pages: dict) -> dict:
    """issue number -> page ID, from the `github` field of each work item.
    `ghsnapshot.issues_by_page` takes it to find an adopted issue."""
    return {field["number"]: page_id
            for page_id, (frontmatter, _body) in pages.items()
            for field in [frontmatter.get("github") or {}]
            if field.get("number")}


def criteria_of(root: Path, tree: dict | None = None) -> dict:
    """page ID of a work item -> [(criterion ID, title)], sorted."""
    found = {}
    for path, (_bundle, frontmatter, _body) in _tree(root, tree).items():
        if frontmatter.get("type") != "AcceptanceCriterion":
            continue
        item = ghmodel.page_id_of(frontmatter.get("item", ""))
        found.setdefault(item, []).append(
            (path.stem, frontmatter.get("title", path.stem)))
    return {key: sorted(value) for key, value in found.items()}


def milestone_pages(root: Path, tree: dict | None = None) -> dict:
    return {path.stem: frontmatter
            for path, (bundle, frontmatter, _body) in _tree(root, tree).items()
            if bundle == "roadmap" and frontmatter.get("type") == "Milestone"}


def _tree(root: Path, tree: dict | None) -> dict:
    return collect(root) if tree is None else tree


TYPE_MODES = ("labels", "issue_types")
PROJECT_PAGE_PATH = "docs/product/roadmap/projects/PROJECT-01.md"


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def type_mode(tree: dict, snapshot: dict) -> str:
    """The type form of the board: the `type_mode` of the Project page, or
    `labels` for a repository that a user owns. No right of a token changes
    it (STORY-351): an issue type belongs to an organization, and the
    same bundle must give the same plan to each token and each machine."""
    field = next(((frontmatter.get("github") or {})
                  for _path, (bundle, frontmatter, _body) in tree.items()
                  if bundle == "roadmap"
                  and frontmatter.get("type") == "Project"), {})
    value = field.get("type_mode")
    repo = snapshot.get("repo") or {}
    is_org = bool(repo.get("owner_is_org"))
    if value is None and not is_org:
        return "labels"
    if value == "issue_types" and not is_org:
        owner = escape_controls(str(repo.get("full", "")).split("/")[0])
        raise UsageError(
            f"issue types belong to an organization, and `{owner}` is a user. "
            f"Set `type_mode: labels` in {PROJECT_PAGE_PATH}.")
    if value in TYPE_MODES:
        return value
    issues = snapshot.get("issues") or []
    labelled = sum(1 for issue in issues if any(
        name.startswith(ghmodel.LABEL_PREFIX)
        for name in issue.get("labels") or []))
    typed = sum(1 for issue in issues if issue.get("type"))
    raise UsageError(
        f"{PROJECT_PAGE_PATH} has no valid `type_mode` in its `github` "
        f"field. Set it to `labels` or `issue_types`. The board has "
        f"{_count(labelled, 'issue')} with a `{ghmodel.LABEL_PREFIX}` label "
        f"and {_count(typed, 'issue')} with an issue type: record the form "
        f"that the board holds.")


def uses_issue_types(mode: str) -> bool:
    """True when the sync writes an organization issue type, not a label."""
    return mode == "issue_types"


def type_label(frontmatter: dict, mode: str) -> str:
    """The issue type name, or the `type:` label of the `labels` mode."""
    name = frontmatter.get("type", "")
    if uses_issue_types(mode):
        return name
    return f"{ghmodel.LABEL_PREFIX}{name.lower()}"


def stored_payload(page_id: str, frontmatter: dict, body: str,
                   mode: str, refs: dict, criteria: dict) -> dict:
    """The nine push values a page holds now. `plan`, `apply`, and `pull` all
    compare against this one shape, so they build it the one way."""
    return ghmodel.push_payload(page_id, frontmatter, body,
                                type_label(frontmatter, mode), refs,
                                criteria.get(page_id, []))


def build(root: Path, snapshot: dict, keep=()) -> Plan:
    """`keep` names pages whose bundle values the user keeps over an edit
    that a person made in GitHub. Such a page did not change, so its hash
    still matches `pushed_hash`, and without `keep` the plan holds no update
    for it: the edit stays, and every pull reports it again."""
    # One walk of the tree for the whole build. The four readers below want
    # the same pages, and a walk for each would read every file four times.
    tree, broken = read_tree(root)
    require_readable(root, broken)
    mode = type_mode(tree, snapshot)
    plan = Plan(tree=tree)
    pages = work_items(root, tree)
    criteria = criteria_of(root, tree)
    stored = numbers_of(pages)
    pushed = ghsnapshot.issues_by_page(snapshot, stored)
    refs = ghsnapshot.refs(snapshot, stored)
    unknown = sorted(set(keep) - set(pushed))
    if unknown:
        raise UsageError(
            f"--keep names {escape_controls(', '.join(unknown))}, which has "
            f"no issue in "
            f"GitHub, so there is no GitHub value to replace. Give the ID of "
            f"a page that a `DIFFERENT:` or `BOUND:` line of `github pull` "
            f"names.")
    used_labels = set()
    issue_changes = []
    card_changes = []
    state_changes = []
    for page_id, (frontmatter, body) in pages.items():
        label = type_label(frontmatter, mode)
        if page_id in pushed:
            change = _update_change(page_id, frontmatter, body,
                                    pushed[page_id], label,
                                    criteria.get(page_id, []), refs,
                                    force=page_id in keep)
            if change:
                used_labels.update(change.detail["labels"])
                issue_changes.append(change)
            _state_changes(page_id, frontmatter, pushed[page_id],
                           state_changes, plan.conflicts, card_changes)
            continue
        detail = {
            "title": ghmodel.issue_title(page_id, frontmatter),
            "body": ghmodel.issue_body(page_id, frontmatter, body,
                                       criteria.get(page_id, [])),
            "type": label,
            "labels": ghmodel.labels_of(frontmatter, label),
            **_relations(frontmatter),
            **_dates(frontmatter),
            **_card(frontmatter),
        }
        used_labels.update(detail["labels"])
        issue_changes.append(Change(action="create_issue", page=page_id,
                                    detail=detail,
                                    reason="the page has no github field"))
    # The order is the run order of `apply`: a label and an issue type exist
    # before the issue that carries them, a Project field before any value it
    # holds, and a milestone before the issue that names it.
    type_changes = _type_changes(mode, snapshot, used_labels)
    plan.changes.extend(type_changes)
    plan.changes.extend(_field_changes(snapshot))
    plan.changes.extend(_milestone_changes(root, snapshot, tree))
    # A card before the update of its issue: the update sets the two date
    # fields, and a date needs the card.
    plan.changes.extend(card_changes)
    plan.changes.extend(issue_changes)
    plan.changes.extend(state_changes)
    plan.refusals.extend(_limit_refusals(pages))
    plan.refusals.extend(_graph_refusals(pages))
    if uses_issue_types(mode):
        _refuse_missing_type_rights(snapshot, type_changes, issue_changes,
                                    pushed)
    return plan


def _refuse_missing_type_rights(snapshot, type_changes, issue_changes, pushed):
    """The `issue_types` mode needs 2 rights that a token may lack: to make
    an issue type (an owner of the organization), and to set the type of an
    issue (push access). GitHub drops the second with no error, so the plan
    stops here and names the issue. A recorded snapshot with no `rights` key,
    or an issue with no `can_type`, gives no check. [inferred]"""
    made = [change.detail["name"] for change in type_changes
            if change.action == "create_issue_type"]
    if made and (snapshot.get("rights") or {}).get("org_admin") is False:
        raise UsageError(
            f"the organization has no issue type "
            f"`{escape_controls(', '.join(made))}`. Making one needs an "
            f"owner of the organization (a classic token also needs "
            f"`admin:org`).")
    blocked = sorted(
        change.detail["number"] for change in issue_changes
        if change.action == "update_issue"
        and pushed[change.page].get("can_type") is False
        and change.detail["type"] != ghmodel.live_type(
            pushed[change.page], change.detail["type"]))
    if blocked:
        names = ", ".join(f"#{escape_controls(number)}" for number in blocked)
        repo = escape_controls(snapshot.get("repo", {}).get("full", ""))
        raise UsageError(
            f"the token cannot set the issue type of {names}. It needs push "
            f"access to `{repo}`.")


def _page_of(target):
    return ghmodel.page_id_of(target) if target else None


def _relations(frontmatter: dict) -> dict:
    """The three relationship keys, which `apply` turns into GitHub links."""
    return {
        "parent_page": _page_of(frontmatter.get("parent")),
        "blocked_by_pages": [_page_of(target) for target
                             in frontmatter.get("blocked_by") or []],
        "milestone_page": _page_of(frontmatter.get("milestone")),
    }


def _dates(frontmatter: dict) -> dict:
    """The two planned dates, which `apply` sets on the Project card."""
    return {"planned_start": frontmatter.get("planned_start_date"),
            "planned_end": frontmatter.get("planned_end_date")}


def _card(frontmatter: dict) -> dict:
    """The two-direction values that a new issue gets: the Status of its
    card and its assignee. `apply` stores them in `synced` after it sent
    them."""
    state = frontmatter.get("state", "backlog")
    owner = frontmatter.get("owner") or ""
    return {"state": state, "option": ghmodel.STATUS_OPTIONS[state],
            "assignee": (owner.split(":", 1)[1]
                         if owner.startswith("human:") else None)}


def is_bound(pushed_hash, issue) -> bool:
    """A bound page has a number, no `pushed_hash`, and an issue with no OKF
    marker: the issue holds text that a person wrote. An issue with the
    marker was made by the sync, and the next plan pushes it again."""
    return not pushed_hash and not issue.get("okf")


def _update_change(page_id, frontmatter, body, issue, label, criteria, refs,
                   force=False):
    """The update of one pushed page, or None when nothing changed. `force`
    is the `--keep` of the page: the update goes even with an unchanged hash.

    Unresolved means a relationship names an issue that this same run creates.
    [inferred P3-7]
    The hash is then not computable, so the safe answer is to push again: a
    wrong `unchanged` leaves GitHub behind the bundle with no report.
    """
    try:
        payload = ghmodel.push_payload(page_id, frontmatter, body, label,
                                       refs, criteria)
        new_hash = ghmodel.push_hash(payload)
        reason = "the pushed values changed"
    except ghmodel.Unresolved as unresolved:
        payload, new_hash = None, None
        reason = f"{unresolved} has no issue yet"
    stored = (frontmatter.get("github") or {}).get("pushed_hash")
    # Only `--keep` sends the bundle text over a bound page: an edit of the
    # page is not a choice. [inferred]
    if is_bound(stored, issue):
        if not force:
            return None
        reason = ("the user sends the bundle text over the text that a "
                  "person wrote")
    elif new_hash and stored == new_hash:
        if not force:
            return None
        reason = ("the user keeps the bundle values over the edit in "
                  "GitHub")
    labels = ghmodel.labels_of(frontmatter, label)
    # `gh issue edit` adds a label and never drops one. A tag that the page
    # lost, or a `drifted` that a person accepted, would leave its label on
    # the issue and every later `pull` would report it as a person's edit.
    remove = sorted(set(issue.get("labels") or []) - set(labels))
    detail = {"number": issue["number"], "node_id": issue["node_id"],
              "payload": payload, "pushed_hash": new_hash, "type": label,
              **_relations(frontmatter), **_dates(frontmatter),
              "labels": labels, "remove_labels": remove}
    return Change(action="update_issue", page=page_id, detail=detail,
                  reason=reason)


def _type_changes(mode: str, snapshot: dict, used_labels: set) -> list:
    """An issue type is made on the organization, by an owner of it. The
    `labels` mode gets the labels type:epic, type:feature, type:story, and
    type:task instead."""
    out = []
    used = set(used_labels)
    live_labels = set(snapshot.get("labels") or [])
    if uses_issue_types(mode):
        live_types = set(snapshot.get("issue_types") or {})
        for name in WORK_ITEMS:
            if name not in live_types:
                out.append(Change(
                    "create_issue_type", None, {"name": name},
                    "the organization has no issue type of this name. "
                    "Making one adds it to every repository of the "
                    "organization, not to this one."))
    else:
        for name in WORK_ITEMS:
            used.add(f"type:{name.lower()}")
    for name in sorted(used - live_labels):
        out.append(Change("create_label", None, {"name": name},
                          "the repository has no label of this name"))
    return out


def _field_changes(snapshot: dict) -> list:
    """The Status field with one option for each state, and the two date fields.

    An option that this run makes changes the option set, and the probe has
    not answered whether the option IDs of the items survive that change
    (D37). The safe path is a reread_fields step: apply reads the field list
    again before it sets any Status value, and never keeps an option ID
    across a change of the options.
    """
    fields = snapshot.get("project", {}).get("fields") or {}
    out = []
    status = fields.get(STATUS_FIELD)
    if status is None:
        out.append(Change("create_field", None,
                          {"name": STATUS_FIELD, "data_type": "SINGLE_SELECT",
                           "options": list(ghmodel.STATUS_OPTIONS.values())},
                          "the Project has no Status field"))
    else:
        missing = [name for name in ghmodel.STATUS_OPTIONS.values()
                   if name not in (status.get("options") or {})]
        if missing:
            # `updateProjectV2Field` replaces the whole option list, so one
            # call installs every missing option. The change carries one
            # option for each state, because a call that sent only the
            # missing one would delete the others. [inferred]
            out.append(Change(
                "create_option", None,
                {"field": STATUS_FIELD, "names": missing,
                 "options": list(ghmodel.STATUS_OPTIONS.values())},
                f"the Status field has no option named "
                f"{', '.join(missing)}"))
    for name in DATE_FIELDS:
        if name not in fields:
            out.append(Change("create_field", None,
                              {"name": name, "data_type": "DATE"},
                              "the Project has no field of this name"))
    if out:
        # A new field has an ID that the snapshot does not hold, and a new
        # option set may not keep its option IDs.
        out.append(Change("reread_fields", None, {},
                          "a field or an option set changed, so the field "
                          "IDs are read again before any value is set"))
    return sorted(out, key=lambda change: (
        change.action != "create_field", change.action == "reread_fields",
        change.detail.get("name", "")))


def _milestone_changes(root: Path, snapshot: dict,
                       tree: dict | None = None) -> list:
    """A milestone matches by its OKF marker, not by its title: a person can
    rename a milestone in GitHub and the link must survive it."""
    live = {ghmodel.page_id_of(item["okf"]): item
            for item in snapshot.get("milestones") or []
            if item.get("okf")}
    out = []
    for page_id, frontmatter in sorted(milestone_pages(root, tree).items()):
        title = ghmodel.issue_title(page_id, frontmatter)
        due = frontmatter.get("target_date")
        description = (f"{frontmatter.get('description', '')}\n\n"
                       f"{ghmodel.marker(ghmodel.page_target(page_id, 'Milestone'))}")
        found = live.get(page_id)
        detail = {"title": title, "due_on": due, "description": description}
        if found is None:
            out.append(Change("create_milestone", page_id, detail,
                              "the milestone is not in GitHub"))
        elif found.get("due_on") != due or found.get("title") != title:
            out.append(Change("update_milestone", page_id,
                              dict(detail, number=found["number"]),
                              "the title or the date changed"))
    return out


def _limit_refusals(pages: dict) -> list:
    counts = {}
    for _page_id, (frontmatter, _body) in pages.items():
        parent = _page_of(frontmatter.get("parent"))
        if parent:
            counts[parent] = counts.get(parent, 0) + 1
    return [f"{escape_controls(parent)} has {count} children. GitHub holds "
            f"{MAX_SUB_ISSUES} sub-issues for each parent. Move the extra "
            f"children under another parent."
            for parent, count in sorted(counts.items())
            if count > MAX_SUB_ISSUES]


def _graph_refusals(pages: dict) -> list:
    """A cycle and a chain that is too deep. `plan` does not run `check`, and
    the probe has not said what GitHub does with either (D37), so the plan
    refuses them itself."""
    out = []
    for name, rule in (("parent", "E5"), ("blocked_by", "E6")):
        edges = {page_id: [_page_of(target) for target
                           in _targets(frontmatter.get(name))]
                 for page_id, (frontmatter, _body) in pages.items()}
        cycle = find_cycle(edges)
        if cycle:
            out.append(f"`{name}` makes a cycle: "
                       f"{escape_controls(' -> '.join(cycle))} "
                       f"(rule {rule}). Remove one link of it.")
    parents = {page_id: _page_of(frontmatter.get("parent"))
               for page_id, (frontmatter, _body) in pages.items()}
    deep = []
    for page_id in pages:
        depth, node, seen = 1, page_id, {page_id}
        while parents.get(node) and parents[node] not in seen:
            node = parents[node]
            seen.add(node)
            depth += 1
        if depth > MAX_LEVELS:
            deep.append(page_id)
    if deep:
        out.append(f"{escape_controls(', '.join(sorted(deep)))} sit too "
                   f"deep: GitHub holds "
                   f"{MAX_LEVELS} levels of sub-issues. Move them under a "
                   f"parent of a higher level.")
    return out


def _targets(value) -> list:
    """One link target or a list of them, as a list."""
    if not value:
        return []
    return [value] if isinstance(value, str) else list(value)


def _state_changes(page_id, frontmatter, issue, changes, conflicts,
                   cards=None):
    """The two-direction changes of one pushed page. `cards` takes an
    add_to_project change, which `build` runs before the issue updates; with
    no list it goes into `changes`."""
    cards = changes if cards is None else cards
    item = issue.get("project_item") or {}
    synced = (frontmatter.get("github") or {}).get("synced") or {}
    state = frontmatter.get("state", "backlog")
    card = OPTION_STATE.get(item.get("status"))
    # A closed issue is the GitHub value, as `pull` reads it. A plan that
    # read the card alone would find `same` when a person closed the issue
    # and left the card, and then reopen that issue.
    live = ghmodel.closed_state(issue, state) or card
    if not item.get("id"):
        # A Status value and a date need a Project card. An issue that is not
        # on the board gets one first, and `apply` takes its ID from that
        # call.
        cards.append(Change(
            "add_to_project", page_id,
            {"number": issue["number"], "node_id": issue["node_id"]},
            f"issue #{escape_controls(issue['number'])} is not on the "
            f"Project"))
    if live is None:
        # A new card, or a card with no Status, holds no value to take, so
        # the bundle state is the one to send. A `take` here would leave the
        # card empty on every run.
        verdict = "push"
    else:
        verdict = ghmodel.reconcile(state, live, synced.get("state"))
    if verdict == "conflict":
        conflicts.append(ghmodel.conflict_line(page_id, "state", state, live))
    elif verdict == "push" or (verdict == "same" and card != state):
        # `same` with another card Status: the issue is closed and the card
        # was not moved. The board must show the state of the issue.
        changes.append(Change(
            "set_status", page_id,
            {"item_id": item.get("id"), "field": STATUS_FIELD,
             "option": ghmodel.STATUS_OPTIONS[state], "state": state},
            f"the bundle moved {escape_controls(page_id)} to {state}"))
    # The open or closed state of the issue answers to the state of the page,
    # not to the verdict. A card that a person moved to Done gives `same`, and
    # the issue would then stay open for ever. `take` is the one verdict this
    # skips: GitHub moved, and `pull` writes the page.
    if verdict in ("push", "same"):
        if state in CLOSE_REASON and issue.get("state") == "OPEN":
            changes.append(Change(
                "close_issue", page_id,
                {"number": issue["number"], "node_id": issue["node_id"],
                 "reason": CLOSE_REASON[state]},
                f"{escape_controls(page_id)} is {state}"))
        elif state not in CLOSE_REASON and issue.get("state") == "CLOSED":
            changes.append(Change(
                "reopen_issue", page_id,
                {"number": issue["number"], "node_id": issue["node_id"]},
                f"{escape_controls(page_id)} is {state} and the issue is "
                f"closed"))
    owner = frontmatter.get("owner") or ""
    live = ghmodel.live_owner(issue)
    if owner.startswith("human:"):
        verdict = ghmodel.reconcile(owner, live, synced.get("owner"))
        if verdict == "conflict":
            conflicts.append(
                ghmodel.conflict_line(page_id, "owner", owner, live))
        elif verdict == "push":
            login = owner.split(":", 1)[1]
            # `gh issue edit` adds an assignee and never drops one. The old
            # assignee would stay, `live_owner` reads the first of the list,
            # and the next `pull` would take that name back into the page.
            changes.append(Change(
                "set_assignee", page_id,
                {"number": issue["number"], "login": login, "owner": owner,
                 "remove_logins": sorted(
                     set(issue.get("assignees") or []) - {login})},
                f"the bundle owner of {escape_controls(page_id)} changed"))


def subject(change: Change) -> str:
    """What the change acts on. A change of a page gives the page ID. A
    change with no page names the thing in its detail, because
    `create_issue_type` for Epic and for Story read the same line without
    it, and the user answers for each one before the apply."""
    if change.page:
        return escape_controls(change.page)
    name = change.detail.get("name") or change.detail.get("field")
    return escape_controls(name) if name else "-"


def render(plan: Plan, fmt: str = "text", prefix: str = "") -> str:
    """`prefix` goes in front of each change, so a dry run reads as `would
    create_issue ...` from this one formatter."""
    if fmt == "json":
        return json.dumps({
            "changes": [{"action": c.action, "page": c.page,
                         "detail": c.detail, "reason": c.reason}
                        for c in plan.changes],
            "conflicts": plan.conflicts,
            "refusals": plan.refusals,
        }, indent=2, sort_keys=True)
    lines = [f"{prefix}{c.action} {subject(c)}: {c.reason}"
             for c in plan.changes]
    lines += [f"CONFLICT: {line}" for line in plan.conflicts]
    lines += [f"REFUSE: {line}" for line in plan.refusals]
    return "\n".join(lines or ["no change"])
