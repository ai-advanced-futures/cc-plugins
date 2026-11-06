# ADR-010: Prose correctness as a third axis, and the release-gate adjudication that shipped it

**Status:** Accepted
**Date:** 2026-08-18

## Context

The plugin already answers two questions with two separate verdicts. ADR-006
settled that shape. The detector tiers score whether a machine wrote the text.
The STE checker scores whether the text obeys a rule set. The two never share a
scale. Taking the mean of them would hide both.

Correctness is a third, distinct question: is the prose right? It gets the same
treatment as its precedent. It has its own module, its own verdict, and its own
config file. It joins neither the detector composite nor the STE report.

`lib/correctness_checker.py` adds three deterministic rules to a plugin that
already carries the AI-detection tiers and the STE checker. The rules are C1
(misspellings), C2 (doubled words) and C3 (article agreement).

This ADR is also the adjudication record of the gate. Every rule ran over the
eight corpus documents. For the count beside each corpus result, every rule also
ran over every tracked markdown file in the repository.

### The measurement that killed the dictionary design

The first design for this check used a general-purpose spellchecking
dictionary. The dictionary sat behind the prose-extraction seam of the STE
checker. It ran over 14,816 words of real repository prose. It produced **413
findings and 0 genuine ones**. The seam removes code. It cannot remove
technical vocabulary from running prose, and a dictionary trips on that
vocabulary.

Two mechanical causes made the number this large. First, the `en` dictionary of
`pyspellchecker` lacks 35 of the 52 ordinary modern English words tested. Some
examples are `workflow`, `filesystem`, `runtime`, `timestamp`, `metadata`,
`deliverables`, `refactor` and `changelog`. Second, the dictionary is US-only,
but the repository writes British English. It flags 22 of 26 British spellings,
including `behaviour` and `generalising`. No `en_GB` dictionary ships with it.

A dictionary of correct words cannot work here. It needs hand-curation of most
of a technical vocabulary. So this check does not use one. It fires only on
words that are definitely wrong. It uses a curated misspelling list that maps
known misspellings to their corrections. It never asks whether a word is in a
dictionary at all.

### `checked_spans` moves to a shared module

Two checkers now need the same prose extraction. The extraction removes code
and exempt zones. Its line numbers stay true to the raw file. `checked_spans`
moves from `lib/ste_checker.py` to a new `lib/prose_spans.py`. `ste_checker`
re-exports the name. No existing caller or test changes.

One behaviour changes with the move. It is a real STE bug fix that rides
alongside the extraction. It is not a side effect of the extraction.
`checked_spans` had no YAML frontmatter handling. The `---`-delimited
frontmatter block of a document reached the checkers as prose. It merged into
the surrounding sentence.

`prose_spans` now strips a leading frontmatter block by delimiter, not by
parsing. Of the 693 tracked files that open with `---`, 6 hold a block that is
not a YAML mapping. All 693 have a closing delimiter. So delimiter detection
handles every one of them. It does not over-match the 5,408 mid-document lines
of `---` or longer that the repository also holds. The measurement covers all
693 files that carry frontmatter. **748 findings disappear, 277 documents change
their finding count, and 50 documents change verdict.**

## Gate run

> **The C3 numbers in this section are the v0.4.0 gate run. They are
> superseded.** ADR-011 re-measured C3 at v0.4.1. It reports **3** findings
> repository-wide. All three are correct. Every one of the 54 below was false.
> Two facts from that re-measurement belong here. First, the 54 had already
> drifted to **59** before a line changed. Another change merged after the gate
> run and brought five more findings. A repository-wide count is stale on the
> next merge that adds prose. Second, the "obvious next step" that this section
> names was taken, along with three others. The numbers for C1 and C2 below
> still stand.

The gate ran over the eight documents of the corpus. Each document ran
individually through `correctness_checker.py`. Every document scored `PASS: 0
findings` for all three rules. The corpus is clean. After the port into this
repository, the test of the corpus gate runs over 2 documents: the README and
ADR-009.

Repo-wide, every rule ran over all 1,527 tracked `*.md` files (`git ls-files
"*.md"`). The run used `check()` directly, not the CLI. So it needed no
subprocess for each file. The counts are C1 0, C2 6 and C3 54.

The C3 count was **60 at the gate run and is 54 now.** A post-gate review found
a fault. `_expected_article` consulted `c3_initialisms` for the whole token
only. Its hyphen and possessive fallbacks reached `c3_sounded_h` and
`c3_long_u`. They never reached the table. So every hyphenated initialism
dropped through to the vowel test, even when its head was already a table row.

That raised a FAIL on `an STE-plus-tells` in ADR-008 of this plugin. It also
raised a FAIL on `a UUID-scoped` in source document 1. The fault was a one-line
logic error. It was not a limit of the rule. So the team fixed it and did not
record it. The six hits it accounted for are gone. The numbers throughout this
section are the post-fix ones. The fix is not gate-tuning. The gate cuts a rule
that produces a **false positive in the corpus**. The corpus was clean and
remains clean.

### Adjudication table

