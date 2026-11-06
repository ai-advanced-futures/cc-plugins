---
name: marketing-content
description: Build a content strategy and calendar aligned to funnel stages, SEO data, and brand voice
---

# Content Strategy

> **Delegation note:** Content production (writing blog posts, emails, social copy) is delegated to `marketing:draft-content` (Anthropic plugin) when available. This skill owns content strategy (TOFU/MOFU/BOFU architecture, SEO keyword prioritization, content briefs) and Truth Tier compliance of all produced content.

## Purpose

Create content that serves the customer at every stage of their journey — from not knowing you exist (TOFU) to choosing you over alternatives (BOFU). 
## Content by Funnel Stage

### TOFU — Top of Funnel (Awareness)
**Goal:** Attract strangers with useful content.
**Formats:** Blog posts, SEO articles, YouTube, podcasts, social threads.
**Voice:** Teach and share your insights, because a reader at this stage is not ready to buy.
**Truth Tier:** Tier 1-3 only. TOFU is not the place to promote roadmap.

### MOFU — Middle of Funnel (Consideration)
**Goal:** Build trust and demonstrate expertise.
**Formats:** Case studies, comparison guides, webinars, email sequences.
**Voice:** Show customer outcomes, because evidence builds more trust than claims.
**Truth Tier:** Tier 1-2 only. Case studies must be real.

### BOFU — Bottom of Funnel (Decision)
**Goal:** Reduce friction to conversion.
**Formats:** Demo videos, pricing pages, ROI calculators, trial CTAs.
**Voice:** Clear, direct. State what the customer gets.
**Truth Tier:** Tier 1 only. No future-tense at BOFU.

## SEO Integration
When Ahrefs MCP is connected:
- Pull keyword ideas for your owned word + category
- Filter for commercial intent, search volume > 100/mo
- Map keywords to content pieces by funnel stage

## Voice Guide Application
All content passes through voice-guide.md before delivery:
- Dos: [from brand identity]
- Donts: vocabulary to avoid
- Tone: [from brand identity]

## Output
`content-calendar.md` with 30-day plan by channel, format, keyword, and funnel stage.
