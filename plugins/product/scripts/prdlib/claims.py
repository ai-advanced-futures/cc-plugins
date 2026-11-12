"""Claims: the lease of one agent on one work item.

A claim is a field group on the work item, not a page. The lock covers one
working tree only. Between clones git is the check: two claims change the
same `claim` lines, so the second push gets a conflict.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import DataError, UsageError
from .ids import resolve
from .lock import write_lock
from .logbook import append_entry, entry_line, timestamp
from .page import load_page, write_page
from .regen import collect
from .registry import WORK_ITEMS
from .statecmd import apply_change, require_actor
from .textsafe import escape_controls
from .times import parse_time
from .tree import bundle_dir, iter_pages

DEFAULT_LEASE = "30m"
LEASE_RE = re.compile(r"^(\d+)([smh])$")
UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


def parse_lease(text: str) -> int:
    """The seconds of a lease string such as 45s, 30m, or 2h."""
    match = LEASE_RE.match(str(text or ""))
    if not match:
        raise UsageError(
            f"{escape_controls(text)} is not a lease. Use 45s, 30m, or 2h.")
    seconds = int(match.group(1)) * UNIT_SECONDS[match.group(2)]
    if seconds == 0:
        raise UsageError("a lease of zero holds the item for no time. Use 30m.")
    return seconds


def is_live(claim: object, now: datetime) -> bool:
    """A claim with a lease in the future holds the item."""
    if not isinstance(claim, dict):
        return False
    lease = parse_time(claim.get("lease_expires_at"))
    return bool(lease and lease > now)


def _log(root: Path, page, text: str, actor: str, now: datetime) -> None:
    bundle_root = bundle_dir(root, "roadmap")
    append_entry(
        bundle_root / "log.md",
        entry_line("Claim", page.path.stem,
                   str(page.path.relative_to(bundle_root)), text, actor, now),
        now)


def _refuse_unclaimable(page, now: datetime) -> None:
    """Raise when this page cannot be claimed. It writes nothing, so a group
    runs it for every member before the group writes its first page."""
    if page.type not in WORK_ITEMS:
        raise DataError(
            f"{escape_controls(page.path.stem)} is a "
            f"{escape_controls(page.type)}, which cannot be claimed")
    # The live lease is read before the state, because a held item is
    # in the claimed state: reading the state first names the state and
    # hides the agent that holds the item.
    held = page.frontmatter.get("claim")
    if is_live(held, now):
        # `by` is a required key of the Claim class, and rule E2 reports a
        # claim without it. This message must still name the holder and
        # not raise a KeyError over the page that E2 rejects.
        raise DataError(
            f"{escape_controls(page.path.stem)} is claimed by "
            f"{escape_controls(held.get('by', 'no one'))} until "
            f"{escape_controls(held.get('lease_expires_at'))}")
    state = page.frontmatter.get("state", "backlog")
    if state != "ready":
        raise DataError(
            f"{escape_controls(page.path.stem)} is {escape_controls(state)}. "
            "Only a ready item can be claimed.")


def claim(root: Path, identifier: str | list[str], actor: str,
          lease: str = DEFAULT_LEASE,
          now: datetime | None = None) -> list[Path]:
    """Take every ready item of the group, or take none of them.

    One spec covers one Story or more, and one spec is built one time. Two
    ready Stories of one spec must not start two builds, so every member is
    checked first and the pages are written after: a group with one bad
    member writes nothing and needs no rollback.
    """
    seconds = parse_lease(lease)
    require_actor(actor)
    now = now or datetime.now(timezone.utc)
    wanted = [identifier] if isinstance(identifier, str) else list(identifier)
    if not wanted:
        raise UsageError("claim needs one ID or more")
    taken = []
    with write_lock(root):
        # One walk for the whole group, as in expire. Each claim resolves its
        # ID and computes ready or blocked from it, and `apply_change` puts the
        # written state back, so a member claimed here is current for the next.
        tree = collect(root)
        # Two identifiers can name one page, because `resolve` accepts an
        # alias. The dedup keeps one claim and one log line for that page.
        pages, seen = [], set()
        for one in wanted:
            path = resolve(root, one, tree)
            if path in seen:
                continue
            seen.add(path)
            pages.append(load_page(path))
        for page in pages:
            _refuse_unclaimable(page, now)
        for page in pages:
            page.frontmatter["claim"] = {
                "by": actor,
                "at": timestamp(now),
                "lease_expires_at": timestamp(now + timedelta(seconds=seconds)),
            }
            if not page.frontmatter.get("owner"):
                page.frontmatter["owner"] = actor
            # The claim is on the page before the state change, because
            # apply_change reads the page again.
            write_page(page)
            apply_change(root, page.path.stem, "claimed", actor, now=now,
                         tree=tree)
            _log(root, page,
                 f"claimed until {page.frontmatter['claim']['lease_expires_at']}",
                 actor, now)
            taken.append(page.path)
    return taken


def heartbeat(root: Path, identifier: str, actor: str,
              lease: str = DEFAULT_LEASE,
              now: datetime | None = None) -> Path:
    """Move the lease of a claim forward.

    The lease may already be over: the same agent takes its own work back,
    and the `by` check refuses it after another agent claimed the item.
    """
    seconds = parse_lease(lease)
    # The same actor test as claim: a bad actor string must never reach a
    # page or the log.
    require_actor(actor)
    now = now or datetime.now(timezone.utc)
    with write_lock(root):
        path = resolve(root, identifier)
        page = load_page(path)
        held = page.frontmatter.get("claim")
        if not isinstance(held, dict):
            raise DataError(
                f"{escape_controls(path.stem)} has no claim to extend")
        if held.get("by") != actor:
            raise DataError(
                f"{escape_controls(path.stem)} is claimed by "
                f"{escape_controls(held.get('by'))}, not {actor}")
        held["heartbeat_at"] = timestamp(now)
        held["lease_expires_at"] = timestamp(now + timedelta(seconds=seconds))
        write_page(page)
    return path


# The states a release gives back. An item in in_review waits for a person,
# and an item in blocked or done keeps its state.
RELEASABLE_STATES = ("claimed", "in_progress")


def release_page(root: Path, page, actor: str, now: datetime,
                 tree: dict | None = None) -> None:
    """Remove the claim and ask for ready. Call it with the lock held.

    `expire` releases many items in one run and passes its own walk of the
    bundle as `tree`, so the ready-or-blocked computation below does not
    read every page again for each item."""
    held = page.frontmatter.pop("claim", None)
    write_page(page)
    if page.frontmatter.get("state") in RELEASABLE_STATES:
        apply_change(root, page.path.stem, "ready", actor, now=now, tree=tree)
    holder = (held or {}).get("by", "no one")
    _log(root, page, f"released from {holder}", actor, now)


def release(root: Path, identifier: str, actor: str,
            now: datetime | None = None) -> Path:
    """Give one claimed item back."""
    # release_page writes the Event for every state, and apply_change runs
    # for two states only, so the actor test belongs here. [inferred]
    require_actor(actor)
    now = now or datetime.now(timezone.utc)
    with write_lock(root):
        path = resolve(root, identifier)
        page = load_page(path)
        if not isinstance(page.frontmatter.get("claim"), dict):
            raise DataError(
                f"{escape_controls(path.stem)} has no claim to release")
        release_page(root, page, actor, now)
    return path


def expire(root: Path, actor: str, now: datetime | None = None) -> list[Path]:
    """Release each item whose lease is in the past."""
    # The actor test comes first, as in claim: expire writes one Event for
    # each item it releases. [inferred]
    require_actor(actor)
    now = now or datetime.now(timezone.utc)
    released = []
    with write_lock(root):
        # One walk for the whole run. Each release computes ready or blocked
        # from it, and `apply_change` puts the written state back, so an item
        # released here is current for the item released next.
        tree = collect(root)
        for path in iter_pages(bundle_dir(root, "roadmap")):
            try:
                page = load_page(path)
            except DataError:
                # check reports this page as E1. One broken page must not
                # stop the release of every other item.
                continue
            held = page.frontmatter.get("claim")
            if not isinstance(held, dict) or is_live(held, now):
                continue
            release_page(root, page, actor, now, tree)
            released.append(path)
    return released
