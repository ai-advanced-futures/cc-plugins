# Changelog

## 0.6.0

This version is the port of the plugin to this repository.

- The plugin has no contract with a host system of the source repository. No
  agent has a mode that skips a question, and no agent asks the person a
  question.
- The commands `profile` and `setup` ask the questions. All four commands
  dispatch the agents with the Agent tool and the full agent names.
- The skills have bare names that equal the names of their folders.
- Each script runs with `uv run ${CLAUDE_PLUGIN_ROOT}/lib/<file>.py` and has a
  PEP 723 header.
- The fact check dispatches `grounded-synthesis:grounded-synthesis-orchestrator`.
  When that agent fails, the run goes on with 2 iterations at most and marks
  the output UNVERIFIED FACTS.
- `fact_gate.py` stops with exit code 1 when the handoff file has the status
  failed.
- `extract_prose.py` has the option `--out`. `hf_detectors.py` prints its
  availability when it runs as a script.
- The live tests are in `tests/integration/`. They run with `make itest TIER=hf`.

## 0.5.0

The version of the source repository. The next versions are in this file.
