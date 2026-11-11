---
name: calculations-rule-of-40
description: Calculate the Rule of 40 against a target of 40, 50 or 60, with the weighted score, a sourced ladder and reference lines
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/rule_of_40.py *), Edit(/.product-finance/rule-of-40-input.json)
---

# Rule of 40 Calculation Skill

## Purpose

Calculate the Rule of 40 (growth % + margin %) and grade it against a target of 40, 50 or 60 (default 40). The report shows the gap to each bar and the source of each bar.

## When to Use

- Checking whether a SaaS product meets a Rule of 40 target
- Comparing the EBITDA margin and the free cash flow margin against the same target
- Seeing how far the score is from 40, 50 and 60
- Tracking the score from one period to the next

## What This Skill Provides

The Rule of 40 report includes:
- Classic Rule of 40 score
- Weighted Rule of 40 (a plugin convention, not graded)
- One target line per margin given, with `met` or `short by N`
- A target status: `met`, `short`, `split` or `not_graded`
- The ladder: the score minus each bar of 40, 50 and 60, with the source of each bar
- Reference lines for NRR and gross margin, never in the score, because no source ties them to a bar
- Trend analysis (with previous-period data)
- The recommendations: one per short margin, or one line when met or not graded.

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| revenue_growth_rate | float | Yes | Revenue growth rate as percentage (e.g., 50 for 50%) |
| ebitda_margin | float | Yes | EBITDA margin as percentage (can be negative) |
| company_stage | enum | No | early, growth, scale, or mature (feeds only JSON `health_status`) |
| previous_period_growth | float | No | Previous period growth for trend analysis |
| previous_period_margin | float | No | Previous period margin for trend analysis |
| arr | float | No | Annual Recurring Revenue for context |
| target | int | No | The bar the product is graded against: 40, 50 or 60 (default 40) |
| fcf_margin | float | No | Free cash flow margin, as a percentage (12.5, not 0.125) |
| months_of_revenue | int | No | Months since the product's first revenue |
| nrr | float | No | Net revenue retention, as a percentage (115, not 1.15) |
| gross_margin | float | No | Gross margin, as a percentage (75, not 0.75) |

Pass `--assumptions <path>` to use setup's `targets.rule_of_40_target` when the input gives no `target`.

<!-- See docs/METHODOLOGY.md — Company Stage Definitions for ARR-to-stage mapping -->

The two margins:
- EBITDA margin: ebitda_margin is EBITDA / revenue x 100. Plain EBITDA counts stock-based pay as a cost; adjusted EBITDA adds it back.
- FCF margin (`fcf_margin`): Free cash flow margin, %: (operating cash flow - capital spending) / revenue x 100. Stock-based pay is not cash, so it is not subtracted.

A `target` other than 40, 50 or 60 stops the run with exit code 3 and names the key.

## Formulas

### Classic Rule of 40
```
Rule of 40 Score = Revenue Growth Rate (%) + EBITDA Margin (%)
FCF basis score  = Revenue Growth Rate (%) + FCF Margin (%)   (only when fcf_margin is given)
```

Example: 50% growth + (-10%) EBITDA margin = 40, which meets the default target of 40.

### Weighted Rule of 40
```
Weighted Rule of 40 = (1.33 × Revenue Growth %) + (0.67 × EBITDA Margin %)
```

In valuation studies, growth outweighs FCF margin: 2–3 times for late-stage cloud companies (Bessemer, The Rule of X, 2024) and 3.8 times on ARR multiples (Meritech Software Pulse, 14-August-2026). This score uses EBITDA margin; the weights are a plugin convention.

## The Target

No input picks the target: not the product type, the stage or an AI label. A target the person gives on the run applies; otherwise setup's stored target, when the run passes `--assumptions`; otherwise 40. A stored target that is not 40, 50 or 60 stops the script with exit 3 when it would apply (in interactive mode, when the file is read before the first prompt); a run then goes on without --assumptions and says setup's target was not used.

