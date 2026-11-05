---
description: "Bootstrap a repo-specific PR-review system into this repository. Interrogates the repo and its review history, proposes a checklist of review concerns, confirms them with you, then writes .claude/code-review/contract.md and generates one .claude/skills/reviewing-<concern> lens per confirmed concern, adds a router block to CLAUDE.md that points at the contract, and writes a REVIEW.md block for Anthropic's Code Review service on GitHub. Idempotent — safe to re-run to fold in new signal."
argument-hint: "[concerns to emphasise]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Skill, AskUserQuestion, Write, Edit
---

# /code-review:setup

This command makes or refreshes the review system. Do not check first that the system exists,
because this command is how the system gets made.

## Step 1 — Invoke the bootstrap coordinator

Invoke the `code-review:bootstrapping` Skill. Pass any arguments verbatim as free-form
hints (e.g. a concern to emphasise). The skill owns all interaction from here. It runs these five
steps:

1. Detect any prior `.claude/code-review/contract.md` / `.claude/skills/reviewing-*` and offer
   update or fresh.
2. Mine four signal sources (GitHub PR review history, repo docs, git/codebase shape, prior
   artifacts).
3. Draft a checklist of review concerns, each with its evidence.
4. Ask you to confirm, add, or drop concerns, to confirm invariants and deterministic gates, and
   to confirm the REVIEW.md failure statements, skip paths, and Nit limit.
5. Write the contract and one lens skill per concern, add the router block to `CLAUDE.md` and
   the block to `REVIEW.md` (unless you declined either in step 4), check branch protection,
   then print a receipt.
