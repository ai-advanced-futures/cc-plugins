# ADR-001: Strategic Partnerships Plugin Architecture

**Status:** Accepted. Decision 1 is superseded by ADR-002. Decisions 2, 3, and 4 stay in force.
**Date:** 2026-03-04

---

## Context

The `strategic-partnerships` plugin guides founders, product leaders, and business development teams through the full life cycle of software ecosystem partnerships. The phases are readiness assessment, partner discovery, deal structure, technical architecture, revenue modeling, and a final go or no-go recommendation.

Four design questions needed an answer:
1. Whether to use agents (LLM orchestration) or skills (direct LLM instruction)
2. Whether to include Python scripts for the quantitative models
3. How to structure the workflow across phases
4. Which research frameworks to use and how to give credit for them

---

## Decision 1: Skill-Only Architecture (No Agents, No Python)

**Status: superseded by ADR-002.** The first version of the plugin used only skills. ADR-002 moves the full run to an agent pipeline with Python scripts. The phase skills stay as the quick path. The text below is the original decision.

### Decision

Implement all plugin functions as skills (direct LLM instruction files) and not as agents (orchestrated multi-agent workflows with Python scripts).

### Rationale

**For skills-only:**
- Partnership analysis is fundamentally a judgment-and-narrative task — it requires synthesis of qualitative context (ecosystem dynamics, competitive position, strategic fit) that LLMs perform well without structured computation
- The quantitative elements (scoring, revenue projections, NPV) involve simple arithmetic with user-supplied data, not complex deterministic computation that would justify a Python script
- Skills are simpler to maintain, extend, and debug than agent pipelines
- Skills load directly in context with zero latency — no subprocess overhead, no data passed through files
- Avoids the context budget risk of multi-agent orchestration for a plugin used primarily interactively

**Against agents:**
- No hard real-time data requirement (frameworks are academic; data is user-supplied or estimated)
- No parallel-processing requirement (phases are sequential by design — each builds on the previous)
- No state management requirement across invocations that would justify a state machine

### Consequences

- All analytical work is performed by Claude directly, guided by the skill instruction files
- Users supply inputs interactively; skills guide structured elicitation
- The plugin cannot call external APIs, execute Python, or write files — by design
- Future additions requiring real computation (e.g., a Monte Carlo revenue simulator) would need a Python script and a version bump

---

## Decision 2: Six-Phase Sequential Workflow

### Decision

Structure the plugin as a six-phase sequential workflow: Assess → Discover → Structure → Architect → Monetize → Recommend.

### Rationale

The six phases map directly to Popp's partnership lifecycle and create a natural onboarding ramp for users:

1. **Assess** (readiness) must precede everything — starting partnership work without knowing your position and gaps is a common failure mode
2. **Discover** (candidates) requires the assess output (power position, archetype, ICP) as an input
3. **Structure** and **Architect** (deal design + technical design) can be done in parallel but both require discover output to know which model type to design for
4. **Monetize** (financial model) requires the structure output to have defined revenue streams
5. **Recommend** (decision) requires all prior outputs to produce a credible go/no-go

The sequential design also aligns with Popp's sequencing principle: start low-integration (referral, revenue share) to build trust before committing to high-integration models (OEM, development cooperation).

### Consequences

- Users can enter at any phase (skills are independently usable)
- Each phase skill refers to the full workflow
- The skill `partnerships-recommend` is a synthesis phase on purpose: it adds no new framework, and it only combines the earlier outputs

---

## Decision 3: Academic Framework Grounding

### Decision

Ground all analytical frameworks in peer-reviewed research and authoritative practitioner books with full attribution in `frameworks.md`. Prohibit ad-hoc intuition as a substitute for validated frameworks.

### Frameworks Selected

| Framework | Author | Rationale for Selection |
|-----------|--------|------------------------|
| Partner Model Taxonomy | Popp & Meyer | Validated at SAP across 50+ partnerships; the most cited software partnership taxonomy |
| Business Model Taxonomy | Popp & Meyer | Provides archetype language for the value exchange that most practitioners lack |
| Revenue Stream 6-Attribute Model | Popp & Meyer | Makes implicit deal economics explicit; prevents revenue stream design errors |
| 4 Levers of Platform Leadership | Gawer & Cusumano | MIT/Surrey research; best-validated framework for platform boundary decisions |
| Network Effects Typology | Parker et al. | Dartmouth/BU; distinguishes strategic from tactical partnerships |
| Platform Openness Framework | Parker et al. | Required for API and developer access decisions |
| Ecosystem Monetisation Principles | Parker et al. | Prevents over-monetisation — the most common ecosystem failure mode |
| Ecosystem Health Indicators | Jansen | Utrecht University; the only peer-reviewed framework for ecosystem viability assessment |
| Power Dynamics | Jansen | Required for negotiation posture; ignored by most practitioners |
| Forrester 2025 Benchmarks | Forrester | Industry data; provides market-validated targets for ROI projections |

### Consequences

- Every claim and threshold in the plugin is traceable to a published source
- Framework attribution is maintained in `frameworks.md` with full bibliographies
- The skill `partnerships-recommend` combines all 9 frameworks (A–I) into one decision. This is on purpose.

---

## Decision 4: Partner Scoring Priority Labels (not "Tier")

### Decision

In the skill `partnerships-discover`, label scoring bands as **Priority A / B / C** rather than **Tier 1 / 2 / 3**.

### Rationale

The skill `partnerships-structure` uses a three-tier partner program design (Registered / Silver / Gold). This is the standard industry term for partner program membership levels. If both `partnerships-discover` (scoring priority) and `partnerships-structure` (program tier) used "Tier 1/2/3", the same name would mean two things.

Priority A/B/C is distinct enough to avoid confusion while preserving the prioritisation concept.

### Consequences

- All references to discover scoring bands use Priority A/B/C
- All references to partner program membership levels use Tier 3/2/1 (Registered/Silver/Gold)
- The two label systems are clearly distinguished in both skills

---

## Alternatives Considered

### Alternative: Agent-Based Pipeline (Rejected in this ADR; adopted by ADR-002)

A multi-agent design where a thin orchestrator dispatches parallel domain agents (deal-structure agent, ecosystem-health agent, monetization agent) was considered.

**Rejected because:**
- The plugin's analytical complexity does not require parallelism — phases are sequential
- Agent pipeline overhead would add latency and context budget cost for an interactive tool
- The skill-only approach is sufficient and significantly simpler to maintain

### Alternative: Single Monolithic Skill (Rejected)

A single SKILL.md covering all six phases in one file was considered.

**Rejected because:**
- A single SKILL.md would be too large to maintain effectively
- Users frequently want to run a single phase (e.g., just discover, or just monetize) — skill modularity enables this
- Phase-specific context is cleaner when each skill can be developed and iterated independently

---

## References

- Popp, K.M., Meyer, R. (2010). *Profit from Software Ecosystems*. Books on Demand.
- Gawer, A., Cusumano, M. (2002). *Platform Leadership*. Harvard Business School Press.
- Parker, G., Van Alstyne, M., Choudary, S.P. (2016). *Platform Revolution*. W.W. Norton.
- Jansen, S. (2016). "A Power Perspective on Software Ecosystem Partnerships." PROFES 2016.
- Jansen, S. (2021). "Is Your Software Ecosystem in Danger?" Utrecht University.
- Forrester Research (2025). "The State of B2B Partner Ecosystems." RES182126.
