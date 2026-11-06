"""Canonical terminal-node resolution — see Charter §11.1 check 5."""
from __future__ import annotations

CANONICAL_TERMINALS = frozenset({"A.2", "A.3", "B.2", "B.3", "C.2", "C.3", "E.2", "E.3"})
TERMINAL_ALIASES = {
    "D.2": "B.2",  # framework: D.2 is an alternate label for B.2
}


def canonical_terminal_node(node: str) -> str:
    """Resolve a terminal-node string to its canonical form.

    Accepts the 9 strings in the schema enum (A.2, A.3, B.2, B.3, C.2, C.3, D.2, E.2, E.3).
    Returns one of the 8 canonical terminals.
    Raises ValueError for unknown inputs.
    """
    if node in CANONICAL_TERMINALS:
        return node
    if node in TERMINAL_ALIASES:
        return TERMINAL_ALIASES[node]
    raise ValueError(f"unknown terminal node: {node!r}")
