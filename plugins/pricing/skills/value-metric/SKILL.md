---
name: value-metric
description: Select the right pricing axis (value metric) for a feature or product using Campbell's 3 criteria plus Amadeo's AI-era 4th criterion. Detects per-user pricing antipattern and recommends the metric that scales with Speed × Accuracy of Outcome.
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py *), Edit(/.pricing/**), Read(//**/skills/value-metric/value-metric.md)
---

# Value Metric — Select the Right Pricing Axis

Choose the billing unit that aligns price with the value customers actually receive.

## When to Use

- "What should we price on — per seat or per document?"
- "Is per-user pricing right for our AI assistant?"
- "What's the right pricing axis for our new feature?"
- "We're debating usage-based vs seat-based pricing"
- "How should we measure value for billing?"

## Assessment Framework

### Campbell's 3 Criteria

| Criterion | Test |
|-----------|------|
| **Alignment** | Does the metric scale with value delivered to the customer? |
| **Understandability** | Can customers explain the metric to their boss in one sentence? |
| **Growth alignment** | Does revenue grow as the customer gets more value? |

### Amadeo AI-Era 4th Criterion

- Does the metric scale with **Speed × Accuracy of Outcome**?
- For AI-era features, the metric must capture compounding value — not static seat count

### Per-User Antipattern Detection

Flags `per_user_antipattern: true` when:
- The feature's value does not scale with user count
- Adding users does not increase value generated

## Flow

1. Present 2–4 candidate value metrics
2. Score each against Campbell 3 criteria (0–4 score)
3. Apply Amadeo AI-era test (4th criterion)
4. Detect per-user antipattern
5. Recommend approved metric or flag failure with alternatives
6. Output `.pricing/value-metric.json`

## Output

`.pricing/value-metric.json` — approved value metric, Campbell score (0–4), per-user antipattern flag, recommended pricing axis.

## Cross-References

- **Reads from:** the jtbd graph, through `brain_read.py outcomes` (if it holds data — informs metric selection). When `pricing:price` runs this skill, take jtbd data only from what its price gate accepted, and none when the gate accepted nothing.
- **Next step:** `/pricing:price` — use selected metric when computing RIGHT_PRICE
- **Orchestrated by:** `pricing-auditor` and `new-offering-pricer` agents
- **Full prompt:** Read `${CLAUDE_SKILL_DIR}/value-metric.md` before you start.
- **Plugin root:** `${CLAUDE_PLUGIN_ROOT}`
