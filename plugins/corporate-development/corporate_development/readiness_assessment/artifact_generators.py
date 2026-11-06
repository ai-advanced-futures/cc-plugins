"""Artifact generators for Phase 0 readiness assessment outputs."""

import json
from datetime import datetime
from typing import Dict, Any


class ReadinessAssessmentGenerator:
    """Generate readiness_assessment.json artifact."""

    def generate(self, assessment_data: Dict[str, Any]) -> str:
        """Generate machine-readable JSON assessment.

        Args:
            assessment_data: Complete assessment results

        Returns:
            JSON string with assessment data
        """
        output = {
            "assessment_date": datetime.now().isoformat(),
            "company_name": assessment_data.get("company_name", "Unknown"),
            "overall_readiness_score": assessment_data.get("overall_score", 0),
            "gate_decision": assessment_data.get("gate_decision", "NO_GO"),
            "dimension_scores": self._build_dimension_scores(assessment_data),
            "recommendations": assessment_data.get("recommendations", []),
            "next_phase": "discover" if assessment_data.get("gate_decision") in ["GO", "CONDITIONAL"] else None,
            "next_command": "/corporate-development:discover" if assessment_data.get("gate_decision") in ["GO", "CONDITIONAL"] else None
        }

        return json.dumps(output, indent=2)

    def _build_dimension_scores(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build dimension scores section."""
        dimensions = {}

        for dim_name in ["ceo_readiness", "strategic_clarity", "organizational_capacity",
                         "financial_readiness", "governance_framework"]:
            if dim_name in data:
                dim_data = data[dim_name]
                dimensions[dim_name] = {
                    "score": dim_data.get("score", 0),
                    "weight": dim_data.get("weight", 0),
                    "weighted_score": dim_data.get("score", 0) * dim_data.get("weight", 0)
                }

        return dimensions


class ReadinessSummaryGenerator:
    """Generate readiness_summary.md artifact."""

    def generate(self, summary_data: Dict[str, Any]) -> str:
        """Generate executive summary markdown.

        Args:
            summary_data: Assessment summary data

        Returns:
            Markdown string with executive summary
        """
        company = summary_data.get("company_name", "Unknown")
        overall = summary_data.get("overall_score", 0)
        gate = summary_data.get("gate_decision", "NO_GO")
        ceo_score = summary_data.get("ceo_score", 0)

        date_str = datetime.now().strftime("%B %d, %Y")

        # Build markdown (condensed - see design doc for full template)
        summary = f"""# Acquisition Readiness Assessment - {company}

**Assessment Date**: {date_str}
**Overall Readiness**: {overall:.1f}/100 ({gate})
**Recommendation**: {"Proceed with M&A activities" if gate == "GO" else "Address capability gaps before proceeding"}

## Executive Summary

{company} demonstrates {"strong" if overall >= 80 else "moderate" if overall >= 65 else "limited"} acquisition readiness.

**Gate Decision**: {gate}

---

## Detailed Assessment

### 1. CEO Readiness ({ceo_score:.0f}/100)

CEO readiness score indicates {"strong leadership capability" if ceo_score >= 80 else "developing leadership capability"}.

---

## Recommendations

1. {"Build integration team capacity" if overall < 80 else "Maintain readiness"}
2. {"Enhance M&A governance" if overall < 70 else "Continue current trajectory"}

---

## Next Steps

**Next Phase**: Phase 1 - Target Discovery

```bash
/corporate-development:discover
```
"""
        return summary


class AcquisitionPlaybookGenerator:
    """Generate acquisition_playbook.md artifact."""

    def generate(self, playbook_data: Dict[str, Any]) -> str:
        """Generate acquisition playbook markdown.

        Args:
            playbook_data: Strategic criteria and framework

        Returns:
            Markdown string with playbook
        """
        company = playbook_data.get("company_name", "Unknown")
        industries = ", ".join(playbook_data.get("target_industries", []))
        revenue = playbook_data.get("revenue_range", "Not specified")

        # Build playbook (condensed - see design doc for full template)
        playbook = f"""# Acquisition Playbook - {company}

**Created**: {datetime.now().strftime("%B %d, %Y")}
**Version**: 1.0

---

## 1. Target Profile Definition

### Industries
- **Primary**: {industries}

### Company Profile
- **Revenue Range**: {revenue}

---

## 2. Evaluation Criteria & Scoring

### Quantitative Criteria (60% weight)

| Criterion | Weight | Scoring |
|-----------|--------|---------|
| Revenue Growth | 15% | 50%+ YoY = 100, 30-49% = 75, <20% = 0 |
| Annual Revenue | 10% | $20M+ = 100, $10-20M = 75, $5-10M = 50 |

---

## 3. Phase-by-Phase Decision Gates

### Phase 0: Acquisition Readiness
- **Gate Criteria**: Readiness score ≥65, CEO readiness ≥7.0
- **Approval**: Board strategic session

### Phase 1: Target Discovery
- **Gate Criteria**: 10-15 qualified targets
- **Approval**: CEO + Board review
"""
        return playbook
