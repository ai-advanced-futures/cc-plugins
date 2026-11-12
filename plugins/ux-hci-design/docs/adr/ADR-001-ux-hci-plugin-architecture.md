# ADR-001: UX/HCI Design Plugin Architecture

**Status:** Accepted
**Date:** 2026-01-22
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Architect:** Luis F. Amadeo
**Port note:** This text is the port of the original ADR to the cc-plugins marketplace. The decision of 2026 stands. The port changed names and tool grants only. See "Changes made for the marketplace port" in the section Consequences.

---

## Context

Software teams have a gap. The methods that made UX/HCI design a strict discipline do not reach current practice. These are the problems:

1. **Lost foundations.** New designers do not know the basic HCI principles of Norman, Nielsen, Cooper, and Rams.
2. **AI-era gaps.** Existing UX frameworks are older than AI interfaces. They do not cover how people and AI work together.
3. **Accessibility debt.** Teams add WCAG compliance late. They do not design it in from the start.
4. **Workflow silos.** Discovery (JTBD), requirements (PRD), and design (UX) are separate activities.
5. **Ad-hoc practice.** No repeatable UX method exists that has the discipline of ODI for product discovery.
6. **Generic AI design.** AI-generated interfaces have no clear intent and no theory behind them.

The current UX tools have these limits:

- **Existing design plugins** focus on how an interface looks. They do not give a UX method.
- **The JTBD plugin** gives strict discovery. It does not connect to UX artifacts.
- **The PRD plugin** records requirements. It does not turn them into user-centered design deliverables.
- **No complete UX method plugin** that rests on design theory exists.

This ADR records the architecture decisions for a UX/HCI Design plugin that closes these gaps.

---

## Decision

We build a **UX method plugin for the full lifecycle**. The plugin does these things:

1. **Bases design on theory.** It encodes the methods of the design masters (Norman, Nielsen, Cooper, Rams, Jobs, and others) as JSON schemas. A machine can read them, and the AI can explain them.
2. **Gives a structured workflow.** The workflow follows the framework Empathize, Define, Ideate, Prototype, Test. It has a guided mode and a flexible mode.
3. **Connects to the ecosystem.** It makes UX artifacts from JTBD and PRD output.
4. **Treats modern needs as cross-cutting.** Accessibility and AI-HCI are part of each phase. They are not added at the end.
5. **Serves all skill levels.** Beginners use an orchestrator. Advanced users use commands for single phases.
6. **Produces outputs in several formats.** The formats are JSON, Mermaid, code, and Markdown. Other tools can use them.

We build the plugin as follows:

- **Platform:** a Claude Code plugin that runs the full workflow.
- **Architecture:** a hybrid of commands and agents (one orchestrator and several specialists).
- **Knowledge encoding:** structured JSON schemas. A machine can read them, and the AI can explain them.
- **Output format:** specialized formats for each artifact type.
- **Validation:** three layers (examples, schemas, tests).

---

## Architecture Decisions

### 1. Scope: Full lifecycle and integration bridge

**Decision:** The plugin supports the complete UX lifecycle. It also bridges from JTBD and PRD.

**Rationale:**
- **The design masters cover the full range.** Norman (research), Nielsen (evaluation), Cooper (personas), and Rams (principles) together cover the whole UX process.
- **Strict method needs completeness.** A partial workflow has no discipline and no consistency.
- **Integration adds value.** A JTBD or PRD output that becomes a UX artifact makes the tools work together.
- **Real practice is holistic.** UX practitioners work across the full lifecycle.

**Modes of operation:**
1. **Standalone mode.** The plugin guides the practitioner through the full UX process (research, design, evaluation).
2. **Integration mode.** The plugin accepts JTBD or PRD input and makes baseline artifacts. Then it starts a guided refinement.

**Trade-offs:**
- ✅ **Pro:** It covers UX practice from start to end.
- ✅ **Pro:** The work flows from discovery to requirements, design, and build.
- ✅ **Pro:** It serves new projects and existing SDLC processes.
- ❌ **Con:** The scope is larger and the build takes longer.
- ❌ **Con:** It is more complex than a tool for one phase.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Discovery-focused only** | Simpler, focused | Doesn't help with design/evaluation | ❌ Rejected |
| **Evaluation-focused only** | Quick value, clear output | Misses strategic UX work | ❌ Rejected |
| **Design-generation only** | Fast deliverables | No research or validation | ❌ Rejected |
| **Full-lifecycle + Integration** | Complete, integrated | Complex, larger scope | ✅ **Selected** |

