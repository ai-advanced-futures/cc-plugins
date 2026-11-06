# ADR-009: Zone markers in code contexts are suppressed by fences only

**Status:** Accepted
**Date:** 2026-07-31

## Context

`lib/zone_parser.py` read `ai-check:zone` markers from raw lines. It knew
nothing about markdown. A marker written as a documentation example looked the
same as a real marker. This caused two faults. We measured them on
`origin/main` at `267930c3`.

**Fault A, fail-closed.** `ZONE_START_RE.search()` and `ZONE_END_RE.search()`
match anywhere on a line. The malformed-marker guard fires on any line that
holds `<!--` and `ai-check:zone` and matches neither pattern. So an example
marker reached six error paths.

Two paths were live. The checker could not check its own design spec. It
could not check its own `SKILL.md`.

**Fault B, fail-open.** A well-formed example marker created a real zone. Such
examples usually carry `author="human"`. So the zone became an exempt
calibration zone, and the checker never checked its span.

One document held a fenced start-marker example, five banned words, and a
fenced end-marker example. It scored `PASS: 0 findings ... 1 exempt zones`.
The plugin's own `README.md` was an instance.

The fix needed knowledge that already existed one layer up.
`prose_spans.checked_spans` tracks fences at `prose_spans.py:101-112`. But it
calls `parse_zones` first, at `prose_spans.py:92`. So the parser fixed the
zone boundaries before any fence knowledge applied.

## Decision

Two faults need two mechanisms. Three earlier designs tried to use one
mechanism for both. Each design failed on a different case.

**Mechanism 1. Fenced regions suppress markers.** A marker is real if and only
if three things hold.

- It matches **in the raw source**.
- It matches **per line**.
- It does not begin inside a **closed** fenced region.

`fenced_line_numbers(src)` supplies the fenced lines.

**Mechanism 2. A code mask feeds the guard and nothing else.** The
malformed-marker guard tests substrings. So it needs a masked line.
`code_mask(src)` supplies it. The code never asks the mask what a marker is.

### The mask may never decide what a marker is

The mask replaces code characters with spaces. The marker patterns contain
`\s*` and `\s+`. So a mask can **create** a match that the raw source never
held:

```
raw:    <!--XXXXXXai-check:zoneYstartYname="a"Yauthor="ai"XX-->   -> no match
masked: <!--      ai-check:zone start name="a" author="ai"  -->   -> MATCHES
```

Suppose the mask decided if a marker exists. Then a document that exits 3
today could silently gain an exempt `author="human"` zone. A match against the
raw source makes this impossible. The mask can only suppress a marker. It can
never invent one.

### Matching is per line, never whole-source

`\s` matches a newline. So on a whole-source scan, `ZONE_START_RE` matches
**across** a line break. We verified this on the 2026-07-29 spec:

```
repr: '<!-- ai-check:zone\nstart name="…" author="…" -->'
```

That match is the wrapped prose that this change must stop from tripping the
guard. Per-line scanning keeps the main case fixed.

### Fences suppress, inline spans do not

A real marker is never inside a fenced block. A fence holds code. Zones
delimit prose. So suppression inside a fence is safe.

Inline backticks are ambiguous, because a real marker can share a line with
backticked prose. Three shapes break if an inline span may suppress a marker:

- A span within one line encloses a marker.
- A span opens on the marker line and closes on the next line.
- Stray backticks stand on each side of a real pair.

All three parse correctly today. The first two would raise "zone end without a
matching start". The third loses **both** markers.

Then `parse_zones` falls back to the implicit `whole_doc` / `ai` zone.
`get_baseline_zone` loses the calibration zone. `reassemble` splices a rewrite
over text that the author wrote and stands behind. It fails silently.

The risks are not equal. A lost real marker corrupts an author's text without
a warning. A failure to suppress an example is noisy and harmless.

An earlier revision argued that a real marker line carries no backticks,
because a zone name is `[A-Za-z0-9_-]+`. That argument is wrong. The character
set limits the marker, not the line.

