# ADR-010: Cost-Class Design-Review Gate

**Status:** Accepted
**Date:** 2026-06-01
**Plugin:** architecture v2.10.0 (before the port to architecture-assess)

## Context

The agentic pricing program defined telemetry for archetype-baseline cost signals. This release extends the plugin to produce a new federation schema (`cost-class-classification.schema.json`) that classifies any AI-stack design by cost band and 4-layer stack position, yielding an advisory guardrail verdict for application-layer designs with high/critical cost exposure.

The decision space had several non-obvious choices:

- **Math/judgment boundary**: cost-band classification is purely numeric; layer classification requires reading system architecture narrative — a judgment call.
- **Model tier**: the layer classification is rubric-bounded and single-step; the pricing program's haiku vs. sonnet vs. opus progression needed an explicit decision.
- **Federation coupling discipline**: the plugin already observes pricing's output schemas. Adding a new federation link required explicitly deciding whether to import `pricing.lib` code or to reimplement from schema spec only.
- **Status file topology**: the specialist needs a status file of its own, with a distinct path, that the skill reads.
- **Verdict semantics**: the gate posture is advisory (architecture is a review tool, not a CI hard-block enforcer). The 16-cell (4 layers × 4 bands) matrix needed an explicit rule for which cells fire `requires_guardrail = true`.

## Decision

Eight decisions are recorded for this release:

### Decision 1 — New federation schema `cost-class-classification.schema.json`

A new JSON Schema file `schemas/cost-class-classification.schema.json` is the canonical wire format for the cost-class output of this plugin. This plugin is the **producer**; pricing and product-finance are recorded as **consumers**. Neither consumer is wired in this release.

### Decision 2 — Standalone specialist + 3-module producer pipeline

The cost-class gate is implemented as a new isolated specialist:

- `cost_class_input_loader.py` — validates the consumed `cost-amplifier-readout` input (`schemas/cost-amplifier-readout.schema.json`) + positivity guard
- `cost_class_band.py` — deterministic Python band classifier (see Decision 3/4)
- `cost_class_emitter.py` — CLI that drives the pipeline end-to-end and writes the federation output + status file

(All three modules live in `scripts/`, mirroring the aiml producer layout.) The specialist agent (`cost-class-gate-agent.md`) and skill (`/architecture-assess:cost-class-review`) are isolated from the existing 14 assessor agents and the `design` and `review` skills. No existing agent file or skill file is modified.

### Decision 3 — Hybrid math/judgment split (pricing ADR-001 discipline)

Following the pricing plugin's ADR-001 principle ("math to Python, judgment to agent"):

- **Python (deterministic):** `cost_class_band.classify_cost_class(composite_p75, composite_p95)` returns one of four band values based on fixed numeric thresholds. The function is pure and has no LLM call.
- **Agent (judgment):** the 4-layer AI-stack classification (`foundation_model`, `infrastructure_orchestration`, `application`, `vertical_labor_anchor`) is the agent's rubric-bounded judgment from reading the product's business model + customer base. This cannot be reduced to a numeric formula.

### Decision 4 — Cost-class band thresholds, tail escalator, and boundary semantics

Constants defined in `cost_class_band.py`:

| Constant | Value | Meaning |
|---|---|---|
| `_BOUNDED_UPPER` | `3.0` | Upper bound (inclusive) for `class_1_bounded` |
| `_MODERATE_UPPER` | `8.0` | Upper bound (inclusive) for `class_2_moderate` |
| `_HIGH_UPPER` | `20.0` | Upper bound (inclusive) for `class_3_high` |
| `_P95_TAIL_ESCALATOR` | `50.0` | `composite_p95 ≥ 50.0` → always `class_4_critical`, regardless of p75 |

Classification logic:

- `class_1_bounded`: `composite_p75 ≤ 3.0`
- `class_2_moderate`: `3.0 < composite_p75 ≤ 8.0`
- `class_3_high`: `8.0 < composite_p75 ≤ 20.0`
- `class_4_critical`: `composite_p75 > 20.0` OR `composite_p95 ≥ 50.0` (tail escalator)

Band boundaries are **upper-inclusive for the lower band** — a value of exactly `3.0` is `class_1_bounded`, not `class_2_moderate`.

### Decision 5 — Advisory-not-blocking verdict semantics

`requires_guardrail` is `true` in exactly **2 of the 16 (layer × band) cells**:

- `ai_stack_layer == "application"` AND `cost_class ∈ {class_3_high, class_4_critical}`

All other 14 cells return `requires_guardrail = false`. The `vertical_labor_anchor` signal never triggers a guardrail at any band.