### 2. Methodology framework: Iterative framework

**Decision:** Use the design thinking framework (Empathize, Define, Ideate, Prototype, Test) as a cycle that repeats.

**Rationale:**
- **It matches real practice.** UX work repeats and goes wide, then narrow. It is not a straight line.
- **It uses the strength of each master.** Each phase draws on the methods of specific experts.
- **It has natural connection points.** JTBD maps to Define. PRD maps to Prototype.
- **It is flexible.** Users can start at any phase and repeat a phase when needed.

**Phase-master mapping:**
- **EMPATHIZE:** Norman (observation), Cooper (ethnography), Moggridge (contextual inquiry)
- **DEFINE:** Cooper (personas), Garrett (5 elements), Cagan (opportunity assessment), Kolko (synthesis)
- **IDEATE:** Rams (10 principles), Jobs/Ive (simplicity), Maeda (computational thinking)
- **PROTOTYPE:** Wroblewski (mobile-first), Moggridge (interaction patterns), Walter (emotional design)
- **TEST:** Nielsen (heuristics), Krug (usability testing), Norman (discoverability evaluation)

**Trade-offs:**
- ✅ **Pro:** It shows real UX practice, which is a cycle.
- ✅ **Pro:** Each phase has a clear purpose and expert support.
- ✅ **Pro:** Users can repeat phases as needed.
- ✅ **Pro:** It fits agile and iterative development.
- ❌ **Con:** It is more complex than a linear checklist.
- ❌ **Con:** Users must know when to repeat a phase and when to move on.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Linear phase model** | Simple, clear sequence | Doesn't match real practice | ❌ Rejected |
| **Deliverable-driven** | Flexible, composable | No guided workflow for beginners | ❌ Rejected |
| **Framework-based iterative** | Matches reality, expert-grounded | More complex | ✅ **Selected** |

### 3. Cross-cutting concerns: Accessibility and AI-HCI in all phases

**Decision:** Put accessibility and AI-HCI checkpoints in every phase. Do not treat them as separate topics.

**Rationale:**
- **Future use.** Most software will use or deliver AI features.
- **Prevention costs less than repair.** A problem found early (Empathize, Define) costs less than a fix at the end (Test).
- **Industry direction.** Leading companies (Anthropic, Google, Microsoft) treat AI UX as a base need.
- **Equal rank.** Accessibility and AI-HCI are human-centered design requirements. They are not add-ons.

**Implementation:**
- Each phase has **3 checkpoint categories:** Core UX, Accessibility, AI-HCI.
- Example in EMPATHIZE: find how the mental models of users about AI differ from their models of normal software.
- Example in PROTOTYPE: design AI confidence indicators, explanation UI, and controls that keep a human in the loop.

**Standards in the plugin:**
- **Accessibility:** WCAG 2.2, Section 508, ARIA patterns
- **AI-HCI:** Microsoft 18 Guidelines, Google PAIR Guidebook, Shneiderman's Human-Centered AI

**Trade-offs:**
- ✅ **Pro:** It prevents accessibility debt and AI-HCI debt. Design-in costs less than repair.
- ✅ **Pro:** It stays useful as AI becomes common.
- ✅ **Pro:** It makes better products for all users.
- ❌ **Con:** Each phase becomes more complex.
- ❌ **Con:** Practitioners must learn a new framework (AI-HCI).

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Cross-cutting (both)** | Prevention, future-proof | More complex | ✅ **Selected** |
| **Dedicated evaluation phase** | Simpler, isolated | Too late, remediation expensive | ❌ Rejected |
| **Optional/on-demand** | Simpler workflow | Easy to skip, technical debt | ❌ Rejected |

### 4. Plugin architecture: Orchestrator, phase commands, and quick actions

**Decision:** Give one main orchestrator command. Add commands for single phases and quick actions.

**Rationale:**
- **Two user types.** Beginners need a guided workflow. Advanced users need targeted tools.
- **It matches professional practice.** Some projects need the full UX process. Others need only a quick heuristic evaluation.
- **SDLC integration.** Advanced users add UX checkpoints at specific SDLC gates.
- **Growing complexity.** Users start with the orchestrator. Later they use the phase commands.

