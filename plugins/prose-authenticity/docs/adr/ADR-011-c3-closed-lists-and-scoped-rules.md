# ADR-011: C3 widens by closed list, and a general rule only where the ambiguity cannot arise

**Status:** Accepted
**Date:** 2026-08-19

## Context

C3 shipped in v0.4.0 at **FAIL** severity. It was wrong every time it fired.
The gate run of ADR-010 recorded 54 findings across the repository, all false.
It shipped the rule because the eight-document corpus was clean.

Re-measured on `main` at `cae1ba76`, the count was **59, not 54**. The five
extra findings came from another change. That change merged after the gate run
and brought five `a uniformly` findings with it.

That is the first thing this ADR records. **A repository-wide count in a
document is stale on the next merge that adds prose.** The number in ADR-010
was true when written. It was false five weeks later. Nothing signalled the
change.

The cause of the 59 findings fits in one sentence. **English picks the article
by SOUND. C3 read SPELLING.** `_expected_article` tried three closed lookups.
Then it fell back to `word[0] in "aeiou"`. The fallback produced every finding.

The tempting fix is a general rule. An all-caps token is an initialism, so the
rule takes the name of its first letter. `R` is `ar`, `M` is `em` and `H` is
`aitch`. So `an SDLC`, `an R` and `an HTML` all resolve. The rule would have
cleared most of the 59 in one edit.

The rule is also wrong. The shipped test suite already said so.
`test_the_table_is_closed_not_a_rule` pins `a HEAD start`. `HEAD` is the word
`head` in capitals. H is `aitch`, so the rule would demand `an HEAD`. `MOAT` is
the same.

**Nothing mechanical separates an initialism from a word written in capitals.**
That is why `c3_initialisms` is a closed table. A first-letter rule silently
re-opens the bug that the table exists to prevent.

The same shape appears in the `u-` class. `uniform` is `uni` + `form` and takes
`a`. `uninitialised` is `un` + `initialised` and takes `an`. Both open `u-n-i`.
A `uni-` prefix rule clears seven of the nine. It breaks `an unimportant`,
`an unintended` and `an uninterrupted`.

## Decision

**Widen C3 by closed list. Add a general rule only where the ambiguity behind
the closed list cannot arise.**

Four changes follow from that decision. The list gives them in the order of
their making.

1. **A letter-name rule scoped to ONE-CHARACTER tokens.** The letters whose
   names open on a vowel sound take `an`. They are `A E F H I L M N O R S X`. A
   single character has no word reading. So the ambiguity between an initialism
   and a word cannot occur at this length. That ambiguity kills the all-caps
   rule.

   The change removed the `F: "an"` row from the table. The rule returns `an`
   for `F` and runs below the table. So the row was redundant. Its deletion
   changed nothing. That is the definition of an untestable config row.

   The criterion is narrow on purpose. A row goes when a rule BELOW it in the
   same chain returns the same answer for the same reason. `ADR`, `API` and `ID`
   also coincide with the final vowel test. They stay. That agreement is a
   coincidence of spelling. It is not a rule that subsumes them.

   It would end the moment the fallback changed. `F` was different. The
   letter-name rule answers `an` for `F` BECAUSE `F` is `ef`. That is the same
   reason the row existed.

2. **Fifteen rows added to the closed table.** Thirteen take `an`: SDLC, LOI,
   NDA, HTML, SMB, MQL, MVP, HCM, MC, ML, SP, SoT and FAQ. Two take `a`: URI and
   UTC. The table already held HTTP and no HTML. That is the shape of the whole
   gap. The first pass seeded the table from whatever it happened to hit.

   FAQ is the one judgment call. `eff-ay-cue` takes `an` and `fack` takes `a`.
   Both are attested. The config marks FAQ as a convention, not as a spelling
   fact.

3. **Case-folded lookup.** Both sides of the table lookup fold to lower case. So
   `an mc`, `an sdlc` and `an mcp-server` reach the table. This contradicts the
   v0.4.0 docstring. The docstring claimed that folding would "turn the table
   into an all-caps rule, which is what fires on `a HEAD start`". That does not
   follow.

   A folded lookup is still a lookup. `HEAD` is absent from the table under
   every casing. **A closed table keeps `HEAD` safe. Case sensitivity does
   not.** The old wording actually describes a different hazard. That hazard is
   folding one side only.

4. **A conjunction guard.** A match that ends in `and` or `or` is two tokens that
   the regex adjoined. An example is `A and B converge`, where `A` is a label.
   The existing uppercase-label guard cannot reach it. That guard fires only
   mid-sentence. This capital opens the line.

   The guard has two conjunctions, not seven. The cut is measured, not
   stylistic. The guard needs to suppress a match only where the fallback would
   otherwise be wrong. The fallback reads the first letter. `and` and `or` open
   on a vowel. So the fallback asks `A and B` to become `an and`.

   `nor` and `but` open on a consonant. They never produced a finding to
   suppress. A first draft listed all four. The two extra members changed only
   the strings `An nor …` and `An but …`. Both are REAL article faults, silently
   swallowed.

   `for`, `so` and `yet` stay out for a second reason. Each also reads as
   something that legitimately follows an article (`a for loop`,
   `a so-called fix`, `a yet-unnamed rule`).

## Measurement

