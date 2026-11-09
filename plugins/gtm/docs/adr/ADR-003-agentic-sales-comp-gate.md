# ADR-003: Agentic sales-comp gate

**Status:** Accepted
**Date:** 2026-06-01
**Updated:** 2026-11-05 (port to this marketplace)
**Updated:** 2026-11-07 (STORY-146: the gate agent has no shell tool; the skill or the caller runs the emitter)
**Plugin:** gtm
**Version introduced:** 1.4.0

---

## Context

gtm makes and reads two handoff files:

- **The sales-comp precondition gate.** gtm writes a gate file. It says if the five preconditions are met before a variable-pay plan can start. The schema is `schemas/sales-comp-precondition-gate.schema.json`.
- **The p15 trigger event.** The `aiml` plugin writes this file. gtm reads it and sends stakeholder messages with six templates. The schema is `schemas/p15-trigger-event.schema.json`.

This ADR records eight decisions about the design.

---

## Decisions

### Decision 1: Three modules for the producer (loader, classifier, emitter)

**Context:** The gate must be exact. The same inputs must give the same file each time. No agent judgment is allowed in this path.

**Decision:** Split the producer into three library modules:

- `sales_comp_gate_input_loader.py` checks and normalizes the inputs.
- `sales_comp_gate.py` has `classify_cliff`. It applies the exact precondition and risk rules.
- `sales_comp_gate_emitter.py` writes the file to the schema.

The agent sits above the modules. It gives judgment only for the story of the five preconditions.

**Consequence:** Each module has its own unit tests. The agent can change and the gate rules stay the same. The tests of the rules need no agent mock.

### Decision 2: Math in code, judgment in the agent

**Context:** The exact gate logic must be in Python. The readable assessment and the word choice for messages need judgment.

**Decision:** The code holds all cliff rules: the threshold comparisons, the `re_pause` precedence, and the check for extra properties. The agent writes the story of the five preconditions and picks the template for an audience. The gate file carries the machine decision. The agent adds the story.

**Consequence:** The exact path is fully tested with no model call. The judgment layer can change without a change to the schema.

### Decision 3: A word list for operator and customer language, and a lint

**Context:** The message templates must use operator words (what the system does). They must not use customer words (what the product gives). This is a different rule from the superlative rule of `truth_tier_validator`.

**Decision:** Add `definitions/comms-vocabulary.json`. It lists the operator words that are allowed and the customer words that are not. Add the function `comms_vocabulary.check_customer_vocabulary(text)` as a lint. Keep `truth_tier_validator` for superlatives. The two checks find different faults.

**Consequence:** `test_comms_router.py` runs the lint on all six templates. A new template with a customer word fails the test.

### Decision 4: The sonnet model for the gate agent

**Context:** The agent applies a short rubric of five yes-or-no checks to structured inputs. This is bounded judgment.

**Decision:** The gate agent uses `model: sonnet`. The opus model is not needed for a task with exact rules below it.

**Consequence:** The cost stays low. If the rubric ever needs open synthesis, a new decision can raise the model.

### Decision 5: No change to the two schemas

**Context:** The two schemas and the precondition matrix were already agreed before gtm made and read the files.

**Decision:** gtm implements its side of those files and does not change the schemas. The plugin holds a copy of each schema in `schemas/`. The `$id` of each copy is its file name.

**Consequence:** A schema change comes from the owner of the schema. The copy in `schemas/` then changes with it.

### Decision 6: `re_pause` needs prior-state inputs and is never written into the gate file

**Context:** The gate schema does not allow extra properties. The `re_pause` flag needs two inputs that are not part of the schema: `prior_recommendation` and `re_pause_trigger_fired`.

**Decision:** `classify_cliff` computes `re_pause`. It fires only when `prior_recommendation == "proceed"` and `re_pause_trigger_fired == true`. The loader checks and carries these two inputs. They are in the `SalesCompGateInput` dataclass. They are never written into the gate file. The emitted file holds only the fields of the schema. `test_sales_comp_gate.py` tests all four combinations of the two inputs.

**Consequence:** No extra field can enter the file. Each combination has a test.

### Decision 7: How a run is started and how it hands off

**Context:** The gate is a skill, `sales-comp-gate-review`. The skill reads the gate agent file and follows it in the main conversation, so it can ask the person the five preconditions. A dispatched run cannot ask.

**Decision:** The gate agent has the tools `Read, Write` and no shell tool. In the main conversation, the skill asks the five preconditions, writes `.gtm/sales-comp-gate-input.json`, and runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/sales_comp_gate_emitter.py`, which writes `.gtm/sales-comp-precondition-gate.json` and the handoff file `.gtm/sales-comp-gate-handoff.json`. The skill approves only that one script in its `allowed-tools`. In a dispatched run, the agent takes the preconditions from the dispatch fields, writes `.gtm/sales-comp-gate-input.json`, and ends with the line `INPUT: .gtm/sales-comp-gate-input.json`. The caller then runs the emitter. The `completed_skills` value of the emitter is `gtm:sales-comp-gate-review`.

**Consequence:** The handoff path is fixed and a program can read it. The gate produces a recommendation and has no side effect that is hard to undo.

### Decision 8: The comp model is a library, not part of the producer path. The loader is stricter than the schema.

**Context:** `sales_comp_model.py` computes a reference calculation with four parts: Land, Expand, Quality-Bonus, and Churn-Clawback. If these pay amounts went into the gate file, the amounts could leave the plugin in a public file.

**Decision:** The comp model is a library. No agent calls it, because the script has no command line. It is not in the path from loader to classifier to emitter. The gate file carries precondition signals and no pay amounts. The loader also rejects `at_risk_pct < 0` at load time, although the schema does not check this bound.

**Consequence:** No pay amount is in the gate file by design. A test checks that a negative `at_risk_pct` raises `ValueError` before the classifier runs.
