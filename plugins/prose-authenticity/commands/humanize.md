---
description: Auto-loop a document through detect → rewrite → fact-check → re-verify until it passes AI detectors, preserving meaning and human-authored zones
argument-hint: "<file-or-text> [--profile <name>] [--tier heuristics|hf|api|all] [--genre expository|literary|verbatim] [--in-place]"
---

Run the full humanize loop on the file path or pasted text in `$ARGUMENTS`.

1. Read the arguments. The defaults are: the bundled neutral profile, the
   heuristics tier, and output in the run directory (the input file stays as it is
   unless `--in-place` is set, because the loop needs the original to compare). `--genre` overrides the question-adjudicator's
   genre classification for the rhetorical-question gate (`literary` and
   `verbatim` exempt the document).
2. Dispatch the agent `prose-authenticity:orchestrator` with the `Agent` tool.
   Give it these fields: `input`, `profile` (default `-`), `tiers` (default
   `heuristics`), `genre` (if any) and `in_place` (default `false`).
3. Read the `prose-authenticity-handoff.json` file at the path that the agent
   returns. Show `verdict`, `output_path`, `report_path` and `degradations`.
4. If `verdict` is `GIVE_UP`, say that the output is a best effort, and give the
   reason from the report.

The fact check needs the grounded-synthesis plugin. Without it, the report shows
UNVERIFIED FACTS.

The final report names any correctness or STE fault the rewrite introduced,
measured as a delta against your original. Faults your document already had
are listed separately. The loop does not fix either kind — see ADR-012 for
why it discloses rather than gates.
