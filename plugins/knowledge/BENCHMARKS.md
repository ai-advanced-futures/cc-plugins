# Benchmarks

A plain-language summary of the knowledge 2.0.0 reader experiments. The latest
540-answer run finished on **16 November 2026 (UTC)**. All data was invented;
no private project knowledge was used.

## Three active versions

| Version | Approach |
| --- | --- |
| Saved reference — `search-then-walk-1` | Original fast-reader draft: search, then inspect nearby linked pages. Kept unchanged for comparison. |
| `ask` — `search-then-walk-2` | Local search and a bounded link walk, with source paths and relevant context. |
| `ponder` — `search-then-walk-3` | Reference-style answer instructions with current safety fixes and citations. Requests 8-10 short context facts when supported. |

All three prompts include graph-link retrieval. Ponder uses the same search and
link-search limits as ask; it does not add a page-by-page agent loop. Neither
shipped command supports remote graphs, caller-supplied start nodes, or neighbor filters.

## Latest results

Each version answered the same 60 questions three times on a 340-page graph.
Each row is an average over 180 completed answers.

| Version | Seconds per answer | Accuracy | Required facts | Relevant context | Answer cost estimate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saved reference | 10.05 | 95.6% | 97.9% | 95.1% | $0.0693 |
| `ask` | 8.36 | 96.7% | 98.5% | 92.2% | $0.0576 |
| `ponder` | 10.49 | 96.1% | 98.1% | 93.5% | $0.0681 |

**Accuracy** requires every required fact and no conflicting answer. **Facts and
context** measure the mean share of expected information returned per answer.
Time excludes setup and grading. Cost is a CLI list-price estimate, not verified
billing, and excludes grading.

### What this means

- **Ask remains the faster, cheaper default.** It also had the highest observed
  accuracy in this run: 174 correct answers out of 180, compared with 173 for ponder.
- **Ponder returned modestly more context:** 1.3 percentage points above ask, for
  about 25.5% more time and 18.3% more answer cost. It did not improve accuracy.
- **The saved reference is not consistently more accurate.** Its earlier accuracy
  advantage did not repeat, although it still returned the most expected context.
- These are observations on one synthetic question set, not evidence of statistical
  significance or results for every real project. The repeated run is not a fresh
  held-out test: the earlier aggregate results informed the choice of ponder.

## Historical page-by-page comparison

The 14 November 2026 run used a different ponder implementation, `page-by-page-1`.
It read pages one at a time and used child agents to select the next links.
These results remain separate from the replacement's measurements.

| Historical version | Seconds per answer | Accuracy | Required facts | Relevant context | Answer cost estimate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saved reference | 8.11 | 96.7% | 98.3% | 95.2% | $0.0650 |
| `ask` | 6.65 | 95.0% | 97.5% | 90.8% | $0.0565 |
| Former `ponder` — `page-by-page-1` | 123.31 | 85.6% | 86.8% | 79.2% | $0.5016 |

The old run used CLI 2.1.323; the latest run used 2.1.325. Provider load and caching
were not fixed. The historical difference therefore does not isolate the effect
of changing the implementation. See the [historical full report](evals/BENCHMARK-2026-11-14.md)
for its measurements, failures, and recoveries.

## Experiment stages

Page counts exclude indexes. Only the two full runs supply the comparison tables.

| Stage | Available data | Work performed |
| --- | --- | --- |
| Early pilot | 12 pages; one question | Checked the setup. A local setting selected a different model, so its timing is not a Claude comparison result. |
| Small checks | 50 pages; 12 questions | Selected live reader checks, grading controls, and smoke questions; not a full 12-question comparison. |
| Development | 120 pages; 36 questions | Offline search checks. Fifteen questions needed follow-up retrieval; visible links supplied their missing facts. No full live timing comparison. |
| 14 November full run | 340 pages; 60 questions | Reference, ask, and page-by-page ponder; three repeats: 540 completed results. |
| 15-16 November UTC full run | Same 340 pages and 60 questions | Reference, ask, and reference-based ponder; three repeats: 540 valid results. Inputs stayed fixed during the run. |

## How the latest run worked

1. Fix the readers, questions, models, and grading rules. Keep the answer key out
   of answering workspaces.
2. Use fresh, sequential sessions and mix variant order within each question and repeat.
3. Verify that all answer sessions serve Sonnet 5.5.
4. Check grading with known correct, incorrect, and partial answers, then use three
   separate Opus 5.5 judges per answer. Require three valid responses and take a
   majority vote for each criterion.
5. Retain raw evidence and audit the 540 answers and 1,620 judge sessions before
   publishing the results.

The audit re-extracted all 540 measurements and found exact matches. Sealed native
working copies were not opened; checks used retained records and staged sources.
Twenty-eight ask answers used only the initial search output, with no later tool call.

The full run had no recorded execution or grading errors, runner retries, replacement
batches, or child refusals. Incorrect answers stayed in the quality scores. Retained
results cannot prove the absence of service-internal retries. The recorded cost
estimate was **$35.1098 for answers plus $34.0286 for grading: $69.1384 total**,
excluding preliminary checks. This is not a billing total.

Before the full run, a smoke measurement exposed the timing reader's version check.
CLI 2.1.325 records were validated without pinning the executable to an older version.
The saved answer was graded without rerunning it, and the failed measurement remains
retained. A live-probe wording check was also corrected using its saved response.

See the [latest full report](evals/BENCHMARK.md) for token counts, evidence checks,
and limitations; the [run guide](evals/RUNNING.md) for commands; and the
[dataset guide](evals/README.md) for early checks. These benchmarks do not measure
the separate rollout to other plugins' ask skills.
