# ADR-002: From Skills Only to an 11-Agent Pipeline

**Date:** 2026-03-04
**Status:** Accepted (amended for the marketplace port)
**Supersedes:** Decision 1 of ADR-001 (Skill-Only Architecture)

---

## Context

The first version of the plugin used only skills: 6 SKILL.md files loaded into the context window of Claude, with all framework analysis done in that context. This worked well for interactive use, but it had two limits:

1. **Context compaction.** A full 6-phase partnership analysis can collect 80,000 to 120,000 tokens in one context window. When the work spans many hours or sessions, compaction cuts the output of the earlier phases. The quality of the synthesis then drops.

2. **Apollo response size.** A raw Apollo company enrichment answer has 50 to 100 fields for each company. An answer for 10 companies, passed to an agent, uses 15,000 to 20,000 context tokens. Most of these tokens are noise (social URLs, SEO data, funding metadata).

These two limits needed a change of architecture.

---

## Decision

Change the full run from skills only to an **11-agent pipeline that passes data between agents through files**. The phase skills stay as a quick path for interactive use.

The pipeline has:
- A thin **orchestrator** (sonnet). It starts the agents in order with the `Agent` tool, and it reads only `session.json` between starts.
- 5 **phase agents** (sonnet): assess, discover, structure, architect, monetize. Each writes its output to `.sp-tmp/<session_id>/<phase>.md` and returns only `DONE: <phase>`.
- 1 **synthesizer** (opus). It writes `synthesize.md`.
- A **discover-agent** that starts 6 **discover-worker** agents (haiku) in parallel, one for each partnership model of Popp. It merges their results and starts the apollo-enricher.
- An **apollo-enricher** (haiku). It calls the Apollo server when the person added one, keeps 10 fields with an allowlist (`apollo_extractor.py`), and writes a compact table of about 600 tokens.
- A **pre-flight-agent** (haiku). It runs `simulate_phase.py` before each phase to check the inputs (HIGH, MEDIUM, or LOW confidence).
- An **evaluator-agent** (haiku). It runs `evaluate_phase.py` after each phase to check the output (PASS or FAIL, with a gap list).

The skill `partnerships` starts the full run. It is the only part that asks the person.

---

## Rationale

### Questions only in skills

Claude Code removes `AskUserQuestion` from every subagent. So an agent cannot ask the person. The skill `partnerships` runs in the main conversation. It takes the 5 product context fields from the words of the person (name, category, target market, existing integrations, partnership goals), and it asks for the missing fields. Then it makes the session with `session_manager.py`, and it starts the orchestrator with `session_id` and `product_context`. The orchestrator asks nothing. If a field is absent, it writes no file and ends with `DONE: strategic-partnerships FAILED: session_id and product_context are required`.

### Run order

For each phase in the order assess, discover, structure, architect, monetize, the orchestrator does these steps:
1. Start `strategic-partnerships:pre-flight-agent`.
2. Start the phase agent with `session_id` and `product_context`.
3. Start `strategic-partnerships:evaluator-agent`.
4. Run `session_manager.py --complete-phase`.

Then it starts `strategic-partnerships:synthesizer`, runs `session_manager.py --complete`, and ends with `DONE: strategic-partnerships`. The skill reads `session.json` and `synthesize.md`, and it shows the go or no-go result.

A LOW pre-flight confidence does not stop the run. The pre-flight agent records it in `session.json`. A FAIL of the evaluator does not stop the run either. The synthesizer puts the gaps in the risk register. No agent can ask the person, so a stop would have no answer.

### Nesting

The deepest chain is: main conversation, then `orchestrator` (layer 1), then `discover-agent` (layer 2), then the 6 `discover-worker` agents and the `apollo-enricher` (layer 3). Claude Code allows up to three layers below the main conversation. The agents of layer 3 start no agent. A plugin that starts the orchestrator from a subagent puts the workers in layer 4, and Claude Code then withholds the `Agent` tool from the discover agent.

### File-based protocol

