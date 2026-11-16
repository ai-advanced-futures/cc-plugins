## Knowledge graph

The generic knowledge graph of this repository is `{{CONTAINER}}bundle/`.
[AGENTS.md](./{{CONTAINER}}AGENTS.md) holds its rules.

- Run `/knowledge:ask <question>` to ask a question. It searches the local graphs in
  `.claude/knowledge.json` and cites its sources.
- Run `/knowledge:ponder <question>` for fuller context from local graph links.
  Both readers exclude remote graphs and do not apply start nodes or neighbor filters.
- Run `/knowledge:learn <path or URL>` to add a source or an answer.
- Run `/knowledge:forget <graph>:/<path>` to remove a page and each reference
  to it.

Do not edit the generated files: each `index.md`, each `LINKS` block, and
`links.tsv`. Write pages only through `knowledge_graph.py`.
