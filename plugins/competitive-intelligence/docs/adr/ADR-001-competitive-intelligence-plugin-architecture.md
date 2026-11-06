# ADR-001: competitive-intelligence Plugin — Architecture Decisions

**Status:** Accepted
**Date:** 2026-02-28
**Plugin:** competitive-intelligence 1.0.0 and 1.1.0 (Decision 1 amended 1.3.0; Decisions 1, 4 and 6 amended 1.7.0)

---

## Context

The marketplace had plugins for product strategy, go-to-market, engineering, and financial intelligence. It had no tool for systematic competitive analysis. Product teams and business leaders did competitive work ad hoc: separate spreadsheets, informal reviews, and single-lens assessments that missed structural threats. The plugin must:

- Cover the full competitive ecosystem (direct, indirect, substitutes, non-consumption, technology disruption threats)
- Run several strategic frameworks (JTBD, Forces, Economic Value, Strategic Positioning, Technology Disruption, Loss/Churn) with intelligent cascading, and not as separate silos
- Produce AI-native structured outputs (JSON files, Python scripts) that other plugins can read (pricing, gtm, business-case), and not only reports for people
- Change its depth and lens priority to fit the trigger (feature validation, competitive response, strategic planning, ongoing monitoring)
- Let a coach plugin run it with prepared answers, with no person to answer a question

**1.0.0** set up the agent architecture with six lens skills and the full 6-phase workflow. **1.1.0** applied the file-based inter-agent protocol to solve a context-window problem. The context of the caller grew with the output of each phase. This caused silent loss of accuracy in later phases.

---

## Decision Drivers

- **Evolutionary architecture first:** Start with the smallest pipeline that does the job. Add complexity only after use shows the need. 1.0.0 was the MVP. 1.1.0 reduced the context size after the growth problem showed in practice.
- **Agents orchestrate agents:** One agent cannot keep the six strategic lenses independent. Each lens must reason fresh, with no influence from the conclusions of an earlier lens. A pipeline of several agents with clear boundaries is the correct design.
- **Human in the loop:** The person sees a checkpoint at each phase boundary (Context, Ecosystem, Intelligence, Lens Analysis, Synthesis, Deliverables). The person can redirect, deepen, or cancel before the work goes on. A run that a coach starts has no person, so it asks nothing and records each default it uses.
- **Economic equation:** Deterministic operations (confidence scoring, data triangulation, economic value modeling, loss/churn aggregation) belong in Python scripts. Probabilistic reasoning (competitor interpretation, gap analysis, strategic implications, recommendations) belongs in LLM agents. LLM tokens spent on exact math are waste. Python spent on strategic reasoning is fragile.
- **Continuous intelligence loop:** The monitoring trigger (`monitoring`) maps to the cycle OBSERVE, ANALYZE, DERIVE, TEST, DEPLOY OFTEN, VERIFY. The plugin can run again against the artifacts of an earlier session for an incremental update. It is not only for fresh analyses.

---

## Considered Options

### Option A: One skill, no agents

Do all six lenses one after the other in one context window.

**Pros:** Simplest to build; no coordination work; works on any platform.
**Cons:** The context window collects the ecosystem map, all six lens analyses, and the synthesis together. This is 70-90K tokens before the deliverables start. Compaction removes early-phase decisions (user scope, competitor priorities, confidence thresholds) before the later lenses run. Loss/Churn must validate all earlier lenses, but it runs last on a context that has lost detail. Layers 2 and 3 cannot run in parallel. A coach plugin cannot run it with prepared answers without the same context failure.

### Option B: Python-first pipeline

Do ecosystem mapping, lens scoring, and deliverable generation mainly in Python. Use the LLM only for the final synthesis text.

**Pros:** Fully deterministic; fast; testable at each stage.
**Cons:** Competitor interpretation, job-step gap assessment, forces analysis, moat identification, and disruption evaluation are reasoning tasks. They are not rule-based lookups. NLP pipelines that copy this reasoning in Python cost too much, and they give lower quality than LLM agents with good lens instructions.

### Option C: Hybrid — agent pipeline + 6 lens skills + Python scripts for deterministic work (chosen)

