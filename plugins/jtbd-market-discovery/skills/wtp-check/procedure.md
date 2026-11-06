# WTP check procedure

The skill `jtbd-market-discovery:wtp-check` asks the questions of Step 1 and dispatches `jtbd-market-discovery:wtp-check-runner`. The runner follows this file. It cannot ask the person anything, so it takes each input from the dispatch fields.

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.

## Purpose

Validate pricing decisions with rigorous multi-layer analysis because unrealistic pricing is the #1 reason products fail - this framework challenges assumptions and surfaces reality.

## Prerequisites

**Required:**
- Target pricing or WTP estimate to validate
- Market context (B2B/B2C, segment, competitors)
- EVC estimate (economic value created)

**Optional:**
- WTP survey data
- Competitive pricing data
- Historical pricing failures/successes

## Process

### Step 0: Read the Start Time and the Version

Run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time. The result file needs both.

Then run `git rev-parse --show-toplevel` on its own; its output is the git root, and when it fails the git root is the working directory. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py finished --base <git root>`: `input_dir` is the session it prints. Read `p7.json` and `p8.json` from `input_dir`. When it exits 1, no discover run has finished: halt, writing no `p9.json`, and write the result file with `results: []` and the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "no finished jtbd discover session: none holds p7.json and p8.json"}`. Otherwise run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py wtp-folder --base <git root>`: `session_dir` is the folder it prints. A person's run writes into no session that it did not start, because that session belongs to another run. When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.

### Step 1: Collect Pricing Hypothesis

Take the pricing to validate from the dispatch fields:

```
I'll rigorously validate your pricing using a 6-layer framework.

This framework is SKEPTICAL by design - it challenges pricing assumptions
and surfaces risks before you go to market.

What pricing do you want to validate?
- Target price: $__/month
- Target segment: [B2B/B2C, role, industry]
- Market context: [brief description]

Also helpful (but optional):
- EVC estimate (value created for customer)
- Competitor pricing you've researched
- WTP survey data if you have it
```

Take each input from the dispatch fields. In a plugin run, take each answer from the answers file instead. An input that neither gives is not known; ask for nothing, because an agent cannot ask the person.
- the target price per month, from `target_price`
- the target segment (role, industry), from `target_segment`
- B2B or B2C, from `market_context`
- the economic value the offering creates per customer per month, if known, from `evc_estimate`
- the path to WTP survey data, if there is any, from `wtp_survey_path`

### Step 2: Execute Layer 1 - Statistical Outlier Detection

If user has WTP survey data:

**Apply IQR method:**
```
Analyzing WTP survey responses (n=87)...

Statistical Analysis:
- Median WTP: $15/month
- Mean WTP: $22/month (pulled up by outliers)
- Q1 (25th percentile): $10/month
- Q3 (75th percentile): $25/month
- IQR: $15
- Outlier threshold: Q3 + 1.5×IQR = $47.50/month

Outliers detected: 3 respondents ($60, $75, $100)
Outlier rate: 3.4% (acceptable < 5%)

Adjusted median (excluding outliers): $14/month

✓ PASS: Statistically valid WTP range: $10-25/month
```

If no survey data:
```
⚠ SKIPPED: No survey data available
Recommendation: Conduct Van Westendorp PSM survey before final pricing
```

### Step 3: Execute Layer 2 - Competitive Benchmarking

Research competitive landscape:

**Input:**
- the direct competitors, what they charge, and any free alternatives, from `competitor_pricing`

**Critical for B2C: Check for free alternatives**
```
Competitive Analysis:

Direct Competitors:
- Competitor A: $20/month (premium features)
- Competitor B: $15/month (basic)
- Competitor C: $25/month (enterprise)

Free Alternatives:
- Google Maps: FREE (navigation, traffic, ETA)
- Waze: FREE (community-driven traffic)
- Apple Maps: FREE (built into iOS)

⚠ CHALLENGED: Free alternatives dominate this market
Reality Check: 95% of users use free options

Your pricing ($69/month) is 4.6× higher than paid competitors
and competes with FREE alternatives that satisfy 80% of needs.

Recommendation: Explain differentiation or pivot to B2B
```

### Step 4: Execute Layer 3 - Van Westendorp PSM (if available)

If user has PSM survey data:

**Van Westendorp questions:**
- At what price would this be so cheap you'd question quality? (Too Cheap)
- At what price would this be a bargain? (Not a Bargain)
- At what price would this be getting expensive? (Getting Expensive)
- At what price would this be so expensive you wouldn't buy? (Too Expensive)

**Find acceptable price range:**
```
Van Westendorp Price Sensitivity Meter:

Intersection Points:
- Point of Marginal Cheapness (PMC): $8/month
- Optimal Price Point (OPP): $18/month
- Indifference Price Point (IPP): $22/month
- Point of Marginal Expensiveness (PME): $35/month

Acceptable Price Range: $8-35/month
Optimal Price: $18-22/month

Your pricing ($69/month) is ABOVE Point of Marginal Expensiveness.
Expected conversion rate: < 5% (most users find it too expensive)

⚠ FAILED: Pricing exceeds acceptable range by 2×
```

If no PSM data:
```
⚠ SKIPPED: No Van Westendorp PSM data available
Recommendation: Run PSM survey with target segment (n > 100)
```

### Step 5: Execute Layer 4 - Value Economics Reality Check

Compare WTP to EVC created:

**Formula:** `WTP should be 10-30% of EVC`

**Analysis:**
```
Value Economics Check:

EVC Created: $420/month
Target WTP: $69/month
WTP as % of EVC: 16.4%

✓ PASS: WTP is within sustainable range (10-30% of EVC)

Value Capture Analysis:
- Customer retains: $351/month (83.6% of value)
- You capture: $69/month (16.4% of value)
- Incentive to switch: Strong ($351/month net benefit)

However, this assumes:
1. Customer believes your EVC claim
2. No free alternatives exist (VIOLATED - Google Maps is free)
3. Customer willing to pay for marginal improvement

Reality: If free alternative captures 80% of value ($336/month),
your marginal value is only $84/month, making $69/month = 82% of
marginal value. This is UNSUSTAINABLE.

⚠ CHALLENGED: Free alternatives change the economics
```

### Step 6: Execute Layer 5 - Confidence Scoring

Assess data quality and confidence:

**Factors:**
```
Confidence Score Calculation:

Sample Size:
- Survey respondents: 87
- ✓ GOOD: n > 30 (statistically valid)

Response Consistency:
- Standard deviation: $12
- Mean: $22
- CV (std/mean): 54.5%
- ⚠ MODERATE: High variance (prefer CV < 30%)

Data Recency:
- Survey conducted: 2 weeks ago
- ✓ GOOD: Recent data (< 3 months)

Segment Match:
- Survey sample: Urban commuters (target segment)
- ✓ EXCELLENT: Perfect match

Overall Confidence: MODERATE (70%)
Concern: High variance suggests segment is not homogeneous
Recommendation: Re-segment to find more cohesive groups
```

### Step 7: Execute Layer 6 - Segment-Specific Benchmarks

Apply segment-specific reality checks:

**B2C Benchmarks:**
```
B2C Pricing Reality Check:

Typical B2C SaaS Pricing:
- Freemium: $0-5/month (mass market)
- Basic: $5-15/month (broad appeal)
- Premium: $15-30/month (power users)
- Luxury: $30-50/month (niche, high-value)
- Ultra-luxury: $50+/month (rare, exceptional value)

Your pricing: $69/month
Category: Ultra-luxury (top 2% of B2C SaaS)

Ultra-luxury pricing REQUIRES:
- Exceptional brand (e.g., Apple, Tesla)
- No free alternatives
- Network effects or lock-in
- Clear 10× differentiation

Your product:
❌ Competing with free alternatives
❌ No network effects mentioned
❌ Value prop is marginal improvement (not 10×)

⚠ FAILED: B2C pricing unrealistic for market position
```

**B2B Benchmarks:**
```
B2B Pricing Reality Check:

Typical B2B SaaS Pricing (per user/month):
- Basic tools: $10-30/user/month
- Core workflow: $30-80/user/month
- Mission-critical: $80-200/user/month
- Enterprise: $200+/user/month

Your pricing: $60/user/month
Category: Core workflow (mid-range)

B2B pricing at $60/month REQUIRES:
✓ Measurable ROI (time savings, error reduction)
✓ Workflow integration (not standalone utility)
✓ Admin/reporting features
✓ Multi-user collaboration

Your product (team coverage):
✓ Clear ROI ($11,513/month value created)
✓ Workflow integration (team management)
✓ Admin features (coverage dashboards)
✓ Multi-user (managers + team members)

