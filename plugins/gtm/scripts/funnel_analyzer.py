from __future__ import annotations

from dataclasses import dataclass


class BottleneckDetector:
    def find_worst(
        self,
        stages: dict[str, float],
        revenue_impact: dict[str, float] | None = None,
    ) -> str | None:
        if not stages:
            return None
        invalid = [k for k, v in stages.items() if not (0.0 <= v <= 1.0)]
        if invalid:
            raise ValueError(
                f"Conversion rates must be between 0.0 and 1.0. "
                f"Invalid stages: {invalid}. "
                f"Pass rates as decimals (e.g., 0.12 not 12)."
            )
        min_rate = min(stages.values())
        worst = [k for k, v in stages.items() if v == min_rate]
        if len(worst) == 1:
            return worst[0]
        if revenue_impact:
            return max(worst, key=lambda k: revenue_impact.get(k, 0.0))
        return worst[0]


@dataclass
class FunnelDiagnostic:
    monthly_visitors: int
    signup_rate: float
    activation_rate: float
    mql_rate: float
    sql_rate: float
    close_rate: float
    acv: float

    def project_monthly_revenue(self) -> float:
        """Return projected monthly ARR from funnel conversion rates.

        Formula: visitors * signup * activation * mql * sql * close * (ACV/12)
        Example: 1000 visitors, all rates=1.0, ACV=$12,000 → $1,000,000/month
        """
        closed = (
            self.monthly_visitors
            * self.signup_rate
            * self.activation_rate
            * self.mql_rate
            * self.sql_rate
            * self.close_rate
        )
        return round(closed * self.acv / 12, 2)
