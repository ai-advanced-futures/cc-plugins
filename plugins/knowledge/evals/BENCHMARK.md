# Reader benchmark: 14 November 2026

## Run

Knowledge 2.0.0 was measured on `benchmark-1`: 340 synthetic content pages and
60 fixed questions. Each of three variants answered every question in three fresh
sessions, for 540 completed results. Variant order was mixed within each question
and repeat with seed 2196. Reader files, questions, models, and grading criteria
stayed unchanged during the run. No changes were tuned on the final dataset.

## Results

Each row is a mean over 180 completed answers.

| Variant | Mean seconds | Accuracy | Facts | Context | Tool calls | Model turns | Agents | Tokens | Answer cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `search-then-walk-1` — saved reference | 8.11 | 96.7% | 98.3% | 95.2% | 1.4 | 2.4 | 1.0 | 54,409 | $0.0650 |
| `search-then-walk-2` — `ask` | 6.65 | 95.0% | 97.5% | 90.8% | 0.8 | 1.8 | 1.0 | 36,363 | $0.0565 |
| `page-by-page-1` — `ponder` | 123.31 | 85.6% | 86.8% | 79.2% | 39.0 | 37.2 | 4.7 | 1,416,472 | $0.5016 |

On this set, `ask` was faster and used fewer tokens than the saved reference, but
its accuracy was 1.7 percentage points lower and its context retrieval was
4.4 points lower. It was faster and scored higher than `ponder`. These are observed
differences on one synthetic set, not a statistical significance claim or a result
for all real projects.

### Tokens and grading

These are mean recorded token counts and CLI cost estimates per accepted result.

| Variant | Input tokens | Output tokens | Cache-read tokens | Cache-write tokens | Grading cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saved reference | 4.9 | 790.7 | 32,078.0 | 21,535.3 | $0.0637 |
| `ask` | 3.5 | 720.3 | 16,585.3 | 19,054.1 | $0.0626 |
| `ponder` | 83.8 | 17,115.2 | 1,333,140.2 | 66,132.9 | $0.0642 |

## What the numbers mean

- **Accuracy:** all required facts are present, with no conflicting answer.
- **Facts and context:** the mean per-answer share of expected required facts or
  relevant context facts. These are separate criteria, not the native combined score.
- **Time:** checked CLI session elapsed time, including waits between follow-up
  turns but excluding setup and grading. The source is
  `cli_session_cost_state_2.1.323`, not an independent process timer.
- **Model turns:** unique real model-response IDs in the main and child logs.
  Streamed blocks and synthetic error messages do not add turns.
- **Tool calls:** unique model-issued calls. The reference and `ask` each have one
  additional scripted search before the model starts; `ponder` has none.
- **Agents:** child-agent starts, excluding the main session.
- **Tokens:** recorded input, output, cache-read, and cache-write totals, including
  child agents. The table sums these categories.
- **Cost:** CLI list-price estimates, not verified billing. Answer cost excludes
  grading. Grading cost describes the accepted three-judge batch only.

## Models and evidence

The reference and `ask` served `claude-sonnet-5-5`. `ponder` served
`claude-sonnet-5-5` and `claude-haiku-5-5`. Each accepted grading batch used three
separate `claude-opus-5-5` sessions with checked JSON votes and reasons. Model IDs
came from retained responses, not requested aliases. Child processes ignored local
model-routing settings; saved settings and credentials were not changed.

The final audit re-extracted all 540 reports and matched every measurement to its
ledger entry. It checked 540 unique answer sessions and 1,620 unique accepted judge
sessions. The saved reference is one variant with four hash-checked files.

Reader implementation: `e82d48bd3`. Final measurement correction: `0b1b48559`.
Dataset SHA-256:
`367d9be3b3c27842bf59709fd3dcdebb404e13dd8ac45dec05e73ab9c0e2341f`.
The recorded runtime hash matched the reader package before these result documents
were added. Only measurement code changed during the run, as described below.

## Failures and recovery

- One `ponder` answer attempt reached the 600-second limit without a final result.
  One explicitly approved retry completed in 221.113 seconds with the same limit.
  The failed attempt remains retained and has no factual score.
- Four grading batches had one judge that could not produce valid structured
  output. Each batch was replaced with three fresh judges on the identical saved
  answer and criteria. One replacement had separate approval; three used a later
  ten-batch limit. Thus, four replacements added 12 judge sessions. Failed batches
  remain retained. A factual FAIL never caused a retry.
- Two completed answers needed count-extraction corrections. One child had a real
  refusal with no text; another had two distinct real refusals. Matching failed-task
  and child identities proved that their records were complete. The saved answers
  received their first grading after correction; neither answer was rerun.
- Eleven `ponder` child-agent sessions ended in refusal. Their real responses remain
  in the counts, and the parent answers were graded as returned. Neither other
  variant recorded a child refusal.

Every continuation rechecked retained measurements and copied evidence. Original
reports and ledgers were not overwritten. Where measurement code changed, the
remaining configuration had to match. The final set contains exactly the planned
540 positions, without counting copied records as new sessions.

The published means describe completed answers and accepted grading batches.
The timed-out answer and four failed judge responses lack complete verified usage.
Their reported zero or absent cost is not evidence of zero cost. Full-run token and
cost totals, including incomplete work, are therefore unavailable.

## Limits

The questions use controlled fictional templates, not a sample of real traffic.
Provider load and prompt caching were not held constant. The 11 child refusals are
part of the observed `ponder` result, not evidence that a deeper walk is always less
accurate. Remote graphs and caller-supplied start nodes were not measured here;
those remain reasons to choose `ponder`.

Raw logs contain local paths and session IDs and remain outside the public release.
Only this reviewed summary is published. See [Run knowledge benchmarks](RUNNING.md)
for the commands and validation rules.
