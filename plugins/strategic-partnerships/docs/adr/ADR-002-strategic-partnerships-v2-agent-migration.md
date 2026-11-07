# ADR-002: From Skills Only to an 8-Agent Pipeline

**Date:** 2026-03-04
**Amended:** 2026-11-06
**Status:** Accepted (amended for the marketplace port)
**Supersedes:** Decision 1 of ADR-001 (Skill-Only Architecture)

---

## Context

The first version of the plugin used only skills: 6 SKILL.md files loaded into the context window of Claude, with all framework analysis done in that context. This worked well for interactive use, but it had two limits:

1. **Context compaction.** A full 6-phase partnership analysis can collect 80,000 to 120,000 tokens in one context window. When the work spans many hours or sessions, compaction cuts the output of the earlier phases. The quality of the synthesis then drops.

2. **Apollo response size.** A raw Apollo company enrichment answer has 50 to 100 fields for each company. An answer for 10 companies, passed to an agent, uses 15,000 to 20,000 context tokens. Most of these tokens are noise (social URLs, SEO data, funding metadata).

These two limits needed a change of architecture. A third need is a narrow tool grant: an agent that can run any shell command, or start any agent, has more power than its work needs.

---

## Decision

Change the full run from skills only to an **8-agent pipeline that passes data between agents through files**. The skills run the scripts and start the agents. No agent has `Bash`, `Agent` or `Skill`. The phase skills stay as a quick path for interactive use.

The pipeline has:
- 5 **phase agents** (sonnet): assess, discover, structure, architect, monetize. Each writes its output to `.sp-tmp/<session_id>/<phase>.md` and returns only `DONE: <phase>`. They have `Read` and `Write`.
- 1 **synthesizer** (opus). It writes `synthesize.md`. It has `Read` and `Write`.
- 6 **discover-worker** agents (haiku) in parallel, one for each partnership model of Popp. They have `Read` and `Write`.
- An **apollo-enricher** (haiku). It has `Read`, `Write` and the one tool `mcp__apollo__apollo_bulk_enrich_organizations`. It calls the Apollo server when the person added one, and it writes the raw answer to `apollo-raw.json`.

The **discover-agent** and the **monetize-agent** each run in two steps, because a script runs between the two parts that need judgment:
- discover-agent, `step: inputs`: merge the candidates and score the ecosystem and the power position. `step: report`: write `discover.md` from the results of the scorer scripts.
- monetize-agent, `step: inputs`: write the revenue projections and the NPV input. `step: report`: write `monetize.md` from the result of the NPV script.

The skill `partnerships` runs the loop of the 5 phases in the main conversation. The skills `partnerships-discover` and `partnerships-monetize` hold a `## Phase steps` section that both the full run and the single phase follow. The skills run `apollo_extractor.py` on the raw Apollo answer, and the scripts `simulate_phase.py`, `evaluate_phase.py`, the 3 scorers and `npv_calculator.py`. The skill `partnerships` is the only part that asks the person.

---

## Rationale

### Questions only in skills

Claude Code removes `AskUserQuestion` from every subagent. So an agent cannot ask the person. The skill `partnerships` runs in the main conversation. It takes the 5 product context fields from the words of the person (name, category, target market, existing integrations, partnership goals), and it asks for the missing fields. Then it makes the session with `session_manager.py`, and it starts each agent with `session_id` and `product_context`. The agents ask nothing.

### Run order

For each phase in the order assess, discover, structure, architect, monetize, the skill `partnerships` does these steps:
1. Run `simulate_phase.py` with `--out`, and record the confidence with `session_manager.py --update-preflight --from-file`.
2. Run the agents of the phase with `session_id` and `product_context`. For discover and monetize, follow the `## Phase steps` of the phase skill.
3. Run `evaluate_phase.py` with `--out`, and record the result with `session_manager.py --update-evaluator --from-file`.
4. Run `session_manager.py --complete-phase`.

Then it starts `strategic-partnerships:synthesizer` and runs `session_manager.py --complete`. When the synthesizer ends with `DONE: strategic-partnerships`, the skill reads `session.json` and `synthesize.md`, and it shows the go or no-go result.

