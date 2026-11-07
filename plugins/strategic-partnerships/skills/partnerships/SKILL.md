---
name: partnerships
description: Run the full strategic partnership analysis for a software product, from readiness to a go or no-go recommendation. Use when the user wants to evaluate partnership readiness, find partners, structure a deal, design an integration, model partnership revenue, or get one go or no-go recommendation. It covers partner programs, OEM, reseller, open source, SaaS, and consulting models.
argument-hint: "[product name, category, target market, existing integrations, partnership goals]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# Strategic Partnerships

This skill runs the full 6-phase partnership analysis for one software product. The result is a go or no-go recommendation, a roadmap, and a board-ready brief.

The method comes from Popp and Meyer (*Profit from Software Ecosystems*), Gawer and Cusumano (*Platform Leadership*), Parker, Van Alstyne and Choudary (*Platform Revolution*), Jansen (ecosystem health and power dynamics), and Forrester (2025 State of B2B Partner Ecosystems). The file `${CLAUDE_PLUGIN_ROOT}/frameworks.md` gives the full attribution.

## When this skill runs

The person:
- mentions "partnership", "strategic partner", "ecosystem strategy", or "partner program"
- asks about OEM, white-label, reseller, VAR, or channel partnerships
- asks about "open source + commercial" or "open core" strategy
- asks about partner program design, tiers, or revenue share
- mentions "complementors", "platform strategy", or "ecosystem monetization"
- asks how to structure a deal with a partner
- wants to assess "partnership readiness" or "ecosystem fit"
- plans a marketplace listing, such as Salesforce AppExchange or AWS Marketplace
- asks about certifications, ISV programs, or GSI and SI partnerships

## Routing

The full run follows the steps below. For one phase only, tell the person to run the skill of that phase:

| Phase | Skill | Purpose |
|-------|-------|---------|
| 1 | `/strategic-partnerships:partnerships-assess` | Market position, business model archetype, power dynamics, readiness |
| 2 | `/strategic-partnerships:partnerships-discover` | Ecosystem map and ranked partner candidates |
| 3 | `/strategic-partnerships:partnerships-structure` | Business, legal, and operational deal framework |
| 4 | `/strategic-partnerships:partnerships-architect` | Technical integration architecture |
| 5 | `/strategic-partnerships:partnerships-monetize` | Revenue streams, NPV, and ROI |
| 6 | `/strategic-partnerships:partnerships-recommend` | Go or no-go decision, roadmap, and board-ready brief |

## Steps

1. Read `$ARGUMENTS` as free text, and map it to the 5 fields of the product context: product name, category, target market, existing integrations, and partnership goals.
2. Ask the person for the missing fields with `AskUserQuestion`, because the agents cannot ask the person.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --sweep` to remove old sessions that did not finish. A finished session stays, because `synthesize.md` is the report of the person.
4. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --init`. It prints the new session id. The session folder is `.sp-tmp/<session id>/`.
5. For each phase in the order assess, discover, structure, architect, monetize, run these steps in this conversation. Run each command on its own, as it is written: no `;`, no `&&`, no `$?` and no shell variable, because the grant of this skill allows 1 `uv run` command only. No agent of this plugin has `Bash` or `Agent`, so you run each script and start each agent. Start each agent with the `Agent` tool in the foreground: set `run_in_background: false` in each `Agent` call. Use its full name, because a bare name finds no agent. Wait for each agent to end before the next step. The run takes time. A run with `claude -p` stops your turn when you end it, so end it only after step 7.
   1. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase '<phase>' --session-id '<session id>' --out '.sp-tmp/<session id>/preflight-<phase>.json'`.
   2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-preflight --session-id '<session id>' --phase '<phase>' --from-file '.sp-tmp/<session id>/preflight-<phase>.json'`. A LOW confidence does not stop the run. The value goes into `session.json`, and the person sees it in the final answer.
   3. Run the agents of the phase. For assess, structure and architect: start `strategic-partnerships:assess-agent`, `strategic-partnerships:structure-agent` or `strategic-partnerships:architect-agent` with `session_id` and `product_context`. For discover and monetize: read the section `## Phase steps` of `${CLAUDE_PLUGIN_ROOT}/skills/partnerships-discover/SKILL.md` or `${CLAUDE_PLUGIN_ROOT}/skills/partnerships-monetize/SKILL.md`, and follow it.
   4. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/evaluate_phase.py --phase '<phase>' --session-id '<session id>' --out '.sp-tmp/<session id>/evaluator-<phase>.json'`.
   5. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-evaluator --session-id '<session id>' --phase '<phase>' --from-file '.sp-tmp/<session id>/evaluator-<phase>.json'`. When step 4 exits 1 because the phase file is missing, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --update-evaluator --session-id '<session id>' --phase '<phase>' --result FAIL --gaps 'phase file missing'`. A FAIL does not stop the run. The synthesizer puts the gaps into the risk register.
   6. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --complete-phase --session-id '<session id>' --phase '<phase>'`.

   When a script exits 2 (the session id is not a plain name), start no more agents, and say that the run failed with the message of the script.
6. Start `strategic-partnerships:synthesizer` with `session_id`. Wait for it to end. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --complete --session-id '<session id>'`.
7. When the synthesizer ends with `DONE: strategic-partnerships`, read `.sp-tmp/<session id>/session.json` and `.sp-tmp/<session id>/synthesize.md`, and show the person:
   - the go or no-go result (the `go_no_go` key in the header of `synthesize.md`)
   - the path `.sp-tmp/<session id>/synthesize.md`
   - each phase with a LOW value in `preflight_scores`: an earlier phase file was missing or thin, and the phase still ran
   - each phase with a FAIL value in `evaluator_scores`: the phase file lacks a rubric section, and the synthesizer put the gap into the risk register
8. When the synthesizer does not end with `DONE: strategic-partnerships`, or a script exited 2, say that the run failed. Show the last lines.
