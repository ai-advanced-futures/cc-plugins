# Changelog

## 1.7.0

This version ports the plugin to this marketplace.

- The plugin works when you install it. Each question to the person now comes from a skill, because a subagent cannot ask a question.
- New skill `competitive-intelligence`. It runs the full six-phase analysis in the main conversation, and it asks the person at each checkpoint.
- The five commands are gone. Each skill takes the text of the command with the same name.
- The six lens skills moved to `skills/lenses-<name>/SKILL.md`. A lens skill is not a command, and the person cannot start it.
- The lens executor reads each lens skill and follows it, because the `Agent` tool starts an agent and not a skill.
- Each skill and each agent name is now the name of its folder or file. The names have no `competitive-intelligence:` prefix and no `comp-intel` name.
- Each agent has only the tools it needs. No agent has `AskUserQuestion` or `Task`.
- The intelligence gatherer uses its own `WebSearch` and `WebFetch` tools. It can use an MCP research server that the person added. It does not need one.
- Script calls use `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. The scripts `result_name.py` and `vendor_archetype_emitter.py` list their packages in a PEP 723 block.
- The vendor-archetype schema is now in `schemas/`, and the result-file checker is in `tests/plugin_result/`. No file of the plugin reads a path outside the plugin folder.
- The plugin no longer has a link to a dispatcher plugin, a deck output, or a handoff file for other plugins. The result file of `discover` and `analyze` stays.
- Tests run in CI with no skips.
- The version in `plugin.json`, in `scripts/__init__.py` and in the result-file examples is 1.7.0.

Versions 1.0.0 to 1.6.1 came before the port. They come from commit `c2a329f` of a private repository.
