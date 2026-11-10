---
description: Build launch plan and go-to-market campaign with channel strategy, content calendar, and MQL criteria
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "Bash(date *)", "Bash(git rev-parse *)", "Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *)", "mcp__ahrefs__get_keyword_ideas", "mcp__ahrefs__get_search_volume", "mcp__canva__generate_design", "mcp__canva__autofill_template", "mcp__notion__notion-create-page", "mcp__slack__slack_post_message"]
---

# /gtm:marketing:launch

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. The permission rule matches only that command line, so inline code (`python3 -c`, `node -e`, a heredoc) and scripts of your own fail. Write each file with the Write tool.
Run each agent you dispatch in the foreground and wait for it to finish, because the result file is written after the agent ends.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask for a number or free text in one chat message. Offer only options that are real values, because an option such as "Type amount" gives the person no value to pick.

## Purpose

Build a complete go-to-market launch plan — channel strategy, content calendar, demand gen programs, and MQL criteria — anchored to brand positioning and the beachhead segment identified through Moore's Technology Adoption Lifecycle. Every channel recommendation is tied to a specific ICP segment and funnel stage. MQL criteria are defined precisely so sales and marketing share a single definition of a qualified lead.

## Usage

```
/gtm:marketing:launch
/gtm:marketing:launch --launch-date 2026-04-01
/gtm:marketing:launch --beachhead-only     # focus only on beachhead segment
```

## Inputs

Ask only for an input the run does not have yet, one question at a time:

- AskUserQuestion [q: product_description]: "What does the product do, and who uses it?" A plugin run with no answer stops and writes its result file with the halt gap.
- AskUserQuestion [q: target_customer]: "Which customers should the launch win first?"
  - **Default:** when nobody answers, the run chooses the beachhead segment from the product description.
- AskUserQuestion [q: self_serve]: "Can a customer sign up and reach the product's first value without talking to sales?" With no answer, the run names no growth motion.
- AskUserQuestion [q: channels]: "Which channels will you use to reach those customers?"
  - **Default:** when nobody answers, the run chooses 3 to 5 channels from step 5's list for the target customer.
- AskUserQuestion [q: year_one_targets]: "What should each channel deliver in the first year?" With no answer, the plan sets no year-one target.

## Process

0. **Read the start time and the version** — run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time. The result file needs both.

1. **Load brand artifacts** — read `brand-identity.json` and `messaging-architecture.json`. If either is missing, ask user to run `/gtm:marketing:brand` first or provide a product description to scaffold minimal brand context.

2. **Apply Kotler STP** — run segmentation, targeting, and positioning:
   - Segmentation: identify 3-5 distinct market segments from `gtm-context.json.icp`
   - Targeting: score each segment on market size, accessibility, fit, and urgency
   - Positioning: confirm or refine positioning statement per targeted segment

3. **Map to Moore Technology Adoption Lifecycle** — identify the beachhead segment (the most likely early adopter group with acute pain, budget, and willingness to be a reference customer). Design the launch to dominate this segment before crossing the chasm.

4. **Run Ahrefs keyword research** (if connected) — query `get_keyword_ideas` for the top 10 value-proposition phrases from `messaging-architecture.json`. Filter by search volume, keyword difficulty, and SERP intent. Output: priority keyword list by funnel stage (TOFU/MOFU/BOFU).

5. **Design channel strategy** — select 3-5 demand gen channels appropriate for the beachhead segment and business stage:
   - TOFU: SEO/content, paid search, LinkedIn ads, podcast sponsorships, community
   - MOFU: email nurture, webinars, case studies, comparison pages
   - BOFU: demos, free trials, ROI calculators, reference calls

6. **Design TOFU/MOFU/BOFU content calendar** — map 90 days of content across all channels. Each content item specifies: type, topic, target keyword (if SEO), target persona, funnel stage, distribution channels, and owner.

7. **Define MQL criteria** — specify the exact behavioral and demographic thresholds that qualify a lead as marketing-qualified:
   - Demographic fit (ICP match score ≥ threshold)
   - Behavioral signals (page views, content downloads, email opens, trial intent)
   - Exclusion criteria (competitors, wrong company size, wrong geography)

8. **Write output artifacts:**
   - `launch-plan.json` — structured launch plan with timeline, channels, budget allocation, success metrics
   - `campaign-plan.json` — campaign briefs for each demand gen program
   - `content-calendar.md` — 90-day content calendar with briefs and distribution

9. **Generate Canva assets** (if connected) — autofill launch announcement templates with brand messaging for social, email header, and blog hero image.

10. **Publish to Notion** (if connected) — create a new page in the GTM workspace with the launch plan and content calendar.

11. **Announce in Slack** (if connected) — post a launch plan summary to the configured GTM channel.

12. **Pass to integrity-agent** — validate all claims in campaign copy and launch messaging against Truth Tier system.

13. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/marketing-agent.md` with the Read tool and follow its `## Result file` section, in every run.

## Output Artifacts

- `launch-plan.json` — launch timeline, channels, budget, success metrics
- `campaign-plan.json` — demand gen campaign briefs per channel
- `content-calendar.md` — 90-day content calendar with briefs
- `mql-criteria.json` — precise MQL definition (synced to `gtm-context.json`)
- `truth-tier-audit.json` — integrity validation on all campaign copy
