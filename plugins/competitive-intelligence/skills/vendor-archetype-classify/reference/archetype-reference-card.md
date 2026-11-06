# Vendor Archetype Reference Card

Source: JustKeenAI Agentic Pricing in B2B SaaS v2.1, Chapter 1 ("Five vendor
archetypes in market today") + Chapter 2 terminal patterns.

## The 7 signals (extraction rubric)

| Signal | Means |
|---|---|
| `has_outcome_metric` | per-resolution / per-conversation / per-case / per-outcome charge |
| `has_platform_fee_floor` | six-figure platform fee or annual minimum floor |
| `has_seat_price` | per-user / per-seat subscription |
| `has_usage_meter` | metered API / credits / per-action |
| `passthrough_dominant` | dominant charge is raw token / per-ACU pass-through |
| `labor_anchored` | seat anchored to displaced professional-labor cost (>$1000/seat vertical) |
| `bounded_agent_surface` | amplifier multiplier structurally bounded (<5x): search / notetaking |

## The 5 archetypes

| Archetype | Anchor vendors | Best-in-class pattern (Chapter 2) |
|---|---|---|
| `pure_outcome_absorbed` | Intercom Fin | Pure per-resolution at scale; upgrade → add platform floor (A.3) |
| `hybrid_platform_outcome` | Sierra, Decagon, Cresta | Per-outcome + quality SLA + tier floor (B.2) |
| `pure_per_seat` (vertical_anchor) | Harvey, Hebbia, EvenUp | Labor-anchored per-seat (C.2) |
| `pure_per_seat` (bounded_surface) | Perplexity Enterprise, Notion AI | Bounded-surface flat per-seat |
| `hybrid_seat_meter` | Writer, Glean | Lite/Pro seat + metered API (C.3/A.2) |
| `pure_passthrough` | Cursor, GitHub Copilot 2026, Devin | Tiered hybrid + mandatory spend cap (E.2/E.3) |
