# Agentic SDLC Frameworks

This file is loaded section-by-section by `sdlc-assessor` and `sdlc-challenger`.
Agents load only the sections they need via the `§marker` pattern — never the full file.

---

<!-- §chain-start -->
## §chain — Agentic SDLC 21-Step Lifecycle

The agentic SDLC lifecycle is organized into 6 phases (Phase 0–5). Each step maps
to a human role and an agent assist mode.

**Phase 0 — Customer Intelligence (Steps 0.1–0.3)**

- Step 0.1: Continuous Customer Research — ongoing interview synthesis and signal collection
- Step 0.2: JTBD Mapping — functional, emotional, and social jobs extraction
- Step 0.3: Market Hypothesis Formation — opportunity scoring and competitive framing

**Phase 1 — Product Discovery (Steps 1.1–1.3)**

- Step 1.1: PRD and Feature Backlog — outcome-driven requirements with acceptance criteria
- Step 1.2: Story Decomposition — epics → stories → tasks with dependency mapping
- Step 1.3: Prioritization and Roadmapping — value/effort matrix and quarter-level roadmap

**Phase 2 — Architecture and Design (Steps 2.1–2.3)**

- Step 2.1: Architecture Assessment — cross-domain architecture review (→ `/architecture-assess:assess`)
- Step 2.2: System Design — new architecture decisions grounded in ADRs (→ `/architecture-assess:design`)
- Step 2.3: API Contract Design — interface definitions, schema agreements, versioning strategy

**Phase 3 — Implementation (Steps 3.1–3.6)**

- Step 3.1: Feature Brief + Brainstorm — agent-assisted scope framing, acceptance criteria, JTBD alignment
- Step 3.2: Simulate — adversarial gap scan BEFORE the plan is written; agent simulates writing the plan and surfaces missing information, ambiguous requirements, and blind spots. Most important quality gate in the chain.
- Step 3.3: Plan + Test-Driven Development — agent-generated implementation plan; failing tests first, then minimal implementation
- Step 3.4: Execute + Code Review — implementation with peer review and architectural constitution alignment
- Step 3.5: Simplify — pre-commit quality pass; `/simplify` runs before push to catch duplication, abstraction leaks, and unnecessary complexity
- Step 3.6: Verify AI — **two-boundary step**: (a) pre-push: `/silent-failure-hunter` + `/type-design-analyzer`; (b) post-push: MR gate (e.g., LLM-as-judge reviewer). Target: ≤2 issues caught at L3 per MR. >10 issues/MR = L1/L2 session layer is failing.

**Phase 4 — Delivery (Steps 4.1–4.5)**

- Step 4.1: CI/CD Pipeline Execution — automated build, test, and deployment validation
- Step 4.2: Fix Preview Agent — autonomous post-deploy triage; reads CI/CD Inspect stage results; auto-creates issues; re-enters SDLC at Step 3.2. Requires ephemeral environments.
- Step 4.3: Staged Rollout — canary deployment, progressive delivery, rollback readiness
- Step 4.4: PM Release Gate — deliberate human business decision before production promotion; NOT a CI/CD automation gate. Owner: PM or product lead.
- Step 4.5: Production Verification — smoke tests, SLO monitoring, user impact confirmation

**Phase 5 — Learning Loop (Step 15)**

- Step 15: Production Learning — telemetry analysis, error budget review, WER/golden-dataset evaluation (for AI features), feedback synthesis back to Phase 0

> **Note on numbering:** Steps are labeled 0.1–4.5 and 15. Step 15 is intentionally the last
> step and the first step of the next cycle — the loop closes here.
<!-- §chain-end -->

---

<!-- §zone-model-start -->
## §zone-model — Four-Zone Infinity Loop (Stakeholder Communication Frame)

The agentic SDLC is organized as a continuous four-zone loop — the organizational
communication frame for non-engineering stakeholders. Map Phase findings to Zone language
when presenting to executives, PMO, or org-level audiences.

**The Infinity Loop:**
```
Zone 1: Design → Zone 2: Build → Zone 3: Deploy → Zone 4: Feedback → (back to Zone 1)
```

The loop never stops. Even products shipping every sprint receive Zone 4 Feedback that
triggers Zone 1 Design updates. This is the operating model — not a sequential waterfall.

| Zone | Phase Mapping | Organizational Description |
|------|--------------|---------------------------|
| **Zone 1: Design** | Phase 0 (Customer Intelligence) + Phase 1 (Product Discovery) | Product context layer: Business Case, PRD, UX Design, Technical Design. Establishes *why* and *what* before engineering begins. |
| **Zone 2: Build** | Phase 2 (Architecture & Design) + Phase 3 (Implementation) | Development chain: Brainstorm → Spec → Simulate → Plan → Execute → Verify AI. Where agents and engineers co-produce working software. |
| **Zone 3: Deploy** | Phase 4 (Delivery — Steps 4.1–4.5) | Preview environments, Staging, PM Release Gate, Blue-Green production deploy, Fix Preview Agent. |
| **Zone 4: Feedback** | Step 15 (Production Learning) | Production monitoring, customer feedback, market signals, retrospective → spec revision. Feeds back into Zone 1. |

**When to use Zone language vs. Phase language:**
- **Zone language:** Executive updates, PMO cadence reporting, org-design conversations, maturity roadmaps
- **Phase language:** Technical assessments, sdlc-spec.md, toolchain gap analysis, pilot scoring

