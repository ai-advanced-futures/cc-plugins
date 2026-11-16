# The deep-walk evaluation

The legacy evaluation checks `knowledge:ponder` and the brain shortcuts.
A brain that falls back to local `knowledge:ask` no longer produces walk state;
that result is unmeasured here. Use `../evals/` to compare ask and ponder.

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

## The local search (`/knowledge:ask`)

`kq_fixture.py` builds a synthetic graph of 12 pages, and `kq-questions.yaml`
holds 6 questions for it. Each name, date and number is invented.

Tests with no model call (the search, the walk, the grant of the skill, and
that the script writes no file in the project):

```bash
cd plugins/knowledge && pytest tests/test_kq.py -q
```

One live run, from the repository root. It starts a paid Sonnet session:

```bash
python3 plugins/knowledge/eval/kq_fixture.py /tmp/kq-garden
cd /tmp/kq-garden
claude -p "/knowledge:ask Who pays for the repair of the east fence?" \
  --plugin-dir <repo>/plugins/knowledge --model sonnet
```

A right answer states each `key` text of the question in `kq-questions.yaml`
and conflicts with none of them. The `context` texts are the facts of other
pages that a good answer also gives. The graph is small, so each run finds
the answer page: this run tests that the skill works, not how well it finds
a page in a large graph.
