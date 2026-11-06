"""
Multi-Source Triangulation Module.

Cross-reference findings across multiple sources to identify corroborated
facts, contradictions, and unverified claims. This module is critical for
ensuring intelligence quality and confidence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class VerificationStatus(Enum):
    """Final verification status for findings (output dimension).

    Derived from SourceAgreement (input dimension):
    - SourceAgreement.STRONG → CORROBORATED
    - SourceAgreement.MODERATE → PARTIALLY_CONFIRMED
    - SourceAgreement.WEAK → SINGLE_SOURCE
    - SourceAgreement.CONFLICTING → CONTRADICTED
    """

    CORROBORATED = "corroborated"  # Multiple independent sources agree
    SINGLE_SOURCE = "single_source"  # Only one source, unverified
    CONTRADICTED = "contradicted"  # Sources disagree
    PARTIALLY_CONFIRMED = "partially_confirmed"  # Some aspects verified
    UNVERIFIABLE = "unverifiable"  # Cannot be verified with available data


class SourceAgreement(Enum):
    """Level of agreement between sources.

    This enum describes SOURCE RELATIONSHIPS (input dimension).
    Maps to VerificationStatus (output dimension) as follows:
    - STRONG (3+ sources agree) → VerificationStatus.CORROBORATED
    - MODERATE (2 sources agree) → VerificationStatus.PARTIALLY_CONFIRMED
    - WEAK (single source) → VerificationStatus.SINGLE_SOURCE
    - CONFLICTING (sources disagree) → VerificationStatus.CONTRADICTED
    """

    STRONG = "strong"  # 3+ sources agree
    MODERATE = "moderate"  # 2 sources agree
    WEAK = "weak"  # Single source
    CONFLICTING = "conflicting"  # Sources disagree


@dataclass
class Finding:
    """Represents a finding from competitive intelligence."""

    id: str
    claim: str
    value: Any
    source_id: str
    source_type: str  # e.g., "official", "review", "news"
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorroborationResult:
    """Result of corroboration analysis for a finding."""

    finding_id: str
    claim: str
    status: VerificationStatus
    agreement: SourceAgreement
    supporting_sources: List[str] = field(default_factory=list)
    contradicting_sources: List[str] = field(default_factory=list)
    confidence_adjustment: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class Contradiction:
    """Represents a contradiction between sources."""

    id: str
    claim_type: str
    finding_a: Finding
    finding_b: Finding
    severity: str = "moderate"  # low, moderate, high
    resolution: Optional[str] = None
    resolution_confidence: float = 0.0


@dataclass
class TriangulationReport:
    """Complete triangulation report for an analysis."""

    session_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_findings: int = 0
    corroborated: List[CorroborationResult] = field(default_factory=list)
    single_source: List[CorroborationResult] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    confidence_summary: Dict[str, float] = field(default_factory=dict)


class FindingMatcher:
    """Match similar findings across sources for comparison."""

    # Comparison hierarchy:
    # _values_match_exactly() → strict equality (threshold: type match + <0.001 diff for numbers)
    # _values_similar() → loose match (threshold: 15% diff for numbers, containment for strings)
    # _values_contradict() → in ContradictionDetector — explicit opposition (30% diff for numbers)
    # These are intentionally separate to support different use cases (are_similar vs detect contradictions)
    # Future refactor: consolidate into compare_values(v1, v2) → ValueRelationship enum

    # Similarity thresholds
    EXACT_MATCH_THRESHOLD = 0.95
    SIMILAR_MATCH_THRESHOLD = 0.7

    def __init__(self):
        """Initialize the matcher."""
        self.claim_type_mappings: Dict[str, Set[str]] = {
            "pricing": {"price", "pricing", "cost", "rate", "fee", "subscription", "$/month", "/month"},
            "feature": {"feature", "capability", "function", "support", "api"},
            "customer": {"customer", "client", "user", "company"},
            "market": {"market", "segment", "industry", "vertical"},
            "growth": {"growth", "revenue", "funding", "employees"},
        }

    def extract_claim_type(self, finding: Finding) -> str:
        """Extract the type of claim from a finding."""
        claim_lower = finding.claim.lower()

        for claim_type, keywords in self.claim_type_mappings.items():
            if any(kw in claim_lower for kw in keywords):
                return claim_type

        return finding.metadata.get("claim_type", "general")

    def are_similar(
        self,
        finding_a: Finding,
        finding_b: Finding,
        strict: bool = False
    ) -> bool:
        """Check if two findings are about the same claim."""
        # Same source means not independent
        if finding_a.source_id == finding_b.source_id:
            return False

        # Must be same claim type
        type_a = self.extract_claim_type(finding_a)
        type_b = self.extract_claim_type(finding_b)

        if type_a != type_b:
            return False

        # Check for value similarity
        if strict:
            return self._values_match_exactly(finding_a.value, finding_b.value)
        else:
            return self._values_similar(finding_a.value, finding_b.value, type_a)

    def _values_match_exactly(self, value_a: Any, value_b: Any) -> bool:
        """Check if values match exactly."""
        if type(value_a) is not type(value_b):
            return False

        if isinstance(value_a, (int, float)):
            return abs(value_a - value_b) < 0.001
        elif isinstance(value_a, str):
            return value_a.lower().strip() == value_b.lower().strip()
        else:
            return value_a == value_b

    def _values_similar(
        self,
        value_a: Any,
        value_b: Any,
        claim_type: str
    ) -> bool:
        """Check if values are similar (not exact match required)."""
        if type(value_a) is not type(value_b):
            # Allow string/number comparison for pricing
            if claim_type == "pricing":
                try:
                    num_a = float(str(value_a).replace("$", "").replace(",", ""))
                    num_b = float(str(value_b).replace("$", "").replace(",", ""))
                    # Within 20% is similar for pricing
                    if max(num_a, num_b) > 0:
                        diff = abs(num_a - num_b) / max(num_a, num_b)
                        return diff < 0.2
                except (ValueError, TypeError):
                    pass
            return False

        if isinstance(value_a, (int, float)):
            # Within 15% is similar
            if max(abs(value_a), abs(value_b)) > 0:
                diff = abs(value_a - value_b) / max(abs(value_a), abs(value_b))
                return diff < 0.15
            return True
        elif isinstance(value_a, str):
            # Simple string containment
            a_lower = value_a.lower().strip()
            b_lower = value_b.lower().strip()
            return a_lower in b_lower or b_lower in a_lower
        else:
            return value_a == value_b

    def find_related_findings(
        self,
        target: Finding,
        findings: List[Finding],
        strict: bool = False
    ) -> List[Finding]:
        """Find findings related to the target."""
        related = []
        for finding in findings:
            if finding.id != target.id and self.are_similar(target, finding, strict):
                related.append(finding)
        return related


class ContradictionDetector:
    """Detect contradictions between findings."""

    def __init__(self, matcher: Optional[FindingMatcher] = None):
        """Initialize the detector."""
        self.matcher = matcher or FindingMatcher()
        self._contradiction_counter = 0

    def _generate_contradiction_id(self) -> str:
        """Generate a unique contradiction ID."""
        self._contradiction_counter += 1
        return f"contradiction-{self._contradiction_counter:04d}"

    def detect(
        self,
        findings: List[Finding]
    ) -> List[Contradiction]:
        """Detect contradictions among findings."""
        contradictions = []
        processed_pairs: Set[Tuple[str, str]] = set()

        for i, finding_a in enumerate(findings):
            for finding_b in findings[i + 1:]:
                # Skip same source
                if finding_a.source_id == finding_b.source_id:
                    continue

                # Skip already processed pair
                pair = tuple(sorted([finding_a.id, finding_b.id]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)

                # Check for contradiction
                contradiction = self._check_contradiction(finding_a, finding_b)
                if contradiction:
                    contradictions.append(contradiction)

        return contradictions

    def _check_contradiction(
        self,
        finding_a: Finding,
        finding_b: Finding
    ) -> Optional[Contradiction]:
        """Check if two findings contradict each other."""
        # Must be same claim type
        type_a = self.matcher.extract_claim_type(finding_a)
        type_b = self.matcher.extract_claim_type(finding_b)

        if type_a != type_b:
            return None

        # Check for value contradiction
        if self._values_contradict(finding_a.value, finding_b.value, type_a):
            severity = self._assess_severity(finding_a, finding_b, type_a)
            return Contradiction(
                id=self._generate_contradiction_id(),
                claim_type=type_a,
                finding_a=finding_a,
                finding_b=finding_b,
                severity=severity,
            )

        return None

    def _values_contradict(
        self,
        value_a: Any,
        value_b: Any,
        claim_type: str
    ) -> bool:
        """Check if values contradict each other."""
        # Handle None values
        if value_a is None or value_b is None:
            return False

        # Convert to comparable types if needed
        if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
            # More than 30% difference is a contradiction
            if max(abs(value_a), abs(value_b)) > 0:
                diff = abs(value_a - value_b) / max(abs(value_a), abs(value_b))
                return diff > 0.3
            return False

        if isinstance(value_a, str) and isinstance(value_b, str):
            a_lower = value_a.lower().strip()
            b_lower = value_b.lower().strip()

            # Explicit opposites
            opposites = [
                ("yes", "no"),
                ("true", "false"),
                ("available", "unavailable"),
                ("supported", "not supported"),
                ("free", "paid"),
            ]

            for pos, neg in opposites:
                if (pos in a_lower and neg in b_lower) or \
                   (neg in a_lower and pos in b_lower):
                    return True

            # Different non-empty values for same claim
            if a_lower and b_lower and a_lower != b_lower:
                # Only contradiction if they're both short definitive statements
                if len(a_lower) < 50 and len(b_lower) < 50:
                    return True

        return False

    def _assess_severity(
        self,
        finding_a: Finding,
        finding_b: Finding,
        claim_type: str
    ) -> str:
        """Assess the severity of a contradiction."""
        # Both high confidence = high severity
        if finding_a.confidence > 0.7 and finding_b.confidence > 0.7:
            return "high"

        # One high confidence = moderate
        if finding_a.confidence > 0.7 or finding_b.confidence > 0.7:
            return "moderate"

        # Pricing contradictions are always at least moderate
        if claim_type == "pricing":
            return "moderate"

        return "low"


class CorroborationValidator:
    """Validate and score corroboration of findings.

    Confidence Adjustment Architecture
    ------------------------------------
    This class produces ADVISORY confidence adjustments stored in
    CorroborationResult.confidence_adjustment. These are NOT additive
    deltas to be applied directly to numeric confidence scores.

    Callers should interpret adjustments as level-based upgrades/downgrades:
    - CORROBORATION_BOOST (+0.2 advisory): upgrade ConfidenceLevel by one tier
    - SINGLE_SOURCE_PENALTY (-0.1 advisory): keep current level (informational only)
    - CONTRADICTION_PENALTY (-0.3 advisory): downgrade ConfidenceLevel by one tier

    Primary confidence calculation is in confidence_scoring.calculate_confidence()
    (multiplicative algorithm, source-based). Triangulation provides corroboration
    context that callers apply by re-calling calculate_confidence() with updated
    source count/quality, or by using VerificationStatus to adjust the level.

    VerificationStatus → ConfidenceLevel mapping:
    - CORROBORATED (STRONG agreement) → upgrade level by 1
    - PARTIALLY_CONFIRMED (MODERATE agreement) → keep level
    - SINGLE_SOURCE (WEAK) → keep level (apply SINGLE_SOURCE_PENALTY context)
    - CONTRADICTED / CONFLICTING → downgrade level by 1
    """

    # Advisory confidence deltas (see class docstring for usage)
    CORROBORATION_BOOST = 0.2
    SINGLE_SOURCE_PENALTY = -0.1
    CONTRADICTION_PENALTY = -0.3

    def __init__(self, matcher: Optional[FindingMatcher] = None):
        """Initialize the validator."""
        self.matcher = matcher or FindingMatcher()

    def validate(
        self,
        finding: Finding,
        all_findings: List[Finding]
    ) -> CorroborationResult:
        """Validate a finding against all other findings."""
        # Find related findings from different sources
        related = self.matcher.find_related_findings(finding, all_findings)

        if not related:
            return CorroborationResult(
                finding_id=finding.id,
                claim=finding.claim,
                status=VerificationStatus.SINGLE_SOURCE,
                agreement=SourceAgreement.WEAK,
                confidence_adjustment=self.SINGLE_SOURCE_PENALTY,
                notes=["No corroborating sources found"],
            )

        # Check for support vs contradiction
        supporting = []
        contradicting = []

        for rel in related:
            if self._supports(finding, rel):
                supporting.append(rel.source_id)
            elif self._contradicts(finding, rel):
                contradicting.append(rel.source_id)

        return self._build_result(finding, supporting, contradicting)

    def _supports(self, target: Finding, other: Finding) -> bool:
        """Check if other finding supports the target."""
        return self.matcher.are_similar(target, other, strict=False)

    def _contradicts(self, target: Finding, other: Finding) -> bool:
        """Check if other finding contradicts the target."""
        detector = ContradictionDetector(self.matcher)
        return detector._values_contradict(
            target.value,
            other.value,
            self.matcher.extract_claim_type(target)
        )

    def _build_result(
        self,
        finding: Finding,
        supporting: List[str],
        contradicting: List[str]
    ) -> CorroborationResult:
        """Build a corroboration result."""
        if contradicting and not supporting:
            return CorroborationResult(
                finding_id=finding.id,
                claim=finding.claim,
                status=VerificationStatus.CONTRADICTED,
                agreement=SourceAgreement.CONFLICTING,
                supporting_sources=supporting,
                contradicting_sources=contradicting,
                confidence_adjustment=self.CONTRADICTION_PENALTY,
                notes=[f"Contradicted by {len(contradicting)} source(s)"],
            )

        if supporting and contradicting:
            return CorroborationResult(
                finding_id=finding.id,
                claim=finding.claim,
                status=VerificationStatus.PARTIALLY_CONFIRMED,
                agreement=SourceAgreement.CONFLICTING,
                supporting_sources=supporting,
                contradicting_sources=contradicting,
                confidence_adjustment=0.0,  # Mixed signals
                notes=[
                    f"Supported by {len(supporting)} source(s)",
                    f"Contradicted by {len(contradicting)} source(s)",
                ],
            )

        # Only supporting sources
        if len(supporting) >= 2:
            agreement = SourceAgreement.STRONG if len(supporting) >= 3 else SourceAgreement.MODERATE
            return CorroborationResult(
                finding_id=finding.id,
                claim=finding.claim,
                status=VerificationStatus.CORROBORATED,
                agreement=agreement,
                supporting_sources=supporting,
                confidence_adjustment=self.CORROBORATION_BOOST,
                notes=[f"Corroborated by {len(supporting)} independent source(s)"],
            )

        return CorroborationResult(
            finding_id=finding.id,
            claim=finding.claim,
            status=VerificationStatus.PARTIALLY_CONFIRMED,
            agreement=SourceAgreement.MODERATE,
            supporting_sources=supporting,
            confidence_adjustment=self.CORROBORATION_BOOST / 2,
            notes=["Partially confirmed by 1 additional source"],
        )


class Triangulator:
    """Main triangulation engine for cross-referencing sources."""

    def __init__(self):
        """Initialize the triangulator."""
        self.matcher = FindingMatcher()
        self.contradiction_detector = ContradictionDetector(self.matcher)
        self.corroboration_validator = CorroborationValidator(self.matcher)

    def triangulate(
        self,
        findings: List[Finding],
        session_id: str = "default"
    ) -> TriangulationReport:
        """Perform full triangulation analysis on findings."""
        report = TriangulationReport(
            session_id=session_id,
            total_findings=len(findings),
        )

        if not findings:
            report.confidence_summary = self._calculate_confidence_summary(report)
            return report

        # Detect contradictions first
        report.contradictions = self.contradiction_detector.detect(findings)

        # Validate each finding
        for finding in findings:
            result = self.corroboration_validator.validate(finding, findings)

            if result.status == VerificationStatus.CORROBORATED:
                report.corroborated.append(result)
            elif result.status == VerificationStatus.SINGLE_SOURCE:
                report.single_source.append(result)

        # Calculate confidence summary
        report.confidence_summary = self._calculate_confidence_summary(report)

        return report

    def _calculate_confidence_summary(
        self,
        report: TriangulationReport
    ) -> Dict[str, float]:
        """Calculate overall confidence metrics."""
        total = report.total_findings
        if total == 0:
            return {
                "corroboration_rate": 0.0,
                "single_source_rate": 1.0,
                "contradiction_rate": 0.0,
                "overall_confidence": 0.0,
            }

        corroborated_count = len(report.corroborated)
        single_source_count = len(report.single_source)
        contradiction_count = len(report.contradictions)

        corroboration_rate = corroborated_count / total
        single_source_rate = single_source_count / total
        contradiction_rate = contradiction_count / total if total > 1 else 0.0

        # Overall confidence weighted formula
        overall = (
            corroboration_rate * 1.0 +
            (1 - single_source_rate) * 0.5 +
            (1 - contradiction_rate) * 0.3
        ) / 1.8

        return {
            "corroboration_rate": round(corroboration_rate, 3),
            "single_source_rate": round(single_source_rate, 3),
            "contradiction_rate": round(contradiction_rate, 3),
            "overall_confidence": round(overall, 3),
        }

    def get_high_confidence_findings(
        self,
        report: TriangulationReport,
        findings: List[Finding]
    ) -> List[Finding]:
        """Get findings with high triangulation confidence."""
        corroborated_ids = {r.finding_id for r in report.corroborated}
        return [f for f in findings if f.id in corroborated_ids]

    def get_unverified_claims(
        self,
        report: TriangulationReport
    ) -> List[str]:
        """Get claims that remain unverified (single source)."""
        return [r.claim for r in report.single_source]

    def resolve_contradiction(
        self,
        contradiction: Contradiction,
        resolution_method: str = "higher_confidence"
    ) -> Finding:
        """Attempt to resolve a contradiction by choosing the better finding."""
        finding_a = contradiction.finding_a
        finding_b = contradiction.finding_b

        if resolution_method == "higher_confidence":
            winner = finding_a if finding_a.confidence >= finding_b.confidence else finding_b
        elif resolution_method == "more_recent":
            winner = finding_a if finding_a.timestamp >= finding_b.timestamp else finding_b
        elif resolution_method == "official_source":
            if finding_a.source_type == "official":
                winner = finding_a
            elif finding_b.source_type == "official":
                winner = finding_b
            else:
                winner = finding_a if finding_a.confidence >= finding_b.confidence else finding_b
        else:
            winner = finding_a  # Default to first

        # Update contradiction with resolution
        contradiction.resolution = f"Resolved via {resolution_method}: {winner.source_id}"
        contradiction.resolution_confidence = winner.confidence

        return winner


def triangulate_findings(
    findings: List[Finding],
    session_id: str = "default"
) -> TriangulationReport:
    """Convenience function to triangulate a list of findings.

    Args:
        findings: List of findings to triangulate
        session_id: Session identifier for the report

    Returns:
        Complete triangulation report
    """
    triangulator = Triangulator()
    return triangulator.triangulate(findings, session_id)
