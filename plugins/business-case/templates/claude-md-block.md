## Business cases

The business cases of this repository are the graph `{{DIR}}/` (graph name
`business-case` in `.claude/knowledge.json`). Each case has its records in a
case folder, `business-cases/<slug>/`, and the pages are a copy of them.

- Run `/business-case:ask <question>` for questions such as "what does the
  price part of case X say" and "which evidence does the forecast rest on".
- Run `/business-case:build` to make or change a case. Run
  `/business-case:learn` to confirm the pages of a case.
- Write pages only through `bc_graph.py`. Do not edit the generated files:
  each `index.md`, each `LINKS` block, and `links.tsv`, because the next
  regeneration overwrites a hand edit. Do not edit a page of a case, because
  the next `publish` writes the values of the case folder over it.
