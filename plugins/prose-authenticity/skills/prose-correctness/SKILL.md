---
name: prose-correctness
description: Deterministic spelling and mechanical-grammar check for prose that already exists. Use before shipping a document — a PRD, ADR, spec, README, release note, or any deliverable — to catch misspellings, doubled words, and article disagreement that the AI-likelihood and STE checks do not look at.
---

# Prose Correctness — Deterministic Check

Run `${CLAUDE_PLUGIN_ROOT}/lib/correctness_checker.py` over a document
that already exists. This check measures whether the prose is **correct**. The
detector tiers measure whether a machine wrote it, and the STE checker measures
whether it obeys a rule set. The three questions give three verdicts on three
separate scales, because a shared scale would hide one measurement behind
another. See ADR-010.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/lib/correctness_checker.py <document>
```

Exit codes: `0` clean, `2` at least one fault, `3` the file or config could not
be read. Exit `1` is reserved for a future WARN rule and no rule emits WARN.

## What it finds

| Rule | Fault |
|---|---|
| C1 | a token on the curated misspelling list |
| C2 | the same word twice in a row, within one line |
| C3 | `a` or `an` disagreeing with the word that follows |

## What it does not find

It does not parse grammar. It will not catch a correctly-spelled wrong word —
`form` for `from` — unless that pair is on the list. **It catches only
misspellings someone has already written down**, which is the cost of not
asking whether a word is in a dictionary. A general dictionary was measured at
413 findings and 0 genuine over this repository's prose.

**C3 knows only the initialisms it has been told.** English picks the article
by sound. The checker sees spelling. Three closed lists in
`config/correctness.yaml` bridge that gap. A word outside them drops through
to a vowel test, which reads the first letter and nothing else. It fails
whenever a word does not sound the way it looks.

A sweep of every tracked document here found no false C3 fault. That is one
day's prose, not a promise. **Fix a wrong C3 report with a new row, because a new
rule adds a new source of false reports.**

ADR-011 says why a rule that reads capitals as initialisms costs more than
the gap it closes.

**A PASS is not proof the whole document was read.** An inline code span
that wraps a line break makes the extractor blank the next line's prose. It
exposes that line's code instead. The line then reaches no rule — not C1, not
C2, not C3, not the STE checker. Its faults stay invisible and the document
still scores PASS.

Up to 72 of this repository's 1,570 tracked files hold a line that opens such
a span. ADR-011 records the defect. Nobody has fixed it. A gate that reads exit 0 as proof
of correct prose is wrong for this check, so wire it into no such gate.

**This check does not replace Word.** Exporting to `.docx` and running Word's
spelling and grammar checker remains a legitimate review step, and it is how
this gap was found.

## Adding an entry

Edit `${CLAUDE_PLUGIN_ROOT}/config/correctness.yaml`. Every key must be
wrong in **every** register this repository writes — the test suite enforces
that against two real documents, and it will reject a key that appears as a
correct word in any of them.

To correct a C3 report, add a row to `c3_initialisms`. The lookup folds
case, so the casing of the key does not change what it matches. Write it the
way a reader says it. Two keys must stay different after folding — `SOT`
beside `SoT` fails the suite.

Set the value to `a` or `an` as a reader says the word aloud. Then add the
phrase to `C3_TABLE_PHRASES`, in the unit tests. The suite matches the two
sets exactly, so a row with no phrase fails.

`uniformity` opens with a vowel letter and a consonant sound. Such a word
goes in `c3_long_u` instead. Add the word, because a pattern also matches words that read differently.

`uniform` is `uni` plus `form` and takes `a`. `uninitialised` is `un` plus
`initialised` and takes `an`. No spelling rule separates them.
