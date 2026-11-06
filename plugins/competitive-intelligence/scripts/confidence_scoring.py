"""
Competitive Intelligence Plugin - Confidence Scoring Framework

Implements confidence scoring and propagation system for competitive intelligence findings.

Confidence Levels:
- HIGH: Multiple verified sources, primary sources, corroborated data
- MEDIUM: Single credible source or multiple secondary sources
- LOW: Single low-quality source or unverified claims
- SPECULATIVE: Inference, assumptions, no direct evidence

Features:
- Confidence level definitions and ordering
- Scoring algorithm based on sources and quality
- Aggregation of confidence from multiple findings
- Propagation from findings to recommendations
- Display formatting for reports
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ConfidenceLevel(Enum):
    """
    Four-level confidence scale for competitive intelligence findings.

    Values are ordered (higher = more confident):
    - HIGH (3): Strong evidence from multiple reliable sources
    - MEDIUM (2): Moderate evidence or single reliable source
    - LOW (1): Weak evidence or low-quality source
    - SPECULATIVE (0): No direct evidence, inference only
    """
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    SPECULATIVE = 0


@dataclass
class ConfidenceFinding:
    """
    A single finding with associated confidence level.

    Attributes:
        statement: The finding or claim
        confidence: Confidence level for this finding
        sources: List of sources supporting this finding
        rationale: Explanation for the confidence level
    """
    statement: str
    confidence: ConfidenceLevel
    sources: List[str]
    rationale: str = ""


@dataclass
class ConfidenceScore:
    """
    Detailed confidence score with numeric representation.

    Attributes:
        level: Categorical confidence level
        numeric_score: Numeric score between 0.0 and 1.0
        num_sources: Number of sources considered
        rationale: Explanation of the score
    """
    level: ConfidenceLevel
    numeric_score: float
    num_sources: int
    rationale: str = ""


def calculate_confidence(
    num_sources: int,
    source_quality: str = "medium",
    verification_method: str = "secondary",
    is_inference: bool = False
) -> ConfidenceScore:
    """
    Calculate confidence score based on sources and quality.

    Algorithm:
    1. Start with base score from source count
    2. Adjust for source quality (high/medium/low)
    3. Adjust for verification method (primary/secondary/none)
    4. Cap at 0.0 if inference with no sources

    Args:
        num_sources: Number of sources (negative treated as 0)
        source_quality: Quality of sources ("high", "medium", "low", "none")
        verification_method: How verified ("primary", "secondary", "none")
        is_inference: Whether this is pure inference

    Returns:
        ConfidenceScore with level and numeric score
    """
    # Handle edge cases
    if num_sources < 0:
        num_sources = 0

    if is_inference and num_sources == 0:
        return ConfidenceScore(
            level=ConfidenceLevel.SPECULATIVE,
            numeric_score=0.0,
            num_sources=0,
            rationale="Pure inference with no direct evidence"
        )

    # Base score from source count
    if num_sources == 0:
        base_score = 0.0
    elif num_sources == 1:
        base_score = 0.5
    elif num_sources == 2:
        base_score = 0.7
    else:  # 3 or more
        base_score = 0.85

    # Quality multiplier
    quality_map = {
        "high": 1.2,
        "medium": 1.0,
        "low": 0.7,
        "none": 0.3
    }
    quality_mult = quality_map.get(source_quality.lower(), 0.8)

    # Verification multiplier
    verification_map = {
        "primary": 1.1,
        "secondary": 1.0,
        "none": 0.8
    }
    verification_mult = verification_map.get(verification_method.lower(), 0.9)

    # Calculate final score
    numeric_score = base_score * quality_mult * verification_mult

    # Cap at 1.0
    numeric_score = min(1.0, numeric_score)

    # Map to confidence level.
    # Thresholds are expressed on the ConfidenceLevel enum scale (0–3) to stay
    # consistent with aggregate_confidence(), which operates on enum values directly.
    # Conversion: enum_value = numeric_score * 3 (since numeric_score ∈ [0.0, 1.0])
    enum_value = numeric_score * 3
    if enum_value >= 2.5:
        level = ConfidenceLevel.HIGH
    elif enum_value >= 1.5:
        level = ConfidenceLevel.MEDIUM
    elif enum_value >= 0.5:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.SPECULATIVE

    # Generate rationale
    rationale = f"{num_sources} source(s), {source_quality} quality, {verification_method} verification"

    return ConfidenceScore(
        level=level,
        numeric_score=numeric_score,
        num_sources=num_sources,
        rationale=rationale
    )


def aggregate_confidence(findings: List[ConfidenceFinding]) -> ConfidenceScore:
    """
    Aggregate confidence from multiple findings.

    Uses conservative aggregation:
    - Empty list → SPECULATIVE
    - Single finding → That finding's level
    - Multiple findings → Weighted average, pulled down by low confidence

    Args:
        findings: List of findings to aggregate

    Returns:
        Aggregated ConfidenceScore
    """
    if not findings:
        return ConfidenceScore(
            level=ConfidenceLevel.SPECULATIVE,
            numeric_score=0.0,
            num_sources=0,
            rationale="No findings to aggregate"
        )

    if len(findings) == 1:
        finding = findings[0]
        return ConfidenceScore(
            level=finding.confidence,
            numeric_score=finding.confidence.value / 3.0,  # Normalize to 0-1
            num_sources=len(finding.sources),
            rationale=f"Single finding: {finding.statement[:50]}..."
        )

    # Multiple findings - calculate weighted average
    # Weight lower confidence more heavily (conservative)
    total_value = 0.0
    total_sources = 0

    for finding in findings:
        confidence_value = finding.confidence.value
        # Weight: lower confidence gets higher weight in pulling average down
        weight = 1.0 / (confidence_value + 1)  # More weight for lower confidence
        total_value += confidence_value * weight
        total_sources += len(finding.sources)

    # Calculate weighted average
    total_weights = sum(1.0 / (f.confidence.value + 1) for f in findings)
    avg_value = total_value / total_weights

    # Map average to level
    if avg_value >= 2.5:
        level = ConfidenceLevel.HIGH
    elif avg_value >= 1.5:
        level = ConfidenceLevel.MEDIUM
    elif avg_value >= 0.5:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.SPECULATIVE

    numeric_score = avg_value / 3.0  # Normalize to 0-1

    return ConfidenceScore(
        level=level,
        numeric_score=numeric_score,
        num_sources=total_sources,
        rationale=f"Aggregated from {len(findings)} findings"
    )


def propagate_confidence(
    findings: List[ConfidenceFinding],
    recommendation_type: str = "strategic",
    loss_churn_validated: bool = False
) -> ConfidenceScore:
    """
    Propagate confidence from findings to a recommendation.

    Recommendations inherit confidence from their supporting evidence.
    Uses conservative propagation: recommendation is no more confident
    than its weakest supporting finding.

    Args:
        findings: Evidence findings supporting the recommendation
        recommendation_type: Type of recommendation ("strategic" or "tactical")
        loss_churn_validated: Reserved — currently raises NotImplementedError.
            There is a contradiction between agent instructions (downgrade competing
            lenses to LOW) and this code (upgrade recommendation confidence). The
            feature is disabled until the product decision is resolved.

    Returns:
        ConfidenceScore for the recommendation
    """
    if not findings:
        return ConfidenceScore(
            level=ConfidenceLevel.SPECULATIVE,
            numeric_score=0.0,
            num_sources=0,
            rationale="No supporting evidence"
        )

    # Find minimum confidence (weakest link)
    min_confidence = min((f.confidence for f in findings), key=lambda c: c.value)

    # For strategic recommendations, require higher confidence
    if recommendation_type == "strategic":
        # Only downgrade if evidence is not uniformly strong
        all_high = all(f.confidence == ConfidenceLevel.HIGH for f in findings)
        if all_high and len(findings) >= 3:
            # Multiple high-confidence findings can support high-confidence strategic recommendation
            final_level = ConfidenceLevel.HIGH
        else:
            # Downgrade by one level for strategic recommendations
            adjusted_value = max(0, min_confidence.value - 1)
            adjusted_levels = {
                3: ConfidenceLevel.HIGH,
                2: ConfidenceLevel.MEDIUM,
                1: ConfidenceLevel.LOW,
                0: ConfidenceLevel.SPECULATIVE
            }
            final_level = adjusted_levels[adjusted_value]
    else:
        # Tactical recommendations can keep same confidence
        final_level = min_confidence

    # KNOWN CONTRADICTION — loss/churn override is intentionally disabled.
    #
    # This code upgrades confidence by one tier when loss_churn_validated=True.
    # Agent instructions (lens-executor.md, synthesizer.md) instead say to
    # *downgrade* all competing lens scores to LOW. These are opposite behaviors.
    #
    # The correct direction requires a product decision. Until that decision is
    # recorded and the agent instructions are updated to match, this path is
    # disabled so the codebase does not silently produce wrong output on either path.
    #
    # TODO: Resolve before enabling this feature.
    #   See: /tmp/aw-debate/RECOMMENDATION.md Fix 6
    if loss_churn_validated:
        raise NotImplementedError(
            "loss_churn_validated override is disabled pending a product decision. "
            "See: agents/lens-executor.md (CROSS-VALIDATION / loss_churn_override_active) vs "
            "confidence_scoring.py:propagate_confidence for the contradiction."
        )

    # Count total sources
    total_sources = sum(len(f.sources) for f in findings)

    rationale = f"Propagated from {len(findings)} findings ({recommendation_type})"

    return ConfidenceScore(
        level=final_level,
        numeric_score=final_level.value / 3.0,
        num_sources=total_sources,
        rationale=rationale
    )


def format_confidence_display(
    level: ConfidenceLevel,
    format_type: str = "badge",
    numeric_score: Optional[float] = None
) -> str:
    """
    Format confidence level for display.

    Args:
        level: Confidence level to format
        format_type: Display format ("badge", "text", "numeric")
        numeric_score: Optional numeric score for numeric format

    Returns:
        Formatted string for display
    """
    if format_type == "badge":
        # Badge format: [HIGH] [MEDIUM] [LOW] [SPECULATIVE]
        badges = {
            ConfidenceLevel.HIGH: "[HIGH]",
            ConfidenceLevel.MEDIUM: "[MEDIUM]",
            ConfidenceLevel.LOW: "[LOW]",
            ConfidenceLevel.SPECULATIVE: "[SPECULATIVE]"
        }
        return badges[level]

    elif format_type == "text":
        # Text description
        descriptions = {
            ConfidenceLevel.HIGH: "High confidence (verified from multiple reliable sources)",
            ConfidenceLevel.MEDIUM: "Medium confidence (credible but limited sources)",
            ConfidenceLevel.LOW: "Low confidence (unverified or low-quality sources)",
            ConfidenceLevel.SPECULATIVE: "Speculative (inference without direct evidence)"
        }
        return descriptions[level]

    elif format_type == "numeric":
        # Numeric format: 85% confidence
        if numeric_score is not None:
            percentage = int(numeric_score * 100)
            return f"{percentage}%"
        else:
            # Use level value as percentage
            percentage = int((level.value / 3.0) * 100)
            return f"{percentage}%"

    else:
        # Default to badge
        return format_confidence_display(level, format_type="badge")


# Convenience functions

def create_finding(
    statement: str,
    sources: List[str],
    source_quality: str = "medium",
    verification_method: str = "secondary"
) -> ConfidenceFinding:
    """
    Create a finding with automatic confidence calculation.

    Args:
        statement: The finding statement
        sources: List of sources
        source_quality: Quality of sources
        verification_method: How verified

    Returns:
        ConfidenceFinding with calculated confidence
    """
    score = calculate_confidence(
        num_sources=len(sources),
        source_quality=source_quality,
        verification_method=verification_method
    )

    return ConfidenceFinding(
        statement=statement,
        confidence=score.level,
        sources=sources,
        rationale=score.rationale
    )


def is_high_confidence(level: ConfidenceLevel) -> bool:
    """Check if confidence level is HIGH."""
    return level == ConfidenceLevel.HIGH


def is_actionable_confidence(level: ConfidenceLevel) -> bool:
    """
    Check if confidence is high enough for action.

    MEDIUM or higher is considered actionable.
    """
    return level.value >= ConfidenceLevel.MEDIUM.value


def confidence_warning(level: ConfidenceLevel) -> Optional[str]:
    """
    Get warning message for low confidence levels.

    Args:
        level: Confidence level

    Returns:
        Warning message or None if no warning needed
    """
    if level == ConfidenceLevel.LOW:
        return "⚠️  Low confidence - verify before acting"
    elif level == ConfidenceLevel.SPECULATIVE:
        return "⚠️  Speculative - requires validation"
    return None
