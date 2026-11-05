"""The warnings of `ddd.py check`: W1 to W6, W8, and W9. The general check of
the knowledge plugin owns page size (A21)."""
import re
from datetime import datetime, timedelta, timezone

from .bundle import Bundle, context_page, glossary_types, stored_edges
from .issues import WARN, Issue
from .links import START
from .page import line_of

QUESTION_DAYS = 30
ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
# The heuristic of event_storm_serializer.is_past_tense in ddd-design 0.2.0
# (MIT, Luis F. Amadeo). See NOTICE.
PAST_SUFFIXES = ("ed", "en")
IRREGULAR = {"Made", "Sent", "Built", "Sold", "Lost", "Won", "Set", "Cut",
             "Run", "Hit", "Put", "Met", "Got", "Gone", "Done", "Said",
             "Read", "Spent", "Lent", "Bent", "Found", "Bound"}


def code_form(title: str) -> str:
    """`Order placed` -> `OrderPlaced`. A title in code form stays."""
    words = re.split(r"[\s_-]+", title.strip())
    return "".join(word[:1].upper() + word[1:] for word in words if word)


def is_past_tense(name: str) -> bool:
    if not re.fullmatch(r"[A-Z][A-Za-z]+", name or ""):
        return False
    last = re.findall(r"[A-Z][a-z]*", name)[-1]
    return last.lower().endswith(PAST_SUFFIXES) or last in IRREGULAR


def invariant_items(body: str) -> int:
    """The number of list items under `## Invariants`."""
    count, inside = 0, False
    for line in body.splitlines():
        if line.startswith("## ") or line.startswith(START):
            inside = line.strip() == "## Invariants"
            continue
        if inside and ITEM_RE.match(line):
            count += 1
    return count


def _parse_time(value):
    try:
        when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def w1(bundle: Bundle) -> list:
    """A Term, Aggregate, or Event has no `context`."""
    return [Issue(WARN, "W1", path, 1, f"the {page.type} has no context")
            for path, page in bundle.pages.items()
            if page.type in glossary_types() and not page.frontmatter.get("context")]


def w2(bundle: Bundle) -> list:
    """An Aggregate is in a Context that has no `subdomain` (Evans §A2)."""
    out = []
    for path, page in bundle.pages.items():
        if page.type != "Aggregate":
            continue
        found = context_page(bundle, page)
        if found is not None and not found.frontmatter.get("subdomain"):
            out.append(Issue(WARN, "W2", path, line_of(page, "context"),
                             f"{found.id} has no subdomain. Do the strategic "
                             f"work on the context before its aggregates."))
    return out


def w3(bundle: Bundle) -> list:
    """A live Aggregate has no item under `## Invariants` (Evans §A1)."""
    return [Issue(WARN, "W3", path, 1,
                  "the aggregate has no item under `## Invariants`. An "
                  "aggregate with no invariant is an anemic model.")
            for path, page in bundle.pages.items()
            if page.type == "Aggregate" and page.live
            and invariant_items(page.body) == 0]


def w4(bundle: Bundle) -> list:
    """An Event title is not in the past tense."""
    return [Issue(WARN, "W4", path, line_of(page, "title"),
                  f"the event {page.title!r} is not in the past tense, as in "
                  f"OrderPlaced")
            for path, page in bundle.pages.items()
            if page.type == "Event" and not is_past_tense(code_form(page.title))]


def w5(bundle: Bundle) -> list:
    """More than one Context has `subdomain: core`."""
    core = [page for page in bundle.pages.values()
            if page.type == "Context" and page.live
            and page.frontmatter.get("subdomain") == "core"]
    if len(core) < 2:
        return []
    names = ", ".join(sorted(page.id for page in core))
    return [Issue(WARN, "W5", page.path, line_of(page, "subdomain"),
                  f"more than one core context: {names}") for page in core]


def w6(bundle: Bundle) -> list:
    """A live edge points to a deprecated page."""
    out = []
    for path, page in bundle.pages.items():
        if not page.live:
            continue
        for field_name, target_id, target in stored_edges(bundle, page):
            other = bundle.pages.get(target)
            if other is not None and not other.live:
                out.append(Issue(WARN, "W6", path, line_of(page, field_name),
                                 f"{field_name}: {target_id} is deprecated"))
    return out


def w8(bundle: Bundle) -> list:
    """A page has no inbound edge and no outbound edge. Source and Question
    pages are exempt."""
    linked = set()
    for path, page in bundle.pages.items():
        for _field, _target_id, target in stored_edges(bundle, page):
            linked.update((path, target))
    return [Issue(WARN, "W8", path, 1, "the page has no edge (an orphan)")
            for path, page in bundle.pages.items()
            if page.type not in ("Source", "Question") and path not in linked]


def w9(bundle: Bundle) -> list:
    """An open Question is older than 30 days, by `generated.at`."""
    limit = datetime.now(timezone.utc) - timedelta(days=QUESTION_DAYS)
    out = []
    for path, page in bundle.pages.items():
        if page.type != "Question" or page.frontmatter.get("state") != "open":
            continue
        generated = page.frontmatter.get("generated")
        when = _parse_time(generated.get("at")) if isinstance(generated, dict) else None
        if when is not None and when < limit:
            out.append(Issue(WARN, "W9", path, line_of(page, "state"),
                             f"the question is open since "
                             f"{when.date().isoformat()}"))
    return out


RULES = [w1, w2, w3, w4, w5, w6, w8, w9]
