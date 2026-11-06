# ADR-005: Rhetorical-Question Gate

**Status:** Accepted

## Context

The heuristics tier measures these signals: burstiness, TTR, modifier density,
hedge density, connector density, em-dash density, and pattern-phrase density.
None of them observes a `?`. A proposal full of rhetorical questions scored a
clean 10/100.

## Decision

We add a rhetorical-question gate as a fourth input to the verdict lattice. The
gate is in `lib/question_gate.py`. It has three parts: a deterministic scanner
(`scan()`), a deterministic evaluator (`evaluate()`), and a genre classifier
(`genre_signals()`). Seven decisions define the gate.

### 1. The gate is a non-composite, fourth verdict input, not a detector tier

The gate result goes to `verdicts.decide(..., gate=...)` as a fourth input next
to the three detector tiers. The gate is deliberately **not** a tier. It has no
composite score. It has no slot in `TIER_PRECEDENCE`. The strictest-available-tier
selection does not apply to it.

The gate can only override the composite verdict. A gate `FAIL` overrides even a
passing composite. A gate `UNADJUDICATED` forces `UNAVAILABLE` (see decision 4).

The gate is optional. When `decide(..., gate=None)` runs, it omits the `gate` key
from its output. So every v0.1.1 fixture that predates the gate stays
byte-for-byte `==`-equal. We could add the gate and not re-baseline one existing
verdict fixture.

### 2. A three-genre trichotomy: `expository` gated, `literary` and `verbatim` exempt

`GENRES = (expository, literary, verbatim)`. The gate checks only `expository`.
The genres `literary` and `verbatim` are exempt (`EXEMPT_GENRES`). The two
exemptions have **different** reasons:

- `literary` is a **stylistic** exemption. A rhetorical question is a legitimate
  rhetorical device in creative prose. If we flatten it into a declarative, we
  damage the voice that the author chose.
- `verbatim` is an **integrity** exemption. It is the stronger of the two.

  Assume we rewrite the recorded question of a speaker into a declarative. We do
  more than flatten a voice. We make the document **false**. The text claims to
  record what a person said. If we edit that record, we fabricate the record.

The `verbatim` exemption generalises a rule of the anti-ai-tells skill. That
skill already ships the rule for each quotation. `skills/anti-ai-tells/SKILL.md:62` states "Apply this
checklist only to machine-drafted text (L-027)." The `verbatim` genre
lifts that guarantee from one quotation to a whole document. The `quoted`
candidate label carries the same guarantee down to one sentence. That sentence
can be in a file that the gate otherwise checks.

### 3. Whole-document scan, human zones included

`scan()` walks the entire document, human-authored zones included. It does not
walk only the AI and mixed zones that the humanizer may rewrite. So the gate
still **reports** a rhetorical question that a **human** wrote. `reassemble()`
copies human zones byte-for-byte. It cannot rewrite that question.

This is intentional. The gate must show every rhetorical question in the
delivered artifact, not only the questions that the tool can fix. Sometimes the
only rhetorical questions are in human zones. Then `rewritable_remaining == 0`,
and the loop reports **"manual fix required"** (a `GIVE_UP` with that reason).
The loop does not pass silently. A silent pass would tell the user that the
document is clean when it is not.

### 4. Fail-closed lives in `run_detectors.py`, not in the pure `evaluate()`

`evaluate()` is a pure function. It has no path, no run-dir, and no file I/O. A
pure function cannot fail closed about an argument that nobody gave it. Suppose
the caller never adjudicated the candidates. Then `evaluate()` cannot know that
the caller *should have* adjudicated them.

So the fail-closed policy lives one layer up, in `run_detectors.py`. That script
always scans and always passes the candidates through. When candidates are
present but unadjudicated, `evaluate()` returns `UNADJUDICATED`.
`apply_gate_override()` maps `UNADJUDICATED` to an `UNAVAILABLE` verdict. A caller
can skip the gate only when it produces a genuine adjudication. A caller cannot
skip the gate by omitting one.

### 5. The five → seven action amendment (ADR-001), and why `fact_checked` re-scans

The gate adds two lead actions to the loop vocabulary: `RUN_QUESTION_SCAN` and
`ADJUDICATE_GATE`. So `loop_controller.next_action()` has seven actions, not
five. We amend ADR-001 to match.

Every iteration **re-enters** at `RUN_QUESTION_SCAN`, not at `RUN_DETECTORS`.
This is critical. After the loop fact-checks a rewrite, it scans again before it
scores.

A humanizer rewrite is free text. Nothing in its structure stops it from adding a
*new* rhetorical question while it removes an AI tell. A scan on each iteration
closes that hole. A rewrite cannot smuggle in a question that the gate never
sees.

### 6. Code surfaces are exempt: `evaluate()` applies the exemption, and the scan still runs

On a code surface, the gate returns `EXEMPT`. `evaluate()` applies the exemption
(its step 1: `source_surface == "code"`). The exemption does **not** come from a
skipped scan. The scan still runs on code. It still finds a `?` inside a comment
or docstring. Then `evaluate()` exempts the surface.

