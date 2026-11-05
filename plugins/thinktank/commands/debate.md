---
description: Conduct structured multi-agent analysis to determine optimal implementation approach
agent: debate-coordinator
allowed-tools: Task(*), Write(*), Read(*), Edit(*), AskUserQuestion(*), WebFetch(*), Grep(*), Glob(*)
---

# Think Tank Debate

The result is `RECOMMENDATION.md`: one approach that held up through research
and at least 3 rounds of Socratic debate between strategists with different
lenses. Each step below runs as a dispatched agent, because a debate that one
model simulates alone produces no real disagreement.

## Setup

### Step 1: Confirm the topic

If the conversation already holds a clear problem or topic, confirm it with
the user. If not, ask for it:

```json
{
  "questions": [
    {
      "question": "What topic or problem should we analyze in this Think Tank debate?",
      "header": "Debate Topic",
      "multiSelect": false,
      "options": [
        {"label": "Enter topic", "description": "Provide the problem, feature, or decision to analyze"}
      ]
    }
  ]
}
```

Store the confirmed topic as `DEBATE_TOPIC`.

### Step 2: Select the active roles

Ask the user which roles to activate:

```json
{
  "questions": [
    {
      "question": "Which strategist perspectives do you want active in this debate?",
      "header": "Active Roles",
      "multiSelect": true,
      "options": [
        {"label": "Pragmatist", "description": "Fastest path to working solution with minimal complexity"},
        {"label": "Innovation-Focused", "description": "Elegant design, optimal outcomes, long-term extensibility"},
        {"label": "Research-Driven", "description": "Empirical evidence and proven best practices"},
        {"label": "Reuse-Focused", "description": "Leverage existing solutions, libraries, and community tools"}
      ]
    }
  ]
}
```

Store the selected roles as `ACTIVE_ROLES`. In every file name below,
`[ROLE_NAME]` is the role name in lowercase, with hyphens for spaces, and with
every other character that is not a letter, a digit, or a hyphen removed:
`Innovation-Focused` becomes `innovation-focused`. Give this exact name to each
agent you dispatch for the role.

### Step 3: Custom roles

Ask whether the user wants custom roles:

```json
{
  "questions": [
    {
      "question": "Do you want to add custom strategist roles?",
      "header": "Custom Roles",
      "multiSelect": false,
      "options": [
        {"label": "Yes, add custom roles", "description": "Define additional perspectives for this debate"},
        {"label": "No, use selected roles", "description": "Proceed with standard roles"}
      ]
    }
  ]
}
```

If the user selects "Yes", ask:

```json
{
  "questions": [
    {
      "question": "Define each custom role. Format: [Role Name]: [Description of strategic lens]",
      "header": "Custom Role Definitions",
      "multiSelect": false,
      "options": [
        {"label": "Enter custom roles", "description": "One role per line (e.g., 'Security-First: Focus on security constraints')"}
      ]
    }
  ]
}
```

Append the custom roles to `ACTIVE_ROLES`. A custom role goes through every
phase that a standard role goes through.

When `ACTIVE_ROLES` holds fewer than 2 roles, ask Step 2 again, because one
strategist has no other view to debate.

### Step 4: Show the setup

Show this summary before Phase 1:

```markdown
# Debate Setup Confirmed

**Topic:** [DEBATE_TOPIC]

**Active Strategist Roles:**
- [Role 1]
- [Role 2]
...

Starting debate with [N] strategist perspectives.
```

## Phase 1: Research questions

Dispatch one `thinktank:implementation-strategist` agent for each role in
`ACTIVE_ROLES`, with the topic and its lens. Each one writes the research
questions its strategy depends on, and why each one matters, to
`research-needs/[ROLE_NAME]-questions.md`.

## Phase 2: Isolated research

For each role, dispatch one `thinktank:researcher` agent with only that role's
questions. It writes `research-results/[ROLE_NAME]-research.md`.

Keep the research of each role apart until Phase 4. A strategist that sees the
research of another role drifts toward that role's answer, and the debate
loses its distinct positions.

## Phase 3: Proposals

Dispatch each strategist again with its own questions, its own research, and
its lens, and no other role's files. Each one writes a complete strategy to
`proposals/[ROLE_NAME]-proposal.md`: the approach, the argument for it, the
trade-offs, and the research findings that support it.

## Phase 4: Socratic deliberation

1. Dispatch `thinktank:debate-coordinator` with all proposals and the topic.
   It writes the tensions, the unexamined assumptions, and the trade-offs to
   `deliberation/debate-plan.md`.
2. Run at least 3 rounds. In each round, dispatch the coordinator with the
   proposals, `deliberation/debate-plan.md`, and every earlier round file, so
   that its questions follow up on the answers. It writes the questions to
   `deliberation/round-N-questions.md`. Then dispatch each strategist with all
   proposals, all earlier responses, and its own questions. Collect the
   answers in `deliberation/round-N-responses.md`. A strategist answers the
   challenge, and does not restate its proposal.
3. Dispatch the coordinator one more time, with the proposals and every
   `deliberation/` file. It writes which arguments held up,
   which concerns stay open, and which approach is strongest to
   `deliberation/coordinator-analysis.md`.

The coordinator asks questions and does not argue for an approach, because a
coordinator with a side turns the debate into a vote.

## Phase 5: Recommendation

From the coordinator analysis and the deliberation files, write
`RECOMMENDATION.md` with these sections:

- **Recommended Approach**: [Clear, concise statement]
- **Why This Approach**: [3-4 compelling reasons based on deliberation]
- **Key Trade-offs Accepted**: [What we're giving up and why it's acceptable]
- **Approaches Considered**: [Brief summary of alternatives from active roles]
- **Critical Success Factors**: [2-3 things that must go right]
- **Research Insights Applied**: [How key findings shaped the decision]
- **Debate Insights**: [Key turning points or revelations from the deliberation]

Keep the document short: state the decision and the reasons for it. Each
reason points to a finding or a debate round that supports it.
