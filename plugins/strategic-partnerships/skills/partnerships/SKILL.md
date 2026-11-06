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
5. Dispatch `strategic-partnerships:orchestrator` with the `Agent` tool in the foreground (set no `run_in_background`), and give it `session_id` and `product_context` (the 5 fields). The run takes time. A run with `claude -p` stops your turn when you end it, so end it only after the orchestrator returns its last line.
6. When the orchestrator ends with `DONE: strategic-partnerships`, read `.sp-tmp/<session id>/session.json` and `.sp-tmp/<session id>/synthesize.md`, and show the person:
   - the go or no-go result (the `go_no_go` key in the header of `synthesize.md`)
   - the path `.sp-tmp/<session id>/synthesize.md`
   - each phase with a LOW value in `preflight_scores`: an earlier phase file was missing or thin, and the phase still ran
   - each phase with a FAIL value in `evaluator_scores`: the phase file lacks a rubric section, and the synthesizer put the gap into the risk register
7. When the orchestrator does not end with `DONE: strategic-partnerships`, say that the run failed. Show its last lines.