We rejected the suppression of the whole scan. That option joins two concerns
that must stay apart: discovery and policy. Unconditional discovery also gives a
deterministic result for a comment-free `.py`: `zones == []`. During
implementation, a naive `zones[0]` access turned that case into an `IndexError`.

### 7. U6 (evidence guard) and U7 (proposal condition)

- **U6: both exempting genres need cited evidence.**

  A claim of `literary` or `verbatim` without cited `genre_evidence` falls back
  to `expository`. A `verbatim` claim must also cite at least 2 of the four
  `GENRE_SIGNAL_FAMILIES`. At least 1 of them must be STRONG. A STRONG family is
  in `STRONG_GENRE_SIGNALS` (`timestamp_matches`, `transcript_heading`).

  This is a deliberate compensating control. It is not a duplicate check. Two of
  the four families (`speaker_label_lines`, `disfluency_tokens`) **over-count on
  ordinary memos by design**. `Note:` reads as a speaker label. `like` reads as a
  disfluency.

  We could tighten those regexes, but then we risk a miss on real transcripts.
  Instead, the design lets them over-count and blocks the false exemption at the
  guard. A board memo cites only the two weak families. It fails the STRONG
  requirement and stays gated.
- **U7: the rewrite-proposal condition keys on `verbatim` WITH evidence.**

  The condition does not key on a genre that `evaluate()` may discard. Loop rule 7
  (`_gate_action_post_cap`) dispatches a rewrite only when the *resolved* gate
  status is `FAIL` with `rewritable_remaining > 0`.

  Genre resolution (with the U6 evidence check) happens **before** the loop tests
  the proposal condition. So the loop never dispatches a rewrite against a genre
  that `evaluate()` would discard. It never dispatches a rewrite against a null
  rewrite proposal.

## Consequences

- The verdict lattice gains a fourth input that is not a tier. `decide(gate=None)`
  is a pure no-op that keeps every pre-gate fixture. This is why we could add the
  gate without a fixture re-baseline.
- The loop vocabulary grows from five to seven actions (ADR-001 amended). Every
  iteration re-scans. The cost is one extra scan for each iteration. In return, we
  get a guarantee: no rewrite adds a rhetorical question that nobody sees.
- We explicitly accept one residual. The U6 guard checks that the adjudicator
  **cited** evidence. It never checks that the cited counts are **true**. An
  adjudicator that fabricates a `timestamp_matches` count is not caught.

  The spec's Risks section states this, and we accept it. The compensating control
  is the two-family STRONG requirement. It is not a cross-check against the output
  of `genre_signals()`, which `evaluate()` never reads.
- **Auto-detection of `literary` covers only the form that the excerpt shows.**

  The genre `verbatim` has deterministic whole-document signals
  (`genre_signals()`). The genre `literary` has none. The adjudicator sees only
  excerpts, never the whole document. A reflective memoir sentence and a memo
  sentence look the same at the sentence level.

  So the adjudicator claims `literary` **only** from unmistakable literary form in
  the excerpt itself: verse lineation or a screenplay slugline. Creative work in
  ordinary prose (memoir, essay, novel narration) defaults to `expository`. The
  `--genre literary` CLI override exempts it deterministically. The adjudicator
  does not infer it.

  This limit is deliberate and conservative. The failure direction is over-gating
  creative prose that the user did not flag. It is never under-gating an
  expository document.

  A live smoke test found the problem. A poem (visible verse form) and a memoir
  (prose, no visible form) got different adjudications from the same prompt. The
  fix makes the boundary explicit. Before, each excerpt got its own improvised
  answer. Doc contract `c20` pins the limit.

### Implementation deviations from the spec

- **`SPEAKER_LABEL_RE` gained an optional leading `[HH:MM:SS]` timestamp
  prefix.**

  The spec's regex matched a speaker label only at the start of a line. The
  deviation has a reason. A real transcript export from Otter, Zoom, or Granola
  often has no markdown transcript heading. Without the prefix, such a transcript
  would cite only `timestamp_matches`, which is a **single** family. That fails
  the two-family guard of U6.

  Then U6 would reject `verbatim`. The gate would enforce on a genuine transcript.
  The humanizer would rewrite the own words of a speaker. Decision 2 exists to
  prevent that exact falsification.

  Now a speaker label can carry a leading timestamp. So a transcript with no
  heading can cite both `speaker_label_lines` and `timestamp_matches`, and it
  stays exempt. The deviation does **not** weaken the deliberate memo over-count.
  `Note:` still matches `speaker_label_lines`. The count stays 4 on the reference
  memo. Neither STRONG family fires, so the gate still checks a memo.
- **`scan()` slices the RAW line for both the excerpt text and the identity
  hash.**

  An earlier implementation sliced the excerpt from the **masked** line (inline
  code and URLs blanked). It still hashed the raw content. That erased the subject
  of a question from the text that went to the judgment agent.
  `` Does `foo()` return None? `` became `Does         return None?`. Two such
  excerpts looked the same, but they hashed **apart**, because the hash still saw
  the raw bytes.

  Span **discovery** still runs on the masked line. A `?` inside inline code or a
  URL must not start a candidate. But the excerpt and the id both come from the raw
  line, so they can never disagree.