**Loop closure signal:**
> The system is working when Zone 4 signals (telemetry, support tickets, market intelligence)
> automatically trigger Zone 1 updates (PRD revisions, Business Case updates). When this
> loop is manual and ad-hoc, the org is Tier 1–2. When it runs autonomously with human
> oversight, it is Tier 3–4.
<!-- §zone-model-end -->

---

<!-- §discovery-tiers-start -->
## §discovery-tiers — Context Proportionality Model

Not every change requires full Discovery. The tier determines minimum viable context —
not process overhead. Assessing whether an org has this tiered proportionality model is
a key maturity signal: orgs applying Full Discovery to every bug fix, or zero Discovery
to new products, are misaligned on scope-to-investment ratios.

| Change Type | Discovery Tier | Minimum Context Required | Agent Implication |
|-------------|---------------|--------------------------|-------------------|
| New product / standalone offering | **Full** | Business Case + BRD/PRD + Technical Design. UX Design required to validate problem before committing engineering resources. | Agent needs full product context before any implementation work. Absence of Business Case = do not proceed. |
| Major new capability of existing product | **Lightweight** | BRD/PRD update + Technical Design delta. Reference existing Business Case. | Agent loads Feature Area PRD + delta spec. Full Product PRD loaded only on conflict. |
| Minor feature / enhancement | **Minimal** | PRD entry with acceptance criteria. One session to write; no gate ceremony. | Agent loads feature spec + parent PRD section. Business Case not loaded. |
| Bug fix / maintenance / performance | **None** | Jira ticket (or equivalent) is sufficient context. Engineering starts immediately. | Agent loads CLAUDE.md + ticket context only. No spec required. |

**Assessment probe:** Ask: "What does a new product require before engineering starts? What about a bug fix?"
- **Correct answer:** Different process for each tier — proportional to decision irreversibility.
- **Maturity failure (over-process):** Full Discovery required for bug fixes → engineering velocity killed.
- **Maturity failure (under-process):** No Discovery required even for new products → agents build the wrong thing with no context.

**Key principle:** The question at the start of any engineering cycle is not "did we complete Discovery?"
— it is: "**do agents have sufficient product context to execute this correctly?**"

**Harness signal:** If specs are locked in Confluence/Google Drive (not committed to Git), agents
cannot load them regardless of tier. Spec Hygiene (§harness) is a prerequisite for this model to work.
<!-- §discovery-tiers-end -->

---

<!-- §roles-start -->
## §roles — Role Evolution: Traditional → Agentic

How each role changes in an agentic SDLC. Used by sdlc-assessor to map current org structure
to future state recommendations.

| Role | Traditional Responsibilities | Agentic Additions | Effort Shift |
|------|------------------------------|-------------------|-------------|
| **Product Manager** | Requirements, roadmap, stakeholder sync | **Spec author and context anchor owner** — PRDs and feature briefs committed to Git in agent-readable format; JTBD synthesis, competitive intelligence dispatch | 30% research → 10% (agent-assisted); spec authorship becomes PM's primary quality lever |
| **Software Engineer** | Code, test, review | **Harness builder, not code writer** — designs CLAUDE.md, defines hooks, curates tool registry, validates agent output. Pilot constraint: prompt-only for first sprint (no manual code edits) to build trust calibration | 60% implementation → 20%; 40% → prompt design + harness maintenance |
| **QA Engineer** | Manual test cases, regression suites | **3-track QE model**: (1) Outer Loop — exploratory testing embedded in pod, Week 2+; (2) Platform Engineering — AI test harness, self-healing tests, test generation with guardrails; (3) SRE/ML Specialization — WER tracking, golden datasets, production model quality. Handoff model eliminated. | Manual handoffs → shift-left embedded QE |
| **Solution Architect** | Design decisions, ADRs, reviews | Architecture assessment orchestration, ADR quality gate. **Architecture review bottleneck (enterprise structural signal):** In orgs with >50 engineers and centralized architecture teams, review cycles of 5–15 days will block agentic pod velocity before Sprint 1 ends. Fix: (1) define architecture decision envelope at pod kick-off — what decisions are pre-approved for pod autonomy; (2) pod tech lead approves in-envelope decisions within 48h; (3) shared architecture review only for out-of-envelope decisions — specifically: **net-new system-to-system interactions** (new service dependency, new integration contract, new event schema). NOT for: feature additions, data model changes, refactors, or code organization. Probe: *"How long does architecture approval take? Who can approve? What triggers a required review?"* | **Architecture review bottleneck** (5–15 day cycles) is a Tier 1 structural blocker in enterprise orgs. |
| **DevOps/Platform** | CI/CD pipelines, infra as code | **Write-protected mandatory pipeline gates** — build, MR gate, tests are write-protected; pod teams can ADD steps but cannot REMOVE them. Makes SDLC compliance technically mandatory, not culturally aspirational. | Ops → platform strategy; compliance shifts from culture to infrastructure |
| **Data Scientist** | Model development, feature engineering | Agent-in-the-loop ML pipelines, model monitoring | Experiment velocity 3–5× |
| **Engineering Manager** | Sprint planning, performance reviews | Agent dispatch, org maturity tracking, agentic pod velocity measurement | 25% coordination → orchestration |

