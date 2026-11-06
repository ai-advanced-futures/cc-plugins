# Pricing Plugin — Frameworks Reference

This plugin is built on five intellectual frameworks. Each one contributes a distinct layer
to the pricing process. This document explains each framework's origin, core thesis, key
equations or rules, and how it was incorporated into the plugin's implementation.

---

## Table of Contents

1. Luis F. Amadeo — VALUE = Speed × Accuracy of Outcome
2. [Madhavan Ramanujam — Monetizing Innovation](#2-madhavan-ramanujam)
3. [Patrick Campbell / ProfitWell — Value Metrics](#3-patrick-campbell--profitwell)
4. [Hamilton Helmer — 7 Powers](#4-hamilton-helmer--7-powers)
5. [Tony Ulwick / JTBD — Outcome-Driven Innovation](#5-tony-ulwick--jtbd)
6. [How the Frameworks Connect](#how-the-frameworks-connect)
7. [v1.1 Roadmap — Retention Pricing](#v11-roadmap--retention-pricing)

> **Scope notice:** v1.0 of this plugin prices for **acquisition** — the initial WTP
> decision. The full Amadeo framework also covers **retention** pricing (ongoing monthly
> WTP driven by Love and Fear after purchase). Retention pricing is documented in the
> [v1.1 Roadmap](#v11-roadmap--retention-pricing) section below.

---

## 1. Luis F. Amadeo

**Role in plugin:** AI-era classification + AI_MULTIPLIER + emotional pricing model
(Fear, Love, supply/demand scaffolding)

### Who

Luis F. Amadeo is a Chief Agentic Officer and the architect of this plugin. His pricing
philosophy emerged from observing that traditional pricing frameworks were designed for a
pre-AI world where software produces static, deterministic outputs. AI-era products behave
differently: they improve over time, they compress time-to-outcome, and their value is a
function of the *quality* of the outcome they deliver — not just its existence.

But Amadeo goes further than a single equation. His full framework also describes the
**emotional mechanics of pricing** — specifically how Fear and Love govern both the initial
purchase decision and the ongoing willingness to keep paying month after month.

---

### The Core Equation

> **VALUE = Speed × Accuracy of Outcome**

Traditional software does a job. AI-era software does it *faster* and *more accurately* —
and that combination creates value that compounds differently from static features. A feature
that is 5× faster and 95% accurate is not just marginally better; it changes how customers
use the product, what they pay for, and what tier they belong in.

---

### The AI_MULTIPLIER Formula

```
AI_MULTIPLIER = 1.0 + (speed_improvement × accuracy_improvement)
```

**Variable definitions:**

| Variable | Definition | Example |
|---|---|---|
| `speed_improvement` | How much faster the feature delivers the outcome vs. the non-AI alternative, expressed as a ratio | 4.0 = 4× faster than manual review |
| `accuracy_improvement` | Quality fraction on a 0–1 scale. 1.0 = perfect; 0.9 = 90% accurate | 0.93 = 93% accuracy |
| `AI_MULTIPLIER` | The premium multiplier applied to the base price | 4.72 = feature justifies 4.72× the base price |

**Worked example:**
```
Speed improvement:   4× faster than manual code review
Accuracy:            93%

AI_MULTIPLIER = 1.0 + (4.0 × 0.93)
             = 1.0 + 3.72
             = 4.72
```
A feature with a 4.72× multiplier applied to a $50/mo base = $236/mo justified price
before moat and market-readiness constraints.

---

### The Emotional Pricing Model: Fear and Love

Amadeo's framework treats pricing as an emotional event, not just a rational calculation.
Customers do not make purchase decisions purely on value math. They are moved by two
competing emotional forces — Fear and Love — that operate at different moments in the
customer lifecycle.

#### Fear

Fear is the dominant emotion **before purchase**. It takes three forms:

| Fear type | What the customer is thinking |
|---|---|
| **Fear of the alternative** | "If I don't have this, I'm stuck with the slow, inaccurate way of doing this job. My competitors who have it will be faster than me." |
| **Fear of missing out** | "This is becoming standard. If I wait, I'm falling behind. The gap will compound." |
| **Fear of inaction** | "Every month I don't have this, the cost of the unsolved problem continues. The pain isn't going away on its own." |

These three fears **raise the pre-purchase WTP** above what a purely rational analysis would
produce. A customer who is afraid pays more to eliminate the source of fear. This is why
urgency matters in sales — it's not manipulation, it's Fear made concrete.

**After purchase,** Fear takes a different form. Once a customer has experienced the product
delivering high Speed × Accuracy, a new fear emerges:

| Post-purchase fear | What the customer is thinking |
|---|---|
| **Fear of regression** | "I cannot go back to how it was. The old way is now unacceptable to me." |
| **Fear of capability loss** | "My workflow depends on this now. Losing it would cost me the speed advantage I've built." |
| **Fear of competitive parity loss** | "If I cancel and a competitor keeps using this, the gap closes — on me." |

Post-purchase Fear is one of the two forces that sustain **Retention WTP** — the
willingness to keep paying each month.

---

#### Love

Love is the dominant emotion **after purchase** — but only when the product consistently
delivers high Speed × Accuracy. Love is the emotional state that reaffirms the purchase
decision. It is not a one-time event. **Love is time-bound: it needs to keep coming.**

Love manifests as outcomes the customer experiences personally:

- *"I have time to work on what actually matters now."*
- *"I can take on work I couldn't do before."*
- *"My work-life balance is better."*
- *"I'm doing better, more strategic work."*
- *"I feel capable in a way I didn't before."*

These are not product features. They are **life outcomes** produced by the product
consistently doing a job with high Speed × Accuracy. When customers feel these outcomes
repeatedly, they develop a sentiment that turns into loyalty — and loyalty turns into
**low churn probability** at renewal.

The relationship between Love and customer sentiment follows a compounding logic:

```
High Speed × Accuracy (each interaction)
  → Customer experiences the outcome they sought
    → Emotional reaffirmation: "Yes, this is why I bought it"
      → Positive sentiment accumulates
        → Loyalty and stickiness grow
          → Retention WTP rises or holds
```

When Love stops being delivered — when the product degrades, when accuracy drops, when
speed improvements plateau — sentiment erodes. The customer no longer feels the outcomes
they valued. Love decays, and with it, the emotional justification for the subscription
price. This is the early warning signal of churn.

**Love and Fear at renewal time (both active):**

At the monthly renewal moment, both forces are present simultaneously:
- Love says: *"I keep getting these outcomes. This is still worth it."*
- Fear says: *"I cannot afford to lose this. Going back would hurt."*

When both are strong, retention WTP is high and price elasticity is low — the customer
will tolerate price increases. When Love is weak but Fear is still present, the customer
stays but is a churn risk. When both are weak, churn follows.

---

### The Two WTP Moments

Amadeo's framework identifies two distinct willingness-to-pay events in every subscription:

**WTP₁ — Acquisition WTP (pre-purchase)**

> What will a customer pay to acquire access to the product?

Primarily driven by:
- Pre-purchase Fear (of alternative, of inaction, of missing out)
- Rational value math (opportunity cost of the unsolved job)
- Social proof and competitive signaling

This is what **v1.0 of this plugin computes** via the dual-path formula.

---

**WTP₂ — Retention WTP (post-purchase, recurring)**

> What will a customer continue paying, month after month, to keep the product?

Primarily driven by:
- Love (accumulated positive sentiment from consistent Speed × Accuracy outcomes)
- Post-purchase Fear (of regression, capability loss, competitive parity loss)
- Switching cost inertia (Helmer)
- Whether the product continues to deliver new value or has plateaued

WTP₁ and WTP₂ are **not the same number** and are **not determined by the same forces**.
A customer may have a high WTP₁ (bought eagerly) but a declining WTP₂ (hasn't felt Love
in three months, post-purchase Fear is fading). This is the emotional anatomy of churn.

> **v1.0 of this plugin computes WTP₁ only.**
> WTP₂ (Retention WTP) is the scope of [v1.1](#v11-roadmap--retention-pricing).

---

### Supply, Demand, and Cost

The economic scaffolding of Amadeo's framework maps to classical supply/demand mechanics:

| Economic concept | Amadeo / Plugin implementation |
|---|---|
| **Demand ceiling** | `WTP_max` — maximum a customer will pay at current market readiness |
| **Supply floor** | `MARGIN_FLOOR = production_cost / (1 − target_margin)` — minimum viable price |
| **Value-justified price** | `VALUE_SIGNAL` — the price the formula produces without market constraints |
| **Demand gap** | `VALUE_SIGNAL > WTP_max` → `segment_signal` — market not yet ready to pay what this is worth |
| **Emotional demand amplifiers** | Pre-purchase Fear raises demand (shifts curve up); Love sustains demand elasticity post-purchase |

The supply/demand bracket is not just math — it is the economic frame inside which Fear and
Love operate. Fear raises a customer's demand curve before purchase (they pay more to
eliminate the fear). Love flattens the curve post-purchase (they become less price-sensitive
because they're emotionally invested).

```
Demand curve shape:
  High pre-purchase Fear → steep upward shift in WTP₁ (willing to pay more to fix the pain)
  High post-purchase Love → inelastic demand at renewal (less sensitive to price increases)
  Love decay → elastic demand (small price increase triggers churn consideration)
  Both Fear + Love → maximum retention WTP
```

The `segment_signal` in Path B is a demand curve reading: the VALUE_SIGNAL exceeds current
WTP_max because the emotional demand conditions (Fear and Love) haven't yet developed enough
for the market to recognize the full value of what's being delivered. It is a signal to
invest in building those conditions — through jtbd-market-discovery or through product
marketing that makes the Fear and Love outcomes explicit.

---

### The Accuracy Fear Signal (Special Case)

**If `accuracy_improvement < 0.8`, `AI_MULTIPLIER` is locked at 1.0.**

This is a special case of Fear operating as a *negative* force. When an AI feature delivers
below 80% accuracy, customers experience a different kind of fear: **fear of the product
itself**. Errors undermine trust. Trust loss is faster than trust building. A premium price
on a low-accuracy feature creates Fear-of-product rather than Fear-of-alternative — and
that form of Fear produces churn, not retention.

The accuracy fear signal is a forcing function: **fix the model before pricing it as AI-era**.

```python
# pricing_calculator.py:206
if accuracy_improvement < 0.8:
    return 1.0  # no premium for degraded accuracy
```

---

### The Layer 2 High-Multiplier Gate

When `AI_MULTIPLIER > 5×`, three conditions must ALL be true:

| Condition | Question it answers |
|---|---|
| `has_autonomy` | Does the feature complete the job without human intervention? |
| `has_compounding` | Does the value grow as the feature accumulates data/usage over time? |
| `has_attribution` | Can you prove the speed×accuracy improvement is *caused by the AI*, not by the dataset or the UX? |

`has_compounding` is also the Love-sustaining condition. A feature that compounds in value
over time continues delivering new Love — new outcomes — to the customer. A feature that
plateaus stops generating Love and becomes vulnerable to WTP decay at renewal.

---

### What v1.0 Implements vs. What v1.1 Defers

| Amadeo concept | v1.0 status | v1.1 scope |
|---|---|---|
| VALUE = Speed × Accuracy | ✅ Fully implemented (AI_MULTIPLIER) | — |
| Cost / Supply floor | ✅ Fully implemented (MARGIN_FLOOR) | — |
| Pre-purchase Fear | ✅ Partially implemented (WTP elicitation captures fear-driven ceiling) | Explicit Fear scoring as demand amplifier |
| Demand ceiling | ✅ Implemented (WTP_max bracket) | — |
| Supply/demand gap signal | ✅ Implemented (segment_signal) | — |
| Accuracy fear signal | ✅ Implemented (< 0.8 → multiplier = 1.0) | — |
| Love (post-purchase) | ❌ Not implemented | Sentiment/Love score as retention input |
| Post-purchase Fear | ❌ Not implemented | Fear-of-loss score at renewal |
| Retention WTP (WTP₂) | ❌ Not implemented | `retention` skill in v1.1 |
| Love decay → churn signal | ❌ Not implemented | Churn risk signal in v1.1 |

---

### Where Amadeo's Philosophy Appears in the Plugin

| Component | How it's used |
|---|---|
| `Layer1Score.ai_causes_value` | Distinguishes AI-driven value from dataset-driven value |
| `compute_ai_multiplier()` | Direct implementation of VALUE = Speed × Accuracy |
| `accuracy < 0.8` branch | Accuracy fear signal — negative Fear from product quality |
| Layer 2 gate (`apply_layer2_gate()`) | High-multiplier gate; `has_compounding` = Love-sustaining condition |
| `MetricScore.ai_era_alignment` | 4th Campbell criterion: metric scales with Speed × Accuracy |
| `MARGIN_FLOOR` | Cost / supply floor |
| `VALUE_SIGNAL` in Path B | Value-justified price before emotional/market constraints |
| `segment_signal` | Demand gap — market not yet ready; emotional demand conditions not developed |

---

## 2. Madhavan Ramanujam

**Role in plugin:** Feature classification (Killer/Leader/Filler) + tier design + failure mode detection

### Who

Madhavan Ramanujam is a partner at Simon-Kucher & Partners, the world's leading pricing
strategy consultancy. His 2016 book *Monetizing Innovation* is based on an analysis of
1,500+ product launches across industries. His central finding was provocative: **most
product failures are not engineering failures — they are pricing failures in disguise.**

Teams build features without asking whether customers will pay for them, then discover too
late that the wrong things were built at the wrong price points.

### Core Thesis

The order of operations matters:
1. Understand willingness-to-pay **before** building
2. Design packaging **before** setting prices
3. Set prices **based on value**, not on cost

Most teams do this backwards.

### Killer / Leader / Filler Classification

Every feature in a product belongs to exactly one of three categories:

| Category | Definition | Pricing role |
|---|---|---|
| **Killer** | Must-have. Gates the purchase decision. Customers won't buy without it. | Present in all tiers. Never withheld. Used in the Better tier as the primary anchor. |
| **Leader** | Differentiator. Drives upgrade decisions from Good to Better or Better to Best. | Present in Better and Best. The feature that makes someone want to pay more. |
| **Filler** | Table stakes. Nice to have. Doesn't drive purchase or upgrade but rounds out the package. | Sprinkled across tiers for completeness. Never the reason a customer buys. |

**The key mistake Ramanujam identifies:** Teams often make Filler features their headline
offer and hide Killer features inside bundles. This produces what he calls **Hidden Gems** —
high-value features that customers don't know exist and therefore don't pay for.

### Good / Better / Best Architecture

The three-tier structure is not accidental. Ramanujam's research shows it matches how
customers naturally think about value:

| Tier | Purpose | Target |
|---|---|---|
| **Good** | Entry point. Proves basic value. | ~20% of customers |
| **Better** | Anchor. Killer + Leaders. The tier most customers should choose. | ~60-70% of customers — this is the goal |
| **Best** | Premium. Everything + moat-creating features (network effects, deep integrations). | ~10-20% of customers |

**The "Better" tier as anchor:** Ramanujam's most important insight is that the middle tier
is where the money is. It should be designed to feel like the obvious, rational choice. The
Good tier exists to make Better feel reasonable; the Best tier exists to make Better feel
even more reasonable by contrast.

### The 9-Benefit Complexity Limit

**No tier should contain more than 9 benefits.**

Ramanujam's research shows that beyond 9 line items, customers stop reading and start feeling
overwhelmed. They make worse decisions, upgrade less often, and churn more quickly.

```python
# pricing_calculator.py:376
def validate_tier_complexity(benefits_per_tier: dict[str, list]) -> list[str]:
    return [tier for tier, benefits in benefits_per_tier.items() if len(benefits) > 9]
```

### The 4 Failure Modes

Ramanujam identified nine failure modes; the plugin surfaces the four most common:

| Failure Mode | Description | Plugin detection |
|---|---|---|
| **Feature Shock** | Too many features in a tier. Customers are overwhelmed. | Tier exceeds 9-benefit limit |
| **Minivations** | Under-priced high-WTP features. Leaving money on the table. | AI-era feature priced as Legacy; WTP gap detected |
| **Hidden Gems** | High-WTP features buried in the wrong tier or not surfaced. | Killer/Leader features placed in Filler position |
| **Undead Features** | Features customers no longer want, still consuming roadmap and support budget. | Legacy features with near-zero WTP and high cost |

### Where Ramanujam's Framework Appears in the Plugin

| Component | How it's used |
|---|---|
| `RamanujamCategory` enum | KILLER / LEADER / FILLER assigned per feature in audit |
| `validate_tier_complexity()` | Enforces 9-benefit limit in packaging |
| `package` skill | Good/Better/Best tier design using Killer/Leader/Filler assignments |
| `pricing-auditor` agent | Failure mode detection in executive audit report |
| Tier price anchoring | Better tier as the anchor (60-70% target) |

---

## 3. Patrick Campbell / ProfitWell

**Role in plugin:** Value metric selection + per-user antipattern detection

### Who

Patrick Campbell founded ProfitWell in 2012 to help SaaS companies understand their pricing
and reduce churn. ProfitWell was acquired by Paddle in 2022 for $200M. Before the acquisition,
ProfitWell's benchmarking database covered $5B+ in SaaS ARR, making Campbell one of the most
data-informed voices in SaaS pricing.

His core contribution to this plugin is not a single equation but a **framework for choosing
the right pricing axis** — what to charge *on*, before deciding how much to charge.

### Core Thesis

The value metric — the unit you charge on — is more important than the price itself.

A wrong value metric creates structural churn: customers grow, the metric grows, the bill
grows, but the perceived value doesn't grow proportionally. They leave. A right value metric
creates natural expansion revenue: as customers succeed, they use more, the metric grows,
revenue grows, and everyone wins.

### The 3 Campbell Criteria

A value metric is good if all three conditions are true:

| Criterion | Question | Example (good) | Example (bad) |
|---|---|---|---|
| **Alignment** | Does this metric reflect value delivered to the customer? | "per document analyzed" — customer gets value from each doc | "per user seat" — adding an admin doesn't create value |
| **Understandability** | Can the customer control and understand this metric? | "per API call" — clear and predictable | "per AI token consumed" — most customers don't understand tokens |
| **Growth alignment** | When this metric grows, does value to the customer grow proportionally? | "per outcome delivered" — more outcomes = more value | "per GB stored" — storage cost ≠ value in most products |

**Score 3/3:** Campbell-approved value metric. Use it.
**Score 2/3:** Borderline. Acceptable if the third criterion is near-miss.
**Score 1/3 or 0/3:** Misaligned. Find a different pricing axis.

### The Per-User Antipattern

Campbell's most-cited finding: **per-seat pricing is often a trap for AI-era products.**

Per-seat pricing made sense for collaboration tools (Slack, Notion) where more users = more
value because everyone needs access. But for AI tools, value comes from *outcomes*, not
headcount. Adding a 10th user to an AI code reviewer doesn't deliver 10× the value of the
first user — unless that user is actually using the tool.

```python
# pricing_calculator.py:334
def detect_per_user_antipattern(growth_equals_value_growth: bool) -> bool:
    """Returns True (antipattern present) when adding users does NOT
    proportionally increase value delivered."""
    return not growth_equals_value_growth
```

**When the antipattern is detected**, the plugin flags it and recommends moving to a
usage-based or outcome-based metric.

### Amadeo's 4th Criterion

The plugin adds one criterion to Campbell's three: **AI-era alignment**.

| Criterion | Question |
|---|---|
| `ai_era_alignment` | Does this metric scale with Speed × Accuracy of Outcome? |

This is Amadeo's contribution to Campbell's framework. A metric like "per document analyzed"
scores high because it scales with both the speed (more docs = more speed benefit) and
accuracy (better docs = better outcomes) of the AI. A metric like "per user seat" scores low
because it doesn't scale with either.

### Where Campbell's Framework Appears in the Plugin

| Component | How it's used |
|---|---|
| `MetricScore` dataclass | 4-criterion scoring (3 Campbell + 1 Amadeo) |
| `is_campbell_approved` | Returns True if total score ≥ 3 |
| `detect_per_user_antipattern()` | Flags per-seat pricing when growth ≠ value growth |
| `value-metric` skill | Full Campbell + Amadeo scoring workflow |
| `evaluate_value_metric()` | Function that produces `MetricScore` from 4 boolean inputs |

---

## 4. Hamilton Helmer — 7 Powers

**Role in plugin:** MOAT_MULTIPLIER for pricing premium from competitive position

### Who

Hamilton Helmer is a Stanford professor and founder of Strategy Capital. His 2016 book
*7 Powers: The Foundations of Business Strategy* is a rigorous analysis of what creates
durable competitive advantage. Unlike Porter's 5 Forces (which analyzes industry structure)
or the BCG matrix (which analyzes portfolio position), Helmer focuses on the specific
mechanisms that allow individual companies to sustain higher margins over time.

### Core Thesis

**Competitive advantage comes from one of exactly seven types of "power."**

Power is defined as the ability to achieve persistent excess returns. Without at least one
of the seven powers, a business is a commodity competing on execution and luck. With even
one, the business can sustain superior margins permanently.

### The 7 Powers

| Power | Definition | Pricing implication |
|---|---|---|
| **Scale Economies** | Unit costs fall as volume grows, creating a cost advantage at scale. | **Penetration pricing** — price lower to grow volume faster, widening the cost gap. Premium pricing defeats the strategy. |
| **Network Economies (Effects)** | Product becomes more valuable as more users join (e.g., Visa, Slack). | **Premium pricing** justified — value delivered increases with network size. |
| **Counter-Positioning** | A new entrant adopts a superior business model that the incumbent can't copy without cannibalizing their existing business. | **Aggressive pricing** — the incumbent is structurally blocked from responding. |
| **Switching Costs** | Customers face high real or perceived costs to leave (data migration, retraining, workflow rebuild). | **Premium pricing** — customers pay above market rather than absorb switching cost. |
| **Branding** | Sustained price premium via customer trust built over time. | **Premium pricing** — brand sustains the premium even when alternatives exist. |
| **Cornered Resource** | Exclusive access to a key input (data, talent, IP, geography). | **Premium pricing** — competitors can't replicate. |
| **Process Power** | A proprietary organizational process that delivers superior outcomes and can't be easily replicated. | **Premium pricing** — operational excellence creates durable differentiation. |

### MOAT_MULTIPLIER

The plugin translates Helmer's assessment into a numerical multiplier:

```
MOAT_MULTIPLIER = Helmer score, clamped to [1.0, 2.5]
```

- **1.0**: No moat detected. Commodity pricing applies.
- **1.5**: One moderate power (e.g., some switching costs but no network effects).
- **2.0**: One strong power (e.g., strong network effects).
- **2.5**: Multiple reinforcing powers (e.g., network effects + switching costs + cornered data resource).

### Scale Economy Special Case

Scale Economies are handled differently from the other six powers. They imply that
pricing power comes from volume, not from premium. Charging a premium when your
competitive advantage is cost efficiency defeats the strategy by slowing volume growth.

```python
# pricing_calculator.py:221
_SCALE_ECONOMY_ADVISORY = (
    "Penetration pricing advisory: Scale Economy moat detected. "
    "Your pricing power comes from volume, not premium. "
    "Consider pricing below competitors to accelerate volume growth..."
    "MOAT_MULTIPLIER locked at 1.0."
)
if is_scale_economy:
    return (1.0, _SCALE_ECONOMY_ADVISORY)
```

When Scale Economy is the primary moat, the multiplier is locked at 1.0 and a penetration
pricing advisory is surfaced. This is not a penalty — it's a strategic recommendation aligned
with how the moat actually works.

### Adversarial Moat Elicitation

The `price` skill does not accept self-reported moat scores. It requires the user to name
specific competitors and articulate differential advantages against them. This is because
most teams overestimate their competitive position when not forced to compare against
specific alternatives.

**Rule:** If no competitor is named, `MOAT_MULTIPLIER = 1.0` with a "competitive position
unvalidated" flag.

### Where Helmer's Framework Appears in the Plugin

| Component | How it's used |
|---|---|
| `compute_moat_multiplier()` | Maps Helmer score → MOAT_MULTIPLIER with Scale Economy branch |
| `price` skill, Step 5 | Adversarial moat elicitation requiring competitor comparison |
| `PathBResult.moat_advisory` | Surfaces Scale Economy penetration pricing advisory |
| `Layer1Score.ai_rare_in_market` | Counter-Positioning signal for AI classification |

---

## 5. Tony Ulwick / JTBD

**Role in plugin:** Path A activation (EVC pricing) + opportunity scoring as tier signal

### Who

Tony Ulwick is the founder of Strategyn and the creator of Outcome-Driven Innovation (ODI),
a structured methodology for applying Jobs-to-be-Done theory to product and pricing decisions.
Clayton Christensen popularized the JTBD framing ("customers don't buy products — they hire
them to do a job"); Ulwick operationalized it into a quantitative research methodology.

This plugin treats `jtbd-market-discovery` as its upstream data source. When that plugin
has run, it produces WTP data and EVC estimates that unlock Path A pricing in
this plugin.

### Core Thesis

Customers hire products to complete **jobs** — specific outcomes they want to achieve in
specific circumstances. Price should reflect the economic value of completing the job, not
the cost of building the solution.

**Opportunity score formula (Ulwick):**
```
Opportunity Score = Importance + max(0, Importance − Satisfaction)
```

Where:
- `Importance` = how important the outcome is to the customer (1–10 scale)
- `Satisfaction` = how satisfied customers are with current solutions (1–10 scale)

High importance + low satisfaction = underserved outcome = pricing opportunity.

### Economic Value to Customer (EVC)

EVC is the maximum rational price a customer would pay for a product relative to their
next-best alternative:

```
EVC = Reference_Price + Differentiation_Value
```

Where:
- `Reference_Price` = what the customer currently pays for the next-best alternative
- `Differentiation_Value` = the incremental value your product delivers over that alternative
  (quantified as time saved × hourly rate, error reduction × cost per error, etc.)

EVC bounds the Path A formula, and the price is then capped at WTP_max, the willingness to pay
jtbd measured: a Path A price never exceeds either.

### Path A vs Path B — The JTBD Dependency

| Path | Activated when | Confidence | Formula |
|---|---|---|---|
| **Path A** | the price gate accepts a jtbd result in `.jtbd-market-discovery/results/` (person's run with none: `.jtbd/wtp-validation.json` (Path A only when it states a `period`)) | "validated" with customer data or published sources, else "estimated" | `min(WTP, max(FLOOR, min(EVC, REF + AI_Δ + MOAT_Δ)))` |
| **Path B** | No JTBD data | "estimated" | `max(FLOOR, min(WTP_max, BASE × AI_MULT × MOAT_MULT))` |

**The strategic implication:** Running `jtbd-market-discovery` before `pricing` replaces the multiplicative Path B formula
with an EVC-anchored Path A formula. This is the recommended workflow for any feature with
significant revenue potential.

### Opportunity Scores as Tier Signal

When `jtbd-market-discovery` has run, its opportunity scores inform tier placement in the
`package` skill:

- **High opportunity score** (8–10): Feature is addressing an underserved job → Leader or Killer placement, top tier
- **Medium opportunity score** (5–7): Feature is partially addressed → Leader placement, middle tier
- **Low opportunity score** (<5): Feature is adequately served by alternatives → Filler placement

### Where JTBD/ODI Appears in the Plugin

| Component | How it's used |
|---|---|
| Path A activation | `price` skill Step 2 gate: a jtbd result in `.jtbd-market-discovery/results/` (old fallback: `.jtbd/wtp-validation.json`, only when it states a `period`) |
| `PathAResult.evc` | EVC from `jtbd-market-discovery` data; it bounds the formula, and WTP_max caps the price |
| `PathAResult.value_signal` | the Path A price before the WTP_max cap; its excess over the price is headroom |
| `PathAResult.floor_advisory` | set when the margin floor is above WTP_max: the capped price is below the floor |
| `segment_signal` | Path B: the gap between VALUE_SIGNAL and WTP_max → recommendation to run JTBD. Path A: headroom above WTP_max, not a market gap |
| Opportunity score → tier | High-score outcomes → Killer/Leader; low-score → Filler |
| `pricing-auditor` agent | Imports `.jtbd-market-discovery/opportunity-scores.json` (else `.jtbd/opportunity-scores.json`) for audit context |

---

## How the Frameworks Connect

The five frameworks are not independent modules — they form a layered system with a
rational core and an emotional outer layer.

### The Rational Layer (v1.0 — implemented)

```
JTBD / ODI
  ↓ Provides: WTP₁ validation (the Path A cap), EVC, opportunity scores
  ↓ Activates: Path A

Amadeo (rational)
  ↓ Provides: AI_MULTIPLIER (speed × accuracy premium)
  ↓ Provides: MARGIN_FLOOR (cost / supply floor)
  ↓ Classifies: Legacy / Hybrid / AI-era features

Campbell / ProfitWell
  ↓ Provides: Value metric selection and validation
  ↓ Detects: Per-user antipattern

Helmer 7 Powers
  ↓ Provides: MOAT_MULTIPLIER (competitive premium)
  ↓ Triggers: Penetration advisory for Scale Economy moats

Ramanujam
  ↓ Provides: Killer/Leader/Filler classification
  ↓ Designs: Good/Better/Best tier architecture
  ↓ Detects: Feature Shock, Minivations, Hidden Gems, Undead Features
```

**The dual-path formula brings the rational layer together:**

```
Path A (JTBD + Amadeo + Helmer):
  RIGHT_PRICE = min(WTP_max, max(MARGIN_FLOOR, min(EVC, REFERENCE_PRICE + AI_VALUE_DELTA + MOAT_VALUE_DELTA)))

Path B (Amadeo + Helmer):
  RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_max, BASE × AI_MULTIPLIER × MOAT_MULTIPLIER))
  VALUE_SIGNAL = BASE × AI_MULTIPLIER × MOAT_MULTIPLIER  [unconstrained gap signal]
```

Then Ramanujam + Campbell complete the workflow:
- Which tier the feature belongs in (Ramanujam)
- What pricing axis the tier is charged on (Campbell)

---

### The Emotional Layer (Amadeo — v1.0 partial, v1.1 full)

The rational layer computes **what a feature is worth**. The emotional layer explains **why
customers actually pay** — and keep paying. These are different questions.

```
Pre-purchase moment (WTP₁ — v1.0):

  JTBD opportunity score
    → High importance + low satisfaction = Fear of inaction
      → Raises effective WTP₁ above neutral valuation

  AI_MULTIPLIER
    → Rational value premium from Speed × Accuracy
      → Justifies price above legacy alternative

  Pre-purchase Fear (of alternative, of missing out, of cost of inaction)
    → Emotional amplifier on WTP₁
    → Currently implicit in WTP elicitation; not scored separately


Post-purchase moment (WTP₂ — v1.1):

  Speed × Accuracy delivered consistently
    → Customer experiences life outcomes (time, focus, capability, balance)
      → Love accumulates as positive sentiment
        → Loyalty and stickiness develop
          → Retention WTP holds or rises

  Fear of regression / capability loss
    → Post-purchase Fear sustains WTP₂ even when Love is temporarily absent

  Love decay (product plateaus, accuracy drops, value stops compounding)
    → Sentiment erodes
      → Retention WTP becomes elastic
        → Churn probability rises
```

**The emotional interpretation of existing signals:**

| Plugin output | Rational reading | Amadeo emotional reading |
|---|---|---|
| `segment_signal` gap | Market WTP below value-justified price | Fear and Love not yet strong enough in this market segment to support the value-justified price |
| `accuracy < 0.8` fear signal | No AI premium justified | Product is generating Fear-of-product, which destroys Love and accelerates churn |
| `has_compounding = true` | Value grows with usage | Product will keep generating Love; retention WTP will hold |
| `has_compounding = false` | Value is static | Love may plateau; plan for WTP erosion at renewal |
| High Helmer switching cost | Competitive moat | Post-purchase Fear of loss is structurally high; supports retention WTP |

---

## v1.1 Roadmap — Retention Pricing

### The Gap

v1.0 answers: *"What should we charge to acquire a customer?"*

v1.1 will answer: *"What should we charge to keep a customer — and at what price does
retention break down?"*

These are different questions driven by different emotional mechanics. Acquisition pricing
is primarily about Fear. Retention pricing is primarily about Love and post-purchase Fear
together.

### What a `retention` Skill Would Model

A v1.1 `retention` skill would collect signals across two emotional dimensions:

**Love signals (WTP₂ support)**

| Signal | Proxy measure | What it indicates |
|---|---|---|
| Usage frequency | Sessions per week / month | Customer keeps coming back = Love still active |
| Feature depth | Number of distinct features used | Broad adoption = Love is broad, not fragile |
| Outcome verbalization | NPS comment analysis / qualitative | Can the customer describe the life outcomes they're getting? |
| Time-since-last-value | Days since last measurable outcome | Love needs fresh experiences; long gaps = decay risk |
| Expansion behavior | Seat additions / usage growth | Love is growing, not just holding |

**Fear signals (WTP₂ floor)**

| Signal | Proxy measure | What it indicates |
|---|---|---|
| Workflow dependency | Integrations, data volume, custom configurations | How painful would leaving be? |
| Switching cost estimate | Time + cost to migrate to alternative | High switching cost = high post-purchase Fear floor |
| Competitive alternatives | Are comparable alternatives improving? | Closing gap reduces Fear of missing out; pressure on Fear floor |
| Time since last price increase | Months since last renewal price change | Long gap = customer has normalized current price; increase may surface latent churn |

### The Retention WTP Formula (proposed)

```
LOVE_SCORE    = weighted average of Love signals (0–10)
FEAR_SCORE    = weighted average of Fear signals (0–10)

RETENTION_WTP = CURRENT_PRICE × (1 + LOVE_COEFFICIENT × LOVE_SCORE
                                   + FEAR_COEFFICIENT × FEAR_SCORE)
```

Where:
- `LOVE_COEFFICIENT` and `FEAR_COEFFICIENT` are calibrated per segment from churn data
- `RETENTION_WTP > CURRENT_PRICE` → pricing headroom; customer will absorb a price increase
- `RETENTION_WTP ≈ CURRENT_PRICE` → hold; any increase triggers churn consideration
- `RETENTION_WTP < CURRENT_PRICE` → churn risk; price is above what Love + Fear can currently sustain

### Churn Risk Signal

```
CHURN_RISK = HIGH   when LOVE_SCORE < 4 AND FEAR_SCORE < 4
CHURN_RISK = MEDIUM when LOVE_SCORE < 4 OR  FEAR_SCORE < 4
CHURN_RISK = LOW    when LOVE_SCORE ≥ 6 AND FEAR_SCORE ≥ 4
```

### Love Replenishment Recommendations

The v1.1 `retention` skill would also recommend specific product actions to restore Love
when it is decaying:

- **Low usage frequency** → Proactive re-engagement with new Speed × Accuracy use cases
- **Low outcome verbalization** → Customer success intervention to make outcomes explicit
- **Plateaued feature adoption** → Surface underused features that could generate new Love
- **Long time-since-last-value** → Trigger an outcome delivery event (automated summary,
  proof-of-value report, ROI statement)

### How v1.1 Connects to v1.0

```
v1.0 output:
  RIGHT_PRICE (acquisition) → the price to acquire a customer

v1.1 input:
  RIGHT_PRICE (acquisition) + LOVE_SCORE + FEAR_SCORE
    → RETENTION_WTP (renewal) → the price at which the customer renews vs. churns
    → CHURN_RISK signal
    → Love replenishment recommendations
```

The two-WTP structure forms a complete pricing lifecycle: acquire at the right price,
then sustain at the right price by continuously earning the Love that justifies it.

---

## Asking Questions About the Frameworks

If you want to understand how a specific pricing decision was made, ask directly:

```
"Why is my feature classified as Hybrid instead of AI-era?"
"How was the MOAT_MULTIPLIER of 1.8 calculated?"
"Why is my value metric not Campbell-approved?"
"What would need to change for Path A to activate?"
"Why is the AI_MULTIPLIER capped at 5× for this feature?"
"What does the segment_signal gap of $133 mean strategically?"
"Why does my Scale Economy moat get a 1.0 multiplier instead of higher?"
"Is my WTP₁ acquisition price sustainable as a WTP₂ retention price?"
"What does it mean that has_compounding is false for my AI feature?"
"How do Love and Fear apply to my specific product's churn rate?"
```

The plugin is designed to explain its reasoning. Every output includes the inputs, the path
taken, and the formula used — so the pricing recommendation is always auditable.

*See also: `README.md` for usage examples, `SKILL.md` for command reference.*

---

*See also: `README.md` for usage examples, `SKILL.md` for command reference.*