Each margin given is scored as growth + margin, and that score is graded against the target:
- A score equal to or above the target is `met`. A lower score is `short by N`, where N is the target minus the score.
- The status is `met` when every margin line is met, `short` when every line is short, and `split` when the lines differ.
- A split prints one note: "The EBITDA and FCF lines disagree at <target>. The two margins differ by capital spending, stock-based pay, working capital, interest and tax. Use the margin your board or investors use."
- A split is neither met nor short. Report both lines. If the person names the margin their board or investors use, give that line's verdict and still show the other. Do not average the two margins.
- The two lines stay apart because no source defines a Rule of 40 on an average of the two margins.
- When `months_of_revenue` is 12 or less, the product is not graded (status `not_graded`): growth is not a year-on-year rate before the thirteenth month. When `months_of_revenue` is not given, the report says the age was not checked.
- When `arr` is under 25,000,000, the report prints the ICONIQ caution beside the result. ICONIQ writes: "we typically only begin to place real weight against Rule of 40 for companies with at least $25M ARR". The product is still graded.

JSON `health_status` is the 0.14.0 stage band, kept unchanged, with no published source. The markdown report does not print it. Do not report `health_status` to the person as a verdict or a grade. The verdict is `target_status`.

`health_status` is not a verdict because no published source gives its stage bands.

This plugin has no peer data for the score. Do not compare it with other companies; show the ladder.

## The Ladder

The ladder shows the score minus each bar. It is arithmetic, not a verdict, so it prints whether or not the product is graded. The Source column holds these cells:

| Bar | Source |
|-----|--------|
| 40 | Feld (2015): "The 40% rule is that your growth rate + your profit should add up to 40%." |
| 50 | No published benchmark found. A bar you set. |
| 60 | Vista Equity Partners (8 Jan 2026): "an emerging aspiration, not a universal baseline". |

## Reference Lines

NRR and gross margin print as reference lines. They never enter the score, the status or a recommendation.
- When `months_of_revenue` is 12 or less, the NRR line says NRR is not available before the thirteenth month of revenue. This line prints whether or not `nrr` is given.
- Otherwise, NRR prints when it is given.
- Gross margin prints when it is given.
- Gross margin prints beside Bessemer's State of AI 2025 figures: AI Supernovas average 25% gross margins; Shooting Stars about 60%.

## Output Format

The JSON report for 50% growth and -5% EBITDA margin, with no other input:

```json
{
  "rule_of_40_score": 45.0,
  "weighted_rule_of_40": 63.15,
  "revenue_growth_rate": 50.0,
  "ebitda_margin": -5.0,
  "health_status": "excellent",
  "target": 40,
  "target_source": "default",
  "target_status": "met",
  "target_lines": [
    {
      "basis": "ebitda",
      "margin": -5.0,
      "score": 45.0,
      "status": "met",
      "short_by": null
    }
  ],
  "target_notes": "Age not checked: months_of_revenue was not given.\nSize not checked: arr was not given.",
  "ladder": [
    {
      "bar": 40,
      "target": true,
      "ebitda": 5.0,
      "fcf": null,
      "source": "Feld (2015): \"The 40% rule is that your growth rate + your profit should add up to 40%.\""
    },
    {
      "bar": 50,
      "target": false,
      "ebitda": -5.0,
      "fcf": null,
      "source": "No published benchmark found. A bar you set."
    },
    {
      "bar": 60,
      "target": false,
      "ebitda": -15.0,
      "fcf": null,
      "source": "Vista Equity Partners (8 Jan 2026): \"an emerging aspiration, not a universal baseline\"."
    }
  ],
  "reference_lines": "",
  "benchmark_notes": "Classic Rule of 40: 45.0%\nWeighted Rule of 40: 63.2% (plugin convention, not graded)",
  "balance_analysis": "Growth Rate: 50.0%\nEBITDA Margin: -5.0%",
  "recommendations": [
    "Meets the target of 40 on every margin given."
  ]
}
```

`ladder[*].ebitda` and `ladder[*].fcf` hold the score minus the bar, not the score.

The target fields:

| Field | Type | Values |
|-------|------|--------|
| `target` | int | 40, 50 or 60 |
| `target_source` | string | `default`, `chosen` or `setup` |
| `target_status` | string | `met`, `short`, `split` or `not_graded` |
| `target_lines[].status` | string | `met`, `short` or `not_graded` |
| `target_notes` | string | Lines joined by newlines; empty string when none |
| `reference_lines` | string | Lines joined by newlines; empty string when none |

