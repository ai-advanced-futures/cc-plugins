---
name: vendor-archetype-classify
description: Classifies the current pricing of a vendor into one of the 5 canonical agentic-pricing archetypes. Use when the person wants to know which archetype the pricing page of a vendor maps to, or wants to refresh the Wave 1 vendor registry.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vendor_archetype_emitter.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py *), Skill, Edit(/.competitive-intelligence/**), Read(//**/skills/vendor-archetype-classify/reference/archetype-reference-card.md)
---

# Vendor Archetype Classification

This skill classifies the current pricing model of a vendor into one of the five canonical vendor archetypes (JustKeenAI v2.1 Chapter 1). You run in the main conversation, so you ask the person and you run the program. The agent `competitive-intelligence:vendor-archetype-classifier-agent` cannot ask and has no shell.

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <args>`, one command per Bash call. Never run inline code in any language, and write every file with the Write tool, because only this plugin's scripts run with no question to the person.

## When to use

- Classify a single vendor's pricing page → archetype.
- Audit / refresh the 22-vendor Wave 1 seed registry (`definitions/wave1-vendors.json`).

## How it works

1. Ask the person for the vendor name and its pricing page with `AskUserQuestion`, unless the person already gave them. The page is a URL or a pasted text. For a registry refresh, read `${CLAUDE_PLUGIN_ROOT}/definitions/wave1-vendors.json`, ask which vendors to refresh, and use the `vendor_name` and `pricing_page_url` of each.
2. Dispatch `competitive-intelligence:vendor-archetype-classifier-agent` with the `Agent` tool, in the foreground: set `run_in_background: false`. Give it `vendor_name`, and `pricing_page_url` or `pricing_page_text`. Wait for it to finish. For a registry refresh, dispatch it for one vendor, run steps 4 to 6 for that vendor, and only then dispatch it for the next one, because each vendor uses the same input file.
3. The agent extracts seven boolean pricing signals from the pricing page of the vendor, writes them to `.competitive-intelligence/vendor-archetype-input.json`, and ends with the line `INPUT: .competitive-intelligence/vendor-archetype-input.json`. If it reports a gap, show the gap to the person and stop.
4. Run the emitter on the input file, from the project folder, on its own:
   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vendor_archetype_emitter.py --input .competitive-intelligence/vendor-archetype-input.json --output-dir .`
   When the script fails to import a package, show a gap that names the missing package and stop. Make up no output, because the handoff file must come from the emitter.
5. The deterministic Python classifier (`scripts/vendor_archetype_classifier.py`, which the emitter calls) maps the signals to one of: `pure_outcome_absorbed`, `hybrid_platform_outcome`, `pure_per_seat` (+ `seat_anchor`), `hybrid_seat_meter`, `pure_passthrough`. The emitter writes `.competitive-intelligence/vendor-archetype-classification.json` (the federation artifact, `audience: mixed`) and a handoff file.
6. Read `.competitive-intelligence/vendor-archetype-handoff.json`. Show the person the `state`. For `success`, show the archetype and the `best_in_class_pattern`. For `blocked` or `error`, show the `reason`.
7. When the state is `success`, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root . ingest .competitive-intelligence/vendor-archetype-classification.json` on its own, from the project folder, as in step 4. When the output holds an `INIT:` line, show that line. When the command exits 1, show its errors, say that the result stays in the file, and do not report success. Then stop: do not write or change a file in `.competitive-intelligence/` or in the graph, and do not run `ingest` again in this turn, because the graph would then hold data that no step of this skill made. Else show the `ingested` line. Ask one question: "Learn these results?" Ask it with `AskUserQuestion` [q: none], with the options `Yes` and `No`, in this turn. On yes, run the skill `competitive-intelligence:learn` with the run ID in the `ingested` line. When you have no `AskUserQuestion` tool, for example in `claude -p`, do not write the question as text, because the answer then comes in a new turn, and the new turn does not have the tools of this skill. Write this line in your reply, on its own line, with the run ID in the `ingested` line: `Next: /competitive-intelligence:learn <RUN ID>`.

If the agent reports a gap (no pricing page), show the gap to the person and stop.

Take the archetype from the classifier output, because the classifier is a deterministic script.

When the person asks what a signal or an archetype means, or asks for the anchor vendors of an archetype, read `${CLAUDE_SKILL_DIR}/reference/archetype-reference-card.md`. It holds the signal rubric and the 5-archetype definitions with framework citations.
