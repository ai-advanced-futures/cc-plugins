---
name: frameworks-pmf-signal
description: Sean Ellis Product-Market Fit Signal — 40% Rule, survey methodology, retention curve analysis, and the PMF gate that prohibits scaling before fit is confirmed.
---

# Product-Market Fit Signal (Sean Ellis)

## Purpose

Sean Ellis established the most operationally useful definition and test for product-market fit (PMF): if at least 40% of users say they would be "very disappointed" if the product disappeared, the product has PMF. Below 40%, scaling sales and marketing will accelerate burn without building a durable business — it is the fastest way to obscure a product problem with a GTM problem. This framework provides the survey methodology, the retention curve interpretation, and the qualitative signal triangulation that together constitute a PMF verdict. The PMF gate: commit to scaling GTM investment only after PMF is confirmed, because clever go-to-market cannot make up for a product that users do not truly need.

## Core Concepts

**The 40% Rule**
Ask users: "How would you feel if you could no longer use [Product]?"
- Very disappointed
- Somewhat disappointed
- Not disappointed (it isn't really that useful)
- N/A — I no longer use [Product]

The PMF threshold is ≥40% responding "very disappointed." This threshold was derived empirically by Ellis from analyzing dozens of startups and correlating this metric with growth outcomes.

**Why "Very Disappointed" — Not NPS or Satisfaction**
NPS measures satisfaction and likelihood to recommend, which can be high even for products users would not miss. The "very disappointed" framing captures dependency — whether the product has become genuinely irreplaceable in the user's workflow. A product with 70 NPS but 20% "very disappointed" does not have PMF; it has a pleasant but dispensable product.

**Survey Cohort Requirements**
The Ellis survey must be administered to the right population to produce valid results:
- Users who have used the product at least twice
- Users who have used the product within the last two weeks (excluding inactive users)
- Minimum sample size: 40 responses (draw conclusions only from 40 or more)
- Exclude users on onboarding assistance who have not yet formed independent habits

**The Retention Curve**
The retention curve plots the percentage of a user cohort that remains active at each time interval (Day 1, 7, 14, 30, 60, 90, 180). The shape of the curve is the most honest PMF signal:

- **PMF retained:** Curve flattens at a non-trivial percentage (above ~20-30% at Day 90). Users have found sustainable value and formed habits. This asymptotic shape indicates a core group for whom the product is genuinely irreplaceable.
- **No PMF:** Curve approaches zero. Even initially engaged users eventually abandon the product. No feature optimization or pricing change will fix this — the product is not solving a problem users care enough about to sustain.
- **Unclear PMF:** Curve flattens but at very low levels (<5%). Possible niche PMF — the product fits a small segment but the addressable market may be insufficient.

**Qualitative Signal Triangulation**
The 40% survey and retention curve are the quantitative tests. Four qualitative signals strengthen or weaken the verdict:

1. **Inbound pull:** Do users reach out asking for features that indicate deep use-case investment?
2. **Referral behavior:** Do users proactively share the product with colleagues without any referral incentive?
3. **Usage without prompting:** Do users use the product in ways the team did not design for?
4. **Loss aversion language:** Do users use language like "I can't imagine going back to how we did this before"?

**The PMF Gate**
The PMF Gate is a go/no-go decision point. Scaling GTM spend before PMF is confirmed is classified as a high-risk action requiring explicit executive acknowledgment:
- Below 40% "very disappointed" AND retention curve approaching zero → No scale; return to product iteration
- Below 40% but retention curve flattening → Partial PMF; investigate which segment has it, optimize for that cohort
- At or above 40% AND retention curve flattening → PMF confirmed; scale GTM with confidence

## Application Protocol

**Step 1 — Administer the Ellis PMF Survey**
Select the correct cohort: users who have used the product 2+ times in the last 14 days. Survey all eligible users if n < 200. Use the exact question wording from Ellis. Include two follow-up open-text questions:
- "What type of person do you think would most benefit from [Product]?" (identifies the PMF segment)
- "What is the main benefit you receive from [Product]?" (identifies the value driver)
- "How can we improve [Product] for you?" (identifies gaps — from "very disappointed" users only)

**Step 2 — Analyze the 40% Score**
Calculate percentage "very disappointed." Segment results by:
- User role/persona (which segment has the highest score?)
- Use case (which workflow drives highest score?)
- Tenure (cohort who has been using longest vs. newest users)
- Company size / industry (which ICP segment scores highest?)

The segment where the score is highest is the PMF beachhead. Even if the overall score is below 40%, a segment score above 40% indicates where PMF exists and where GTM should focus.

**Step 3 — Build and Interpret the Retention Curve**
Select 3 cohorts: earliest users (strongest product experience), users from 6 months ago, users from 3 months ago. Plot retention for each cohort at Day 7, 14, 30, 60, 90, 180. Assess curve shape for each cohort. If newest cohort is flattening more than oldest, PMF may be improving. If oldest cohort is flattening and newest is declining, investigate feature regressions or ICP drift.

**Step 4 — Score Qualitative Signals**
Rate each of the four qualitative signals (Inbound pull, Referral, Unprompted usage, Loss aversion language) as: Strong / Weak / Absent. Strong on 3+ = high-confidence PMF. Weak/absent on 3+ = reinforces no-PMF verdict.

**Step 5 — Render PMF Verdict**
Combine quantitative and qualitative evidence. Issue one of four verdicts:
1. **PMF Confirmed** — Scale GTM
2. **Segment PMF** — Scale only for the PMF segment; limit GTM to that segment
3. **PMF In Progress** — Identify retention curve flattening segment; accelerate iteration there
4. **No PMF** — Stop scaling; return to product discovery

**Step 6 — Define the PMF Iteration Loop**
If PMF is not confirmed, define the next product hypothesis, the experiment, and the re-survey timeline. Re-survey after at least 4 weeks, because product changes need that time to affect behavior. Re-survey every 6-8 weeks during active iteration.

## Output Format

```
PMF SURVEY RESULTS
------------------
Survey date: [date]
Eligible cohort (2+ uses, active in 14 days): [N users]
Responses received: [N] — response rate: [X%]

"Very disappointed" : [X%]  ← PMF threshold: 40%
"Somewhat disappointed": [X%]
"Not disappointed": [X%]
"No longer use": [X%]

SEGMENT BREAKDOWN (very disappointed %)
----------------------------------------
Segment                | Score | PMF?
[Persona A / Use Case] | [X%]  | [ ] Yes / No
[Persona B / Use Case] | [X%]  | [ ] Yes / No
[Persona C / Use Case] | [X%]  | [ ] Yes / No

Highest-scoring segment: [name] at [X%]
PMF beachhead: [this segment — if score ≥40%]

OPEN-TEXT SYNTHESIS (from "very disappointed" respondents)
----------------------------------------------------------
Primary value driver: "[Synthesized answer from open text]"
Ideal user description: "[Synthesized persona from responses]"
Top improvement request: "[Synthesized from responses]"

RETENTION CURVE ANALYSIS
-------------------------
Cohort        | Day 7 | Day 14 | Day 30 | Day 60 | Day 90 | Shape
[Oldest]      | [X%]  | [X%]   | [X%]   | [X%]   | [X%]   | [Flat/→0]
[6 months]    | [X%]  | [X%]   | [X%]   | [X%]   | [X%]   | [Flat/→0]
[3 months]    | [X%]  | [X%]   | [X%]   | [X%]   | [X%]   | [Flat/→0]
Long-run floor (Day 90 across all cohorts): [X%]
Curve verdict: [ ] Flattening (PMF signal)  [ ] Approaching zero (No PMF)

QUALITATIVE SIGNAL SCORE
-------------------------
Inbound pull (feature requests from power users): [ ] Strong  [ ] Weak  [ ] Absent
Referral without incentive: [ ] Strong  [ ] Weak  [ ] Absent
Unprompted usage beyond designed use case: [ ] Strong  [ ] Weak  [ ] Absent
Loss aversion language from users: [ ] Strong  [ ] Weak  [ ] Absent
Qualitative verdict: [Strong / Mixed / Weak]

PMF GATE VERDICT
----------------
[ ] PMF CONFIRMED — Quantitative ≥40% + retention curve flattening + qualitative strong
    → CLEAR TO SCALE GTM
[ ] SEGMENT PMF — ≥40% in [segment] only
    → Scale GTM only for [segment]; redesign ICP and channel mix
[ ] PMF IN PROGRESS — Retention flattening for [cohort/segment] but survey below 40%
    → Accelerate iteration in [specific area]; re-survey in 6-8 weeks
[ ] NO PMF — Survey below 40% + retention approaching zero
    → STOP SCALING; return to product discovery

ITERATION PLAN (if PMF not confirmed)
--------------------------------------
Hypothesis: "[What product change will improve PMF signal]"
Experiment: "[Specific feature or experience change]"
Re-survey date: [6-8 weeks out]
Success criterion: [X% very disappointed in re-survey]
```
