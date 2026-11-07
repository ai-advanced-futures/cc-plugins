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
- **Assessment:** 3 domain agents run one after the other and write 3 domain files.
- **Synthesis:** the `synthesizer` (opus, two passes) writes `synthesis.md`.
- **Deliverables:** the `deliverable-generator` writes 3 output documents.

**Reason:** The 3 domains are independent when they assess, and they depend on each other when they are joined. Separate assessment keeps each domain agent small: it reads only its part of `frameworks.md`. A separate synthesizer finds the conflicts between frameworks, and a domain agent cannot see them alone.

### D3: Only the skills ask the person

Claude Code removes `AskUserQuestion` from each subagent. So only a skill asks the person a question. A skill reads `docs/intake.md`, asks, writes `context.yaml`, and starts the agents. The agents ask nothing.

The full run goes in this order:

1. The skill `data-strategy` asks all the questions, makes the session with `session_manager.py new`, and writes `context.yaml`.
2. The skill writes the answer files and runs the 3 scorers of the strategy and platform domains with `--out`.
3. The skill starts the 3 domain agents with 3 `Agent` calls, one at a time, each in the foreground. An agent that runs in the background returns in a new turn that does not have the `allowed-tools` of the skill, and the next script is then refused. `product-analyst` writes its input file (`step: inputs`).
4. The skill runs `product_portfolio_scorer.py`, and starts `product-analyst` again (`step: report`).
5. The skill writes the 3 `.done` flags, and runs `session_manager.py all-done` to check them.
6. The skill starts the `synthesizer` (`step: inputs`), runs `roadmap_builder.py`, starts the `synthesizer` again (`step: report`), and starts the `deliverable-generator`.

No agent starts an agent, so the skill does this work in the main conversation.

The skills `strategy`, `platform`, and `products` ask only the questions that their agent reads, make a session with one domain, and start the domain agent directly. The skill `roadmap` asks nothing. It starts the `deliverable-generator` with an earlier session.

**Reason:** A file flag shows completion with no other channel. Each step is a plain call that the skill can check. No agent talks to another agent by message, so a failure shows as a missing file.

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

A JSON file in the session folder holds the input. The skill runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <input.json> --out <output.json>`, and the agent reads the output file. When an agent makes the input, it writes the input file and returns, and the skill runs the script. So no agent has `Bash`. A scoring script writes its JSON object to the output file and prints one line. Without `--out`, it prints the object. A bad or missing file gives one line on stderr and exit code 1. Each script starts with a PEP 723 block, so `uv run` needs no setup.

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
- The 3 domain agents run one after the other, so the run is slower than a parallel start. The synthesizer must wait for all 3.
- The opus synthesizer costs more time and money than a smaller model.
- Six frameworks make `frameworks.md` long. Each agent reads only its own part, marked with `§` comments.

### Risks
- **Gartner maturity is subjective.** The person gives the ratings, and `maturity_calculator.py` scores them. The agents do not guess a rating.
- **The synthesizer can miss the DAMA and Data Mesh conflict.** The header value `framework_conflict: detected` forces the full read.
- **The main conversation holds all the dispatches.** The skill `data-strategy` starts 7 agent runs, one at a time in the foreground, and runs 15 script calls, so its context grows. Each agent returns one line and each script prints one line. No agent has `WebSearch`, `Bash`, or `Agent`.

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
