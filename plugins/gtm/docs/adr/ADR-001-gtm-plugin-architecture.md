# ADR-001: GTM plugin architecture

**Status:** Accepted
**Date:** 2026-02-24
**Updated:** 2026-02-28 (thin coordinator, parallel waves, definitions as the source of truth, integrity hardening)
**Updated:** 2026-11-05 (port to this marketplace: the run order, the optional tools)
**Updated:** 2026-11-06 (STORY-177: the score and band come from truth_tier_validator.py; band choice holds the output)

---

## Context

The plugin must cover the full revenue cycle, from brand identity to closed revenue. It must also stop a known failure of AI marketing: a claim about the product that is larger than the product.

Constraints:

- The plugin must work with no outside tool. An MCP server is optional. When a server is missing, the step uses web research.
- The plugins `value-ip`, `jtbd-market-discovery`, `competitive-intelligence`, and `pricing` are sources of evidence. They are optional. The plugin works without them.
- Each artifact must pass an integrity gate before delivery.
- Field intelligence from real customer calls overrides the default of a framework when the two conflict.
- A subagent cannot ask the person a question. Only a command or a skill, which runs in the main conversation, can ask.

---

## Decision

### Many agents and one mandatory integrity gate

The plugin has 13 agents. The integrity agent runs after each content agent, on every path. No artifact reaches the person before it passes the gate.

| Agent | Model | Role |
|---|---|---|
| `orchestrator` | sonnet | Reads the dispatch fields, runs the waves, and holds the session state |
| `brand-agent` | opus | Brand identity, voice, and positioning |
| `marketing-agent` | sonnet | Campaigns, content, and launch plans |
| `sales-agent` | sonnet | Pitch outline, prospecting, and pipeline coaching |
| `funnel-agent` | sonnet | Revenue funnel and bottleneck detection |
| `integrity-agent` | sonnet | Truth Tier audit. It is the gate. |
| `knowledge-agent` | sonnet | Reads call transcripts, win and loss notes, and playbooks |
| `codebase-scanner` | haiku | Scans the product code for real capabilities |
| `research-agent` | haiku | Web research when an MCP server is missing |
| `sales-comp-gate-agent` | sonnet | Sales-comp precondition gate (ADR-003) |
| `marketing-launch-runner`, `marketing-brand-runner`, `marketing-funnel-runner` | sonnet | Routes for a coach plugin (ADR-005) |

### Questions to the person

No agent asks the person a question, and no agent has the `AskUserQuestion` tool. An agent takes its values from the dispatch fields.

- `/gtm:run` asks first. It asks the role, the stage, the goal, the PMF gate, the codebase scan, and the files to read. It then starts the orchestrator with the dispatch fields.
- When the orchestrator needs a choice, it writes `.gtm/open-questions.json`, ends with the line `OPEN: .gtm/open-questions.json`, and stops. The command asks the person and starts the orchestrator again with `resume: true`.
- A score from 0.60 to 0.84 needs a choice: rerun the agent or override. A score below 0.60 stops the run with no question.

### Truth Tier system

Each claim gets a tier when the agent writes it.

| Tier | Label | Evidence | Output rule |
|---|---|---|---|
| 1 | SHIPPED | Code in production, customers use it | State as fact |
| 2 | IN_FLIGHT | Code in progress or early access | "Now in early access" |
| 3 | COMMITTED | Designed, budgeted, scheduled | "Coming in Q3" |
| 4 | STRATEGIC_INTENT | Direction stated, not funded | "Our vision is" |
| 5 | SPECULATION | No evidence | Blocked. It never appears. |

The integrity score is `(total_claims - tier_5_blocked) / total_claims`. The floor is 0.60. The target is 0.85. `scripts/truth_tier_validator.py` computes the score and its band (`floor`, `choice`, `pass`). The orchestrator runs it between the 2 dispatches of each integrity pass. The integrity agent has no shell tool and does not count the score.

### Scripts for exact work

Python scripts do the work that a model must not improvise. A command or an agent runs a script with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. Five scripts have a command line and a PEP 723 block: `result_name.py`, `plugin_integrator.py`, `sales_comp_gate_emitter.py`, `truth_tier_validator.py`, and `output_check.py`. The other scripts are library code with unit tests. Where a text once ran a library script, the text now gives a rule that the model applies from a file in `definitions/` or `schemas/`.

### The definitions folder

The folder `definitions/` holds the shared concepts that each agent and skill must keep the same: the truth tiers, the funnel stages, the integrity score, the superlative word list, MEDDPICC, the bottleneck algorithm, the wave routing, the MQL thresholds, and the map from a command to the MCP servers that it can use. A change to a shared concept goes into `definitions/` first.

