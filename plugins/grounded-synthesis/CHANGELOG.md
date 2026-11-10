# Changelog

## 0.4.7

- `lib/session_paths.py --resolve` with no session id makes a new uuid4 and the session folder, and prints the lines `session_id: <uuid4>` and `session_dir: <path>`. Step 1 of the orchestrator calls this form, so the agent runs no shell command to make a uuid. Before, the permission check refused the first command of the agent in 3 of 3 audit runs with only `Bash(uv run:*)` (STORY-191). `--resolve <session_id>` does not change.
- The orchestrator text says to run each shell command on its own, with no `$(...)`, variable, pipe, `&&` or `;`, and to write each value in full. A test reads each command block of the agent.
- The README names the grants of a headless run: `Bash(uv run:*)`, `Write` and `Read`.

## 0.4.6

- Step 2 of the skill `grounded-synthesis-audit` starts the orchestrator in the foreground, with `run_in_background: false`, and waits for its reply. Before, the `Agent` call often had no `run_in_background` key, and the harness then started the orchestrator in the background (4 of 10 live runs). A background agent cannot ask for a permission, so a Bash call outside the grant of the skill was refused and the audit stopped (STORY-239).

## 0.4.5

- The fact count is a ceiling. The fact extractor writes at most the target count (12 by default, bounded [8, 20]), and fewer when the source holds fewer. A fact file can have 0 facts when `extraction_notes` gives the reason. The audit skips such a source with the warning `the source holds no fact`, so the status is `partial`; when no source holds a fact, the audit fails with `no source holds a fact`. A statement about the source itself (its length, its form, what it does not contain) is not a fact. Before, the extractor wrote such statements to get to 8 or 12 facts, and no draft could keep them (STORY-218).

## 0.4.4

- The last line of an audit gives the counts of the gap report. `lib/gap_report.py` prints it from the `summary` of `handoff.json`, so the line and the file give the same counts. A count of 1 is singular ("1 source"). The line names the sources not analyzed when there is one.
- The orchestrator ends with that line, with no change. It takes no count from the answer of a sub-agent.
- The coverage-checker returns `Wrote source-{i}-coverage.json` with no count.

## 0.4.3

- The gap report names each source with no fact file or no coverage file (in `## Sources not analyzed`) and each fact with no verdict (in the new `## Facts with no verdict`). The status is then `partial`, not `ok`.
- `summary.facts_checked` counts the facts with no verdict.
- The orchestrator clamps `key_facts_per_source` at Step 1 and writes it into `session.json`. `invocation.key_facts_per_source` of the handoff holds the clamped value of the run, not always 12.

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
