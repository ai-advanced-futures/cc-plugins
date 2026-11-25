# ADR-003: Save the result of each run as an OKF graph

**Status:** Accepted
**Date:** 2026-11-25
**Plugin:** value-ip v1.4.0

---

## Context

`value-ip:analyze` writes one result file to `.value-ip/results/` (ADR-002). The file is complete for one run,
but a later session cannot search across runs, cannot follow a differentiator to the run that found it, and
cannot tell which results a person read and agreed with. The sibling plugins `jtbd-market-discovery`,
`competitive-intelligence`, `business-case` and `ux-hci-design` keep their results as graphs that follow the
brain standard of the `knowledge` plugin (`plugins/knowledge/standard/brain-standard.md`), so `/knowledge:ask`
and the other plugins read them with one reader.

Two options were open: a full brain, or a result file that `knowledge:learn` can ingest into the generic graph.

## Decision

1. **A full brain.** The plugin has one save script, `scripts/vip_graph.py`, with the operations of section 8 of the
   standard, a LinkML schema with a generated JSON Schema, a brain check, the PostToolUse hook, the skills
   `setup`, `learn` and `ask`, and `knowledge` as its only dependency. The result is a graph a reader finds without
   knowing value-ip. A generic ingest would give pages with no typed edge, no `grade` and no rule that stops a
   page from being called validated.
2. **The result file stays the record.** The graph is a copy that `ingest` makes from the file. The analyze run,
   the runner and the synthesizer do not change, and no coach or consumer that reads the file breaks.
3. **Four page types.** `Run` (one result file, its identity), `Differentiator` (one `differentiator` result),
   `Verdict` (the `right_to_win` result, with the recommendation and the mean score when the text states them) and
   `Gap` (one gap). Each page except the Run page has the required edge `run`. The result file's `sources`,
   `method`, `defaults` and `rests_on_default` are fields of the page, so the provenance is not lost.
4. **Grade.** `grade` has one value, `model`: a result of the debate is a judgement of the model. `ingest` refuses
   a result with no `model` source. A page is never called validated by the code.
5. **Human confirmation.** `ingest` writes `draft` pages through the save script, after the person answers "Learn
   these results?". `verify-run --by human:<login>` is the only way to `stable`, and rule `VIP-verified` fails a
   `stable` page with no `verified` entry of a person. A second confirmation adds an entry.
6. **Identity.** A Run page is identified by `result_file`. `ingest` refuses a file that is already in the graph,
   and rule `VIP-run` fails two Run pages with the same file. No run is overwritten.
7. **Nothing guessed.** A verdict value that does not start with PASS, CONDITIONAL or FAIL gets no
   `recommendation`, and a method with no "mean N of 5" gets no `mean_score`.
8. **Known brain.** `knowledgelib/probe.py` of the knowledge plugin lists the pair `("value-ip", "scripts/vip_graph.py")`,
   as for each other brain.

## Consequences

- A consumer reads a run with `vip_graph.py results`, or searches with `/knowledge:ask`. The file path stays valid.
- The plugin now needs `uv` and `knowledge` to save a graph. `analyze`, `challenge` and `guard` need neither.
- The graph holds results of each run. A repeated run of the same artifact makes new pages: the graph has no
  merge of differentiators across runs, because the debate gives no identity to a claim.