Split the plugin into three layers:
1. LLM agents for the 6-phase workflow (context-analyst, ecosystem-mapper, intelligence-gatherer, lens-executor, synthesizer, deliverable-generator). A skill in the main conversation starts them and coordinates them.
2. LLM lens skills (SKILL.md files) for independent analysis by lens, with intelligent cascading across 4 execution layers.
3. Python scripts for deterministic operations: confidence scoring, triangulation, economic value modeling, loss/churn data processing, the result file name, vendor archetype classification.

---

## Decision Outcome

**Chosen: Option C — Hybrid.**

### Decision 1: Agent Pipeline Architecture (1.0.0, amended 1.7.0)

The plugin has nine agents with clear role boundaries. Six agents run the phases. Two runners route a coach to the result file (ADR-004). One agent classifies vendor pricing (ADR-002).

| Agent | Model | Role |
|-------|-------|------|
| context-analyst | sonnet | Phase 1: scoping, lens priority configuration, from the answers in its dispatch |
| ecosystem-mapper | sonnet | Phase 2: multi-dimensional competitor classification (6 dimensions) |
| intelligence-gatherer | sonnet | Phase 3: multi-source data collection, triangulation, confidence scoring |
| lens-executor | sonnet | Phase 4: thin coordinator that reads the 6 lens skills and follows them across 4 execution layers |
| synthesizer | opus | Phase 5: cross-lens integration, SWOT, confidence-weighted recommendations |
| deliverable-generator | sonnet | Phase 6: AI-native artifacts (JSON, Python scripts), human artifacts, and the rules of the result file |
| discover-runner | sonnet | Route for a coach: follows `discover` with the answers of a `plugin-run` block |
| analyze-runner | sonnet | Route for a coach: follows `analyze` with the answers of a `plugin-run` block |
| vendor-archetype-classifier-agent | sonnet | Extracts the pricing signals of one vendor and runs the classifier |

Every agent uses the sonnet model, except the synthesizer, which uses opus *(amended 1.3.0)*. The synthesizer is the last analysis step and the only consumer of the full data (Decision 5). It writes the final SWOT and recommendations that the person reads, so the role-tier rule for the synthesis role applies (opus). The individual lenses stay on sonnet, because the reasoning of a lens fits the capability of sonnet at this problem size.

**Amendment (1.7.0):** The coordinator is not an agent. It is the skill `competitive-intelligence`. The coordinator must ask the person at each checkpoint, and Claude Code removes `AskUserQuestion` from every subagent. So the coordinator runs in the main conversation. It starts the phase agents with the `Agent` tool, under the names `competitive-intelligence:<agent>`.

**Rationale:** One coordinator that holds the full 6-phase workflow in one context would reach 70-90K tokens before Phase 6. Role separation keeps the context of each agent small. The lens-executor is thin on purpose. Its job is coordination, not analysis.

### Decision 2: Six-Lens Execution with Intelligent Cascading (1.0.0)

The six lenses form 4 execution layers that follow the causal dependencies:

```
Layer 1:   jtbd-performance
                  ↓ (gives push/pull signals and value baselines)
Layer 2:   forces-analysis  |  economic-value
                  ↓
Layer 3:   strategic-positioning  |  technology-disruption
                  ↓
Layer 4:   loss-churn  ← validates all earlier lenses with ground-truth data
```

The lens executor runs the layers in this order. Amended 1.7.0: the `Agent` tool starts an agent, not a skill. So for each lens the executor reads the lens skill file (`skills/lenses-<name>/SKILL.md`) and follows it in its own context. The lenses in one layer run one after the other.

**Loss/Churn as ground-truth override:** When `retention_risk = HIGH` and `confidence ≥ MEDIUM`, loss-churn can override the confidence assessments of all other lenses, because customer behavior data has more weight than framework inference.

> **⚠️ Override mechanism DISABLED pending a product decision (annotated 1.2.8).** The original design had the `loss_churn_validated` flag *upgrade* confidence by one tier in `propagate_confidence()`. That code path is now **disabled: `propagate_confidence(loss_churn_validated=True)` raises `NotImplementedError`**. There is an unresolved **contradiction**. The code would *upgrade* the confidence of the recommendation. The agent instructions (`synthesizer.md`, "Loss/Churn Ground Truth Override") *downgrade* every competing lens to LOW. These are opposite directions. Until the product decision on upgrade or downgrade is recorded, only the manual aggregation of the synthesizer applies the override (downgrade competing lenses to LOW). `propagate_confidence()` never applies it. See `scripts/confidence_scoring.py` (the `# KNOWN CONTRADICTION` block) and `agents/synthesizer.md`.

