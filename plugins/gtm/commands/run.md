---
description: Full GTM build — asks your role, stage and goal, runs all agents in sequence, produces complete GTM package
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "AskUserQuestion"]
---

# /gtm:run

## Purpose

Run the full GTM build in a single command. This command asks you the questions. Then it dispatches the `gtm:orchestrator` agent. The orchestrator profiles your business stage and runs all agents in the correct dependency order to produce a complete, integrity-checked GTM package. Use this when starting from scratch or when you want a full end-to-end refresh.

The orchestrator cannot ask you anything. This command asks every question first, in this conversation, and gives the answers to the orchestrator.

## Usage

```
/gtm:run
/gtm:run --stage pre-pmf
/gtm:run --profile founder
/gtm:run --scan-codebase
```

A flag answers its question. Skip that question, because the person already answered it.

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

3. **Ask the codebase scan question** — ask if the orchestrator may scan the product codebase for product capabilities, existing integrations and tech differentiation. The scan is read-only and writes nothing to the repository. Set `scan_codebase` to `true` or `false`.

4. **Ask for files to ingest** — ask for the paths of files to learn from (call transcripts, win/loss notes, playbooks, product documents). The list can be empty. Set `files` to the list.

5. **Dispatch the orchestrator** — call the `Agent` tool with `subagent_type` `gtm:orchestrator` in the foreground. Give it these fields: `user_type`, `stage`, `goal`, `pmf_gate_bypassed`, `scan_codebase`, `files`. Wait for it to finish.

6. **Read the last line of its reply:**
   - `OPEN: .gtm/open-questions.json` — an agent needs your choice.
     1. Read `.gtm/open-questions.json`. It always holds `agent` and `options`.
     2. Floor breach (the file holds `integrity_score` and `top_issues`): show the agent, the score and the top issues. Ask with `AskUserQuestion`: `rerun` or `override`. Dispatch `gtm:orchestrator` again with the fields of step 5, and add `resume: true` and `breach_choice: {"<agent>": "rerun"}` or `{"<agent>": "override"}`.
     3. Other question (the file holds `question`, and maybe `contradictions` or `drift`): show the question and the extra detail. Ask with `AskUserQuestion` with the listed `options`. When `options` is empty, ask for free text. Dispatch `gtm:orchestrator` again with the fields of step 5, and add `resume: true` and `answers: {"<agent>": "<choice>"}`. The orchestrator passes the choice to that agent as its dispatch field: `contradiction_resolution` for `knowledge`, `competitor_context` for `sales`, `mql_sql_resolution` for `funnel`.
     4. Wait for it to finish. Do step 6 again with the new reply. A later wave can raise a new question.
   - `DONE: gtm` — go to step 7.
   - Neither line — show the reply to the person, say that the run did not finish, and stop.

7. **Deliver the GTM package** — When the reply names an agent that did not finish, say so first. List the files of `gtm-output/`. Show the integrity scores, the count of blocked Tier 5 claims and the recommended next actions. List the outside tools that would add data to the output if the person connected them (run `/gtm:setup`).

A score below 0.60 stops the run. The orchestrator asks no question for it and ends with `DONE: gtm`. Show its report to the person.

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
- When you want the orchestrator to sequence everything automatically
- When multiple agents need to run in coordination
