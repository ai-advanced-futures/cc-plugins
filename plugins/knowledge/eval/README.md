# The ask evaluation

The evaluation runs in headless Claude Code sessions, not in pytest, because
each step of a walk needs a live Haiku judgment (A19). pytest tests the
scoring code with fixed inputs.

```bash
python3 plugins/knowledge/eval/run_ask_eval.py --runs 3
```

A run passes when the answer cites each expected page and the walk reads
fewer than half the pages of the graphs. A question passes when 2 of its 3
runs pass. The script exits 1 when a question fails.

## The runtime check of each plugin

Load all five plugins in one headless session and run the setup skills on a
fresh repository (the `verifying-plugin-runtime` skill):

```bash
mkdir /tmp/kg-runtime && cd /tmp/kg-runtime && git init -q
claude -p "/knowledge:setup" --plugin-dir <repo>/plugins/knowledge --plugin-dir <repo>/plugins/system-design \
  --plugin-dir <repo>/plugins/product --plugin-dir <repo>/plugins/business-domain --plugin-dir <repo>/plugins/architecture
```

Then run `/system-design:setup`, `/product:setup`, `/business-domain:setup`, and `/architecture:setup`
the same way, and `uv run <repo>/plugins/knowledge/scripts/knowledge.py check`.
Each setup must end with `CHECKS: PASSED`, and the last check must print
`0 errors`. The session must load each plugin with its dependency on
`knowledge` (`"dependencies": ["knowledge"]`).
