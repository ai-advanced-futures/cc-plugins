#!/usr/bin/env bash
# Pricing Plugin — Session Start Hook
# Surfaces available upstream data so the agent can activate Path A or B
# without re-asking questions already answered by partner plugins.
#
# Outputs advisory messages to stdout when relevant data files are present.
# Silent when no pricing-relevant context exists.

set -euo pipefail

JTBD_NEW_DIR=".jtbd-market-discovery"
JTBD_DIR=".jtbd"
PRICING_DIR=".pricing"
CI_DIR=".competitive-intelligence"

msgs=()

# A jtbd result in the new folder comes first (activates Path A once the person confirms it).
# The old folder's files are announced only when there is no such result.
# Usable means the file parses and its `results` (not its `gaps`) hold a willingness_to_pay entry.
jtbd_result=""
if [[ -d "${JTBD_NEW_DIR}/results" ]] && command -v python3 >/dev/null 2>&1; then
    # -I: isolated mode. The cwd is the opened repo, so it must not be on sys.path,
    # and PYTHON* environment variables must not apply.
    jtbd_result=$(python3 -I - "$(pwd)/${JTBD_NEW_DIR}/results" <<'PY' || true
import json, pathlib, sys
found = ""
for path in sorted(pathlib.Path(sys.argv[1]).glob("*.json")):
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        continue
    results = doc.get("results") if isinstance(doc, dict) else None
    if isinstance(results, list) and any(
        isinstance(r, dict) and r.get("kind") == "willingness_to_pay" for r in results
    ):
        found = "yes"
print(found)
PY
)
fi

if [[ -n "$jtbd_result" ]]; then
    msgs+=("PRICING: jtbd result found in ${JTBD_NEW_DIR}/results/ — Path A pricing available once you confirm the run.")
else
    if [[ -f "${JTBD_DIR}/wtp-validation.json" ]]; then
        msgs+=("PRICING: ${JTBD_DIR}/wtp-validation.json found — Path A pricing available.")
    fi
    if [[ -f "${JTBD_DIR}/evc-analysis.json" ]]; then
        msgs+=("PRICING: ${JTBD_DIR}/evc-analysis.json found — EVC data available for pricing ceiling.")
    fi
    if [[ -f "${JTBD_DIR}/opportunity-scores.json" ]]; then
        msgs+=("PRICING: ${JTBD_DIR}/opportunity-scores.json found — opportunity scores available for audit context.")
    fi
fi

# Check for competitive intelligence strategic analysis (moat rarity data)
if [[ -f "${CI_DIR}/strategic-analysis.json" ]]; then
    msgs+=("PRICING: .competitive-intelligence/strategic-analysis.json found — competitor moat data available for MOAT_MULTIPLIER elicitation.")
fi

# Check for existing pricing recommendation (prior run present)
if [[ -f "${PRICING_DIR}/pricing-recommendation.json" ]]; then
    msgs+=("PRICING: .pricing/pricing-recommendation.json exists from a prior session — consider whether it needs updating.")
fi

# Check for existing audit report (prior audit present)
if [[ -f "${PRICING_DIR}/audit-report.md" ]]; then
    msgs+=("PRICING: .pricing/audit-report.md exists — a prior audit is available.")
fi

if [[ ${#msgs[@]} -gt 0 ]]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " Pricing Plugin — Upstream Data Detected"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for msg in "${msgs[@]}"; do
        echo " ${msg}"
    done
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

exit 0