**Agentic-native roles (new or expanded):**

- **Prompt Engineer / AI System Designer** — designs agent instructions and harness primitives; owns CLAUDE.md quality
- **AI Quality Lead** — validates agent outputs, manages hallucination risk and accuracy thresholds; owns WER and golden datasets
- **Platform Team** — manages the agentic infrastructure (see §platform); publishes internal plugin catalog

**Architecture review bottleneck (enterprise-specific structural signal):**
> In orgs with >50 engineers and centralized architecture teams, architecture review cycles averaging 5–15 days will block agentic pod velocity before the first sprint completes. The fix is not faster reviewers — it is pre-approved architecture envelopes with bounded pod-level authority. Detect this signal by asking: "How long does architecture approval take? Who can approve?"

**Quality agent disambiguation:**
> A "Quality Agent" in the agentic SDLC is a **harness component** (automatic QA gate in the pipeline), not a standalone product or PM-facing agent. The MR gate (Step 3.6) and Fix Preview Agent (Step 4.2) are the quality agents.

**Architecture gate trigger (precise definition):**
> A new architecture review is required when and only when: a **net-new system-to-system interaction**
> is introduced — a new service-to-service dependency, a new integration contract (OpenAPI spec),
> or a new event schema in a shared platform repo. This is the trigger.
>
> Architecture review is NOT required for: adding a feature, changing a data model, refactoring code,
> updating tests, or any change that stays within a bounded context's existing system boundary.
>
> A small architecture team (2–3 architects for a 100+ engineer org) cannot review everything —
> and should not. The self-service model for features is a necessity, not a preference. The architecture
> team's leverage comes from defining the decision envelope, not from reviewing individual decisions.
<!-- §roles-end -->

---

<!-- §harness-start -->
## §harness — Agentic Harness Primitives

The harness is the set of infrastructure decisions that enable reliable agentic workflows.
Evaluate maturity of each primitive independently.

| Primitive | What It Is | Maturity Signal | Missing Signal |
|-----------|-----------|----------------|---------------|
| **Context Anchor** | `CLAUDE.md` at repo root — per-session briefing for agents | Substantive CLAUDE.md (>50 lines) with agent objectives, project context, and prior decisions | Agent asks "what are we building and why?" every session. Most common Tier 1 failure. |
| **Spec Hygiene** | Product specs (PRD, BRD, feature briefs) committed to Git | `docs/specs/`, `docs/prd/`, `.claude-plugin/`, or `*.md` spec files in repo | Specs locked in Confluence / Google Drive / Notion — agents cannot read them. |
| **Hooks System** | `.claude/settings.json` PostToolUse / PreToolUse / Stop hooks | Session-layer behavior governed. **Highest-value use case: context lifecycle management** — SessionStart hooks that load only task-relevant state (not full prior session), Stop hooks that write checkpoint files so sessions resume from disk rather than stale in-context state. Hooks that only run linters are present but immature (score lower). | Session-layer ungoverned. Or hooks present but only run linters — no context lifecycle management, no checkpoint files. Context degrades silently across long sessions. |
| **Observation** | Telemetry, structured logging, distributed traces | OTel spans on agent calls, latency histograms | No agent-specific logs |
| **Evaluation** | Automated quality checks on agent output | LLM-as-judge, rule-based scorers, regression suites | Manual spot-check only |
| **Memory** | Persistent context across sessions | Vector stores, episodic memory, project memory | No cross-session state |
| **Tool Registry** | Curated, versioned tool library | Typed tool contracts, MCP servers, version-pinned tools | Ad-hoc tool definitions |
| **Feedback Loop** | Human corrections feed back into harness | RLHF pipeline, correction capture, preference logging | No correction capture |
| **Guardrails** | Input/output validation and safety gates | Schema validators, content filters, PII redaction | Unvalidated LLM output |
| **Orchestration** | Multi-agent workflow management | Agent dispatch, DONE signals, handoff files. **Durability signals:** agents write state to deterministic file paths before signaling DONE; orchestrator reads path references only, never re-injects sub-agent content into its own context. | Single-agent monoliths. Or multi-agent but orchestrator accumulates sub-agent output in context (context grows O(n) with agent count — CRITICAL at 5+ agents). |
| **Bounded Context Isolation** | Subdirectory `CLAUDE.md` files scoped per domain (e.g., `src/payments/CLAUDE.md`, `src/orders/CLAUDE.md`) | Each domain has its own CLAUDE.md encoding its ubiquitous language and domain-specific constraints. Agents working in `src/payments/` load domain context without polluting other bounded contexts. | Single root CLAUDE.md for entire repo — agents working in domain A load domain B context unnecessarily. No ubiquitous language contract per domain. |
| **Spec-Reference-Check** | Pre-commit hook that verifies every commit message references a spec or plan file in `docs/` | `spec-reference-check` script in `.claude/settings.json` PreToolUse (Bash) hooks. Every commit is traceable to a spec. | Commits with no spec traceability — engineering work disconnected from product intent. Agents working from tribal knowledge rather than committed specs. |
| **No-Break Guard** | PostToolUse hook that immediately alerts when an existing test breaks during implementation | `no-break-guard` script fires on every Edit/Write. Prevents existing test regression at edit time — distinct from TDD Guard (which ensures *new* tests exist before implementation). | Regressions discovered at MR time (expensive) or in CI (very expensive) rather than at edit time (free to fix). |
| **Platform Repo** | Dedicated cross-cutting repository with shared ADRs, MCP servers, `CLAUDE.md` templates, hook library, and deterministic tool functions | `platform-engineering/` or equivalent with `docs/adrs/`, `platform/mcp-servers/`, `templates/CLAUDE.md.template`. All pod repos reference it. | Each pod repo independently manages standards. Cross-cutting decisions copy-pasted rather than referenced. No single source of truth for shared MCP servers. |
| **Deterministic Tool Library** | Tax calculations, consent validation, price eligibility, payment scheduling committed as code — not prompts | `platform/tools/<domain>/<function>.ts` with typed contracts and tests. Same input always produces same output. | Deterministic operations handled by LLM prompts — non-reproducible, untestable, compliance risk. |

