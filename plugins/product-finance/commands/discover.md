---
description: Discovery stage financial analysis with market sizing (TAM/SAM/SOM), revenue opportunity, and CAC estimates by channel
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# Product Finance Discover Command

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `uv run python`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because only the plugin's own scripts are tested.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Every run

0. **Read the start time and the version** — run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and keep its output as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. Never type a time yourself, because a typed time is a guess and not the time of the run. The result file needs both.
1. Do the work the rest of this file describes.
2. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/market-analyzer.md` with the Read tool and follow its `## Result file` section, in every run.

## Purpose

The discover command performs comprehensive discovery stage financial analysis to help you understand market opportunity, estimate revenue potential, and project customer acquisition costs before building your product or feature. This is typically the second command you run after `/product-finance:setup`.

**Key outputs:** Market sizing (TAM/SAM/SOM), revenue opportunity by segment, CAC estimates by channel, and go-to-market financial recommendations.

## When to Use

- **Early product discovery:** Before building a new product or major feature
- **Market opportunity assessment:** Quantifying addressable market and revenue potential
- **Go-to-market planning:** Estimating customer acquisition costs and channel strategy
- **Fundraising preparation:** Building data-driven market sizing for investors
- **Strategic planning:** Annual or quarterly market analysis
- **Post-JTBD analysis:** Translating Jobs-to-be-Done insights into financial projections

## What It Does

1. **Market Sizing Analysis (TAM/SAM/SOM):**
   - Calculates Total Addressable Market
   - Determines Serviceable Addressable Market
   - Projects Serviceable Obtainable Market
   - Validates assumptions against industry benchmarks

2. **Revenue Opportunity Calculation:**
   - Projects revenue by customer segment
   - Calculates average revenue per customer (ARPC)
   - Estimates market penetration scenarios
   - Models pricing strategy implications

3. **CAC Estimation by Channel:**
   - Estimates Customer Acquisition Cost for each channel
   - Compares channel efficiency and scale potential
   - Projects blended CAC across channels
   - Identifies optimal channel mix

4. **JTBD Plugin Integration:**
   - Automatically imports willingness-to-pay (WTP) data
   - Leverages customer segments from JTBD analysis
   - Uses economic value calculations for pricing validation
   - Enriches financial projections with customer insights

5. **Go-to-Market Recommendations:**
   - Recommends target segments based on financial attractiveness
   - Suggests optimal channel strategy
   - Provides pricing guidance
   - Identifies risks and mitigation strategies

## Command Behavior

### Hybrid Data Collection Approach

The discover command uses a **smart integration strategy**:

1. **Check for JTBD data:** In a person's run only, if a jtbd result exists, import it as **Person run** below says
2. **Fill gaps interactively:** Prompt for any missing financial data
3. **Validate assumptions:** Cross-check JTBD insights with financial reality
4. **Enrich with benchmarks:** Add industry-standard CAC and conversion rates

**Philosophy:** Leverage existing customer research (JTBD), augment with financial analysis, validate with benchmarks.

### Plugin run

A plugin run reads only the `result_file` of the `inputs_from` entry whose `plugin` is `jtbd-market-discovery`. It uses that file only when its `run.run_id` equals the entry's `run_id` and its `run.case` equals the block's `case`. Otherwise, and when the file is missing or is not JSON, it records the gap `{"kind": "customer_segment", "label": "Customer segments from jtbd", "why": "<the reason>"}` and sizes the market from the answers alone. With no jtbd entry, it reads no jtbd file. It then records no gap.

The `result_file` path is relative to the git root. A file that is JSON but holds no `customer_segment` result is also the gap above, with the reason.

When the run uses the file, its `customer_segment` results are the segments of Phase 3. The answers still size the market in Phase 2. When the answers also give `segments` or `target_acv`, the answers win, and the result copies no jtbd source for that value.

A segment's ACV comes from the one `willingness_to_pay` result whose `value.segment` is that segment's name. Take its `point`, else the middle of its `low` and `high`, else the one bound it gives. A jtbd willingness to pay has `period` `month`: the ACV is 12 times that value. A value with `period` `year` is the ACV as written. A segment with no such result, or with more than one, has no ACV from the file: use the answers' `target_acv` when they give one, else record a `customer_segment` gap that names the segment.

### Person run

In `discover`, a person's run reads a jtbd result only at the `post_jtbd` stage; `setup`'s `jtbd` option reads it when the person picks that option. It reads the newest file in `.jtbd-market-discovery/results/` (by `run.finished_at`) that holds a `customer_segment` or `willingness_to_pay` result, and names it in the "Found JTBD analysis" line. It reads no `.jtbd/` file. It checks no `run_id` or `case`. Skip a file that is not JSON, and name it. Skip a file that has no `run.finished_at`. When the two newest files have the same `run.finished_at`, name both files and read neither. The file the run reads is the accepted file. With no accepted file, show no "Found JTBD analysis" line, leave out `--jtbd-data`, and size the market from the answers.

The person's segments are the list the calculator reads: the top-level `segments` and the `market.target_segments` of `.product-finance/assumptions.json`, merged by `segment_name`, the top-level fields winning field by field. Names match when they are equal after trimming spaces and ignoring case. A segment's willingness to pay comes from the `willingness_to_pay` result whose `value.segment` names it. If more than one result names it, name the conflict and set none. Take the result's `point`, else the middle of its `low` and `high`, else the one bound it gives. A value with `period` `month` is 12 times that value a year; a value with `period` `year` is used as written.

Set `willingness_to_pay` and `wtp_source` on the person's segment of the same name. A value the person wrote is kept, because the person's answer outranks a jtbd value. Name a jtbd segment that has no match, and add no segment for it. A person's segment with no matching result stays unchanged. A `willingness_to_pay` that is present and not null is a value the person wrote, with or without a `wtp_source`: keep it, and set no `wtp_source` on it. `wtp_source` is the path of the accepted file. Show the unmatched names in the "Found JTBD analysis" line. An unmatched name or a missing value does not stop the run. Save the merged segments to the top-level `segments` of `.product-finance/assumptions.json` before the calculator runs. `--jtbd-data` gets the accepted file.

### Calculator run

In a person's run, before the first script run, write this run's answers into `.product-finance/assumptions.json` as top-level keys, by the table below. Create the file if it does not exist, and keep every other top-level key it already holds. Write every number as a JSON number, such as `12000`: text such as `"12000"`, and `true` or `false` for a number, make the script exit with code 3.

| Question id | Key in assumptions.json |
| --- | --- |
| `tam_method` | `tam.method` |
| `total_market_size` | `tam.total_market_size` |
| `icp_percent` | `tam.icp_filter_percent` |
| `potential_customers` | `tam.potential_customers` |
| `target_acv` | `tam.target_acv` |
| `value_per_customer` | `tam.economic_value_per_customer` |
| `capture_percent` | `tam.value_capture_percent` |
| `value_customers` | `tam.potential_customers` |
| `sam_percent` | `sam_filters.geographic` |
| `som_timeframe_years` | `som_timeframe_years` |
| `market_share_percent` | `som_market_share_pct` |
| `segments` | `segments` |
| `inbound_monthly_spend` | `inbound_marketing.monthly_spend` |
| `inbound_mqls_per_month` | `inbound_marketing.mqls_per_month` |
| `mql_conversion_percent` | `inbound_marketing.mql_to_customer_pct` |
| `sdr_count` | `outbound_sales.sdrs` |
| `sdr_annual_cost` | `outbound_sales.sdr_cost_annual` |
| `opps_per_sdr_month` | `outbound_sales.opps_per_sdr_monthly` |
| `ae_count` | `outbound_sales.aes` |
| `ae_annual_cost` | `outbound_sales.ae_cost_annual` |
| `close_rate_percent` | `outbound_sales.opp_to_close_pct` |
| `plg_free_users_month` | `plg.free_users_monthly` |
| `plg_conversion_percent` | `plg.free_to_paid_pct` |
| `plg_cost_per_signup` | `plg.cost_per_signup` |
| `partner_count` | `partnerships.active_partners` |
| `partner_commission_percent` | `partnerships.commission_pct` |
| `partner_acv` | `partnerships.average_acv` |
| `customers_per_partner_quarter` | `partnerships.customers_per_partner_quarterly` |
| `enterprise_ae_count` | `field_sales.enterprise_aes` |
| `enterprise_ae_annual_cost` | `field_sales.ae_cost_annual` |
| `deals_per_enterprise_ae_year` | `field_sales.deals_per_ae_annual` |
| `community_monthly_investment` | `community.monthly_investment` |
| `community_conversions_month` | `community.conversions_monthly` |
| the three shares asked in Phase 2b | `sam_filters.geographic`, `.customer_size`, `.channel` |

