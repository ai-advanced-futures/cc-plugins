# MEDDPICC — Canonical Definition

MEDDPICC is the qualification framework used to score sales pipeline opportunities.
A deal reaches SQL status only after MEDDPICC criteria have been confirmed through discovery.

## Criteria

| Letter | Criterion        | Question to Answer                                                           |
|--------|------------------|------------------------------------------------------------------------------|
| M      | Metrics          | What is the quantified business impact of solving this problem?              |
| E      | Economic Buyer   | Who has budget authority and will sign the contract?                         |
| D      | Decision Criteria| What factors will the buyer use to select a vendor?                          |
| D      | Decision Process | What is the exact approval process and timeline to close?                    |
| P      | Paper Process    | What legal, procurement, or security reviews are required before signing?    |
| I      | Implicated Pain  | What is the confirmed, urgent business pain driving the purchase decision?   |
| C      | Champion         | Who inside the account is actively advocating for our solution?              |
| C      | Competition      | Which competitors are being evaluated, and what is our differentiated edge?  |

## Usage in GTM Plugin

- `funnel-agent` applies MEDDPICC scoring when building SQL-stage pipeline entries
- `sales-agent` uses MEDDPICC during pitch narrative construction to pre-empt objections
- Score each criterion 0–2: 0 = unknown, 1 = partially confirmed, 2 = fully confirmed
- A deal is considered SQL when total MEDDPICC score ≥ 10 of 16

## Score Thresholds

| Score | Status                        |
|-------|-------------------------------|
| 0–5   | MQL only                      |
| 6–9   | SAL (accepted, not qualified) |
| 10–13 | SQL (qualified)               |
| 14–16 | High-confidence close         |