**Command structure (the design of 2026):**
```
PRIMARY COMMAND (Orchestrator):
/ux:design → Full guided workflow through all 5 phases

PHASE-SPECIFIC COMMANDS (Advanced):
/ux:empathize → Research & discovery only
/ux:define → Synthesis & persona creation only
/ux:ideate → Concept generation only
/ux:prototype → Wireframe/prototype generation only
/ux:test → Evaluation & testing only

INTEGRATION COMMANDS:
/ux:integrate → Import JTBD/PRD data, auto-generate baseline artifacts

QUICK-ACTION COMMANDS (SDLC checkpoints):
/ux:evaluate-heuristics → Nielsen's 10 + AI-HCI quick eval
/ux:accessibility-audit → WCAG compliance check
/ux:generate-persona → Single persona from data
/ux:journey-map → Single journey map
```

**Trade-offs:**
- ✅ **Pro:** It serves beginners and advanced users.
- ✅ **Pro:** It allows SDLC integration at specific gates.
- ✅ **Pro:** Users see simple tools first and advanced tools later.
- ❌ **Con:** The plugin has more commands to maintain.
- ❌ **Con:** The documentation must say when to use each command.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Single orchestrator only** | Simple, guided | No flexibility for advanced users | ❌ Rejected |
| **Individual commands only** | Maximum flexibility | No guidance for beginners | ❌ Rejected |
| **Hybrid structure** | Serves all user types | More commands to maintain | ✅ **Selected** |

### 5. Agent architecture: Orchestrator and specialists

**Decision:** Use one orchestrator agent and specialist agents (researcher, evaluator, artifact generator).

**Rationale:**
- **Separate duties.** Each agent has deep knowledge of its own area.
- **Coordination need.** A full-lifecycle workflow needs coordination across phases.
- **Reuse.** Advanced users can start a specialist directly.
- **Context control.** The orchestrator keeps the context across phases. The specialists do the work.

**Helper structure (STORY-371: the 8 helpers are forked skills, and the folder of the agent files is gone):**
```
skills/
  ux-design/SKILL.md             → Manages full workflow, starts the helper skills
  ux-researcher/SKILL.md         → Empathize phase expertise
  ux-evaluator/SKILL.md          → Test phase, all evaluation frameworks
  ux-artifact-generator/SKILL.md → Define phase, generates deliverables
  (and 5 more helpers: the 3 reviewers, ux-concept-designer, ux-prototype-builder)
```

**Trade-offs:**
- ✅ **Pro:** The duties are clearly separate.
- ✅ **Pro:** Each specialist has a narrow focus.
- ✅ **Pro:** Advanced users can reuse the specialists through the phase commands.
- ❌ **Con:** Context passes from one agent to the next.
- ❌ **Con:** It is more complex than one agent.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Single UX agent** | Simpler, maintains context | Too large, hard to maintain | ❌ Rejected |
| **Phase-specific agents** | Maximum specialization | Complex context handoff | ❌ Rejected |
| **Hybrid (orchestrator + specialists)** | Balanced specialization + coordination | Moderate complexity | ✅ **Selected** |

### 6. Knowledge encoding: Structured schemas

**Decision:** Encode the frameworks of the design masters as JSON schemas. Do not use reference documents.

**Rationale:**
- **One source of truth.** Docs and schemas do not duplicate each other, so they cannot drift apart.
- **Made for AI.** Claude can explain, summarize, and put a schema in context when asked. Users do not need separate docs.
- **Directly usable.** Evaluation commands can score against the schemas in code.
- **Forced precision.** A structured format makes the content exact and complete.
- **Easy to connect.** Automated checks, CI/CD pipelines, and linters can use JSON schemas.

**Schema architecture:**
```
schemas/
  heuristics/
    nielsen-usability-10.json          # Classic 10 heuristics with scoring rubric
    ai-hci-microsoft-18.json           # AI interaction guidelines
    combined-heuristics.json           # Unified evaluation framework

  design-principles/
    norman-interaction-principles.json # Affordances, feedback, mental models
    rams-good-design-10.json           # 10 Commandments with evaluation criteria
    cooper-goal-directed.json          # Goal-directed design process
    jobs-simplicity-principles.json    # Apple design philosophy

  accessibility/
    wcag-2.2-criteria.json             # Full WCAG 2.2 testable criteria
    aria-patterns.json                 # Accessible interaction patterns

  frameworks/
    garrett-five-elements.json         # UX framework layers
    design-thinking-phases.json        # Empathize→Test process

  outputs/
    persona-schema.json                # Persona artifact structure
    journey-map-schema.json            # Journey map format
    evaluation-report-schema.json      # Test phase outputs
```

