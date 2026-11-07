# Strategic Partnerships — C4 Architecture Diagrams

## C4 Level 1 — System Context

```mermaid
C4Context
    title Strategic Partnerships — System Context
    Person(user, "User", "Founder / BD / Product Leader")
    System(sp, "strategic-partnerships", "Skills and an 8-agent pipeline: readiness assessment, partner discovery, deal structure, integration architecture, revenue modeling, go or no-go synthesis")
    System_Ext(apollo, "Apollo MCP server", "Optional: company enrichment for partner candidates. The user adds it with claude mcp add.")
    Rel(user, sp, "Runs /strategic-partnerships:*")
    Rel(sp, apollo, "Enriches partner candidates (optional)")
```

---

## C4 Level 2 — Container

```mermaid
C4Container
    title Strategic Partnerships — Container

    Person(user, "User", "Founder / BD / Product Leader")
    System_Ext(apollo, "Apollo MCP server", "Optional company enrichment")

    Container_Boundary(sp, "strategic-partnerships plugin") {
        Container_Boundary(skills, "Skills (main conversation: they run the scripts and start the agents)") {
            Container(full, "partnerships", "skill", "Entry point of the full run: reads the product context, asks for the missing fields, sweeps old sessions, makes the session, runs the loop of the 5 phases, starts the synthesizer, shows the result")
            Container(phaseSkills, "partnerships-assess, -discover, -structure, -architect, -monetize, -recommend", "skills", "Quick path in the conversation, or full quality path that runs the scripts and starts the agents of the phase")
        }

        Container_Boundary(phases, "Phase Agents (Read, Write)") {
            Container(assess, "assess-agent", "sonnet", "Archetype classification, network effects, power dynamics, readiness scorecard")
            Container(discover, "discover-agent", "sonnet", "step inputs: merge the candidates, score the ecosystem and the power position. step report: write discover.md")
            Container(structure, "structure-agent", "sonnet", "Revenue streams, partner tiers, network effects design, term sheet outline")
            Container(arch, "architect-agent", "sonnet", "Platform leadership levers, openness framework, DX gap analysis, integration blueprint")
            Container(monetize, "monetize-agent", "sonnet", "step inputs: revenue projections and the NPV input. step report: ROI verdict and monetize.md")
            Container(synth, "synthesizer", "opus", "Two-pass synthesis: YAML headers, then full text for FAIL phases, then GO/NO-GO")
        }

        Container_Boundary(workers, "Workers") {
            Container(worker, "discover-worker", "haiku", "Single Popp model candidate scan (x6 in parallel), Read and Write")
            Container(enricher, "apollo-enricher", "haiku", "Context firewall: writes the raw Apollo answer to a file. Read, Write and one Apollo tool")
        }

        Container_Boundary(scripts, "Python Scripts (uv run, tested)") {
            Container(sess, "session_manager.py", "Python", "Session lifecycle: init, sweep, update scores (--from-file), complete phase, complete")
            Container(scorer, "partner_scorer.py", "Python", "Weighted score, 4 to 20 range, Priority A/B/C")
            Container(npv, "npv_calculator.py", "Python", "NPV, ROI multiple, GO/CONDITIONAL_GO/NO_GO verdict")
            Container(eco, "ecosystem_health_scorer.py", "Python", "5 Jansen dimensions, health score, at_risk flag")
            Container(power, "power_dynamics_scorer.py", "Python", "4 power factors, net balance, negotiation stance")
            Container(sim, "simulate_phase.py", "Python", "Pre-flight: available inputs, HIGH/MEDIUM/LOW confidence")
            Container(evl, "evaluate_phase.py", "Python", "Post-run: section rubric, PASS/FAIL + gap list")
            Container(ext, "apollo_extractor.py", "Python", "Allowlist: 50+ raw fields, 10 structured fields")
        }

        ContainerDb(session_bus, ".sp-tmp/session_id/", "File system", "Session state and phase output files (assess.md, discover.md, ..., synthesize.md, session.json)")
    }

    Rel(user, full, "Runs")
    Rel(user, phaseSkills, "Runs")
    Rel(full, sess, "Runs --sweep, --init, --update-preflight, --update-evaluator, --complete-phase and --complete")
    Rel(full, sim, "Runs before each phase (--out)")
    Rel(full, evl, "Runs after each phase (--out)")
    Rel(full, assess, "Starts: session_id, product_context")
    Rel(full, structure, "Starts")
    Rel(full, arch, "Starts")
    Rel(full, synth, "Starts")
    Rel(full, phaseSkills, "Reads the Phase steps of partnerships-discover and partnerships-monetize")
    Rel(full, session_bus, "Reads session.json and synthesize.md")
    Rel(phaseSkills, sim, "Full quality path: runs simulate_phase.py")
    Rel(phaseSkills, assess, "Full quality path: starts the phase agents")
    Rel(phaseSkills, worker, "partnerships-discover: starts x6 in parallel")
    Rel(phaseSkills, discover, "partnerships-discover: starts with step inputs, then step report")
    Rel(phaseSkills, scorer, "partnerships-discover: scores candidates (--out)")
    Rel(phaseSkills, eco, "partnerships-discover: scores ecosystem health (--out)")
    Rel(phaseSkills, power, "partnerships-discover: scores power dynamics (--out)")
    Rel(phaseSkills, enricher, "partnerships-discover: starts (Priority A/B, max 10)")
    Rel(phaseSkills, ext, "partnerships-discover: applies the field allowlist (--out)")
    Rel(phaseSkills, monetize, "partnerships-monetize: starts with step inputs, then step report")
    Rel(phaseSkills, npv, "partnerships-monetize: calculates NPV and verdict (--out)")
    Rel(assess, session_bus, "Writes assess.md, DONE: assess")
    Rel(discover, session_bus, "Writes candidates.json, the scorer inputs and discover.md")
    Rel(enricher, apollo, "apollo_bulk_enrich_organizations (optional)")
    Rel(enricher, session_bus, "Writes apollo-raw.json, or the fallback notice")
    Rel(synth, session_bus, "Reads all phase .md files (two passes), writes synthesize.md")
```

