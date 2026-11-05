# Changelog

## 0.4.2

- The README names the job `grounded-synthesis` of the CI workflow `.github/workflows/ci.yml`. One workflow replaces the workflow file of this plugin. The plugin behavior does not change.

## 0.4.1

This version follows the license rule of the repository: the root Apache-2.0 `LICENSE` covers each plugin.

- The plugin has no `LICENSE` file and `plugin.json` has no `license` key.
- The new file `NOTICE` holds the MIT notice of the source plugin, in the shape of `plugins/business-domain/NOTICE`.

## 0.4.0

This version is the port of the plugin to this repository.

- The agents run each library script as `uv run ${CLAUDE_PLUGIN_ROOT}/lib/<file>.py`. Each script has a PEP 723 header that lists its packages.
- The orchestrator starts the worker agents by their qualified names: `grounded-synthesis:fact-extractor` and `grounded-synthesis:coverage-checker`. It uses the `Agent` tool.
- The skill name is `grounded-synthesis-audit`. The command has no `name` key and no `agent` key.
- The caller contract has five fields (`draft_path`, `source_paths`, `key_facts_per_source`, `output_dir_override`, `output_path`). The three fields of the source caller contract are removed (ADR-007).
- `lib/session_paths.py` has the option `--sweep-days N`. The orchestrator runs it to delete session folders that are older than 30 days.
- The sweep deletes only folders with a uuid4 name, skips symbolic links, and needs `--sweep-days` of 1 or more. The session base must be an absolute path and must not be the root or the home folder. `--resolve` refuses a session id that leaves the base folder.
- The orchestrator puts paths in single quotes in its Bash commands. The Runtime Gate refuses a path that holds a quote, `$(`, or a backtick.
- The pin of `pypdf` is `>=6.21.4,<7.0.0`. Version 6.21.4 has the fix for each advisory that was open on 2026-11-05.
- The tests read no file outside the plugin folder, start no `uv`, and have no skip. The end-to-end test with frozen fixtures always runs.
- The plugin has a workflow, `.github/workflows/grounded-synthesis.yml`.
- The prompt files have no finding of `prompt_lint.py`.

Versions 0.1.0 to 0.3.0 are in the source repository at commit `c2a329f12eb7b21cba1d4096255cd40a75121cb1`.
