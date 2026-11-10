---
description: Auto-loop a document through detect → rewrite → fact-check → re-verify until it passes AI detectors, preserving meaning and human-authored zones
argument-hint: "<file-or-text> [--profile <name>] [--tier heuristics|hf|api|all] [--genre expository|literary|verbatim] [--in-place]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/zone_parser.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/extract_prose.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/profile_store.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/fact_gate.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/loop_controller.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/question_gate.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/lib/fault_delta.py *), Bash(uv run --with torch==2.15.0 --with transformers==5.22.2 ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py *)
---

Run the full humanize loop on the file path or pasted text in `$ARGUMENTS`. You are the
coordinator. Every iterate or stop decision comes from `lib/loop_controller.py`, every score from
`lib/run_detectors.py`, and every reassembly from `lib/zone_parser.py --reassemble` (markdown) or
`lib/extract_prose.py --reassemble` (code files).

Rules for the whole run:

- Handle paths only. Never read a document, a rewrite, a candidate or a score file into
  context, because the content fills the context window. You may read `loop-state.json`. The first
  exception is pasted input: write it with `Write` to `<run_id>/input.md` before any script call,
  and use that path from then on. The second exception is the report that `detection-analyst`
  returns as text: save it to `<run_id>/report.md` with `Write`, with no change.
- No person answers during a run. Take each value from `$ARGUMENTS` or from its default.
- Quote each placeholder in a command line with single quotes, and write each `'` inside a value
  as `'\''`. This holds for numbers too (`--iter '<N>'`). A value can hold a quote, a `$(...)` or a
  backtick, and the shell runs it if it is not quoted.
- Run each command on its own. Use no variable, no `$(...)`, no pipe and no `&&` or `;` chain, and
  write each path in full. The shell cannot check such a command before it runs, and refuses it.
- Start sub-agents with the `Agent` tool and the full type name, such as
  `prose-authenticity:humanizer`. Only you start sub-agents.
- A failed dispatch is one that returns an error or returns without its output file. A script that
  exits 3 writes no file. Record each failure as a degradation. Do not run a scripted step on a
  missing file. If the failure stops the loop, use the `GIVE_UP` branch: write the best
  candidate (the original if none) and flag it. A flagged give-up is better than a silent wrong
  output.

Steps:

1. **Read the arguments.** The defaults are: profile `-` (the bundled neutral profile), tiers
   `heuristics`, output in the run directory (the input file stays as it is unless `--in-place` is
   set, because the loop needs the original to compare). `--genre` overrides the genre of
   the question-adjudicator (`literary` and `verbatim` exempt the document).
2. **Run setup.** Get the time with `date -u +%Y%m%dT%H%M%SZ`, as 1 command on its own. Never write a time yourself, because 2 runs with the same time share 1 folder. Run `mkdir -p .prose-authenticity`, then `mkdir '.prose-authenticity/run-<time>'` with no `-p`. If that `mkdir` fails because the folder exists, get the time again and make a new folder. Let `run_id` be `run-<time>`. In the command lines below, `<run_id>` stands for the path
   `.prose-authenticity/<run_id>`. Each run has a new folder, so there is no resume. Check that
   the input has 50 words or more (the heuristics floor). If it has fewer, stop and say
   `<N> words, need >= 50 to score`.
3. **Ingest zones.** Markdown or raw input:
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/zone_parser.py '<input>' --out '<run_id>/zones.json'`.
   Code file (.py, .js, .ts):
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/extract_prose.py '<input>' --out '<run_id>/zones.json'`.
   Both print one line (`zones=<n>`, or the ambiguity count for code). If the ambiguity count is
   not 0, start `prose-authenticity:extraction-agent` with `run_in_background: false` in the `Agent` call (wait for the reply, as in step 5) and with the ambiguity list (zone id, text,
   source file path). After it writes `<run_id>/zone-mapping-decisions.json`, run
   `extract_prose.py` again with `--decisions '<run_id>/zone-mapping-decisions.json' --out '<run_id>/zones.json'`.
