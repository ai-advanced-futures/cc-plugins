---
name: value-ip:ip-extraction
description: Methodology for identifying and articulating IP claims that survive all 4 framework tests
---

# IP Extraction Methodology

## Purpose

Identify, articulate, and validate Intellectual Property (IP) claims from any artifact. An IP claim is genuine only if it survives all four framework lenses at the same time.

**Definition of IP in this context:** Not just patents or trade secrets — any unique approach, algorithm, methodology, data structure, workflow, or insight that:
1. Creates structural competitive advantage (Helmer)
2. Represents a genuinely new value creation (Blue Ocean)
3. Has disruptive potential incumbents cannot easily counter (Christensen)
4. Is Core differentiation, not commodity context (Moore)

## Types of IP Worth Capturing

### Algorithmic IP
- Novel calculation methods, scoring models, formulas
- Unique approaches to processing or analysis
- Custom heuristics or decision trees

### Methodological IP
- Unique workflows or processes
- Novel frameworks or analytical lenses
- Proprietary research or validation methods

### Architectural IP
- System designs that create structural advantages
- Integration patterns competitors cannot replicate
- Data models or schema designs that encode unique insight

### Knowledge IP
- Accumulated expertise encoded in systems or processes
- Unique data assets or training sets
- Industry-specific ontologies or taxonomies

## Extraction Protocol

### Step 1: Identify Candidates
Scan the artifact for elements that seem novel, proprietary, or unusually specific:
- Is there a formula, score, or algorithm described?
- Is there a workflow that competitors would need to invent from scratch?
- Is there a unique combination of existing ideas that creates new value?
- Is there data, a model, or accumulated knowledge that's hard to replicate?

### Step 2: Four-Framework Survival Test
For each candidate, apply all four tests:
- **Helmer:** Does this create a structural barrier (at least one power)?
- **Blue Ocean:** Does this create new value (at least one Create/Raise element)?
- **Christensen:** Is this tied to a disruptive trajectory or genuine JTBD?
- **Moore:** Is this Core (would customers choose you BECAUSE of this)?

A candidate is a genuine IP claim only if it passes all four tests.

**Numeric per-framework pass thresholds (must all be met):**
- **Helmer:** At least one power with individual score ≥ 3
- **Blue Ocean:** At least one Create or Raise element with overall score ≥ 3
- **Christensen:** Overall framework score ≥ 3
- **Moore:** core_percentage > 60 AND overall score ≥ 3

### Step 3: Articulate the Claim
For each surviving claim:
- **Name:** 2-5 word memorable name
- **Description:** One sentence — what it does and why it's unique
- **Helmer Power:** Which power does this create?
- **Blue Ocean Value:** What does this eliminate or create?
- **Disruption Type:** Disruptive / Sustaining / New Market
- **Core or Context:** CORE (protectable) or CONTEXT (commodity)
- **Confidence:** High / Medium / Low

### Step 4: Distinguish from Features
Not all valuable features are IP:
- A useful feature that competitors already offer is not IP
- A useful feature embedded in a unique process or data = potential IP

**Replication timeline thresholds:**
- Fast red-flag screen: if a well-funded competitor could replicate this in < 3 months, it is almost certainly not IP — stop here.
- Full bar: IP requires that replication would take a well-funded competitor ≥ 18 months. Claims that survive the 3-month screen but fall below 18 months must still pass the Helmer replication-timeline scoring rubric to qualify as defensible IP.

## Red Flags (Claim Rejected)
- "We do X faster" — unless backed by unique process power (Helmer)
- "We combine A and B" — unless the combination creates fundamentally new value
- "We use AI" — AI is table stakes; the unique training data or feedback loop might be IP
- "We have a better UX" — UX is context unless it encodes unique knowledge
- "We've built this before" — experience alone is not IP without encoded process power

## Output Format

**Priority ordering required:** The IP claim record captures only the primary Helmer power (first in powers_found list) and the primary Blue Ocean Create element (first in create list). Framework agents order their findings by priority, most significant first.

```
IP CLAIMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Claim N]: [Name]
Description: [One sentence]
Helmer Power: [POWER_NAME]  ← list primary (most significant) power first
Blue Ocean Value: [what it creates or eliminates]  ← list primary Create element first
Disruption Type: [DISRUPTIVE / SUSTAINING / NEW_MARKET]
Core or Context: [CORE — protectable]
Confidence: [HIGH / MEDIUM / LOW]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