Write the `segments` answers into the top-level `segments`, merged by `segment_name` as the calculator merges them. The `channels` answer picks which channel objects are written. Write a channel object only when all its fields are answered. When this run asked `channels`, remove from the file each channel object the answer did not pick: the script computes a CAC for every channel object it finds. Each segment in `segments` has the fields `segment_name`, `potential_customers`, `target_acv`, `conversion_rate_pct` and `acquisition_difficulty`.

A dotted name in the table, such as `tam.icp_filter_percent`, is a key inside a top-level object. When this run asked at least one question for `tam`, its answers write the whole `tam` object, the method and its inputs; the same holds for `sam_filters`. A written object keeps no key it held before this run. A run that asked no question for an object keeps what the file holds. `sam_percent` writes `"sam_filters": {"geographic": <answer>}` and nothing else; the three shares of Phase 2b write all three keys. An answer to a dotted name the script lists on exit 3, such as `tam.icp_filter_percent`, adds that one key inside its top-level object and keeps the object's other keys. A name such as `segments[Mid-Market].target_acv` is the `target_acv` of the top-level segment named Mid-Market; add that segment when only setup's list holds it.

When the script exits with code 3, it lists each missing or invalid input by its name in `assumptions.json`. These are most often `average_acv`, `gross_margin_pct` and `monthly_churn_pct`, which no question of this command asks. Ask the person for each input it lists (AskUserQuestion [q: none]), write each answer under the name the script lists, and run the script once more. In automated mode, an exit with code 3 asks nothing. When it lists a number written as text, rewrite it and run once more; otherwise go straight to the rule for a second exit with code 3.

When the script lists a value as `not a number` and the value is a plain number written as text (digits, an optional sign, one decimal point, no unit or letter), rewrite it in the file as a JSON number without asking, in automated mode too, before the run once more, together with any answers you ask for. Ask the person only for a value that cannot be read that way. A value setup wrote under `market` or `retention` stays as setup wrote it, so setup's own entries are kept.

When the second run also exits with code 3, ask nothing more and run the script no more, because a third run gives the same exit. Work out each figure whose inputs are all present by the formulas in this command, with no code at all, and end its `method` with: Computed by the model from the formula stated in the command; no script ran. Record each figure you could not work out as a gap, with the inputs still missing in `why`.

A value answered in this run is a `person` source, though it is read from `.product-finance/assumptions.json`, with `ref` `asked in this run: <input>`. An answer the person picked from an option labelled as the default or as recommended stays a `default` source. A value read from the file that this run did not ask stays a `default` source with the file as `ref`.

## Question Flow

### Phase 1: Market Context

**Question** (AskUserQuestion [q: market]): "Which product and market is this analysis for?"
- **Type:** text

**Question** (AskUserQuestion [q: discovery_stage]): "What stage of discovery are you in?"

**Options:**
- `pre_jtbd` - Market sizing before customer research
- `post_jtbd` - Financial analysis after JTBD research (recommended)
- `refresh` - Updating existing discovery analysis

**If `post_jtbd`:**
- In a person's run only, read the jtbd result as **Person run** says
- If found, display: "Found JTBD analysis: <file>. Importing segments and willingness to pay..." and the unmatched jtbd segment names
- Continue with Phase 2: a jtbd result gives no market size

**If `pre_jtbd` or file not found:**
- Continue with manual market sizing in Phase 2

### Phase 2: Market Sizing (Manual Mode)

**Introduction:**
```
Market Sizing Analysis
======================
We'll calculate your addressable market using the TAM/SAM/SOM framework:
- TAM: Total Addressable Market (theoretical maximum)
- SAM: Serviceable Addressable Market (what you can reach)
- SOM: Serviceable Obtainable Market (realistic capture in 3-5 years)

Start with TAM and work down to SOM with increasing realism.
```

#### 2a. Total Addressable Market (TAM)

**Question** (AskUserQuestion [q: tam_method]): "How would you like to calculate TAM?"

**Options:**
- `top_down` - Start with total market size, narrow by ICP filters
- `bottom_up` - Start with target customers, multiply by pricing
- `value_theory` - Start with economic value created, estimate capture

**For `top_down`:**

**Question** (AskUserQuestion [q: total_market_size]): "What is the total market size for your category?"
- **Type:** number
- **Guidance:** "Total revenue of all companies in your space (e.g., '$50B project management software market')"
- **Example:** "$50,000,000,000"

**Question** (AskUserQuestion [q: icp_percent]): "What percentage of this market matches your Ideal Customer Profile?"
- **Type:** number (0-100)
- **Guidance:** "Filter by company size, industry, geography, etc."
- **Example:** "10% (SMBs in North America with 10-200 employees)"

**Auto-calculate:**
```
TAM = Total Market × ICP Filter %
Example: $50B × 10% = $5B TAM
```

**For `bottom_up`:**

**Question** (AskUserQuestion [q: potential_customers]): "How many potential customers fit your target profile globally?"
- **Type:** integer
- **Guidance:** "Total companies/users matching your ICP"
- **Example:** "500,000 companies"

**Question** (AskUserQuestion [q: target_acv]): "What is your target Annual Contract Value (ACV)?"
- **Type:** number
- **Guidance:** "Average annual revenue per customer at your target pricing"
- **Example:** "$10,000/year"

**Auto-calculate:**
```
TAM = Potential Customers × Target ACV
Example: 500,000 × $10,000 = $5B TAM
```

**For `value_theory`:**

**Question** (AskUserQuestion [q: value_per_customer]): "What is the total economic value you create per customer annually?"
- **Type:** number
- **Guidance:** "Time saved × cost per hour, or revenue increased, or cost reduced"
- **Example:** "$50,000 in time/cost savings per customer"

**Question** (AskUserQuestion [q: capture_percent]): "What percentage of this value can you realistically capture?"
- **Type:** number (0-100)
- **Guidance:** "Typically 10-30% of value created. Account for competition and alternatives."
- **Example:** "20% ($10,000 annual price)"

**Question** (AskUserQuestion [q: value_customers]): "How many potential customers could benefit from this value?"
- **Type:** integer
- **Example:** "500,000 companies"

**Auto-calculate:**
```
Price = Economic Value × Capture %
TAM = Potential Customers × Price
Example: 500,000 × ($50,000 × 20%) = $5B TAM
```

#### 2b. Serviceable Addressable Market (SAM)

**Introduction:**
"SAM is the portion of TAM you can realistically reach given your business model, distribution channels, and geographic focus."

**Question** (AskUserQuestion [q: sam_percent]): "What constraints limit your addressable market?"

**Collect filters:**
- **Geographic reach:** "Which markets can you serve?"
  - Options: `global`, `north_america`, `us_only`, `eu_only`, `specific_countries`
  - If specific: "Which countries?" (text)

- **Customer size:** "What customer sizes can you serve?"
  - Options: `all`, `smb_only` (1-200 employees), `mid_market` (200-2000), `enterprise` (2000+), `mixed`

