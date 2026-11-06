# ADR-002: Agent Patterns and Architectural Decisions

**Status:** Accepted
**Date:** 2026-04-08 (rewritten for the port, 2026-11-05)
**Authors:** Luis F. Amadeo

---

## Context

This ADR records how the plugin shows its features to the user, how an agent gets parallel work done, who asks the person questions, and how the model cost is shared between the agents. ADR-001 records the overall design.

---

## Decision 1: Skills only (no `commands/` folder)

### Decision

The plugin has no `commands/` folder. Each entry point (`/aiml:decide`, `/aiml:design`, and so on) is a skill.

### Rationale

Each feature starts an agent that reads files, runs scripts, starts sub-tasks and writes files. A skill can state all of this. A command adds one more layer between the command and the agent, and gives no gain.

### Consequences

- Each feature is started as `/aiml:<skill>`.
- There is one place for the full text of a feature.

---

## Decision 2: Sub-tasks of `design-agent` and `simulator-agent` run in parallel

### Context

`design-agent` and `simulator-agent` each have three independent analysis tasks. The tasks do not depend on each other.

### Decision

Both agents have the `Agent` tool. Each starts three general-purpose sub-agents in one message, and merges the results. A sub-agent has no named agent file. It gets a prompt with the full context from its parent. A sub-agent cannot start another agent, so the depth is two.

### Rationale

The wall-clock time is that of the slowest sub-task, not the sum of the three. A sub-task is not used by anyone else, so a named file gives no gain.

### Consequences

- The parent agent must put enough context in each sub-task prompt.
- When the `Agent` tool is not available, the agent does the three tasks in order. The result is the same and the run is slower.

---

## Decision 3: Only a skill asks the person

### Context

A sub-agent that the `Agent` tool starts cannot ask the person a question. Its `AskUserQuestion` call does not reach the person. Only the main conversation can ask.

### Decision

- Only a skill asks questions, with `AskUserQuestion`. A skill that needs answers asks them before it starts its agent, and gives the answers to the agent as fields of the prompt.
- No agent has `AskUserQuestion` in `tools:`.
- When an agent needs more information, it writes the questions to `.aiml/open-questions.md` and ends its reply with `NEEDS-INPUT: <agent>`. The skill reads the file, asks the person, and starts the agent again with the answers.
- A skill starts its agent with the `Agent` tool and the name `aiml:<agent>`. The skill has no `agent:` key, because that key works only with `context: fork`, and a forked skill cannot ask the person.
- The skill `orchestrate` runs in the main conversation. It runs the next skill with the `Skill` tool.
- `scaffold-agent`, `tune-agent`, `simulate` and the three producers need no input in the normal case. `tune` and `evaluate` ask only when they find no log, or cannot tell the mode.

### Rationale

The rule follows what Claude Code allows. It also keeps the agents free of dialogue, so that they are easy to test and to read.

### Consequences

- An agent always ends with `DONE: <agent>` or `NEEDS-INPUT: <agent>`. The three producer agents end with `DONE: aiml`. A skill reads the last line.
- There is no "automated mode". The key `automated` is not in `.aiml/handoff.json`, and no agent has a block that tests for a run without a person.
- A test (`test_prompt_rules.py`) fails when an agent gets `AskUserQuestion` or `Task` in `tools:`.

### Alternatives considered

- **Agents that ask.** Rejected: the question does not reach the person.
- **Two sets of agent files, for runs with and without a person.** Rejected: it doubles the files, and the two sets drift apart.

---

## Decision 4: Opus for 3 agents, sonnet for 5, haiku for 3

### Context

The agents have different reasoning needs. Opus costs about 5 times more per token than sonnet.

### Decision

**opus**:
- `decision-agent`: the choice of LLM, ML or hybrid fixes all later work.
- `design-agent`: architecture choices add up. A wrong choice means rework in each later step.
- `simulator-agent`: it must find the failures of a plan that the engineer did not see.

**sonnet**:
- `plan-agent`, `scaffold-agent`, `tune-agent`, `evaluate-agent`, `ops-agent`: the input is well defined and the output has a fixed form.

**haiku**:
- The three producer agents. They run one script and report the result.

Each agent has `model:` with the alias `opus`, `sonnet` or `haiku`.

### Rationale

The opus agents have unclear inputs, or choices with large effects. The sonnet agents have clear inputs from earlier files. The haiku agents have no judgment to make.

### Consequences

- The steps `decide`, `design` and `simulate` cost more than the others.
- If opus is not available, `decision-agent` has the highest priority, then `simulator-agent`, then `design-agent`.

### Alternatives considered

- **All sonnet.** Rejected: the choice of approach and the search for failures are worse on sonnet.
- **All opus.** Rejected: about 5 times the cost for the structured steps, with no gain.