Each phase agent writes its output to disk and returns only `DONE: <phase>`. The orchestrator never keeps phase content in its context. Its context stays at about 3K tokens, no matter how many phases are complete.

We considered a different design: the Agent tool returns the phase output to the caller. We rejected it, because return values collect in the context of the caller. This is the compaction problem that this change solves.

### Haiku for extraction and checks

The apollo-enricher, the discover workers, the pre-flight agent, and the evaluator agent do structured extraction and rule checks. They need no deep judgment. Haiku costs far less than opus and answers faster.

We considered sonnet for all agents. We rejected it, because haiku does these tasks with the same accuracy at a lower cost.

### Apollo is optional, and it is isolated

The apollo-enricher is a context firewall. It receives the raw Apollo answer, writes it to `apollo-raw.json`, runs the allowlist in `apollo_extractor.py`, and writes only a compact table to `apollo-enrichment.md`. The raw answer never reaches the orchestrator or the discover agent.

Apollo is an outside tool that the person adds with `claude mcp add apollo`. The enricher has the tool entry `mcp__apollo__*`. When the server is absent or the call fails, the enricher writes a notice to `apollo-enrichment.md`, and the discover agent goes on. The plugin starts no outside service and holds no key.

### Opus for synthesis

The synthesizer is the step with the most judgment. It combines 5 phase outputs, resolves conflicts, and writes a go or no-go recommendation with numbers. It uses two passes:
- **Pass 1:** read only the YAML headers of all phase files (about 42 lines for each file) to find the phases with a FAIL.
- **Pass 2:** read the full text only for the phases with a FAIL.

This keeps the context of the synthesizer at about 12K tokens when all phases are complete.

### Session folder and cleanup

Each run uses `.sp-tmp/<session_id>/` in the current folder of the person. The folder holds `session.json` and all phase files. `session_manager.py --sweep` removes the folders in `.sp-tmp/` that are older than 60 minutes and have no `completed_at`. This recovers from a crash. The sweep checks only folders in `.sp-tmp/`, so it cannot remove `.sp-tmp/` itself or a session that is younger than 60 minutes. `session_manager.py --complete` sets `completed_at`. A complete session stays until the person deletes it, because `synthesize.md` is the report of the person.

### No handoff file

The first agent version wrote a handoff file for a pipeline plugin of the source repository. No plugin of this marketplace reads that file, so the port removes the file and the step that writes it. If a later plugin needs a handoff, that plugin adds it again.

---

## Consequences

**Positive:**
- The context of the orchestrator stays small, no matter how long the pipeline is.
- Apollo data is about 600 tokens, and not 15,000 to 20,000.
- The pre-flight agent and the evaluator agent add quality checks with no person in the loop.
- After a failure, the phase files stay on disk.
- Python scripts do the math and the checks, and the scripts have tests.
- The plugin works when no Apollo server is present.

**Negative:**
- The plugin has 11 agent files to maintain.
- A complete session folder stays in `.sp-tmp/` until the person deletes it.
- The discover phase is more complex: 6 parallel workers, one enricher, and a merge.
- A full run takes time and costs more than a phase skill.

**Neutral:**
- The phase skills stay as a quick path. They apply the framework in the conversation, and a person can ask them for a scored analysis too.

---

## Compliance

- Context protection: the orchestrator reads `session.json` only, and never the phase content.
- Math and checks in Python: `partner_scorer`, `npv_calculator`, `ecosystem_health_scorer`, `power_dynamics_scorer`, `simulate_phase`, `evaluate_phase`, `apollo_extractor`, and `session_manager`. Agents and skills run them as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`.
- Judgment and text in agents.
- No agent has `AskUserQuestion` or `Task` in its `tools:` list.
- The orchestrator ends with `DONE: strategic-partnerships` as its last line.

---

## References

- `ADR-001-strategic-partnerships-plugin-architecture.md`: the first architecture (skills only)
- Popp & Meyer, *Profit from Software Ecosystems*: the frameworks that all phase agents use