### Session state

The file `gtm-context.json` is at the git root. It holds the product, the market, the brand, the learned knowledge, the plugin inputs, and the completion flags. Lists append and remove duplicates. Objections merge by their text, and their counts add up.

The key `plugin_inputs` holds `competitive_intelligence`, `jtbd`, and `pricing`, each with a list of paths from `plugin_integrator.py`. It holds `value_ip` only when the script finds the scorecard of `value-ip`.

---

## Alternatives considered

1. **One large agent.** Rejected. It exceeds the context window for a full-funnel job. It has no integrity isolation.
2. **Scripts only, no agents.** Rejected. Marketing strategy needs judgment that fixed code cannot give.
3. **MCP servers as a requirement.** Rejected. Most people do not have them. Web research covers most cases.
4. **An integrity audit that the person may skip.** Rejected. An optional step is a skipped step.

---

## Consequences

**Positive:**

- A Tier 5 claim never reaches the person.
- The brand agent uses the opus model for the most important output.
- Real customer evidence overrides theory.
- The scripts do the exact math. The model does not guess numbers.
- The plugin works with no MCP server and no optional plugin.

**Negative:**

- More agents add latency. The scanner and the research agent use the haiku model to reduce it.
- A file holds the session state. This does not suit many people who work at the same time.
- The integrity gate adds one model call for each path. This is intended.

---

## Amendments of 2026-02-28

### Thin coordinator

The orchestrator reads only `completion_flags` and one short `completion_log` line of each agent from `gtm-context.json`. The artifacts move through files:

- `.gtm/working/<agent>/` holds the drafts of the content agents.
- `gtm-output/` holds the final artifacts. Only the integrity agent writes there.
- `.gtm/audit/` holds the audit of each agent.

The context use of the orchestrator stays the same for a build of any size.

### Waves

```
Wave 0: knowledge-agent and codebase-scanner   (when the dispatch fields ask for them)
Wave 1: brand-agent, then integrity-agent (brand)
Wave 2: marketing-agent and sales-agent in one message, then integrity-agent for each
Wave 3: funnel-agent, then integrity-agent (funnel), then the consolidated audit
```

Each wave uses foreground `Agent` calls. After each call, the orchestrator reads `completion_flags`. The file `definitions/wave-routing.json` holds the agents of each wave.

### Preliminary MQL seed

The orchestrator derives a first MQL definition from the stage, with `gtm_init.seed_mql()`. The marketing agent and the sales agent read it, and so they run at the same time. The funnel agent corrects any difference in Wave 3. The SQL definition must stay a superset of the MQL definition.

### Definitions as machine-readable data

| File | Content | Reader |
|---|---|---|
| `definitions/superlatives.txt` | Word list for superlative detection | `truth_tier_validator.py` |
| `definitions/wave-routing.json` | Agents of each wave | `gtm_completion_manager.py` |
| `definitions/mcp-commands.json` | Command to MCP server map | `/gtm:setup` |
| `definitions/mql-thresholds.json` | MQL threshold for each stage | `gtm_init.py` |
| `definitions/integrity-score.md` | Score formula and thresholds | `gtm_constants.py` |

### Constants

The file `scripts/gtm_constants.py` holds the agent name lists and the integrity thresholds. `gtm_init.py` and `gtm_completion_manager.py` import them. A test checks this.

### Integrity hardening

- A score from 0.60 to 0.84 (band `choice`) writes no file to `gtm-output/`. The flag `completion_flags.<agent>_integrity` stays false until the person chooses rerun or override.
- When the person overrides a score from 0.60 to 0.84, the integrity agent runs again in phase `write` with `override_flag=true`. It writes the drafts, with the Tier 5 claims removed, to `gtm-output/`.
- A score below 0.60 (band `floor`) always stops the run.
- The consolidated audit runs only when all four audits exist and no band is `floor` (a band `choice` counts only after its override).
- A superlative with no source is Tier 5. It is blocked.

---

## Amendments of the port (2026-11-05)

- Each outside tool is optional: the 7 MCP servers, Docker MCP Toolkit, and the plugins `enterprise-search`, `customer-support`, `sales`, `marketing`, `data`, `value-ip`, and `tech-contracts`. A step uses the tool when the person has it. It works without the tool when not. The plugin starts no outside service, and it has no `.mcp.json` file.
- The `value-ip` scorecard is found at `.value-ip/*/output/value-ip-scorecard.md`. Each `value-ip` claim gets Tier 3 (COMMITTED). With no scorecard, the brand agent works from the capabilities of the product and from the learned knowledge.
- The plugin makes no slide file. `pitch-deck.json` is an outline.
