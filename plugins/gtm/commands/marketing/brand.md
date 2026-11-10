---
description: Build brand identity, voice, positioning, and StoryBrand narrative from real product capabilities
allowed-tools: ["Read(*)", "Write(*)", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "Bash(date *)", "Bash(git rev-parse *)", "Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *)", "mcp__canva__search_designs", "mcp__canva__generate_design"]
---

# /gtm:marketing:brand

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. The permission rule matches only that command line, so inline code (`python3 -c`, `node -e`, a heredoc) and scripts of your own fail. Write each file with the Write tool.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask for a number or free text in one chat message. Offer only options that are real values, because an option such as "Type amount" gives the person no value to pick.

## Purpose

Build a complete brand identity system grounded in actual product capabilities — not generic platitudes. This command runs five frameworks in sequence (Golden Circle → Ries & Trout → StoryBrand → Aaker → Pine) in this session, and it dispatches no agent. It produces a messaging hierarchy that survives both creative scrutiny and the Truth Tier audit of step 10. Every claim in brand output must trace back to a verifiable product capability.

## Usage

```
/gtm:marketing:brand
/gtm:marketing:brand --product-doc path/to/product-brief.md
/gtm:marketing:brand --rerun         # overwrite existing brand artifacts
```

## Inputs

Ask only for an input the run does not have yet, one question at a time:

- AskUserQuestion [q: product_description]: "What does the product do, and who uses it?" A plugin run with no answer stops and writes its result file with the halt gap.
- AskUserQuestion [q: target_customer]: "Which customers is the brand for?"
  - **Default:** when nobody answers, the run chooses the target customer from the product description.
- AskUserQuestion [q: product_capabilities]: "What can the product do today that a customer could check?" With no answer, the run states no proof point.
- AskUserQuestion [q: differentiators]: "What makes the product different from what customers use today?" With no answer, the run writes no positioning statement.

## Process

0. **Read the start time and the version** — run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time. The result file needs both.

1. **Load `gtm-context.json`** — extract `product_capabilities`, `positioning_differentiators`, `icp`, and any existing brand artifacts. If `gtm-context.json` is missing, ask for a product description via `AskUserQuestion` [q: product_description] and scaffold minimal context.

2. **Apply Sinek Golden Circle** — surface WHY (core purpose and belief), HOW (differentiated approach), and WHAT (product and features). WHY must be grounded in founder intent or customer transformation, not revenue goals.

3. **Apply Ries & Trout Positioning** — define the category the product will own or create. If the category is crowded, identify the specific niche or attribute to own. Output: single-sentence positioning statement in the format "For [ICP], [Product] is the [category] that [differentiator]."

4. **Apply Miller StoryBrand** — cast the customer as hero, the product as guide. Build the 7-part SB7 narrative:
   - Character (customer with a goal)
   - Problem (external, internal, philosophical)
   - Guide (your brand as trusted advisor)
   - Plan (clear 3-step process)
   - Call to Action (direct and transitional CTA)
   - Avoiding Failure (stakes)
   - Achieving Success (transformation)

5. **Apply Aaker Brand Identity System** — define brand as product, organization, person, and symbol. Identify core identity (2-3 attributes) and extended identity (supporting associations). Establish brand personality across Aaker's five dimensions.

6. **Apply Pine Experience Economy** — place the brand experience on the value ladder: commodity → goods → services → experiences → transformation. Name the highest rung the product reaches today and the specific transformation customers undergo.

7. **Build messaging hierarchy** — synthesize all frameworks into four levels:
   - **Tagline** (≤ 8 words, category-owning)
   - **Value proposition** (one sentence, JTBD-anchored)
   - **Elevator pitch** (3 sentences: problem → solution → proof)
   - **Full narrative** (paragraph-length StoryBrand script)

8. **Write output artifacts:**
   - `brand-identity.json` — structured brand identity with all framework outputs
   - `messaging-architecture.json` — full messaging hierarchy with variants by ICP segment
   - `voice-guide.md` — tone, vocabulary, example phrases to use and to avoid, brand personality
   - `purpose-statement.md` — Golden Circle WHY in narrative form
   - `storybrand-script.md` — complete SB7 narrative ready for website homepage

9. **Generate Canva assets** (if connected) — search for matching brand templates and generate a visual mood board or initial brand kit.

10. **Audit all artifacts in this session** — Read `${CLAUDE_PLUGIN_ROOT}/commands/audit.md` with the Read tool and follow its steps 2 to 9 on every artifact of step 8, one artifact after the other. That is: classify every claim, block Tier 5 claims, flag Tier 4 claims for rewording, and write `truth-tier-audit.json` with the `integrity_score` and the cleaned artifacts. Do not dispatch an agent for this step, because this command has no `Agent` grant.

11. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/brand-agent.md` with the Read tool and follow its `## Result file` section, in every run.

## Output Artifacts

- `brand-identity.json` — full identity system (Golden Circle + Aaker + Pine outputs)
- `messaging-architecture.json` — tagline, value prop, elevator pitch, narrative
- `voice-guide.md` — brand voice, tone, vocabulary rules
- `purpose-statement.md` — WHY statement in long-form narrative
- `storybrand-script.md` — SB7 script for homepage / hero section
- `truth-tier-audit.json` — integrity validation results
