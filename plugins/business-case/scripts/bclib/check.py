"""The brain check of business-case. Each rule is a function of Ctx (see rules.py)."""
from __future__ import annotations

from bclib.context import make
from bclib.rules import RULES


def run(root, directory=None) -> list:
    ctx = make(root, directory)
    issues = []
    for rule in RULES:
        issues += rule(ctx)
    return issues
