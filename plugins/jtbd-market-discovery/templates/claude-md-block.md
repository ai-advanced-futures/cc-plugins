## Jobs to be done

The results of the market discovery runs of this repository are the graph
`{{DIR}}/` (graph name `jtbd` in `.claude/knowledge.json`).

- Run `/jtbd-market-discovery:ask <question>` for questions such as "which
  outcomes are most underserved" and "what will segment S pay".
- Run `/jtbd-market-discovery:learn` to confirm the pages of a run.
- Write pages only through `jtbd_graph.py`. Do not edit the generated files:
  each `index.md`, each `LINKS` block, and `links.tsv`, because the next
  regeneration overwrites a hand edit.