- **Channel constraints:** "What distribution channels do you have access to?"
  - Options: `direct_sales`, `self_service`, `partners`, `marketplace`, `mixed`

When the person did not give `sam_percent`, ask for the three shares after the three filter options are picked, as numbers from 0 to 100 in one call (AskUserQuestion [q: none], up to three questions). Each question's recommended option is your estimate from the options picked, labelled as recommended.

**Auto-calculate SAM:** when the person gives the reachable share directly (`sam_percent`), SAM = TAM × that share, and the three filters are not needed. Otherwise:
```
SAM = TAM × Geographic Filter × Size Filter × Channel Filter

Example: $5B TAM
× 40% (North America only)
× 60% (SMB + Mid-market, excluding enterprise)
× 80% (Direct + Self-service, no partners yet)
= $960M SAM
```

#### 2c. Serviceable Obtainable Market (SOM)

**Introduction:**
"SOM is your realistic market capture within 3-5 years, accounting for competition, adoption rates, and execution capability."

**Question** (AskUserQuestion [q: som_timeframe_years]): "What is your target timeframe for SOM?"
- **Type:** integer (1-10)
- **Default:** 3 years
- **Guidance:** "Typically 3-5 years for startups, 1-3 years for new features"

**Question** (AskUserQuestion [q: competitive_intensity]): "What is the current competitive intensity in your market?"
- **Options:**
  - `low` - Few competitors, greenfield opportunity
  - `medium` - Several competitors, differentiated positioning
  - `high` - Many competitors, must displace incumbents
  - `very_high` - Saturated market, free alternatives exist

**Question** (AskUserQuestion [q: market_share_percent]): "What market share do you think is realistic to capture?"
- **Type:** number (0-100)
- **Guidance:**
  - Greenfield: 5-15% realistic
  - Competitive: 1-5% realistic
  - Saturated: 0.1-1% realistic
- **Example:** "2% of SAM in 3 years"

**Auto-calculate SOM:**
```
SOM = SAM × Realistic Market Share %

Example: $960M SAM × 2% = $19.2M SOM (3-year target)
```

**Validation check:**
```
If SOM > $100M for seed stage: ⚠️ WARNING - May be too optimistic
If SOM < $10M: ⚠️ WARNING - Market may be too small for venture scale
If SOM/SAM > 10%: ⚠️ WARNING - Market share projection may be aggressive
```

### Phase 3: Customer Segments and Revenue Opportunity

**If a jtbd result was merged:** show each segment with the willingness to pay the merge set. Then ask the questions below as in manual mode: the merge sets only willingness to pay.

For a segment already in `assumptions.json`, keep its name, `willingness_to_pay` and `wtp_source`, and ask only for the fields it lacks.

**If manual mode:**

**Question** (AskUserQuestion [q: segment_count]): "How many distinct customer segments are you targeting?"
- **Type:** integer (1-5)
- **Guidance:** "Groups with different needs, budgets, or acquisition strategies"
- **Example:** "3 segments: Startups, SMBs, Mid-Market"

**For each segment:**

**Segment #N Details:**

**Question** (AskUserQuestion [q: segments]): "Segment name?"
- **Type:** string
- **Example:** "SMB SaaS Companies"

**Question** (AskUserQuestion [q: segments]): "How many potential customers in this segment?"
- **Type:** integer
- **Guidance:** "Portion of SAM addressable customers"
- **Example:** "100,000 companies"

**Question** (AskUserQuestion [q: segments]): "What is the target ACV for this segment?"
- **Type:** number
- **Guidance:** "Annual Contract Value - how much revenue per customer per year"
- **Example:** "$12,000"

**Question** (AskUserQuestion [q: segments]): "What is the expected conversion rate for this segment?"
- **Type:** number (0-100)
- **Guidance:**
  - Self-service: 1-5% of visitors
  - Sales-led: 10-25% of qualified leads
  - Enterprise: 15-30% of opportunities
- **Example:** "15% of qualified leads"

**Question** (AskUserQuestion [q: segments]): "How difficult is it to acquire customers in this segment?"
- **Options:**
  - `low` - High inbound interest, short sales cycle, self-service
  - `medium` - Moderate effort, mid-length sales cycle
  - `high` - Complex sale, long cycle, competitive
  - **Why:** Determines relative CAC estimates

**Auto-calculate segment opportunity:**
```
Segment Revenue Opportunity = Customers × ACV × Conversion Rate

Example: SMB Segment
100,000 potential × $12,000 ACV × 15% conversion = $180M opportunity
```

**Repeat for all segments.**

**Calculate total revenue opportunity:**
```
Total Revenue Opportunity = Sum of all segment opportunities
Market Penetration Required = SOM / Total Revenue Opportunity

Example:
Total opportunity: $450M
SOM target: $19.2M
Required penetration: 4.3% (realistic)
```

### Phase 4: Customer Acquisition Cost (CAC) by Channel

**Introduction:**
```
CAC Estimation by Channel
=========================
We'll estimate Customer Acquisition Cost for each go-to-market channel.
CAC directly impacts unit economics and determines viable channels.

Target: CAC Payback < 12 months (LTV:CAC ratio > 3:1)
```

**Question** (AskUserQuestion [q: channels]): "Which acquisition channels are you planning to use?"

**Options (multi-select):**
- `inbound_marketing` - Content, SEO, paid ads → self-service signup
- `outbound_sales` - SDRs + AEs cold outreach
- `product_led_growth` - Free trial/freemium → paid conversion
- `partnerships` - Channel partners, resellers, integrations
- `field_sales` - Enterprise field sales teams
- `community` - Community-led growth, user groups

**For each selected channel:**

#### Channel: Inbound Marketing

**Question** (AskUserQuestion [q: inbound_monthly_spend]): "What is your estimated monthly marketing spend for inbound?"
- **Type:** number
- **Guidance:** "Paid ads + content + tools + marketing team allocation"
- **Example:** "$20,000/month"

**Question** (AskUserQuestion [q: inbound_mqls_per_month]): "How many Marketing Qualified Leads (MQLs) per month do you expect?"
- **Type:** integer
- **Guidance:** "Leads from content, ads, SEO, events"
- **Example:** "500 MQLs/month"

**Question** (AskUserQuestion [q: mql_conversion_percent]): "What is your MQL-to-customer conversion rate?"
- **Type:** number (0-100)
- **Guidance:** "Typically 5-15% for self-service, 2-5% for sales-led"
- **Example:** "10%"

**Auto-calculate:**
```
Customers per month = MQLs × Conversion Rate
Example: 500 × 10% = 50 customers/month

Inbound CAC = Marketing Spend / Customers
Example: $20,000 / 50 = $400 CAC
```

#### Channel: Outbound Sales

**Question** (AskUserQuestion [q: sdr_count]): "How many SDRs (Sales Development Reps) will you have?"
- **Type:** integer
- **Example:** "3 SDRs"

**Question** (AskUserQuestion [q: sdr_annual_cost]): "What is the fully-loaded annual cost per SDR?"
- **Type:** number
- **Guidance:** "Salary + benefits + tools + overhead = typically $80K-$150K"
- **Default:** $100,000
- **Example:** "$110,000"

**Question** (AskUserQuestion [q: opps_per_sdr_month]): "How many qualified opportunities per SDR per month?"
- **Type:** integer
- **Guidance:** "Typical range: 8-15 opps/SDR/month"
- **Example:** "10 opps/month"

**Question** (AskUserQuestion [q: ae_count]): "How many Account Executives (AEs) will close these deals?"
- **Type:** integer
- **Example:** "2 AEs"

**Question** (AskUserQuestion [q: ae_annual_cost]): "What is the fully-loaded annual cost per AE?"
- **Type:** number
- **Guidance:** "Salary + commission + benefits + overhead = typically $150K-$300K"
- **Default:** $200,000
- **Example:** "$220,000"

