# ADR-007: The checker implements a derived STE subset, not the standard

**Status:** Accepted
**Date:** 2026-07-29

## Context

ASD owns the copyright to ASD-STE100 in whole and in part. ASD is the AeroSpace and Defence Industries Association of Europe, Brussels. The name is EU trade mark 017966390. Issue 9 has 53 writing rules and about 900 approved words. ASD gives the specification free of charge as a PDF file, and you request it through a form.

We cannot copy the dictionary or the rule text into this repository.

We also do not need to. A measured run showed this. With a prompt and no checker, the models wrote 231 sentences that had two rule breaks. The models learned STE from their training data. Both breaks were mechanical and are cheap to check.

## Decision

The prompt carries the judgment. The checker covers only the rules that survive a good prompt and that a machine can verify exactly. These rules are a narrow band.

We name rules by their intent, in our own words. Each word list belongs to this repository, so we can correct it.

## Consequences

The checker is partial by design. It will not find each STE break.

For an approximate rule, the checker reports WARN and a person decides. Only an exact rule gives FAIL.

The banned list will drift from the ASD dictionary. We accept this. The list is config, so a correction costs one edit.
