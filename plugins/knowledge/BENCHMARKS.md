# Benchmarks

A plain-language summary of the knowledge 2.0.0 experiments, completed on
14 November 2026. All data was invented; no private project knowledge was used.

## Three versions compared

| Version | Approach |
| --- | --- |
| Saved reference — `search-then-walk-1` | Original fast-reader draft: search, then inspect nearby linked pages. Kept unchanged for comparison. |
| Current `ask` — `search-then-walk-2` | Revised local search with a limited walk through linked pages, source paths, and relevant context. |
| Current `ponder` — `page-by-page-1` | Visit pages one at a time. Child agents select which linked pages to visit next. |

Both fast versions include a limited graph walk. We did not measure a second
version of the page-by-page `ponder` approach.

## Results

Each version answered the same 60 questions three times on a 340-page graph.
Each row is an average over 180 completed answers.

| Version | Seconds per answer | Accuracy | Required facts | Relevant context | Answer cost estimate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saved reference | 8.11 | 96.7% | 98.3% | 95.2% | $0.0650 |
| Current `ask` | 6.65 | 95.0% | 97.5% | 90.8% | $0.0565 |
| Current `ponder` | 123.31 | 85.6% | 86.8% | 79.2% | $0.5016 |

**Accuracy** requires every required fact and no conflicting answer. **Facts and
context** measure the share of expected information returned. Time and cost exclude
setup and grading; cost is an estimate from Claude Code, not verified billing.

### What this means

- These local results favor `ask` over current `ponder` for speed, cost, and quality.
- Revised `ask` was faster than the reference, but lost 1.7 percentage points of
  accuracy and 4.4 points of context retrieval.
- This does **not** make `ponder` unnecessary. Remote graphs and caller-supplied
  start nodes were not tested. One implementation does not represent every walk design.

## Experiment stages

Only the final stage supplies the comparison table above. Page counts exclude indexes.

| Stage | Available data | Work performed |
| --- | --- | --- |
| Early pilot | 12 pages; one question | Checked the evaluation setup. A local setting selected a different model, so its timing is not a Claude comparison result. |
| Small checks | 50 pages; 12 questions | Selected live reader checks and grading controls, not a full 12-question comparison. |
| Development | 120 pages; 36 questions | Offline search checks. Fifteen questions needed follow-up retrieval; visible links supplied their missing facts. No full live timing comparison. |
| Final benchmark | 340 pages; 60 questions | Three versions × three repeats × 60 questions: **540 completed results**. No reader tuning on this set. |

## How the final run worked

1. Fix the readers, questions, models, and grading rules. Hide the answer key from
   the answering sessions.
2. Use fresh, sequential sessions, with mixed version order for each question and repeat.
3. Verify Sonnet 5.5 for both fast versions; Sonnet 5.5 and Haiku 5.5 for `ponder`.
4. Check the graders with known answers, then use three separate Opus 5.5 judges
   per answer. Require three valid responses and take a majority vote per criterion.
5. Retain raw evidence. Audit all 540 answer records and 1,620 accepted judge sessions.

## Failures and limits

One answer timeout was retried. Four invalid grading batches were replaced, and
two response-counter errors were fixed without rerunning answers. Failures remain
retained; wrong answers were not retried to improve scores. Eleven `ponder` child
sessions ended in refusal and remain counted.

The means cover completed answers, not all failed attempts; full experiment cost is
unknown. Provider load and caching were not fixed. No statistical significance test
was performed.

See the [full report](evals/BENCHMARK.md) for all measurements and recovery details,
the [run guide](evals/RUNNING.md) for commands, and the
[dataset guide](evals/README.md) for early checks.
