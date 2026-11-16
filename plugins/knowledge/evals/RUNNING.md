# Run knowledge benchmarks

Use the small graph to check the command path, the medium graph to tune a variant, and the
large graph only when you request a benchmark refresh. No command in the ordinary pytest
suite starts a model. The runner defaults to a plan with no model calls.

## Datasets and variants

Content-page counts exclude index, manifest, and log files.

| Dataset | Pages | Questions | Purpose |
| --- | ---: | ---: | --- |
| `smoke-1` | 50 | 12 | Check the full command path |
| `tuning-1` | 120 | 36 | Compare retrieval changes |
| `benchmark-1` | 340 | 60 | Produce the published comparison |

Each dataset has a `workspace/` tree and a `questions.json` file. Only `workspace/` goes
into the model's working directory. Questions, expected facts, and graders stay in the
hidden native evaluation folder. Native case files are made for the selected dataset in
an ignored run folder, so an ordinary plugin evaluation does not start the large benchmark.

The larger graphs include public-name entries that link to records under internal equipment
codes. Questions use the public names; the grader knows both names from source-backed mapping
statements. This checks a follow-up search or link walk, rather than only reading the first result.

An offline check on `tuning-1` found that 15 of 36 questions lacked some required or context
facts in the first search. All 15 recovered those facts through the visible entry and its links.
The benchmark set has not been searched or scored during tuning. These remain controlled,
synthetic templates, not a sample of real user traffic.

The active variants are:

- `search-then-walk-1`: the draft's unchanged four-file reference. Hashes protect the snapshot.
- `search-then-walk-2`: the unchanged `knowledge:ask` retrieval in the working tree.
- `search-then-walk-3`: the replacement local `knowledge:ponder` in the working tree.
  It uses the reference-style search and linked-page walk with safe search inputs
  and citations. Its prompt asks for 8-10 short relevant context facts when
  available and quotes for unknown or disputed facts. It does not raise the
  `find` or `near` budgets.

The runner checks each variant before starting it. The snapshot files have `.txt`
suffixes because they are reference data, not registered skills or executable runtime code.
The runner copies them to their runtime paths in an isolated plugin copy.

The 14 November 2026 results used `page-by-page-1` for the former `ponder`.
That variant is historical, not the working-tree `ponder` or an active runner
choice. Retain its saved results under its original ID. The
[15-16 November 2026 (UTC) report](BENCHMARK.md) measures `search-then-walk-3`
in a full 540-answer run; the [historical report](BENCHMARK-2026-11-14.md) retains
the earlier comparison. Both working-tree commands support local graphs only. Remote graphs,
caller-supplied start nodes, and neighbor filters are unsupported, with no fallback
to the former walker.

## Plan without model calls

From the repository root, print the plan:

```bash
$ python3 plugins/knowledge/evals/benchmark.py plan
```

Inspect the large benchmark plan without running it:

```bash
$ python3 plugins/knowledge/evals/benchmark.py plan --dataset benchmark-1
```

The full three-variant plan has 540 attempts: 60 questions, 3 runs, and 3 variants.
Within each question and repetition, variant order is mixed with a fixed random seed.
This avoids running the full reference batch before the other variants. It does not remove
all effects of provider load or prompt caching; token records include cache reads and writes.

## Select the models

Pass `--model` for the answering session and `--judge-model` for the checked judges. Agent
model settings still apply. Set `--expected-model` to each permitted served answer model ID,
repeating it for subagent models. These are model IDs, not aliases.

For the benchmark runner, `--judge-model` and `--expected-judge-model` both default to
`claude-opus-5-5`. `--expected-judge-model` requires that exact served model ID in every
checked judge response. It is separate from the permitted answer models. If you select
another judge model, set both judge options before the run.

An environment can map `sonnet`, `haiku`, or `opus` to another model. The experiment records
those model-selection values without reading credentials. The report uses served model IDs
from the response, not an assumed model name. A served model outside the permitted list
stops the experiment. Resolve the mapping before a benchmark; changing the permitted model
list afterwards cannot resume an existing experiment.

To use Claude Code's default model and provider settings instead of local model routing,
add `--claude-defaults` to the benchmark or pilot command. This option passes
`--setting-sources ''` to Claude Code and removes all `ANTHROPIC_*` variables,
`CLAUDE_CODE_SUBAGENT_MODEL`, and `CLAUDE_CODE_USE_*` variables from each child process.
This also removes inherited API keys and authentication tokens in `ANTHROPIC_*`.
It keeps the cached Claude Code login and a separately named `CLAUDE_CODE_OAUTH_TOKEN`,
if present. You must have a valid Claude Code login. The parent environment and saved
settings do not change. Without this option, the runner keeps the inherited settings.

