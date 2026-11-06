"""Risk aggregation and analysis for operational assessment."""

from typing import List
from corporate_development.operational_dd.types import DimensionScore, RiskFlag


class RiskAnalyzer:
    """Aggregate and analyze operational risks."""

    def aggregate_all_risks(self, dimension_scores: List[DimensionScore]) -> List[RiskFlag]:
        """Aggregate all risk flags from dimension scores."""
        all_risks = []
        for dim_score in dimension_scores:
            all_risks.extend(dim_score.risk_flags)
        return all_risks

    def group_by_severity(self, risks: List[RiskFlag]) -> dict:
        """Group risks by severity level."""
        grouped = {
            "CRITICAL": [],
            "WARNING": [],
            "INFO": []
        }

        for risk in risks:
            if risk.severity in grouped:
                grouped[risk.severity].append(risk)

        return grouped

    def get_top_risks(self, risks: List[RiskFlag], top_n: int = 5) -> List[RiskFlag]:
        """Get top N risks prioritized by severity."""
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}

        sorted_risks = sorted(risks, key=lambda r: severity_order.get(r.severity, 3))

        return sorted_risks[:top_n]
