# Knowledge evaluations

This folder uses the [Claude Code plugin eval format](https://code.claude.com/docs/en/plugin-evals).
The data is invented. The case files and graders stay outside the workspace that the model reads.

## Pilot

`pilot/fee-correction` checks the evaluation setup on the 12-page garden fixture in
`../eval/kq_fixture.py`. It calls the `knowledge:ask` skill. It does not measure
search quality on a large graph, and it is not a published benchmark.

The question is: "How much does a member pay to rent a bed for a season?"
The graph states that the fee is 40 florins. A July notice corrects an earlier report that
said 45 florins. The corrected income is not recorded.

The case has four independent model graders:

- `accuracy`: the answer gives the current fee, with no conflicting current fee.
- `fact-01-current-fee`: the answer gives 40 florins per plot per season.
- `context-01-correction`: the answer gives the correction, both values, and the notice date.
- `context-02-income`: the answer says that the corrected income is not recorded.

The graders accept equivalent wording. The pilot uses native CLI grading with three judge
votes for each grader. The CLI's combined score is not the accuracy metric: it mixes answer
and context checks. Historical pilot scores remain native scores, not checked grades.

Print the command without starting a model, from the repository root:

```bash
$ python3 plugins/knowledge/evals/run_pilot.py
```

Start one live case, with one answer and model grading:

```bash
$ python3 plugins/knowledge/evals/run_pilot.py --run --output plugins/knowledge/evals/results/pilot-01
```

Use a different output folder for each attempt. The runner refuses to overwrite a folder.
The runner uses the Sonnet alias for the answering session and the Opus alias for grading.
Record the resolved model IDs before comparing results. `--allow-tools Bash` permits shell
calls inside the evaluation sandbox; this is not a test of the skill's permission grant.

The fixture needs `uv` and Python 3.12. Its script runs outside the evaluation sandbox and
installs the two pinned Python dependencies in the uv cache. It builds only an invented graph in the empty
workspace. The model cannot read the case definitions from `evals/`.

The native CLI keeps its report local. Raw reports and temporary paths belong in the ignored
`results/` folder, not in the public release. A report can contain local paths and session IDs.

## Read measurements

Extract a report and check the served model ID:

```bash
$ python3 plugins/knowledge/evals/metrics.py plugins/knowledge/evals/results/pilot-02/aggregate-result.json --expected-model claude-sonnet-5-5
```

The command exits 1 when an attempt is incomplete or its model does not match. It reads
`modelUsage` for token totals, because parent-session usage can omit a fork's tokens.
`transcripts.json` points to copies of the native trace and the main and subagent session
records kept beside the results. The native report remains unchanged. A missing or incomplete
record produces unavailable measurements, not zeros. Older pilot results with `trace-map.json`
remain readable, but that map alone cannot provide complete subagent turn counts.

The pilot on 2026-11-13, with Claude Code 2.1.323, passed all four graders, each with three
PASS votes. It recorded 27.801 seconds for the answer, 6,373 input tokens, 369 output tokens,
and 7,296 cache-read tokens. The CLI recorded $0.044738 for the answer and $0.029440 for
grading. The complete attempt, including setup and grading, took 70 seconds.

**This is not a Sonnet benchmark.** The command requested `sonnet`, but the trace reported
`gpt-6.1-terra`. The session environment mapped the Sonnet alias to that model. Its cost basis
was `unknown`, so these dollar values are CLI estimates, not verified billing. The parent
reported zero turns, and the native trace omitted the reader's final model message. The full
subagent record supplied the missing message: two model turns, one model-issued tool call,
and one subagent start. The initial scripted search is separate. With those records, the
measurement check rejects the run only when it is labeled as a Sonnet measurement. It can
report the recorded model honestly, but one pilot is not the 340-page benchmark. The first
attempt failed during fixture setup on Python 3.15, before a model ran; it is not scored as
an incorrect answer.

## Checked benchmark grading

The benchmark runner uses native eval for answer generation with only the `answer-present`
regex grader (`\S` on `last_message`). This checks for text, not factual quality. The hidden
`native-case.json` file preserves the original rubric outside the answer workspace.

Published quality uses `checked_grading.py`: three fresh, separate, tool-free Claude sessions
per saved answer. Each session returns structured JSON with a Boolean and a nonempty reason
for every criterion. Two of three valid votes determine each result. Answer plugin sessions
do not use `--safe-mode`; the separate checked judges do.

Each attempt retains the grading request, its SHA-256 hash, raw stdout and stderr, process
results, reasons, timing, and the summary. The reader checks the request against the native
question and answer, and the summary against the raw votes. All three responses must have
valid criteria, Boolean votes, reasons, distinct session IDs, successful CLI results, no
permission denials, and valid cost records. An invalid response is an error, not `false`.
Quality stays unavailable, and the run stops. Grading time and cost stay separate from
answer time and cost.

The benchmark options `--judge-model` and `--expected-judge-model` both default to
`claude-opus-5-5`. Each checked response must report exactly the `--expected-judge-model`
value. This check is separate from `--expected-model`, which checks answer models.

Native controls gave different scores for a known-correct multiline answer and its flat-text
form. The cause is unproven. Before a benchmark, you must run checked positive and negative
controls. Correct answers must pass; missing or conflicting facts must fail. Include both
text forms and keep the raw evidence. The implementation alone does not show that
calibration has passed.

On 2026-11-13, four controls on `smoke-1-q001` passed: the correct multiline answer,
its flat form, an incorrect answer, and an answer with one required fact. All three
`claude-opus-5-5` votes agreed with each expected criterion result. One complete native
`ask` run with checked grading then passed all six criteria. These are grading checks,
not final benchmark results.

## Datasets

The committed graph fixtures and source-backed question sets have these sizes and uses:

| Dataset | Content pages | Questions | Use |
| --- | ---: | ---: | --- |
| `smoke-1` | 50 | 12 | Check the full command path |
| `tuning-1` | 120 | 36 | Compare changes to retrieval |
| `benchmark-1` | 340 | 60 | Refresh the published results only on request |

`build_datasets.py --check` validates the counts, source quotes, graph links, and separation
of questions from the model workspace. It uses only the Python standard library and writes
nothing. Builds use the graph's save code and a fixed clock. See [Run knowledge benchmarks](RUNNING.md)
for planning, diagnostic runs, variant selection, and the explicit benchmark command.

The variant names are `search-then-walk-1` for the draft reference,
`search-then-walk-2` for the revised `ask`, and `page-by-page-1` for `ponder`.
The [README comparison](../README.md#benchmark-results) shows the two shipped commands,
`ask` and `ponder`. The [full benchmark report](BENCHMARK.md) also includes the frozen reference.

The report separates accuracy, required-fact retrieval, and relevant-context retrieval.
It also shows mean time per question, tool calls, model turns, subagent starts, input and
output tokens, cache tokens, and estimated cost. Answer-generation cost and grading cost
are separate. A missing measurement is unavailable, not zero.

A full benchmark needs fixed questions, reviewed source facts, scoring rules, model IDs,
and run counts before it starts. The pilot alone does not meet that requirement.
