# ADR-004: Adopt the plugin result file

**Status:** Accepted
**Date:** 2026-10-31
**Amended:** 2026-11-06
**Author:** Luis F. Amadeo
**Plugin:** competitive-intelligence 1.6.0 (amended 1.7.0)

---

## Context

The business-case coach reads what the producer plugins found. Until now, this plugin wrote its own files in its own shape, and a reader could not tell a researched finding from one that the model inferred. The result-file rules fix one shape, the rules R1 to R7, and the invocation block (`plugin-run`) that a coach uses. The checker of these rules is `tests/plugin_result/plugin_result_check.py`, and the tests in `tests/plugin_result/conformance.py` hold this plugin to them. Two skills of this plugin write the file: `discover` and `analyze`.

Four facts of this plugin shaped the adoption:

1. The full-run workflow does not read the steps of `discover` or `analyze`. It runs all six phases. A coach needs a route that runs only the steps of one skill.
2. `discover` runs phases 1 to 3 and `analyze` runs the lenses and the SWOT. Neither reaches Phase 6, the deliverable generator.
3. When research finds nothing, the intelligence gatherer falls back to the inference of the model and marks the finding speculative (`agents/intelligence-gatherer.md`, "Research Pipeline Priority").
4. The plugin folder moved to `.competitive-intelligence/`. This ADR records two decisions that shipped in the same release.

## Decision

1. **Adopt the standard.** `discover` and `analyze` write one result file to `.competitive-intelligence/results/` at the end of every run. This includes a partial run, a halted run, and a run of a person (R1). `result-file.json` names the writer and the defaults registry. `questions/discover.json` and `questions/analyze.json` list the inputs. Each question in the skill carries its `[q: <input>]` id.

2. **The skill is the route.** A coach calls the skill `competitive-intelligence:discover` or `competitive-intelligence:analyze` with the `Skill` tool, in the conversation of the coach. The arguments are the `plugin-run` block, or the path of a file that holds it. The `## Plugin-run block` section of the skill reads the block. In a plugin run, the skill asks the person nothing and shows no checkpoint: it takes each answer from the answers file of the block, and it starts the phase agents itself. A person who runs `/competitive-intelligence:discover` uses the same skill, and the skill asks the questions. No agent of this plugin starts an agent, because a subagent cannot limit the agent types that it starts (D-212, STORY-118).

3. **One writer for both skills.** The `## Result file` section of `agents/deliverable-generator.md` holds the rules for both skills. Each skill reads that section and writes the file, in a plugin run and in a person's run. When the full run dispatches the deliverable generator as Phase 6, the generator writes no result file.

4. **A session for each run.** A coach run uses the session `.competitive-intelligence/<run_id>/`. It reads an earlier session only through `inputs_from`. The `detail` of each result names a file in that session, such as `.competitive-intelligence/acme-0007/intelligence-data.json`. It never names a file at the folder root.

5. **What a result rests on.** The rule maps each entry of the sources of an item by what the entry holds. `user_input` is the `competitors` answer of the person. An entry with a URL is a `published` source. A name with no URL, such as `web_research`, is a `model` source. A result with a `model` source carries the marker `research returned nothing: agent inference`. The evidence of a SWOT item is the text in its parentheses. The website of a competitor is part of its value. It is not a source. The default depth and the default scope mark each discover competitor and alternative. The default purpose marks each analyze result. A run with no market (discover) or no competitor (analyze) halts. It writes the result file with one gap.

6. **The session folder moves.** New sessions go to `.competitive-intelligence/<session>/`. Every reader of an earlier session reads both folders, newest file first. The old folder `.competitive-intel/` is never moved or deleted.

7. **The start-up sweep is deleted.** The sweep was to delete stale sessions at start-up. No tool of that agent could list or delete files, so it never ran. As written, it would also have deleted `monitoring-history/`. No text of this plugin now tells the model to delete a file under either folder.

## Consequences

- A coach can run either skill with answers and read one checked file back.
- A plugin run uses the context of the coach and has each tool of the session of the coach, as a person's run does.
- The build of STORY-118 removes the 2 runner agents `agents/discover-runner.md` and `agents/analyze-runner.md`, and the text that names them.
- The tests in `tests/unit/test_plugin_result_contract.py` hold both skills to the rules through `tests/plugin_result/conformance.py`. The fixtures in `tests/fixtures/plugin-result/` are real result files from test runs.
- `analysis_mode` is not marked as a default. It shapes the framing of the synthesis and the deliverables (`agents/lens-executor.md`), and neither skill runs them.
- Stale unfinished sessions stay in the folder, as they did before, because the sweep never ran.
- A test run has no web search, so every finding in the fixtures rests on the inference of the model. Only an entry with a URL becomes a `published` source. An entry that has a name but no URL, such as `web_research`, stays a `model` source with the inference marker, even in a run that did research.
