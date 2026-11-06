## Integration with Other Plugins

### To brainstorm Plugin

```
> "Brainstorm solutions for minimizing likelihood of underestimating departure time.
   Target segment: Crisis Avoiders (business travelers, high importance 9.8).
   Current solutions failing with 67% gap."
```

### To PRD Plugin

```
> "Create PRD for intelligent navigation solution targeting Crisis Avoiders segment.
   Key requirements:
   - AI-powered departure time predictions
   - Real-time traffic-aware routing
   - Proactive delay alerts
   Value: $38,400/year per customer, price at $960/month"
```

### To Design Plugin

```
> "Design solution addressing these needs:
   1. Minimize underestimating departure time (importance 9.8)
   2. Minimize time in traffic (importance 9.5)
   3. Minimize travel uncertainty (importance 9.2)
   For segment: Professionals who travel 60+ times/month"
```

---

## Executive Summary Template

```markdown
# Market Opportunity Analysis
# Job: [Job Name]
# Date: [Date]

## Key Findings

**Top Opportunity:** [Need statement] (Score: X.X/20)

**Market Characterization:**
- X severely underserved needs (score >14)
- Primary value cluster: [Theme]
- Total addressable value: $X per customer/year

**Target Segment:** [Segment name] (X% of market)
- Avg importance: X.X/10 (severely underserved)
- EVC: $X/year per customer
- Optimal price: $X/month (25% of EVC, 4x ROI)

**Solution Focus:** [1-2 sentence description]

**Strategic Recommendation:**
[2-3 sentences on what to build, who to target, how to price]

## Next Steps

1. Use findings to inform PRD development
2. Prototype solution addressing top 5 needs
3. Validate with 10-15 target customers
4. Iterate based on feedback
5. Launch to Crisis Avoiders segment first
```

---

**Phase 10 Complete!**

---

# Platform Compatibility

This section explains how the JTBD Market Discovery methodology works on both Claude Code (full Python features) and Claude.ai Web (AI-powered fallbacks). Both platforms share the same SKILL.md, but use different tools to achieve the same outcomes.

**Target Feature Parity:** 80-90% functionality on web vs Claude Code

---

## Claude Code (CLI) - Full Features ✅

**Available capabilities:**
- ✅ Python script execution (opportunity_scorer.py, evc_calculator.py, segmentation_engine.py, wtp_validator.py)
- ✅ Local file system access (CSV import/export)
- ✅ Scikit-learn K-means clustering (exact mathematical segmentation)
- ✅ Pandas DataFrame operations (precise calculations)
- ✅ Full automation (scripts run end-to-end)

**Workflow:**
1. Generate needs → CSV export to local file
2. Deploy survey → CSV import from local file
3. Run Python scripts → Automated analysis with exact calculations
4. Export results → JSON/Markdown to local files

**Advantages:**
- ⚡ Fastest workflow (automated scripts)
- 🎯 Most accurate clustering (K-means with silhouette scoring)
- 🔢 Exact calculations (no approximation)
- 💾 File-based persistence (save all outputs)
- 🔁 Reproducible (same data = same results)

**Use Claude Code when:**
- You have 80+ needs and 80+ survey respondents (large datasets)
- You need exact opportunity scores for reporting
- You want reproducible segmentation (same k-means results)
- You're integrating with downstream tools (scripts generate JSON)

---

## Claude.ai Web - AI-Powered Fallback ⚡

**Limitations:**
- ❌ No Python script execution
- ❌ No local file system access
- ❌ No scikit-learn library
- ❌ No file upload (must paste text)

**AI-Powered Alternatives:**
- ✅ **Opportunity scoring** → AI calculates using ODI formula: `Importance + max(Importance - Satisfaction, 0)`
- ✅ **EVC calculation** → AI reasons through time/error/revenue/risk value components
- ✅ **Segmentation** → AI performs conceptual clustering by identifying patterns in needs-importance profiles
- ✅ **WTP validation** → AI applies 6-layer framework with competitive benchmarking
- ✅ **Survey analysis** → Paste CSV data, AI parses and analyzes
- ✅ **Output generation** → Copy-paste results into local files

**Workflow:**
1. Generate needs → Copy to Google Docs / Notion / local file
2. Deploy survey → Collect responses in Google Forms / Typeform
3. Export CSV → Copy survey data (Ctrl+C)
4. Paste in chat → Claude analyzes with AI reasoning
5. Copy results → Save to local files manually

**Expected Accuracy:**
- **Phases 1-3 (Dialogue):** ✅ 100% parity (same Socratic method)
- **Phase 4 (Time-Task):** ✅ 95% parity (simple math)
- **Phase 5 (Survey):** ✅ 90% parity (CSV paste works well)
- **Phase 6 (Opportunity):** ✅ 90% parity (exact formula, AI calculation)
- **Phase 7 (EVC):** ⚠️ 85% parity (AI reasoning approximates)
- **Phase 8 (Segmentation):** ⚠️ 80% parity (conceptual vs K-means)
- **Phase 9 (WTP):** ✅ 90% parity (framework-driven analysis)
- **Phase 10 (Output):** ✅ 95% parity (manual JSON creation)

