# Strategic Partnerships — C4 Architecture Diagrams

## C4 Level 1 — System Context

```mermaid
C4Context
    title Strategic Partnerships — System Context
    Person(user, "User", "Founder / BD / Product Leader")
    System(sp, "strategic-partnerships", "Skills and an 11-agent pipeline: readiness assessment, partner discovery, deal structure, integration architecture, revenue modeling, go or no-go synthesis")
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
        Container_Boundary(skills, "Skills (main conversation)") {
            Container(full, "partnerships", "skill", "Entry point of the full run: reads the product context, asks for the missing fields, sweeps old sessions, makes the session, starts the orchestrator, shows the result")
            Container(phaseSkills, "partnerships-assess, -discover, -structure, -architect, -monetize, -recommend", "skills", "Quick path in the conversation, or full quality path that starts the phase agent")
        }

        Container(orch, "orchestrator", "sonnet", "Thin coordinator: sequential phase dispatch, DONE signal. Asks nothing.")

        Container_Boundary(phases, "Phase Agents") {
            Container(assess, "assess-agent", "sonnet", "Archetype classification, network effects, power dynamics, readiness scorecard")
            Container(discover, "discover-agent", "sonnet", "6-worker parallel dispatch, Apollo enrichment, ecosystem health scoring")
            Container(structure, "structure-agent", "sonnet", "Revenue streams, partner tiers, network effects design, term sheet outline")
            Container(arch, "architect-agent", "sonnet", "Platform leadership levers, openness framework, DX gap analysis, integration blueprint")
            Container(monetize, "monetize-agent", "sonnet", "NPV calculation, Forrester benchmark comparison, ROI verdict")
            Container(synth, "synthesizer", "opus", "Two-pass synthesis: YAML headers, then full text for FAIL phases, then GO/NO-GO")
        }

        Container_Boundary(workers, "Workers and Evaluators") {
            Container(worker, "discover-worker", "haiku", "Single Popp model candidate scan (x6 in parallel)")
            Container(enricher, "apollo-enricher", "haiku", "Context firewall: raw Apollo answer, 10-field allowlist, compact markdown table")
            Container(preflight, "pre-flight-agent", "haiku", "simulate_phase.py: HIGH/MEDIUM/LOW confidence before each phase")
            Container(evaluator, "evaluator-agent", "haiku", "evaluate_phase.py: PASS/FAIL + gap list after each phase")
        }

        Container_Boundary(scripts, "Python Scripts (uv run, tested)") {
            Container(sess, "session_manager.py", "Python", "Session lifecycle: init, sweep, update scores, complete phase, complete")
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
    Rel(full, sess, "Runs --sweep and --init")
    Rel(full, orch, "Starts with the Agent tool: session_id, product_context")
    Rel(full, session_bus, "Reads session.json and synthesize.md")
    Rel(phaseSkills, preflight, "Full quality path: runs simulate_phase.py")
    Rel(phaseSkills, assess, "Full quality path: starts the phase agent")
    Rel(orch, preflight, "Starts before each phase")
    Rel(orch, assess, "Starts")
    Rel(orch, discover, "Starts")
    Rel(orch, structure, "Starts")
    Rel(orch, arch, "Starts")
    Rel(orch, monetize, "Starts")
    Rel(orch, evaluator, "Starts after each phase")
    Rel(orch, synth, "Starts")
    Rel(orch, sess, "Runs --complete-phase and --complete")
    Rel(assess, session_bus, "Writes assess.md, DONE: assess")
    Rel(discover, worker, "Starts x6 in parallel")
    Rel(discover, enricher, "Starts (Priority A/B, max 10)")
    Rel(discover, scorer, "Scores candidates")
    Rel(discover, eco, "Scores ecosystem health")
    Rel(discover, power, "Scores power dynamics")
    Rel(discover, session_bus, "Writes discover.md, DONE: discover")
    Rel(monetize, npv, "Calculates NPV and verdict")
    Rel(enricher, apollo, "apollo_bulk_enrich_organizations (optional)")
    Rel(enricher, ext, "Applies field allowlist")
    Rel(preflight, sim, "Runs simulate_phase.py")
    Rel(preflight, sess, "Runs --update-preflight")
    Rel(evaluator, evl, "Runs evaluate_phase.py")
    Rel(evaluator, sess, "Runs --update-evaluator")
    Rel(synth, session_bus, "Reads all phase .md files (two passes), writes synthesize.md")
```

---

## Agent Model Assignment

| Agent | Model | Rationale |
|---|---|---|
| `orchestrator` | sonnet | Thin coordinator: no framework loading, no synthesis |
| `assess-agent` | sonnet | Framework judgment and qualitative text |
| `discover-agent` | sonnet | Merge and ecosystem scoring logic |
| `structure-agent` | sonnet | Deal design and network effects analysis |
| `architect-agent` | sonnet | Platform strategy and integration blueprint |
| `monetize-agent` | sonnet | Financial interpretation and Forrester benchmarking |
| `synthesizer` | opus | Step with the most judgment: 5-phase integration and quantified GO/NO-GO |
| `discover-worker` | haiku | Structured scan against a single Popp model: extraction task |
| `apollo-enricher` | haiku | Structured extraction and field filtering: no judgment |
| `pre-flight-agent` | haiku | Deterministic confidence class: no judgment |
| `evaluator-agent` | haiku | Deterministic rubric check: no judgment |

---

## Session Folder Protocol

Each run writes to `.sp-tmp/<session_id>/` in the current folder of the person:

```
.sp-tmp/
└── a1b2c3d4/
    ├── session.json            # Run state: phases_complete, preflight_scores, evaluator_scores, completed_at
    ├── assess.md               # assess-agent output
    ├── discover-model-<n>.md   # discover-worker output (n = 1 to 6), with a .json file of the candidates
    ├── candidates.json         # merged candidates, input of partner_scorer.py
    ├── ecosystem-health.json   # input of ecosystem_health_scorer.py
    ├── power-dynamics.json     # input of power_dynamics_scorer.py
    ├── apollo-raw.json         # raw Apollo answer (only when Apollo answered)
    ├── apollo-enrichment.md    # compact Apollo table, or the fallback notice
    ├── discover.md             # discover-agent output
    ├── structure.md            # structure-agent output
    ├── architect.md            # architect-agent output
    ├── npv-input.json          # input of npv_calculator.py
    ├── monetize.md             # monetize-agent output
    └── synthesize.md           # synthesizer output
```

**Sweep:** the skill `partnerships` runs `session_manager.py --sweep` before it makes a session. The sweep removes folders in `.sp-tmp/` that are older than 60 minutes and have no `completed_at`. A complete session stays until the person deletes it.
