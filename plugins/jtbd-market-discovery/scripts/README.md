# JTBD Market Discovery - Analysis Scripts

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Framework:** Outcome-Driven Innovation (ODI) - Tony Ulwick
**Version:** 1.0.0
**Last Updated:** 2026-01-21

---

## Overview

This directory contains Python scripts for quantitative analysis in the Jobs To Be Done (JTBD) market discovery methodology. These scripts implement the comprehensive methodology stack including ODI, EVC, Christensen Forces, multi-dimensional segmentation, and 6-layer WTP validation.

---

## The brain: `jtbd_graph.py` and `jtbdlib/`

The runs of the plugin are saved as pages in `docs/jtbd/`. `jtbd_graph.py` is the only code that writes them. Run it with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root <project> <operation>`.

- The standard operations: `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check` and `log`.
- `write-run --result-file F [--session-dir D] [--by ACTOR]` writes all pages of one run. It runs `init` first when the project has no graph. It prints one JSON object with the path of each page.
- `results (--run KEY | --run-id R | --latest) [--command C] [--case C]` prints the `Result` pages of one run in the shape of a result file.
- `pages TYPE [--run KEY]` prints the pages of one type.
- Exit code 0 means done, 1 means a data error or a failed check, and 2 means wrong input.
- `gen-schema.sh` makes `schema/jtbd.schema.json` and `schema/jtbd.slots.json` from `schema/jtbd.yaml`. Run it after each change of the schema.
- `verify-run KEY --by ACTOR` sets `status: stable` and one `verified` entry on a `Run` page and on each page of the run.
- `probe-plugin.sh` and `claude_md_router.py` are copies of the files in `plugins/system-design/scripts`. Each copy must stay the same, byte for byte. A test of the `knowledge` plugin compares the copies. Change all copies together.

---

## Scripts (To Be Implemented in Phase 2)

### Core Analysis Scripts

1. **opportunity_scorer.py**
   - Calculate ODI opportunity scores from survey data
   - Formula: `Importance + max(Importance - Satisfaction, 0)`
   - Identify underserved needs (high importance, low satisfaction)
   - Output: Ranked list of opportunities (15-20 = extremely high)

2. **evc_calculator.py**
   - Economic Value to Customer (EVC) analysis
   - Quantify dollar value of serving needs better
   - Calculate time saved, errors reduced, revenue increased, risk mitigated
   - Output: Economic value per customer per need

3. **segmentation_engine.py**
   - Multi-dimensional customer segmentation
   - K-means clustering using scikit-learn
   - Needs-based + circumstances-based + behavioral patterns
   - Output: Customer segments with distinct opportunity profiles

4. **wtp_validator.py**
   - 6-layer willingness-to-pay validation
   - Statistical outlier detection, comparative benchmarking
   - Van Westendorp analysis, EVC-based validation
   - Output: Validated price points with confidence scores

---

## Dependencies

All scripts require:
```bash
pip install pandas numpy scikit-learn scipy
```

**Platform-specific:**
- **Claude Code (CLI):** Full Python execution, all dependencies available
- **Claude.ai (web):** AI-powered analysis as fallback (no dependencies required)

---

## Usage Patterns

### Standalone Script Usage

`opportunity_scorer.py`, `segmentation_engine.py` and `evc_calculator.py` are libraries. They have no argument parser. Their `__main__` block prints a demo. A phase agent writes a helper file that imports them.

```bash
# Print the demo of a library
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/opportunity_scorer.py
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/segmentation_engine.py
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/evc_calculator.py
```

### Python API Usage

```python
from jtbd_market_discovery import opportunity_scorer, evc_calculator, segmentation_engine

# Load survey data
import pandas as pd
survey_df = pd.read_csv('survey-results.csv')

# Calculate opportunities
opportunities = opportunity_scorer.calculate_opportunities(survey_df)
print(f"Top 10 Underserved Needs:\n{opportunities.head(10)}")

# Segment customers
segments = segmentation_engine.segment_customers(
    survey_df,
    n_segments=3,
    features=['importance', 'satisfaction']
)

# Calculate EVC for top opportunities
evc_results = evc_calculator.calculate_evc(
    opportunities.head(10),
    assumptions={'hourly_rate': 150, 'error_cost': 5000}
)
```

### Claude Skill Integration

The SKILL.md file orchestrates these scripts through a conversational interface:

```
User: Analyze my survey results and identify opportunities