✓ PASS: B2B pricing is realistic and sustainable
```

### Step 8: Aggregate Validation Results

Synthesize all layers into overall assessment:

**Validation Matrix:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WTP VALIDATION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hypothesis: $69/month for B2C navigation app
Segment: Urban commuters

Layer 1: Statistical Outlier Detection
✓ PASS - Median WTP $15/month (excluding outliers)

Layer 2: Competitive Benchmarking
❌ FAILED - Free alternatives dominate (Google Maps, Waze)
- Paid competitors: $15-25/month
- Your pricing: $69/month (4.6× higher)

Layer 3: Value Economics
⚠ CHALLENGED - WTP/EVC ratio acceptable BUT...
- Free alternative captures 80% of value
- Marginal value too low to sustain $69/month

Layer 4: Confidence Score
⚠ MODERATE - High variance (CV 54.5%)
- Suggests segment needs refinement

Layer 5: B2C Benchmark
❌ FAILED - Ultra-luxury pricing without luxury positioning

[Van Westendorp PSM deferred to v1.2 — skipped]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERALL VALIDATION: ❌ FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Critical Issues:
1. Free alternatives make B2C pricing untenable
2. Pricing 4.6× higher than paid competitors
3. 2× above customer acceptable range

Recommendations:
1. PIVOT TO B2B: Target businesses, not consumers
   - Fleet management companies: $60-80/employee/month ✓
   - Ride-sharing platforms: Enterprise pricing ✓
   - Delivery services: ROI-based pricing ✓

2. If staying B2C: Radical price reduction
   - Target: $15-20/month (within acceptable range)
   - Freemium model to compete with free alternatives
   - Focus on 10× differentiation vs Google Maps

3. Re-segment: Find ultra-high-value niche
   - Medical transport (lives at stake): $100+/month viable
   - Executive chauffeur services: $200+/month viable
   - Emergency services: Enterprise contracts

Next Steps:
- Run /jtbd-market-discovery:discover with B2B segment
- Conduct B2B WTP validation
- Calculate B2B EVC (organizational value, not personal)
```

### Step 9: Scenario Analysis (Optional)

If user wants to explore alternatives:

```
Let's explore alternative pricing scenarios:

Scenario A: B2C Freemium
- Free tier: Basic navigation
- Premium tier: $19/month (predictive routing, insights)
- Conversion rate: 8% (typical for freemium)
- Viable? Maybe - depends on differentiation

Scenario B: B2B Fleet Management
- Target: Delivery companies, field service
- Pricing: $75/employee/month
- Value prop: Route optimization, time savings
- Viable? Yes - strong ROI case

Scenario C: B2B2C via Employers
- Employer pays: $30/employee/month (commute benefit)
- Employee gets: Free premium navigation
- Value prop: Reduced commute stress, on-time arrivals
- Viable? Yes - employer benefits from productivity

Which scenario would you like to explore?
```

### Step 10: Write p9.json and the Result File

Write `{session_dir}/p9.json` as step 10, SYNTHESIZE VALIDATION RESULTS, of the `## Workflow` of `${CLAUDE_PLUGIN_ROOT}/agents/wtp-validator.md` says. Then Read `${CLAUDE_PLUGIN_ROOT}/agents/wtp-validator.md` with the Read tool and follow its `## Result file` section, in every run.

## Important Notes

**This Framework is SKEPTICAL by Design:**
- Challenges assumptions aggressively
- Surfaces uncomfortable truths
- Better to fail in validation than in market

**When Pricing PASSES:**
- All 6 layers validate
- Clear path to sustainable business
- Confidence in go-to-market

**When Pricing FAILS:**
- Majority of layers fail or challenged
- Pivot recommended before launch
- Save 6-12 months of wasted effort

**When Pricing is CHALLENGED:**
- Mixed results across layers
- Addressable concerns but needs work
- Recommended: Test with pilot customers first

**Common Failure Modes:**
1. **Free Alternative Trap** - Hardest to overcome (B2C)
2. **Value Perception Gap** - Customer doesn't believe EVC
3. **Segment Mismatch** - Wrong target segment for pricing
4. **Timing** - Market not ready to pay (yet)

## Integration

After validation, offer next steps:

```
Would you like to:
1. Explore B2B pivot? (/jtbd-market-discovery:discover with B2B segment)
2. Update the product requirements with the validated pricing? (/product:explore)
```

## Examples

**Example 1: B2C Pricing Failure**
```
Input: $69/month for navigation app (B2C)
Result: FAILED - Free alternatives, 4.6× competitor pricing
Recommendation: Pivot to B2B fleet management
```

**Example 2: B2B Pricing Success**
```
Input: $60/month for team coverage management (B2B)
Result: PASSED - Strong ROI, no free alternatives, within benchmarks
Recommendation: Proceed to pilot with 5-10 customers
```

**Example 3: Challenged but Addressable**
```
Input: $30/month for meal planning app (B2C)
Result: CHALLENGED - High variance, competitive market
Recommendation: Tighten segment (e.g., athletes), test with pilot
```
