# Platform Compatibility

Run one command per Bash call.

**Version:** 1.0.0
**Last Updated:** 2026-01-21

---

## Quick Start

### For Developers

```bash
# Install (Claude Code marketplace)
claude plugin install jtbd-market-discovery

# Start discovery
claude
> I want to discover market opportunities for [product/market]

# Or use skill directly
> /jtbd-market-discovery:discover
```

### For Product Analysts

This skill guides you through 10 phases:

1. **Job Identification:** Define what customers are trying to accomplish
2. **Job Decomposition:** Break job into 8-15 steps
3. **Need Generation:** Create 80-100 customer needs
4. **Time and Task Analysis:** Measure the baseline effort of each step
5. **Survey Deployment:** Create the importance/satisfaction survey and collect 50+ answers
6. **Opportunity Scoring:** Calculate the ODI scores
7. **EVC Calculation:** Calculate the economic value to the customer
8. **Segmentation:** Find the customer segments
9. **WTP Validation:** Verify willingness-to-pay
10. **Output Integration:** Assemble the final output

**Time Investment:**
- Initial discovery (Phases 1-4): 4-6 hours
- Survey creation: 2-3 hours
- Data collection: 1-2 weeks (depending on access)
- Analysis (Phases 6-9): 3-4 hours

**Total:** ~10-15 hours of active work + survey fielding time

---

## Platform Compatibility

### Claude Code (CLI) - Full Feature Set

**Available:**
- ✅ All 10 phases
- ✅ Python script execution by the skill (opportunity_scorer.py, segmentation_engine.py, etc.); the agents read the result files and run no code
- ✅ Full statistical analysis (pandas, numpy, scikit-learn)
- ✅ CSV data import/export
- ✅ Automated calculations and visualizations

### Claude.ai (Web) - AI-Powered Fallback

**Available:**
- ✅ All 10 phases with Socratic guidance
- ✅ AI-powered opportunity scoring (when Python unavailable)
- ✅ Template generation and export
- ⚠️ Manual data entry (paste survey results as text)
- ⚠️ Approximate calculations (AI analyzes patterns, no statistical precision)

**Limitations:**
- Cannot execute Python scripts directly
- Cannot read CSV files
- Segmentation uses AI pattern recognition (not k-means)
- WTP validation simplified (fewer layers)

**Recommendation:**
Use Claude Code for quantitative analysis. Use Claude.ai for qualitative work (job identification, need generation, survey design).

---

## Feature Parity Comparison

| Feature | Claude Code (CLI) | Claude.ai (Web) |
|---------|------------------|-----------------|
| **Phase 1: Job Identification** | ✅ Full Socratic dialogue | ✅ Full Socratic dialogue |
| **Phase 2: Job Decomposition** | ✅ Universal Steps framework | ✅ Universal Steps framework |
| **Phase 3: Need Generation** | ✅ ACTION + VARIABLE formula | ✅ ACTION + VARIABLE formula |
| **Phase 4: Survey Design** | ✅ Template generation | ✅ Template generation |
| **Phase 5: Data Collection** | ✅ CSV import | ⚠️ Manual paste (text format) |
| **Phase 6: Opportunity Scoring** | ✅ Python (precise ODI algorithm) | ⚠️ AI approximation (80-90% parity) |
| **Phase 6: Segmentation** | ✅ K-means clustering (sklearn) | ⚠️ AI pattern recognition |
| **Phase 6: Forces Analysis** | ✅ Full calculation | ✅ Full calculation (AI-based) |
| **Phase 7: EVC Calculation** | ✅ Python (4 dimensions) | ⚠️ AI approximation |
| **Phase 7: WTP Validation** | ✅ Full 6-layer framework | ⚠️ Simplified 3-layer |
| **Output Generation** | ✅ JSON, CSV export | ✅ Text/markdown export |
| **Integration with PRD** | ✅ Structured JSON output | ✅ Structured JSON output |

**Legend:**
- ✅ Full feature parity
- ⚠️ Limited or approximate functionality
- ❌ Not available

---

## Platform-Specific Workflows

### Claude Code Workflow (Recommended for Analysis)

```
Phase 1-4: Discovery
├─ Job identification (Socratic dialogue)
├─ Job decomposition (Universal Steps)
├─ Need generation (ACTION + VARIABLE)
└─ Survey design (template)

Phase 5: Data Collection
├─ Field survey (external tool)
└─ Export results as CSV

Phase 6-7: Analysis
├─ Calculate ODI scores
├─ Run segmentation
├─ Calculate EVC
└─ Validate WTP

Result: Structured JSON + CSV ready for PRD skill
```

### Claude.ai Web Workflow (Qualitative Focus)

