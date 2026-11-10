# Changelog

## 0.3.3

- The 5 skills grant the read of `docs/intake.md` and `docs/frameworks.md` of the plugin, and the write of `.data-strategy-tmp/**`. Before, the skills ran only in a permission mode that asks for no approval: in the default mode, the read of a plugin file and the write of a session file were refused, and a skill such as `strategy` started no agent (STORY-330).
- `session_manager.py` has the command `keep-prev <output_dir> <file...>`. It renames each file that exists to `<name>.prev.md`, and replaces an old `.prev.md` file. It works only in a folder of `.data-strategy-tmp`. The skill `roadmap` uses it, so that the skill needs no `mv`.
- `/data-strategy:roadmap` with a `synthesis.md` path now writes the 3 deliverables in a new folder, `.data-strategy-tmp/<new id>/`. Before, it wrote them in the folder of the `synthesis.md` file.

## 0.3.2

- The skills `strategy`, `platform`, `products`, `roadmap` and `data-strategy` start each agent in the foreground with `run_in_background: false`, and say so in a line at the top. Before, an agent could start in the background and return in a new turn that did not have the `allowed-tools` of the skill, and the next script was refused (STORY-312).

## 0.3.1

- Each skill names each script that it runs in its Bash grant (`scripts/<file> *`). Before, the grant `scripts/*` also permitted `uv run` of a file outside the scripts folder through a path with `..`, also a file of the project (STORY-283).

## 0.3.0

- No agent has `Bash`, `Agent`, `WebSearch`, or `Glob`. The agents have `Read`, `Write`, and `Grep`, and `deliverable-generator` has `Read` and `Write`.
- The agent `orchestrator` is removed. The skill `data-strategy` runs the scripts and starts the 5 agents in the main conversation, one at a time, each in the foreground. The line `DONE: data-strategy` is removed.
- `product-analyst` and `synthesizer` take the field `step` with the values `inputs` and `report`. With `inputs`, the agent writes the input file of a script. The skill runs the script. With `report`, the agent reads the result file and writes the report.
- `strategy-assessor` and `platform-auditor` read the result files that the skill writes (`dama_result.json`, `gartner_result.json`, `mesh_result.json`). The agents write no `.done` flag. The skill writes the flags.
- The 5 scoring scripts take `--out <output.json>`. With the option, a script writes its result to the file and prints one line. After an error, a script writes no file.
- `session_manager.py` has the command `new <parent_dir> <domain...>`. It makes the session id and the session, and prints the id. The skills no longer run inline code.
- Each skill says to run every command on its own, with no heredoc, no `; echo`, and no loop.
- The skill `roadmap` tests the `output_dir` (`[A-Za-z0-9._/-]{1,100}`, no `..` part) before it builds a command line with it.
- The agents find the markers of a framework slice with the Grep tool, and not with `grep -n`.
- The skills have `allowed-tools` for the scripts that they run, and a path in a `uv run` line is in single quotes.
- The project scan lists file names with `find` through the Bash tool of the skill.
- New test `tests/test_agent_grants.py`: it fails when an agent has a wide tool grant.

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
