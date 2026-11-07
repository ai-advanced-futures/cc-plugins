---
description: Truth Tier audit — classify every claim in a marketing artifact against the Truth Tier system
allowed-tools: ["Read(*)", "Write(*)", "Glob(*)", "Grep(*)", "AskUserQuestion"]
---

# /gtm:audit

## Purpose

Run a Truth Tier audit on any GTM artifact. This command reads every claim in the file, classifies it against the Truth Tier system (Tier 1 through Tier 5), removes or flags unacceptable claims, and returns both a cleaned artifact and a structured audit report with an integrity score.
The rules are in two files. Read both before you start:

- `${CLAUDE_PLUGIN_ROOT}/definitions/truth-tiers.md` — the five tiers, the rules that assign a tier, and the rules for superlatives and numbers
- `${CLAUDE_PLUGIN_ROOT}/definitions/integrity-score.md` — the integrity score formula and its thresholds

## Usage

```
/gtm:audit path/to/artifact.md
/gtm:audit path/to/campaign-plan.json
/gtm:audit --all                          # audit all GTM artifacts in the working directory
/gtm:audit path/to/file.md --strict       # fail if integrity_score < 0.85
```

## Process

1. **Accept artifact path as input** — the user provides a path to a `.json` or `.md` marketing file. If no path is provided, ask with `AskUserQuestion` which artifact to audit. If `--all` is passed, glob for all `.md` and `.json` files in the `gtm-output/` directory.

2. **Extract all claims from the artifact** — parse the file and extract every factual claim, including:
   - Quantified statements ("reduces time by 40%", "used by 500+ companies")
   - Superlatives ("the best", "the only", "the fastest", "industry-leading")
   - Comparative claims ("better than", "unlike competitors", "outperforms")
   - Future-tense-as-present ("will help you", "you'll see results in days")
   - Unattributed statistics ("studies show", "research confirms", "experts agree")
   - ROI or outcome promises ("you'll save $X", "increase revenue by Y%")

3. **Classify each claim by the rules of `truth-tiers.md`** — give each claim one tier:

   | Tier | Label | Action |
   |------|-------|--------|
   | **Tier 1** | SHIPPED — live in production, customers use it | Approved — assert as fact, cite source |
   | **Tier 2** | IN-FLIGHT — under active development | Approved — use "coming soon" language |
   | **Tier 3** | COMMITTED — on the roadmap with budget and sponsor | Approved with qualifier ("planned for [timeframe]") |
   | **Tier 4** | STRATEGIC INTENT — direction only, no plan | Flagged — rewrite with "we plan to explore" language |
   | **Tier 5** | SPECULATION — no evidence | Blocked — removed from artifact |

   A superlative or a quantified claim with no evidence or no source is Tier 5.

4. **Block Tier 5 claims** — remove all Tier 5 claims from the artifact. Log each removed claim in the audit report with the reason for removal.

5. **Flag Tier 4 claims** — mark each Tier 4 claim in the artifact with a required language fix. Provide a rewrite suggestion that uses the required language of its tier.

6. **Check for language issues** — scan for patterns that are problematic regardless of tier. These are advisory: they go in `language_issues` and leave the score as it is.
   - Superlatives without evidence ("the best", "world-class", "industry-leading") → require supporting data or removal
   - Unattributed quantified claims ("40% faster") → require a source citation or removal
   - Future-tense-as-present ("you will see") → rewrite as "designed to help you" or add qualifier
   - Competitor naming without factual basis → legal risk flag

7. **Calculate the integrity score by the formula of `integrity-score.md`** — `integrity_score = (total_claims - tier_5_blocked) / total_claims`, a number from 0.0 to 1.0. The total stays fixed when claims are blocked. With no claims, there is no score (the gap `no_claims` of `integrity-score.md`): write no `truth-tier-audit.json` and no cleaned file for that artifact, and tell the person that it holds no claim to check. Below 0.60 the artifact fails the floor. Set `floor_breached` to `true` and hold the artifact back, because most of its claims have no proof. With `--strict`, the artifact also fails below 0.85.

8. **Write `truth-tier-audit.json`** — structured audit report. The fields follow `${CLAUDE_PLUGIN_ROOT}/schemas/truth-tier-audit.json`:
   ```json
   {
     "artifact": "campaign-plan.json",
     "audited_at": "<ISO timestamp>",
     "integrity_score": 0.87,
     "blocked_count": 1,
     "claims": [
       { "text": "...", "tier": 5, "blocked": true, "language_issues": [], "suggested_fix": "..." }
     ]
   }
   ```

9. **Return cleaned artifact** — write the cleaned version of the artifact alongside the original, so the person can compare the two files. The cleaned file has all Tier 5 claims removed and all Tier 4 claims replaced with suggested rewrites.

## Output Artifacts

- `truth-tier-audit.json` — full audit report with claim classifications and integrity score
- `<original-name>-cleaned.md` or `<original-name>-cleaned.json` — cleaned artifact
