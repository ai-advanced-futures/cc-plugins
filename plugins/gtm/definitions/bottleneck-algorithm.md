# Bottleneck Detection Algorithm — Canonical Definition

## Algorithm

The bottleneck is the funnel stage with the lowest conversion rate. When two or more stages
share the lowest rate, the tie is broken by selecting the stage with the highest revenue impact
(monthly_volume × avg_deal_value), as that stage bleeds the most revenue per month.

```python
def find_worst(
    stages: dict[str, float],
    revenue_impact: dict[str, float] | None = None,
) -> str | None:
    """Return the stage key with the lowest conversion rate.

    Tie-breaker: if two+ stages share the lowest rate and revenue_impact is
    provided, select the stage with highest (monthly_volume × avg_deal_value).
    Returns None if stages dict is empty.
    """
    if not stages:
        return None
    min_rate = min(stages.values())
    worst = [k for k, v in stages.items() if v == min_rate]
    if len(worst) == 1:
        return worst[0]
    if revenue_impact:
        return max(worst, key=lambda k: revenue_impact.get(k, 0.0))
    return worst[0]  # deterministic fallback: first by dict insertion order
```

## Inputs

`stages` — dict mapping stage transition labels to conversion rates (0.0–1.0):

```python
{
    "visitors_to_signups": 0.12,
    "signups_to_activated": 0.45,
    "activated_to_mql": 0.05,    # ← this is the bottleneck (lowest rate)
    "mql_to_sal": 0.60,
    "sal_to_sql": 0.50,
    "sql_to_closed": 0.25,
}
```

`revenue_impact` (optional) — dict mapping stage labels to monthly revenue at risk:

```python
{
    "visitors_to_signups": 10000.0,   # monthly_volume × avg_deal_value
    "activated_to_mql": 50000.0,      # higher revenue at risk → selected on tie
}
```

## What NOT to use

Do NOT use "likelihood_of_fix" as a scoring factor — it is undefined, LLM-judgment-dependent,
and introduces non-determinism. The bottleneck algorithm must be reproducible given the same inputs.

## Interpretation

1. Fix the bottleneck first — it constrains the entire funnel
2. A 10% improvement at the bottleneck yields more revenue than a 10% improvement at any other stage
3. Re-measure after each intervention to find the new bottleneck

## Implementation

`scripts/funnel_analyzer.py` — `BottleneckDetector.find_worst(stages, revenue_impact)` implements this algorithm.