**Trade-offs:**
- ✅ **Pro:** One source of truth. Docs and schemas cannot drift apart.
- ✅ **Pro:** The AI explains on request, so nobody must maintain extra docs.
- ✅ **Pro:** Code can score against the schemas.
- ✅ **Pro:** CI/CD and linters can use the schemas.
- ❌ **Con:** People read JSON less easily than Markdown docs.
- ❌ **Con:** Schema design needs strict work at the start.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Reference documents (markdown)** | Human-readable, easy to write | Requires parsing, ambiguous | ❌ Rejected |
| **Structured schemas (JSON)** | Machine-readable, actionable | Less human-readable | ✅ **Selected** |
| **Hybrid (docs + schemas)** | Best of both | Maintenance burden, drift risk | ❌ Rejected |

### 7. Framework display: Explicit labels

**Decision:** Show the framework label in the output (for example "Nielsen Heuristic #7"). Do not apply frameworks without a label.

**Rationale:**
- **Learning by exposure.** Users see the labels often and learn the patterns over time.
- **No teaching delay.** The workflow does not slow down.
- **Traceability.** Users can look up a principle when they want more detail.
- **Credibility.** A report that cites specific frameworks has more authority.

**Example output:**
```markdown
## Heuristic Evaluation Results

### ❌ Nielsen Heuristic #1: Visibility of System Status
**Severity: Major (3/4)**
Issue: Loading state not shown during transaction processing
Recommendation: Add progress indicator with estimated time

### ✅ Rams Principle #3: Good Design is Aesthetic
Clean visual hierarchy with appropriate whitespace
```

**Trade-offs:**
- ✅ **Pro:** Users learn naturally through exposure.
- ✅ **Pro:** The workflow does not slow down for teaching.
- ✅ **Pro:** The output has traceability and credibility.
- ❌ **Con:** Users may not understand the labels at first. This is acceptable, because they learn over time.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Implicit (hidden)** | Clean output | No learning, black box | ❌ Rejected |
| **Explicit (labeled)** | Traceable, educational | Slightly verbose | ✅ **Selected** |
| **Teachable (explained)** | Maximum learning | Slows workflow significantly | ❌ Rejected |

### 8. Scoring method: Weights that depend on context

**Decision:** Weight the evaluation criteria by the project context (type, domain, AI intensity, accessibility requirements).

**Rationale:**
- **Context matters.** A mobile fitness app, an enterprise dashboard, and an AI agent have different UX priorities.
- **AI features need more weight.** A product with AI features needs a higher AI-HCI weight.
- **Stakeholders agree.** The scores show what matters for the product.
- **Clear priorities.** Teams know what to fix first in their context.

**Context dimensions:**
```json
{
  "project_context": {
    "type": "mobile-app | web-app | enterprise | ai-agent | iot | voice",
    "domain": "consumer | b2b | healthcare | finance | education",
    "ai_intensity": "none | light | moderate | heavy | core",
    "accessibility_requirements": "none | voluntary | required | critical"
  }
}
```

**Weighting example (AI-heavy consumer mobile):**
```json
{
  "weights": {
    "nielsen_heuristics": 0.25,
    "ai_hci_guidelines": 0.40,
    "accessibility": 0.15,
    "mobile_patterns": 0.20
  }
}
```

**Trade-offs:**
- ✅ **Pro:** The scores are accurate for the real context.
- ✅ **Pro:** Teams know what matters for their product.
- ✅ **Pro:** AI-HCI gets the correct weight.
- ❌ **Con:** It is more complex than one scoring scale for all projects.
- ❌ **Con:** The plugin must detect or receive the context.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Universal scoring (all equal)** | Simple, consistent | Ignores context, inaccurate | ❌ Rejected |
| **Industry-standard only** | Familiar (Nielsen 0-4) | Doesn't integrate frameworks | ❌ Rejected |
| **Unified 0-100 score** | Easy to aggregate | Loses framework specificity | ❌ Rejected |
| **Contextual weighting** | Real-world accurate | More complex | ✅ **Selected** |

