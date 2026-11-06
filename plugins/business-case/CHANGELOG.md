# Changelog

## 0.6.0

The port to this marketplace.

- The coach calls `bc.py` with `uv run`. `bc.py` and `schemas/plugin_result_check.py` have a PEP 723 block (Python 3.9 or later, no package).
- The plugin has no text for a tool of the source repository. An automated run takes its values from the arguments: `/business-case:build <proposal> --automated --offering <name> --market <market> [--strategy <path>]`. Code still refuses each decision in an automated run.
- The command has no `name:` key and no `agent:` key. The plugin has no root `SKILL.md` and no `release.json`.
- The plugin map names the versions and the runners of the ported plugins. The two routes of `competitive-intelligence` are skills. `value-ip` is an optional plugin from outside this marketplace.
- The install check finds the plugins of the `cc-plugins` marketplace.
- The manifest has no email and no version number in its description.
- The tests read no file outside the plugin, and none is skipped.
- The prompt files have no finding of the prompt linter. They hold 618 instructions, 72 fewer than before the revision.
- The command gives the runners it starts the grants they need: the scripts of their plugin, the folder of their result files and the answers file of the case (STORY-168). The README lists the grants, and a test checks the list. The result-file grant is an `Edit` rule, because Claude Code checks a file write against the `Edit` rules. The README and ADR-006 state two limits: a `Bash` pattern matches any text, and no grant covers the run folder of a runner.
- The two `session` blocks of the command tell the model to keep the session ID as written. A made-up ID made the review report refuse the judge reply.

Versions 0.1.0 to 0.5.0 came before the port. They are in commit `c2a329f` of a private repository.
