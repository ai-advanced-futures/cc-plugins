"""One page as GitHub values. No I/O, so the tests need no network.

The issue body is generated whole. Its last line is the OKF marker, so the
script finds the page again when the `github` field of the page is lost. The
title carries the ID [inferred P3-2]. Each criterion is an unchecked task
[inferred P3-3]: GitHub lets a person tick a box, and a ticked
box in the stored body would give a difference that no page change explains.
"""
import json
import re

from .graph import CROSS_BUNDLE_PREFIX, entries_of
from .hashing import GENERATED_BLOCK_RE, short_digest
from .registry import DELIVERED_STATES, STATES, TYPES

MARKER_RE = re.compile(r"<!--\s*okf:\s*(\S+)\s*-->")
PRD_DIR = "docs/product/prd"


def marker(target: str) -> str:
    return f"<!-- okf: {target} -->"


def marker_target(body: str) -> str | None:
    found = MARKER_RE.search(body or "")
    return found.group(1) if found else None


def page_target(page_id: str, type_name: str) -> str:
    """The bundle-relative path of a page, as the marker writes it."""
    return f"/{TYPES[type_name].directory}/{page_id}.md"


def prose(body: str) -> str:
    """The body without the `# <ID>` heading and without a generated block."""
    text = GENERATED_BLOCK_RE.sub("", body or "")
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("# "):
        lines.pop(0)
    return "\n".join(lines).strip()


def issue_title(page_id: str, frontmatter: dict) -> str:
    return f"{page_id}: {frontmatter.get('title', page_id)}"


def _trace_link(target: str) -> str:
    rest = target[len(CROSS_BUNDLE_PREFIX):] if target.startswith(
        CROSS_BUNDLE_PREFIX) else target
    name = rest.rsplit("/", 1)[-1].removesuffix(".md")
    return f"- [{name}]({PRD_DIR}{rest})"


def issue_body(page_id: str, frontmatter: dict, body: str,
               criteria: list[tuple[str, str]]) -> str:
    parts = [frontmatter.get("description", "").strip()]
    text = prose(body)
    if text:
        parts.append(text)
    traces = [target for target, _entry in entries_of(frontmatter, "traces")]
    if traces:
        parts.append("## Traces\n\n" + "\n".join(
            _trace_link(target) for target in traces))
    if criteria:
        parts.append("## Acceptance criteria\n\n" + "\n".join(
            f"- [ ] {cid}: {title}" for cid, title in criteria))
    parts.append(marker(page_target(page_id, frontmatter.get("type", ""))))
    return "\n\n".join(part for part in parts if part) + "\n"


class Unresolved(Exception):
    """A relationship names a page that GitHub does not hold yet. The caller
    plans the create first and computes the hash after the apply."""


NEEDS_REVIEW = "needs-review"
# One Status option of the Project for each state, built from the registry:
# a state added there gets its option with no second edit here.
STATUS_OPTIONS = {state: state.replace("_", " ").capitalize()
                  for state in STATES}
OPTION_STATE = {option: state for state, option in STATUS_OPTIONS.items()}


def synced_of(frontmatter: dict) -> dict:
    """The two-direction pair at this moment. `apply` and `pull` both store
    it, and the next run reads it to tell which side moved."""
    synced = {"state": frontmatter.get("state", "backlog")}
    if (frontmatter.get("owner") or "").startswith("human:"):
        synced["owner"] = frontmatter["owner"]
    return synced


def live_owner(issue: dict) -> str | None:
    """The first assignee as an OKF owner, or None."""
    return f"human:{issue['assignees'][0]}" if issue.get("assignees") else None


def closed_state(issue: dict, page_state: str | None = None) -> str | None:
    """The state that a closed issue gives, or None for an open issue. A
    closed issue wins over its card: `plan` and `pull` both read it first,
    so the two read the same GitHub value.

    A closed issue says only that the work ended, so it cannot tell `done`
    from `released`. A card in a delivered state decides, then the delivered
    state of the page, else `done`. So a closed issue keeps a released page
    released, and only a card that a person moved to another delivered state
    changes it."""
    if issue.get("state") != "CLOSED":
        return None
    if issue.get("state_reason") == "NOT_PLANNED":
        return "cancelled"
    card = OPTION_STATE.get((issue.get("project_item") or {}).get("status"))
    if card in DELIVERED_STATES:
        return card
    return page_state if page_state in DELIVERED_STATES else "done"


