"""Pydantic data models for Phase 0 acquisition readiness assessment."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class MnAExperience(str, Enum):
    """Prior M&A experience levels."""
    NONE = "none"
    LIMITED = "limited"
    MODERATE = "moderate"
    EXTENSIVE = "extensive"


class ReadinessLevel(str, Enum):
    """Readiness level assessments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskTolerance(str, Enum):
    """Risk tolerance levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class IntegrationPhilosophy(str, Enum):
    """Integration approach philosophies."""
    AUTONOMOUS = "autonomous"
    COLLABORATIVE = "collaborative"
    ABSORBED = "absorbed"


class DealStructure(str, Enum):
    """Preferred deal structure types."""
    CASH = "cash"
    STOCK = "stock"
    EARNOUT = "earnout"
    HYBRID = "hybrid"
    CASH_PLUS_EARNOUT = "cash_plus_earnout"


class ValuationMethod(str, Enum):
    """Valuation methodology approaches."""
    REVENUE_MULTIPLE = "revenue_multiple"
    EBITDA = "ebitda"
    DCF = "dcf"


class AssessmentContext(str, Enum):
    """CEO assessment context types."""
    SELF = "self"
    TEAM = "team"
    BOARD = "board"
    COMPREHENSIVE = "comprehensive"


class CEOReadinessInput(BaseModel):
    """CEO assessment scores from external evaluation processes.

    Uses the 3 A's framework from "Buy Then Build":
    - Attitude: Growth mindset, character, resilience
    - Aptitude: Strategic thinking, leadership capability
    - Action: Execution track record, results delivery
    """

    attitude_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Growth mindset, character, resilience (0-10)"
    )
    aptitude_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Strategic thinking, leadership capability (0-10)"
    )
    action_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Execution track record, results delivery (0-10)"
    )
    assessment_context: AssessmentContext = Field(
        ...,
        description="Assessment context: Self/Team/Board/Comprehensive"
    )
    key_strengths: List[str] = Field(
        default_factory=list,
        description="List of key leadership strengths"
    )
    development_areas: List[str] = Field(
        default_factory=list,
        description="List of development opportunities"
    )


class StrategicTargetInput(BaseModel):
    """Target definition and acquisition criteria."""

    target_industries: List[str] = Field(
        ...,
        min_length=1,
        description="Industries to target (e.g., SaaS, AI/ML)"
    )
    revenue_range_min: float = Field(
        ...,
        gt=0,
        description="Minimum target revenue in dollars"
    )
    revenue_range_max: float = Field(
        ...,
        gt=0,
        description="Maximum target revenue in dollars"
    )
    geographic_focus: List[str] = Field(
        ...,
        min_length=1,
        description="Geographic markets (e.g., North America, Europe)"
    )
    strategic_priorities: List[str] = Field(
        ...,
        description="Strategic priorities: Technology/Market/Talent/Revenue"
    )
    growth_threshold_pct: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Minimum growth rate percentage (optional)"
    )

    @model_validator(mode='after')
    def validate_revenue_range(self) -> 'StrategicTargetInput':
        """Validate that revenue_range_max >= revenue_range_min."""
        if self.revenue_range_max < self.revenue_range_min:
            raise ValueError(
                f"revenue_range_max ({self.revenue_range_max}) must be >= "
                f"revenue_range_min ({self.revenue_range_min})"
            )
        return self


class OrganizationalCapacityInput(BaseModel):
    """Integration and resource readiness."""

    prior_mna_experience: MnAExperience = Field(
        ...,
        description="Prior M&A experience level"
    )
    integration_team_size: int = Field(
        ...,
        ge=0,
        description="Number of dedicated M&A resources"
    )
    integration_philosophy: IntegrationPhilosophy = Field(
        ...,
        description="Integration approach: autonomous/collaborative/absorbed"
    )
    cultural_readiness: ReadinessLevel = Field(
        ...,
        description="Cultural readiness for acquisitions"
    )


class FinancialReadinessInput(BaseModel):
    """Capital and deal structure preferences."""

    available_capital_min: float = Field(
        ...,
        ge=0,
        description="Minimum capital committed in dollars"
    )
    available_capital_max: float = Field(
        ...,
        ge=0,
        description="Maximum capital available in dollars"
    )
    preferred_deal_structure: DealStructure = Field(
        ...,
        description="Preferred structure: cash/stock/earnout/hybrid"
    )
    valuation_methodology: Optional[ValuationMethod] = Field(
        None,
        description="Valuation approach: revenue_multiple/ebitda/dcf"
    )
    max_deal_size: float = Field(
        ...,
        ge=0,
        description="Maximum single deal size in dollars"
    )

    @model_validator(mode='after')
    def validate_capital_and_deal_size(self) -> 'FinancialReadinessInput':
        """Validate capital range constraints."""
        # Validate capital range
        if self.available_capital_max < self.available_capital_min:
            raise ValueError(
                f"available_capital_max ({self.available_capital_max}) must be >= "
                f"available_capital_min ({self.available_capital_min})"
            )

        return self


class GovernanceFrameworkInput(BaseModel):
    """Decision gates and risk management."""

    board_approval_required: bool = Field(
        ...,
        description="Whether phase-by-phase board approval required"
    )
    risk_tolerance: Optional[RiskTolerance] = Field(
        None,
        description="Risk tolerance level"
    )
    timeline_expectation_months: int = Field(
        ...,
        ge=0,
        le=24,
        description="Expected months per deal (0-24, 0 means not set)"
    )
    deal_breakers: List[str] = Field(
        default_factory=list,
        description="List of non-negotiable exclusions"
    )


class AcquisitionReadinessInput(BaseModel):
    """Complete Phase 0 acquisition readiness input.

    Combines all five readiness dimensions for comprehensive assessment.
    """

    company_name: str = Field(
        ...,
        description="Acquiring company name"
    )
    ceo_readiness: CEOReadinessInput
    strategic_targets: StrategicTargetInput
    organizational_capacity: OrganizationalCapacityInput
    financial_readiness: FinancialReadinessInput
    governance: GovernanceFrameworkInput
