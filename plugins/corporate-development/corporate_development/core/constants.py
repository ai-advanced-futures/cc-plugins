"""Named constants for gate decision thresholds across all M&A phases.

Using named constants instead of magic numbers ensures consistency and makes
the documented thresholds traceable from specification to code.
"""

# ---------------------------------------------------------------------------
# Phase 0 — Acquisition Readiness
# ---------------------------------------------------------------------------
READINESS_GO_THRESHOLD = 80           # score >= 80 → GO
READINESS_CONDITIONAL_UPPER = 79      # 65 <= score <= 79 → CONDITIONAL
READINESS_CONDITIONAL_LOWER = 65      # 50 <= score < 65 → CONDITIONAL (address gaps)
READINESS_NO_GO_THRESHOLD = 50        # score < 50 → NO_GO

# ---------------------------------------------------------------------------
# Phase 2 — Target Assessment
# ---------------------------------------------------------------------------
TARGET_GO_THRESHOLD = 75
TARGET_CONDITIONAL_THRESHOLD = 50

# ---------------------------------------------------------------------------
# Phase 3 — Operational Due Diligence
# ---------------------------------------------------------------------------
OPERATIONAL_GO_THRESHOLD = 70
OPERATIONAL_CONDITIONAL_THRESHOLD = 50

# ---------------------------------------------------------------------------
# Phase 4 — Financial Due Diligence
# ---------------------------------------------------------------------------
FINANCIAL_GO_THRESHOLD = 75
FINANCIAL_CONDITIONAL_THRESHOLD = 50
