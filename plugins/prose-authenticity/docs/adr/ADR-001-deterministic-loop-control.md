# ADR-001: Deterministic Loop Control

**Status:** Accepted

## Context

The `/prose-authenticity:humanize` command runs a loop. The loop repeats until the verdict is PASS. Each pass has these steps:

1. Score the draft.
2. If the verdict is not PASS, rewrite the flagged zones.
3. Reassemble the draft.
4. Score the draft again.

Two designs were possible for the part that decides whether to iterate again or stop:

1. **Agent-driven loop.** The orchestrator agent reads the latest verdict and the tier scores in each iteration. It reasons in prose. It decides to continue, to switch the detector tier, or to give up.
2. **Deterministic loop-control script.** The script `lib/loop_controller.py` holds a pure state machine. The state machine takes three inputs: the current iteration count, the verdict history, and the configured caps. It returns the next action. The orchestrator only runs that decision.

## Decision

We chose the deterministic loop-control script (option 2). It holds all stop and continue logic:

- the iteration cap
- the score-plateau check
- the fact-gate retry budget

This logic is in `lib/loop_controller.py` and nowhere else. The script is a pure function. It maps typed inputs to a typed action. The orchestrator agent never reasons about whether to keep iterating. It calls the script and reads the returned action. Then it acts on that action.

The action vocabulary has exactly seven values. The function `next_action()` returns them:

- `RUN_QUESTION_SCAN` — scan the draft for rhetorical-question candidates. This is the first action of every iteration (not `RUN_DETECTORS`). A fact-checked rewrite must get a new scan. Without it, the rewrite can add a new rhetorical question that nothing detects (ADR-005).
- `ADJUDICATE_GATE` — the scan found candidates, and no genre override exempts them. Dispatch the question-adjudicator. It classifies the genre and labels each candidate before scoring (ADR-005).
- `RUN_DETECTORS` — score the current draft. This happens after the scan or the adjudication. It also happens at the start of each new iteration after a clean fact-check.
- `ACCEPT` — the verdict is `PASS`. Stop and keep the current draft.
- `DISPATCH_REWRITE` — dispatch the humanizer for another rewrite pass. This action applies when the verdict is not `PASS`, the loop is under the iteration cap, and the score has not plateaued. It also applies when a fact-check just returned missing facts and retries remain.
- `RUN_FACT_CHECK` — a rewrite just finished. Check the fact coverage before you count the iteration as done.
- `GIVE_UP` — stop with no passing verdict. This action applies in any of these cases:
  - The verdict is `UNAVAILABLE`.
  - The loop reaches the iteration cap.
  - The score plateaued. Two scores of the same tier differ by less than `min_delta`.
  - The fact-check retries use up the budget (`FACT_MISS_MAX_RETRIES`).
  - The rhetorical-question gate forces a stop. This happens for a verbatim artifact. It also happens when the rhetorical questions are only in human-authored zones (ADR-005).

**Amendment (ADR-005, rhetorical-question gate):** The vocabulary first had five values. The gate added `RUN_QUESTION_SCAN` and `ADJUDICATE_GATE`. They are the two lead actions of each iteration. The gate also added its two stop conditions to the `GIVE_UP` triggers above. ADR-005 gives the gate design. It also explains why the scan runs again after every rewrite.

There is no `TIER_CHANGE` action. The loop fixes the detector-tier precedence once for each run. Consent and availability set it at the start (ADR-003). The loop does not switch tiers during a run to get a better score.

A tier can disappear during a run. This happens only when a tier that was available becomes unavailable on a later call. An example is an api-tier detector.

In that case, the plateau comparison in `_plateaued()` treats the cross-tier pair as "delta undefined". The function returns `False`, which means not plateaued. The iteration cap stays as the backstop. The loop does not treat the tier loss as a separate controller action.

We rejected the agent-driven loop for three reasons:

- **Untestable convergence.** An agent judges "should I keep going?" in each run. A unit test with synthetic verdict sequences cannot fix that judgment. Each run is a new judgment that nobody can verify.
- **Unbounded token spend.** Nothing stops an agent from reasoning its way into "just one more iteration" again and again. A runaway loop costs money. It has no deterministic ceiling.
- **Non-reproducible bugs.** A user can report a loop bug, for example "it never stopped". If the stop condition is in agent prose and not in code, the bug is almost impossible to reproduce. It is also almost impossible to cover with a regression test.

## Consequences

- The orchestrator agent only runs the decision. It never computes iteration counts, plateau deltas, or cap comparisons. `loop_controller.py` returns each of these numbers.
- Unit tests check `lib/loop_controller.py` against synthetic verdict sequences. The sequences cover four cases:
  - The loop reaches the iteration cap.
  - The score plateaus. N iterations of the same tier show no improvement.
  - The run loses a tier, and the delta has no value. The iteration counts toward the cap, not the plateau test. The comparisons start again, as the fixed-precedence design of ADR-003 requires.
  - The fact-gate retries use up the budget.

  Each sequence gives the expected action every time.
- The state machine is pure. It maps typed inputs to a typed action and does no I/O. A person can reason about it and test it. The test needs no agent, no detector tier, and no fact-coverage check.
- There is a tradeoff. A new stop or continue rule goes into the Python state machine. An example is a future early exit based on cost. The rule does not become new agent prose. This constraint is deliberate. It is not a gap.