4. **Resolve profile.**
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/profile_store.py resolve '<name>' --project-dir .prose-authenticity`
   (`-` gives the bundled profile). The target is positional: the script has no `--profile` option.
5. **Fact baseline (once, from the original).** Start
   `grounded-synthesis:grounded-synthesis-orchestrator` with
   `{draft_path: <abs original>, source_paths: [<abs original>], output_dir_override: <abs>/<run_id>/facts}`
   and no other field. Set `run_in_background: false` in the `Agent` call and wait for the reply,
   because a background agent returns in a new turn, and the grant of this command ends with the
   turn. It fails when the `Agent` call returns an error, when its last line starts
   with `DONE: grounded-synthesis FAILED`, or when `fact_gate.py` exits with a code that is not 0.
   On a failure, record the degradation, init the loop with `--max-iterations '2'`, and plan an
   UNVERIFIED FACTS warning for the report. Read the coverage with
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/fact_gate.py '<run_id>/facts' --from-handoff`. The override
   directory holds only `gap-report.md` and `handoff.json`.
6. **Init the loop.**
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/loop_controller.py --state '<run_id>/loop-state.json' init [--max-iterations '2'] [--genre-override '<G>']`.
   When `genre` is set, pass it here as `--genre-override '<G>'` and on every `RUN_DETECTORS` call
   as `--genre '<G>'`. If you pass it to only one, the loop and the scorer disagree.
7. **Loop.** Repeat
   `uv run ${CLAUDE_PLUGIN_ROOT}/lib/loop_controller.py --state '<run_id>/loop-state.json' next`
   and switch on the action. Every other `loop_controller.py` call uses the same prefix.
   - `RUN_QUESTION_SCAN`: scan the current candidate (the original on iteration 1):
     `uv run ${CLAUDE_PLUGIN_ROOT}/lib/question_gate.py scan '<current-candidate-or-original>' --run-dir '<run_id>'`.
     For a code file add `--decisions '<run_id>/zone-mapping-decisions.json'`. It writes
     `<run_id>/candidates.json` and prints the candidate count on its last line. Then
     `... record-scan --candidate-count '<n>'`.
   - `ADJUDICATE_GATE`: start `prose-authenticity:question-adjudicator` with `run_in_background: false` in the `Agent` call (wait for the reply, as in step 5) and with the path
     `<run_id>/candidates.json`. It writes `<run_id>/adjudication.json`. Then
     `... record-adjudication`. Run `record-adjudication` when the dispatch fails too: it records
     that the step ran, and without it the loop stays in phase `scanned` for ever. On a failure no
     `adjudication.json` exists, so the next `RUN_DETECTORS` scores without the gate and the verdict is
     UNADJUDICATED. Write the failure message with `Write` to `<run_id>/gate-error.txt`, and pass
     `--gate-error-file '<run_id>/gate-error.txt'` on that next `RUN_DETECTORS` call, so the report
     says why the gate did not run.
   - `RUN_DETECTORS`:
     `uv run ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py '<current-candidate-or-original>' --run-dir '<run_id>' --iter '<N>' --tiers '<tiers>' --project-dir .prose-authenticity --original '<original>'`.
     When `<tiers>` holds `hf` or `all`, run it as
     `uv run --with torch==2.15.0 --with transformers==5.22.2 ${CLAUDE_PLUGIN_ROOT}/lib/run_detectors.py ...`, else
     the hf tier is UNAVAILABLE. Always pass `--original`: without it `original_line` means the
     line in the rewrite, and the report needs the line in the document the person edits. Add
     `--gate '<run_id>/adjudication.json'` when that file exists (a scan with no candidates writes
     none), `--genre '<G>'` when `genre` is set, and for a code file
     `--decisions '<run_id>/zone-mapping-decisions.json'` when that file exists. Then
     `... record-scores --verdict '<V>' --tier '<T>' --composite '<C>'` from the printed summary.
     When the summary prints the text `None` for tier and composite (a document with no ai or
     mixed zone), leave out `--tier` and `--composite` and pass only the verdict. That verdict can
     be PASS, FAIL or UNAVAILABLE, because the gate override runs after the scorer writes its
     verdict. Two examples: `record-scores --verdict PASS` for a clean document, and
     `record-scores --verdict FAIL` when the gate forces FAIL (a rhetorical question in a human
     zone, with `rewritable_remaining == 0`). Never pass `--composite None`, because
     `record-scores` rejects it and the loop stops.
   - `DISPATCH_REWRITE`: for each flagged zone, find the latest rewrite path by file listing
     (`<run_id>/rewrites/iter-*/zone-<id>.md`). On iteration 1 there is none: pass `null`, and the
     humanizer uses the zone text from `zones.json`. Start `prose-authenticity:humanizer` with `run_in_background: false`
     in the `Agent` call (wait for the reply, as in step 5, because `record-rewrite` and the reassembly come after it)
     and with: the `zones.json` path, the latest path of each zone, the `scores-iter-<N>.json` path, the
     profile path, the missing-facts list from the loop state, output dir `<run_id>/rewrites/iter-<N>/`,
     and the fact-baseline file `<run_id>/facts/gap-report.md` (a file, because the humanizer has no tool that lists a folder). When the strictest
     tier is hf or api (no per-zone breakdown), flag all ai and mixed zones. Only the heuristics tier
     gives per-zone hits. Gate union: only when `gate.status` in the scores file is `FAIL`, add the
     `zone_id` of each `gate.candidates[]` entry with `label == "rhetorical"` and
     `rewritable == true`. Pass the `<run_id>/adjudication.json` path only when that file exists.
     Then `... record-rewrite`. Then reassemble. Markdown:
     `uv run ${CLAUDE_PLUGIN_ROOT}/lib/zone_parser.py '<original>' --reassemble --run-dir '<run_id>' --iter '<N>'`.
     Code file: the same with `extract_prose.py`, and add
     `--decisions '<run_id>/zone-mapping-decisions.json'` when that file exists, because
     without it reassembly does not put an include-resolved zone back.
   - `RUN_FACT_CHECK`: start `grounded-synthesis:grounded-synthesis-orchestrator` with
     `{draft_path: <abs>/<run_id>/candidate-iter-<N>.<ext>, source_paths: [<abs original>], output_dir_override: <abs>/<run_id>/facts}`,
     with `run_in_background: false` in the `Agent` call (wait for the reply, as in step 5).
     `source_paths` is required each time. Then
     `uv run ${CLAUDE_PLUGIN_ROOT}/lib/fact_gate.py '<run_id>/facts' --from-handoff --ids-only`
     and `... record-factcheck --missing '<ids>'`. A failed dispatch (the rule of step 5), at any
     iteration, has the same result as in step 5: record the degradation and skip the fact check
     from then on (`record-factcheck` with an empty `--missing`).
   - `ACCEPT`: copy the accepted candidate to `<run_id>/output/<basename>`. With `--in-place`,
     copy it over the input after a `.bak` backup. Leave the loop.
   - `GIVE_UP`: read `give_up_reason` (it can be `null`) and `best_iteration` from
     `loop-state.json`. Copy `candidate-iter-<best_iteration>` (the latest candidate if
     `best_iteration` is null) to the output as flagged output. Leave the loop.
8. **Report and handoff.**
   - Run
     `uv run ${CLAUDE_PLUGIN_ROOT}/lib/fault_delta.py --original '<original>' --candidate '<accepted-output>' --out '<run_id>/fault-delta.json'`.
     Exit 0 and exit 2 both write the file (2 means the rewrite introduced faults). Exit 3 writes
     no file: record a degradation and pass no delta path.
   - Start `prose-authenticity:detection-analyst` with `run_in_background: false` in the `Agent` call (wait for
     the reply, as in step 5) and with: `mode` = `humanize-final`,
     `doc` (the original), the accepted-output path, the fault-delta path, the profile name,
     `scores_path` (the last `scores-iter-<N>.json`), the list of all `scores-iter-<N>.json` paths in
     order, the `loop-state.json` path (and `give_up_reason` after a give-up), and `degradations`. It
     returns the report as text. Save that text with `Write` to `<run_id>/report.md`.
   - Write `<run_id>/prose-authenticity-handoff.json` with `Write`:
     `{"run_id": "<run_id>", "verdict": "<V>", "iterations": <N>, "output_path": "<run_id>/output/<basename>", "report_path": "<run_id>/report.md", "degradations": []}`.
     After a give-up, write `"verdict": "GIVE_UP"`, whatever the last detector verdict was.
   - Show `verdict`, `output_path`, `report_path` and `degradations`. If `verdict` is `GIVE_UP`, say
     that the output is a best effort, and give the reason from the report.

The fact check needs the grounded-synthesis plugin. Without it, the report shows UNVERIFIED FACTS.

The final report names any correctness or STE fault the rewrite introduced, measured as a delta
against your original. Faults your document already had are listed separately. The loop does not
fix either kind — see ADR-012 for why it discloses rather than gates.