The selected `--model` and `--judge-model` still apply, as do model choices in plugin
agents. Native eval isolates its answering workspace settings, but its parent and graders
can inherit environment values. This option also clears those values for the parent and
graders. Answer plugin sessions do not use `--safe-mode` or `--bare`, which can disable
plugin behavior. The separate checked judges do use `--safe-mode` and have no tools.

Both runners write the selected mode and permitted model-environment fields to
`experiment.json`; they do not record credentials or provider URLs there. The benchmark
also checks these fields before a resume. Keep `--claude-defaults` unchanged when you
resume. Continue to check the served model IDs with `--expected-model`.

Print the pilot command with these child settings, without model calls:

```bash
$ python3 plugins/knowledge/evals/run_pilot.py --claude-defaults
```

Add `--run` only when you want to start the pilot and its model graders.

## Run a small diagnostic

The following command starts live model calls. Replace `QUESTION_ID` with an ID in the
smoke dataset and `SERVED_MODEL_ID` with the model ID you expect. It runs one question once
on one variant, with model grading:

```bash
$ python3 plugins/knowledge/evals/benchmark.py run-smoke --variant search-then-walk-2 --case QUESTION_ID --runs 1 --expected-model SERVED_MODEL_ID --output .benchmark-runs/smoke-check-01
```

Add `--prepare-only` to build the native cases and fixture without starting any models.
To execute that prepared experiment later, repeat its command without `--prepare-only` and
with `--resume`. The source files and model settings must still match.

Use `run-tuning` for the medium graph. A full run uses 3 fresh sessions per question.
Subset runs and 1- or 2-run diagnostics are available only for the small and medium graphs.
A full benchmark always uses all 60 questions and 3 runs per question.

The fixture script copies the graph, starts an empty git repository, and prepares the
Python dependencies before timing the answer. It needs `uv` and an installed Python 3.12. A temporary
tool directory selects real Git rather than the macOS launcher and gives setup and measured
commands the same Python version and workspace-local dependency cache. Setup can download
dependencies; measured `uv` commands run offline and cannot download Python. The experiment
records the selected tool paths, versions, and file hashes. A resume must match them.

Native eval runs shell commands in its sandbox. No sandbox settings change. This benchmark
grant is separate from the live test of the skill's own permission rules.

## Check grading before a benchmark

The benchmark runner uses native eval to produce and record the answer. Its `case.yaml`
file has only the `answer-present` regex grader (`\S` on `last_message`). This checks for
non-whitespace text, not factual quality. The hidden `native-case.json` file preserves the
original model-grading rubric. Neither case file goes into the answer workspace.

Published quality comes from `checked_grading.py`, not native model votes. For each saved
answer, it starts three fresh, separate, tool-free Claude sessions with structured JSON
output. Each session grades all criteria and gives a Boolean and a nonempty reason for each.
Two of three valid votes determine each criterion's result. The judges count facts anywhere
in the answer, including context sections, and accept equivalent wording.

Each attempt keeps `grading-request.json` and a `checked-grading/` folder. The folder holds
the request and its SHA-256 hash, raw `stdout.json`, `stderr.txt`, and `process.json` for each
vote, plus `timing.json` and `result.json`. Reasons remain in the raw output and summary.
The reader checks the request hash, question, and saved answer against the native prompt
and answer records. It checks the summary against the raw votes.

All three responses must pass validation: successful processes and CLI results, no permission
denials, three distinct session IDs, the exact expected judge model, valid cost records,
and exactly the required criteria with Boolean votes and nonempty reasons. Missing or invalid
output is an error, not a `false` vote or a zero quality score. The run stops with quality
unavailable and retains the evidence. Grading time and cost are recorded separately from
answer time and cost; answer time excludes grading.

Native controls gave different scores for a known-correct multiline answer and its flat-text
form. The cause is unproven. Before a benchmark, you must run positive and negative controls
through checked grading. Confirm that correct answers pass and that missing or conflicting
facts fail, including multiline and flat forms. Keep the raw evidence. The implementation
alone does not show that these calibration checks have passed. Historical pilot scores stay
native scores; do not relabel them as checked grades.