| Document | rule | line | excerpt | verdict | decision |
|---|---|---|---|---|---|
| (all 8 corpus documents) | C1 | n/a | n/a | n/a, zero findings | ship, unproven |
| (all 8 corpus documents) | C2 | n/a | n/a | n/a, zero findings | ship, unproven |
| (all 8 corpus documents) | C3 | n/a | n/a | n/a, zero findings | ship, unproven |
| source document 2 | C2 | 589 | `phase Phase` | genuine | ship |
| source document 3 | C2 | 379 | `to to` | genuine | ship |
| source document 4 | C2 | 345 | `if if` | genuine | ship |
| source document 4 | C2 | 346 | `of of` | genuine | ship |
| source document 5 | C2 | 65 | `company company` | genuine | ship |
| source document 6 | C2 | 1 | `company Company` | genuine | ship |
| source document 7 | C3 | 298 | `A and` | false | ship, known-imprecise |
| source document 8 | C3 | 65 | `An n` | false | ship, known-imprecise |
| source document 9 | C3 | 47 | `an mc` | false | ship, known-imprecise |
| source document 10 | C3 | 5 | `a URI` | false | ship, known-imprecise |
| source document 1 | C3 | 64 | `a UUID-scoped` | false | **fixed**: head is a table row |
| source document 11 | C3 | 23 | `A ubiquitous` | false | ship, known-imprecise |
| source document 12 | C3 | 87 | `an SoT` | false | ship, known-imprecise |
| (48 further C3 repo-wide hits) | C3 | n/a | n/a | false | ship, known-imprecise |

A hand read checked every one of the repo-wide hits of C3 against its source
line. All 54 that survive are correct English that the rule flagged by mistake.
None is a genuine article-agreement fault. They fall into six residual classes
(counted, not estimated):

| count | class | examples |
|---:|---|---|
| 26 | unlisted **UPPERCASE** initialisms | `an SDLC` ×6, `an LOI` ×4, `an HTML` ×2, `an FAQ` ×2 |
| 9 | single letter labels | `an R` ×5, `an M` ×2, `An n`, `an L` |
| 9 | hyphenated compounds whose head is **not** a table row | `an f-string` ×4, `an L-` ×2, `an HTML-comment` |
| 5 | **lowercase-written** initialisms and module names | `an mc` ×2, `A and` ×2, `an sdlc` |
| 4 | morphological variants of `u-` | `a uniformity`, `a universe`, `A ubiquitous` ×2 |
| 1 | mixed case | `an SoT` |

The hyphenated class no longer means that the fallback cannot see the table. It
now means that the head is not in the table. `an HTML-comment` survives because
`HTML` was never a table row. `HTTP` is a row. Adding the missing rows would
remove most of what remains. That is the obvious next step for anyone widening
C3.

> **All six classes above are closed as of v0.4.1 (ADR-011).** ADR-011 added
> the rows, read the letter names, folded the lookup and listed the `u-` words.
> The table did not name one class: `A and B converge`, filed above under
> "lowercase-written". The rule misread a label as an article. It was not a
> casing problem at all.

All six repo-wide hits of C2 are genuine. They sit in three documents.
These widen the corpus for a future round: source documents 4, 5 and 2.

### Gate outcome

| rule | corpus findings | repo-wide findings | branch | outcome |
|---|---:|---:|---|---|
| C1 | 0 | 0 | zero corpus, zero repo-wide, so unproven | ship, unproven |
| C2 | 0 | 6, all genuine | zero corpus, non-zero repo-wide, so unproven and known-imprecise | ship |
| C3 | 0 | 54, all false | zero corpus, non-zero repo-wide, so unproven and known-imprecise | ship |

The row of C3 is the v0.4.0 outcome. At v0.4.1 it reads `0 | 3, all genuine`
(ADR-011). The corpus stayed clean through every change. So the gate never fired
and no rule was cut.

No rule was cut. The corpus is clean for all three rules. No rule gives a false
positive inside it. The condition that would have cut a rule never fired. This
task left `lib/correctness_checker.py`, `config/correctness.yaml` and
`tests/unit/test_correctness_checker.py` unchanged.

## Decision

Ship `lib/correctness_checker.py` as a fourth Python tool in the tool-belt of
the plugin. The release gate below controls the release. C1, C2 and C3 ship.
C4, C5 and C6 are cut.

**The release gate.** Before this check ships, every rule runs over the eight
corpus documents. A person adjudicates every finding by hand and records it in
the table above. The release cuts a rule that does not reach 0 false positives
inside the corpus. Nobody tunes that rule until it looks acceptable.

The gate did its job on this branch. An earlier round of the same rules
produced 18 findings and 0 genuine ones. C1 fired zero times, even though it
carries the whole safety guarantee. Four of the 8 corpus documents failed. After
the rule fixes below, C2 and C3 reach 0 corpus findings and pass. C6 does not
pass, and the release cuts it.

**C4, C5 and C6: measured and cut, not overlooked.**

