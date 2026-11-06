# ADR-001: AIML Plugin Architecture

**Status:** Accepted
**Date:** 2026-04-08 (rewritten for the port, 2026-11-05)
**Authors:** Luis F. Amadeo

---

## Context

Software teams often add AI or ML to a product but have no data scientist. They need help with the full path: the choice of approach, the design, the implementation, the training, the evaluation, and the production work. They must not need deep ML knowledge.

The plugin runs in two ways:

1. **Alone.** The engineer runs `/aiml:decide` and the other skills directly.
2. **With superpowers (optional).** `superpowers:executing-plans` runs the tasks of `docs/aiml/plan.md`.

## Decision

### An 8-skill pipeline, and 4 helper skills

`/aiml:decide` → `/aiml:design` → `/aiml:plan` → `/aiml:simulate` → `/aiml:scaffold` → `/aiml:tune` and `/aiml:evaluate` → `/aiml:ops`

Each skill works alone. The skill `/aiml:orchestrate` is a convenience: it reads `.aiml/handoff.json` and runs the next skill. Three producer skills (`cost-amplifier-readout`, `p15-trigger-detection`, `archetype-baseline-telemetry`) turn a JSON file into a result file. They are not part of the pipeline order.

### An 11-agent roster with model tiers

- **opus** (3 agents): `decision-agent`, `design-agent`, `simulator-agent`. They reason under doubt, make choices that add up, or look for failures.
- **sonnet** (5 agents): `plan-agent`, `scaffold-agent`, `tune-agent`, `evaluate-agent`, `ops-agent`. They do structured work.
- **haiku** (3 agents): the three producer agents. They run one script.

The agent `orchestrator` of earlier versions does not exist. The skill `orchestrate` runs in the main conversation, because only the main conversation can ask the person a question (see ADR-002).

### The plugin does not know its caller

The state is in `.aiml/handoff.json`. Any tool can read it. A skill never depends on who runs it.

### Math in scripts, judgment in agents

Python scripts do the math and the checks, with no model call:

- `metric_calculator.py`: precision, recall, F1, ROC-AUC
- `data_validator.py`: split ratios, class balance, minimum samples, leakage
- `cost_estimator.py`: training and inference cost
- `hyperparameter_validator.py`: checks of the search space

Agents run these scripts with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`, in place of their own math. A script that has a command line has a PEP 723 block, so `uv` installs its packages.

### Fixed artifact paths

Each artifact has a known path in the project of the user. `.aiml/handoff.json` holds the state of the pipeline.

## Consequences

**Positive:**
- An engineer with no ML knowledge can follow the full path.
- The scripts have unit tests that do not start an agent.
- Any tool can read the artifacts.

**Negative:**
- Three opus agents cost more than an all-sonnet plan.
- A full run from `decide` to `ops` needs many agent runs.
- The user needs `uv`.

## Alternatives considered

1. **One agent for everything.** Rejected: too much context in one run, and no way to start at a given step.
2. **All sonnet.** Rejected: the choice of approach, the design and the simulation gain much from opus.
3. **No scripts.** Rejected: math in a prompt is fragile and cannot be tested.
