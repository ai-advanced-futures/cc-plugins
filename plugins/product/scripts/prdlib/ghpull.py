"""`github pull`: GitHub back into the bundle.

A push-only field is never taken automatically. The script recomputes the hash
from the nine values that GitHub now holds and compares it with
`github.pushed_hash`. A difference means a person edited the issue, so the
script reports which of the nine values differ and writes nothing. The skill
asks: keep the OKF value, or take the GitHub value.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import DataError, ghmodel, ghplan, ghsnapshot
from .ids import resolve
from .lock import write_lock
from .new_page import create_locked
from .page import load_page, write_page
from .regen import collect
from .statecmd import apply_change as change_state, stored_state
from .textsafe import escape_controls, fold_single_line
from .tree import bundle_dir

PULLED = " (pulled from GitHub)"
APP_SUFFIX = "[bot]"


def pull_actor(login: str) -> str:
    """The actor of a pulled change. A GitHub App is an agent, not a person
    (DECISION-04: an agent never writes a `human:` actor), and its login
    ends with `[bot]`, which no actor holds. The actor is the slug with
    `-bot`: `example-app[bot]` gives `agent:example-app-bot`. A person has
    the `human:` actor, as before."""
    if login.endswith(APP_SUFFIX):
        return f"agent:{login[:-len(APP_SUFFIX)]}-bot"
    return f"human:{login}"


@dataclass
class Report:
    differences: list = field(default_factory=list)
    bound: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    unknown: list = field(default_factory=list)
    applied: list = field(default_factory=list)


def live_payload(root: Path, snapshot: dict, issue: dict, page_id: str,
                 frontmatter: dict | None = None) -> dict:
    """The nine values, read from GitHub, in the same form the push uses.

    `frontmatter` is the page, when the caller already holds it."""
    if frontmatter is None:
        frontmatter, _body = ghplan.work_items(root)[page_id]
    label = ghplan.type_label(frontmatter, snapshot)
    item = issue.get("project_item") or {}
    return {
        "title": issue.get("title", ""),
        "body": issue.get("body", ""),
        "type": ghmodel.live_type(issue, label),
        "parent": issue.get("parent"),
        "blocked_by": sorted(issue.get("blocked_by") or []),
        "milestone": issue.get("milestone"),
        "planned_start": item.get("planned_start"),
        "planned_end": item.get("planned_end"),
        "labels": sorted(issue.get("labels") or []),
    }


def live_hash(root: Path, snapshot: dict, issue: dict, page_id: str) -> str:
    return ghmodel.push_hash(live_payload(root, snapshot, issue, page_id))


def pull(root: Path, snapshot: dict, login: str, adopt: bool = False,
         now: datetime | None = None) -> Report:
    """Take the lock, then pull (`_pull`). The snapshot comes from the caller,
    so the pull makes no network call while it holds the lock (STORY-441)."""
    with write_lock(root):
        return _pull(root, snapshot, login, adopt, now)


def _pull(root: Path, snapshot: dict, login: str, adopt: bool = False,
          now: datetime | None = None) -> Report:
    """`pull` with the lock held by the caller. The state change calls
    `apply_change` and the adopt calls `create_locked`, because write_lock is
    not re-entrant."""
    now = now or datetime.now(timezone.utc)
    report = Report()
    # One walk of the tree for the whole pull. The readers below take the
    # page they need from it, so no page is parsed again for each item.
    tree = collect(root)
    pages = ghplan.work_items(root, tree)
    known_numbers = ghplan.numbers_of(pages)
    issues = ghsnapshot.issues_by_page(snapshot, known_numbers)
    refs = ghsnapshot.refs(snapshot, known_numbers)
    criteria = ghplan.criteria_of(root, tree)
    for page_id, (frontmatter, body) in pages.items():
        issue = issues.get(page_id)
        stored = (frontmatter.get("github") or {}).get("pushed_hash")
        if issue is None:
            continue
        if not stored:
            if ghplan.is_bound(stored, issue):
                report.bound.append(
                    f"{escape_controls(page_id)}: issue "
                    f"#{escape_controls(issue['number'])} holds the title and "
                    f"body that a person wrote, and the page has no "
                    f"pushed_hash. The sync sends no title or body to it. "
                    f"Send the bundle text with `github apply --keep "
                    f"{escape_controls(page_id)}`, or leave the issue as it "
                    f"is.")
            continue
        # The two-direction fields come first. A page that was pushed
        # correctly has a hash that matches, and the difference block below
        # ends the round for it, so a state pull placed after that block
        # would never run for the normal case. [inferred]
        agreed = set()
        if _pull_state(root, page_id, frontmatter, issue, login, report,
                       now, tree):
            agreed.add("state")
        # `_pull_state` may have written the page, so it is read once here
        # and the two writers below share that one copy.
        page = load_page(resolve(root, page_id, tree))
        if _pull_owner(page, page_id, issue, report):
            agreed.add("owner")
        _store_synced(page, agreed)
        try:
            mine = ghplan.stored_payload(page_id, frontmatter, body, snapshot,
                                         refs, criteria)
        except ghmodel.Unresolved:
            continue
        live = live_payload(root, snapshot, issue, page_id, frontmatter)
        if ghmodel.push_hash(live) == stored:
            continue
        # The payload is the key set: a value added to it is named here
        # with no second list to keep in step.
        names = sorted(key for key in mine if live[key] != mine[key])
        report.differences.append(
            f"{escape_controls(page_id)}: a person changed "
            f"{', '.join(names)} in issue "
            f"#{escape_controls(issue['number'])}. Keep the bundle value with "
            f"`github apply --keep {escape_controls(page_id)}`, or take the "
            f"GitHub value into the page.")
    _adopt(root, snapshot, report, adopt, known_numbers)
    return report


def _pull_state(root, page_id, frontmatter, issue, login, report, now, tree):
    """True when the two sides now hold the same state, so the caller may
    move the synced marker to it. `tree` is the caller's one walk of the
    bundle, which the state write reads and then keeps current."""
    item = issue.get("project_item") or {}
    synced = (frontmatter.get("github") or {}).get("synced") or {}
    page_state = frontmatter.get("state", "backlog")
    live = (ghmodel.closed_state(issue, page_state)
            or ghplan.OPTION_STATE.get(item.get("status")))
    if live is None:
        return False
    # `pull` writes into the bundle, so a field that was never synced is a
    # conflict here and not a push.
    verdict = ghmodel.reconcile(page_state, live, synced.get("state"),
                                unsynced="conflict")
    if verdict == "conflict":
        report.conflicts.append(
            ghmodel.conflict_line(page_id, "state", page_state, live))
        return False
    if verdict == "same":
        return True
    if verdict != "take":
        # The bundle moved and `apply` pushes it. The marker must stay where
        # it is: a marker that moved with the page would make the next
        # `plan` read GitHub as the side that moved, and the change would
        # never reach GitHub.
        return False
    # A closed issue names the person who closed it; a moved card names the
    # person who moved it. When the card gives the state of a closed issue
    # (`released`), the card person is the one who chose it. Neither is always
    # readable, so the gh login is the fallback and the Event line says the
    # change came from GitHub.
    mover = item.get("status_actor")
    if not ghmodel.closed_state(issue):
        who = mover
    elif ghplan.OPTION_STATE.get(item.get("status")) == live:
        who = mover or issue.get("closed_by")
    else:
        who = issue.get("closed_by")
    # `ready` and `blocked` are computed from the blockers, so the write can
    # store a value other than the GitHub one. The check runs before the
    # write: a write of the computed value is a change that nobody asked
    # for, with an Event line of its own.
    computed = stored_state(root, frontmatter, live, tree)
    if computed != live:
        report.conflicts.append(
            f"{escape_controls(page_id)}: GitHub is {live} and the bundle "
            f"stays {escape_controls(page_state)}, "
            f"because the blockers give {computed}. Close the blockers, or "
            f"change them, and run the sync again.")
        return False
    actor = pull_actor(who or login)
    # The change is already made in GitHub. For an agent, the issue is the
    # approval that the state command asks for (DECISION-04, D-037). A cancel
    # and a reopen need a hitl card or a D-id: the pull has none, so it names
    # the way out and writes nothing.
    approved_by = None if actor.startswith("human:") else f"#{issue['number']}"
    try:
        change_state(root, page_id, live, actor, now=now, tree=tree,
                     approved_by=approved_by)
    except DataError as refusal:
        if approved_by is None:
            raise
        # `refusal` is the text of the state command. It holds the actor, a
        # value that a snapshot file gave, so it is escaped here as well.
        line = (f"{escape_controls(page_id)}: {escape_controls(actor)} moved "
                f"issue #{escape_controls(issue['number'])} to "
                f"{live}, and the bundle stays {escape_controls(page_state)}. "
                f"{escape_controls(refusal)}.")
        # Only a cancel or a reopen is a refusal that a card or a D-id fixes.
        # Another refusal (for example, no spec for backlog to ready) stays
        # with no command, because an approval does not change it.
        if "hitl card link" in str(refusal):
            line += (f" Make the move with `prd.py state "
                     f"{escape_controls(page_id)} {live} "
                     f"--actor {escape_controls(actor)} --approved-by "
                     f"<card or D-id>`.")
        report.conflicts.append(line)
        return False
    if not who:
        _mark_pulled(root, page_id)
    report.applied.append(f"{escape_controls(page_id)}: state "
                          f"{escape_controls(page_state)} -> {live}")
    return True


def _mark_pulled(root, page_id):
    """The Event line of a change with no GitHub login ends with a note, so a
    reader can tell a pulled change from a change a person made here."""
    path = bundle_dir(root, "roadmap") / "log.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"* **State**: [{page_id}]"):
            lines[index] = line + PULLED
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pull_owner(page, page_id, issue, report):
    """True when the two sides now name the same owner."""
    frontmatter = page.frontmatter
    owner = frontmatter.get("owner") or ""
    if owner.startswith("agent:"):
        return False                # an agent owner has no assignee.
    live = ghmodel.live_owner(issue)
    synced = ((frontmatter.get("github") or {}).get("synced")
              or {}).get("owner")
    if live == owner:
        return True
    if live is None:
        # The bundle names an owner that GitHub has not got yet. `apply`
        # pushes it, so the marker stays where it is.
        return False
    if owner and owner != synced:
        report.conflicts.append(
            ghmodel.conflict_line(page_id, "owner", owner, live))
        return False
    frontmatter["owner"] = live
    write_page(page)
    report.applied.append(f"{escape_controls(page_id)}: owner "
                          f"{escape_controls(owner) if owner else '-'} -> "
                          f"{escape_controls(live)}")
    return True


def _store_synced(page, agreed):
    """Move the marker for each field that the pull put in agreement, and
    leave the others where they are. A field where the bundle moved is still
    waiting for `apply`: a marker that moved with the page would make the
    next `plan` read GitHub as the side that moved, and the bundle value
    would never reach GitHub."""
    field = dict(page.frontmatter.get("github") or {})
    synced = dict(field.get("synced") or {})
    now = ghmodel.synced_of(page.frontmatter)
    for name in agreed:
        if name in now:
            synced[name] = now[name]
        else:
            synced.pop(name, None)
    if field.get("synced") == synced:
        return
    field["synced"] = synced
    page.frontmatter["github"] = field
    write_page(page)


def _adopt(root, snapshot, report, adopt, stored):
    """An issue in the Project with no page. The spec pulls it in only after
    the user agrees, so the default reports it and writes nothing, and
    --adopt is the gate. [inferred P3-6]

    `stored` maps each issue number that a page names to that page. The
    adopt writes the number and the hash of the GitHub values to the page,
    not the issue body, so the marker is absent until the next apply, and
    the stored number is what keeps a second pull from making a second page
    for the same issue."""
    known = {issue["number"] for issue in
             ghsnapshot.issues_by_page(snapshot, stored).values()}
    known |= set(stored)
    for issue in snapshot.get("issues") or []:
        # An issue with no card is not roadmap work, such as a bug report.
        # Only the Project says what belongs to the roadmap.
        if issue["number"] in known or not issue.get("project_item"):
            continue
        type_name = ghmodel.page_type_of_issue(issue)
        if not adopt:
            report.unknown.append(
                f"#{escape_controls(issue['number'])} "
                f"{escape_controls(issue.get('title', ''))} has no page. "
                f"Run `github pull --adopt` to make a {type_name} page in "
                f"backlog.")
            continue
        # GitHub text is not ours to refuse: a body from the web UI ends each
        # line with CR LF, and a title can hold a tab. Fold both to one line.
        path = create_locked(
            root, type_name,
            fold_single_line(issue.get("title", "")),
            fold_single_line(
                (issue.get("body") or "").strip().split("\n")[0])[:200],
            status="draft", body=issue.get("body") or "")
        page = load_page(path)
        page.frontmatter["github"] = {
            "number": issue["number"], "node_id": issue["node_id"],
            "url": issue.get("url", ""),
            "synced": {"state": "backlog"}}
        # The hash of the values that the issue holds, so the page is not a
        # bound page, and a person's edit after the adopt gives a difference.
        # The next apply sends the bundle text, which keeps the issue body.
        page.frontmatter["github"]["pushed_hash"] = ghmodel.push_hash(
            live_payload(root, snapshot, issue, path.stem, page.frontmatter))
        write_page(page)
        known.add(issue["number"])
        report.applied.append(
            f"{escape_controls(path.stem)}: adopted issue "
            f"#{escape_controls(issue['number'])} in backlog")


def render(report: Report, fmt: str = "text") -> str:
    if fmt == "json":
        return json.dumps({"applied": report.applied,
                           "bound": report.bound,
                           "conflicts": report.conflicts,
                           "differences": report.differences,
                           "unknown": report.unknown},
                          indent=2, sort_keys=True)
    lines = [f"APPLIED: {line}" for line in report.applied]
    lines += [f"DIFFERENT: {line}" for line in report.differences]
    lines += [f"BOUND: {line}" for line in report.bound]
    lines += [f"CONFLICT: {line}" for line in report.conflicts]
    lines += [f"UNKNOWN: {line}" for line in report.unknown]
    return "\n".join(lines or ["no change"])