**Rationale:** JTBD runs first because each later lens needs job-step data (Forces needs push and pull from job gaps; Economic Value needs the job performance gains in numbers). Layers 2 and 3 do not depend on each other. Loss/Churn runs last because it validates the claims of every other lens. If it ran earlier, it would lose its ground-truth role.

### Decision 3: File-Based Inter-Agent Protocol (1.1.0)

Each agent writes its output to disk and returns only a completion signal (`DONE: {phase}`) to its caller. A caller never keeps agent content in its context window.

**Problem solved:** In 1.0.0 the coordinator collected the full output of all 6 phases. It reached about 70-90K tokens by Phase 6. Compaction then removed Phase 1 decisions (user scope, competitor priorities, confidence thresholds) before the later phases ran. The lens executor collected about 40-60K tokens across the 6 lens analyses. Compaction removed the JTBD context before the Loss/Churn validation, which needs that context the most.

**Context window impact:**

| Component | Before 1.1.0 | After 1.1.0 |
|-----------|--------------|-------------|
| Coordinator ceiling | ~70-90K tokens | ~3.2K tokens |
| Lens-executor ceiling | ~40-60K tokens | ~10K tokens |

**Checkpoint flow (when a person runs the skill):**
```
Phase N complete → receive "DONE: {phase}"
→ Read <session>/{phase}-summary.json  (targeted read, not accumulation)
→ Show the summary to the person
→ AskUserQuestion: proceed / adjust / cancel
→ Update session.json → start the next phase
```

**Rationale:** The caller never holds agent output. The caller holds only signals and summaries. The full data is always on disk. A reader reads it fresh at the moment it needs it, and never carries it across a phase boundary.

### Decision 4: Session UUID Scoping (1.1.0, amended 1.7.0)

Each analysis run has its own session folder. The original design used an 8-character UUID. All session artifacts are in `.competitive-intelligence/<session>/`. The `<session>` name is the `run_id` of a coach run, or the start time of a run of a person.

**session.json** is the only state file of the coordinator. It tracks: session_id, mode, started_at, phases_complete, lenses_complete, current_phase, competitor_count, lens_failures, checkpoints_passed.

**Rationale:** One folder for each run lets several sessions run at the same time with no file conflicts. One state file, and not flags in many files, gives the coordinator one place to read before each phase.

The original design also had a start-up sweep that deleted sessions older than 60 minutes. That sweep never ran and is deleted (see the amendment in Decision 6).

### Decision 5: Summary File Pattern at Phase and Lens Boundaries (1.1.0)

Each phase agent and lens skill writes a compact `{phase}-summary.json` (about 50-100 lines) when it finishes, before it returns its DONE signal. The coordinator reads only the summary at a checkpoint, and never the full data file.

**Summary schema (the same for all phases and lenses):**
```json
{
  "phase": "{phase-name}",
  "completed_at": "{ISO-8601}",
  "headline": "{one-line summary}",
  "key_items": ["..."],
  "counts": {},
  "warnings": [],
  "data_file": "{full-data-file}.json"
}
```

**Rationale:** The coordinator must show a clear phase summary to the person at each checkpoint. Without summaries, it would read the full data file, and the context would grow. This defeats the file-based protocol. Summaries separate "what the coordinator needs to know" from "what the analysis produced".

**Scope: coordinators read summaries; the synthesizer is the documented exception.** This rule covers the *coordinator* reads: the skill at the phase checkpoints, and the lens executor at the cross-validation (1.2.5 changed it to read the 6 `{lens}-summary.json` files). The **synthesizer (Phase 5) is the only agent that reads the full data on purpose.** Its evidence-based SWOT cites detail for each competitor and each step (for example `jtbd-analysis.json` `competitor_a.speed = 5`) that the compact summaries do not have. So it reads the 6 full `{lens}-analysis.json` files. This is intentional and has a limit: synthesis is the last analysis step and it starts no agent after it. So it does not carry full data across a phase boundary, and the rule ("callers never carry agent output across boundaries") still holds.

