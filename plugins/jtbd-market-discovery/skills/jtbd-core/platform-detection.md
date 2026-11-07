---
name: jtbd-market-discovery:platform-detection
description: How a phase agent finds out whether a script gave its numbers, and what it does when none did
---

# Platform Detection

## Auto-Detect

No agent of this plugin has the `Bash` tool. In Claude Code (CLI), the skill runs the Python scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/` before it starts the agent, and it names the result file in the dispatch (for example `scores_path`, `evc-results.json`, `clusters_path` or `wtp_results_path`). Check the dispatch:
- **The dispatch names a result file** → read it with the Read tool. Use each number in it as written. Estimate no number that the file gives, because a script computed it.
- **The dispatch names no result file** (Claude.ai Web, or a script that failed) → use AI-powered analysis. Estimate only what no file gives, mark each estimate as an estimate, and record a gap.

## Claude Code (CLI) Path

- Precise calculations by the scripts, with pandas/numpy/scikit-learn
- The skill runs each script with `uv run`; the agent reads the result file
- CSV import/export, JSON output for downstream tools
- Full statistical analysis (ODI, k-means, Monte Carlo)

## Claude.ai Web Path

- AI-powered analysis using Claude reasoning
- User pastes data into the conversation as text or tables
- Approximate results (75–90% parity with Python scripts depending on phase)
- Markdown/text output only (no file exports)

## Reference

For full platform capability matrix, see: `skills/jtbd-core/platform-compat.md`