**Accepted cost.** `SKILL.md:27` wrote a complete, valid marker inside inline
backticks. Nothing separates it from a real marker without a guess. So we
fixed the document, not the parser. The skill now states the convention:
always show a marker inside a fenced block.

### An unclosed fence suppresses nothing

A fence that never closes is literal text. It defines no region. The opener
scan resumes on the **next** line.

Two other rules would lose real markers silently. The first masks to the end
of the file, as `checked_spans` does for prose. Then one stray opener swallows
every marker below it. The second resumes at the end of the file. Then it
hides every later closed fence.

Unclosed fences are a documented condition, and they occur here.
`checked_spans` sets `meta["truncated_scan"]` for this case at
`prose_spans.py:134`.

The cost is this. An example marker inside an unclosed fence stays real. So
Fault B survives in a document that already has a markdown error. The failure
is noisy, not silent.

### The fence rule is CommonMark, not `ste_checker`'s

An earlier revision aligned the fence rule with `prose_spans.FENCE_RE`
(`prose_spans.py:12`). The aim was one definition in the plugin. That was
wrong.

`FENCE_RE` ignores run length. It closes on a line that carries an info
string. So an outer fence of four backticks closes on its first inner fence of
three backticks. This is the standard idiom for showing fenced markdown.

An example marker between the inner fences then falls outside every region. It
becomes a real exempt zone. Fault B would survive the fix in any document that
documents fenced markdown.

Correctness is more important than alignment. The plugin holds **three** fence
detectors, not two. The three differ:

| Axis | `zone_parser.FENCE_OPEN_RE` | `prose_spans.FENCE_RE` | `question_gate._FENCE` |
|---|---|---|---|
| closing run length | at least the opener's | ignored | ignored |
| info string on closer | not a closer | closes | closes |
| indent tolerated | `^ {0,3}` | `^\s{0,3}`, so a tab counts | any, the line is stripped first |
| marker character | must match the opener | must match the opener | ignored, either toggles |

`question_gate._FENCE` (`question_gate.py:112`, used at
`question_gate.py:187-191`) is the most permissive of the three. It is older
than this change, and this change does not touch it. But this ADR is the first
place in the plugin that compares the fence rules. An account that named only
two would have been wrong on the day we wrote it.

`checked_spans` mis-tracks nested fences. `_FENCE` treats an indented fence as
a fence, but `zone_parser` does not. Both defects existed before this change
and are outside its scope. We record both as follow-ups.

`code_mask` is likewise the **third** inline-code masker in the plugin.
`prose_spans.py:14` and `question_gate.py:113` both define the same
`` re.compile(r"`[^`]*`") ``. It handles neither a double-backtick span nor a
span that crosses a line break. `code_mask` handles both.

The same reasoning applies as for the fence table. This ADR is the first
document to compare these maskers. An account of the fence rules alone would
be incomplete. We leave the unification to a follow-up, not to this change.

### Inline spans open on a run of any length

An earlier revision limited inline-span openers to one or two backticks. The
reason: three or more backticks are fence syntax. CommonMark treats a run of
three in running text as an ordinary code span. Prose that shows marker syntax
inside triple backticks is common.

The limit left such prose unmasked, so the guard fired on it. That is a new
instance of Fault A, which the fix produced. We measured it across four
documents.

The wider rule risks nothing. A fence-opening line already bounds a span. So
the scan never reads the backticks of a fence as an inline opener. The mask
feeds only the guard. Too much masking can silence a guard that should fire.
But it can never lose, corrupt, or invent a marker.

## Consequences

Five call sites gain the fix: `ste_checker`, `question_gate`, `run_detectors`,
`reassemble`, and the command line of the parser.

`README.md` keeps its FAIL verdict. The verdict comes from banned-word
findings. The count of exempt zones drops from one to zero. `SKILL.md` and
three design specs move from exit 3 to a verdict.

