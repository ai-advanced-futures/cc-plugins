# ADR-008: The discipline map and the tell-7 conflict rule

**Status:** Accepted
**Date:** 2026-07-29

## Context

STE and the checklist of anti-AI tells govern different layers. It is wrong to apply both to everything. The authors of STE wrote it for maintenance manuals, where ambiguity is a safety hazard. STE aims to remove interpretive variance. It does not aim to persuade.

A measured run recorded the cost of STE on everything. Two sections of argument lost their force. The run rewrote every verbatim quote from a client into reported speech.

The two disciplines collide on two points, not one.

Tell 7 warns against sentences of uniform length. STE sets a cap that demands short sentences.

Tell 2 offers a comma as the fix for an em-dash in the middle of a sentence. STE bans a comma that joins two clauses when both clauses can stand alone. On a surface that needs STE and tells, the fix for tell 2 then breaks STE.

## Decision

A discipline map gives each surface one of three treatments: STE plus tells, tells only, or neither. The trigger is simple. Ask if a wrong reading is a defect or if persuasion is the job. Do not apply either treatment to text that you quote from a person.

The STE cap and the sentence-variance tell can disagree. Then vary the length on purpose. The checker enforces this as rule R7, a floor for the standard deviation.

Tell 2 and the one-idea rule can disagree. Then split the sentence. Do not use a comma. A period never breaks the one-idea rule.

## Consequences

R7 is the only rule in the checker that reconciles two disciplines. The other rules enforce one discipline each. The clash of tell 2 and the one-idea rule has no matching rule. A writer on a surface of STE plus tells must split the sentence by hand.

We measured the rows of the map for client-facing surfaces. We extrapolated the rows for repository surfaces from the same trigger. These rows cover PRDs, ADRs, specifications, issues, pull request descriptions, and review comments. Nobody has measured them yet.

A document that mixes surfaces needs a treatment for each section. Sub-project 2 adds a `discipline=` zone attribute for that. Until then, the map is guidance that a writer applies. The checker reads whole documents.
