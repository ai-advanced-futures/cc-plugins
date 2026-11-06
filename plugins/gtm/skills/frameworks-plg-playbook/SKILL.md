---
name: frameworks-plg-playbook
description: Product-Led Growth playbook — freemium vs. trial model selection, time-to-value optimization, viral hook design, PQL definition, and expansion trigger mapping.
---

# Product-Led Growth (PLG) Playbook

## Purpose

Product-Led Growth is a GTM model in which the product itself is the primary driver of acquisition, conversion, and expansion — replacing or augmenting traditional sales and marketing motions. The core thesis is that the most effective sales motion is the product being experienced before commitment. PLG compresses the buyer journey by letting the product deliver the value proposition directly, converts users into advocates through genuine delight, and expands revenue through natural usage growth rather than sales-led upsell. This playbook operationalizes the critical PLG design decisions: which access model to use, how to get users to value as fast as possible, where to embed viral mechanics, when to qualify a user as sales-ready (PQL), and what triggers expansion revenue.

## Core Concepts

**PLG vs. Sales-Led Growth (SLG)**
In SLG, a salesperson explains the product value before the prospect experiences it. In PLG, the product demonstrates value before a salesperson is needed. PLG is appropriate when:
- The product can deliver meaningful value in a self-serve session
- The primary buyer is also the primary user (or can be influenced by users)
- The product has natural virality or network effects
- The time-to-value is achievable without significant configuration

**Freemium vs. Free Trial**

*Freemium:*
- Users access a permanently limited version at no cost
- The free tier is designed to be genuinely useful, not artificially crippled
- Conversion to paid is triggered by hitting a usage limit or needing an advanced feature
- Best when: network effects exist (more users = more value), the free tier creates viral exposure, or the TAM is massive and top-of-funnel volume is strategically valuable
- Risk: free tier too useful → users stay on the free tier; free tier too limited → users leave before they activate

*Free Trial:*
- Users access the full product for a defined period (7, 14, or 30 days)
- Conversion is triggered by trial expiration
- Best when: the full product experience is required to demonstrate value, onboarding is relatively simple, and the conversion decision is time-bounded
- Risk: users fail to activate during the trial period (time-to-value exceeds trial length)

**Time-to-Value (TTV)**
The elapsed time from sign-up to the moment the user first experiences the product's core value (the Aha Moment). TTV is the most important PLG operating metric. Long TTV = most users churn before experiencing value. The design goal is: get every user to the Aha Moment before they have a reason to leave. Target TTV by product type:
- Collaboration tools: < 5 minutes
- Analytics/BI: < 30 minutes with sample data
- Integration platforms: < 2 hours to first working connection
- Complex enterprise tools: < 24 hours with guided onboarding

**Viral Hook**
The in-product mechanic that naturally causes users to invite, share, or expose the product to new users. Viral hooks must be embedded in the product's core workflow — not bolted on as a referral program. Effective viral hooks:
- **Collaboration invite:** "Invite your team to see this dashboard" (user needs teammates to unlock value)
- **Shared artifact:** Proposals, reports, or boards created in the product are shared externally, exposing the brand
- **Social proof:** Public profile pages, case study generation, or leaderboard visibility
- **Watermark/attribution:** Free-tier outputs carry brand attribution (e.g., "Made with [Product]")

