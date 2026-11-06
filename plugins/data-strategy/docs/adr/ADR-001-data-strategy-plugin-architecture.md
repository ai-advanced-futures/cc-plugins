# ADR-001: data-strategy plugin architecture

**Status:** Accepted
**Date:** 2026-03-10 (written again for the port, version 0.2.0)
**Author:** Luis F. Amadeo
**Plugin:** `data-strategy`

---

## Context

Software companies need to know if their data investments fit their strategy, if the data platform is sound, and if the data products have value. No other plugin of this marketplace does this work as a whole:

- It starts from business outcomes, not from signals in a codebase.
- It joins six frameworks across three domains, and it settles the conflicts between them.
- It writes deliverables for more than one audience.

---

## Decisions

### D1: A separate plugin

The plugin is separate from any codebase-architecture plugin.

**Reason:**
- This plugin starts from business questions. A codebase plugin starts from a scan of the code.
- Separate versions let each plugin change at its own speed.

### D2: Four steps with files between them

The agents share data through files in the session folder `.data-strategy-tmp/{session_id}/`:

- **Intake:** a skill asks the person and writes `context.yaml`.
- **Assessment:** 3 domain agents run in parallel and write 3 domain files.
- **Synthesis:** the `synthesizer` (opus, two passes) writes `synthesis.md`.
- **Deliverables:** the `deliverable-generator` writes 3 output documents.

**Reason:** The 3 domains are independent when they assess, and they depend on each other when they are joined. Parallel assessment saves time. A separate synthesizer finds the conflicts between frameworks, and a domain agent cannot see them alone.

### D3: Only the skills ask the person

Claude Code removes `AskUserQuestion` from each subagent. So only a skill asks the person a question. A skill reads `docs/intake.md`, asks, writes `context.yaml`, and starts one agent. The `orchestrator` and the other agents ask nothing.

The full run goes in this order:

1. The skill `data-strategy` asks all the questions, makes the session with `session_manager.py create`, and writes `context.yaml`.
2. The skill starts `data-strategy:orchestrator` with `session_id` and `output_dir`.
3. The orchestrator starts the 3 domain agents with 3 `Agent` calls in one message. Each call waits for its agent.
4. The orchestrator runs `session_manager.py all-done` to check the 3 `.done` flags.
5. The orchestrator starts the `synthesizer`, then the `deliverable-generator`.
6. The orchestrator ends with the line `DONE: data-strategy`.

The skills `strategy`, `platform`, and `products` ask only the questions that their agent reads, make a session with one domain, and start the domain agent directly. The skill `roadmap` asks nothing. It starts the `deliverable-generator` with an earlier session.

**Reason:** A file flag shows completion with no other channel. Each step is a plain call that the orchestrator can check. No agent talks to another agent by message, so a failure shows as a missing file.

### D4: Six frameworks, three domains

Each framework belongs to one agent. This stops two agents from judging the same concept in two ways.

| Framework | Agent | Domain |
|-----------|-------|--------|
| DAMA-DMBOK (11 knowledge areas) | `strategy-assessor` | Governance maturity |
| Gartner D&A Maturity (5 levels) | `strategy-assessor` | Business maturity |
| Data Mesh (Dehghani, 4 principles) | `platform-auditor` | Architecture |
| Data Engineering Lifecycle (Reis and Housley) | `platform-auditor` | Implementation |
| Data as a Product (DJ Patil, Dehghani) | `product-analyst` | Product portfolio |
| Data Contracts (Andrew Jones) | `product-analyst` | Producer and consumer rules |

DAMA assumes central data stewardship. Data Mesh assumes that each domain owns its data. The two disagree. The `synthesizer` names the conflict, shows both positions, and gives a recommendation for the company.

Each domain file starts with a YAML header. The synthesizer reads the headers first and reads the full text only when it needs to:

```yaml
---
domain: {strategy|platform|products}
slug: {strategy|platform|products}
gap_flag: {none|minor|major}         # "major" starts the full read
framework_conflict: {none|detected}  # "detected" starts the full read
maturity_level: {1|2|3|4|5}
top_risks: {integer}
constitution_check: {pass|partial|fail}
---
```

### D5: Three deliverables

| Deliverable | File | Audience | Format |
|-------------|------|----------|--------|
| Strategy report | `strategy-report.md` | CPO, CDO | Markdown |
| Architecture decision record | `data-platform-adr.md` | Engineering leads | Markdown (extended Nygard) |
| Data roadmap | `data-roadmap.md` | Product and engineering | Markdown with an effort and impact matrix |

### D6: Python scripts for the numbers

Scripts do all scoring, maturity levels, roadmap groups, and session flags. The agents do not calculate them. The same input gives the same score on each run, and the unit tests cover the scripts.

The agent writes the input to a JSON file in the session folder and runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <input.json>`. Each scoring script prints one JSON object. A bad or missing file gives one line on stderr and exit code 1. Each script starts with a PEP 723 block, so `uv run` needs no setup.

There are 6 scripts: `dama_scorer.py`, `maturity_calculator.py`, `data_mesh_evaluator.py`, `product_portfolio_scorer.py`, `roadmap_builder.py`, and `session_manager.py`.

---

## Consequences

### Good
- The plugin covers a problem that no other plugin of this marketplace covers.
- The conflict between DAMA and Data Mesh is explicit.
- The YAML headers let the synthesizer read less text.
- A missing file shows each failed step.
- The 3 deliverables serve three audiences.

### Bad
- The 3 domain agents run in parallel. The synthesizer must wait for all 3.
- The opus synthesizer costs more time and money than a smaller model.
- Six frameworks make `frameworks.md` long. Each agent reads only its own part, marked with `§` comments.

### Risks
- **Gartner maturity is subjective.** The person gives the ratings, and `maturity_calculator.py` scores them. The agents do not guess a rating.
- **The synthesizer can miss the DAMA and Data Mesh conflict.** The header value `framework_conflict: detected` forces the full read.
- **Web search can send company words.** The 3 domain agents have `WebSearch`. A query can hold words from the company context.

---

## Alternatives considered

### Alt 1: Extend a codebase-architecture plugin
Rejected. The business-first questions do not fit a plugin that starts from a scan of the code.

### Alt 2: Only separate commands, with no full run
Rejected. The person would run strategy, platform, and products by hand to get the joined result. The deliverables need all 3 domains in one session.

### Alt 3: All agents talk by messages
Rejected. A subagent cannot ask the person, and a message between agents adds a channel that can fail with no trace. Files in the session folder are plain and can be checked.

---

## References

- Zhamak Dehghani, *Data Mesh* (2022)
- DAMA International, *DMBOK2* (2017)
- Joe Reis and Matt Housley, *Fundamentals of Data Engineering* (2022)
- DJ Patil, *Data Jujitsu* (2012); Andrew Jones, *Driving Data Quality with Data Contracts* (2023)
