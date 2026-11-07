---
description: Score a document or pasted text for AI-generation tells — PASS/WARN/FAIL report with line-level findings, no rewriting
argument-hint: "<file-or-text> [--tier heuristics|hf|api|all] [--genre expository|literary|verbatim]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/*), Bash(uv run --with torch==2.15.0 --with transformers==5.22.2 ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py *)
---

Score the file path or pasted text in `$ARGUMENTS` for AI-generation likelihood. A single pass
rewrites nothing.

Rules for the whole run:

- Handle paths only: a document or a score file in context fills the context window. The one
  exception is the report that `detection-analyst` returns: save it with `Write`, with no change.
  If the input is pasted text, write it with `Write` to `.prose-authenticity/<run_id>/input.md` before any
  script call, and use that path from then on.
- Quote each placeholder in a command line with single quotes, and write each `'` inside a value
  as `'\''`. This holds for numbers too (`--iter '1'`). A value can hold a quote, a `$(...)` or a
  backtick, and the shell runs it if it is not quoted.
- Run each command on its own. Use no variable, no `$(...)`, no pipe and no `&&` or `;` chain, and
  write each path in full. The shell cannot check such a command before it runs, and refuses it.
- Start sub-agents with the `Agent` tool and the full type name, such as
  `prose-authenticity:detection-analyst`. Only you start sub-agents.

Steps:

1. **Read the arguments.** `--tier` sets the detector tiers (default `heuristics`; add `hf` or
   `api` only when asked, because the api tier needs consent that `/setup` records, and the
   script checks it). `--genre` overrides the genre of the question-adjudicator for the
   rhetorical-question gate (`literary` and `verbatim` exempt the document from the gate).
2. **Run setup.** Get the time with `date -u +%Y%m%dT%H%M%SZ`, as 1 command on its own. Never write a time yourself, because 2 runs with the same time share 1 folder. Run `mkdir -p .prose-authenticity`, then `mkdir '.prose-authenticity/run-<time>'` with no `-p`. If that `mkdir` fails because the folder exists, get the time again and make a new folder. In the command lines below, `<run_id>` stands for the
   path `.prose-authenticity/run-<time>`.
3. **Scan for interrogatives.** The gate is never opt-in.
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/question_gate.py scan '<path>' --run-dir '<run_id>'`
   writes `<run_id>/candidates.json` and prints the candidate count on its last line.
4. **Adjudicate only when the count is above 0.** A document with no candidates has no
   `adjudication.json`. Otherwise start `prose-authenticity:question-adjudicator` with `run_in_background: false`
   in the `Agent` call (wait for the reply, as in step 6) and with the path
   `<run_id>/candidates.json`. It writes `<run_id>/adjudication.json`. If the dispatch fails (a
   timeout, a malformed output or a missing agent), no such file exists. Write the failure
   message with `Write` to `<run_id>/gate-error.txt`, so the report says why the gate did not run.
5. **Score and check.**
   - `uv run ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py '<path>' --run-dir '<run_id>' --iter '1' --tiers '<tiers>' --project-dir .prose-authenticity`
     Add `--gate '<run_id>/adjudication.json'` when that file exists,
     `--gate-error-file '<run_id>/gate-error.txt'` when step 4 failed, and `--genre '<G>'` when
     `--genre` is set. When `<tiers>` holds `hf` or `all`, run it as
     `uv run --with torch==2.15.0 --with transformers==5.22.2 ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py ...`, else
     the hf tier is UNAVAILABLE. If it fails because the input is too short, tell the person
     `<N> words, need ≥50` and stop. Show no traceback.
   - `uv run ${CLAUDE_PLUGIN_ROOT}/lib/correctness_checker.py '<path>' --out '<run_id>/correctness.json'`
   - `uv run ${CLAUDE_PLUGIN_ROOT}/lib/ste_checker.py '<path>' --out '<run_id>/ste.json'`

   The two checkers exit 0 on PASS, 1 on WARN, 2 on FAIL and 3 on a config or read error. Exit 3
   writes no file: record a degradation and pass no path for that checker. Read the exit code before
   you start the analyst. Both verdicts are reported beside the tier verdict and outside it, because ADR-006
   keeps the three scales apart.
6. **Report.** Start `prose-authenticity:detection-analyst` with `run_in_background: false` in the `Agent`
   call (wait for the reply: a background agent returns in a new turn, and the grant of this command ends
   with the turn) and with: `mode` = `check`,
   `doc` (the path), `scores_path` (`<run_id>/scores-iter-1.json`), the correctness and STE JSON
   paths, and `degradations`. It returns the report as text. Save that text with `Write` to
   `<run_id>/report.md`.
7. Show the report path and the verdict line (the first line of the report).

The report also carries a correctness verdict (spelling, doubled words, article agreement) and an
STE verdict. Both are reported beside the tell score, not inside it, because they measure a
different thing and ADR-006 keeps them out of the composite.
