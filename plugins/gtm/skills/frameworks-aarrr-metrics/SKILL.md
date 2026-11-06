---
name: frameworks-aarrr-metrics
description: Dave McClure's Pirate Metrics (AARRR) — five-stage growth funnel with metric definitions, bottleneck identification, and Aha Moment detection.
---

# Pirate Metrics — AARRR (McClure)

## Purpose

Dave McClure's AARRR framework (Acquisition, Activation, Retention, Referral, Revenue) is the canonical GTM measurement system for product-led and growth-oriented businesses. It imposes discipline on growth analysis by forcing teams to measure the full customer lifecycle — not just top-of-funnel vanity metrics. The framework's power is in bottleneck identification: most growth problems are concentrated in one or two stages, and fixing the wrong stage wastes resources. AARRR also anchors the "Aha Moment" — the specific product event that converts a new user into a retained user — which is the highest-leverage intervention point in most GTM motions. No scale effort is justified until the Aha Moment is identified and optimized.

## Core Concepts

**The 5 Stages**

**A — Acquisition**
How do users find you? The stage measures the efficiency of all channels in delivering qualified visitors or sign-ups. Key distinction: acquisition is not just traffic — it is qualified traffic (people who could plausibly become customers). Measuring raw traffic inflates the metric and obscures channel quality.

Core metrics:
- Visitors by channel (organic, paid, social, referral, direct)
- Qualified visitor rate (visitors who match ICP)
- Sign-up rate (visitors → registered users)
- CAC by channel (customer acquisition cost)
- Payback period by channel

**A — Activation**
Did users have a good first experience? Activation is the bridge between acquisition and retention — it is the moment a new user first experiences the product's core value. Activation rate measures the percentage of new users who reach a predefined "activated" state within a defined time window (typically 24-72 hours). Almost every unactivated user leaves for good.

Core metrics:
- Activation rate (% of sign-ups who complete the activation event)
- Time-to-activation (median hours/days from sign-up to activation)
- Activation event completion rate by step (to find drop-off in onboarding)

**R — Retention**
Do users come back? Retention is the most critical stage — it is the proxy for product-market fit. High acquisition and activation with poor retention indicates the product is not delivering durable value. Retention is typically measured as the percentage of users still active at day 7, day 30, and day 90 after their first session.

Core metrics:
- Day 7 / Day 30 / Day 90 retention rate
- Churn rate (monthly/annual)
- Net Revenue Retention (NRR) for subscription businesses
- Retention curve shape (does it flatten, or does it approach zero?)

A retention curve that flattens (asymptotic) indicates PMF. A retention curve that approaches zero indicates PMF is not yet achieved.

**R — Referral**
Do users tell others? Referral is the virality stage. High organic referral reduces blended CAC and signals that users find the product genuinely valuable. NPS is a leading indicator; actual referral events (invites sent, referral links clicked, word-of-mouth attributable sign-ups) are the real measure.

Core metrics:
- NPS (Net Promoter Score) — leading indicator
- Viral coefficient (K-factor): (invites sent per user) × (conversion rate of invites)
- Referral-attributed sign-ups as % of total
- Invite/share feature usage rate

**R — Revenue**
Do users pay? The revenue stage measures monetization efficiency. For subscription businesses: MRR, ARR, ARPU, LTV. For transactional businesses: average order value, purchase frequency, LTV. The critical ratio is LTV:CAC — the business model is viable only when LTV significantly exceeds CAC (minimum 3:1, healthy 5:1+).

Core metrics:
- MRR / ARR
- ARPU (Average Revenue Per User)
- LTV (Customer Lifetime Value)
- LTV:CAC ratio
- Expansion revenue rate (upsell/cross-sell as % of total revenue)

**The Aha Moment**
The Aha Moment is the specific in-product event that strongly correlates with long-term retention. It is not the onboarding step — it is the moment the user first experiences the core value proposition. Examples:
- Facebook: adding 7 friends in 10 days
- Twitter: following 30 accounts
- Dropbox: storing a first file across two devices
- Slack: sending 2,000 team messages

Identifying the Aha Moment requires cohort analysis: compare retained users vs. churned users and find the specific action(s) that retained users completed disproportionately in their first week.