**Question** (AskUserQuestion [q: close_rate_percent]): "What is your opportunity-to-close rate?"
- **Type:** number (0-100)
- **Guidance:** "Typical range: 20-30%"
- **Example:** "25%"

**Auto-calculate:**
```
Opportunities per month = SDRs × Opps per SDR
Example: 3 × 10 = 30 opps/month

Customers per month = Opportunities × Close Rate
Example: 30 × 25% = 7.5 customers/month

Monthly Sales Cost = (SDRs × SDR Cost + AEs × AE Cost) / 12
Example: (3 × $110K + 2 × $220K) / 12 = $64,167/month

Outbound CAC = Monthly Sales Cost / Customers
Example: $64,167 / 7.5 = $8,556 CAC
```

#### Channel: Product-Led Growth (PLG)

**Question** (AskUserQuestion [q: plg_free_users_month]): "What is your expected monthly free user acquisition?"
- **Type:** integer
- **Guidance:** "Organic + paid signups to free tier"
- **Example:** "2,000 free users/month"

**Question** (AskUserQuestion [q: plg_conversion_percent]): "What is your free-to-paid conversion rate?"
- **Type:** number (0-100)
- **Guidance:** "Typical range: 2-10% within 90 days"
- **Example:** "5%"

**Question** (AskUserQuestion [q: plg_cost_per_signup]): "What is your estimated cost per free signup?"
- **Type:** number
- **Guidance:** "Marketing spend / signups. Typical range: $10-$100"
- **Example:** "$25"

**Auto-calculate:**
```
Paid conversions per month = Free Users × Conversion Rate
Example: 2,000 × 5% = 100 customers/month

PLG CAC = Cost per Free Signup / Conversion Rate
Example: $25 / 5% = $500 CAC
```

#### Channel: Partnerships

**Question** (AskUserQuestion [q: partner_count]): "How many active channel partners do you expect?"
- **Type:** integer
- **Example:** "5 partners"

**Question** (AskUserQuestion [q: partner_commission_percent]): "What is the average commission per customer?"
- **Type:** number
- **Guidance:** "Typically 10-30% of first year revenue or flat fee"
- **Example:** "20% of ACV"

**Question** (AskUserQuestion [q: partner_acv]): "What is your average ACV?"
- **Type:** number
- **Reference:** From assumptions.json or prompt
- **Example:** "$10,000"

**Question** (AskUserQuestion [q: customers_per_partner_quarter]): "How many customers per partner per quarter?"
- **Type:** integer
- **Guidance:** "Typical range: 1-5 customers/partner/quarter"
- **Example:** "2 customers/partner/quarter"

**Auto-calculate:**
```
Customers per month = (Partners × Customers per Partner per Quarter) / 3
Example: (5 × 2) / 3 = 3.3 customers/month

Partnership CAC = Commission % × ACV
Example: 20% × $10,000 = $2,000 CAC
```

#### Channel: Field Sales (Enterprise)

**Question** (AskUserQuestion [q: enterprise_ae_count]): "How many enterprise AEs will you have?"
- **Type:** integer
- **Example:** "3 enterprise AEs"

**Question** (AskUserQuestion [q: enterprise_ae_annual_cost]): "What is the fully-loaded cost per enterprise AE?"
- **Type:** number
- **Guidance:** "Salary + commission + travel + overhead = typically $250K-$400K"
- **Default:** $300,000
- **Example:** "$320,000"

**Question** (AskUserQuestion [q: deals_per_enterprise_ae_year]): "How many enterprise deals per AE per year?"
- **Type:** integer
- **Guidance:** "Typical range: 3-8 deals/year depending on deal size"
- **Example:** "5 deals/year"

**Auto-calculate:**
```
Customers per month = (Enterprise AEs × Deals per Year) / 12
Example: (3 × 5) / 12 = 1.25 customers/month

Monthly Enterprise Sales Cost = (Enterprise AEs × AE Cost) / 12
Example: (3 × $320K) / 12 = $80,000/month

Enterprise CAC = Monthly Cost / Customers
Example: $80,000 / 1.25 = $64,000 CAC
```

#### Channel: Community-Led Growth

**Question** (AskUserQuestion [q: community_monthly_investment]): "What is your investment in community building?"
- **Type:** number
- **Guidance:** "Community manager salary + events + tools"
- **Example:** "$10,000/month"

**Question** (AskUserQuestion [q: community_conversions_month]): "How many community-driven conversions per month?"
- **Type:** integer
- **Guidance:** "Word-of-mouth, user groups, advocates"
- **Example:** "15 customers/month"

**Auto-calculate:**
```
Community CAC = Community Investment / Conversions
Example: $10,000 / 15 = $667 CAC
```

### Phase 5: Calculate Blended Metrics

**Auto-calculate overall projections:**

**Blended CAC:**
```
Blended CAC = (Sum of all channel costs) / (Sum of all channel customers)

Example:
Total monthly cost: $174,167
Total monthly customers: 177
Blended CAC: $984
```

**Channel Mix Analysis:**
```
Channel Distribution:
- Inbound: 28% of customers (50/177)
- Outbound: 4% of customers (7.5/177)
- PLG: 56% of customers (100/177)
- Partnerships: 2% of customers (3.3/177)
- Field: 1% of customers (1.25/177)
- Community: 8% of customers (15/177)
```

**CAC Efficiency Ranking:**
```
Most efficient (lowest CAC):
1. Inbound: $400 CAC
2. Community: $667 CAC
3. PLG: $500 CAC

Least efficient (highest CAC):
1. Enterprise: $64,000 CAC (justified by $100K+ ACV)
2. Outbound: $8,556 CAC
3. Partnership: $2,000 CAC
```

**CAC Payback Period:**
```
For each channel:
CAC Payback = CAC / (Monthly Revenue per Customer × Gross Margin)

Example (Inbound):
ACV: $12,000
Monthly revenue: $1,000
Gross margin: 75%
CAC payback: $400 / ($1,000 × 75%) = 0.53 months (16 days) ✅ EXCELLENT

Example (Enterprise):
ACV: $120,000
Monthly revenue: $10,000
Gross margin: 80%
CAC payback: $64,000 / ($10,000 × 80%) = 8 months ✅ GOOD
```

**LTV:CAC Ratio:**
```
For each segment/channel:
LTV = (ACV / 12) × (1 / Monthly Churn Rate) × Gross Margin
Or equivalently: LTV = ACV × (1 / Annual Churn Rate) × Gross Margin
LTV:CAC = LTV / CAC

Example (SMB via Inbound):
ACV: $12,000/year
Churn: 3%/month (33.33 month lifetime = 2.78 years)
Gross Margin: 75%

LTV = ($12,000 / 12) × (1 / 0.03) × 0.75
    = $1,000/month × 33.33 months × 0.75
    = $25,000

CAC: $400
LTV:CAC: $25,000 / $400 = 62.5:1 ✅ EXCELLENT

Note: Very high LTV:CAC may indicate underestimated CAC at scale.
```

### Phase 6: Recommendations and Validation

**Financial Health Assessment:**

**Market Opportunity Health:**
- ✅ **EXCELLENT:** SOM > $50M AND TAM/SAM/SOM ratio is reasonable (<10% penetration)
- ⚠️ **GOOD:** SOM $10M-$50M AND penetration < 15%
- ⚠️ **Warning:** SOM < $10M OR penetration > 20%
- ❌ **Critical:** SOM < $5M OR unrealistic penetration (>30%)

**CAC Health by Segment:**
- ✅ **EXCELLENT:** CAC payback < 6 months AND LTV:CAC > 5:1
- ✅ **GOOD:** CAC payback 6-12 months AND LTV:CAC 3-5:1
- ⚠️ **Warning:** CAC payback 12-18 months OR LTV:CAC 1.5-3:1
- ❌ **Critical:** CAC payback > 18 months OR LTV:CAC < 1.5:1

