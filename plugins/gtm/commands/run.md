---
description: Full GTM build — asks your role, stage and goal, runs all agents in sequence, produces complete GTM package
allowed-tools: ["Read(*)", "Write(*)", "Edit(*)", "Agent", "Glob(*)", "Grep(*)", "AskUserQuestion", "Skill", "Bash(git rev-parse *)", "Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plugin_integrator.py *)", "Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/truth_tier_validator.py *)", "Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/output_check.py *)"]
---

# /gtm:run

## Purpose

Run the full GTM build in a single command. This command asks you the questions. Then it dispatches the `gtm:orchestrator` agent, which profiles your business stage and prepares the session. Then this command runs all other agents in the correct dependency order to produce a complete, integrity-checked GTM package. Use this when starting from scratch or when you want a full end-to-end refresh.

No agent asks you anything or starts another agent. This command asks every question in this conversation, runs every script, makes every `Agent` call in the foreground (`subagent_type` `gtm:<agent>`), and reads the completion flags.

## Usage

```
/gtm:run
/gtm:run --stage pre-pmf
/gtm:run --profile founder
/gtm:run --scan-codebase
/gtm:run --resume
```

A flag answers its question. Skip that question, because the person already answered it. `--resume` answers the run mode question of the Routing section.

## Process

1. **Ask the profile questions** — use `AskUserQuestion`:
   - Role (`user_type`): `founder`, `cmo`, `head-of-sales`, `growth` or `product`
   - Business stage (`stage`): `idea`, `pre-pmf`, `pmf`, `growth` or `scale`
   - Primary goal (`goal`): launch, grow, defend or enter a new market

2. **Apply the PMF gate** — if `stage` is `idea` or `pre-pmf`:
   - Show the Sean Ellis test: "Would customers be very disappointed if your product disappeared?" (40% answer "very disappointed").
   - Say that GTM amplifies product-market fit and does not create it.
   - Ask: continue with a research-mode build, or stop and validate first.
   - If the person stops, end this command. Dispatch no agent.
   - If the person continues, set `pmf_gate_bypassed` to `true`. Else set it to `false`.

3. **Ask the codebase scan question** — ask if the codebase-scanner may scan the product codebase for product capabilities, existing integrations and tech differentiation. The scan is read-only and writes nothing to the repository. Set `scan_codebase` to `true` or `false`.

4. **Ask for files to ingest** — ask for the paths of files to learn from (call transcripts, win/loss notes, playbooks, product documents). The list can be empty. Set `files` to the list.

