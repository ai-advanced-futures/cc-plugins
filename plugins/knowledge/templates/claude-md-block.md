## Knowledge graph

The generic knowledge graph of this repository is `{{CONTAINER}}bundle/`.
[AGENTS.md](./{{CONTAINER}}AGENTS.md) holds its rules.

- Run `/knowledge:ask <question>` to ask a question. It reads each graph in
  `.claude/knowledge.json`, one step at a time.
- Run `/knowledge:learn <path or URL>` to add a source or an answer.
- Run `/knowledge:forget <graph>:/<path>` to remove a page and each reference
  to it.

Do not edit the generated files: each `index.md`, each `LINKS` block, and
`links.tsv`. Write pages only through `knowledge_graph.py`.
