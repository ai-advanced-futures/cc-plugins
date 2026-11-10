# ADR-004: Keep the output of a run as the jtbd knowledge graph

**Status:** Accepted
**Date:** 2026-11-06
**Decision:** D-050
**Adopts:** the brain standard of the `knowledge` plugin, `plugins/knowledge/standard/brain-standard.md`

---

## Context

Each run of this plugin wrote files into `.jtbd-market-discovery/` and into a session folder. The next run overwrote the files at the root, and no tool could ask a question across runs, such as "which outcomes are most underserved" or "what will this segment pay". Other plugins (`pricing`, `gtm`, `business-case`, `product-finance`) read single files by name.

The `knowledge` plugin has a standard for a brain: a folder of pages, a schema, one script that writes the pages, a check, and a hook that runs the check after each write. `system-design`, `architecture`, `business-domain` and `product` follow it.

## Decision

1. **One graph.** The graph is named `jtbd`. Its folder is `docs/jtbd/`. `.claude/knowledge.json` lists it. The first `write-run` makes the graph when the project has none.

2. **Seven page types.** `Run` (RUN), `Job` (JOB), `JobStep` (STEP), `Outcome` (OUTCOME), `Segment` (SEGMENT), `WtpValidation` (WTP) and `Result` (RESULT). Each page except `Run` has a `run` link to its run. A later run adds a new tree of pages and changes no page of an earlier run.

3. **One writer.** `scripts/jtbd_graph.py` is the only code that writes a page. Its operations are the standard ones (`init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, `log`) and four more:
   - `write-run` writes all pages of one run from the session folder and the result file. It writes `status: draft` and `generated.by`.
   - `verify-run` is for a person. It sets `status: stable` and one `verified` entry on the `Run` page and on each page of the run.
   - `results` prints the `Result` pages of one run in the shape of a result file.
   - `pages` prints the pages of one type.

4. **Result pages.** One `Result` page holds one entry of a result file. A fact lives in one place: the `Outcome`, `WtpValidation` and `Job` pages do not repeat a value of their `Result` page (check rule `J-once`). `results` prints the entries again, so a reader gets the same shape as before.

5. **Kept files.** Four files stay beside the graph, because other plugins read them by name: `customer-needs.json`, `opportunity-scores.json`, `evc-analysis.json` and `wtp-validation.json` in `.jtbd-market-discovery/`. The result files stay in the `results/` folder. The four other root files (`job-statement.json`, `job-steps.json`, `customer-segments.json`, `final-output.json`) are not written there any more, because no reader reads them. The last reader story removes the kept files. 2026-11 (STORY-113, D-056): the result file is `result.json` in the session folder, and no file stays beside the graph.

6. **Hook and skills.** A hook runs `regen`, the brain check and the general check after each write. The skills `setup`, `ask` and `learn` are the entry points. `learn` is the only skill that confirms a run.

7. **A person confirms.** A run writes only `draft` pages. A person says "Learn these results?" at the end of a `discover` or `wtp-check` run, and `learn` runs `verify-run`. The command sets `generated.by` of each page to the person, so a confirmed page no longer names the plugin version. An automated run asks nothing and its pages stay `draft`.

## Consequences

- A person or an agent can ask a question across runs with `/jtbd-market-discovery:ask`.
- The plugin needs the `knowledge` plugin and `uv`. `scripts/probe-plugin.sh` finds the plugin. Without `uv`, the hook runs the steps with `python3`.
- Two copies of a file are the same bytes as in other plugins: `scripts/probe-plugin.sh` and `scripts/claude_md_router.py`. A test of the `knowledge` plugin compares them.
- A kept file and a page hold the same value until the reader stories merge. `write-run` writes both from the same files, and a test pins that `results` prints the result file again.
- A run that fails in `write-run` ends with the line `GRAPH: FAILED <exit code> <first error line>`. The kept files and the result file exist, so no reader loses its input.