**Critical path:** Context Anchor → Spec Hygiene → Hooks System must be present before any other primitives yield reliable value. An org with strong Observation but no Context Anchor is measuring chaos.

**Hooks System scoring guidance:**
- Hooks present + only run linters: score 0.5 (present but immature)
- Hooks present + manage context lifecycle (SessionStart loads task-scoped context, Stop writes checkpoints): score 1.0 (full credit)
- Ask explicitly: "Do your Stop hooks write checkpoint files? Do your SessionStart hooks load only task-relevant context, or the full prior session?"

Harness maturity score = count of implemented primitives / 15. Classify:
- 0–3: Pre-harness (ad-hoc AI use)
- 4–6: Emerging harness
- 7–9: Capable harness
- 10–12: Strong harness
- 13–15: Production harness
<!-- §harness-end -->

---

<!-- §maturity-start -->
## §maturity — Org Maturity Tiers (0–4)

Classify the organization into one of 5 tiers based on current SDLC practices.

> ⚠️ **Classification warning**: CI/CD sophistication ≠ SDLC maturity. An org with Harness/Jenkins
> pipelines but no CLAUDE.md, specs locked in Google Drive, and an inverted testing pyramid is
> **Tier 1** — not Tier 3. Weight session-layer and harness signals equally with pipeline signals.

**Tier 0 — Pre-Agentic**
- No AI integration in development workflow
- Manual pipelines, ad-hoc tooling
- Signals: no CI/CD, no LLM tools, waterfall or informal process
- Recommendation: Start with a single Phase 3.1–3.2 pilot (Feature Brief + Simulate)

**Tier 1 — AI-Assisted**
- Point AI tools in use (Copilot, ChatGPT, Claude for drafting)
- No systematic agent workflow, no harness
- Signals: isolated AI use; **no CLAUDE.md**; specs locked in Confluence/Google Drive; inverted testing pyramid (heavy e2e, thin unit); MR gate catching >10 issues/MR (session layer failing); **unsanctioned AI tools in use** (multiple tools coexisting without governance = security and consistency risk); Claude plugin marketplace unknown to engineering team
- Recommendation: Install CLAUDE.md. Commit one spec to Git. Pilot Phase 3.1–3.2. Audit and standardize AI tool usage — unsanctioned tools bypass official pipelines.

**Tier 2 — Agent-Augmented**
- Agents integrated into 1–3 SDLC phases; CLAUDE.md present
- Some harness primitives in place (Context Anchor + Spec Hygiene)
- Signals: `/architecture-assess:assess` or `/product:explore` plugin use, partial CI integration, specs in Git for at least one team
- **Structural blocker to detect:** Architecture review bottleneck (5–15 day cycles). Ask: *"How long does architecture approval take? Who can approve?"* If answer is >48h and requires central architecture team approval for any change: this is a Tier 2 structural blocker that will kill agentic pod velocity before Sprint 1 ends. Fix: pre-approved architecture decision envelope at pod kick-off + pod tech lead approves in-envelope decisions within 48h + shared architecture review only for net-new system-to-system interactions (new service dependencies, new integration contracts). Not for feature additions, data model changes, or refactors.
- Recommendation: Add Hooks System. Run Simulate step. Define architecture envelope with pod-level tech lead authority to unblock review bottleneck.

**Tier 3 — Agent-Collaborative**
- Agents participate in most SDLC phases with human oversight
- Strong harness (8+ of 15 primitives), full Hooks System with context lifecycle management, Simulate step active
- Signals: agent dispatch, multi-agent coordination, DONE signals, handoff files; architecture envelope defined; ephemeral environments for PR testing; Playwright tests colocated in app repos; ≤10 issues caught at MR gate per cycle; **inner-source plugin marketplace** (shared plugin repo with platform team governance); Fix Preview Agent deployed or in progress
- Recommendation: Build Fix Preview Agent (Step 4.2). Introduce PM Release Gate. Target ≤2 issues/MR. Build Platform Repo (§harness) for shared MCP servers and CLAUDE.md templates.

**Tier 4 — Agentic-Native**
- Agents operate autonomously across all 6 phases with human oversight on strategic decisions
- Full harness (12–15 of 15 primitives) in production; Fix Preview Agent active
- Signals: autonomous Phase 0 learning loops; self-healing CI; ≤2 issues/MR (session layer governs quality); production anomaly detection with WER/golden-dataset evaluation; ADR generation automated; **Platform Repo established** with shared MCP servers, CLAUDE.md templates, and hook library; inner-source plugin marketplace at maturity Level 4+ (see §plugin-marketplace-maturity)
- Recommendation: Continuous harness fidelity improvement; build institutional agentic memory (Step 15 learning loop closure).
<!-- §maturity-end -->