### Decision 6: Questions Only in Skills; Agents Take Answers From Dispatch Fields (1.1.0, amended 1.7.0)

Claude Code removes `AskUserQuestion` from every subagent. So only a skill, which runs in the main conversation, asks the person. No agent of the plugin has `AskUserQuestion` or `Task` in its `tools:` list. The skill asks the intake questions first, then starts the agent with the answers as dispatch fields. An agent takes each answer from its dispatch fields and asks nothing. When an agent needs an answer during a run, it writes the open questions to `open-questions.json` in the session folder and returns `QUESTIONS: <path>`. The skill asks them and starts the agent again with the answers.

Trigger/mode taxonomy:
```
"trigger": "feature_decision | competitor_response | strategic_planning | monitoring"
"analysis_mode": "strategic_planning | sales_enablement"   (optional, default strategic_planning — ADR-003)
```

**Failure rule.** When a phase or a lens fails two times:
- A skill asks the person: Retry, Skip (a lens only), or Cancel.
- The lens executor marks a lens that fails two times `skipped`, writes the reason in `lens_failures`, and goes on. A reduced analysis is better than none.
- A runner writes the result file with a gap for the phase that failed.
- A phase that fails is fatal for the full run, because the phases depend on each other. A skipped phase damages every later phase.

**Rationale:** A subagent cannot ask a question, and a coach has no person to answer. The skill is the one place that knows whether a person is present. The agents have one rule: ask nothing and use the dispatch fields.

**Amendment (plugin-results, Part A):** new sessions are written to `.competitive-intelligence/{uuid}/`. A session begun in `.competitive-intel/` continues there. The orchestrator no longer carries a start-up sweep: no tool on that agent can list or delete, so the sweep never ran, and as written it would have deleted `monitoring-history/`. No agent or skill text tells the model to delete anything under either folder. The text above is the original decision and stays as written.

### Decision 7: Hybrid Python + LLM Architecture (1.0.0)

Python scripts do the deterministic operations. LLM agents do the reasoning.

**Python scripts (deterministic):**
- `confidence_scoring.py` — four-tier confidence propagation (HIGH/MEDIUM/LOW/SPECULATIVE); its `loss_churn_validated` override path is disabled (it raises `NotImplementedError` — see Decision 2). The agent text holds its thresholds.
- `triangulation.py` — multi-source claim validation and contradiction detection
- `workflow_engine.py` — phase sequencing and state management
- `lens_economic_value.py` — EVC calculations (time savings × hourly rate, error reduction × cost per error, revenue impact × margin, risk reduction × probability × impact)
- `lens_loss_churn.py` — win/loss pattern aggregation, churn frequency analysis
- `lens_technology_disruption.py` — multi-factor disruption scoring (capability maturity, economic feasibility, adoption barriers, timing)
- `plugin_integration.py` — schema generation for other plugins
- `phase_02_ecosystem_mapping.py` — multi-dimensional competitor classification (Type, JTBD Alternative, Threat Level, Stage, Market Overlap, Tech Disruption Factor)
- `web_research.py` — search and fetch helpers for competitor data
- `result_name.py` and `vendor_archetype_emitter.py` — the two scripts that a skill or an agent runs, with `uv run` (Decision 8)

**LLM agents do:** competitor interpretation, job-step performance gap analysis, forces assessment (push/pull/anxiety/habit), moat identification, disruption threat text, synthesis across lenses, confidence-weighted recommendations.

**Rationale:** This is the economic equation. Whether a disruption score is HIGH from four weighted factors is arithmetic. Whether that HIGH score means the company must leave a market segment is a strategic reasoning problem. The two belong in different layers.

### Decision 8: Script Calls With uv (1.7.0)

