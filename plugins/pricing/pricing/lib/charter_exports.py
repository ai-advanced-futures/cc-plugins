"""Charter exports — stable surface that cross-plugin tests bind to.

Per spec §12. Pricing-core sub-spec is free to rename internal modules;
this file's symbols do not change. If a symbol must change, bump pricing's
major version and update the Charter §11.3.2 test in standards.
"""
from vocabulary_linter.terminals import CANONICAL_TERMINALS, canonical_terminal_node

from pricing.lib.pattern_catalogue import PATTERN_IDS, PATTERNS, PatternDef

__all__ = [
    "PATTERN_IDS",
    "PATTERNS",
    "PatternDef",
    "canonical_terminal_node",
    "CANONICAL_TERMINALS",
]