---

## Agent Model Assignment

| Agent | Model | Rationale |
|---|---|---|
| `assess-agent` | sonnet | Framework judgment and qualitative text |
| `discover-agent` | sonnet | Merge and ecosystem scoring logic, and the report |
| `structure-agent` | sonnet | Deal design and network effects analysis |
| `architect-agent` | sonnet | Platform strategy and integration blueprint |
| `monetize-agent` | sonnet | Financial interpretation and Forrester benchmarking |
| `synthesizer` | opus | Step with the most judgment: 5-phase integration and quantified GO/NO-GO |
| `discover-worker` | haiku | Structured scan against a single Popp model: extraction task |
| `apollo-enricher` | haiku | Absorbs the raw Apollo answer into a file: no judgment |

---

## Tool Grants

No agent has `Bash`, `Agent` or `Skill`. The skills run each script and start each agent. The test `tests/unit/test_agent_grants.py` checks this.

| Agent | Tools |
|---|---|
| `assess-agent`, `discover-agent`, `structure-agent`, `architect-agent`, `monetize-agent`, `synthesizer`, `discover-worker` | `Read`, `Write` |
| `apollo-enricher` | `Read`, `Write`, `mcp__apollo__apollo_bulk_enrich_organizations` |

---

## Session Folder Protocol

Each run writes to `.sp-tmp/<session_id>/` in the current folder of the person:

```
.sp-tmp/
└── a1b2c3d4/
    ├── session.json            # Run state: phases_complete, preflight_scores, evaluator_scores, completed_at
    ├── preflight-<phase>.json  # result of simulate_phase.py (--out), input of --update-preflight --from-file
    ├── evaluator-<phase>.json  # result of evaluate_phase.py (--out), input of --update-evaluator --from-file
    ├── assess.md               # assess-agent output
    ├── discover-model-<n>.md   # discover-worker output (n = 1 to 6), with a .json file of the candidates
    ├── candidates.json         # merged candidates, input of partner_scorer.py
    ├── ecosystem-health.json   # input of ecosystem_health_scorer.py
    ├── power-dynamics.json     # input of power_dynamics_scorer.py
    ├── partner-scores.json     # result of partner_scorer.py
    ├── ecosystem-health-result.json  # result of ecosystem_health_scorer.py
    ├── power-dynamics-result.json    # result of power_dynamics_scorer.py
    ├── apollo-raw.json         # raw Apollo answer (only when Apollo answered)
    ├── apollo-enrichment.md    # compact Apollo table, or the fallback notice
    ├── discover.md             # discover-agent output
    ├── structure.md            # structure-agent output
    ├── architect.md            # architect-agent output
    ├── npv-input.json          # input of npv_calculator.py
    ├── monetize-notes.md       # projections of the monetize-agent (step inputs)
    ├── npv-result.json         # result of npv_calculator.py
    ├── monetize.md             # monetize-agent output
    └── synthesize.md           # synthesizer output
```

**Sweep:** the skill `partnerships` runs `session_manager.py --sweep` before it makes a session. The sweep removes folders in `.sp-tmp/` that are older than 60 minutes and have no `completed_at`. A complete session stays until the person deletes it.