## Application Protocol

**Step 1 — Instrument All 5 Stages**
Ensure event tracking is in place for each stage transition. The most common gap is between Activation and Retention — teams measure sign-ups and revenue but have no visibility into whether users activated or why they churned.

**Step 2 — Calculate Stage Conversion Rates**
Build the AARRR funnel:
- Acquisition → Activation: % of sign-ups who activate
- Activation → Retention: % of activated users retained at Day 30
- Retention → Referral: % of retained users who refer
- Retention → Revenue: % of retained users who convert to paid

**Step 3 — Identify the Bottleneck**
The bottleneck is the stage with the largest relative drop-off. Optimize one stage at a time, because several changes at once spread effort and hide which change caused a result. Fix the worst bottleneck first.

Bottleneck identification rules:
- Below-benchmark Acquisition: channel diversification, ICP tightening, messaging improvement
- Below-benchmark Activation: onboarding redesign, time-to-value compression, friction removal
- Below-benchmark Retention: product-market fit investigation, feature gap analysis
- Below-benchmark Referral: viral loop design, referral program, NPS remediation
- Below-benchmark Revenue: pricing model, upsell motion, expansion trigger design

**Step 4 — Find the Aha Moment**
Run cohort analysis: split users into retained (Day 30 active) and churned (Day 30 inactive). For each cohort, calculate the frequency of every in-product action in the first 7 days. The Aha Moment candidates are actions where the retained cohort's frequency is 2x+ the churned cohort's frequency.

**Step 5 — Optimize Toward the Aha Moment**
Redesign onboarding to deliver users to the Aha Moment as fast as possible. Remove every step between sign-up and the Aha Moment that is not strictly necessary.

**Step 6 — Set Stage Benchmarks**
Compare current rates to SaaS/PLG benchmarks by stage. Flag any stage more than 20% below benchmark as a priority bottleneck.

## Output Format

```
AARRR FUNNEL SNAPSHOT
---------------------
Stage       | Metric                    | Current  | Benchmark | Status
ACQUISITION | Sign-up rate (visitor→)   | [X%]     | 2-5%      | [ ] ✓/✗
            | CAC (blended)             | [$X]     | [target]  | [ ] ✓/✗
ACTIVATION  | Activation rate           | [X%]     | 40-60%    | [ ] ✓/✗
            | Time-to-activation        | [X hrs]  | <24 hrs   | [ ] ✓/✗
RETENTION   | Day 7 retention           | [X%]     | >40%      | [ ] ✓/✗
            | Day 30 retention          | [X%]     | >20%      | [ ] ✓/✗
            | Retention curve shape     | [flat/→0]| Flattens  | [ ] ✓/✗
REFERRAL    | NPS                       | [X]      | >40       | [ ] ✓/✗
            | Viral coefficient (K)     | [X]      | >0.5      | [ ] ✓/✗
REVENUE     | LTV:CAC ratio             | [X:1]    | >3:1      | [ ] ✓/✗
            | NRR                       | [X%]     | >100%     | [ ] ✓/✗

PRIMARY BOTTLENECK: [Stage] — [metric + gap from benchmark]
Secondary bottleneck: [Stage] — [metric + gap]

AHA MOMENT ANALYSIS
-------------------
Aha Moment candidate: "[Specific in-product action]"
Retained cohort frequency (Day 1-7): [X times]
Churned cohort frequency (Day 1-7): [X times]
Multiplier: [Xr retained vs. churned — must be 2x+ to qualify]
Confidence: [ ] Confirmed  [ ] Hypothesis — needs cohort validation

ONBOARDING PATH TO AHA MOMENT
------------------------------
Step 1: [Action] — median time: [X min]
Step 2: [Action] — median time: [X min]
Step 3: AHA MOMENT — [action] — target: within [X hours] of sign-up
Friction to remove: [specific steps between sign-up and Aha that can be eliminated]

BOTTLENECK SPRINT PLAN
-----------------------
Stage to fix: [bottleneck stage]
Hypothesis: "[Why the bottleneck exists]"
Experiment: "[Specific change to test]"
Success metric: "[Stage rate] improves from [X%] to [Y%] within [N weeks]"
```