**Overall:** 80-90% feature parity (web is viable for most use cases)

---

## Web-Specific Workflow Guide

### Phase 6: Opportunity Scoring on Web

**What you'll do:**
```
You: I've collected survey data. Here's the CSV:

respondent_id,need_001_importance,need_001_satisfaction,need_002_importance,need_002_satisfaction,...
R001,9,3,8,4,...
R002,8,2,9,3,...
[... paste all 87 respondents]

Please calculate opportunity scores using the ODI algorithm.

Claude: Analyzing survey data...

Calculating opportunity scores for 85 needs across 87 respondents:

**Top 10 Opportunities (Severely Underserved):**

1. N034: Minimize time to estimate departure time
   - Avg Importance: 9.3/10
   - Avg Satisfaction: 3.2/10
   - Opportunity Score: 15.3 (9.3 + (9.3 - 3.2))
   - Status: SEVERELY UNDERSERVED

2. N012: Reduce likelihood of arriving late due to traffic
   - Avg Importance: 9.1/10
   - Avg Satisfaction: 3.4/10
   - Opportunity Score: 14.8
   - Status: SEVERELY UNDERSERVED

[Continues for all 85 needs...]
```

**Accuracy:** ✅ Exact same results as Python script (formula is simple)

---

### Phase 7: EVC Calculation on Web

**What you'll do:**
```
You: Based on the top opportunities, help me calculate Economic Value to Customer (EVC) for a navigation app that improves on-time arrival.

Context:
- Target user: Urban commuter with 20 trips/month
- Time value: $25/hour
- Current late arrival rate: 30% (6 trips/month)
- Proposed late arrival rate: 5% (1 trip/month)

Claude: Calculating EVC using the 4-component framework...

**Component 1: Time Savings Value**
- Current time spent dealing with late arrivals: 3 hours/month
- Improved: 0.5 hours/month
- Time saved: 2.5 hours/month × $25/hour = $62.50/month

**Component 2: Error Reduction Value**
- Current cost of being late: $150/month (missed opportunities)
- Improved cost: $25/month
- Error reduction: $125/month

[Continues through all 4 components + performance premium...]

**Total Baseline EVC: $756/month**
**With 20% Performance Premium: $907/month**
```

**Accuracy:** ⚠️ ~85-90% (AI reasoning approximates, may vary ±10-15%)

**Why less accurate:** EVC requires assumptions (time value, error costs). AI makes reasonable estimates but may differ from precise user inputs. Python script forces explicit input parameters.

---

### Phase 8: Segmentation on Web

**What you'll do:**
```
You: Here's the same survey data. Please perform customer segmentation to identify distinct groups based on their needs-importance patterns.

[Paste same CSV]

Claude: Performing conceptual segmentation analysis...

I've identified **3 distinct customer segments** based on needs-importance profiles:

**Segment 1: Crisis Avoiders (30%, n=26 respondents)**

*Defining characteristics:*
- Extremely high importance on time-critical needs (avg 9.1/10)
- Very low satisfaction with current solutions (avg 3.2/10)
- High opportunity scores across planning and execution phases

*Sample respondents:* R003, R017, R024, R031, R045, R059...

*Needs they prioritize:*
- Minimize time to estimate departure time (Importance: 9.8/10)
- Reduce likelihood of arriving late (Importance: 9.6/10)
- Minimize effort to adapt route during trip (Importance: 9.2/10)

*Psychographic profile:*
- Professionals with critical meetings
- High anxiety about being late
- Willing to pay premium for reliability
- **Estimated WTP: $80-100/month**

[Continues for all 3 segments...]
```

**Accuracy:** ⚠️ ~80-85% (conceptual patterns vs K-means clustering)

**Why less accurate:** K-means uses mathematical distance metrics. AI identifies patterns conceptually. Segment sizes and characteristics will be similar but not identical.

**When this matters:** If you need exact cluster assignments for targeted marketing, use Claude Code. For strategic understanding, web is sufficient.

---

### Phase 9: WTP Validation on Web

**What you'll do:**
```
You: I'm considering pricing this navigation app at $69/month. Please validate this pricing using the 6-layer WTP validation framework.

Context:
- Target segment: Crisis Avoiders (30% of market)
- EVC calculated: $756/month baseline
- Survey WTP responses: [paste WTP column from survey]

Claude: Applying 6-layer WTP validation framework...

**Layer 1: Statistical Outlier Detection**
- Raw median WTP: $18/month
- Mean WTP: $31/month (skewed by outliers)
- Clean median (outliers removed): $15/month
- Result: ⚠️ CHALLENGED (your price is 4.6x median)

**Layer 2: Competitive Benchmarking**
| Competitor | Price | Market Share |
|------------|-------|--------------|
| Google Maps | FREE | 60% |
| Waze | FREE | 25% |
| Apple Maps | FREE | 12% |
| Your proposed | $69/month | 0% |

Result: ❌ FAIL (free alternatives dominate)

[Continues through all 6 layers...]

**Overall Validation:** ❌ FAIL (B2C pricing at $69/month not viable)
