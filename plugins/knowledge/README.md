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
- `/knowledge:ponder <question>`: search local graphs, then inspect nearby linked
  pages with one Sonnet reader. Return an answer, cited sources, and 8-10 short
  relevant context facts when available. Quote evidence for unknown or disputed facts.
- `/knowledge:forget <graph>:/<path>`: remove a page and each reference to
  it, after one yes.
- `knowledge:checking` (hidden): run the brain check and the general check
  after a write.

## Choose a reader

Both readers use `kq.py find` and `kq.py near`: one search before the reader
starts, up to two further searches, and one link search when results contain
pages. `ponder` uses the saved reference's search-then-walk approach with safe
search inputs and source citations. Its prompt asks for more relevant context
and stronger evidence for unknown or disputed facts, not a larger search budget.
`ask` retrieval is unchanged.

Both commands search local graphs only and report excluded remote graphs.
Neither applies caller-supplied start nodes or neighbor filters. `ponder` stops
when a request requires these unsupported features; `ask` ignores caller walk
hints. Neither uses the former page-by-page walker as a fallback. An excluded
remote graph is not evidence that the remote graph has no answer.

Both readers cite pages and leave graph files unchanged. Saving an answer is a
separate, user-approved `knowledge:learn` action. Existing brain callers stay
unchanged; their start nodes and neighbor filters do not apply to the local
search. A separate audit covers those callers.

The shared `knowledge.py walk` API and `knowledge:neighbor-judge` agent remain
available for direct callers. Neither `ask` nor `ponder` uses that page-by-page
procedure.

## Evaluations

The committed [synthetic datasets](evals/README.md) contain 50, 120, and 340
content pages. Use the small set for command checks and the medium set for
tuning. The large set runs only with an explicit benchmark refresh.
See [Run knowledge benchmarks](evals/RUNNING.md) for model checks, measurements,
and commands. Ordinary tests start no model sessions.

### Benchmark results

Start with the [plain-language benchmark summary](BENCHMARKS.md) for the current
comparison and the separate historical page-by-page results.

Measured on 15-16 November 2026 (UTC): 340 synthetic content pages, 60 fixed
questions, and three fresh answer sessions per question for each reader. The full
run contains 540 valid results, including the frozen draft reference. Here,
`ponder` means the replacement `search-then-walk-3`, not the former page-by-page reader.

| Command | Mean seconds | Accuracy | Facts | Context | Tool calls | Model turns | Agents | Tokens | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ask` | 8.36 | 96.7% | 98.5% | 92.2% | 0.9 | 1.9 | 1.0 | 39,581 | $0.0576 |
| `ponder` | 10.49 | 96.1% | 98.1% | 93.5% | 1.4 | 2.4 | 1.0 | 55,135 | $0.0681 |

Ponder returned 1.3 percentage points more expected context, but 0.6 points lower
accuracy, at about 25.5% more time and 18.3% more answer cost. Ask remains the
faster, cheaper default; this run does not establish an accuracy gain from ponder.
The frozen reference took 10.05 seconds, with 95.6% accuracy and 95.1% context.
Its earlier accuracy advantage did not repeat.

Each value is a mean over 180 answers. Accuracy requires all required facts and no
conflicting answer. Facts and context are mean per-answer shares. Tool calls exclude
the scripted pre-model search; 28 ask answers used that search alone. Model turns
include child agents. The agents column counts child starts. Tokens include input,
output, cache reads, and cache writes.

All answers served `claude-sonnet-5-5`. Three separate `claude-opus-5-5` judges
graded each answer. Time comes from checked CLI 2.1.325 session records, excluding
setup and grading. Cost is the CLI list-price estimate, not verified billing.
Mean grading cost was $0.0621 for ask and $0.0642 for ponder, separate from the table.

All 540 measurements matched their retained records in the audit. The full run
had no recorded execution or grading errors, runner retries, replacement batches,
or child refusals. Preliminary smoke/checker corrections are disclosed in the
[full report](evals/BENCHMARK.md), along with audit limits and token counts.

The same 60 synthetic questions were reused, and earlier aggregate results informed
the choice of ponder. This is not a fresh held-out validation or a statistical
significance claim. Provider load and caching were not controlled. The
[14 November report](evals/BENCHMARK-2026-11-14.md) preserves the old measurements;
its different CLI and implementation prevent a clean historical speed comparison.

## The standard

`standard/brain-standard.md` holds the rules of every brain: the bundle, the
page, the schema, the links, the manifest, the skills, the save code, the
checks, the reports, `forget`, and writes to a remote graph.

`docs/brain-studio.md` names the plugins that people use to build brains (the Brain Studio), and shows how their work reaches the next plugin and `sofa`.

## Scripts

| Script | Use |
|---|---|
| `scripts/knowledge.py` | `registry`, `fetch`, `resolve`, `show`, `neighbors`, `pages`, `walk`, `check`, `brain-root`, `brain-check`, `forget-plan`, `remote-checkout`, `remote-publish`. |
| `scripts/knowledge_graph.py` | The save code of the generic graph: `init`, `upgrade`, `move`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, `log`. `body KEY --file PATH [--append]` writes the text of a page above its `LINKS` block (`--file -` reads standard input). `link` adds a `sources` entry with `id`, `resource`, `title`, and `last_modified`, read from the target. `new --slug SLUG` names the page file. A Source page with a `raw/` resource takes the base name of its raw file. |
| `scripts/kq.py` | The local search of `/knowledge:ask` and `/knowledge:ponder`: `find` (rank the passages, print the 8 best pages) and `near` (rank linked pages near the answer pages). Standard library only: run it with `python3`. `scripts/kq.json` holds its settings. |
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
