## Competitive intelligence

The competitive intelligence of this repository is the graph `{{DIR}}/` (graph
name `competitive-intelligence` in `.claude/knowledge.json`).

- Run `/competitive-intelligence:ask <question>` for questions such as "which
  competitors does the market have" and "what did the latest run find".
- Run `/competitive-intelligence:discover` or `/competitive-intelligence:analyze`
  to make new pages. Run `/competitive-intelligence:learn` to confirm the
  pages of a run.
- Write pages only through `ci_graph.py`. Do not edit the generated files:
  each `index.md`, each `LINKS` block, and `links.tsv`, because the next
  regeneration overwrites a hand edit.
