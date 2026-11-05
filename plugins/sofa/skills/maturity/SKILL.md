---
name: maturity
description: 'Assess how mature a sofa factory is in a repository: the three proofs per story, how much the team decides alone, the veracity of the brains, and the quality of the prompts and instructions of the repository. Offers to prompt-fit the prompts. Use when the user says "sofa maturity", "how mature is the factory", "assess the team".'
metadata:
  internal: true
---

# maturity — how far the factory is

Read the data, score it, write 1 report. Change no other file without the user's agreement.

## Step 1 — Collect

- From the state store (`<skill folder>/scripts/sofa-state report --json`, and `metrics --story <id> --json` for each story of the roadmap in `done` or `released`).
- From the roadmap: the story and feature metrics fields, or `docs/adlc/metrics/*.json`.
- From the brains: for each brain of `.claude/knowledge.json`, the number of pages, the mean `veracity` (50 when absent), and the share of pages not validated or changed in 180 days.
- From the repository: each prompt file — `CLAUDE.md` files at each level, `AGENTS.md`, `.claude/rules/*.md`, `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`, `docs/adlc/roles/*.md`.

## Step 2 — Score

Each dimension 0..100, with the numbers behind it:

| Dimension | How |
|---|---|
| Proof of concept | share of stories with an unknown that have a proof in a brain |
| Proof of process | share of merged PRs with a complete Proofs block |
| Proof of product | share of stories `released` with a verifier line |
| Proof of intent | mean confirmed intent score of released features |
| Autonomy | autonomous decisions / (autonomous decisions + hitl questions), and its trend per week |
| Flow | median cycle hours (picked up → released), median trips, defects per story |
| Knowledge | mean effective validity of the brains (veracity, lowered by age) |
| Prompts | share of prompt files that are short, specific, and have no contradictions (step 3) |

## Step 3 — Prompts

Review the prompt files with the `prompt:reviewing-prompts` skill, in subagents (1 subagent per 5 files, `sonnet`). Each returns a fit score and the top 3 problems per file. Then ask the user with `AskUserQuestion`: prompt-fit all files below 70, choose files, or not now. For each chosen file, run `prompt:revising-prompts` and land the changes through 1 PR (on a running team, send it to the orchestrator as a `TASK` for the designer, who owns the routers and the rules).

## Step 4 — Report

Write `docs/adlc/maturity-<date>.md`: the table of step 2, the change since the last report, the 3 weakest points with 1 concrete next step each, and the prompt files list. Land it through a PR. Show the table to the user.
