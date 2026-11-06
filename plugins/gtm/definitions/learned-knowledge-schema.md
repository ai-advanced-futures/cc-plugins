# learned_knowledge — Schema Reference

`learned_knowledge` is the field intelligence layer of `gtm-context.json`. It holds human-provided
competitive, customer, and sales data ingested by the knowledge-agent and stored in the GTM context.

## Schema

```json
{
  "learned_knowledge": {
    "customer_language": {
      "<segment>": "<string: actual language customers use to describe their pain>"
    },
    "winning_phrases": [
      "<string: phrases that reliably unlock deals or resonate in discovery>"
    ],
    "objections": [
      {
        "objection": "<string: the objection text>",
        "frequency": "<low|medium|high>",
        "deal_kill_risk": "<low|medium|high>",
        "response": "<string: feel/felt/found response>"
      }
    ],
    "win_patterns": [
      "<string: conditions or phrases associated with closed-won deals>"
    ],
    "loss_patterns": [
      "<string: conditions or phrases associated with closed-lost deals>"
    ],
    "competitor_intel": {
      "<competitor_name>": {
        "strengths": ["<string>"],
        "weaknesses": ["<string>"],
        "pricing_signals": "<string>",
        "displacement_plays": ["<string>"]
      }
    },
    "channel_benchmarks": {
      "<channel>": {
        "cpl": "<number|null>",
        "conversion_rate": "<number|null>",
        "source": "<string: data source or 'field_estimate'>"
      }
    }
  }
}
```

## Field Rules

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `customer_language` | object | No | Keyed by ICP segment; used by brand-agent for voice/tone |
| `winning_phrases` | array of strings | No | Sales-agent uses for SPIN and MEDDPICC; overrides framework defaults |
| `objections` | array of objects | No | Tiered by `frequency` + `deal_kill_risk`; used by sales-agent |
| `win_patterns` | array of strings | No | Overrides Decision Criteria defaults in MEDDPICC |
| `loss_patterns` | array of strings | No | Flags criteria we lose on; feeds sales-agent competitive analysis |
| `competitor_intel` | object | No | Keyed by competitor name; used by sales-agent Challenger deck |
| `channel_benchmarks` | object | No | Keyed by channel name; used by marketing-agent with `source` attribution |

## Truth Tier Assignment for Ingested Data

Field intelligence ingested from real documents (call recordings, CRM exports, customer interviews)
is assigned higher truth tiers than strategic documents. See `definitions/truth-tiers.md` for
the full tier system and `agents/knowledge-agent.md` for per-file-type tier assignment rules.

| Data Source | Default Tier | Reason |
|-------------|--------------|--------|
| Call recordings (`.vtt`) | Tier 1 (SHIPPED) | Customer said it on record |
| CRM exports (`.json`) | Tier 1 (SHIPPED) | System-of-record data |
| Win/loss write-ups (`.md`) | Tier 2 (IN_FLIGHT) | Post-hoc analysis, not raw data |
| Strategy decks (`.pdf`) | Tier 3 (COMMITTED) | Intended direction, not actuals |

## High-Confidence Merge Rule

When the knowledge-agent merges data from multiple sources, a field is marked `high_confidence: true`
when **3 or more independent sources** corroborate the same signal. Below 3 sources, the field is
retained without the high_confidence flag (but not discarded).

**Example:** If 3 separate call recordings all mention "integration with Salesforce" as a win reason,
`winning_phrases` gets `"Salesforce integration"` with `high_confidence: true`.

## Python Reference

- Ingestion: `scripts/document_ingester.py` — `DocumentIngester.ingest()` → populates `learned_knowledge`
- Extraction patterns: `scripts/document_ingester.py::KEYWORD_PATTERNS`
- Merge algorithm: `agents/knowledge-agent.md` Step 5 (merge + deduplication)