def reconcile(page_value, live_value, synced, unsynced: str = "push") -> str:
    """The verdict for one two-direction field: same, push, take, or conflict.

    synced is the value at the last sync. A side that differs from it is the
    side that moved. Two moved sides are a conflict: the sync writes nothing
    for that field and asks the user.

    unsynced is the verdict when no value was ever synced, because no side
    can then be read as the one that moved. `plan` answers push: the bundle
    is the source of truth of the OKF graph, and a conflict for every card of
    a Project that already holds cards would make the first sync unusable
    [inferred]. `pull` answers conflict: it writes into the bundle, so it
    needs evidence that GitHub is the side that moved.
    """
    if page_value == live_value:
        return "same"
    if synced is None:
        return unsynced
    page_moved = page_value != synced
    live_moved = live_value != synced
    if page_moved and live_moved:
        return "conflict"
    return "push" if page_moved else "take"


def conflict_line(page_id: str, field: str, page_value, live_value) -> str:
    """The one sentence both `plan` and `pull` give for a moved field."""
    return (f"{page_id}: {field} is {page_value} in the bundle and "
            f"{live_value} in GitHub. Both changed since the last sync. "
            f"Choose one and run the sync again.")


def page_id_of(target: str) -> str:
    """The page ID of a bundle-relative target, such as /stories/STORY-11.md."""
    return target.rsplit("/", 1)[-1].removesuffix(".md")


def _number(refs: dict, target: str) -> int:
    page_id = page_id_of(target)
    if page_id not in refs:
        raise Unresolved(page_id)
    return refs[page_id]


# `ghplan.type_label` writes this prefix, and `page_type_of_label` reads it
# back. Both sides name it here, so the two cannot drift apart.
LABEL_PREFIX = "type:"
_TYPE_BY_LOWER = {name.lower(): name for name in TYPES}


def page_type_of_label(label: str, fallback: str = "Task") -> str:
    """The page type of an issue type name or a `type:` label.

    The inverse of `ghplan.type_label`, and its pair: a decode written at
    the one call site that needs it was a `capitalize()`, which cannot give
    back a type of two words. The lookup can.
    """
    name = str(label or "")
    if name.startswith(LABEL_PREFIX):
        name = name[len(LABEL_PREFIX):]
    return _TYPE_BY_LOWER.get(name.lower(), fallback)


def _label_type(issue: dict) -> str:
    """The `type:` label of an issue, or "" when it carries none."""
    return next((name for name in sorted(issue.get("labels") or [])
                 if name.startswith(LABEL_PREFIX)), "")


def live_type(issue: dict, type_label: str) -> str | None:
    """The type of an issue, in the form the push payload writes.

    A repository that takes the `type:` label path holds no issue type, so
    the live value is the `type:` label. Reading `issueType` there gives
    `type:` for every page, and every `pull` then reports a false difference
    on `type`.
    """
    if not type_label.startswith(LABEL_PREFIX):
        return issue.get("type")
    return _label_type(issue)


def page_type_of_issue(issue: dict, fallback: str = "Task") -> str:
    """The page type of an issue: its issue type, or its `type:` label."""
    return page_type_of_label(issue.get("type") or _label_type(issue),
                              fallback)


def labels_of(frontmatter: dict, type_label: str) -> list[str]:
    labels = set(frontmatter.get("tags") or [])
    if frontmatter.get("drifted"):
        labels.add(NEEDS_REVIEW)
    if type_label.startswith(LABEL_PREFIX):
        labels.add(type_label)
    return sorted(labels)


def push_payload(page_id: str, frontmatter: dict, body: str, type_label: str,
                 refs: dict, criteria=()) -> dict:
    """The nine push-only values, in GitHub form. Raises Unresolved when a
    relationship names a page that has no issue yet."""
    parent = frontmatter.get("parent")
    milestone = frontmatter.get("milestone")
    return {
        "title": issue_title(page_id, frontmatter),
        "body": issue_body(page_id, frontmatter, body, list(criteria)),
        "type": type_label,
        "parent": _number(refs, parent) if parent else None,
        "blocked_by": sorted(_number(refs, target) for target
                             in (frontmatter.get("blocked_by") or [])),
        "milestone": _number(refs, milestone) if milestone else None,
        "planned_start": frontmatter.get("planned_start_date"),
        "planned_end": frontmatter.get("planned_end_date"),
        "labels": labels_of(frontmatter, type_label),
    }


def push_hash(payload: dict) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return short_digest(text)