**Product Qualified Lead (PQL)**
A PQL is a user who has demonstrated, through product behavior, that they are ready for a commercial conversation. PQLs are not just activated users — they are users who have hit a threshold of engagement or value extraction that correlates with conversion. PQL definition requires:
1. Identifying the specific product actions that predict conversion (via cohort analysis)
2. Setting engagement thresholds (e.g., "created 5+ reports" or "invited 3+ teammates")
3. Setting a time window (actions within the first 14 days)
4. Routing PQLs to sales with full product context (what they did, what they haven't done)

**Expansion Trigger**
The specific event or threshold that triggers an upsell or expansion conversation. Expansion triggers must be embedded in the product experience — the user hits a limit or milestone that makes the upgrade obviously valuable.

Common expansion triggers:
- Seat limit reached (collaboration products)
- Usage cap hit (API calls, records, reports)
- Feature gate encountered (user tries to use a paid feature)
- Outcome milestone (user achieves a significant result — prompt to upgrade to sustain/scale it)

## Application Protocol

**Step 1 — Select Access Model**
Evaluate Freemium vs. Free Trial against four criteria:
1. Can the product deliver genuine value in a limited version? (Yes → Freemium candidate)
2. Does the full product experience require full access to demonstrate value? (Yes → Trial candidate)
3. Is viral distribution through free-tier usage strategically valuable? (Yes → Freemium)
4. Is the trial period sufficient for users to reach the Aha Moment? (No → extend trial or switch to Freemium)

**Step 2 — Map and Compress Time-to-Value**
Document every step between sign-up and the Aha Moment. For each step:
- Is this step strictly necessary?
- Can it be deferred (done after first value, not before)?
- Can it be automated or pre-filled?

Eliminate or defer every non-essential step. Target: halve current TTV.

**Step 3 — Design the Viral Hook**
Identify where in the core product workflow a user naturally generates output that others need to see or collaborate on. Design the sharing mechanic into that workflow. Test: does the viral hook feel like product functionality or like a marketing ask? It must feel like product functionality.

**Step 4 — Define the PQL**
Run cohort analysis: compare users who converted to paid vs. users who churned. Identify the 2-3 product actions (and thresholds) that most strongly differentiate the two cohorts. Draft the PQL definition:
"A user who has [Action 1 at threshold X] and [Action 2 at threshold Y] within [N] days of sign-up."

Validate: what % of current users meet this definition? What is the conversion rate of PQL-qualified users?

**Step 5 — Map Expansion Triggers**
For each paid tier or add-on, identify the natural usage pattern that makes the upgrade obviously valuable. Build in-product prompts that appear at the trigger moment — not in a marketing email, but in the product, at the moment of friction.

**Step 6 — Build the PLG Dashboard**
Instrument and monitor weekly: TTV, activation rate, Day 7 and Day 30 retention, PQL volume and conversion rate, viral coefficient, expansion revenue rate.

## Output Format

```
PLG MODEL SELECTION
-------------------
Access model: [ ] Freemium  [ ] Free Trial  [ ] Hybrid (freemium + trial of premium)
Rationale: [2-3 sentences on why this model fits product and GTM context]
Free tier design: [What is included / what is gated]
Trial length (if applicable): [X days] — covers TTV: [ ] Yes  [ ] No (risk flag)

TIME-TO-VALUE MAP
-----------------
Step | Action                        | Avg Time | Necessary? | Eliminate/Defer?
 1   | Email verification            | 2 min    | Yes        | —
 2   | Profile setup                 | 5 min    | Defer       | Move to post-Aha
 3   | Connect data source           | 20 min   | Yes        | —
 4   | [Aha Moment — first insight]  | 25 min   | TARGET     | —
Current TTV: [X min/hours]
Target TTV: [Y min/hours]
Steps to eliminate/defer: [list]

VIRAL HOOK DESIGN
-----------------
Core workflow action: "[What users naturally do in the product]"
Shareable output: "[What they generate that others need to see]"
Viral mechanic: "[How the hook is embedded — invite / artifact / attribution]"
Estimated K-factor impact: [estimated viral coefficient]

PQL DEFINITION
--------------
Required Action 1: "[Action]" at threshold: [N times/events]
Required Action 2: "[Action]" at threshold: [N times/events]
Optional Action 3: "[Action]" at threshold: [N times/events — boosts score]
Time window: [N days from sign-up]
Current % of users qualifying as PQL: [X%]
PQL → Paid conversion rate: [X%]
Routing: [How PQLs are surfaced to sales — CRM alert / Slack / dashboard]

EXPANSION TRIGGER MAP
---------------------
Trigger Event               | Current Tier | Upgrade Target | In-Product Prompt
Seat limit reached (≥N)     | Starter      | Growth         | [prompt text]
[Usage cap hit]             | Free         | Pro            | [prompt text]
[Feature gate encountered]  | Free         | Pro            | [prompt text]
[Outcome milestone]         | Growth       | Enterprise     | [prompt text]

PLG HEALTH DASHBOARD
--------------------
Metric              | Current | Target | Status
TTV (median)        | [X]     | [Y]    | [ ] ✓/✗
Activation rate     | [X%]    | [Y%]   | [ ] ✓/✗
Day 30 retention    | [X%]    | [Y%]   | [ ] ✓/✗
PQL volume/month    | [N]     | [N]    | [ ] ✓/✗
PQL conversion rate | [X%]    | [Y%]   | [ ] ✓/✗
Viral coefficient   | [X]     | >0.5   | [ ] ✓/✗
Expansion rev rate  | [X%]    | [Y%]   | [ ] ✓/✗
```
