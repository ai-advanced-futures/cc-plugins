# Changelog

## 2.1.0

This version ports the plugin to this marketplace.

- Script calls now work. Each of the 8 scripts has a command line, and agents and skills run them as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. Each script lists its Python needs in a PEP 723 block.
- New skill `partnerships`. It runs all six phases. It takes the product context from your words, asks for the missing facts, makes the session, starts the orchestrator, and shows the go or no-go result.
- The six phase skills are now `partnerships-assess`, `partnerships-discover`, `partnerships-structure`, `partnerships-architect`, `partnerships-monetize`, and `partnerships-recommend`. Each skill name is the name of its folder.
- Only skills ask questions, because a subagent cannot ask. The agents take the product context from their dispatch and ask nothing.
- Agents start other agents with the `Agent` tool and the full name `strategic-partnerships:<agent>`.
- Each agent has a `description`, a model alias, and only the tools that it needs.
- Each phase agent reads its framework text from the plugin file `frameworks.md` with a clear instruction.
- The Apollo step works when you add an Apollo server named `apollo`. Without the server, the plugin writes a notice and the run goes on.
- The cleanup of old sessions is now `session_manager.py --sweep`. It checks only folders in `.sp-tmp/`. It keeps a complete session.
- A session id must be a plain name: 1 to 64 characters of letters, digits, `.`, `_` and `-`, and not `.` or `..`. A script refuses any other `--session-id` with exit code 2, so no script can read or write outside `.sp-tmp/`.
- A second run of a phase skill gives a new result. The skill always starts the phase agent, and the agent writes its phase file again, also when the file exists.
- The sixth phase follows the same rule: `partnerships-recommend` always starts the synthesizer, and the synthesizer writes `synthesize.md` again.
- When a script refuses the session id (exit code 2), each phase skill and the orchestrator stop: they start no agent and read no file. The skills run the check before they read `assess.md`.
- The skill `partnerships` and the orchestrator start agents in the foreground, and the skill ends its turn only after the orchestrator returns its last line. A run with `claude -p` no longer stops while the orchestrator works.
- The contract with a pipeline plugin of the source repository, and its handoff file, are removed.
- Tests run in CI with no skips.

Versions up to 2.0.0 came before the port. They come from commit `c2a329f` of a private repository.
