"""Vocabulary linter — the Charter, §5.3."""
from vocabulary_linter.terminals import (
    CANONICAL_TERMINALS,
    TERMINAL_ALIASES,
    canonical_terminal_node,
)
from vocabulary_linter.vocabulary import (
    Violation,
    lint_agent_file,
    lint_handoff_artifact,
    lint_text,
)

__all__ = [
    "CANONICAL_TERMINALS",
    "TERMINAL_ALIASES",
    "Violation",
    "canonical_terminal_node",
    "lint_agent_file",
    "lint_handoff_artifact",
    "lint_text",
]
