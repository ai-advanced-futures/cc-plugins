---
name: frameworks-growth-loops
description: Compounding Growth Loops — map loop types (viral/content/paid/data), model Input→Action→Output→Reinvestment, calculate loop multiplier, and design constraint experiments.
---

# Compounding Growth Loops

## Purpose

The Growth Loop framework replaces the linear funnel with a compounding system view of growth. A funnel is a one-way flow — traffic in, customers out. A growth loop is a system where the output of one growth cycle becomes the input to the next, creating compounding acceleration. Loops are the architecture of durable, defensible growth; funnels are the architecture of growth that requires constant linear input. This framework provides the tools to identify, model, map, and optimize growth loops — and to run disciplined constraint experiments that isolate the single variable limiting loop velocity.

## Core Concepts

**Loop vs. Funnel**
- **Funnel thinking:** Spend $X on ads → get Y visitors → convert Z% → revenue. To double revenue, double ad spend. Growth is linear with cost.
- **Loop thinking:** Each customer creates conditions (content, referrals, data, viral events) that acquire additional customers. Each cycle of the loop reinvests its output as the next cycle's input. Growth compounds without proportionally increasing cost.

**The Four Primary Loop Types**

**1. Viral Loop**
Users invite or expose non-users to the product as a natural consequence of using it. The output of each cycle (users) generates new inputs (new users via invitation or exposure).
- Examples: Slack (team invitation), Figma (file sharing), Calendly (meeting links exposing the product to invitees)
- Mechanism: Using the product requires or naturally involves sharing it with others
- Compounding driver: K-factor (viral coefficient) — each user invites K new users who convert at rate r
- Constraint: Invite rate, share friction, or conversion rate of exposed non-users

**2. Content Loop**
Content created by users or the company attracts search traffic, which creates new users, who create more content, which attracts more search traffic.
- Examples: Notion (public templates), GitHub (public repos), Yelp (user reviews), G2 (review platform)
- Mechanism: Content creation is a natural byproduct of product use; content indexes in search and attracts new users
- Compounding driver: Content indexed × search conversion rate × % of new users who create content
- Constraint: Content creation rate, SEO conversion rate, or content quality

**3. Paid Loop**
Revenue from converted customers funds paid acquisition of new customers, who generate revenue that funds more acquisition. The loop compounds when LTV > CAC, producing a cash surplus that can be reinvested.
- Examples: Most subscription SaaS with positive unit economics
- Mechanism: Margin from existing customers finances customer acquisition; improving retention or ARPU expands the reinvestment pool
- Compounding driver: Reinvestment rate (what % of margin goes back into acquisition), CAC efficiency, and LTV growth
- Constraint: Margin squeeze, CAC inflation, or reinvestment cap

**4. Data/Network Loop**
More users generate more data, which improves the product's intelligence/accuracy/recommendations, which makes the product more valuable, which attracts more users.
- Examples: Google Search (more searches → better results), Waze (more drivers → better routing), ML-powered B2B tools (more customers → better model → better product)
- Mechanism: Product quality is a direct function of data volume; data accumulates with scale
- Compounding driver: Data-to-quality conversion efficiency and switching cost created by accumulated data advantage
- Constraint: Data collection rate, model update frequency, or quality-to-value conversion

**The Loop Model: Input → Action → Output → Reinvestment**
Every loop has four components:
1. **Input:** The resource that starts the cycle (users, budget, content pieces, data points)
2. **Action:** What users or the system does that transforms the input
3. **Output:** The result that can be reinvested (new users, revenue, content, data)
4. **Reinvestment:** The mechanism by which output becomes the next cycle's input

**Loop Multiplier**
The multiplier is the ratio of Output to Input for one loop cycle. A multiplier > 1 means the loop is growing. A multiplier < 1 means it is shrinking. A multiplier = 1 means it is stable (no compounding). The loop multiplier is a product of all the conversion rates within the loop.

For a viral loop: Multiplier = (invites sent per user) × (activation rate of invited users)
For a content loop: Multiplier = (content pieces per user) × (search visitors per piece) × (sign-up rate)

**Loop Constraint**
The single conversion rate or action within the loop that, if improved, would most increase the overall multiplier. Constraint experiments are structured A/B tests targeting the constraint only — not multiple variables simultaneously.

## Application Protocol

