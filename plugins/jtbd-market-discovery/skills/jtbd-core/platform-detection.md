---
name: jtbd-market-discovery:platform-detection
description: How to detect Claude Code vs Claude.ai Web and adapt agent behavior
---

# Platform Detection

## Auto-Detect

Check whether the **Bash tool** is available:
- **Bash available** → Claude Code (CLI) → use Python scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/`
- **Bash unavailable** → Claude.ai Web → use AI-powered analysis

## Claude Code (CLI) Path

- Precise calculations using pandas/numpy/scikit-learn
- Run Python scripts directly (import from `${CLAUDE_PLUGIN_ROOT}/scripts/` or call via `uv run`)
- CSV import/export, JSON output for downstream tools
- Full statistical analysis (ODI, k-means, Monte Carlo)

## Claude.ai Web Path

- AI-powered analysis using Claude reasoning
- User pastes data into the conversation as text or tables
- Approximate results (75–90% parity with Python scripts depending on phase)
- Markdown/text output only (no file exports)

## Reference

For full platform capability matrix, see: `skills/jtbd-core/platform-compat.md`
