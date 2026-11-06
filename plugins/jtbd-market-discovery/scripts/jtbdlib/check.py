"""The brain check of the jtbd graph. Each rule is a function of Ctx (see rules.py)."""
from __future__ import annotations

from jtbdlib.context import make
from jtbdlib.rules import RULES


def run(root, directory=None) -> list:
    ctx = make(root, directory)
    issues = []
    for rule in RULES:
        issues += rule(ctx)
    return issues