### 9. Context detection: Detect, confirm, and save

**Decision:** Detect the context from the codebase. Show it to the user for confirmation. Save it to `.ux-config.json`.

**Rationale:**
- **No setup.** Detection removes friction.
- **Accuracy.** The user confirms the result, so a wrong class is caught.
- **Learn once.** The config file keeps the context for later sessions.
- **Override.** Users can set the context again when needed.

**Flow (the design of 2026):**
```
1. User runs: /ux:design
2. Plugin auto-detects:
   - package.json → React web app
   - @anthropic-ai/sdk → AI-heavy
   - WCAG references → accessibility-aware
3. Plugin presents: "Detected: Web app, Consumer, AI-heavy, Accessibility required"
4. User confirms or modifies
5. Plugin saves to: .ux-config.json
6. Future runs: "Using saved context from .ux-config.json (override with --reconfigure)"
```

**Trade-offs:**
- ✅ **Pro:** Good UX: smart defaults and human oversight.
- ✅ **Pro:** Accurate: the user checks the detection.
- ✅ **Pro:** The user answers once. The plugin saves the answer.
- ❌ **Con:** It is the most complex option to build (detection, confirmation, and saving).

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Explicit config only** | No ambiguity | Requires user knowledge, manual setup | ❌ Rejected |
| **Auto-detect only** | Zero friction | May misclassify, no override | ❌ Rejected |
| **Interactive discovery** | Accurate | Adds friction to every run | ❌ Rejected |
| **Hybrid (auto + confirm + save)** | Best UX, accurate, flexible | Complex implementation | ✅ **Selected** |

### 10. Output formats: Specialized formats

**Decision:** Each artifact type uses the best format for it. Personas use JSON. Journey maps use Mermaid. Prototypes use code. Reports use Markdown.

**Rationale:**
- **Fit for purpose.** Each artifact has its own use and its own readers.
- **Easy to connect.** Downstream tools (PRD, analytics, marketing) can read JSON.
- **Version control.** Code and Mermaid work well in git.
- **Easy to read.** Stakeholders can read Markdown reports.

**Format strategy:**
- **Personas:** JSON schema (code, PRD tools, and analytics can read it)
- **Journey maps:** Mermaid diagrams (visual, and git can track them)
- **Mental models:** Mermaid or DOT graphs
- **Wireframes and prototypes:** React, HTML, or SVG code artifacts
- **Evaluation reports:** Markdown with scoring tables
- **Design principles:** YAML or JSON (for automated checks)
- **Accessibility audits:** JSON (WCAG criteria and results)
- **AI-HCI evaluations:** JSON (scores for the Microsoft 18 guidelines)

**Trade-offs:**
- ✅ **Pro:** Each format fits its purpose.
- ✅ **Pro:** Downstream tools can use the output.
- ✅ **Pro:** Version control works well.
- ✅ **Pro:** The outputs have professional quality.
- ❌ **Con:** The team must maintain several format generators.
- ❌ **Con:** Users must understand several formats.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Markdown only** | Simple, human-readable | Hard to parse, poor integration | ❌ Rejected |
| **JSON only** | Machine-readable | Poor for reports/visual artifacts | ❌ Rejected |
| **Multi-format specialized** | Optimal per artifact | More complex | ✅ **Selected** |

### 11. JTBD/PRD integration: Auto-generate, then refine with guidance

**Decision:** Make baseline artifacts from JTBD and PRD automatically. Then start a guided refinement workflow.

**Rationale:**
- **Fast value.** Auto-generation saves hours of manual work.
- **Quality.** Guided refinement keeps the work strict and finds gaps.
- **Learning.** Practitioners see how JTBD maps to UX and build skills.
- **No loss.** The transformation logic keeps all information.

**Transformation examples:**

| Input | Output | Transformation |
|-------|--------|----------------|
| JTBD Job Statement | Design Goal | Job becomes actionable goal |
| JTBD Job Steps | Journey Map phases | Steps map to journey phases |
| JTBD Customer Needs | User Requirements | Needs become prioritized requirements |
| JTBD Market Segments | Proto-personas | Segments become enriched personas |
| JTBD Opportunity Scores | Design Priority | Scores inform priority ranking |
| PRD Requirements | Feature Specs | Requirements become interaction specs |
| PRD Success Metrics | UX Metrics | Metrics align with UX measurement |