**Channel Strategy Recommendations:**

Based on analysis, provide:

1. **Primary channel recommendation:**
   - "Focus on [channel] as primary acquisition channel"
   - "Rationale: Lowest CAC ($X), shortest payback (X months), scalable"

2. **Secondary channels:**
   - "Supplement with [channel] for [segment]"
   - "Experiment with [channel] once primary channel is proven"

3. **Avoid/delay:**
   - "Delay [channel] until [milestone]"
   - "Reason: CAC too high ($X) relative to ACV ($Y)"

4. **Segment prioritization:**
   - "Target [segment] first: Highest WTP, lowest CAC, best LTV:CAC"
   - "Enter [segment] later: Requires [capability/scale]"

5. **Pricing validation:**
   - "Current pricing ($X) validated by market WTP"
   - "Consider [adjustment] based on segment analysis"

6. **Risk flags:**
   - ⚠️ "TAM assumption relies on market creation (higher risk)"
   - ⚠️ "CAC estimates based on assumptions, not actuals (test with pilots)"
   - ⚠️ "High competitive intensity may increase CAC over time"

## Output

### File 1: `.product-finance/discovery-report.json`

Structured data for downstream analysis:

```json
{
  "market_sizing": {
    "tam": {
      "value": 5000000000,
      "calculation_method": "bottom_up",
      "assumptions": {
        "potential_customers": 500000,
        "target_acv": 10000
      }
    },
    "sam": {
      "value": 960000000,
      "filters": {
        "geographic": "north_america",
        "customer_size": "smb_mid_market",
        "channel": "direct_self_service"
      },
      "sam_to_tam_ratio": 0.192
    },
    "som": {
      "value": 19200000,
      "timeframe_years": 3,
      "market_share_pct": 2.0,
      "som_to_sam_ratio": 0.02
    }
  },
  "customer_segments": [
    {
      "segment_name": "SMB SaaS Companies",
      "potential_customers": 100000,
      "target_acv": 12000,
      "conversion_rate_pct": 15,
      "acquisition_difficulty": "medium",
      "revenue_opportunity": 180000000,
      "willingness_to_pay": 12000,
      "wtp_source": ".jtbd-market-discovery/results/20261102T101500Z-discover-acme-acme-0001.json"
    },
    {
      "segment_name": "Mid-Market Tech",
      "potential_customers": 30000,
      "target_acv": 45000,
      "conversion_rate_pct": 20,
      "acquisition_difficulty": "medium",
      "revenue_opportunity": 270000000
    }
  ],
  "revenue_opportunity": {
    "total": 450000000,
    "penetration_required_for_som": 4.3,
    "by_segment": [
      {
        "segment": "SMB SaaS Companies",
        "opportunity": 180000000,
        "percentage": 40
      },
      {
        "segment": "Mid-Market Tech",
        "opportunity": 270000000,
        "percentage": 60
      }
    ]
  },
  "cac_by_channel": [
    {
      "channel": "inbound_marketing",
      "cac": 400,
      "customers_per_month": 50,
      "monthly_cost": 20000,
      "cac_payback_months": 0.53,
      "ltv_cac_ratio": 61.9,
      "efficiency_rank": 1
    },
    {
      "channel": "outbound_sales",
      "cac": 8556,
      "customers_per_month": 7.5,
      "monthly_cost": 64167,
      "cac_payback_months": 11.4,
      "ltv_cac_ratio": 2.9,
      "efficiency_rank": 5
    },
    {
      "channel": "product_led_growth",
      "cac": 500,
      "customers_per_month": 100,
      "monthly_cost": 50000,
      "cac_payback_months": 0.67,
      "ltv_cac_ratio": 49.5,
      "efficiency_rank": 3
    },
    {
      "channel": "partnerships",
      "cac": 2000,
      "customers_per_month": 3.3,
      "monthly_cost": 6600,
      "cac_payback_months": 2.67,
      "ltv_cac_ratio": 12.4,
      "efficiency_rank": 4
    },
    {
      "channel": "field_sales",
      "cac": 64000,
      "customers_per_month": 1.25,
      "monthly_cost": 80000,
      "cac_payback_months": 8.0,
      "ltv_cac_ratio": 3.9,
      "efficiency_rank": 6,
      "notes": "High CAC justified by $120K+ ACV enterprise deals"
    },
    {
      "channel": "community",
      "cac": 667,
      "customers_per_month": 15,
      "monthly_cost": 10000,
      "cac_payback_months": 0.89,
      "ltv_cac_ratio": 37.1,
      "efficiency_rank": 2
    }
  ],
  "blended_metrics": {
    "blended_cac": 984,
    "total_customers_per_month": 177,
    "total_monthly_cost": 174167,
    "weighted_cac_payback_months": 2.1,
    "weighted_ltv_cac_ratio": 25.1
  },
  "jtbd_integration": {
    "data_imported": true,
    "source_file": ".jtbd-market-discovery/results/20261102T101500Z-discover-acme-acme-0001.json",
    "segments_imported": 2,
    "wtp_data_available": true
  },
  "health_assessment": {
    "market_opportunity": "excellent",
    "cac_efficiency": "excellent",
    "ltv_cac_health": "excellent",
    "overall": "excellent"
  },
  "recommendations": {
    "primary_channel": "product_led_growth",
    "primary_rationale": "Lowest CAC ($500), high volume (100 customers/month), scalable",
    "secondary_channels": ["inbound_marketing", "community"],
    "avoid_channels": [],
    "target_segment_priority": [
      "SMB SaaS Companies",
      "Mid-Market Tech"
    ],
    "pricing_validation": "Validated: $12K ACV aligned with segment WTP",
    "risk_flags": [
      "CAC estimates based on assumptions - validate with pilot campaigns",
      "PLG conversion rate (5%) needs validation through testing"
    ]
  },
  "metadata": {
    "created_at": "2026-01-23T10:00:00Z",
    "analysis_stage": "discovery",
    "confidence_level": "medium",
    "data_sources": ["user_provided", "jtbd_analysis", "industry_benchmarks"]
  }
}
```

### File 2: `.product-finance/discovery-report.md`

Stakeholder-ready markdown report:

