# The legacy page-by-page evaluation

This historical harness scores page-by-page walk state and brain shortcuts.
It does not measure the local single-reader `knowledge:ask` or the replacement
`knowledge:ponder`: neither command produces its walk state. Do not use a
missing-state result as an accuracy or traversal result for either command.
Execution of `run_ask_eval.py` is disabled: its command exits 2 before any model
starts. Historical scoring functions and verdicts remain available for tests.
Use the [benchmark run guide](../evals/RUNNING.md) to compare the active readers.

The historical evaluation used headless Claude Code sessions with a live Haiku
judgment for each walk step (A19). Pytest tests its scoring code with fixed inputs
and starts no model.

Its historical pass rule required an answer that cited each expected page and
a walk that read fewer than half the graph pages. A question passed when 2 of
its 3 runs passed. These rules do not define a pass for either local reader.
The 14 November 2026 benchmark's `ponder` results refer to `page-by-page-1`, not
the replacement `search-then-walk-3`. A fresh benchmark for the replacement is
approved but has not run.

## The runtime check of each plugin

Load all five plugins in one headless session and run the setup skills on a
fresh repository (the `verifying-plugin-runtime` skill):

```bash
$ mkdir /tmp/kg-runtime && cd /tmp/kg-runtime && git init -q
$ claude -p "/knowledge:setup" --plugin-dir <repo>/plugins/knowledge --plugin-dir <repo>/plugins/system-design \
  --plugin-dir <repo>/plugins/product --plugin-dir <repo>/plugins/business-domain --plugin-dir <repo>/plugins/architecture
```

Then run `/system-design:setup`, `/product:setup`, `/business-domain:setup`, and `/architecture:setup`
the same way, and `uv run <repo>/plugins/knowledge/scripts/knowledge.py check`.
Each setup must end with `CHECKS: PASSED`, and the last check must print
`0 errors`. The session must load each plugin with its dependency on
`knowledge` (`"dependencies": ["knowledge"]`).

## The local reader checks

`kq_fixture.py` builds a synthetic graph of 12 pages, and `kq-questions.yaml`
holds 6 questions for it. Each name, date and number is invented.

Check local search, linked-page retrieval, permission rules, and the `ponder`
prompt without model calls:

```bash
$ cd plugins/knowledge && pytest tests/test_kq.py tests/test_skill_ponder.py -q
```

One live run, from the repository root. It starts a paid Sonnet session:

```bash
$ python3 plugins/knowledge/eval/kq_fixture.py /tmp/kq-garden
$ cd /tmp/kq-garden
$ claude -p "/knowledge:ask Who pays for the repair of the east fence?" \
  --plugin-dir <repo>/plugins/knowledge --model sonnet
```

A right answer states each `key` text of the question in `kq-questions.yaml`
and conflicts with none of them. The `context` texts are the facts of other
pages that a good answer also gives. The graph is small, so each run finds
the answer page: this run tests that the skill works, not how well it finds
a page in a large graph.
