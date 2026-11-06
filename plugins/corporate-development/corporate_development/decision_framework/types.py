"""Phase 6 input data models."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from corporate_development.core.types import ComplexityRating  # noqa: F401 — re-exported for callers


# ============================================================================
# Enums for Constrained Values
# ============================================================================


class StrategicClarity(str, Enum):
    """Strategic clarity levels for Phase 0 readiness."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MarketPosition(str, Enum):
    """Market position classifications for Phase 2 assessment."""
    LEADER = "leader"
    CHALLENGER = "challenger"
    NICHE = "niche"


# ComplexityRating is now canonical in corporate_development.core.types.
# The import above re-exports it for backward compatibility with existing callers.


# ============================================================================
# Phase Data Models
# ============================================================================


class Phase0ReadinessData(BaseModel):
    """Phase 0 readiness assessment data."""

    ceo_readiness_score: int = Field(..., ge=0, le=100)
    org_readiness_score: int = Field(..., ge=0, le=100)
    strategic_clarity: StrategicClarity


class Phase2AssessmentData(BaseModel):
    """Phase 2 strategic assessment data."""

    strategic_fit_score: int = Field(..., ge=0, le=100)
    market_position: MarketPosition
    differentiation_strength: str


class Phase5IntegrationData(BaseModel):
    """Phase 5 integration planning data."""

    complexity_rating: ComplexityRating
    critical_risks: List[str]
    total_activities: int = Field(..., ge=0)


class DealRecommendationInput(BaseModel):
    """Input data for Phase 6 deal recommendation.

    Required fields come from Phase 3 (operational_health_score)
    and Phase 4 (financial_health_score). Optional fields from other
    phases enrich the analysis when available.
    """

    # Required fields
    company_name: str
    acquirer_name: str
    operational_health_score: int = Field(..., ge=0, le=100)  # From Phase 3
    financial_health_score: int = Field(..., ge=0, le=100)    # From Phase 4

    # Optional phase data
    phase_0_readiness: Optional[Phase0ReadinessData] = None
    phase_2_assessment: Optional[Phase2AssessmentData] = None
    phase_5_integration: Optional[Phase5IntegrationData] = None

    # Additional optional context
    annual_revenue: Optional[float] = None
    deal_size: Optional[float] = None
    team_strength: Optional[str] = None
    tech_debt_level: Optional[str] = None
    customer_concentration: Optional[str] = None
    competitive_position: Optional[str] = None