## Refresh the published benchmark

Run this command only after the checked controls pass. Only this command starts the
340-page dataset. It starts live model calls and must be an explicit user request. Pass each permitted served model ID with `--expected-model`:

```bash
$ python3 plugins/knowledge/evals/benchmark.py refresh-benchmarks --expected-model SERVED_MODEL_ID --output .benchmark-runs/benchmark-01
```

The default is all three active variants. Pass `--variant` more than once to select
variants. A refreshed comparison of the shipped commands requires at least
`search-then-walk-2` and `search-then-walk-3`. The reference helps detect a loss after
code or prompt changes; it is not a third shipped command. Keep the dated
`page-by-page-1` results as history, not as measurements of the replacement.

The output folder must be outside the source plugin. This keeps generated case files out
of ordinary native case discovery. Each output folder gets a `.gitignore` that excludes
its contents. The runner stores the schedule and hashes of the dataset, runtime files,
variants, and measurement code before any attempt. Each completed attempt is appended to `attempts.jsonl`.
There are no automatic retries. A wrong answer is a scored result; an environment error,
incomplete grading, or invalid measurement stops the run and remains visible.

To continue a run stopped between valid attempts, repeat its command with `--resume`.
The configuration and hashes must match. A failed or interrupted attempt is not rerun
silently: retain that experiment and start a separate one after fixing the cause.

## Read the report

The native report contains the answer-present check. The saved session result supplies the
answer text. The separate checked-grading records supply quality votes and reasons. The
copied main and subagent records supply model-turn and tool-call totals. A turn is one unique
model response, not one streamed message block. Subagent starts count the retained child
sessions. Tool calls are model-issued calls; the scripted search before the model starts is
recorded separately.

A child's explicit terminal refusal can have no text. It is a complete record for counting
only when a matching failed-task record confirms the end. The report keeps the child refusal
visible. If that child records several real refusals, each distinct message counts once;
the child-refusal count still counts one child. Each refusal must match the failed task.
Synthetic error messages do not count as model responses. A child with neither a final text
response nor the required refusal evidence still makes counts unavailable.

The measurements are:

- Accuracy: each required fact is correct, with no conflicting answer.
- Fact retrieval: the share of required facts returned.
- Context retrieval: the share of the expected relevant context facts returned.
- Answer time: the checked CLI session duration, including waits between automatic follow-up
  turns, but excluding fixture setup and grading. The report names the timing source.
- Tokens: recorded input, output, cache-read, and cache-write tokens, including subagents.
- Cost: the CLI estimate, with answer cost and grading cost separate. The cost basis is shown.

A deep walk can produce several result events in one session. Their token and cost fields
are cumulative: the reader takes one checked final total, not their sum. It counts shell
tasks separately from agents. A sandbox failure has no accuracy score.

For CLI 2.1.323 and 2.1.325, the reader checks each saved session duration against
session identity, cost, model totals, and log timestamps. The timing-source label includes
the actual CLI version. The 2.1.325 check used a retained native answer whose session
duration was 8.035 seconds; its start and end matched the log within the existing
two-second tolerance. This observation supports that record, not every possible run:
each later record must pass the same checks.

This saved `cost-state` format is internal, not a stable public interface. An unverified
CLI version or an inconsistent saved state stops measurement. A single result with no
saved state can use its public duration field; a multi-result run cannot. These times
come from CLI records, not an independent process timer. Supporting a record format
does not pin the CLI executable or change the user's installed default.

Every judge checks facts, not exact wording or answer length. Each expected fact has source
evidence in the dataset. Source-path formatting is not part of the quality score. That lets
the reference, fast ask, and ponder use the same grading rules.

Print a summary after all planned attempts finish:

```bash
$ python3 plugins/knowledge/evals/benchmark_report.py .benchmark-runs/benchmark-01
```

Print the Markdown table for the plugin README:

```bash
$ python3 plugins/knowledge/evals/benchmark_report.py .benchmark-runs/benchmark-01 --readme-table
```

The report refuses to make that table for a subset, duplicate attempts, missing measurements,
the wrong dataset, or quality without `checked_claude_3` grading and recorded judge models. It never edits README automatically. Raw reports can contain home
paths and session IDs, so keep them in ignored result folders. Only a reviewed summary belongs
in the public README. Native temporary workspaces are retained to preserve evidence; remove
only the run folders after the records have been copied and checked.
