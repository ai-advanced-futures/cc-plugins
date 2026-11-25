---
name: value-ip:guard
description: Proactive guardian mode — challenge value assumptions BEFORE new work is marked complete
agent: debate-coordinator
allowed-tools: Task(*), Read(*), Write(*), Glob(*), Grep(*), AskUserQuestion(*)
---

# /value-ip:guard

## Purpose

Proactive guardian mode. Invoke BEFORE marking any new work complete to ensure what you're building has genuine differentiated value.

Best used:
- Before completing a feature implementation
- Before finalizing a PRD
- Before shipping a competitive response
- Before closing an M&A deal

## Step 0: Load Config and Initialize Pipeline State

**Read config** — use the Read tool on `${CLAUDE_PLUGIN_ROOT}/config/pipeline-defaults.json`. If absent or unreadable, default to `auto_mode: false`.

Store `auto_mode` and `auto_answers` in working memory.

**Initialize pipeline state** — use the Write tool to write `.value-ip-state.json` in the current working directory:

```json
{
  "version": "1.1.0",
  "phase": "GUARD",
  "round": 0,
  "max_rounds": 1,
  "artifact_path": null,
  "artifact_type": null,
  "framework_results": {
    "helmer": "pending",
    "blue_ocean": "pending",
    "christensen": "pending",
    "moore": "pending"
  },
  "unresolved_tensions": [],
  "auto_mode": false,
  "started_at": "<current UTC ISO timestamp>",
  "updated_at": null
}
```

Replace `false` in `"auto_mode"` with the actual config value. Replace `"<current UTC ISO timestamp>"` with the actual current time.

**If `auto_mode: true`:** Skip the AskUserQuestion in Step 1 and infer what is being built from the current conversation context.

## Step 1: Understand What's Being Built

**If `auto_mode: false`:**

Ask:

```json
{
  "questions": [
    {
      "question": "What are you about to complete? Describe the value you believe you're creating.",
      "header": "Guardian Check",
      "multiSelect": false,
      "options": [
        {"label": "Feature or component", "description": "A specific feature being implemented"},
        {"label": "Plan or PRD", "description": "A strategic document about to be finalized"},
        {"label": "Competitive response", "description": "A response to a competitive threat"},
        {"label": "M&A target assessment", "description": "Due diligence on a potential acquisition"}
      ]
    }
  ]
}
```

**If `auto_mode: true`:**

Skip AskUserQuestion. Infer what is being built from the current conversation context and proceed to Step 2.

## Step 2: Run Guardian Analysis

Quick scan through all 4 frameworks. Focus on: "Would THIS specific work be considered genuine IP or differentiation?"

**Guard mode context:** Guard mode creates no `debate-context/` files. Run each framework agent for Steps 1-3 of their SKILL only (no file writes). Each agent returns their framework scan findings inline as text. Collect all four inline responses before generating the verdict.

Dispatch each framework agent with the work description and the instruction to return findings inline (not written to files):
1. **helmer-agent** → return abbreviated Helmer scan inline
2. **blue-ocean-agent** → return abbreviated Blue Ocean scan inline
3. **christensen-agent** → return abbreviated Christensen scan inline
4. **moore-agent** → return abbreviated Moore scan inline

Pass all four inline findings to the synthesizer/coordinator for the guardian verdict. The coordinator and the synthesizer work from the in-context findings alone, and name no `debate-context/` file path.

## Step 3: Generate Guardian Verdict

Three possible outcomes:

**GREEN — Proceed:**
> "Analysis confirms this work contains genuine value differentiation. IP claims: [N]. Proceed."

**YELLOW — Conditional:**
> "This work has some differentiation but [specific weakness]. Consider addressing [challenge] before marking complete."

**RED — Stop:**
> "This work does not contain genuine value differentiation. It is [commodity/sustaining/context]. Recommend [specific change] before proceeding."

## Step 4: If RED or YELLOW

Generate specific recommendations for what would need to change for this work to pass the value test.
The team must respond to these before marking the work complete.

**State reset:** Use the Write tool to reset `.value-ip-state.json` to `"phase": "INIT"` after recommendations are presented:

```json
{
  "version": "1.1.0",
  "phase": "INIT",
  "round": 0,
  "max_rounds": 4,
  "artifact_path": null,
  "artifact_type": null,
  "framework_results": {
    "helmer": "pending",
    "blue_ocean": "pending",
    "christensen": "pending",
    "moore": "pending"
  },
  "unresolved_tensions": [],
  "auto_mode": false,
  "started_at": null,
  "updated_at": null
}
```