The verdict is **advisory**: the architecture plugin is a design-review tool, not a CI hard-block enforcer. A `requires_guardrail = true` output surfaces the finding for a human or downstream gating agent to act on; it does not itself fail a build or block a merge.

### Decision 6 — Model tier: sonnet

The agent uses the sonnet tier for the layer classification step. Rationale:

- The classification is rubric-bounded (4 choices with explicit definitions), single-step, and advisory — this is the same judgment profile as the pricing plugin's `agentic-pricing-strategist`, which runs on Sonnet.
- NOT the haiku tier: the aiml producer agents use Haiku because they do **zero judgment** (they are schema-driven emitters). This agent does make a judgment call.
- NOT the opus tier: Opus's edge is largest on open-ended synthesis and deep reasoning tasks; a rubric-bounded 4-way classification where the rubric is in-prompt does not justify Opus cost.

**Named trap encoded in agent prompt:** the framework's hybrid-layer trap — *"a portco that is application-layer in business model but vertical-labor-anchor in customer base inherits the vertical-anchor protection automatically"* — is named verbatim in the agent prompt. The tie-break rule: when business model and customer base diverge, classify by the protection the customer base confers (e.g., a legal-AI product priced against associate cost is `vertical_labor_anchor`, not `application`).

**Escape hatch:** if a future eval or trajectory pass shows systematic layer-misclassification, revisit to Opus then (one-line `model:` frontmatter change). The decision is empirically revisable, not speculative.

### Decision 7 — Reimplementation only — no `pricing.lib` import

This plugin does **not** import `pricing.lib` code. Federation is **schema-coupled only**: the plugin reads and validates data shapes defined in the federation schemas in `schemas/`; it does not import Python modules from the pricing plugin.

This is enforced by an AST-walk anti-regression guard: `tests/unit/test_no_pricing_lib_imports.py` walks every `.py` file under `scripts/` and fails the suite if any `import pricing` or `from pricing` statement is found.

### Decision 8 — Distinct status file `cost-class-handoff.json`

The cost-class specialist writes its own status file to:

```
.architecture/cost-class-handoff.json
```

Shape (`status` is the discriminator):
- complete: `{"status": "complete", "classification_path": "<path to the §7.14 output>", "produced_at": "<iso8601>"}`
- blocked:  `{"status": "blocked", "reason": "<which input was missing/invalid>", "produced_at": "<iso8601>"}`

- The **emitter** (`cost_class_emitter.py`) writes the `complete` form after successfully producing the §7.14 federation output (same `.architecture/` directory).
- The **agent** (`cost-class-gate-agent.md`) writes the `blocked` form if the dispatch context lacks a valid `ai_stack_layer` / `ai_stack_layer_basis`, then still ends with its `DONE:` line.
- The **skill** reads the status file and shows the result to the person.

Consumers (pricing, product-finance) are **not wired** in this release. Their read paths for `cost-class-handoff.json` are reserved for later work.

## Consequences

**Positive:**
- The advisory gate is **discoverable but non-enforcing**: downstream consumers can choose to read `requires_guardrail` and escalate, or ignore it — the architecture plugin does not dictate enforcement posture.
- The **Sonnet→Opus escape hatch** is a one-line change (`model: sonnet` → `model: opus` in the agent frontmatter), gated on empirical misclassification evidence rather than speculative preference.
- The **CI vanilla-pip lane** is satisfied: `requirements-dev.txt` declares `jsonschema>=4.17.0` so the CI `pip install -r requirements-dev.txt` path can run the schema-validation tests without a full uv workspace.

**Negative:**
- The 14-agent assessor surface is larger by one specialist but still isolated — new sessions must enumerate agents correctly (ADR-009 bounded-context discipline applies).
- The scripts run from `${CLAUDE_PLUGIN_ROOT}/scripts/`, but the status files go to `.architecture/` of the project of the user. A consumer must read the project folder, not the plugin folder.

## References

- pricing plugin ADR-001 — math/judgment split principle (Python for math, agent for judgment).
- aiml plugin ADR-004 — Haiku producer agents (zero-judgment emitter pattern).
- This plugin ADR-009 — AP#7c bounded-context session isolation.
- `scripts/cost_class_band.py` — numeric classifier constants and `classify_cost_class()`.
- `scripts/cost_class_emitter.py` — CLI pipeline driver.
- `schemas/cost-class-classification.schema.json` — federation wire format.
- `schemas/cost-amplifier-readout.schema.json` — the input that the aiml plugin writes.
- `tests/unit/test_no_pricing_lib_imports.py` — AST-walk anti-regression guard.