```markdown
# Discovery Stage Financial Analysis

**Analysis Date:** January 23, 2026
**Market Opportunity:** EXCELLENT
**CAC Efficiency:** EXCELLENT
**Overall Health:** EXCELLENT

---

## Executive Summary

**Market Opportunity:**
- TAM: $5.0B (500K potential customers × $10K ACV)
- SAM: $960M (19% of TAM - North America, SMB/Mid-Market)
- SOM: $19.2M (2% of SAM - 3-year target)

**Revenue Opportunity:**
- Total addressable: $450M across 2 segments
- SOM requires 4.3% penetration (realistic)

**Customer Acquisition:**
- Blended CAC: $984
- CAC Payback: 2.1 months (EXCELLENT)
- LTV:CAC Ratio: 25:1 (EXCELLENT)

**Recommendation:** Proceed with product development. Strong market opportunity with highly efficient acquisition channels validated.

---

## Market Sizing Analysis

### TAM: Total Addressable Market
**Value:** $5.0 Billion

**Calculation Method:** Bottom-Up
- Potential customers: 500,000 companies
- Target ACV: $10,000
- TAM = 500,000 × $10,000 = $5.0B

**Assumptions:**
- ICP: B2B SaaS companies with 10-200 employees
- Geographic scope: Global (narrowed to North America in SAM)
- Pricing validated against willingness-to-pay research

### SAM: Serviceable Addressable Market
**Value:** $960 Million (19% of TAM)

**Filters Applied:**
- **Geographic:** North America only (40% of TAM)
- **Customer Size:** SMB + Mid-Market, excluding enterprise (60% of filtered TAM)
- **Channel:** Direct sales + Self-service (80% of reachable)

**Rationale:**
- Initial focus on North American market for operational efficiency
- SMB/Mid-Market segments have best product-market fit
- Direct and self-service channels match go-to-market capability

**Validation:** ✅ 19% SAM/TAM ratio is realistic and defensible

### SOM: Serviceable Obtainable Market
**Value:** $19.2 Million (2% of SAM, 0.4% of TAM)

**Timeframe:** 3 years

**Market Share Target:** 2.0% of SAM

**Competitive Context:**
- Competitive intensity: Medium
- Several competitors with differentiated positioning
- 2% share is realistic with strong execution

**Validation:** ✅ Conservative market share target, achievable with proper execution

---

## Customer Segments & Revenue Opportunity

### Segment 1: SMB SaaS Companies
**Opportunity:** $180M (40% of total)

**Profile:**
- Potential customers: 100,000 companies
- Target ACV: $12,000/year
- Conversion rate: 15%
- Acquisition difficulty: Medium

**Willingness-to-Pay:** $12,000 (validated via JTBD analysis)

**Segment Priority:** PRIMARY TARGET
- Strong product-market fit
- Proven willingness to pay
- Efficient acquisition channels

### Segment 2: Mid-Market Tech
**Opportunity:** $270M (60% of total)

**Profile:**
- Potential customers: 30,000 companies
- Target ACV: $45,000/year
- Conversion rate: 20%
- Acquisition difficulty: Medium

**Segment Priority:** SECONDARY TARGET
- Higher ACV justifies higher CAC
- Requires more mature sales process
- Enter after proving SMB segment

---

## Customer Acquisition Cost (CAC) by Channel

### Channel Efficiency Ranking

| Rank | Channel | CAC | Customers/Month | Payback | LTV:CAC | Status |
|------|---------|-----|-----------------|---------|---------|--------|
| 1 | Inbound Marketing | $400 | 50 | 0.5 mo | 62:1 | ✅ EXCELLENT |
| 2 | Community | $667 | 15 | 0.9 mo | 37:1 | ✅ EXCELLENT |
| 3 | Product-Led Growth | $500 | 100 | 0.7 mo | 50:1 | ✅ EXCELLENT |
| 4 | Partnerships | $2,000 | 3 | 2.7 mo | 12:1 | ✅ GOOD |
| 5 | Outbound Sales | $8,556 | 8 | 11.4 mo | 3:1 | ✅ GOOD |
| 6 | Enterprise Field | $64,000 | 1 | 8.0 mo | 4:1 | ✅ GOOD* |

*Enterprise CAC justified by $120K+ ACV deals

### Blended Metrics
- **Blended CAC:** $984
- **Total Customers/Month:** 177
- **Weighted Payback:** 2.1 months ✅ EXCELLENT
- **Weighted LTV:CAC:** 25:1 ✅ EXCELLENT

### Channel Mix (by volume)
- Product-Led Growth: 56% of customers (primary driver)
- Inbound Marketing: 28% of customers
- Community: 8% of customers
- Outbound Sales: 4% of customers
- Partnerships: 2% of customers
- Enterprise Field: 1% of customers

---

## Detailed Channel Analysis

### 1. Inbound Marketing (Rank #1 Efficiency)
**CAC:** $400 | **Payback:** 16 days | **LTV:CAC:** 62:1

**Investment:**
- Monthly marketing spend: $20,000
- Expected MQLs: 500/month
- MQL-to-customer rate: 10%

**Output:** 50 customers/month

**Assessment:** ✅ EXCELLENT
- Lowest CAC of scalable channels
- Fast payback (16 days)
- Highly efficient for SMB segment

**Recommendation:** Primary acquisition channel for SMB segment

---

### 2. Product-Led Growth (Rank #3 Efficiency, Rank #1 Volume)
**CAC:** $500 | **Payback:** 20 days | **LTV:CAC:** 50:1

**Investment:**
- Free user acquisition: 2,000/month
- Cost per signup: $25
- Free-to-paid conversion: 5%

**Output:** 100 customers/month (highest volume)

**Assessment:** ✅ EXCELLENT
- Highest volume channel
- Low CAC with fast payback
- Scalable with product improvements

**Recommendation:** Primary growth engine. Focus on improving conversion rate from 5% → 7%+ for even better unit economics.

**Risk:** 5% conversion assumption needs validation. Test with pilot.

---

### 3. Community-Led Growth (Rank #2 Efficiency)
**CAC:** $667 | **Payback:** 27 days | **LTV:CAC:** 37:1

**Investment:**
- Community building: $10,000/month
- Community manager + events + tools

**Output:** 15 customers/month

**Assessment:** ✅ EXCELLENT
- High-quality, word-of-mouth customers
- Strong retention typically
- Scales with product adoption

**Recommendation:** Invest early to build brand and advocacy. Lower volume but high quality.

---

### 4. Outbound Sales (Rank #5 Efficiency)
**CAC:** $8,556 | **Payback:** 11.4 months | **LTV:CAC:** 3:1

**Investment:**
- 3 SDRs @ $110K/year
- 2 AEs @ $220K/year
- Monthly cost: $64,167

**Output:** 7.5 customers/month

**Assessment:** ⚠️ WARNING - CAC payback near 12-month threshold

**Rationale:**
- Higher CAC but targets mid-market segment ($45K ACV)
- 11.4 month payback acceptable for higher-value customers
- LTV:CAC of 3:1 meets healthy threshold

**Recommendation:** Delay until PLG and inbound are proven. Use for mid-market expansion in Year 2.

---

### 5. Enterprise Field Sales (Rank #6 Efficiency by CAC, but justified)
**CAC:** $64,000 | **Payback:** 8 months | **LTV:CAC:** 4:1

**Investment:**
- 3 Enterprise AEs @ $320K/year
- Monthly cost: $80,000

**Output:** 1.25 customers/month (15/year)

**Assessment:** ✅ GOOD (high CAC justified by high ACV)

**Rationale:**
- Enterprise deals average $120K+ ACV
- 8-month payback acceptable for enterprise
- LTV:CAC of 4:1 exceeds healthy threshold (3:1+)

**Recommendation:** Add in Year 2 after proving product-market fit with SMB. Enterprise requires mature product and case studies.

---

### 6. Partnerships (Rank #4 Efficiency)
**CAC:** $2,000 | **Payback:** 2.7 months | **LTV:CAC:** 12:1

**Investment:**
- 5 channel partners
- Commission: 20% of first-year ACV

**Output:** 3.3 customers/month

**Assessment:** ✅ GOOD

**Recommendation:** Opportunistic. Build partnerships as they arise but don't lead with this channel.

---

## Go-to-Market Strategy Recommendations

### Phase 1: Year 1 - Prove SMB Product-Market Fit
**Primary Channel:** Product-Led Growth (PLG)
- Target: 100 customers/month via free-to-paid conversion
- Investment: Optimize onboarding, improve activation metrics
- Goal: Achieve 7% free-to-paid conversion (from 5% assumption)

**Secondary Channel:** Inbound Marketing
- Target: 50 customers/month via content + paid ads
- Investment: $20K/month marketing spend
- Goal: Validate $400 CAC and 10% MQL conversion

**Tertiary Channel:** Community-Led Growth
- Target: 15 customers/month via advocacy
- Investment: $10K/month community building
- Goal: Build brand and word-of-mouth engine

**Year 1 Targets:**
- Total customers: ~2,000 (165/month average)
- Blended CAC: ~$600
- ARR: ~$24M (at $12K ACV)

### Phase 2: Year 2 - Scale and Expand to Mid-Market
**Add Channel:** Outbound Sales
- Target: Mid-market segment ($45K ACV)
- Hire: 3 SDRs + 2 AEs
- Goal: 8 mid-market customers/month

**Continue Scaling:** PLG + Inbound + Community
- Increase spend to capture more volume
- Improve conversion rates through optimization

**Year 2 Targets:**
- Total customers: ~4,500 cumulative
- ARR: ~$54M
- Blended CAC: ~$800 (increases with outbound)

### Phase 3: Year 3 - Enterprise Expansion
**Add Channel:** Enterprise Field Sales
- Target: Enterprise segment ($120K+ ACV)
- Hire: 3 Enterprise AEs
- Goal: 15 enterprise deals/year

**Year 3 Targets:**
- Total customers: ~7,000 cumulative
- ARR: ~$84M (includes enterprise deals)
- SOM achievement: On track for $19.2M SOM by end of year

---

## JTBD Integration Summary

**Data Source:** the jtbd result file the run read, in `.jtbd-market-discovery/results/`

**Segments Imported:** 2 customer segments with WTP data

**Key Insights:**
- SMB segment WTP validated at $12K/year
- Economic value calculations support pricing strategy
- Customer needs aligned with product capabilities

**Integration Quality:** ✅ EXCELLENT
- Financial projections grounded in customer research
- WTP data reduces pricing risk
- Segment priorities validated by both financial and customer data

---

## Risk Assessment & Mitigation

### Risk 1: CAC Assumptions Unvalidated
**Severity:** MEDIUM
**Mitigation:**
- Run pilot campaigns before scaling spend
- Start with $5K test budgets per channel
- Validate conversion rates with real data

### Risk 2: PLG Conversion Rate (5%) May Be Optimistic
**Severity:** MEDIUM
**Mitigation:**
- Benchmark against similar products
- Build excellent onboarding to maximize activation
- Target 7% conversion through product improvements

### Risk 3: Market Share (2% of SAM) Requires Execution Excellence
**Severity:** LOW
**Mitigation:**
- Conservative 3-year target
- Strong unit economics provide buffer
- Multiple efficient channels reduce dependency risk

### Risk 4: Competitive Intensity May Increase CAC Over Time
**Severity:** MEDIUM
**Mitigation:**
- Focus on differentiation (product quality, customer success)
- Build community/brand moat early
- Diversify across multiple channels

---

## Key Metrics to Track

**Market Penetration:**
- Track % of SAM captured quarterly
- Monitor competitive wins/losses
- Measure brand awareness in target segments

**Channel Performance:**
- Actual CAC vs. projected by channel
- Conversion rates at each funnel stage
- CAC payback period by cohort

**Segment Performance:**
- Revenue mix by segment (SMB vs. Mid-Market)
- ACV by segment (actual vs. target)
- LTV by segment (track churn and expansion)

**Go-to-Market Efficiency:**
- Blended CAC trend (should stay < $1,500)
- LTV:CAC ratio (target 3:1 minimum)
- CAC payback period (target < 12 months)

---

## Financial Validation

### Market Opportunity: ✅ EXCELLENT
- TAM $5B is defensible (bottom-up calculation)
- SAM $960M is realistic (19% of TAM with clear filters)
- SOM $19.2M is achievable (2% market share in 3 years)
- Penetration requirement (4.3%) is conservative

### Unit Economics: ✅ EXCELLENT
- Blended CAC $984 with 2.1 month payback
- LTV:CAC ratio 25:1 (excellent, well above 3:1 threshold)
- Multiple efficient channels reduce risk
- Healthy margins support growth investment

### Overall Assessment: ✅ PROCEED
Strong market opportunity with validated customer demand (JTBD research) and efficient acquisition channels. Financial projections are conservative and achievable.

**Recommended Next Steps:**
1. Run pilot campaigns to validate CAC assumptions ($5K budget per channel)
2. Build MVP focused on SMB segment needs
3. Implement PLG onboarding to maximize free-to-paid conversion
4. Develop content marketing engine for inbound lead generation
5. Launch community initiative to build brand and advocacy
6. Re-run financial analysis after 6 months with actual data

---

**Analysis prepared by:** Product Finance Plugin v0.1.0
**Methodology:** TAM/SAM/SOM framework + Channel-specific CAC estimation + JTBD integration
**Confidence Level:** MEDIUM (assumptions-based, requires validation with real data)
```