---

<!-- §pilot-start -->
## §pilot — Pilot Project Selection Criteria

When recommending a pilot, evaluate candidate projects against these criteria.
Higher score = better pilot candidate.

| Criterion | High Signal (3 pts) | Medium Signal (1 pt) | Low Signal (0 pts) |
|-----------|--------------------|--------------------|------------------|
| **Bounded scope** | Clear start/end, <3 month timeline | 3–6 months | Open-ended or multi-year |
| **Low blast radius** | Non-critical path, easy rollback | Some dependencies | Core system, hard to rollback |
| **Data availability** | Rich existing documentation, ADRs, test coverage | Partial docs | No docs, no tests |
| **Team receptivity** | Team actively interested in AI | Neutral | Resistant or skeptical |
| **Measurable outcomes** | Quantifiable KPIs (velocity, defect rate) | Qualitative goals | No success criteria |
| **Architecture API-readiness** | Domain data fully accessible via existing APIs today | APIs exist but require MCP server to be built first | No API access; direct DB or manual data extraction required |
| **Existing PoC** | Working PoC or prototype already validated by a practitioner | Partial PoC or design spike | No prior exploration |

> **Note:** API-readiness is the most under-estimated criterion. A pilot on a fully API-ready domain can produce a working agent in Week 1. A pilot that requires building an MCP server first extends timeline by 3–6 weeks and derails momentum.

**Scoring:**
- 18–21: Strong pilot candidate — proceed immediately
- 12–17: Viable with preparation — address gaps first (especially API-readiness and data availability)
- 0–11: Not ready — identify prerequisites before committing to a pilot

**Default pilot recommendation by maturity tier:**
- Tier 0–1: Phase 3.1–3.2 (Feature Brief + Simulate on a single low-blast-radius story)
- Tier 2: Phase 3.1–3.2 + Spec hygiene installation (commit first spec to Git)
- Tier 3: Phase 3.3–3.5 (Plan + TDD + Simplify harness full chain)
- Tier 4: Phase 4.2 (Fix Preview Agent) + Step 15 (learning loop closure)
<!-- §pilot-end -->

---

<!-- §platform-start -->
## §platform — Platform Team Design

The platform team is the enabler of agentic SDLC adoption. Size and structure scale with org maturity.

**Platform Team Responsibilities:**
1. Agentic harness infrastructure (observation, evaluation, memory, guardrails)
2. Tool registry curation — versioned, typed, security-reviewed
3. Model governance — provider selection, cost management, latency SLOs
4. Developer experience — onboarding, documentation, internal tooling
5. AI quality — hallucination tracking, accuracy benchmarking, regression testing

**Sizing by maturity tier:**

| Tier | Platform Team Size | Structure |
|------|--------------------|-----------|
| 0–1 | 0 (not yet needed) | AI Champion role in engineering team |
| 2 | 1–2 engineers | Enabling sub-team within platform/infra |
| 3 | 3–5 engineers | Dedicated Platform Team (Team Topologies enabling team) |
| 4 | 5–10 engineers | Platform Product (internal developer platform for AI) |

**Key Platform Team signals from codebase:**
- Presence of shared tool libraries (→ tool registry maturity)
- Centralized prompt/agent directories (→ governance signal)
- CI/CD integration with agent workflows (→ pipeline maturity)
- Agent output logging and evaluation frameworks (→ harness signal)
<!-- §platform-end -->

---

<!-- §do-now-start -->
## §do-now — DO NOW / DO LATER Decision Grid

Classify each SDLC step recommendation into DO NOW (high value, low friction) vs
DO LATER (high value, high friction or dependency) vs DON'T DO (low value).

**DO NOW criteria:**
- Measurable impact within 30 days
- No new infrastructure required
- Team can start with existing tools
- Low risk of disruption

**DO LATER criteria:**
- Requires infrastructure investment (harness primitives, new tooling)
- Depends on earlier steps reaching maturity first
- High coordination cost (multiple teams, procurement)

**Enterprise principle: "Don't replace the SDLC, extend it."**
Large orgs (>100 engineers) cannot absorb a wholesale SDLC replacement. The agentic SDLC is a non-disruptive overlay — it adds agent-assist steps on top of existing gates without removing existing process. Sequencing rule: **ship one agent, document the case study, then extend. Policy follows practice.**

**CI/CD enforcement as mandate mechanism:**
Write-protect mandatory CI/CD gates (build, MR gate, test suite) so teams can add steps but cannot remove them. This makes SDLC compliance technically mandatory rather than culturally aspirational — the path of least resistance becomes the correct path.

**Example grid for Tier 1 org:**

