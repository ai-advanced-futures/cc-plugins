from __future__ import annotations

PLUGIN_VERSION: str = "0.4.4"
DEFAULT_FACTS_PER_SOURCE: int = 12
FACTS_PER_SOURCE_BOUNDS: tuple[int, int] = (8, 20)
ALLOWED_EXTENSIONS: tuple[str, ...] = (".md", ".markdown", ".txt", ".pdf")
COVERAGE_VERDICTS: tuple[str, ...] = ("PRESENT", "MISSING")  # v0.1.0 binary only; partial-coverage verdict deferred to v0.2.0

# Sonnet context-window safety budget. Reserve OVERHEAD_BUDGET tokens for system
# prompt + agent prose + dispatch context inside fact-extractor; the source-text
# cap MAX_SOURCE_TOKENS is set so that even a max-size source keeps the fact-extractor
# context under CRITICAL_CONTEXT_THRESHOLD.
CRITICAL_CONTEXT_THRESHOLD: int = 150_000
OVERHEAD_BUDGET: int = 5_000
MAX_SOURCE_TOKENS: int = CRITICAL_CONTEXT_THRESHOLD - OVERHEAD_BUDGET  # 145_000

OUTPUT_SUFFIX: str = ".grounded-synthesis-report.md"

# Caller contract (ADR-007): dispatch fields that the orchestrator must document.
# A change here breaks each caller agent that sends these fields.
EXPECTED_DISPATCH_FIELDS: frozenset[str] = frozenset({
    "draft_path",
    "source_paths",
    "key_facts_per_source",
    "output_dir_override",
    "output_path",
})