### Console Output

**Summary displayed to user:**

```
Discovery Financial Analysis Complete!
======================================

Market Opportunity
------------------
TAM: $5.0B (Total Addressable Market)
SAM: $960M (Serviceable Addressable Market - 19% of TAM)
SOM: $19.2M (3-year target - 2% of SAM)
Market Opportunity Health: ✅ EXCELLENT

Customer Segments
-----------------
1. SMB SaaS Companies
   - Opportunity: $180M
   - Target ACV: $12,000
   - Priority: PRIMARY (target first)

2. Mid-Market Tech
   - Opportunity: $270M
   - Target ACV: $45,000
   - Priority: SECONDARY (expand to in Year 2)

Total Revenue Opportunity: $450M
SOM Penetration Required: 4.3% (realistic)

Customer Acquisition Costs
---------------------------
Top 3 Most Efficient Channels:
1. Inbound Marketing: $400 CAC, 0.5 mo payback ✅
2. Community: $667 CAC, 0.9 mo payback ✅
3. Product-Led Growth: $500 CAC, 0.7 mo payback ✅

Blended Metrics:
- Blended CAC: $984
- Total Customers/Month: 177
- CAC Payback: 2.1 months ✅ EXCELLENT
- LTV:CAC Ratio: 302:1 ✅ EXCEPTIONAL

JTBD Integration
----------------
✅ Imported segment data from .jtbd-market-discovery/results/<file>
✅ 2 customer segments with WTP data
✅ Pricing validated against willingness-to-pay research

Go-to-Market Recommendation
----------------------------
PRIMARY CHANNEL: Product-Led Growth
- Highest volume (100 customers/month)
- Low CAC ($500)
- Scalable with product improvements

SECONDARY CHANNELS: Inbound Marketing + Community

SEGMENT PRIORITY:
1. SMB SaaS Companies (Year 1)
2. Mid-Market Tech (Year 2)
3. Enterprise (Year 3)

Overall Assessment
------------------
Market Opportunity: ✅ EXCELLENT
CAC Efficiency: ✅ EXCELLENT
Unit Economics: ✅ EXCELLENT

RECOMMENDATION: PROCEED WITH PRODUCT DEVELOPMENT
Strong market opportunity with efficient acquisition channels.

Files Generated
---------------
✓ .product-finance/discovery-report.json (structured data)
✓ .product-finance/discovery-report.md (stakeholder report)

Next Steps
----------
1. Run pilot campaigns to validate CAC assumptions ($5K/channel)
2. Build MVP focused on SMB segment
3. Implement PLG onboarding for conversion optimization
4. Develop inbound marketing content strategy
5. Launch community building initiative
6. Run `/product-finance:feature-roi` to prioritize features
7. Run `/product-finance:unit-economics` after 6 months with actual data
```

## Implementation Notes

### For Claude Code Agent

**Data Collection Strategy:**
1. **Check for existing data first:**
   - Look for `.product-finance/assumptions.json`
   - In a person's run only, look for the jtbd result that **Person run** names
   - Pre-fill any available data

2. **Smart prompting:**
   - Ask only for data that is not yet available
   - Explain WHY each data point matters (business context)
   - Provide examples and benchmarks
   - Show calculations in real-time as data is collected

3. **Progressive disclosure:**
   - Start with required data (market sizing)
   - Add optional detail (channel breakdown)
   - Skip sections if user wants quick analysis

**Validation Rules:**

**Market Sizing:**
- TAM should be > $100M for venture-scale businesses
- SAM/TAM ratio typically 10-50% (warn if outside)
- SOM/SAM ratio typically 1-10% (warn if >15%)
- SOM should be $10M+ for Series A+ companies

**CAC Health:**
- CAC payback should be < 12 months (warn if > 18)
- LTV:CAC should be > 3:1 (warn if < 2:1)
- If LTV:CAC > 100:1, likely underestimating CAC (flag for user)