## Process

1. **Collect Input Data:**
   - Get the revenue growth rate and the EBITDA margin, as percentages
   - Get the optional inputs: `target`, `fcf_margin`, `months_of_revenue`, `arr`, `nrr` and `gross_margin`
   - Get the company stage (optional; it feeds only JSON `health_status`)

2. **Calculate Rule of 40:**
   - Add the growth rate to each margin given
   - Calculate the weighted version (a plugin convention, not graded)

3. **Grade Against the Target:**
   - Compare each margin line with the target: `met` or `short by N`
   - Set the status: `met`, `short`, `split` or `not_graded`
   - Add the age line and the size line

4. **Print the Ladder and the Reference Lines:**
   - Subtract each bar of 40, 50 and 60 from each score
   - Print the source of each bar
   - Print the Reference Lines as the Reference Lines section says

5. **Write the Recommendations:**
   - For each short margin: the gap, closed by N points of growth or N points of that margin
   - When every margin meets the target: one line that says so
   - When the product is not graded: one line to run it again from the thirteenth month

6. **Trend Analysis (if previous-period data):**
   - Calculate the score change
   - State the change in growth and in margin

## Run the Script

Do these steps only when this skill runs as `/product-finance:calculations-rule-of-40`. When a command or an agent tells you to read this page, do not do these steps: follow the steps of that command or agent, because it has its own steps for the figures.

1. Write the inputs that the person gave to `.product-finance/rule-of-40-input.json` with the Write tool: 1 JSON object, with the field names of the Input Requirements table. Write each number as a JSON number. Leave out each input that the person did not give.
2. Run this command 1 time, as the only command of the Bash call:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/rule_of_40.py --input .product-finance/rule-of-40-input.json --format markdown
   ```

3. Show the output of the script to the person. An exit with code 3 lists each input that the script refused, one on each line. When a listed value is a number that you wrote as text, or an input that you wrote under another name, write it again as a JSON number under the name of the line, and run the command again 1 time. When a listed value is the value that the person gave, show the lines to the person and ask for a value that the script accepts, because only the person can change an input. When a run exits with a code other than 0 and 3, work out the figures with the formulas of this page, and tell the person that no script ran. Do not read a file of the plugin, because this page gives each input name.

## Example Calculation

**Scenario 1: Met at the default target**
```
Revenue Growth: 80%
EBITDA Margin: -30%
Rule of 40: 80 + (-30) = 50.0 against 40: met
Weighted: (1.33 × 80) + (0.67 × -30) = 86.3 (plugin convention, not graded)
Ladder: 40 +10.0, 50 0.0, 60 -10.0
```

**Scenario 2: Short at the default target**
```
Revenue Growth: 15%
EBITDA Margin: -10%
Rule of 40: 15 + (-10) = 5.0 against 40: short by 35
Weighted: (1.33 × 15) + (0.67 × -10) = 13.3 (plugin convention, not graded)
Recommendation: closes with 35 points of growth or 35 points of EBITDA margin
```

**Scenario 3: Split between the two margins, at a target of 50**
```
Revenue Growth: 30%
EBITDA Margin: 15%
FCF Margin: 31%
Target: 50 (your choice)
EBITDA basis: 30 + 15 = 45.0 against 50: short by 5
FCF basis: 30 + 31 = 61.0 against 50: met
Status: SPLIT
The EBITDA and FCF lines disagree at 50. The two margins differ by capital spending, stock-based pay, working capital, interest and tax. Use the margin your board or investors use.
Recommendation: closes with 5 points of growth or 5 points of EBITDA margin
```

For Scenario 3, report the split and both lines. Do not average the two margins.

## Sources

The verified sources, read on 2026-11-08:
- Brad Feld, The Rule of 40% For a Healthy SaaS Company, feld.com, 3 Feb 2015
- Vista Equity Partners, Rethinking Software Benchmarks in an AI-Driven Market, 8 Jan 2026
- ICONIQ, The ICONIQ Enterprise Five (2025 KPIs)
- Bessemer Venture Partners, The State of AI 2025, 13 Aug 2025
- Bessemer, The Rule of X, 2 Jan 2024
- Meritech Software Pulse, 14-August-2026 edition
