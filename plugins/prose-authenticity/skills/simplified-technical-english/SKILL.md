---
name: simplified-technical-english
description: ASD-STE100 Simplified Technical English drafting discipline — load while WRITING any technical artifact so it is born conformant. Use when writing PRDs, ADRs, specs, technical documentation, issues, pull request descriptions, acceptance criteria, commercial terms, or legal sections.
---

# Simplified Technical English — Drafting Discipline

Apply while writing. `${CLAUDE_PLUGIN_ROOT}/lib/ste_checker.py` checks
text that already exists. This skill keeps new text from needing the check.

Use this skill together with `prose-authenticity:anti-ai-tells`. Neither one
is enough alone. STE governs the sentence: vocabulary, syntax, length, and
ambiguity. The tells checklist governs the stance. You can write
posture-perfect prose that breaks every STE rule, and you can write
STE-perfect prose that hedges and apologises in every paragraph.

## The 12 applied rules

| Rule | Applied as |
|---|---|
| One word, one meaning | Each term has one meaning in the document. No word changes sense between sections. |
| Approved vocabulary | Simple, common words. Technical names are kept when no simple word exists. |
| Short sentences | 20 words maximum for instructions. 25 words maximum for descriptions. |
| Short paragraphs | 6 sentences maximum. |
| Active voice | "I will write the model." Not "the model will be written." |
| Present tense | Use the present tense when possible. |
| One idea per sentence | Put two ideas in two sentences, not joined by a comma or a dash. |
| Articles | Always use "the", "a", or "an". |
| Noun clusters | 3 words maximum. |
| No jargon | No idioms. No metaphors. No industry shorthand. |
| Consistent terms | The same thing has the same name every time. |
| Vertical lists | Use lists for complex information. |

## Where STE applies

| Surface | Discipline |
|---|---|
| PRDs, ADRs, specifications, technical documentation | STE + tells |
| Issues, bug reports | STE + tells |
| Pull request descriptions, pull request review comments | STE + tells |
| Acceptance criteria, success measures, input rules | STE + tells |
| Enumerated deliverables, scope lists, timelines | STE + tells |
| Commercial terms, IP, legal sections | STE + tells |
| Argument sections, reflections, executive narrative | Tells only |
| Brand copy, sales copy, marketing copy | Tells only |
| Text quoted from a person | Neither |
| Code comments, docstrings | Neither |

STE applies where a wrong reading is a defect. Tells-only applies where
persuasion is the job.

## The conflict rule

Tell 7 warns against uniform sentence length. The STE cap commands short
sentences. Where they disagree, **vary the length on purpose**. A 19-word
sentence next to a 4-word sentence satisfies both. A page of 11-word
sentences satisfies one.

## Banned vocabulary

This repository owns these lists. They are not the ASD dictionary, which ASD
holds the copyright to. `config/ste.yaml` holds the same lists, and a
documentation contract keeps the two in step.

**Part A** — single-token corporate vocabulary. An exact match, so the
checker FAILs on it.

- leverage
- seamless
- synergy
- innovative
- AI-powered
- imperative
- non-negotiable
- robust

**Part B** — multi-word contextual phrases. A judgment-dependent match, so
the checker WARNs.

- specification variance
- binding constraint on throughput
- return edges
- conditions of satisfaction
- productivity multiplier
- the whole board
- the constraint moves downstream
- blueprints persuade nobody
- agentic SDLC

**Exempt terms** — repository product and plugin names. The checker flags them at no severity, even when they also appear above.

- agentic SDLC

## Abbreviations

A period after a listed abbreviation (`e.g.`, `i.e.`, `Dr.`) does not end a
sentence. Without this list, the checker would read "e.g." as a phantom
sentence break. That change stops the break from inflating the sentence
count and the length spread. The list lives in `config/ste.yaml`, under the
key `sentence_abbreviations`.

Some abbreviations end real sentences too (`etc.`, `No.`, `Inc.`, `Ltd.`).
Those live under the key `sentence_abbreviations_ambiguous`. The period after
one of them closes the sentence, unless the next character is a lowercase
letter or a digit. A single-letter initial follows the same principle by
position: "J. Smith" is one name, and "We prefer option A." is one sentence.

## Guardrail

A quotation is exempt from STE and the tells checklist in two cases. The
first is a markdown block quote. The second is a zone marked with
author="human". An inline quotation in running prose is not automatically
exempt. This repeats the guardrail in
the skill `prose-authenticity:anti-ai-tells`.
