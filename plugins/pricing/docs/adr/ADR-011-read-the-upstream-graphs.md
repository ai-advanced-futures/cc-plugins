# ADR-011: Read the upstream graphs

**Status:** Accepted
**Date:** 2026-11-06
**Decides:** how `pricing` reads the data of `jtbd-market-discovery` and `competitive-intelligence`
**Related:** ADR-010 (the plugin result file)

---

## Context

`jtbd-market-discovery` and `competitive-intelligence` now write a knowledge graph (a set of pages in a bundle) at the end of each run. They no longer write the files that `pricing` used to read. A reader of a graph must not read the page files itself, because the page layout is the business of the writer.

## Decision

1. **One script reads the graphs.** `scripts/brain_read.py` has the operations `wtp`, `outcomes`, `moats` and `status`. A prompt file runs only this script. No prompt file names a path in the folder of another plugin.

2. **The script reads through the save script of the writer.** It finds the plugin with `scripts/probe-plugin.sh` (a byte copy of the file in the other plugins), runs `jtbd_graph.py` or `ci_graph.py` with `--root <git root>`, and reads the JSON that it prints. It reads no page file. It starts the probe from the folder of the `pricing` plugin and gives it that folder as the project folder, so a planted module in the project does not run, and the probe skips the candidate `<project>/.claude/plugins/<name>`: the save script of a project that was just opened never runs with no prompt. So a writer plugin that is installed only in `<project>/.claude/plugins/<name>` is not found: the reader gives `no-plugin`. Pricing finds a writer plugin as a sibling folder, in the home install, or in the plugin cache.

3. **The interpreter.** `PRICING_GRAPH_PYTHON` first, then `uv run --quiet`, then `python3`. `status` adds `--offline`, so the session-start hook never fetches a package.

4. **No graph is a plain message.** Each operation prints `found: false`, a `cause` word and a `why` text, and exits 0. The prompt shows the `why` and goes on with no input (Path B, or no moat context).

5. **The newest run that holds the data.** `wtp`, `outcomes` and `moats` read `pages Run`, sort by `finished_at` (newest first), and stop at the first run that holds the data. A plugin run names its run: `wtp --run-id R --case C` reads that run only, and refuses a run that is not there or that exists twice.

6. **A price cites a file.** In a person's run, `wtp --out <run folder>/upstream` writes the printed result of the run as a result file (named by `result_name.py`), and the price cites that file. Each `cites.file` in it points to the file of the cited run. The script writes only under `.pricing/`.

7. **The hook prints a note only for usable data.** `status` reads the graph names in `.claude/knowledge.json`, then checks the data with a 7 s limit. It prints no file name and no page path.

8. **The old output files are not read.** The files that the writer plugins wrote before the graphs are no longer a source. A person with only such files gets Path B and the plain message.

## Consequences

- A change of the output of `results` or `pages` in a writer plugin can break `brain_read.py`. The test `test_graph_inputs.py` builds real graphs with the save scripts of the sibling plugins, and the CI job of `pricing` runs when one of them changes.
- The `scripts/probe-plugin.sh` copy is one more copy to keep equal (`test_probe_copy.py`, and the knowledge release test).
- A person must have the writer plugin installed to use Path A with real data.

## Rejected

- **Read the page files in `pricing`.** The page layout would become a second contract between two plugins.
- **Cite a graph page in `cites.file`.** `business-case` opens each cited path as a result file.
- **A hook that only says "the graph is set up".** It would announce a graph with no willingness to pay.