A LOW pre-flight confidence does not stop the run. The skill records it in `session.json`. A FAIL of the evaluator does not stop the run either. The synthesizer puts the gaps in the risk register. No agent can ask the person, so a stop would have no answer.

### Narrow grants

An agent with `Bash` can run any command, and an agent with `Agent` can start any agent. A wrong or injected instruction in a file that an agent reads then has a wide effect. The agents of this plugin need only to read and write files, so they have only `Read` and `Write`. The one outside tool has its full name, and no wildcard, so a new tool of the Apollo server does not reach the agent with no review. The test `tests/unit/test_agent_grants.py` fails on a `Bash`, `Agent`, `Skill` or `mcp__<server>__*` entry in `agents/`.

The scripts print one line when they run with `--out`, and the result is in a file. The main conversation carries a small line for each script, and no result text.

### Nesting

Each agent runs one layer below the main conversation. No agent starts another agent, so Claude Code needs no nesting depth and withholds no tool.

### File-based protocol

Each phase agent writes its output to disk and returns only `DONE: <phase>`. The main conversation never keeps phase content in its context, because it reads `session.json` and the last output file only.

We considered a different design: the Agent tool returns the phase output to the caller. We rejected it, because return values collect in the context of the caller. This is the compaction problem that this change solves.

### Haiku for extraction

The apollo-enricher and the discover workers do structured extraction. They need no deep judgment. Haiku costs far less than opus and answers faster.

We considered sonnet for all agents. We rejected it, because haiku does these tasks with the same accuracy at a lower cost.

### Apollo is optional, and it is isolated

The apollo-enricher is a context firewall. It receives the raw Apollo answer and writes it to `apollo-raw.json`. The skill runs the allowlist in `apollo_extractor.py`, and the script writes only a compact table to `apollo-enrichment.md`. The raw answer never reaches the main conversation or the discover agent.

Apollo is an outside tool that the person adds with `claude mcp add apollo`. When the server is absent or the call fails, the enricher writes a notice to `apollo-enrichment.md`, and the run goes on. The plugin starts no outside service and holds no key.

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
- The main conversation stays small, no matter how long the pipeline is.
- Apollo data is about 600 tokens, and not 15,000 to 20,000.
- No agent can run a shell command or start an agent.
- The pre-flight check and the evaluator check add quality checks with no person in the loop.
- After a failure, the phase files stay on disk.
- Python scripts do the math and the checks, and the scripts have tests.
- The plugin works when no Apollo server is present.

**Negative:**
- The plugin has 8 agent files to maintain.
- The skill `partnerships` holds the run loop, so a long full run keeps its steps in the main conversation.
- A complete session folder stays in `.sp-tmp/` until the person deletes it.
- The discover phase is more complex: 6 parallel workers, one enricher, two steps of the discover agent, and a merge.
- A full run takes time and costs more than a phase skill.

**Neutral:**
- The phase skills stay as a quick path. They apply the framework in the conversation, and a person can ask them for a scored analysis too.

---

## Compliance

- Grants: no agent has `Bash`, `Agent`, `Skill` or a `mcp__<server>__*` wildcard in its `tools:` list. `tests/unit/test_agent_grants.py` checks this.
- Context protection: the main conversation reads `session.json` and the last output file only, and never the phase content of the other phases.
- Math and checks in Python: `partner_scorer`, `npv_calculator`, `ecosystem_health_scorer`, `power_dynamics_scorer`, `simulate_phase`, `evaluate_phase`, `apollo_extractor`, and `session_manager`. Only skills run them, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`.
- Judgment and text in agents.
- No agent has `AskUserQuestion` or `Task` in its `tools:` list.
- The synthesizer ends with `DONE: strategic-partnerships` as its last line.

---

## References

- `ADR-001-strategic-partnerships-plugin-architecture.md`: the first architecture (skills only)
- Popp & Meyer, *Profit from Software Ecosystems*: the frameworks that all phase agents use
