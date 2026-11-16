# Reader benchmark: 15-16 November 2026 (UTC)

## Run

Knowledge 2.0.0 was measured on `benchmark-1`: 340 synthetic content pages and
60 fixed questions. Each of three variants answered each question in three fresh
sessions, for **540 valid results**. The run started on 15 November and finished
on 16 November UTC, taking about 4 hours 6 minutes including setup and grading.

The variants are the frozen draft reference (`search-then-walk-1`), local `ask`
(`search-then-walk-2`), and reference-based local `ponder` (`search-then-walk-3`).
All are designed to search and then inspect bounded linked pages. The replacement
ponder keeps current safety fixes and source citations; it is not the frozen reference.

Variant order was mixed within each question and repeat with seed 2196. Reader
files, datasets, models, and grading rules stayed fixed throughout the full run.
The earlier aggregate results informed the choice of the ponder approach. This
rerun uses the same questions, so it is not a fresh held-out validation. No
question-specific rules or answer keys were added to the readers.

The [14 November report](BENCHMARK-2026-11-14.md) retains the former page-by-page
ponder results and their recovery history. Those numbers do not measure the
replacement.

## Results

Each row is a mean over 180 completed answers.

| Variant | Mean seconds | Accuracy | Facts | Context | Tool calls | Model turns | Agents | Tokens | Answer cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `search-then-walk-1` — saved reference | 10.05 | 95.6% | 97.9% | 95.1% | 1.6 | 2.6 | 1.0 | 60,763 | $0.0693 |
| `search-then-walk-2` — `ask` | 8.36 | 96.7% | 98.5% | 92.2% | 0.9 | 1.9 | 1.0 | 39,581 | $0.0576 |
| `search-then-walk-3` — `ponder` | 10.49 | 96.1% | 98.1% | 93.5% | 1.4 | 2.4 | 1.0 | 55,135 | $0.0681 |

### Observed trade-off

Compared with ask, ponder returned **1.3 percentage points more expected context**,
but had **0.6 points lower accuracy**. It took about **25.5% longer** and cost
about **18.3% more** per answer. Accuracy counts were 174 of 180 for ask, 173 for
ponder, and 172 for the reference.

These results support ask as the faster, cheaper default. Ponder provides a
modest observed context gain, not an established accuracy improvement. The frozen
reference had the highest context score but lower accuracy than either shipped
reader. Its accuracy advantage from the earlier run did not repeat.

### Tokens and grading

These are mean recorded token counts and CLI cost estimates per accepted result.

| Variant | Input tokens | Output tokens | Cache-read tokens | Cache-write tokens | Grading cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saved reference | 5.2 | 836.3 | 37,013.7 | 22,907.9 | $0.0627 |
| `ask` | 3.8 | 761.3 | 19,614.7 | 19,201.2 | $0.0621 |
| `ponder` | 4.8 | 1,033.2 | 32,274.7 | 21,822.5 | $0.0642 |

Recorded full-run estimates total **$35.1098 for answers** and **$34.0286 for
grading**, or **$69.1384 combined**. These are CLI list-price estimates, not
verified billing. They exclude preliminary live checks, grading controls, and
smoke checks.

## What the numbers mean

- **Accuracy:** all required facts are present, with no conflicting answer.
- **Facts and context:** the mean per-answer shares of expected required facts
  and relevant context facts. They are not one globally weighted fact ratio.
- **Time:** checked CLI session elapsed time, including waits between follow-up
  turns but excluding setup and grading. The source is
  `cli_session_cost_state_2.1.325`, not an independent process timer.
- **Model turns:** unique real model-response IDs in the main and child logs.
  Streamed blocks and synthetic error messages do not add turns.
- **Tool calls:** unique model-issued calls. Each variant has one additional
  scripted search before the model starts, excluded from this column.
- **Agents:** child-agent starts, excluding the main session.
- **Tokens:** input, output, cache-read, and cache-write totals, including child
  agents. The main table sums these categories.
- **Cost:** CLI list-price estimates. Answer cost excludes grading; grading cost
  covers the accepted three-judge batch.

Twenty-eight ask answers used only the initial search output, with no later tool
call. The counts describe observed behavior, not guaranteed compliance with every
prompt step.

## Models and evidence

All answer sessions served `claude-sonnet-5-5`. Each answer was graded by three
separate, tool-free `claude-opus-5-5` sessions. Raw replies, structured votes,
reasons, request bindings, and actual served models were checked. Native answer
execution supplied the answer; its text-presence check is not the quality score.

Child processes ignored local model and provider overrides. Saved settings and
credentials were unchanged. The run used installed CLI 2.1.325 without pinning it
to an older executable. Reader and measurement implementation: `3bb0f91f`.

An independent audit re-extracted all 540 measurements and matched every journal
entry exactly. It confirmed the unique schedule, 540 distinct answer sessions,
1,620 distinct judge sessions, and exact grading bindings. All 418 source files
matched the measured commit. Retained staged files and all 540 recorded skill
bodies matched their expected sources, apart from the variable first-search output.
The evidence tree stayed unchanged during the audit.

Sealed native working copies were not opened or compared. The audit checks retained
records; it has no signed record of file bytes at execution time. It did not grade
answers again.

Dataset SHA-256:
`367d9be3b3c27842bf59709fd3dcdebb404e13dd8ac45dec05e73ab9c0e2341f`.
Measured runtime SHA-256:
`bd9a3e7f6eed30fbf3ec57724cc87c5c775578000e53287c65e1247f35566ac9`.
Journal SHA-256:
`fc1ca1ccac22e246bef121e06a113b29e7e175ec96d8ec4ab8ecb9219c152526`.

## Failures and preliminary checks

The full 540-answer run had no recorded execution or grading errors, runner
retries, replacement grading batches, or child refusals. Factual failures remained
in the quality scores. Retained records cannot prove that the service made no
internal retry.

Before the full run:

- Ten live probes checked registration, local answers, unsupported requests,
  permission boundaries, and unchanged product and business-case callers.
- Four grading controls passed with unanimous expected votes: correct multiline,
  correct flat text, incorrect, and partial answers.
- The first native smoke answer completed, but the extractor rejected CLI 2.1.325
  because only 2.1.323 had been validated. Its saved cost-state passed the same
  session, cost, token, and timestamp checks. Version-specific coverage was added;
  seven damaged copies were rejected through the measurement CLI.
- The saved ponder answer received its first grading in a copied evidence folder,
  without an answer rerun. Reference and ask then completed their smoke checks.
  All three returned all required facts and expected context for that one question.
- A live start-node probe initially failed because its checker did not accept
  the equivalent phrase "doesn't support." The saved response passed the corrected
  check without a model rerun.

Preliminary failures and original records remain retained. They are not part of
the full-run means or the 540 scheduled positions.

## Limits

The questions use controlled fictional templates, not a sample of real traffic.
There are 60 distinct questions repeated three times, not 540 independent questions.
Provider load and prompt caching were not held constant. No statistical significance
claim is made. Prompt choice used earlier aggregate results on the same dataset.

The earlier benchmark used CLI 2.1.323; this run used 2.1.325. Historical time and
cost differences therefore do not isolate the implementation change. Prefer the
within-run comparison when choosing between ask and ponder.

Both shipped readers support local graphs only. Remote graphs, supplied start
nodes, and neighbor filters are unsupported, with no page-by-page fallback. This
benchmark does not measure the separate rollout of fast-first ask to other plugins.

Raw logs contain local paths and session IDs and remain outside the public release.
Only reviewed summaries are published. See [Run knowledge benchmarks](RUNNING.md)
for commands and validation rules.