Claude: [Uses opportunity_scorer.py to calculate scores]
        [Uses segmentation_engine.py to find patterns]
        [Presents integrated analysis]
```

---

## Data Formats

### Input: Survey Results CSV

Expected format from `templates/needs-survey-template.csv`:

```csv
Job Statement,Job Step,Customer Need,Importance (1-10),Satisfaction (1-10),Respondent ID,Industry,Company Size
"Get to destinations on time","UNDERSTAND - Estimate departure time","Minimize time to estimate departure",8.5,4.2,R001,Tech,Enterprise
"Get to destinations on time","UNDERSTAND - Estimate departure time","Determine traffic conditions ahead",9.1,3.8,R001,Tech,Enterprise
...
```

**Required columns:**
- `Customer Need`: The need statement (ACTION + VARIABLE)
- `Importance (1-10)`: Importance rating
- `Satisfaction (1-10)`: Satisfaction rating

**Optional columns for segmentation:**
- `Industry`, `Company Size`, `Role`, `Experience Level`
- Any demographic or behavioral variables

### Output: Opportunities CSV

```csv
Customer Need,Job Step,Importance,Satisfaction,Opportunity,Rank,Interpretation
"Minimize time to identify conflicting absences","UNDERSTAND - Identify upcoming absence requests",9.2,3.1,15.3,1,"Extremely underserved"
"Determine alternative routes during congestion","REVISE - Reset route as needed",8.8,3.5,14.1,2,"Extremely underserved"
...
```

**Columns:**
- `Opportunity`: Calculated score (0-20 scale)
- `Rank`: Sorted by opportunity (1 = highest)
- `Interpretation`: Human-readable category

---

## Implementation Notes

### Phase 2 Development (Coming Next)

Each script will be implemented with:
1. **Core calculation functions** (pure logic, testable)
2. **CLI interface** using `argparse`
3. **Data validation** (check required columns, handle missing data)
4. **Error handling** (graceful degradation for missing dependencies)
5. **Web compatibility layer** (fallback for Claude.ai)
6. **Documentation** (docstrings, type hints, examples)
7. **Unit tests** (pytest framework)

### Web Compatibility Strategy

**Claude Code (CLI):**
```python
def calculate_opportunities(df):
    # Full pandas/numpy implementation
    import pandas as pd
    import numpy as np
    # ... actual calculation
```

**Claude.ai (web):**
```python
def calculate_opportunities_ai_fallback(survey_text):
    # AI-powered analysis when pandas not available
    prompt = f"Analyze this survey data and calculate opportunity scores..."
    # Return structured results approximating pandas output
```

### Design Principles

1. **Modular:** Each script is independent and reusable
2. **Testable:** Pure functions with clear inputs/outputs
3. **Documented:** Comprehensive docstrings and examples
4. **Validated:** Input validation and error messages
5. **Cross-platform:** Works in CLI and web environments
6. **Extensible:** Easy to add new analysis methods

---

## Testing

The tests are in `tests/unit/`, one file for each script. From the plugin folder, run:

```bash
pytest tests/ -q
```

---

## Contributing

When adding new scripts:

1. **Follow naming convention:** `{purpose}_{type}.py` (e.g., `opportunity_scorer.py`)
2. **Include docstrings:** Module, class, and function level
3. **Add type hints:** For all function signatures
4. **Write tests:** Unit tests with >80% coverage
5. **Update __init__.py:** Add exports to `__all__`
6. **Update this README:** Document usage and examples
7. **Author attribution:** Include "Luis F. Amadeo (Chief Agentic Officer)" in module docstring

---

## Resources

- **ODI Methodology:** See `../references/odi-methodology.md`
- **Universal Job Steps:** See `../references/universal-job-steps.md`
- **Need Generation:** See `../references/need-generation-guide.md`
- **Survey Instructions:** See `../templates/survey-instructions.md`
- **Implementation Plan:** See `../docs/IMPLEMENTATION_PLAN_V1.0.md`

---

## License

MIT License - Copyright (c) 2026 Luis F. Amadeo (Chief Agentic Officer)

See `../LICENSE` for full license text.

---

**README Version:** 1.0.0
**For:** JTBD Market Discovery Plugin v1.0
**Author:** Luis F. Amadeo (Chief Agentic Officer)
