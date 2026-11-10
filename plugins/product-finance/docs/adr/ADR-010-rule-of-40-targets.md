# ADR-010: Rule of 40 targets: 40, 50 or 60, one score, labelled sources

**Status:** Accepted (decided 2026-11-08; built in v0.15.0)
**Date:** 2026-11-08
**Builds on:** ADR-009, `ADR-009-exact-figures.md` (exact figures, rounded half away from zero at output)
**Plugin:** product-finance v0.15.0
**Decided here:** D-562, 2026-11-09 (the rule of ADR-010 as merged in source PR #344); the owner, 2026-11-10 (the quotes, and this record)

---

## Context

`scripts/rule_of_40.py` adds revenue growth % and EBITDA margin % and grades the sum against bands set by company stage:
- early: 30, 20, 10
- growth: 40, 30, 20
- scale and mature: 50, 40, 30

The bands arrived in the plugin's first commit (a19be6de5, 2026-03-01) with no source. The recommendations use a flat 40 at every stage, so at growth stage a score of 37 reads GOOD and also "Improve score by 3 points".

The person who owns the plugin asked for more than one bar. Rule of 40 suits a legacy SaaS baseline. A new AI-native or agentic product may aim higher, at a Rule of 50 or 60. The person's first proposal was:
- pick the target from the business model or the launch year;
- use free cash flow (FCF) margin for 60 and EBITDA margin for 40 and 50;
- weight profit twice as much as growth for 50 and 60.

Pasted context (Bain, and a LinkedIn post) supported it.

Six strategists tested the proposal on 2026-11-08 in a structured debate. Each had its own research, and three rounds followed. The findings:

1. **40 is the only bar with a published definition.** The sources are Feld (2015), ICONIQ and Bessemer.
2. **50 has no published definition.**
3. **60 appears only as a 2026 aspiration or forecast.** Vista (8 Jan 2026) calls it "an emerging aspiration, not a universal baseline". ICONIQ and Kellblog mention it too. None gives a formula, a margin basis or a measured distribution.
4. **Growth outweighs margin in valuation.** Every 2024–2026 regression found weights growth 2 to 4.5 times as heavily as margin: Bessemer 2–3 times, Meritech 3.8 times (August 2026 edition), Clouded Judgement about 3 times. No source supports "investors weight profit twice as much as growth".
5. **Bain's direction for AI is a softer bar, a Rule of 30.** This is from an extract only; the page returned HTTP 403.
6. **Mixing margins across targets contradicts itself.** Take 30% growth, 15% EBITDA margin and 31% FCF margin. That product clears 40, misses 50 and clears 60. Public FCF usually reads higher than EBITDA, mostly because stock pay is added back (secondary source). So FCF is not the stricter test for public-style companies, and for a private product the direction is unknown.
7. **Year-on-year growth does not exist before a product's thirteenth month of revenue.** ICONIQ "typically only begin[s] to place real weight against Rule of 40 for companies with at least $25M ARR", because early growth is inflated.

## Decision

1. **One score.** It stays revenue growth % plus margin %. No input adds to it or multiplies it.
2. **Three targets, a default of 40, and no inference.**
   - `target` is an optional input, and it must be exactly 40, 50 or 60.
   - The default is 40 for every product, and a target the person gives always applies.
   - No input picks the target: not business model, launch year, pricing model, gross margin, NRR or stage. No source maps any of them to a bar.
   - The report says whether the target is the default or the person's choice.
3. **The ladder, with each row labelled by its source.** Every graded report shows the score against 40, 50 and 60.
   - 40 cites Feld (2015).
   - 50 reads "No published benchmark found. A bar you set."
   - 60 quotes Vista (2026): "an emerging aspiration, not a universal baseline".
   - The report prints no percentile, no "top quartile" and no company goal.
4. **Margin basis: each given margin on its own line.**
   - `ebitda_margin` is required and `fcf_margin` is optional.
   - Each margin given is scored on its own line against the target, and neither wins.
   - When the two lines disagree at the target, the status is `split` and a reconcile line names the usual causes, with no direction claimed.
   - `--help` and the docs define both margins, including how stock pay is treated.
   - No target is tied to one basis.
5. **Weighting.** The weighted view stays 1.33 × growth + 0.67 × margin at every target. It is labelled a plugin convention and is never graded.
6. **The 12-month gate.** Before 12 months of revenue the product gets no verdict, because its growth is not a year-on-year rate. The report says so and still prints the score, the ladder arithmetic and the reference lines. When `months_of_revenue` is not given, the product is graded with the line "age not checked".
7. **No size gate.** A product under $25M ARR is graded. The ICONIQ sentence prints beside the result as a caution. When ARR is not given, the line reads "size not checked".
8. **Verdict words.**
   - Each margin line reads `met` or `short by N`.
   - A short product gets "closes with N points of growth or N points of margin". The plugin picks no lever, because no evidence picks one.
   - The stage-band word leaves the markdown.
9. **JSON.** `health_status` stays byte-identical for every input that is valid today. A new `target_status` (`met`, `short`, `split` or `not_graded`) sits beside it.
10. **Reference lines, never in the score.**
    - NRR prints beside the score, or reads "not available" under 12 months of revenue.
    - Gross margin prints with the Bessemer State of AI cohort points, about 25% for the fastest cohort and about 60% for the next, with no advice verb.
11. **Sources are read at their URLs before release.** The ICONIQ, Vista, Feld, Bessemer and Meritech passages are re-read at their own pages before the report prints them. Several were first read through summaries.
12. **Legacy text goes.** The unsourced lines in `rule_of_40.py` are removed or labelled under the same rule:
    - "Top quartile performance for public SaaS companies", and "you're in the top quartile";
    - "Target: >50% growth rate";
    - "reduce burn by 30-50%";
    - the stage target ranges.

## Consequences

- A person can grade against 40, 50 or 60. The report never presents 50 or 60 as a published benchmark.
- A new AI-native or agentic product gets its score and the ladder from the start, and a verdict from its thirteenth month of revenue.
- An explicit target of 40 gives the same report as the default. A test pins this.
- No existing `health_status` value changes. The Rule of 40 goldens are re-pinned by hand, once, for the new lines.
- The advice is thin: the gap in points, not a lever. These datasets would change that:
  - a primary cohort table showing an AI-native median at or above 50 on one stated basis, which would justify a context-picked default;
  - Rule of 40 measured against later outcomes by ARR band, which would justify a size gate;
  - which term moved for companies that crossed 40, which would let the report name a lever.
- **Rejected:**
  - a business-model or launch-year mapping;
  - a margin basis tied to each target;
  - profit-weighted scoring for 50 and 60;
  - an NRR-weighted score;
  - stage caps on the target;
  - a $25M size gate.

## Amendments in v0.15.0

Rulings made while building. Each one changes or narrows the text above.

- **Ruling 1: a typed 40 is a choice.** A typed 40 reads "(your choice)" and `target_source` is `chosen`; only an absent `target` reads `default`. This amends the Consequences sentence "An explicit target of 40 gives the same report as the default." The score, the ladder and the status are the same. The source line is not.
- **Ruling 2: the gate edge.** 12 months of revenue or less is not graded, and 13 is graded.
- **Ruling 3: a refused new key exits 3.** An input with a refused `target`, `fcf_margin`, `months_of_revenue`, `nrr` or `gross_margin` exits with code 3 and names the key. In 0.14.1 the script ignored these keys. This is a narrowing of decision 6.
- **Ruling 4: more unsourced lines go.** The Balance Type line and the trend judgment lines also go from the Rule of 40 markdown. The Magic Number band sentence in the Rule of 40 report stays, as the shared text of ADR-005.
- **The ICONIQ quote is printed unedited.** Finding 7 shows `begin[s]` because the ADR quotes ICONIQ in running prose. The report quotes the source as written: "we typically only begin to place real weight against Rule of 40 for companies with at least $25M ARR".
- **Setup keys stay unread.** `setup` stores `rule_of_40_target` and `target_rule_of_40`. `rule_of_40.py` does not read them and `setup` tells the person so.
- **The health check takes no target.** The health check descriptions take no target clause, because that command takes no target.
