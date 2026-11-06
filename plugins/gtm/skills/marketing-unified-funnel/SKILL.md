---
name: marketing-unified-funnel
description: Design the MQL→SAL→SQL handoff system and revenue math connecting marketing and sales
---

# Unified Revenue Funnel

## Purpose

The handoff between marketing and sales is where most revenue is lost. This skill designs the MQL→SAL→SQL handoff with clear criteria, SLAs, and revenue math — ensuring both teams work from the same definition of a good lead.

## Handoff Design

### MQL → SAL Handoff

**MQL Entry Criteria** (example — customize per business):
- Matches ICP firmographic (industry + company size + role)
- Has ≥ 2 intent signals (pricing page visit, demo request, content download)
- Has not been previously rejected by sales

**SAL Definition**: An MQL that sales has formally accepted as worth pursuing — before qualification has been confirmed through discovery.

**Sales Acceptance SLA**: Sales must accept or reject MQL within 24 business hours of assignment.

**Rejection Criteria** (must be documented — no silent drops):
- Does not match ICP
- Already a customer
- Duplicate of existing deal

### SAL → SQL Handoff

**SQL Definition**: A SAL where a discovery meeting has confirmed budget, authority, need, and timeline (BANT or MEDDPICC equivalent).

**First Outreach SLA**: First outreach within 4 business hours of SAL assignment.

### Revenue Math

```
Monthly Revenue = Visitors × Signup_Rate × Activation_Rate × MQL_Rate × SQL_Rate × Close_Rate × ACV/12
```

Run this forward (projection) and backward (what do we need at each stage to hit revenue target?).

## Output
- `funnel-metrics.json` (complete, with handoff SLAs)
- `handoff-sla.md` (the signed agreement between marketing and sales)
- `revenue-math.md` (forward and backward projection)