| Action | Category | Rationale |
|--------|----------|-----------|
| Install CLAUDE.md at repo root (>50 lines) | DO NOW | Highest-leverage 30-minute investment; unlocks agent grounding |
| Commit one spec (PRD or feature brief) to `docs/specs/` | DO NOW | Spec hygiene — agents can now read the spec |
| Add `.claude/settings.json` with Stop hook | DO NOW | Session-layer governance; captures incomplete sessions |
| Write-protect mandatory CI/CD gates in pipeline | DO NOW | Makes compliance technical, not cultural |
| Use `/product:explore` for next feature PRD | DO NOW | No infra, immediate value, reversible |
| Run `/architecture-assess:assess` on main service | DO NOW | Baseline ADR, low friction |
| Add auto-release-notes step to CI/CD | DO NOW | Low friction, high signal for PM Release Gate |
| Move Playwright tests into app repo | DO NOW | Required for colocated CI gate; typically a 1-day DevOps effort |
| Add `/competitive-intelligence` to product cycle | DO NOW | High value, installable today |
| Add `spec-reference-check` pre-commit hook (.claude/settings.json) | DO NOW | 30-minute investment; every commit becomes traceable to a spec in docs/; prevents engineering work disconnected from product intent |
| Add `no-break-guard` PostToolUse hook on Edit/Write | DO NOW | Catches existing test regression at edit time (free) rather than at MR time (expensive); pairs with TDD Guard |
| Create one Claude.ai Project per bounded context (PM + Platform team) | DO NOW | ~2 hours; upload CLAUDE.md content, Feature Area PRD, Feature Spec template; enables PM parallel drafting sessions with shared context immediately |
| Commit one Feature Spec in 15-section format with Agent Directives (Section 15) | DO NOW | Makes spec-to-agent-execution bridge concrete; agents know exactly which context files to load and which gates apply |
| Build inner-source plugin marketplace repo (shared platform-governed plugin catalog) | DO LATER | Requires spec hygiene + hooks system + at least one proven pilot; Level 2–3 of §plugin-marketplace-maturity is the achievable target |
| Build context packaging skills (/package-context + /collect-outputs) for PM parallel web agent workflows | DO LATER | Requires spec hygiene + output schemas defined first; unlocks 5× PM spec authoring throughput |
| Ephemeral per-PR environments | DO LATER | Requires infra config; unlock after Playwright colocation |
| Full upstream MCP pipeline (spec → agent) | DO LATER | Requires spec hygiene + hooks system first |
| QE 3-track restructuring | DO LATER | Requires ephemeral environments prerequisite |
| Install OTel on agent calls | DO LATER | Requires infra work, needs harness context |
| Build autonomous Phase 0 loop | DON'T DO (yet) | Premature at Tier 1 — prerequisites missing |

**Anti-pattern to flag explicitly:**
> Building a custom binary or proprietary harness daemon that reimplements Claude Code primitives
> (file read/write, bash execution, tool invocation, plugin architecture, MCP integration) is a
> **DON'T DO** at any tier. Claude Code already provides these — the maintenance cost exceeds any
> gain, and the custom system will fall behind Anthropic's platform improvements. Detect this
> anti-pattern during assessment; recommend migration to Claude Code native primitives instead.
<!-- §do-now-end -->

---

<!-- §feature-spec-start -->
## §feature-spec — 15-Section Feature Spec Format with Agent Directives

The Feature Spec is the primary execution context for agents. A well-structured Feature Spec
answers: what to build, why, how to verify it, and how agents should behave while building it.

**Recommended for:** Tier 2+ orgs. The 15-section format with Agent Directives enables agents
to execute autonomously against well-defined acceptance criteria without re-asking for context.

### The 15-Section Format

| Section | Owner | Content |
|---------|-------|---------|
| 1. Goal & Problem Statement | PM | Customer problem, JTBD, desired outcome |
| 2. Success Criteria | PM | Measurable outcomes — how we know this shipped correctly |
| 3. User Story | PM | Actor, action, outcome in standard format |
| 4. Acceptance Criteria | PM + QE | Testable acceptance criteria (BDD or numbered list) |
| 5. UX Flows | PM + Designer | Step-by-step user flows; Figma link if visual |
| 6. Out of Scope | PM | Explicit exclusions to prevent scope creep |
| 7. Open Questions | PM | Unresolved questions; owner + deadline for each |
| 8. Architecture Decisions | Architect + Eng Lead | ADR references, key technical choices |
| 9. Data Dependencies | Eng Lead | Input/output data, API contracts, MCP servers |
| 10. Integration Points | Eng Lead | Services, APIs, event streams this feature touches |
| 11. Test Harness Design | QE + Eng Lead | Test pyramid design; TDD approach; Playwright scope |
| 12. Edge Cases & Constraints | Eng Lead | Failure modes, compliance constraints, rate limits |
| 13. Implementation Plan | Eng Lead | Dependency-ordered tasks; parallel subagent candidates |
| 14. Revision History | PM | Version table with semver, date, author, change summary |
| **15. Agent Directives** | Platform / Eng Lead | **Key innovation** — machine-readable instructions for agent behavior |

### Section 15 — Agent Directives (The Key Innovation)

Section 15 is a YAML block embedded in every spec that tells agents *how* to interact with
the spec — which files to load, which gates apply, what is explicitly out of scope. Without
Agent Directives, agents must infer context loading and gate behavior from narrative text.
With Agent Directives, behavior is explicit and reproducible.

