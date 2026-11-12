"""`prd.py state`: the one write path for `state`.

A skill never edits `state` with an edit tool. Each change adds one Event, so
the log is complete. An `agent:` actor can make each change when the call
names an approval (`--approved-by`). The 5 moves of FREE_AGENT_MOVES need no
approval. A cancel, and a reopen from `done` or `released`, need a hitl card
link or a D-id. An agent never writes a `human:` actor.
"""
import re
from datetime import datetime, timezone
from pathlib import Path

from . import DataError, UsageError, approval
from .ids import resolve
from .lock import write_lock
from .logbook import append_entry, state_line
from .page import load_page, write_page
from .regen import COMPUTED_STATES, collect, computed_state
from .registry import DELIVERED_STATES, STATES, WORK_ITEMS
from .textsafe import escape_controls
from .tree import bundle_dir

# process:regen is regen's own internal actor (see regen.REGEN_ACTOR). regen
# writes its Event line directly, not through change(), so the CLI accepts
# only a human or an agent. Accepting process: here would let a caller skip
# the agent-transition check below.
ACTOR_RE = re.compile(r"(human|agent):[A-Za-z0-9._-]+")



def stored_state(root: Path, frontmatter: dict, wanted: str,
                 tree: dict | None = None) -> str:
    """The state that a request for `wanted` stores on this page.

    A request for ready or blocked gives the computed value: no actor sets
    those two states directly. A caller that must not write a value other
    than the one it asked for reads this first."""
    if wanted not in COMPUTED_STATES:
        return wanted
    walked = tree if tree is not None else collect(root)
    pages = {p: (b, fm) for p, (b, fm, _body) in walked.items()}
    trial = dict(frontmatter, state="ready")
    return computed_state(trial, bundle_dir(root, "roadmap"), pages) or "ready"

def require_actor(actor: str) -> None:
    """Every write path names its actor the same way, so the refusal is one
    sentence written one time."""
    if not ACTOR_RE.fullmatch(actor):
        raise UsageError(
            f"{escape_controls(actor)} is not an actor: use human:<login> or "
            "agent:<id>")


# The 5 moves of claim, release and expire. An agent makes them with no
# approval: they take work and give it back, and name no person. [decided: D-038]
FREE_AGENT_MOVES = {
    ("ready", "claimed"),
    ("claimed", "in_progress"),
    ("in_progress", "in_review"),
    ("claimed", "ready"),
    ("in_progress", "ready"),
}


def check_permission(root: Path, page, old: str, wanted: str, actor: str,
                     approved_by: str | None) -> None:
    """Refuse a change that the actor may not make. Nothing is written."""
    # A wrong shape stops here, for each actor.
    given = approval.kind(approved_by) if approved_by is not None else None
    if actor.startswith("human:"):
        return
    if (old, wanted) in FREE_AGENT_MOVES:
        return
    if given is None:
        raise DataError(
            f"an agent change from {escape_controls(old)} to {wanted} needs "
            "--approved-by: "
            f"{approval.SHAPE_LIST}")
    reopen = old in approval.REOPEN_FROM and wanted in approval.REOPEN_STATES
    if (wanted == "cancelled" or reopen) and given not in approval.STRONG:
        what = "cancel" if wanted == "cancelled" else f"reopen from {old}"
        raise DataError(
            f"an agent {what} needs --approved-by with a hitl card link or a "
            f"D-id that hitl decided (you gave: {given})")
    # A request for ready or blocked is a request to leave backlog: the
    # blockers decide which of the two is stored.
    if (page.type == "Story" and old == "backlog"
            and wanted in COMPUTED_STATES):
        spec = page.frontmatter.get("spec")
        if not isinstance(spec, str) or spec in ("", "none"):
            raise DataError(
                f"{escape_controls(page.id)} has no spec: an agent sets a Story to "
                f"ready only when its spec file is in the tree")
        base = root.resolve()
        target = (base / spec).resolve()
        if not (target.is_relative_to(base) and target.is_file()):
            raise DataError(
                f"{escape_controls(page.id)}: the spec file "
                f"{escape_controls(spec)} is not in the tree")


def change(root: Path, identifier: str, wanted: str, actor: str,
           now: datetime | None = None, tree: dict | None = None,
           approved_by: str | None = None) -> str:
    """The CLI path: take the lock, then apply the change."""
    with write_lock(root):
        return apply_change(root, identifier, wanted, actor, now=now,
                            tree=tree, approved_by=approved_by)


def apply_change(root: Path, identifier: str, wanted: str, actor: str,
                 now: datetime | None = None,
                 tree: dict | None = None,
                 approved_by: str | None = None) -> str:
    """The same change with the lock already held.

    claim, release, and expire call this one: write_lock is an exclusive
    create and is not re-entrant, so a nested `with write_lock(root)` waits
    the full timeout and then raises.

    `tree` is a `regen.collect` map the caller already holds. This function
    reads the whole tree twice for each call without it, once to resolve the
    ID and once to compute ready or blocked, so a caller in a loop passes
    its own map. The written state is put back into that map below: a later
    call in the same loop must read the new state of a blocker, not the one
    the map held when the loop started.
    """
    if wanted not in STATES:
        raise DataError(f"{escape_controls(wanted)} is not a state")
    require_actor(actor)
    now = now or datetime.now(timezone.utc)

    path = resolve(root, identifier, tree)
    page = load_page(path)
    if page.type not in WORK_ITEMS:
        raise DataError(f"{escape_controls(path.stem)} is a "
                        f"{escape_controls(page.type)}, which has no state")
    old = page.frontmatter.get("state", "backlog")

    # The permission answers the request, not the computed value. An agent
    # releases an item to ready; the blockers then decide whether ready or
    # blocked is stored. Reading the computed value first refuses the
    # release of an item that has an open blocker. [inferred]
    check_permission(root, page, old, wanted, actor, approved_by)

    wanted = stored_state(root, page.frontmatter, wanted, tree)

    if old == wanted:
        return wanted

    page.frontmatter["state"] = wanted
    if wanted == "in_progress" and not page.frontmatter.get("actual_start_date"):
        page.frontmatter["actual_start_date"] = now.strftime("%Y-%m-%d")
    if wanted in DELIVERED_STATES and old not in DELIVERED_STATES:
        page.frontmatter["actual_end_date"] = now.strftime("%Y-%m-%d")
    elif old in DELIVERED_STATES and wanted not in DELIVERED_STATES:
        # The end date belongs to the delivered states. A person who reopens
        # an item must not leave a finish date on open work.
        page.frontmatter.pop("actual_end_date", None)
    write_page(page)
    if tree is not None and path in tree:
        bundle, _old_fm, body = tree[path]
        tree[path] = (bundle, page.frontmatter, body)

    bundle_root = bundle_dir(root, "roadmap")
    append_entry(
        bundle_root / "log.md",
        state_line(path.stem, str(path.relative_to(bundle_root)),
                   old, wanted, actor, now, approved_by),
        now)
    return wanted
