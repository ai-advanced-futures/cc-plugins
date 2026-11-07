# Changelog

## 0.7.0

This version gives each agent a narrow tool grant (STORY-123).

- No agent has the tool `Bash` or `Agent`. Each agent has a `tools:` line, and
  the line holds only `Read` and `Write`, or `Read`.
- The agent `orchestrator` is gone. The command `humanize` runs the loop in the
  main conversation. The command `check` runs the `/check` steps. Both commands
  start the sub-agents with the Agent tool and the full agent names.
- The commands `check`, `humanize` and `profile` have `allowed-tools` for
  `uv run ${CLAUDE_PLUGIN_ROOT}/lib/*`. The commands `check` and `humanize` also
  allow the hf tier command (`uv run --with torch==2.15.0 --with transformers==5.22.2`). The
  versions are pinned, so a new release does not run without a review.
- The agent `detection-analyst` has the tool `Read` only. It reads the JSON
  files that the command wrote, and it returns the report as text. The command
  saves `report.md`, because the runtime refuses a file write by a sub-agent for
  a report.
- The scripts `zone_parser.py`, `correctness_checker.py`, `ste_checker.py` and
  `fault_delta.py` have the option `--out <path>`. They write the JSON to the
  file and print one line. An error exit writes no file.
- The script `run_detectors.py` has the option `--gate-error-file <path>`. It
  replaces `--gate-error`. A message from an agent reaches the script as a file,
  never as an argument. The old option is an error (exit code 2).
- Each placeholder in a command line is in single quotes. A value cannot add a
  second command.
- The plugin no longer prints the line `DONE: prose-authenticity`.
- The new test `tests/unit/test_agent_grants.py` fails when an agent holds a
  wide grant.

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
