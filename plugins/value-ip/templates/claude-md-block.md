## Value and IP

The value and IP findings of this repository are the graph `{{DIR}}/` (graph name
`value-ip` in `.claude/knowledge.json`). Each run of `/value-ip:analyze` writes a
result file to `.value-ip/results/`, and `/value-ip:learn` turns that file into pages:
one Run, the Differentiators that survived the debate, the Verdict and the Gaps.

- Run `/value-ip:ask <question>` for questions such as "which differentiators
  survived the debate" and "what did the latest verdict say".
- Run `/value-ip:analyze` to make a result file. Run `/value-ip:learn` to save it in
  the graph and to confirm its pages.
- Write pages only through `vip_graph.py`. Do not edit the generated files:
  each `index.md`, each `LINKS` block, and `links.tsv`, because the next
  regeneration overwrites a hand edit. Each page is the judgement of the model, so
  call no page validated until a person confirms it.
