## UX design

The UX design of this repository is the graph `{{DIR}}/` (graph name
`ux-hci-design` in `.claude/knowledge.json`).

- Run `/ux-hci-design:ask <question>` for questions such as "which personas
  does the product have" and "what did the evaluation of screen X find".
- Run `/ux-hci-design:ux-design` to make new pages. Run
  `/ux-hci-design:learn` to confirm the pages of a run.
- Write pages only through `ux_graph.py`. Do not edit the generated files:
  each `index.md`, each `LINKS` block, and `links.tsv`, because the next
  regeneration overwrites a hand edit.
