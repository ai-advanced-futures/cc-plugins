"""Health scoring and aggregation for operational assessment."""

from typing import List
from corporate_development.operational_dd.types import DimensionScore, OperationalHealthResult
from corporate_development.core.phase import PhaseGate
from corporate_development.core.constants import OPERATIONAL_GO_THRESHOLD, OPERATIONAL_CONDITIONAL_THRESHOLD


class HealthScorer:
    """Calculate overall operational health from dimension scores."""

    def calculate_overall_score(self, dimension_scores: List[DimensionScore]) -> int:
        """Calculate weighted average of dimension scores.

        Args:
            dimension_scores: List of dimension scores with weights

        Returns:
            Overall score (0-100)
        """
        if not dimension_scores:
            return 0

        weighted_sum = sum(score.score * score.weight for score in dimension_scores)
        return round(weighted_sum)

    def determine_gate(self, overall_score: int) -> PhaseGate:
        """Determine gate decision from overall score.

        Args:
            overall_score: Overall operational health score (0-100)

        Returns:
            Gate decision (GO/CONDITIONAL/NO_GO)
        """
        if overall_score >= OPERATIONAL_GO_THRESHOLD:
            return PhaseGate.GO
        elif overall_score >= OPERATIONAL_CONDITIONAL_THRESHOLD:
            return PhaseGate.CONDITIONAL
        else:
            return PhaseGate.NO_GO

    def aggregate_risks(self, dimension_scores: List[DimensionScore]) -> tuple:
        """Aggregate risks from all dimensions.

        Args:
            dimension_scores: List of dimension scores with risk flags

        Returns:
            Tuple of (all_risks, critical_count, warning_count, info_count)
        """
        all_risks = []
        critical_count = 0
        warning_count = 0
        info_count = 0

        for dim_score in dimension_scores:
            for risk in dim_score.risk_flags:
                all_risks.append(risk)
                if risk.severity == "CRITICAL":
                    critical_count += 1
                elif risk.severity == "WARNING":
                    warning_count += 1
                elif risk.severity == "INFO":
                    info_count += 1

        return all_risks, critical_count, warning_count, info_count

    def generate_risk_summary(self, critical_count: int, warning_count: int, info_count: int) -> str:
        """Generate summary of risk counts.

        Args:
            critical_count: Number of critical risks
            warning_count: Number of warning risks
            info_count: Number of info risks

        Returns:
            Risk summary string
        """
        if critical_count > 0:
            return f"{critical_count} CRITICAL risk(s) require immediate attention"
        elif warning_count > 0:
            return f"{warning_count} WARNING(s) should be addressed during integration"
        elif info_count > 0:
            return f"{info_count} INFO item(s) noted for awareness"
        else:
            return "No significant risks identified"

    def calculate_health(self, dimension_scores: List[DimensionScore]) -> OperationalHealthResult:
        """Calculate complete operational health assessment.

        Args:
            dimension_scores: List of dimension scores

        Returns:
            Complete operational health result
        """
        overall_score = self.calculate_overall_score(dimension_scores)
        gate_decision = self.determine_gate(overall_score)
        all_risks, critical_count, warning_count, info_count = self.aggregate_risks(dimension_scores)
        risk_summary = self.generate_risk_summary(critical_count, warning_count, info_count)

        return OperationalHealthResult(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            gate_decision=gate_decision,
            risk_summary=risk_summary,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count
        )
