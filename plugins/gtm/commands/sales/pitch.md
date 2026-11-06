---
description: Build pitch deck and sales narrative using Challenger Sale and StoryBrand frameworks
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)"]
---

# /gtm:sales:pitch

## Purpose

Build a complete sales pitch — deck structure, narrative arc, and speaker notes — using the Challenger Sale's Teach/Tailor/Take Control structure and StoryBrand's customer-as-hero narrative. The resulting pitch teaches buyers something they did not know about their business, tailors the insight to their specific situation, and positions your product as the natural resolution. Generic vendor pitches that lead with features are explicitly rejected by this agent.

## Usage

```
/gtm:sales:pitch
/gtm:sales:pitch --audience "VP Engineering"     # tailor pitch to specific buyer persona
/gtm:sales:pitch --deal "Acme Corp"              # load deal-specific context from HubSpot
/gtm:sales:pitch --format slides                 # slides | narrative | both (default: both)
```

## Process

1. **Load context artifacts** — read `brand-identity.json`, `messaging-architecture.json`, and ICP from `gtm-context.json`. If a deal name is provided, pull deal-specific context from HubSpot (if connected). Identify primary buyer persona for this pitch.

2. **Apply Challenger Sale — Teach** — develop the commercial insight: a counterintuitive truth about the buyer's business or industry that reframes their current approach as suboptimal. The insight must:
   - Be surprising but defensible
   - Lead logically to your product's solution
   - Not be something the buyer can easily find themselves
   - Be backed by data, research, or pattern matching from customer conversations

3. **Apply Challenger Sale — Tailor** — adapt the commercial insight to the specific buyer persona. Different personas within the same account care about different things:
   - Economic buyer: ROI, risk, strategic fit
   - Technical buyer: integration, security, scalability
   - User buyer: workflow impact, ease of use, time savings
   - Coach/Champion: political win, career upside

4. **Apply Challenger Sale — Take Control** — structure the pitch to move confidently toward a decision. Define clear next steps at each part of the pitch. Build in assertive moments where the rep can acknowledge tension and continue forward.

5. **Apply StoryBrand to narrative arc** — position the customer as hero throughout the pitch. The product appears as the guide, not the protagonist. Structure:
   - Parts 1-3: Customer's world (character + problem — internal, external, philosophical)
   - Parts 4-5: The insight (what they are missing, what it costs them)
   - Parts 6-7: The guide appears (your brand, credibility markers, empathy + authority)
   - Parts 8-9: The plan (clear 3-step process, low friction)
   - Part 10: Social proof (case study — specific, quantified, relatable)
   - Part 11: CTA (specific next step, low risk)
   - Part 12: Failure/success stakes (optional — only if urgency is real)

6. **Build `pitch-deck.json`** — part-by-part outline of the pitch (a JSON file, no slide file):
   - Part number, title, narrative purpose
   - Key message (one sentence — what the buyer must think after this part)
   - Visual direction (chart, quote, diagram, image, minimal text)
   - Speaker talking points (3-5 bullets)
   - Transition to next part

7. **Write `pitch-narrative.md`** — full speaker guide including:
   - Opening hook (first 30 seconds verbatim)
   - Full talking track for each part
   - Discovery questions to ask at each section
   - Objection handling playbook (top 5 objections with responses)
   - Closing language options (assumptive close, summary close, next-step close)

8. **Pass to integrity-agent** — validate all claims in pitch outline and speaker notes. Block Tier 5 claims. Flag any ROI or market size claims that require sourcing.

## Output Artifacts

- `pitch-deck.json` — part-by-part outline of the pitch with talking points
- `pitch-narrative.md` — full speaker guide with objection handling
- `truth-tier-audit.json` — integrity validation on all pitch claims

## Challenger Sale Summary

| Phase | What the Rep Does | What the Buyer Experiences |
|-------|-------------------|---------------------------|
| Teach | Delivers commercial insight | Learns something new and valuable |
| Tailor | Adapts insight to buyer persona | Feels heard and understood |
| Take Control | Drives toward decision | Moved by confident, helpful pressure |
