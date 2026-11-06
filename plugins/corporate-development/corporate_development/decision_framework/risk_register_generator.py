"""RiskRegisterGenerator for Phase 6 CSV risk registers."""

import csv
from io import StringIO

from corporate_development.decision_framework.recommendation_synthesizer import FinalRecommendation
from corporate_development.decision_framework.types import DealRecommendationInput


class RiskRegisterGenerator:
    """Generates CSV risk register consolidating all risks."""

    def generate(
        self,
        deal_input: DealRecommendationInput,
        final_recommendation: FinalRecommendation,
    ) -> str:
        """Generate risk register CSV.

        Args:
            deal_input: Original deal input data
            final_recommendation: Final recommendation from synthesizer

        Returns:
            CSV string with risk register
        """
        # Collect risks from final recommendation
        risks = []
        risk_id_counter = 1

        # Critical blockers (Critical severity)
        for blocker in final_recommendation.qualitative_blockers:
            risks.append({
                "Risk ID": f"R-{risk_id_counter:03d}",
                "Source Phase": "Phase 6",
                "Category": "Strategic",
                "Description": blocker,
                "Likelihood": "High",
                "Impact": "High",
                "Severity": "Critical",
                "Mitigation Status": "Identified",
                "Owner": "Strategy Team",
                "Notes": "Critical blocker from qualitative assessment",
            })
            risk_id_counter += 1

        # Major concerns (High severity)
        for concern in final_recommendation.qualitative_concerns:
            risks.append({
                "Risk ID": f"R-{risk_id_counter:03d}",
                "Source Phase": "Phase 6",
                "Category": "Strategic",
                "Description": concern,
                "Likelihood": "Medium",
                "Impact": "High",
                "Severity": "High",
                "Mitigation Status": "Identified",
                "Owner": "Strategy Team",
                "Notes": "Major concern from qualitative assessment",
            })
            risk_id_counter += 1

        # Sort by severity (Critical → High → Medium → Low)
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        risks.sort(key=lambda r: severity_order.get(r["Severity"], 999))

        # Generate CSV
        output = StringIO()
        if risks:
            fieldnames = [
                "Risk ID", "Source Phase", "Category", "Description",
                "Likelihood", "Impact", "Severity", "Mitigation Status",
                "Owner", "Notes",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(risks)
        else:
            # Empty register with header only
            writer = csv.writer(output)
            writer.writerow([
                "Risk ID", "Source Phase", "Category", "Description",
                "Likelihood", "Impact", "Severity", "Mitigation Status",
                "Owner", "Notes",
            ])

        return output.getvalue()
