# Rule of 40

## Definition

The Rule of 40 score is revenue growth % plus a profit margin %. This plugin works it out with `scripts/rule_of_40.py` and grades it against a target of 40, 50 or 60 (default 40) on each margin given. A score equal to the target meets it.

## The two margins

- EBITDA margin: EBITDA / revenue x 100. Plain EBITDA counts stock-based pay as a cost; adjusted EBITDA adds it back.
- FCF margin: (operating cash flow - capital spending) / revenue x 100. Stock-based pay is not cash, so it is not subtracted.

The two margins differ by capital spending, stock-based pay, working capital, interest and tax. When they disagree at the target, the status is `split`.

## The ladder

| Bar | Source |
|-----|--------|
| 40 | Feld (2015): "The 40% rule is that your growth rate + your profit should add up to 40%." |
| 50 | No published benchmark found. A bar you set. |
| 60 | Vista Equity Partners (8 Jan 2026): "an emerging aspiration, not a universal baseline". |

## The weighted score

Weighted Rule of 40 = 1.33 × growth + 0.67 × EBITDA margin. The weights are a plugin convention; the weighted score is not graded.

## The 12-month gate

A product with 12 or fewer months of revenue is not graded: growth is not a year-on-year rate before the thirteenth month.

## The ICONIQ caution

When `arr` is under $25,000,000 the report prints:

Caution (ICONIQ): "we typically only begin to place real weight against Rule of 40 for companies with at least $25M ARR", because "exceptional year-over-year growth inflates Rule of 40 performance for early-stage companies" (ICONIQ, The ICONIQ Enterprise Five (2025 KPIs)).

## Reference lines

NRR and gross margin print as reference lines. They never enter the score, the status or a recommendation.

## Sources

- Brad Feld, The Rule of 40% For a Healthy SaaS Company, feld.com, 3 Feb 2015
- Vista Equity Partners, Rethinking Software Benchmarks in an AI-Driven Market, 8 Jan 2026
- ICONIQ, The ICONIQ Enterprise Five (2025 KPIs)
- Bessemer Venture Partners, The State of AI 2025, 13 Aug 2025
- Bessemer, The Rule of X, 2 Jan 2024
- Meritech Software Pulse, 14-August-2026 edition