5. **Find the plugin outputs** — run `git rev-parse --show-toplevel` on its own. Its output is `<project>`. Then run this command on its own, with nothing before or after it (no `cd`, no `;`, no `echo $?`):

   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plugin_integrator.py --root '<project>' --out '<project>/.gtm/plugin-outputs.json'`

   Keep the single quotes, and write each `'` in the path as `'\''`. The script writes one JSON object to the file (each key is a plugin, and each value is a list of paths) and prints one line. If it fails, say so in the final summary, give the orchestrator no `plugin_outputs_path`, and go on.

6. **Prepare the session** — call the `Agent` tool with `subagent_type` `gtm:orchestrator` in the foreground. Give it these fields: `user_type`, `stage`, `goal`, `pmf_gate_bypassed`, `project_root` (the git root) and `plugin_outputs_path` (`<project>/.gtm/plugin-outputs.json`). Leave `plugin_outputs_path` out when the script of step 5 failed, because the file can then be from an earlier run. It writes `gtm-context.json` and ends its reply with one line:
   - `READY: gtm` — go to step 7.
   - `DONE: gtm` — the PMF gate stopped the run. Show its reply to the person and stop. Start no other agent.
   - Neither line — show the reply to the person, say that the run did not finish, and stop.

7. **Run the waves** — find the run mode (Routing, "Run mode"). Then follow the Routing, Floor breach handling and Open questions sections below. After each step, update `gtm-context.json._meta.last_updated`, and log all routing decisions to `gtm-context.json._meta.execution_log`.

8. **Deliver the GTM package** — When a step stopped the run, say so first and name the agent. Read `.gtm-graph-notes.txt` (in the project folder, not in `.gtm/`) and show each line of it, unchanged, before the rest. Such a line starts with `NO-GRAPH:` or `GRAPH-READ-FAILED:`, and says that the run had no input from the graph of `jtbd-market-discovery` or `competitive-intelligence`, and what to run to make it. An empty file means that both graphs gave input. When the file is absent, say that the run did not read the graphs. List the files of `gtm-output/`. Show the integrity scores, the count of blocked Tier 5 claims and the recommended next actions. List the outside tools that would add data to the output if the person connected them (run `/gtm:setup`). Tell the person which data sources the MCP status limits. Show each line of the "Schema errors" list and each "not checked" line, because such a file does not agree with its schema.

A score below 0.60 stops the run. Show its report to the person.

## Routing

You read only completion_flags and completion_log[agent_name] (one paragraph) from gtm-context.json. All artifact content lives on disk: drafts in .gtm/working/ and finals in gtm-output/. A large context here would slow every later step. (Directory structure and artifact paths: ${CLAUDE_PLUGIN_ROOT}/definitions/directory-structure.md)

Each wave step is a foreground Agent call: the call returns when the agent ends, so there is nothing to poll. After each call, read only the completion flag of that agent from gtm-context.json. If the flag is not true, log it in _meta.execution_log and go to Floor breach handling (integrity flags) or stop the run, name the agent and its flag in the reply (content agent flags).

Run mode: after step 6 and before the waves, read `completion_flags`. When no flag is true, this is a full run. When a flag is true, an earlier run left its state. Then ask the person with `AskUserQuestion`: `resume` (go on with the earlier run) or `full` (run each agent again). The flag `--resume` answers `resume`. When the run has no `--resume` and no person can answer, start no agent, name the 2 choices and `/gtm:run --resume` in the reply, and stop, because a full run erases the flags of the earlier run and a resume shows its output.

Resume wait: on a resume, before the waves, if `.gtm/open-questions.json` holds `integrity_score` and `options` and does not say `answered`, a floor question is still open. Ask the person with `AskUserQuestion` (or use the choice that the person already gave in this run), then apply it as Floor breach handling steps 3 and 4 say. When nobody can answer, dispatch no agent, because the agent would run its pass again and repeat the same question; name `.gtm/open-questions.json` in the reply and stop.

Resume: Skip an agent whose completion flag is true, and call only the agents that did not finish. This rule is for a resume only.

Resume after a stopped integrity pass: for each of brand, marketing, sales and funnel whose flag `completion_flags.<agent>_integrity` is false, read `.gtm/audit/<agent>-integrity.json` with the Read tool. When the file exists and Resume wait found no open floor question, an earlier integrity pass of <agent> read the drafts and stopped (band floor, no claims, or a script that did not run). Then <agent>-agent has not finished: make 1 Agent call to <agent>-agent, also when `completion_flags.<agent>` is true, and then do its INTEGRITY PASS. Do not start with the INTEGRITY PASS, because phase audit already took the Tier 5 claims out of the drafts, and an audit of the same drafts gives a score that is too high. When the file does not exist, no integrity pass read the drafts: do the INTEGRITY PASS, and do not call <agent>-agent again, because no audit changed its drafts.

Full run after an earlier run (the choice `full`): before Wave 0, set each flag of `completion_flags` to false and `_meta.dispatched_agents` to `[]` with the Edit tool. If `.gtm/open-questions.json` exists, overwrite it with the Write tool with {"status": "answered"}. A flag or a question of the earlier run would hide an agent that fails in this run. Then make each Agent call of the waves, also to an agent that finished in the earlier run.

After an answer of the person in this run (a floor choice or an open question), go on from the step that stopped. The agent that the answer names runs again although its completion flag is true.

Change keys of gtm-context.json with the Edit tool, and never write the whole file again with the Write tool, because 2 agents of Wave 2 change it at the same time.

DISPATCH KEYS: before each Agent call to an agent of this table, add its key to
gtm-context.json._meta.dispatched_agents (1 time for each key). A resume reads the
flags of the keys in this list only.

| Agent | Key |
|---|---|
| knowledge-agent | knowledge |
| codebase-scanner | codebase_scanner |
| brand-agent | brand |
| marketing-agent | marketing |
| sales-agent | sales |
| funnel-agent | funnel |

Each Agent call below gives the dispatch field `project_root` (the git root of step 5), so no agent searches for it.

Wave 0 — knowledge and codebase (if applicable):
  → If files is not empty: check whether the skills `enterprise-search` and `customer-support` are in this session. For each one that is, call it with the Skill tool and write its answer to .gtm/working/knowledge/enterprise-search.md or .gtm/working/knowledge/customer-support.md. Ask `enterprise-search` for: Gong call transcripts, win/loss notes, BDR playbooks, case studies, competitor research. Ask `customer-support` for: churn-tagged ticket summaries from the last 90 days.
  → Agent call to knowledge-agent (if files provided), with the dispatch fields files and skill_outputs (the paths written above; an empty list when no skill is in this session). The agent reads those files as data.
  → Agent call to codebase-scanner (if scan_codebase)
  → read completion_flags for the agents in _meta.dispatched_agents (an agent that did not run has no flag to read)
  → proceed when all dispatched Wave 0 agents are complete (skip entirely if none dispatched)
  → knowledge-agent can end with OPEN: .gtm/open-questions.json (see Open questions below)

INTEGRITY PASS of <agent> (brand | marketing | sales | funnel), 3 steps:
  1. Agent call to integrity-agent with this prompt: {"target_agent": "<agent>", "phase": "audit"}
  2. Run this command alone, with nothing before or after it (no cd, no ;, no echo $?):
       uv run ${CLAUDE_PLUGIN_ROOT}/scripts/truth_tier_validator.py --root '<project>' --agent <agent>
     (<project> is the git root. Keep the single quotes, and write each ' in the path as '\''.) The script writes integrity_score and band into
     .gtm/audit/<agent>-integrity.json and prints 1 line. The Bash tool shows "Exit code <n>" for an exit
     that is not 0. With no such line, the exit is 0.
     → Exit 0: go to step 3 in each band (floor, choice and pass), because step 3 writes error_log and the held files.
     → Exit 3 (the line names no_claims): An audit with 0 claims has no integrity score: `truth_tier_validator.py`
       exits 3 with the gap `no_claims`, and the run stops with no file in `gtm-output/`. Skip step 3, because
       there is nothing to write. Leave completion_flags.<agent>_integrity false. Add "integrity pass of <agent> not scored: no_claims, the audit holds 0 claims"
       and the output to _meta.execution_log. Stop the run. In the reply, name the gap no_claims and say that
       the drafts of <agent> hold no claim to check.
     → Exit 4 (the line names floor_holds): an earlier audit of <agent> gave band floor, and <agent>-agent wrote
       no new drafts after it. The script wrote that audit back and gave no new score, because phase audit
       already took the Tier 5 claims out of the drafts, and a second audit of the same drafts counts only the
       claims that stayed. Skip step 3. Leave completion_flags.<agent>_integrity false. Add "integrity pass of
       <agent> not scored: floor_holds" and the output to _meta.execution_log. Stop the run. In the reply, name
       the gap floor_holds and the earlier score, and say that the floor stays until <agent>-agent writes new
       drafts.
     → Each other result (a refused call, an exit that is not 0): the script gives the only valid score, and a
       score counted by hand is not a score. Skip step 3, and leave completion_flags.<agent>_integrity false.
       Add "integrity pass of <agent> not scored: truth_tier_validator.py did not run" and the output to
       _meta.execution_log. Stop the run and say this in the reply.
  3. Agent call to integrity-agent with this prompt: {"target_agent": "<agent>", "phase": "write"}

SCHEMA CHECK: after each integrity pass whose flag is true, and 1 time at Final:
  → Run this command alone, with nothing before or after it (no cd, no ;, no echo $?):
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/output_check.py --root '<project>' --agent <agent>
    (<project> as in step 5; at Final, --context in place of --agent <agent>).
    The Bash tool shows "Exit code <n>" for an exit that is not 0. With no such line, the exit is 0.
  → Exit 0: go on.
  → Exit 1, and the last line is "<n> schema errors in <k> files": Agent call to integrity-agent
    again with target_agent=<agent> and schema_errors=<the error lines>. At Final, fix each
    named field of gtm-context.json with the Edit tool. Then run the check again 1 time.
  → Add each error line that stays to _meta.execution_log and to the "Schema errors" list
    of the final summary. A schema error does not stop the run.
  → Each other result (a refused call, exit 2, another exit code, or exit 1 with another last line): add
    "not checked" and the output to _meta.execution_log and to the final summary.

Wave 1 — brand identity (sequential — identity anchor):
  → Agent call to brand-agent
  → read completion_flags.brand == true
  → INTEGRITY PASS of brand
  → read completion_flags.brand_integrity == true
  → SCHEMA CHECK with --agent brand

Wave 2 — demand generation (parallel — MQL pre-seeding enables this):
  → one message with 2 Agent calls: marketing-agent and sales-agent
  → when both calls return, do the INTEGRITY PASS of marketing and of sales together: step 1 as
    one message with 2 Agent calls, step 2 for marketing and then for sales (1 command at a time),
    and step 3 as one message with 2 Agent calls
  → The 2 agents of each pair run at the same time, and both change gtm-context.json.
    Each agent changes only its own keys with the Edit tool, because a whole-file write
    by one agent erases the keys of the other.
  → read `completion_flags.marketing_integrity` and `completion_flags.sales_integrity`; both are true
  → SCHEMA CHECK with --agent marketing, then with --agent sales
  → Wave completion is the set of flags for the wave in
    ${CLAUDE_PLUGIN_ROOT}/definitions/wave-routing.json (wave2: marketing, marketing_integrity,
    sales, sales_integrity). The wave is complete when each of these flags is true.

Wave 3 — funnel reconciliation (sequential — reconciler):
  → Agent call to funnel-agent
  → read completion_flags.funnel == true
  → INTEGRITY PASS of funnel
  → read completion_flags.funnel_integrity == true
  → SCHEMA CHECK with --agent funnel

Final — session summary to user:
  → read gtm-context.json.integrity_scores{} and completion_log{}
  → SCHEMA CHECK with --context
  → deliver lean summary: integrity scores + artifact paths in gtm-output/ + Tier 5 blocked count
    + the "Schema errors" list and each "not checked" line (or "Schema check: 0 errors")

## Floor breach handling

Bands of the integrity score (truth_tier_validator.py writes `band`):
- floor: integrity_score under 0.60. No file in gtm-output/, and no override.
- choice: integrity_score 0.60 to 0.84. No file in gtm-output/, and completion_flags.<agent>_integrity stays false, until the person chooses rerun or override.
- pass: integrity_score 0.85 and more. The files go to gtm-output/, and completion_flags.<agent>_integrity is true.

If completion_flags.{agent}_integrity == false after step 3 of an INTEGRITY PASS:
- Read band and integrity_score from .gtm/audit/{agent}-integrity.json, and the top issues from
  gtm-context.json.error_log.{agent}_integrity
- Band floor: after step 3, stop. Offer no override. Dispatch no further agent.
  Do not write error_log.{agent}_integrity yourself, because step 3 writes it for each band.
  Report the score and top issues in the reply. Write no question file.
  The floor holds until {agent}-agent writes new drafts: truth_tier_validator.py set completion_flags.{agent}
  to false and kept the audit in .gtm/audit/{agent}-floor-hold.json, so a resume calls {agent}-agent again,
  and the script gives no new score for the same drafts (exit 4, floor_holds).
  Do not change that flag or that file, because the script reads both to hold the floor.
  In the reply, say that the person changes the inputs of {agent} and then runs /gtm:run --resume.
- Band choice: the person must choose. Do this:
  1. Write .gtm/open-questions.json:
     {"agent": "{agent}", "integrity_score": X, "top_issues": [...],
      "options": ["rerun", "override"]}
  2. Show the agent, the score and the top issues. Ask with `AskUserQuestion`: `rerun` or `override`.
  3. Overwrite .gtm/open-questions.json with the Write tool with {"status": "answered"}. Do this before step 4, because a new pass of step 4 can write a new question to this file.
  4. Apply the choice:
     → "rerun": make an Agent call to {agent}-agent again with revised inputs, although completion_flags.{agent} is true. Then do its INTEGRITY PASS.
     → "override" (band choice only):
       → Tier 5 claims: integrity-agent already removed them, and they stay out
       → Agent call to integrity-agent with this prompt: {"target_agent": "{agent}", "phase": "write", "override_flag": true}
         It writes the Tier-5-cleaned drafts of .gtm/working/{agent}/ to gtm-output/. Do no new phase audit,
         and do not run the script again, because the person chose for this score.
       → integrity-agent adds caution banner to each promoted artifact: "⚠️ integrity_score: [X] — below target 0.85"
       → integrity-agent sets completion_flags.{agent}_integrity = true after promotion completes
       → SCHEMA CHECK with --agent {agent}, because the override wrote the files of gtm-output/ again.
- For breach info, read only error_log and the band and integrity_score of the audit file. The content of the agent output is not needed, and it fills the context.

## Open questions

If an agent ends with the line OPEN: .gtm/open-questions.json, stop the waves.
1. Read `.gtm/open-questions.json`. It holds `agent`, `question`, and maybe `options`, `contradictions` or `drift`.
2. Show the question and the extra detail. Ask with `AskUserQuestion` with the listed `options`. When `options` is empty, ask for free text.
3. Overwrite .gtm/open-questions.json with the Write tool with {"status": "answered"}. Do this before step 4, because the agent can write a new question to this file.
4. Make an Agent call to the same agent again, and add the choice as a dispatch field: `contradiction_resolution` for `knowledge-agent`, `competitor_context` for `sales-agent`, `mql_sql_resolution` for `funnel-agent`. If the agent ends with an `OPEN:` line again, do these 4 steps again. Else go on with the wave. A later wave can raise a new question.

## Rules

- Completion flag naming: content agents set `completion_flags.{agent}` (e.g., brand → `completion_flags.brand`); integrity passes set `completion_flags.{agent}_integrity` (e.g., brand → `completion_flags.brand_integrity`). Read the suffixed flag for integrity status, because the unsuffixed flag only shows that the content agent ended. On band floor, `truth_tier_validator.py` sets `completion_flags.{agent}` back to false, because the content agent must write new drafts.
- Run `integrity-agent` after each content agent. Only this command starts it, so the order of the audits stays fixed.
- On band floor (integrity_score under 0.60), after step 3 of the INTEGRITY PASS, report it in the reply and dispatch no further wave.
- Only truth_tier_validator.py gives integrity_score and band. A score counted by hand is not a score.
- Write no helper script: no heredoc, no `python3`, and no script file in the project of the person. The shell grant is the scripts of this plugin that the `allowed-tools` line names.

## Output Artifacts

- `gtm-context.json` — master context file (updated throughout)
- `brand-identity.json`, `messaging-architecture.json`, `voice-guide.md`
- `launch-plan.json`, `campaign-plan.json`, `content-calendar.md`
- `pitch-deck.json`, `pitch-narrative.md`
- `prospecting-plan.json`, `pipeline-playbook.json`
- `funnel-metrics.json`, `funnel-health.md`, `revenue-math.md`
- `consolidated-audit.json` — integrity scores for all marketing artifacts

## When to Use

- First GTM build for a new product or company
- Full refresh after significant product pivot
- When you want one command to sequence everything automatically
- When multiple agents need to run in coordination
