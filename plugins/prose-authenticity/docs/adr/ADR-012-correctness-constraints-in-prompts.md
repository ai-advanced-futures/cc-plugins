# ADR-012: The correctness and STE checks are prompt constraints and a report line, not a loop gate

**Status:** Accepted
**Date:** 2026-08-19

## Context

The plugin gained `lib/ste_checker.py` in v0.3.0 and `lib/correctness_checker.py`
in v0.4.0. No agent prompt named either one. At v0.4.1, a grep for both module
names across `agents/` and `commands/` returned nothing.

The humanizer is the agent that matters here, because it rewrites prose. Its
rules covered tells, facts, zone provenance, and rhetorical questions. Nothing
told it to avoid a new misspelling or a doubled word. Nothing told it to avoid
an article that disagrees with the noun after it.

All three correctness rules catch an editing artifact more than an authoring
error. A botched splice leaves a doubled word. Article disagreement happens when
a rewrite changes the noun after `a` or `an` and leaves the old article in
place. The humanize loop edits prose. So the loop is where these faults get in,
and nothing in the loop takes them out.

Two earlier decisions limit the shape of any fix.

ADR-006 keeps the STE verdict out of the detector composite. A single number
cannot carry two measurements.

ADR-008 keeps STE off surfaces where persuasion is the job. It measured the cost
of applying STE everywhere. Two argument sections lost their force. Every quoted
line became reported speech.

ADR-008 deferred a `discipline=` zone attribute to a later sub-project. That
attribute never shipped. At v0.4.1, `lib/` and `agents/`
carry no reference to it.

## Decision

The humanizer prompt names all three correctness rules. It gives the fault that
each rule catches. It tells the humanizer to read its own rewrite back.

The humanizer does not apply STE. It has no signal for the surface of a zone, so
it cannot make the judgment that ADR-008 requires.

Instead, it carries the two ADR-008 resolutions that need no knowledge of the
surface. First, when it removes an em-dash, it splits the sentence. It does not join two clauses with a comma.
Second, it varies sentence length on purpose. It does not flatten the cadence.

Verification is report-level. The detection-analyst runs both checkers. On a
single-pass `/check`, it reports every finding. On a humanize run, it runs each
checker twice: once on the original, and once on the accepted output. It reports
the delta. The delta is what the rewrite introduced.

The report lists the findings that were already there in a separate list. The
author must fix those.

`lib/fault_delta.py` computes the difference. The architecture principle of the
plugin puts every number and every parse in a tested script, not in agent prose.
A set difference over two lists of findings is exactly that kind of work. The
first draft of this decision had the agent run both checkers twice and diff the
output by hand. The principle forbids that.

Identity is `(checker, rule, excerpt)`. It deliberately excludes the line number.
A rewrite moves text. A comparison keyed on the line would report the whole
surviving pre-existing set as newly introduced. The delta would be useless on
every real run.

The difference is over a multiset, so a second copy of an existing fault counts
as one introduction. R7 is the exception. It works on the whole document and
emits one finding, anchored to the opening sentence. It keys on the rule alone.

Neither verdict enters the detector composite. The report names them
`ste_verdict` and `detector_verdict`. ADR-006 reserved this naming for exactly
this case.

## Alternative rejected: gate the loop on a correctness finding

The loop could treat a new correctness finding as a reason to iterate again. We
rejected this for three reasons.

First, the loop stops when the detectors pass. A correctness finding would have
to force an extra iteration. That makes it an input to the stop condition.
ADR-006 separated the two measurements to avoid exactly that.

Second, a rewrite that fixes a doubled word can introduce a different one. That
needs its own cap and its own oscillation rule. It buys a fix for a fault that a
reader can correct with one keystroke.

Third, `lib/prose_spans.py` has a known fail-open. A wrapped inline code span
inverts parity and hides prose from all four rules. The checker under-reports. A
gate built on an under-reporting check gives false confidence. A disclosure built
on the same check is still honest about what it found.

We enforce the decision and do not only assert it.
`tests/unit/test_prompt_quality.py` pins the action set of the loop at seven. It
fails if any action name mentions correctness or STE. It fails if
`loop_controller.py` imports either checker. It fails if the orchestrator or the
loop uses `fault_delta`. To reverse this ADR, change those tests on purpose.

## Consequences

A reader of a humanize report now learns what the rewrite cost them. They did not
learn this before.

The humanizer can still introduce a correctness fault. Nothing stops it. The
prompt reduces the odds, and the report discloses the result. This is the
accepted residual. It is the reason that the report leads with the delta and does
not bury it.

The disclosure is only as good as the checker. While the `prose_spans` fail-open
stands, a clean delta does not prove that the rewrite introduced nothing.

A fourth correctness rule breaks `test_the_humanizer_names_every_correctness_rule`
until the humanizer prompt names it. The contract reads the rule ids from
`config/correctness.yaml`, so it cannot drift quietly.

If the `discipline=` zone attribute ships, revisit this ADR. A per-zone
discipline signal is exactly what the humanizer lacks. It would make a real STE
instruction possible for the first time.