```yaml
# Section 15: Agent Directives
agent_directives:
  context_files:
    - docs/product/payments/prd/refund-handling/prd.md
    - docs/adrs/ADR-0023-consent-rule.md
  execution_gates:
    - gate: "Simulate before Plan — no implementation plan without passing simulation"
    - gate: "No implementation before failing test — TDD Guard enforced"
    - gate: "Verify against acceptance criteria (Section 4) before marking complete"
  out_of_scope:
    - "Do not modify existing test files — no-break-guard enforced"
    - "Do not call the payment gateway directly — route through payments-mcp"
  acceptance_criteria_section: 4
  model_assignments:
    simulate: haiku        # Fast, cost-optimized gap scanning
    implement: sonnet      # Balanced — spec-to-code execution
    verify: sonnet         # Code quality + acceptance test verification
```

**Assessment probe for sdlc-assessor:** Ask: "Do your feature specs include machine-readable agent behavior instructions?"
- **Present:** Agent Directives section exists in specs — score as Spec Hygiene maturity ++
- **Absent:** Spec exists but no agent directives — agents infer behavior, results vary by session

**Week 1 / Week 2 split (PM + Eng Lead responsibility boundary):**
- **Week 1 (PM):** Sections 1–7 (customer problem, acceptance criteria, UX flows, open questions)
- **Week 2 (Eng Lead):** Sections 8–15 (architecture decisions, data, integration, test harness, implementation plan, agent directives)

This split is the role-clarity model. A spec is not ready for agents until both weeks are complete.
<!-- §feature-spec-end -->

---

<!-- §plugin-marketplace-maturity-start -->
## §plugin-marketplace-maturity — Internal Plugin Ecosystem Maturity Model

For organizations building internal Claude Code plugin ecosystems (inner-sourced plugin catalogs,
domain-specific agents, shared hooks), assess which maturity level their ecosystem has reached.
A Tier 3+ org attempting to build a cohesive agentic SDLC pipeline **requires Level 4–5** in
their internal plugin ecosystem.

### Six Critical Gaps (Maturity Blockers)

These six gaps are the specific, nameable blockers between a collection of useful plugins and
a cohesive agentic SDLC pipeline. Identify which are present during assessment.

| # | Gap | Impact on SDLC Pipeline |
|---|-----|------------------------|
| 1 | **CI/CD stub** — plugin CI only runs an AI review, no structural validation | Every governance rule depends on reviewer memory; violations ship silently |
| 2 | **Invisible MCP dependencies** — no `requires` declaration in plugin.json; no install-time dependency check | Engineers discover missing API tokens only when agents fail at runtime |
| 3 | **No cross-plugin contracts** — no output schema, no event system, no trigger manifest | Primary blocker for autonomous SDLC pipeline — human must manually invoke each skill in sequence |
| 4 | **No shared components layer** — session-init, checkpoint protocol, triage patterns are copy-pasted per plugin | Patterns cannot be composed or governed; one fix requires N updates across N plugins |
| 5 | **Minimal plugin.json** — only name/version/description; no `requires`, `provides`, or compatibility constraints | Plugin-platform contract is underdeclared; dependency resolution impossible |
| 6 | **No formal context/memory management** — ad-hoc session JSON per plugin, no shared state mechanism | Multi-plugin workflows have no shared state; each plugin starts cold |

### Maturity Levels

| Level | Timeline | State | Unblocked SDLC Capability |
|-------|----------|-------|--------------------------|
| **Level 1** | Now | Well-written plugins; human-enforced standards; no CI validation; no cross-plugin contracts | Individual skills useful; manual invocation only |
| **Level 2** | Weeks | CI validates plugin structure on every MR; version bump enforcement automated | Standards enforced without human reviewer memory |
| **Level 3** | Sprint | `plugin.json` declares `requires`/`provides`; dependency checker enforces MCP deps at install time; JSON Schema validates on MR | Silent runtime failures eliminated; install-time contract |
| **Level 4** | Quarter | Shared `plugins/core/` extracted — detect, session-init, checkpoint protocol, MCP gate are referenceable primitives (not copy-pasted) | Patterns composable across plugins; governance centralized |
| **Level 5** | Quarter | Output contracts in skill frontmatter; trigger manifests enable cross-plugin chaining; first end-to-end autonomous pipeline | Agentic SDLC pipeline runs without human invocation at each step |
| **Level 6** | Future | Versioned releases with changelog generation; plugin registry API; SaaS distribution layer | Full inner-sourced platform with external distribution capability |

**Target for agentic SDLC:** Level 4–5. The typical enterprise org starting an agentic SDLC is at Level 1.
Gap from 1→4 is ~1 quarter of platform team investment — manageable but requires explicit commitment.

**Assessment probe:** Ask: "Does your plugin CI validate plugin structure? Can plugins declare dependencies? Do you have shared utility functions across plugins?"
- Answers map directly to Level 1–3 classification.
- Level 4+ requires examining whether shared components have been extracted from existing plugins.
<!-- §plugin-marketplace-maturity-end -->

---

<!-- §autonomy-start -->
## §autonomy — Human-in-the-Loop vs Autonomy Spectrum

Each SDLC step can be placed on a spectrum from full human ownership to full agent autonomy.
Recommend placement based on org maturity and risk tolerance.

**Spectrum:**
```
HUMAN-OWNED ←─────────────────────────────→ AGENT-AUTONOMOUS
   1              2            3           4            5
Manual only   Human leads,  Human + AI   AI leads,   Fully
              AI assists    parallel     human gates  autonomous
```

**Per-phase guidance:**

