## System design

The architecture of this repository is the graph `{{DIR}}/` (graph name
`system-design` in `.claude/knowledge.json`).

- Run `/system-design:ask <question>` for questions such as "which component
  realizes capability X" and "which scenarios constrain this component".
- Run `/system-design:learn [area]` to decide the open parts of the design.
- Write pages only through `system_design.py`. Do not edit the generated
  files: each `index.md`, each `LINKS` block, the blocks of `system.md`, and
  `links.tsv`, because the next regeneration overwrites a hand edit.
