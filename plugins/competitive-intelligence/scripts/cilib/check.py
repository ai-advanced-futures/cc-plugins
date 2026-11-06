"""The brain check of competitive-intelligence. Each rule is a function of Ctx (see rules.py)."""
from __future__ import annotations

from cilib.context import make
from cilib.rules import RULES


def run(root, directory=None) -> list:
    ctx = make(root, directory)
    issues = []
    for rule in RULES:
        issues += rule(ctx)
    return issues