The sweep ran repository-wide through `check()` directly. It covered the 1,570
tracked `*.md` files at `cae1ba76`. The team re-measured the final row on the
branch. The branch tracks 1,571 files, because this ADR is the extra file:

| stage | findings | false | true |
|---|---:|---:|---:|
| `main` at `cae1ba76` | 59 | 59 | 0 |
| after the letter-name rule | 45 | 44 | 1 |
| after the fifteen table rows | 16 | 15 | 1 |
| after case folding | 14 | 11 | 3 |
| after the long-u words | 5 | 2 | 3 |
| after the conjunction guard | **3** | **0** | **3** |

The corpus stayed at 0 findings at every stage. So the release gate never fired
and no rule was cut. The gate cuts on a false positive **inside** the corpus.
That condition was never met.

**The three surviving findings of C3 are its first true positives.** Every one
is a real article fault in a document that belongs to another workstream. This
work left each one in place:

| Document | line | phrase in the document | correct form |
|---|---:|---|---|
| source document 1 | 343 | `a R9 wire` | `an R9 wire` |
| source document 2 | 44 | `a mc code path` | `an mc code path` |
| source document 3 | 90 | `a sdlc-… CLI crash` | `an sdlc-… CLI crash` |

The second sits three lines above `an mc` in the same document. That is its own
evidence.

### A limit on the sweep itself, found while writing this ADR

Running the checker over this document reported `an URI` and `a HTTP`. Neither
phrase appears in it. The cause is one layer down, in `prose_spans.checked_spans`.
It is not a C3 fault.

**An inline code span that wraps a line break inverts the parity of the next
line.** The extractor does not carry inline-span state across lines. So it
blanks the prose and exposes the code. This is the minimal case:

```
Text with `A LONG
SPAN` then `an` and `URI` words.
```

Line 2 extracts as `SPAN an URI`, then a backtick, then `words.`. The words
`then`, `and` and `words` are gone. The extractor fails in both directions at
once. Real prose is hidden from every rule. Code content produces findings.

A backtick-parity scan sets an upper bound. At `cae1ba76`, at most **72** of the
1,570 tracked files hold a line that opens a span without a close. On this
branch, at most 73 of the 1,571 do. This repository's own `CLAUDE.md` is
among them.

This qualifies the measurement above. The sweep read every file. But in those
files it did not read every line. So "no false positives" means none in the
prose that the extractor surfaced.

The fault also affects C1, C2 and the STE checker equally. That is why this ADR
records it and does not fix it. It belongs to `prose_spans`. It needs its own
measurement across all four rules. Mixing it into an article-agreement change
would hide it.

## Consequences

**C3 is now right every time it fires. It was wrong every time before.** That
changes what the rule is for. At FAIL severity it was a rule that a consumer had
to know to distrust. It is now a rule that a consumer can act on.

**The count in this ADR will go stale, exactly as the count in ADR-010 did.** It
is a measurement at `cae1ba76` plus this branch. It is not a standing property.
Anyone who cites it should re-run the sweep. The sweep is twenty lines over
`git ls-files "*.md"` that call `check()`. Do not quote the table.

**C3 knows only what people have told it. This is now stated on the invocation
surface, not only here.** That was a v0.4.0 follow-up. The rule shipped at FAIL
with 54 false positives. An ADR disclosed them. Nothing disclosed them where a
consumer of exit code 2 would look.

**A future editor will want the general rule.** The all-caps rule and the `uni-`
prefix rule are both attractive. Both are wrong. Two tests pin them. Each test
fails when someone installs its rule:
`test_the_letter_name_rule_stops_at_one_character` and
`test_un_plus_a_vowel_is_not_a_long_u_word`.

Proving that the first test fires took two attempts. The obvious mutation left
it green. `VOWEL_SOUNDED_LETTERS` was a string, and `in` on a string is
substring containment. So `"HEAD" in "AEFHILMNORSX"` is False. The mutant
answered `a` for every multi-character token.

**An invalid mutation that makes some other test fail reads as a live guard.**
The constant is now a frozenset. That also closes the real hazard behind it:
`"MN" in "AEFHILMNORSX"` is True.

**The table now needs its folded keys to stay unique.** `SOT` added beside `SoT`
would make the surviving value depend on dictionary order.
`test_no_two_table_keys_fold_together` covers it.

**Every table row is exercised. The limit of that claim is measured, not
assumed.** `test_every_table_row_is_exercised_by_a_phrase` checks three things
against the live config. First, the row has a phrase, by set equality in both
directions. Second, the phrase contains the key of the row. So it exercises that
row and not some other token. Third, the config value sets the orientation of
the pair.

A first draft of this section said that the claim was "enforced rather than
asserted". The pre-PR semantic review disproved it by mutation. A
mutation that inverts `SP` to `a` AND swaps its phrase pair to match leaves the
suite green. That is not a hole to close. The table IS the specification.

So a coordinated edit of a spec and its test is a DECISION, indistinguishable
from a correction. No test can separate the two.

The guard does close the uncoordinated case. It catches four faults. A row has no phrase. A phrase has no
row. A phrase tests the wrong token. A config value changes on its own.

The sentence mattered because it is the shape of overclaim that this plugin has
now shipped four times. It is prose that reads as a guarantee over a test that
does not give one. This ADR records it here and does not reword it quietly.
