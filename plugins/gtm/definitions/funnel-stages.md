# Revenue Funnel Stages — Canonical Definition

Canonical B2B SaaS funnel stage order:

```
Visitor → Signup → Activated → MQL → SAL → SQL → Closed Won
```

## Stage Definitions

| Stage      | Definition                                                                                  | Owner      |
|------------|---------------------------------------------------------------------------------------------|------------|
| Visitor    | Anonymous user who has visited the product or marketing site                                | Marketing  |
| Signup     | Visitor who has created an account or submitted a lead form                                 | Marketing  |
| Activated  | Signup who has completed the core activation event (product-defined)                        | Product    |
| MQL        | Activated user who matches ICP firmographic + has ≥ 2 intent signals                       | Marketing  |
| SAL        | MQL that sales has formally accepted as worth pursuing (before discovery has confirmed fit)  | Sales      |
| SQL        | SAL where discovery has confirmed budget, authority, need, and timeline (BANT/MEDDPICC)    | Sales      |
| Closed Won | SQL where contract is signed and revenue is recognized                                      | Sales      |

## Handoff Order

**Canonical order: MQL → SAL → SQL** (not MQL → SQL → SAL)

- **MQL → SAL**: Marketing hands off to sales; sales accepts or rejects within 24 business hours
- **SAL → SQL**: Sales runs discovery; confirms fit using BANT or MEDDPICC criteria
- **SQL → Closed**: Sales executes close plan

## Revenue Math Formula

```
Monthly ARR = Visitors × Signup_Rate × Activation_Rate × MQL_Rate × SQL_Rate × Close_Rate × (ACV / 12)
```

Note: When SAL rate is tracked separately, insert between MQL_Rate and SQL_Rate.

## Bottleneck Identification

The bottleneck is the stage with the lowest conversion rate. Fix the bottleneck first — improvements
elsewhere are amplified by the bottleneck and will not move the revenue needle until it is resolved.

See `bottleneck-algorithm.md` for the detection algorithm.