| Phase | Steps | Min Tier for Level 3 | Min Tier for Level 4 |
|-------|-------|---------------------|---------------------|
| Phase 0: Customer Intelligence | 0.1–0.3 | Tier 1 | Tier 3 |
| Phase 1: Product Discovery | 1.1–1.3 | Tier 1 | Tier 3 |
| Phase 2: Architecture & Design | 2.1–2.3 | Tier 2 | Tier 4 |
| Phase 3: Implementation | 3.1–3.6 | Tier 2 | Tier 3 |
| Phase 4: Delivery | 4.1–4.5 | Tier 2 | Tier 4 |
| Phase 5: Learning Loop | Step 15 | Tier 3 | Tier 4 |

**Caution zones (never go fully autonomous without explicit gates):**
- Step 2.2 (System Design): ADR must always have human approval gate
- Step 3.4 (Code Review): human peer review required for security-sensitive changes
- Step 4.4 (PM Release Gate): always human — this gate is a deliberate business decision, not automatable
<!-- §autonomy-end -->

---

<!-- §toolchain-sources-start -->
## §toolchain-sources — Marketplace Sources for Dynamic Discovery

Agents discover available plugins by searching these public marketplace repositories.
Use WebSearch to find current plugin listings — do NOT hardcode plugin names here,
as marketplaces update frequently.

**Approved public marketplace sources (soft cap: ≤5 sources):**

1. `https://github.com/anthropics/claude-plugins-official`
2. `https://github.com/anthropics/knowledge-work-plugins`

**Discovery protocol for sdlc-assessor:**
1. For each source URL, use WebSearch to find plugins matching the current SDLC phase
2. Filter by relevance to identified gaps in the org's current toolchain
3. Present top 3–5 recommendations per phase with install instructions
4. Do NOT recommend plugins you cannot verify exist on one of the above sources

**WebSearch query template:**
```
site:github.com/anthropics/<repo> <phase-keyword> plugin
```

Example: `site:github.com/anthropics/claude-plugins-official architecture assessment plugin`
<!-- §toolchain-sources-end -->

---

<!-- §lens-start -->
## §lens — SDLC Assessment Lens

The assessment lens defines what the sdlc-assessor evaluates and what the sdlc-challenger
challenges. Use this as the evaluation rubric.

**Six assessment dimensions:**

1. **Coverage** — Which lifecycle steps are actively practiced? Which are absent?
   - Evidence: commit history, PR descriptions, CI config, test files, ADR directory
   - Key probe: Is the Simulate step (Step 3.2) present? Absence = highest-leverage gap.
   - Output: `phases_covered` list in sdlc-spec.md YAML header

2. **Automation Level** — For each covered step, what is the current autonomy level (1–5)?
   - Evidence: CI/CD config, agent files, script presence, manual process docs
   - Output: autonomy score per phase in sdlc-spec.md

3. **Harness Maturity** — How many of the 15 harness primitives are implemented?
   - Evidence: CLAUDE.md presence + quality, `.claude/settings.json` hooks, spec-in-Git check, OTel config, evaluation scripts, memory implementation, tool definitions
   - **Context lifecycle signal (highest-value harness indicator):** Do hooks govern what context is loaded at session start (lazy, task-scoped), and do Stop hooks write checkpoint files so sessions resume from disk state rather than stale in-context state? Hooks that only run linters score lower than hooks that manage context lifecycle.
   - **Orchestration durability signal:** Do inter-agent handoffs use files (DONE signal + deterministic path), or does the orchestrator re-inject sub-agent output content into its own context? File-based handoffs = durable; content re-injection = silent failure at scale.
   - Output: `org_maturity_tier` in sdlc-spec.md YAML header (0–4)

4. **Role Readiness** — Are the right roles in place for agentic SDLC?
   - Evidence: team structure signals, job descriptions, DORA metrics
   - Output: `roles_addressed` list in sdlc-spec.md YAML header

5. **Toolchain Completeness** — Is the org using appropriate tools for each phase?
   - Evidence: package.json, Brewfile, CI dependencies, installed plugins; ADR directory presence; test framework diversity; spec hygiene (are specs in Git?); Playwright/e2e test colocation
   - Output: Recommended toolchain section in sdlc-spec.md

6. **Quality Funnel Distribution** — Most diagnostic dimension; reveals whether quality is governed at the session layer (ideal) or only at the CI/CD layer (failure signal).
   - Evidence: testing pyramid shape (count test types from package manifests and CI config); MR gate configuration; release cadence constraint (policy vs. technical)
   - Diagnostic: MR gate catching >10 issues/MR → classify as Tier 1 regardless of CI/CD sophistication. Session layer (CLAUDE.md + hooks) is failing.
   - Output: Quality Funnel section in sdlc-spec.md with layer distribution (L1/L2/L3/L4)

**Challenger challenge dimensions (for sdlc-challenger):**

1. Are coverage assessments backed by concrete file evidence, or inferred?
2. Are autonomy ratings realistic given harness maturity (harness constraints automation)?
3. Are role readiness claims validated against actual team structure signals?
4. Are toolchain recommendations discoverable and installable today?
5. Does the pilot recommendation meet the §pilot scoring threshold? Show the math. Is API-readiness criterion scored?
6. Is Quality Funnel evidence present? If assessor claims Tier 2+, is MR gate issue volume documented?
7. Are all new §harness primitives explicitly assessed (or explicitly noted as absent)? Silently skipping a primitive is a challenger flag.
<!-- §lens-end -->
