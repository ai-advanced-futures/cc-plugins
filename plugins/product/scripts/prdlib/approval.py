"""The approval of an agent change: the text of `--approved-by`.

`prd.py` checks only the shape of the text. It cannot see who decided a D-id
or who wrote a card, so the log line names the text and a reader checks it.
"""
import re

from . import UsageError
from .textsafe import escape_controls

# (kind, regex), in the order of the spec: the first kind whose regex matches
# the whole text wins.
SHAPES = tuple((name, re.compile(pattern)) for name, pattern in (
    ("hitl card link", r"https://[a-z0-9.-]+\.slack\.com/archives/[A-Z0-9]+/p\d+(\?\S*)?"),
    ("PR URL", r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+([/?#]\S*)?"),
    ("issue", r"#\d+"),
    ("D-id", r"D-\d{3,}"),
    ("ANSWER id", r"ANSWER:[A-Za-z0-9._-]+"),
    ("URL", r"https?://\S+"),
))

# The kinds that cancel and reopen need: a person decided them on a card.
STRONG = ("hitl card link", "D-id")

# A change from one of these states to one of REOPEN_STATES is a reopen.
REOPEN_FROM = ("done", "released")
REOPEN_STATES = ("backlog", "ready", "claimed", "in_progress", "in_review", "blocked")

SHAPE_LIST = ("a PR URL or #<n>, a D-id, an ANSWER id, "
              "a hitl card link, or another URL")


def kind(text: str) -> str:
    """The kind of approval that `text` is, or a UsageError."""
    for name, pattern in SHAPES:
        if pattern.fullmatch(text):
            return name
    raise UsageError(
        f"{escape_controls(text)} is not an approval: give {SHAPE_LIST}")