An earlier draft of this ADR gave an exact finding count for `README.md`. The
count was correct when we measured it. It was false when this ADR shipped,
because the same commit added a "What's New" section to that README. Any prose
edit can invalidate such a count. So it does not belong in a durable record.

### Cost

`parse_zones` now makes three full passes over the document. Before, it made
one. We measured these times on this machine:

| Document | `fenced_line_numbers` | `code_mask` |
|---|---|---|
| this ADR's design spec, 568 lines | 0.0001 s | 0.0005 s |
| plugin `README.md`, 196 lines | 0.0000 s | 0.0002 s |

Both new passes are quadratic in the worst case. `fenced_line_numbers` slows
down when many openers never close. In the worst case, every line is an opener
with an info string. An info string disqualifies a line as a closer.
`code_mask` slows down when many inline backtick runs never close. In the
worst case, each line holds one run of a unique length. We measured:

| Shape | 500 lines | 1000 lines | 2000 lines | 5000 lines |
|---|---|---|---|---|
| all-unclosed fences | 0.022 s | 0.086 s | 0.356 s | 2.216 s |
| unique-length backtick runs | 0.051 s | 0.239 s | 1.154 s | — |

Four times the lines costs sixteen times the work, as we expect.

Both shapes need a document that is malformed on purpose. Real documents in
this repository cost under a millisecond. The humanize loop makes at most 13
`parse_zones` calls per run. The document size does not grow between
iterations. We accept the cost and do not optimise it. We record it so that a
future change that makes these passes hot has the baseline it needs.

No marker outside a closed fenced region changes meaning. Every zone that is
real today stays real, except in the four residuals below.

### Accepted residuals

A brute-force sweep covered 248,832 documents of five lines each. It compared
them against a CommonMark reference. It found no unnamed marker-loss shape, no
invented zone, and no corrupted zone span.

Four residuals remain. A test pins each one:

1. **Mis-paired fences.** An opener has no closer. A later fence line of the
   same character and enough length pairs with it. This suppresses a real marker between them. CommonMark agrees that this
   text is code content. The document is wrong.
2. **A real marker on a fence-opener line.** The parser skips it with the
   fence line.
3. **A fence indented four or more spaces.** It is not a fence. So an example
   marker inside it stays real, and Fault A survives. To detect indented code
   blocks, the parser needs paragraph context, because a list continuation
   line is also indented. The risk of masking a real list item is larger than
   the benefit.
4. **A fenced block inside a block quote.** The fence pattern anchors at the
   line start. So a `>` prefix defeats it. The parser never suppresses an
   example marker inside a block-quoted fence. So Fault B and its phantom
   `author="human"` zone survive.

Residuals 1 and 2 need a markdown error in the document. Residual 4 does not.
So it is the follow-up candidate: extend the fence pattern to tolerate a
block-quote prefix.

Residuals 1 and 2 are not always silent. The loud variants raise
`ZoneParseError` because the markers do not balance. They are the majority:
1,136 against 1,012 across the corpus of five-line documents.

The silent minority is what matters. `meta["truncated_scan"]` does **not**
mitigate it. We measured the canonical shape of residual 1. `truncated_scan`
is `False` while the human zone is gone.

## Alternatives rejected

- **Strip inline-code spans per line.** The backtick on the failing line is
  unclosed, because the document wraps in the middle of a span. A per-line
  stripper sees nothing to strip.
- **Bound a span against blank lines and fences.** Two unbalanced backticks
  with no blank line between them still bracket a real marker pair.
- **Also bound a span against marker lines, and cap it at one line break.** We
  removed each part in turn. The cap did the work. The marker bound was dead
  code. So the two tests that guard the bound would pass even if we broke the
  bound. The cap also made the fix depend on where a paragraph wraps.
- **Restore marker characters after masking.** This needs a whole-source scan
  to find them. That scan matches across the line wrap that this change must
  repair.
