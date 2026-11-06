"""Type definitions for integration planning.

Following the pattern established in operational_dd and financial_dd modules,
this uses Pydantic models with validation and Enum classes for constrained values.
"""

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from corporate_development.core.types import ComplexityRating  # noqa: F401 — re-exported for callers


# ============================================================================
# Enums for Constrained Values
# ============================================================================


class Priority(str, Enum):
    """Activity priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IntegrationRiskSeverity(str, Enum):
    """Risk severity levels for integration planning."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Backwards-compatible alias — will be removed in a future major version
Severity = IntegrationRiskSeverity


class Likelihood(str, Enum):
    """Risk likelihood levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Impact(str, Enum):
    """Risk impact levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewFrequency(str, Enum):
    """Metric review frequency."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ComplexityRating is now canonical in corporate_development.core.types.
# The import above re-exports it for backward compatibility with existing callers.


# ============================================================================
# Input Models
# ============================================================================


class IntegrationPlanningInput(BaseModel):
    """Input for Phase 5 Integration Planning."""

    # Required
    target_name: str = Field(..., description="Name of the target company")
    acquirer_name: str = Field(..., description="Name of the acquiring company")

    # Optional: From Phase 3 Operational DD
    operational_health_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Operational health score from Phase 3"
    )
    team_strength: Optional[str] = Field(None, description="Team strength assessment")
    tech_debt_level: Optional[str] = Field(None, description="Technical debt level")

    # Optional: From Phase 4 Financial DD
    financial_health_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Financial health score from Phase 4"
    )
    annual_revenue: Optional[float] = Field(None, description="Annual revenue")

    # Optional: From Phase 2 Assessment
    strategic_fit: Optional[str] = Field(None, description="Strategic fit assessment")
    integration_complexity: Optional[str] = Field(None, description="Integration complexity")

    # Optional: Critical risks from any phase
    critical_risks: Optional[List[str]] = Field(None, description="List of critical risks")


# ============================================================================
# Activity and Timeline Models
# ============================================================================


class Activity(BaseModel):
    """Single integration activity."""

    id: str = Field(..., description="Unique activity identifier")
    domain: str = Field(..., description="Domain/area of activity")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Detailed activity description")
    owner: str = Field(..., description="Activity owner/responsible party")
    day_range: str = Field(..., description="Day range (e.g., 'Day 1', 'Days 1-5')")
    priority: Priority = Field(..., description="Activity priority level")
    dependencies: List[str] = Field(default_factory=list, description="List of activity IDs this depends on")
    success_criteria: str = Field(default="", description="Success criteria for completion")
    estimated_hours: Optional[int] = Field(None, ge=0, description="Estimated hours to complete")


class TimePeriod(BaseModel):
    """One of 4 time periods in the 100-day plan."""

    period_name: str = Field(..., description="Name of the period (e.g., 'Days 1-30')")
    focus_theme: str = Field(..., description="Theme/focus for this period")
    start_day: int = Field(..., ge=1, description="Starting day of period")
    end_day: int = Field(..., ge=1, description="Ending day of period")
    activities_by_domain: Dict[str, List[Activity]] = Field(
        default_factory=dict,
        description="Activities organized by domain"
    )


# ============================================================================
# Risk Models
# ============================================================================


class Risk(BaseModel):
    """Integration risk."""

    id: str = Field(..., description="Unique risk identifier")
    domain: str = Field(..., description="Domain/area of risk")
    description: str = Field(..., description="Risk description")
    likelihood: Likelihood = Field(..., description="Likelihood of occurrence")
    impact: Impact = Field(..., description="Impact if occurs")
    severity: IntegrationRiskSeverity = Field(..., description="Overall severity")
    mitigation_strategy: str = Field(..., description="Strategy to mitigate the risk")
    owner: str = Field(..., description="Risk owner/responsible party")


# ============================================================================
# Metric Models
# ============================================================================


class Metric(BaseModel):
    """Success metric/KPI."""

    domain: str = Field(..., description="Domain/area this metric measures")
    metric_name: str = Field(..., description="Name of the metric")
    target_value: str = Field(..., description="Target value to achieve")
    measurement_method: str = Field(..., description="How to measure this metric")
    review_frequency: ReviewFrequency = Field(..., description="How often to review")
    owner: str = Field(..., description="Metric owner/responsible party")


# ============================================================================
# Integration Plan Model
# ============================================================================


class IntegrationPlan(BaseModel):
    """Complete 100-day integration plan."""

    target_name: str = Field(..., description="Name of target company")
    acquirer_name: str = Field(..., description="Name of acquiring company")
    timeline: List[TimePeriod] = Field(..., description="Timeline broken into periods")
    total_activities: int = Field(..., ge=0, description="Total number of activities")
    activities_by_domain: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of activities by domain"
    )
    critical_path_activities: List[str] = Field(
        default_factory=list,
        description="Activity IDs on the critical path"
    )
    integration_risks: List[Risk] = Field(
        default_factory=list,
        description="Identified integration risks"
    )
    risk_count_by_severity: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of risks by severity level"
    )
    success_metrics: List[Metric] = Field(
        default_factory=list,
        description="Success metrics to track"
    )
    complexity_rating: ComplexityRating = Field(..., description="Overall integration complexity")
