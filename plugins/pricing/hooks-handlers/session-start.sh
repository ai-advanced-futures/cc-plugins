#!/usr/bin/env bash
# Pricing Plugin — Session Start Hook
# Surfaces available upstream data so the agent can activate Path A or B
# without re-asking questions already answered by partner plugins.
#
# Outputs advisory messages to stdout when relevant upstream data or prior pricing files are present.
# Silent when no pricing-relevant context exists.

set -euo pipefail

PRICING_DIR=".pricing"

# The plugin folder, found from the path of this file (as probe-plugin.sh does).
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

msgs=()

# The jtbd graph and the competitive-intelligence graph. brain_read.py status prints 0, 1 or 2 plain lines,
# only for a graph that holds usable data. It names no file and no page.
# -I: isolated mode. The cwd is the opened repo, so it must not be on sys.path,
# and PYTHON* environment variables must not apply.
if command -v python3 >/dev/null 2>&1; then
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            msgs+=("$line")
        fi
    done < <(python3 -I "${PLUGIN_ROOT}/scripts/brain_read.py" status --root "$(pwd)" 2>/dev/null || true)
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