**Step 1 — Identify Active and Latent Loops**
For each loop type, ask: Is there a mechanism by which our current product use generates the input for new user acquisition? Map any loop that exists, even weakly.

**Step 2 — Map Each Loop in Full**
For each identified loop, document:
- Input (what starts the cycle)
- Action (what converts input)
- Output (what is produced)
- Reinvestment mechanism (how output feeds back as input)

**Step 3 — Calculate the Loop Multiplier**
Identify all conversion rates in the loop chain. Multiply them. If the multiplier is below 1.0, the loop is decaying. If above 1.0, it is compounding. Document the current multiplier and the target.

**Step 4 — Identify the Loop Constraint**
For each loop, find the conversion rate with the most room for improvement (furthest from benchmark or most sensitive to multiplier). This is the constraint. Run constraint experiments targeting this variable only.

**Step 5 — Design Constraint Experiments**
For the primary constraint in each active loop:
- Define the experiment (what specific change will you test)
- Define the metric (which conversion rate you are targeting)
- Define the test duration and minimum sample size
- Define success criterion (improvement threshold that warrants loop redesign)

**Step 6 — Prioritize Loop Investment**
If multiple loops are active, rank by: current multiplier, scalability (how much can the multiplier grow), and strategic defensibility (how hard is this loop for competitors to replicate). Invest in the highest-scoring loop as the primary growth engine.

## Output Format

```
LOOP INVENTORY
--------------
Loop Type | Active? | Multiplier | Primary Constraint
Viral     | [ ]     | [X.X]      | [e.g., invite rate — currently 15%, benchmark 30%]
Content   | [ ]     | [X.X]      | [e.g., content-per-user — currently 0.2, target 0.8]
Paid      | [ ]     | [X.X]      | [e.g., CAC payback — currently 18mo, target 12mo]
Data      | [ ]     | [X.X]      | [e.g., model update frequency — monthly vs. weekly]

LOOP MAPS
----------

[LOOP TYPE 1] — [e.g., Viral Loop]
Input:          [e.g., 1 new user signs up]
Action:         [e.g., user invites teammates to collaborate]
  Conversion 1: [e.g., invite rate = 40% of users send ≥1 invite]
  Conversion 2: [e.g., invite-to-activation rate = 35%]
Output:         [e.g., 0.14 new activated users per input user]
Reinvestment:   [e.g., each activated user enters the loop as a new input]
Current Multiplier: 0.14 (below 1 — loop is not self-sustaining; depends on external input)
Target Multiplier: 0.5+ (requires invite rate → 70% OR activation rate → 60%)

[LOOP TYPE 2] — [e.g., Content Loop]
Input:          [e.g., 1 user creates 1 public artifact]
Action:         [e.g., artifact indexes in search and gets shared]
  Conversion 1: [e.g., content creation rate = 0.3 pieces per user per month]
  Conversion 2: [e.g., 120 search visitors per indexed piece per month]
  Conversion 3: [e.g., 2.5% visitor-to-sign-up rate]
Output:         [e.g., 0.9 new sign-ups per content piece per month]
Reinvestment:   [e.g., new sign-ups become content creators → more pieces]
Current Multiplier: 0.9 × 0.3 = 0.27
Target Multiplier: 1.0+ (requires content creation rate → 1.0 per user OR SEO conversion → 4%)

CONSTRAINT EXPERIMENT PLAN
---------------------------
Loop: [type]
Constraint: [specific conversion rate — e.g., invite rate]
Current rate: [X%]
Benchmark: [Y%]
Hypothesis: "[Why this constraint is below benchmark and what will fix it]"
Experiment: "[Specific change — e.g., in-product collaboration prompt at first value moment]"
Target metric: [Constraint rate] → [Y%] within [N weeks]
Minimum sample size: [N users per variant]

LOOP PRIORITIZATION
-------------------
Loop     | Multiplier | Scale Ceiling | Defensibility | Priority
Viral    | [X.X]      | [High/Med/Low]| [High/Med/Low]| #[N]
Content  | [X.X]      | [High/Med/Low]| [High/Med/Low]| #[N]
Paid     | [X.X]      | [High/Med/Low]| [High/Med/Low]| #[N]
Data     | [X.X]      | [High/Med/Low]| [High/Med/Low]| #[N]

Primary growth engine: [loop type] — investment rationale: [2 sentences]
```
