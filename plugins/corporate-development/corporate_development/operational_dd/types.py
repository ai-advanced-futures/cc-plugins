"""Type definitions for operational due diligence."""

from pydantic import BaseModel, Field
from typing import List, Optional
from corporate_development.core.phase import PhaseGate


# Assessment Input Types
class TeamAssessmentInput(BaseModel):
    """Input data for team assessment."""
    headcount: int = Field(..., ge=1, description="Number of employees")
    leadership_quality: int = Field(..., ge=0, le=100, description="Leadership quality score")
    skill_coverage: int = Field(..., ge=0, le=100, description="Skill coverage score")
    retention_rate: float = Field(..., ge=0.0, le=1.0, description="Employee retention rate")
    key_person_risk: bool = Field(..., description="Significant key person dependency risk")
    org_chart_file: Optional[str] = Field(None, description="Path to org chart file")


class TechnologyAssessmentInput(BaseModel):
    """Input data for technology assessment."""
    tech_stack: List[str] = Field(..., description="List of technologies used")
    architecture_quality: int = Field(..., ge=0, le=100, description="Architecture quality score")
    technical_debt_level: str = Field(..., description="Technical debt level: LOW/MEDIUM/HIGH")
    scalability_score: int = Field(..., ge=0, le=100, description="Scalability score")
    code_repo_url: Optional[str] = Field(None, description="URL to code repository")


class ProductAssessmentInput(BaseModel):
    """Input data for product assessment."""
    product_quality: int = Field(..., ge=0, le=100, description="Product quality score")
    roadmap_clarity: int = Field(..., ge=0, le=100, description="Product roadmap clarity score")
    customer_satisfaction: int = Field(..., ge=0, le=100, description="Customer satisfaction score")
    feature_completeness: int = Field(..., ge=0, le=100, description="Feature completeness score")


class OperationsAssessmentInput(BaseModel):
    """Input data for operations assessment."""
    process_maturity: int = Field(..., ge=0, le=100, description="Process maturity score")
    workflow_efficiency: int = Field(..., ge=0, le=100, description="Workflow efficiency score")
    documentation_quality: int = Field(..., ge=0, le=100, description="Documentation quality score")
    scalability: int = Field(..., ge=0, le=100, description="Operations scalability score")


class MarketPositionInput(BaseModel):
    """Input data for market position assessment."""
    competitive_standing: int = Field(..., ge=0, le=100, description="Competitive standing score")
    moat_strength: int = Field(..., ge=0, le=100, description="Moat strength score")
    differentiation: int = Field(..., ge=0, le=100, description="Differentiation score")


# Risk Flag
class RiskFlag(BaseModel):
    """Operational risk flag."""
    severity: str = Field(..., description="CRITICAL/WARNING/INFO")
    category: str = Field(..., description="Dimension category (team/technology/product/operations/market)")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="Risk description")
    recommendation: str = Field(..., description="Recommended action")


# Assessment Results
class DimensionScore(BaseModel):
    """Score for a single dimension."""
    dimension: str = Field(..., description="Dimension name")
    score: int = Field(..., ge=0, le=100, description="Dimension score (0-100)")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in overall score")
    strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    concerns: List[str] = Field(default_factory=list, description="Identified concerns")
    risk_flags: List[RiskFlag] = Field(default_factory=list, description="Dimension-specific risks")


class OperationalHealthResult(BaseModel):
    """Complete operational health assessment result."""
    overall_score: int = Field(..., ge=0, le=100, description="Overall operational health score")
    dimension_scores: List[DimensionScore] = Field(..., description="Individual dimension scores")
    gate_decision: PhaseGate = Field(..., description="Gate decision (GO/CONDITIONAL/NO_GO)")
    risk_summary: str = Field(..., description="Summary of key risks")
    critical_count: int = Field(default=0, description="Number of critical risks")
    warning_count: int = Field(default=0, description="Number of warning risks")
    info_count: int = Field(default=0, description="Number of info risks")