**Channel Mix:**
- No single channel should be >70% of volume (concentration risk)
- High-CAC channels need high-ACV justification
- PLG conversion rate 2-10% is typical (validate assumptions)

**Python Script Integration:**

In a person's run, call `scripts/market_sizing_calculator.py` with the collected data, as one command:
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/market_sizing_calculator.py --assumptions .product-finance/assumptions.json --output .product-finance/discovery-report.json --jtbd-data <jtbd file>
```

In a person's run only, pass `--jtbd-data` the jtbd result file that **Person run** read, else leave the option out. When the script exits with any code other than 0 and 3, whether it stops before it reads the file or after, work the figures out with the formulas above, with no code at all, and end each result's `method` with: Computed by the model from the formula stated in the command; no script ran. An exit with code 3 is not that case: follow **Calculator run**. A plugin run reads no `assumptions.json`, so it works the figures out with the formulas above.

**JTBD Integration Logic:**

The script reads the segments from `assumptions.json`, so do the merge that **Person run** describes before it runs. It records the file passed as `--jtbd-data` in `jtbd_integration.source_file`. Its `segments_imported` and `wtp_data_available` count the person's segments, not the matches; the "Found JTBD analysis" line reports the matches.

**Error Handling:**
- If no market data available and user skips, create placeholder with warnings
- If CAC calculations result in negative/zero, prompt for valid inputs
- If LTV:CAC is impossibly high (>500:1), warn about assumption validity

**Data Persistence:**
- Save to `.product-finance/discovery-report.json` (structured)
- Save to `.product-finance/discovery-report.md` (markdown report)
- Update `.product-finance/assumptions.json` with market and CAC data
- Create `.product-finance/reports/` directory if it doesn't exist

### Health Status Logic

**Market Opportunity Health:**
```python
if som > 50_000_000 and som/sam < 0.1:
    health = "excellent"
elif som >= 10_000_000 and som/sam < 0.15:
    health = "good"
elif som < 10_000_000 or som/sam > 0.2:
    health = "warning"
else:
    health = "critical"
```

**CAC Efficiency Health:**
```python
if cac_payback < 6 and ltv_cac > 5:
    health = "excellent"
elif cac_payback <= 12 and ltv_cac >= 3:
    health = "good"
elif cac_payback <= 18 or ltv_cac >= 1.5:
    health = "warning"
else:
    health = "critical"
```

### Channel Recommendations

**Automatic recommendations based on metrics:**

**If PLG has lowest CAC and highest volume:**
- "Focus on Product-Led Growth as primary channel"
- "Optimize free-to-paid conversion rate for maximum efficiency"

**If Inbound CAC < $1000 and payback < 6 months:**
- "Inbound marketing is highly efficient - scale spend"

**If Outbound CAC > 10 months payback:**
- "Delay outbound sales until product-market fit is proven"
- "Outbound economics improve with higher ACV segments"

**If Enterprise CAC > $50K but ACV > $100K:**
- "Enterprise channel justified by high ACV"
- "Add enterprise sales in Year 2 with case studies"

**If multiple channels have CAC < $1000:**
- "Diversify across multiple efficient channels to reduce risk"

## Examples

### Example 1: SaaS Product with JTBD Data

**Scenario:** Post-JTBD analysis, have WTP data

**Flow:**
1. In a person's run only, the discover command detects a jtbd result in `.jtbd-market-discovery/results/`
2. Sets the willingness to pay of 3 segments: $8K, $18K, $35K
3. User confirms/adjusts segment data
4. User estimates CAC for 3 channels: Inbound ($600), PLG ($400), Outbound ($5K)
5. Calculate: Blended CAC $800, payback 3.2 months, LTV:CAC 12:1
6. Recommendation: Focus on PLG + Inbound for SMB segment ($8K ACV)

**Output:** Full discovery report with validated pricing and channel strategy

### Example 2: Pre-JTBD Market Sizing

**Scenario:** Early market analysis without customer research

**Flow:**
1. User selects bottom-up TAM calculation
2. 200K potential customers × $15K ACV = $3B TAM
3. Apply filters: SAM = $600M (20% of TAM)
4. Target 1.5% market share = $9M SOM (3 years)
5. Manual segment definition: 2 segments
6. Estimate CAC for 2 channels: Inbound ($800), Outbound ($8K)
7. Warning: "Consider running JTBD analysis to validate WTP assumptions"

**Output:** Discovery report with recommendation to validate with customer research

### Example 3: Freemium Product

**Scenario:** PLG-focused with aggressive free tier

**Flow:**
1. TAM/SAM/SOM: $2B → $400M → $12M
2. Segments: 1 primary (SMB)
3. Channels: PLG only (10K free signups/month, 8% conversion)
4. CAC: $50 per free signup, $625 effective CAC
5. Calculate: 800 paid customers/month, $5K ACV
6. Blended metrics: CAC payback 1.8 months, LTV:CAC 48:1

**Output:** PLG-optimized strategy with conversion rate optimization focus

## Success Criteria

1. **Market sizing is defensible:** TAM/SAM/SOM based on clear assumptions
2. **Revenue opportunity is realistic:** Segments have validated WTP (ideally from JTBD)
3. **CAC estimates are grounded:** Based on channel benchmarks or pilot data
4. **JTBD integration works:** A person's run merges a jtbd result into the person's segments; a plugin run reads the result `inputs_from` names
5. **Recommendations are actionable:** Clear channel priorities and segment focus
6. **Reports are professional:** Suitable for investor/board presentations
7. **Data flows to next commands:** Assumptions saved for unit-economics and feature-roi analysis

## References

- **Schema:** `templates/assumptions.json` - Market and segment data structure
- **JTBD Integration:** `.jtbd-market-discovery/results/` - segment and willingness-to-pay results
- **Methodology:** `BRAINSTORMING.md` - TAM/SAM/SOM framework and CAC estimation
- **Benchmarks:** Industry-standard CAC by channel and LTV:CAC ratios

## Agent Dispatch

Read `${CLAUDE_PLUGIN_ROOT}/agents/market-analyzer.md` and follow it in this session: it asks the person, and a subagent cannot.

**Process:**
1. Agent loads assumptions from `.product-finance/assumptions.json`
2. In a person's run only, the agent checks for JTBD data as **Person run** in this command says
3. Agent uses skills: market-sizing, cac-estimation, opportunity-analysis
4. Agent interacts with user for data collection (if needed)
5. Agent generates discovery analysis artifacts

**Skills Used:**
- `market-sizing` - TAM/SAM/SOM calculation and validation
- `cac-estimation` - Customer acquisition cost modeling by channel
- `opportunity-analysis` - Revenue opportunity sizing by segment
- `jtbd-integration` - Import and map JTBD willingness-to-pay data
- `benchmark-comparison` - Compare metrics against industry standards

**Output:**
- `.product-finance/discovery-report.json` - Structured discovery data
- `.product-finance/discovery-report.md` - Stakeholder-ready report
- Updates to `.product-finance/assumptions.json` with market data

**User Interaction:** High (validates market assumptions, confirms segments, reviews CAC estimates)

---

## Integration with Other Commands

**Upstream:**
- `/product-finance:setup` provides baseline assumptions and pricing
- jtbd-market-discovery writes segment and willingness-to-pay results to `.jtbd-market-discovery/results/`

**Downstream:**
- `/product-finance:feature-roi` uses SOM and CAC for feature prioritization
- `/product-finance:unit-economics` refines CAC with actual data
- `/product-finance:health-check` validates market opportunity health

**Data Flow:**
- Reads from `.product-finance/assumptions.json`
- In a person's run, reads the jtbd result that **Person run** accepts; a plugin run reads the one **Plugin run** names
- Writes to `.product-finance/discovery-report.json`
- Updates `.product-finance/assumptions.json` with market data

---

**Financial Intelligence as Code** - Quantify market opportunity, validate pricing, and optimize customer acquisition before building.