**Trade-offs:**
- ✅ **Pro:** The baseline is ready fast.
- ✅ **Pro:** Refinement keeps the quality high.
- ✅ **Pro:** Users see the transformations and learn from them.
- ❌ **Con:** The team must maintain the transformation logic.
- ❌ **Con:** It is more complex than a manual-only approach.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Auto-generate only** | Fastest | May lose nuance, lower quality | ❌ Rejected |
| **Guided manual only** | Highest quality | Slow, tedious | ❌ Rejected |
| **Hybrid (auto + refine)** | Speed + quality | More complex | ✅ **Selected** |

### 12. Validation strategy: Three layers

**Decision:** Use examples, schemas, and tests together for full validation.

**Rationale:**
- **No framework distortion.** Several layers catch a drift in the meaning of a framework.
- **Faithful transformation.** The JTBD to UX transformations keep the information.
- **Bias and false output.** The schemas force the use of real frameworks, not invented ones.
- **Quality control.** CI/CD catches regressions.

**The three layers:**

1. **Examples** (`/examples/`): documentation, expected outputs, and training data.
2. **Schemas** (`/schemas/`): runtime validation, error messages, and structural integrity.
3. **Tests** (`/tests/`): CI/CD quality gates, transformation accuracy, and framework fidelity.

**Trade-offs:**
- ✅ **Pro:** Layered defense stops quality loss.
- ✅ **Pro:** Each validation point catches a different type of error.
- ✅ **Pro:** CI/CD automation catches regressions.
- ❌ **Con:** It is the most complex validation approach.
- ❌ **Con:** It has the highest maintenance cost.

**Alternatives considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Examples only** | Simple, educational | No runtime validation | ❌ Rejected |
| **Schemas only** | Runtime validation | No documentation/tests | ❌ Rejected |
| **Tests only** | Automated quality gates | No runtime/doc validation | ❌ Rejected |
| **All three (comprehensive)** | Defense-in-depth | Complex, high maintenance | ✅ **Selected** |

---

## Consequences

### Positive

1. **Strong base.** The design rests on proven methods of the masters of the discipline.
2. **Future use.** AI-HCI and accessibility are part of the design from the start.
3. **Connected workflow.** The work flows from JTBD to PRD, UX, and build.
4. **Skill growth.** Users learn design theory through practice because the labels are explicit.
5. **Quality outputs.** The deliverables come in several formats for professional use and for downstream tools.
6. **Flexibility.** Beginners use the orchestrator. Advanced users use the phase commands.
7. **Maintenance.** Structured schemas are the single source of truth.
8. **Growth.** The architecture lets the team add new frameworks, phases, or outputs.

### Negative

1. **Build complexity.** The full lifecycle, integration, and validation make a large scope.
2. **Maintenance cost.** The team maintains several agents, schemas, and formats.
3. **Learning curve.** Users must learn when to use each command.
4. **Schema change.** A change to a framework needs a careful schema update.
5. **Context detection.** The detection logic needs regular improvement.

### Risks and mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Scope creep** | Delays delivery | Phased implementation (foundation → core → polish) |
| **Schema rigidity** | Hard to evolve | Versioned schemas, backward compatibility |
| **Context misdetection** | Wrong priorities | User confirmation + override options |
| **Framework distortion** | Loss of fidelity | Three-layer validation (examples + schemas + tests) |
| **User confusion** | Poor adoption | Clear documentation, progressive disclosure |

### Changes made for the marketplace port

The original decision of 2026 stands. The port to the cc-plugins marketplace changed names and tool grants only.