A skill or an agent runs a plugin script as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <args>`. Each of the two scripts that a prompt runs starts with a PEP 723 block that lists `requires-python` and its packages, so `uv` installs the packages when the script starts. The other modules of `scripts/` are a library with tests. No prompt runs them. The agent text holds the thresholds of `confidence_scoring.py`.

---

## Consequences

### Becomes easier

- **Confidence regression testing** — `confidence_scoring.py` gives deterministic outputs. The pytest suite checks the propagation rules and the override logic with no LLM.
- **Lens independence** — Each lens skill reads from disk and writes to disk. To add a 7th lens, add a SKILL.md file and a step in the lens executor. No other agent changes.
- **Coach plugins** — A coach runs `discover-runner` or `analyze-runner` with a `plugin-run` block and reads one checked result file.
- **Context preservation** — Phase 1 decisions (scope, competitor priorities, confidence thresholds) are in context-config.json on disk. Each later agent reads them fresh, and compaction cannot remove them.
- **Concurrent session support** — One folder for each run lets runs go in parallel with no file conflicts.

### Becomes harder

- **Cross-agent debugging** — When a lens fails, the error is in that lens and in the `lens_failures` log of session.json. To trace a contradiction across lenses, a person reads several JSON files and not one conversation.
- **Local development testing** — The file-based protocol needs a writable session folder at test time. A test of the coordinator logic must mock the summary file reads and the session.json writes.
- **Parallel lenses** — The lens executor runs the lenses one after the other, because it follows each lens skill in its own context. The result is the same as a parallel run, but the run takes longer.
- **Questions at the start** — The skill `discover` asks up to 7 questions before the first agent starts. The skill asks only the questions that have no answer in the arguments.

---

## Simplicity Gate Verdict

We applied `thinktank:debate` to this question: *"Is this architecture as simple as it must be for the competitive intelligence job?"*

**Not built in 1.0.0 and 1.1.0 on purpose:**
- MCP integrations (Klue, Crayon, Bombora) — Web research with search and fetch is enough for a first version. MCP integrations come when data freshness needs justify the dependency.
- Native historical tracking — Time-stamped artifacts in `.competitive-intelligence/` work with version control. A tracking layer adds infrastructure before the usage pattern is proven.
- Semantic search for intelligence triangulation — Keyword triangulation in triangulation.py is enough at the current data size. Semantic search is the upgrade path when the rate of missed matches goes above a measured limit.
- Predictive disruption models — The 4-factor technology disruption score is an assessment framework that a person can read. Statistical prediction models need training data that does not exist yet.
- Automated competitive monitoring or scheduled runs — A person starts the OBSERVE loop. A scheduler is a later version, after the usage of the monitoring trigger is proven.

**Verdict: the architecture is as simple as it must be for 1.0.0 and 1.1.0.**

---

## Evolution Roadmap

| Trigger | Evolution |
|---------|-----------|
| More than 5 competitive analyses show stale intelligence after 2 weeks | Add web monitoring; run intelligence-gatherer again on the difference |
| Claude Code lets an agent run several agents in parallel at the lens layers | Run the lenses of one layer in parallel again |
| `depth: comprehensive` is the normal choice | Add adaptive competitor tiering in ecosystem-mapper: skip standard analysis for the Low-threat tier |
| The loss/churn override fires in more than 30% of runs | Review the loss-churn confidence threshold; change the `retention_risk = HIGH` criteria |
| MCP integrations for Klue or Crayon are available | Add the MCP tool calls in intelligence-gatherer; the search and fetch tools stay as the fallback |
| The rate of missed matches in triangulation is above 15% | Add semantic search next to keyword triangulation in triangulation.py |
| The `monitoring` trigger is in routine use with a prior session_id | Build an incremental update mode: session.json tracks the prior run; intelligence-gatherer compares with the prior intelligence-data.json |

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-01-22 | Draft | First design (docs/DESIGN.md): 6-phase workflow, 6-lens framework, Python and LLM hybrid |
| 2026-02-27 | Accepted | 1.0.0 architecture formalized; 1.1.0 file-based inter-agent protocol added |
| 2026-02-28 | Accepted | ADR created and committed |
| 2026-06-11 | Accepted | 1.3.0 (F74) — Decision 1 amended: synthesizer sonnet → opus (role-tier rule for the synthesis role); all other agents remain sonnet |
| 2026-06-12 | Accepted | 1.5.0 (F67) — Decision 6 trigger taxonomy aligned to canonical prose values + optional analysis_mode (ADR-003) |
| 2026-11-05 | Accepted | 1.7.0 (port) — Decision 1: the coordinator is the skill `competitive-intelligence`; Decision 2: the lens executor reads each lens skill; Decision 6: only skills ask questions, and agents take answers from dispatch fields; Decision 8: script calls with `uv run` |
