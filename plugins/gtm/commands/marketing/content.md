---
description: Build content strategy and SEO-grounded content calendar using brand voice guide and Ahrefs keyword data
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "mcp__ahrefs__get_keyword_ideas", "mcp__ahrefs__get_search_volume", "mcp__ahrefs__get_backlink_stats", "mcp__canva__generate_design", "mcp__canva__autofill_template"]
---

# /gtm:marketing:content

## Purpose

Build a content strategy and detailed content calendar grounded in SEO keyword data and brand voice. Every piece of content is mapped to a specific customer journey stage, tied to a target keyword cluster (if SEO content), structured using StoryBrand narrative logic, and written in the brand voice defined in `voice-guide.md`. The output is one content brief for each planned piece.

## Usage

```
/gtm:marketing:content
/gtm:marketing:content --horizon 90d       # calendar length (default: 90 days)
/gtm:marketing:content --focus seo        # seo | social | email | all (default: all)
/gtm:marketing:content --keywords-only    # skip calendar, run keyword research only
```

## Process

1. **Load `voice-guide.md` and `brand-identity.json`** — establish brand voice rules, tone, and vocabulary before any content planning begins. If either file is missing, ask user to run `/gtm:marketing:brand` first or provide a brief product description to infer minimal voice guidelines.

2. **Run Ahrefs keyword research** (if connected) — for each funnel stage, identify 10-30 priority keywords:
   - TOFU: broad awareness terms, problem-aware queries (keyword difficulty ≤ 40 preferred)
   - MOFU: solution-aware queries, comparison terms, "best [category]" searches
   - BOFU: branded, competitor comparison, high-intent purchase queries
   - Use `get_keyword_ideas` seeded from value proposition phrases in `messaging-architecture.json`
   - Use `get_search_volume` to prioritize by traffic potential
   - Use `get_backlink_stats` to assess competitive difficulty for target domains

3. **Apply Miller StoryBrand to content structure** — every planned content piece must serve a role in the customer hero's journey. Map each content type to the SB7 framework:
   - Problem-aware content: addresses character + problem
   - Solution content: introduces the guide + plan
   - Proof content: demonstrates success (case studies, testimonials)
   - CTA content: direct and transitional calls to action

4. **Design content calendar structure** — plan content across four types:
   - **Pillar pages** (1-2 per quarter): comprehensive, SEO-authoritative, 3,000+ words
   - **Cluster blog posts** (4-8 per month): 1,000-2,000 words, each linked to a pillar
   - **Social content** (daily/weekly): repurposed from blog and original short-form
   - **Email nurture** (2-4 per month): sequenced by buyer stage, not batch-and-blast

5. **Write one brief for each planned piece** with these 9 fields:
   - Title and working headline
   - Target keyword (primary + 2-3 secondary)
   - Funnel stage and persona
   - SB7 narrative role
   - Word count target
   - Key points to cover (3-5 bullets)
   - Internal links to suggest
   - CTA for this piece
   - Distribution channels

6. **Write `content-calendar.md`** — structured markdown calendar with all briefs organized by week, content type, and distribution channel. Include a keyword map showing pillar → cluster relationships.

7. **Generate Canva visual templates** (if connected) — create or autofill visual templates for blog hero images, social post formats, and email headers using brand colors and style from `brand-identity.json`.

8. **Pass to integrity-agent** — validate all SEO-targeted claims and statistics in content briefs. Flag any claims that require sourcing or softened language.

## Output Artifacts

- `content-calendar.md` — full content calendar with briefs, keywords, and distribution plan
- `keyword-map.json` — pillar and cluster keyword structure with search volume data
- `content-briefs/` — individual brief files for each planned piece (if requested)
- `truth-tier-audit.json` — integrity validation on content claims