```
Phase 1-4: Discovery (Full Parity)
├─ Job identification (Socratic dialogue)
├─ Job decomposition (Universal Steps)
├─ Need generation (ACTION + VARIABLE)
└─ Survey design (template export)

Phase 5: Data Collection
├─ Field survey (external tool)
└─ Copy results as text

Phase 6-7: Analysis (AI-Powered)
├─ Paste survey data as formatted text
├─ AI analyzes patterns and calculates:
│   ├─ Opportunity scores (ODI approximation)
│   ├─ Segments (pattern recognition, not k-means)
│   ├─ Forces (qualitative assessment)
│   └─ WTP (simplified validation)
└─ Generate text/markdown output

Result: Markdown report (80-90% parity with CLI)
```

---

## When to Use Each Platform

### Use Claude Code When:
- ✅ You have survey data in CSV format
- ✅ You need statistical precision (k-means, ODI algorithm)
- ✅ You're analyzing 50+ survey responses
- ✅ You need segmentation with elbow method validation
- ✅ You require full 6-layer WTP validation
- ✅ You're integrating with downstream development tools

### Use Claude.ai Web When:
- ✅ You're in discovery phases (1-4) only
- ✅ You need qualitative guidance (job definition, need generation)
- ✅ You want to validate a job statement quickly
- ✅ You're creating survey templates
- ✅ You have no Python/CLI environment available
- ✅ You have small datasets (< 30 responses)

---

## Migration Path

**Start on Web, Finish on CLI:**

1. **Phase 1-4 on Claude.ai Web:**
   - Complete job identification, decomposition, need generation
   - Export survey template
   - Field survey using external tools

2. **Phase 5-7 on Claude Code CLI:**
   - Import CSV survey results
   - Run Python scripts for precise analysis
   - Generate structured JSON output

**Export/Import:**
```
# Export from Web (Phase 1-4)
Claude Web: Export job statement, steps, and needs to JSON

# Import to CLI (Phase 5-7)
Claude CLI: Import JSON, add survey data, run analysis
```

---

## Troubleshooting Platform Issues

### Claude Code: Python Dependencies

**Issue:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:** Run the script with `uv run`. The PEP 723 block at its top lists the packages.

### Claude Code: CSV Import Fails

**Issue:** CSV encoding errors or format issues

**Solution:**
- Ensure CSV is UTF-8 encoded
- Check for proper column headers (importance, satisfaction)
- Validate data types (numeric ratings 1-10)

### Claude.ai Web: Large Data Pasting

**Issue:** Data too large to paste in chat

**Solution:**
- Summarize data (paste first 10-20 rows)
- Use aggregated statistics instead of raw data
- Consider switching to Claude Code for large datasets

### Claude.ai Web: Segmentation Accuracy

**Issue:** AI pattern recognition may miss subtle segments

**Solution:**
- Provide clear descriptions of expected segments
- Validate segments with domain knowledge
- Use Claude Code for k-means precision if needed

---

## Best Practices by Platform

### Claude Code Best Practices

1. **Data Preparation:**
   - Clean survey data before import
   - Remove incomplete responses
   - Validate rating scales (1-10)

2. **Script Execution:**
   - Run scripts in sequence (scorer → segmentation → EVC → WTP)
   - Check intermediate outputs
   - Use verbose mode for debugging

3. **Output Management:**
   - Export JSON for PRD integration
   - Save CSV for archival/audit
   - Version control analysis results

### Claude.ai Web Best Practices

1. **Structured Input:**
   - Format survey data as tables or lists
   - Label columns (Need, Importance, Satisfaction)
   - Include sample size in description

2. **Validation:**
   - Cross-check AI calculations manually
   - Validate segment definitions with data
   - Compare WTP against competitive benchmarks

3. **Documentation:**
   - Export findings to markdown
   - Save analysis as reference
   - Document assumptions and limitations

---

## Platform Limitations Summary

### What Works Everywhere
- ✅ Socratic dialogue for discovery (Phases 1-4)
- ✅ Job statement validation
- ✅ Universal Job Steps decomposition
- ✅ ACTION + VARIABLE need generation
- ✅ Survey template creation
- ✅ Forces analysis framework
- ✅ Integration with brainstorm/PRD skills

### What Requires Claude Code
- ⚠️ Precise ODI opportunity scoring (Python)
- ⚠️ K-means segmentation with elbow method
- ⚠️ Full 6-layer WTP validation
- ⚠️ CSV import/export automation
- ⚠️ Statistical outlier detection
- ⚠️ Batch processing of survey data

---

## Ready to Start?

This skill works best when you:

1. **Have a clear market or product area** to explore
2. **Can access customers** for validation and surveys
3. **Are open to data-driven insights** (may challenge assumptions)
4. **Are willing to invest time** in comprehensive discovery (~10-15 hours + survey fielding)

When ready, just say:

> "I want to discover market opportunities for [product/market]"

Or invoke directly:

> "/jtbd-market-discovery:discover"

I'll guide you through the entire process, step by step.

---

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**License:** MIT
**For:** JTBD Market Discovery Plugin v1.0
