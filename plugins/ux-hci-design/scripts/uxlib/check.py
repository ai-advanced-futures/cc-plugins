"""The brain check of ux-hci-design. Each rule is a function of Ctx (see rules.py)."""
from __future__ import annotations

from uxlib.context import make
from uxlib.rules import RULES


def run(root, directory=None) -> list:
    ctx = make(root, directory)
    issues = []
    for rule in RULES:
        issues += rule(ctx)
    return issues
