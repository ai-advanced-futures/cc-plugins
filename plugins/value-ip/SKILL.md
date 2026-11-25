---
name: value-ip
description: Use when you need to find TRUE differentiating value and IP in any artifact — plans, PRDs, code, competitive analyses, or M&A due diligence. Runs multi-agent debate using Helmer 7 Powers, Blue Ocean ERRC, Christensen Disruption Theory, and Moore Core vs. Context. Acts as devil's advocate, quality gate, or value guardian.
---

# Value & IP Plugin

## Purpose

Find what's truly yours — before your competitors do.

Given any artifact, this plugin answers: **does this contain genuine, defensible differentiating value — and if so, what is the IP?** Four framework agents debate the artifact, surface every weak claim, and force a verdict.

## Auto-Activation Triggers

This plugin activates when you detect:
- "What's truly differentiating about this?"
- "Is this actually IP or just a feature?"
- "What's our real competitive advantage here?"
- "Is there genuine value differentiation in this plan/PRD/code?"
- "What IP does this acquisition target have?"
- "Devil's advocate — what's wrong with this plan?"
- "What would a competitor say about our differentiation?"
- "Guard this work — does it have real value?"
- Reviewing output from competitive-intelligence, pricing, corporate-development

## Commands

### `/value-ip:analyze`
Full multi-agent debate. Four framework lens agents analyze independently, debate coordinator runs Socratic challenges, synthesizer produces **VALUE & IP SCORECARD + DEVIL'S ADVOCATE REPORT**.

Use when: You have an existing artifact and want a thorough value & IP assessment.

### `/value-ip:challenge`
Fast devil's advocate. Skip the scorecard — go straight to the hardest challenges against your value claims.

Use when: Quick gut-check before committing to more work.

### `/value-ip:guard`
Proactive guardian mode. Invoke BEFORE marking any work complete. Returns GREEN/YELLOW/RED verdict.

Use when: About to finalize a feature, PRD, competitive response, or M&A decision.

## Framework Agents

| Agent | Framework | Core Question |
|-------|-----------|---------------|
| `helmer-agent` | Helmer's 7 Powers | What structural barrier to competition does this create? |
| `blue-ocean-agent` | Blue Ocean ERRC | What genuinely new value curve does this create? |
| `christensen-agent` | Christensen Disruption | Is this disruptive — and can incumbents rationally counter it? |
| `moore-agent` | Moore Core vs. Context | Is this truly Core, or is it commodity Context? |
| `debate-coordinator` | Socratic synthesis | Where are the real tensions and weak claims? |
| `synthesizer` | Dual output | VALUE & IP SCORECARD + DEVIL'S ADVOCATE REPORT |

## Integrates With

- `competitive-intelligence` — reads ecosystem maps and lens analyses
- `pricing` — reads EVC data and feature classifications
- `corporate-development` — reads M&A due diligence artifacts (IP valuation for deals)
- `product-finance` — reads financial models and ROI analyses
- `prd` — reads PRD artifacts
- `tech-budget` — reads technology investment decisions
- `thinktank` — can invoke for extended Socratic deliberation
- `superpowers` — can be called as part of `verification-before-completion`
- `tech-contracts` — for consulting IP clause assessment; invoke `tech-contracts:review` (consultant persona) to validate background IP carve-outs and catch work-for-hire red flags before signing

## Output

Every analysis produces a **dual output**:

1. **VALUE & IP SCORECARD** — structured markdown with framework verdicts, IP claims, and PASS/CONDITIONAL/FAIL verdict. Committable to the repository.

2. **DEVIL'S ADVOCATE REPORT** — specific challenges the team must respond to before marking work complete.
