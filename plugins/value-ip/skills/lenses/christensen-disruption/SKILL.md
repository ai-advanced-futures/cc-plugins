---
name: value-ip:assess-disruption
description: Apply Christensen's Disruption Theory and JTBD lens to classify innovation type
---

# Christensen Disruption Analysis Lens

## Purpose

Classify whether the artifact represents disruptive, sustaining, or new-market innovation using Clayton Christensen's Disruption Theory and Jobs-to-be-Done framework.

**Core thesis:** Disruption is a process, not a product. It starts by serving overlooked customers with a simpler, cheaper solution — then moves upmarket. Incumbents are rationally irrational to ignore it.

## Disruption Types

### Disruptive Innovation
Targets overlooked or overserved customers with a simpler, cheaper, more accessible solution.
- **Low-end disruption:** Overserved customers who want "good enough" at lower cost
- **New-market disruption:** Non-consumers who had no alternative
- Incumbents flee upmarket rather than fight — this is rational: it makes short-term sense
- Eventually moves upmarket and overtakes incumbents

### Sustaining Innovation
Makes a good product better — targets existing customers with better performance.
- Incumbents excel at sustaining innovation
- Is not disruptive: it improves the existing value network
- Still valuable, but not structurally differentiated by disruption

### New Market Creation
Creates an entirely new category where none existed before.
- Not just a better product — a new job being done
- Often dismissed by incumbents as a toy or niche

## Jobs to be Done (JTBD)

The unit of analysis is the JOB, not the customer or product:
- **Functional job:** What outcome does this accomplish?
- **Emotional job:** How does this make the user feel?
- **Social job:** How does this affect how others see them?

Signs of a strong JTBD:
- Customers were "hiring" inadequate alternatives before
- The job has been underserved or ignored
- Progress = completion of the job, not feature satisfaction

## Incumbent Vulnerability Assessment

Incumbents are most vulnerable when:
1. The disruptive solution is initially inferior on their primary metric
2. They are serving customers who demand ever-higher performance
3. Their business model cannot profitably serve the disrupted segment
4. They have financial incentives to flee upmarket

## Analysis Protocol

### Step 1: Identify the Job
What job does this artifact hire the solution to do?
- Who is "hiring" it and why?
- What were they doing before?
- What's the functional/emotional/social job?

### Step 2: Classify Innovation Type
- Does it target overserved customers? → Low-end disruption
- Does it serve non-consumers? → New-market disruption
- Does it make existing products better? → Sustaining
- Does it create new behavior? → New market

### Step 3: Incumbent Vulnerability
- Can incumbents profitably respond?
- Would copying this damage their existing business?
- Are they rationally incentivized to ignore this?

### Step 4: Score Output (1-5)
1 = Pure sustaining innovation, incumbents will respond
2 = Sustaining with some efficiency gains
3 = Clear JTBD focus, early disruption signals
4 = Strong low-end or new-market disruption pattern
5 = Classic disruptive trajectory incumbents cannot rationally counter

## Output Format

```
CHRISTENSEN ANALYSIS
Job to be Done: [statement]
Disruption Type: DISRUPTIVE / SUSTAINING / NEW_MARKET
Target Segment: [who is being targeted, overserved or underserved?]
Incumbent Vulnerability: [can they respond? at what cost?]
Score: X/5
Verdict: [text]

DEBATE POSITION:
My primary argument: [strongest claim]
My biggest concern: [what weakens this]
```
