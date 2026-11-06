# Changelog

## 0.2.0

- The plugin is a port of version 0.1.0 from commit `c2a329f` of a private repository.
- The skills ask the intake questions and write `context.yaml`. The question text is in `docs/intake.md`. The intake agent is removed.
- The orchestrator asks nothing. It starts the 3 domain agents with 3 `Agent` calls in one message, then the synthesizer, then the deliverable generator, and ends with `DONE: data-strategy`. The wave orchestrator and the Teams mode are removed.
- The 5 scoring scripts have a command line and a PEP 723 header. The domain agents run them with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`, so the scores come from the scripts. `session_manager.py` has the commands `done`, `all-done`, and `has-files`. A skill decides that a run is done from the flag file or the output files, and the `DONE` line of an agent is a second sign. An agent that runs a scoring script stops, writes no flag, and reports the error line when the script exits with a code that is not 0.
- The parts for a mission runner of the source repository are removed: `release.json`, the unattended mode, and `handoff_builder.py`.
- The executive presentation and the offer to make slides are removed. The plugin writes 3 deliverables.
- The 5 skills have the names of their folders and a description. The 5 commands are removed. The agents have no colon in `name:` and use the model aliases `sonnet`, `opus`, and `haiku`.
- The agents read `docs/frameworks.md` from the plugin folder.
- New tests for the skill files, the script command lines, the script headers, the agent files, and the version.
- The README, the ADR, and the diagram are written again in ASD-STE100.

## 0.1.0

- The version before the port.
