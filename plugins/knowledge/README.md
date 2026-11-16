# Knowledge

The base of every brain. A brain is a plugin that keeps one kind of project
knowledge as a graph: `product`, `business-domain`, `architecture`, `system-design`, and `knowledge`
(the generic graph). Each brain depends on this plugin.

## Skills

- `/knowledge:setup`: make the generic graph, or migrate an old wiki.
- `/knowledge:learn <path | URL>`: add a source or an accepted answer.
- `/knowledge:ask <question>`: search the local graphs in
  `.claude/knowledge.json` with one Sonnet reader (`knowledge:reader-s`).
  Return an answer, source paths, and relevant context.
- `/knowledge:ponder <question>`: follow graph links one page at a time.
  The Haiku agent `knowledge:neighbor-judge` selects the next pages. Use this
  procedure for remote graphs, caller-supplied start nodes or neighbor filters,
  or a question that needs a deeper search.
- `/knowledge:forget <graph>:/<path>`: remove a page and each reference to
  it, after one yes.
- `knowledge:checking` (hidden): run the brain check and the general check
  after a write.

## Choose a reader

`ask` runs one search before the reader starts, up to two further searches,
and one link search when results contain pages. It searches local graphs only.
It reports excluded remote graphs and points to `ponder`; it does not treat a
remote graph's path as a local folder. Both readers cite pages and leave graph
files unchanged. Saving an answer is a separate, user-approved `knowledge:learn`
action.

Version 2.0.0 moves the former `ask` procedure to `ponder` and removes the draft
`ask-fast` command. Existing brain calls to `knowledge:ask` use the local search.
The fast reader does not apply their start nodes or neighbor filters. Those
callers stay unchanged in this release; a separate audit decides which need
the deeper procedure.

## Evaluations

The committed [synthetic datasets](evals/README.md) contain 50, 120, and 340
content pages. Use the small set for command checks and the medium set for
tuning. The large set runs only with an explicit benchmark refresh.
See [Run knowledge benchmarks](evals/RUNNING.md) for model checks, measurements,
and commands. Ordinary tests start no model sessions.

### Benchmark results

Start with the [plain-language benchmark summary](BENCHMARKS.md) for the three
versions, the experiment stages, and what the results do and do not show.

Measured on 14 November 2026: 340 synthetic content pages, 60 fixed questions, and
three fresh answer sessions per question for each reader. The full run contains
540 completed results, including the saved draft reference. This table shows the
two shipped commands. These results describe this dataset, not all real projects.

| Command | Mean seconds | Accuracy | Facts | Context | Tool calls | Model turns | Agents | Tokens | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ask` | 6.65 | 95.0% | 97.5% | 90.8% | 0.8 | 1.8 | 1.0 | 36,363 | $0.0565 |
| `ponder` | 123.31 | 85.6% | 86.8% | 79.2% | 39.0 | 37.2 | 4.7 | 1,416,472 | $0.5016 |

The saved draft reference took 8.11 seconds, with 96.7% accuracy and 95.2% context
retrieval. Revised `ask` was faster, but scored lower than that reference on this set.

Each value is a mean over 180 completed answers. Accuracy requires all required
facts and no conflicting answer. Facts and context are the mean shares of expected
facts returned per answer. Tool calls exclude the scripted search before the model
starts. Model turns include child agents. The agents column counts child starts.
Tokens include input, output, cache reads, and cache writes.

`ask` used `claude-sonnet-5-5`; `ponder` used `claude-sonnet-5-5` and
`claude-haiku-5-5`. Three separate `claude-opus-5-5` judges graded each answer.
Time comes from checked CLI 2.1.323 session records, excluding setup and grading.
Cost is the CLI list-price estimate for the answer, not verified billing. Mean cost
for the accepted grading batch was $0.0626 for `ask` and $0.0642 for `ponder`.

One answer attempt timed out and was retried once with approval. Four grading
batches were replaced after invalid JSON responses: one separately approved batch
and three under a ten-batch limit. All failed records remain retained. The means
use completed answers and accepted grading batches; total cost including incomplete
attempts is unknown. Eleven `ponder` child-agent sessions ended in refusal. Their
responses remain in the counts, and the parent answers were graded as returned.

See the [full benchmark report](evals/BENCHMARK.md) for the reference result,
measurement definitions, and recovery details.

## The standard

`standard/brain-standard.md` holds the rules of every brain: the bundle, the
page, the schema, the links, the manifest, the skills, the save code, the
checks, the reports, `forget`, and writes to a remote graph.

## Scripts

| Script | Use |
|---|---|
| `scripts/knowledge.py` | `registry`, `fetch`, `resolve`, `show`, `neighbors`, `pages`, `walk`, `check`, `brain-root`, `brain-check`, `forget-plan`, `remote-checkout`, `remote-publish`. |
| `scripts/knowledge_graph.py` | The save code of the generic graph: `init`, `upgrade`, `move`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, `log`. `body KEY --file PATH [--append]` writes the text of a page above its `LINKS` block (`--file -` reads standard input). `link` adds a `sources` entry with `id`, `resource`, `title`, and `last_modified`, read from the target. `new --slug SLUG` names the page file. A Source page with a `raw/` resource takes the base name of its raw file. |
| `scripts/kq.py` | The local search of `/knowledge:ask`: `find` (rank the passages, print the 8 best pages) and `near` (the pages that a walk from the answer page comes to). Standard library only: run it with `python3`. `scripts/kq.json` holds its settings. |
| `scripts/probe-plugin.sh` | Find another plugin. It never takes a plugin from the project folder. Each brain has a copy. |
| `scripts/scaffold.py` | Write a new container for `knowledge:setup`. |

Run `knowledge.py` and `knowledge_graph.py` with `uv run`; they need `pyyaml`
and `jsonschema`. Run `kq.py` with `python3`; it needs only the standard library.

`--root` takes the path of the platform. On Windows it also takes the Git Bash form (`/c/x`), the Cygwin form (`/cygdrive/c/x`), and a drive path with `/` or `\` (`C:/x`, `C:\x`).

## The hook

After each change of the knowledge graph, the hook runs
`knowledge_graph.py regen`, then `knowledge_graph.py check`, then
`knowledge.py check --graph knowledge --cache-only`.

The hook runs these steps only when a file of the graph changed. It finds the
changed files in the change list that `knowledge_graph.py` writes
(`<git dir>/knowledge-changed`), and in the file of an `Edit` or a `Write`.
After a command that changed no file, the hook gives no output. When a command leaves no list (for example, `git` failed), the hook checks everything and shows every warning, as it did before the list.

The hook shows each `K-size` and each `K-cite` warning only for a page that
changed. For each of the 2 rules, it shows one line with the count of the
warnings of the other pages, for example
`K-size warnings on pages that did not change: 3.` or
`K-cite warnings on pages that did not change: 3.` Each other `WARN` and `SKIP`
line stays.

`KNOWLEDGE_NO_CHANGE_LIST=1` stops `knowledge_graph.py` from writing the change
list.

## Tests

```bash
$ pip install -r plugins/knowledge/requirements-dev.txt
$ cd plugins/knowledge && pytest tests/ -q -rs
```

For live registration, permission, and caller checks, run this command from
`plugins/knowledge`. It starts Claude sessions and requires an existing Claude
login. It removes model and provider overrides only from child processes; it
changes no saved settings.

```bash
$ make itest TIER=readers
```
