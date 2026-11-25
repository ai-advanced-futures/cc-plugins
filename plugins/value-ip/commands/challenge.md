---
name: value-ip:challenge
description: Quick devil's advocate mode — challenge value claims without full scorecard
agent: debate-coordinator
allowed-tools: Task(*), Read(*), Write(*), Glob(*), Grep(*), AskUserQuestion(*)
---

# /value-ip:challenge

## Purpose

Fast devil's advocate mode. Skip the full scorecard. Go straight to the debate coordinator to challenge any value claims in an artifact or plan.

Ideal for quick gut-checks before writing more code or continuing a design.

## Step 0: Load Config and Initialize Pipeline State

**Read config** — use the Read tool on `${CLAUDE_PLUGIN_ROOT}/config/pipeline-defaults.json`. If absent or unreadable, default to `auto_mode: false`.

Store `auto_mode` and `auto_answers` in working memory.

**Initialize pipeline state** — use the Write tool to write `.value-ip-state.json` in the current working directory:

```json
{
  "version": "1.1.0",
  "phase": "CHALLENGE",
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

**If `auto_mode: true` and artifact is already in the conversation context:** proceed directly to Step 2, skipping any artifact identification in Step 1.

## Step 1: Get the Artifact

Ask for the artifact or plan to challenge if not in context.

## Step 2: Quick Framework Scan

Run abbreviated (1-pass) versions of all four framework lenses. No full debate — just identify the weakest claims immediately.

**Challenge mode context:** Write no analysis to `debate-context/` files, because challenge mode creates none. Each framework agent runs Steps 1-3 of their SKILL only (no file writes) and returns their abbreviated findings inline as text in their response. The orchestrating agent collects all four agents' inline findings before proceeding to Step 3.

Dispatch each framework agent with the artifact and the instruction to return findings inline (not written to files):
1. **helmer-agent** → return abbreviated Helmer findings inline
2. **blue-ocean-agent** → return abbreviated Blue Ocean findings inline
3. **christensen-agent** → return abbreviated Christensen findings inline
4. **moore-agent** → return abbreviated Moore findings inline

Collect all four inline responses before dispatching the coordinator.

## Step 3: Generate Challenges

**DISPATCH debate-coordinator** to generate the top 3-5 hardest challenges against the artifact's value claims.

**Challenge mode context:** The `debate-context/` files do not exist in challenge mode, so the debate-coordinator reads none of them. Pass all abbreviated framework findings as inline text in the coordinator dispatch. The coordinator works from the in-context findings alone.

## Step 4: Present Challenges

Show challenges to the user in devil's advocate format:

```markdown
## DEVIL'S ADVOCATE — Quick Challenge Mode

### Challenge 1 — Helmer Lens
"[challenge]"
What would need to be true for this to be valid: [condition]

### Challenge 2 — Blue Ocean Lens
"[challenge]"
...
```

No scorecard is produced. This is a conversation, not a report.

**State reset:** Use the Write tool to reset `.value-ip-state.json` to `"phase": "INIT"` after the challenge is presented:

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