- **C5 (spacing faults) cannot run on this seam at all.** The cause is
  structural. It is not fixable.
  - `checked_spans` replaces inline code with a single space. That is its job.
    The subject matter of C5 *is* whitespace. So the seam invented 798 of the
    968 repo-wide findings of C5, or 82%.
  - On the `README.md` of the plugin, raw prose produced 0 findings for C5 and
    the seam produced 114. A rule cannot measure an artifact of its own input
    pipeline.
- **C4 (sentence capitalisation) produced 107 findings, all false.** Its only
  escape hatch is all-or-nothing. A dictionary check would suppress either all
  107 or none. Technical prose legitimately opens sentences with lowercase
  identifiers.
- **C6 (unmatched brackets) produced 49, then 5, then 4 findings across three
  rounds. Every one was false.** Reaching 0 would need two mechanisms that this
  design would have had to invent.
  - First, C6 needs its own paragraph function. `ste_checker.paragraphs`
    splits on `BULLET_RE` by construction. A hard-wrapped continuation line
    that begins `+ ` therefore orphans a bracket pair. That accounts for 2 of
    the 4 residual findings. That function cannot change. Its docstring
    records that merging list items produced false paragraph-length failures in
    the STE checker.
  - Second, C6 needs a second input stream. `INLINE_CODE_RE` matches single
    backticks only. A double-backtick span therefore leaks its brackets. That
    accounts for the other 2 residuals. The fix is `zone_parser.code_mask`. But
    `rule_c6(prose_lines, cfg)` has no raw source to give it.
  - Swapping `code_mask` into `prose_spans` instead changes 212 STE findings
    across 57 documents and flips 7 verdicts. That is a second repo-wide
    behaviour change that rides on this one.
  - This rule has never once produced a genuine finding. Two new mechanisms for
    it are exactly the tuning that the gate exists to forbid. This ADR records
    both fixes for whoever revisits C6.

**The `checked_spans` extraction and the frontmatter fix that rides with it.**
The Context section above records both. It gives three measured numbers: 748
findings disappear, 277 documents change count and 50 documents change verdict.

**Vendoring the dictionary of `codespell` is future work.** It depends on a
measurement. First, run the register filter over all of its roughly 80,000
entries. No entry may be a correct word in any register that this repository
writes. No British spelling may appear as a key. Then measure the result.

Skipping that measurement would reintroduce the dictionary failure of round 1 in
a new form. Nobody has measured whether the dictionary of `codespell` already
honours the register invariant. `codespell` is not installed. There is no
network access to install it.

**The dictionary tier and LanguageTool are future work. They are not opt-in
tiers.** An earlier design put both behind "an explicit
consent flag, exactly as the `api` detector tier already works through
`api_consent`".

That sentence named no config key, no CLI flag, no function and no finding
shape. It named no exit-code behaviour for the case where the user gives consent
and the tool is absent. Nobody could plan it. Nobody could test it.

A dictionary tier needs a British-English dictionary that `pyspellchecker` does
not ship. It also needs a curated project dictionary. Round 1 measured 123
distinct unknown-but-correct terms across the eight corpus documents.
LanguageTool is the only offline tool that genuinely approximates the grammar
engine of Word. It is either a Java distribution of roughly 200 MB or a hosted
API.

Either one collides with the stated posture of this plugin: no LLM, no network,
and a two-line CI requirements file. Cutting both from v0.4.0 makes that posture
true rather than aspirational. With no optional tier shipped, this check adds no
runtime dependency at all.

**CLI-and-skill wiring, no `/check` change.** v0.4.0 ships a CLI and its own
skill. It does not touch `commands/check.md`. This matches the `ste_checker`
precedent exactly. 

`ste_checker` runs only from `skills/simplified-technical-english/SKILL.md`. It
appears as documentation in `README.md`, the container diagram and its own ADRs.
It does not appear in `/check` at all.

`/check` remains the AI-likelihood pipeline. Correctness is a third axis with
its own verdict. Folding it into a command whose report is about AI-likelihood
would re-merge exactly what ADR-006 kept apart.

## Consequences

A caller who wants all three answers (AI-likelihood, STE conformance and
correctness) runs three separate checks. The caller reads three separate
verdicts. That is the accepted cost of the same reasoning that ADR-006 already
accepted for two verdicts. One number cannot carry three measurements. Taking
the mean of any of them would hide the others.

**This is a mechanical check with stated limits.** It does not parse grammar. It
does not catch a correctly-spelled wrong word, such as `form` for `from`, unless
that exact pair is on the curated list. It catches only misspellings that
someone has already written down. That is the cost of never asking whether a
word is in a dictionary.

It does not replace a human editorial pass. It does not replace the own
spelling and grammar checker of Word. Exporting to `.docx` and running the
checker of Word remains a legitimate review step. That step found both the
frontmatter gap and the original dictionary failure.

C4, C5 and C6 stay cut. Whoever revisits them must build the mechanisms that this ADR names. That person
must also re-run the release gate to prove the fix before shipping it.

The starter misspelling list in `config/correctness.yaml` is small on purpose.
It will grow through use. `codespell` itself started the same way.

Every future addition must pass the same register clause as the starter list. No
key may appear as a token in any of the eight corpus documents. A mechanical
check enforces that clause. It is not a judgment call.
