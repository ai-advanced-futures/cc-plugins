# Pipeline inputs

This file lists the input fields of each phase of the pipeline. The command `/corporate-development:pipeline` asks for these fields. The command `pipeline` gives each phase agent its fields from `pipeline_inputs.json`.

## Slug rule

The slug is the folder name of the target. Make it from the company name:

```
slug = company_name.lower().replace(" ", "-").replace("/", "-").replace("_", "-")
```

Then remove each character that is not `a-z`, `0-9` or `-`. Join each run of `-` into 1. Remove a `-` at the start and at the end. Cut the slug to 64 characters, and remove a `-` at the end again. Examples: "Acme Corp" gives `acme-corp`. "123/XYZ Holdings" gives `123-xyz-holdings`. "Acme, Inc." gives `acme-inc`. Use the same slug in all paths of the same target.

When the result is empty, stop with this message and ask for the name again: `the company name gives no slug: write it with the letters a-z or the digits 0-9`.

Then check the slug: it must match `re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", slug)`. The first character must be a letter or a digit, so the check also refuses `.` and `..`. When the check fails, stop before you write a file or dispatch an agent, and ask for the name again, as for an empty slug.

## Files

| Path | Holds |
|---|---|
| `.corporate-development/targets/<slug>/pipeline_inputs.json` | The inputs of all phases. The file holds 1 object for each phase: `{"phase_0": {...}, "phase_1": {...}, ...}`. The command gives a phase agent only its own object. `company_name` is in the object of each phase that needs it: the buyer in `phase_0`, the target in the other phases. |
| `.corporate-development/targets/<slug>/phase_<N>_<name>/` | The artifacts of phase N. |
| `.corporate-development/targets/<slug>/handoffs/phase_<N>_handoff.json` | The handoff of phase N. |
| `.corporate-development/targets/<slug>/handoffs/phase_<N>_questions.md` | The questions of phase N, when an input is missing. |

## Intake rules

- Ask 1 phase at a time.
- Ask not more than 4 questions in 1 call.
- Give a scale or a list of choices in each question.

## Phase 0: Acquisition Readiness

Required:

- `company_name`: the name of the company that buys.
- `ceo_readiness`: an object with `attitude_score`, `aptitude_score` and `action_score`. Each score is from 0 to 10. Attitude is growth mindset, character and resilience. Aptitude is strategic thinking and leadership. Action is the record of execution and results.
- `strategic_targets`: an object with the acquisition criteria. It holds the industry focus, the deal size range, the capability gaps and the integration philosophy.
- `organizational_capacity`: an object with the headcount of the M&A team, the integration experience and the bandwidth.
- `financial_readiness`: an object with the available capital, the debt capacity and the preferred valuation method.
- `governance`: an object with the M&A experience of the board, the approval thresholds and the risk tolerance.

A hard requirement that is not met gives NO_GO: a CEO average below 7.0, no strategic targets, or no committed capital.

| Readiness score | Gate |
|---|---|
| 80 to 100 | GO. Go on to deal sourcing. |
| 65 to 79 | CONDITIONAL. Go on with a plan for moderate remediation. |
| 50 to 64 | CONDITIONAL. Go on only with significant organizational work committed. |
| Below 50 | NO_GO. The company is not ready for M&A. |

## Phase 1: Deal Sourcing

Required:

- `target_markets`: a list of market segments, for example `["SaaS", "FinTech"]`.
- `strategic_focus`: the acquisition strategy.
- `budget_range`: the acquisition budget, for example `"$5M-$20M"`.

Optional: `capability_gaps`, a list of capabilities that the buyer wants to add.

## Phase 2: Target Assessment

Required: `company_name`, the name of the target.

Required, at least one of:

- `industry` or `target_industry`: the industry of the target.
- `strategic_motivation`, `motivation` or `acquisition_motivation`: the reason for the acquisition.

Optional: `revenue`, `employee_count`, `founding_year`, `competitive_advantages`, `red_flags`.

## Phase 3: Operational Due Diligence

Required: `company_name`, the name of the target.

Give at least one dimension object. Give all 5 for a full assessment. Each dimension holds scores from 0 to 100.

- `team`: leadership depth, retention rate, key person risk, bench strength.
- `technology`: stack modernity, architecture quality, technical debt, development velocity, infrastructure.
- `product`: product quality, roadmap clarity, feature completeness, customer satisfaction, product-market fit.
- `operations`: process maturity, workflow efficiency, scalability, automation, quality control.
- `market_position`: competitive standing, moat strength, differentiation, market alignment.

With no dimension object, the phase returns CONDITIONAL and sets `phase_3_not_assessed` to true.

## Phase 4: Financial Due Diligence

Required:

- `company_name`: the name of the target.
- `income_statement`: an object with `revenue`, `cogs`, `operating_expenses`, `interest_expense` and `tax_expense`. Optional: `depreciation`, `amortization`, `owners_compensation`, `period_start` and `period_end`.
  `cogs` is the cost of goods sold. The dates are ISO dates (the default is the year 2025). Phase 4 computes the net income from these numbers, so give no net income. Phase 4 also reads the other names of a key that `StatementParser.INCOME_STATEMENT_SYNONYMS` gives, for example `cost_of_goods_sold` for `cogs`. When the object has 2 names of 1 key, the name of the list above wins.
- `balance_sheet`: an object with 14 numeric line items: `cash`, `accounts_receivable`, `inventory`, `other_current_assets`, `ppe_net`, `intangibles`, `other_assets`, `accounts_payable`, `accrued_expenses`, `current_debt`, `other_current_liabilities`, `long_term_debt`, `other_liabilities`, `equity`. Optional: `as_of_date`.
  `as_of_date` is an ISO date (the default is 2025-12-31).

Optional, and they make the result more exact:

- `ownership`: the owner name and the compensation.
- `prior_year_revenue`: for the growth rate.
- `customer_metrics`: CAC, LTV, churn rate, NPS.

## Phase 5: Integration Planning

The command `pipeline` builds these inputs from the handoffs of Phase 3 and Phase 4. Required:

- `company_name`: the name of the target.
- `target_company`: the name of the company that buys.
- `operational_health_score`: from `next_phase_inputs.operational_health` of Phase 3.
- `financial_health_score`: from `next_phase_inputs.financial_health` of Phase 4.

Optional:

- `integration_scope`: FULL, PARTIAL or MINIMAL.
- `timeline_constraints`: fixed deadlines.

## Phase 6: Deal Decision

Phase 6 gets the handoffs of Phase 0 to Phase 5 as a JSON array. It needs no other input.
