---
description: Score a document or pasted text for AI-generation tells — PASS/WARN/FAIL report with line-level findings, no rewriting
argument-hint: "<file-or-text> [--tier heuristics|hf|api|all] [--genre expository|literary|verbatim]"
---

Score the file path or pasted text in `$ARGUMENTS` for AI-generation likelihood.

1. Read the arguments. `--tier` sets the detector tiers (default `heuristics`).
   `--genre` overrides the question-adjudicator's genre classification for the
   rhetorical-question gate (`literary` and `verbatim` exempt the document from
   the gate).
2. Dispatch the agent `prose-authenticity:detection-analyst` with the `Agent` tool.
   Give it these fields: `input` (the path, or the pasted text), `tiers` (the
   `--tier` value, default `heuristics`) and `genre` (the `--genre` value, if any).
3. Show the report path and the verdict line that the agent returns.

The report also carries a correctness verdict (spelling, doubled words,
article agreement) and an STE verdict. Both are reported beside the tell
score, not inside it, because they measure a different thing and ADR-006 keeps
them out of the composite.