- **Skills.** The plugin has 13 skills. A user runs each one as `/ux-hci-design:<skill>`. The skills are `accessibility-audit`, `ai-hci-audit`, `ask`, `define`, `empathize`, `ideate`, `jtbd-bridge`, `learn`, `prd-bridge`, `prototype`, `setup`, `ux-design`, and `ux-evaluate`.
- **Command names.** The command blocks above show the names of 2026. The skill `ux-design` replaces `/ux:design` (command: `/ux-hci-design:ux-design`). The skill `ux-evaluate` replaces the old skill `evaluate` and the commands `/ux:test` and `/ux:evaluate-heuristics`. The skills `jtbd-bridge` and `prd-bridge` replace `/ux:integrate`. The phase commands and `accessibility-audit` keep their names. The skill `ai-hci-audit` runs the AI-HCI audit alone.
- **Skill names.** The `name:` line in the frontmatter of a skill is the folder name (for example `name: ux-design`). The plugin adds the prefix `ux-hci-design:`.
- **Agents.** The plugin has 8 agents: `accessibility-reviewer`, `ai-hci-reviewer`, `usability-reviewer`, `ux-artifact-generator`, `ux-concept-designer`, `ux-evaluator`, `ux-prototype-builder`, and `ux-researcher`. A skill calls an agent with the name `ux-hci-design:<agent>`. The skill `ux-design` coordinates the phases and starts every agent. The original design had a separate agent that managed the phases; it is not in the plugin.
- **Questions.** An agent cannot ask the person a question. The skill `ux-design` asks the questions with AskUserQuestion.
- **Tool grants.** No helper can start a helper: each helper names `Agent` in its `disallowed-tools`, and each helper except `ux-prototype-builder` also names `Skill`. The skill `ux-design` starts the 3 reviewers, then `ux-evaluator`. Only `ux-prototype-builder` has the Skill tool.
- **Optional plugin.** The tailwind-plus plugin is optional and paid. It is not in this marketplace.

---

## Implementation Plan

### Phase 1: Foundation (weeks 1-2)
- Plugin structure and configuration
- Core schema design (Nielsen, Rams, Norman, WCAG, AI-HCI)
- Schema validation framework
- Context detection logic
- Basic orchestrator agent

### Phase 2: Core workflow (weeks 3-4)
- Empathize and Define phases
- Researcher agent
- Artifact generator agent
- JTBD integration bridge (transformation logic)
- Persona and journey map generation

### Phase 3: Design and prototype (weeks 5-6)
- Ideate and Prototype phases
- Wireframe and prototype generation
- PRD integration bridge
- Context-aware weighting system
- `.ux-config.json` persistence

### Phase 4: Evaluation (weeks 7-8)
- Test phase
- Evaluator agent (Nielsen, Rams, AI-HCI, WCAG)
- Contextual scoring engine
- Evaluation report generation
- Quick-action commands

### Phase 5: Polish and documentation (weeks 9-10)
- Example workflows (at least 3 complete examples)
- Full tests (integration, validation, and output)
- Documentation (README, guides, schema docs)
- Marketplace preparation

---

## Related Decisions

- **Influenced by:** the ADR-001 of the jtbd-market-discovery plugin. It gave the method rigor, the output formats, and the integration patterns.
- **Integrates with:** the JTBD Market Discovery plugin, the PRD plugin, and a developer agent that builds the interface.
- **Future decisions planned in 2026:**
  - ADR-002: web compatibility and a fallback for Claude.ai (if needed). The number ADR-002 now holds the design handoff decision. The web decision has no ADR yet.
  - ADR-003: advanced features (conjoint analysis, eye-tracking integration, and others).

---

## References

### Design master works
- Norman, D. (2013). *The Design of Everyday Things*
- Nielsen, J. (1994). *Usability Engineering*
- Cooper, A. (2014). *About Face: The Essentials of Interaction Design*
- Krug, S. (2014). *Don't Make Me Think, Revisited*
- Garrett, J. J. (2010). *The Elements of User Experience*

### AI-HCI standards
- Amershi, S., et al. (2019). *Guidelines for Human-AI Interaction* (Microsoft Research)
- Google PAIR (2023). *Guidebook for AI UX*
- Shneiderman, B. (2022). *Human-Centered AI*

### Accessibility standards
- W3C (2023). *WCAG 2.2 Guidelines*
- W3C (2023). *ARIA Authoring Practices Guide*

### Plugin architecture
- Claude Code plugin documentation
- Claude Code plugin marketplace standards

---

**Update (STORY-257, version 1.6.0):** the output of the plugin is a brain of the brain standard. The agents still write plain files to `<output_dir>`. After each phase the skill `ux-design` saves them as pages in `docs/ux-hci-design/` with `scripts/ux_graph.py`, and removes the files that it read. The skills `setup`, `learn` and `ask` work on the brain. The first save asks if git keeps the brain, because the pages can hold facts about real people.

**Status:** Ready for implementation
**Next steps:** Start Phase 1 (Foundation)

2026-11-11 (STORY-371, D-1064): the 8 agents are forked helper skills in `skills/<name>/`, and their agent files are deleted.
