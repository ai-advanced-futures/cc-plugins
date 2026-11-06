#!/usr/bin/env python3
"""
UX Health Score Calculator

Calculates unified UX health score from multi-framework evaluation results
using contextual weighting profiles.

Usage:
    python calculate_ux_score.py [--profile PROFILE] [--input FILE] [--output FILE]
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Union

# Contextual weighting profiles for different product types
WEIGHTING_PROFILES = {
    "balanced": {
        "nielsen": 0.25,
        "wcag": 0.25,
        "ai_hci": 0.20,
        "rams": 0.15,
        "norman": 0.15
    },
    "ai-heavy": {
        "nielsen": 0.20,
        "wcag": 0.20,
        "ai_hci": 0.35,
        "rams": 0.10,
        "norman": 0.15
    },
    "accessibility-first": {
        "nielsen": 0.20,
        "wcag": 0.45,
        "ai_hci": 0.15,
        "rams": 0.10,
        "norman": 0.10
    },
    "mobile-first": {
        "nielsen": 0.30,
        "wcag": 0.20,
        "ai_hci": 0.10,
        "rams": 0.20,
        "norman": 0.20
    },
    "enterprise": {
        "nielsen": 0.30,
        "wcag": 0.30,
        "ai_hci": 0.10,
        "rams": 0.10,
        "norman": 0.20
    }
}

# Grade scale mapping
GRADE_SCALE = [
    (90, "A", "Excellent"),
    (80, "B", "Good"),
    (70, "C", "Acceptable"),
    (60, "D", "Needs Work"),
    (50, "F", "Poor"),
    (0, "Block", "Cannot Release")
]


def get_grade(score: float) -> tuple[str, str]:
    """Convert numeric score to letter grade and status."""
    for threshold, grade, status in GRADE_SCALE:
        if score >= threshold:
            return grade, status
    return "Block", "Cannot Release"


def calculate_framework_score(framework_data: dict) -> float:
    """
    Calculate score for a single framework.

    Args:
        framework_data: Dict with passed/failed/total counts or direct score

    Returns:
        Score as float between 0 and 1
    """
    # If direct score provided
    if "score" in framework_data:
        score = framework_data["score"]
        # Normalize if score is 0-100
        if score > 1:
            return score / 100
        return score

    # Calculate from pass/fail counts
    passed = framework_data.get("passed", 0)
    total = framework_data.get("total", 0)

    if total == 0:
        # Check for total_criteria
        total = framework_data.get("total_criteria", 0)
        if total == 0:
            return 1.0  # No criteria = not applicable = perfect score

    return passed / total


def calculate_weighted_score(framework_scores: Dict[str, float], profile: str) -> float:
    """
    Calculate weighted UX health score.

    Args:
        framework_scores: Dict of framework name to score (0-1)
        profile: Name of weighting profile to use

    Returns:
        Weighted score as float between 0 and 100
    """
    if profile not in WEIGHTING_PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Available: {list(WEIGHTING_PROFILES.keys())}")

    weights = WEIGHTING_PROFILES[profile]

    weighted_sum = 0.0
    total_weight = 0.0

    for framework, weight in weights.items():
        if framework in framework_scores:
            weighted_sum += framework_scores[framework] * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize by actual weight used (in case some frameworks missing)
    return (weighted_sum / total_weight) * 100


def normalize_severity(severity: Union[str, int]) -> str:
    """Normalize severity from various formats to standard string."""
    severity_map = {
        4: "critical",
        3: "high",
        2: "medium",
        1: "low",
        0: "none",
        "catastrophe": "critical",
        "major": "high",
        "minor": "medium",
        "cosmetic": "low"
    }

    if isinstance(severity, int):
        return severity_map.get(severity, "medium")

    severity_lower = severity.lower()
    return severity_map.get(severity_lower, severity_lower)


def count_findings_by_severity(findings: List[dict]) -> Dict[str, int]:
    """Count findings grouped by normalized severity."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for finding in findings:
        severity = normalize_severity(finding.get("severity", "medium"))
        if severity in counts:
            counts[severity] += 1

    return counts


def identify_critical_findings(findings: List[dict]) -> List[dict]:
    """Extract critical findings that should block release."""
    critical = []

    for finding in findings:
        severity = normalize_severity(finding.get("severity", "medium"))
        if severity == "critical":
            critical.append({
                "finding_id": finding.get("finding_id", finding.get("id", "unknown")),
                "framework": finding.get("framework", "unknown"),
                "criterion": finding.get("criterion", finding.get("heuristic", finding.get("guideline", "unknown"))),
                "title": finding.get("title", finding.get("name", finding.get("description", "Unknown issue"))),
                "severity": "critical"
            })

    return critical


def calculate_ux_score(
    evaluation_data: dict,
    profile: str = "balanced",
    has_ai_features: bool = False
) -> dict:
    """
    Calculate comprehensive UX health score from evaluation data.

    Args:
        evaluation_data: Dict containing framework evaluation results
        profile: Weighting profile to use
        has_ai_features: Whether product has AI features (affects AI-HCI weight)

    Returns:
        Complete score breakdown with grade and recommendations
    """
    # Extract framework data
    frameworks = {}
    all_findings = []

    # Nielsen heuristics
    if "nielsen" in evaluation_data:
        nielsen_data = evaluation_data["nielsen"]
        frameworks["nielsen"] = calculate_framework_score(nielsen_data)
        all_findings.extend(nielsen_data.get("findings", []))

    # WCAG accessibility
    if "wcag" in evaluation_data or "accessibility" in evaluation_data:
        wcag_data = evaluation_data.get("wcag", evaluation_data.get("accessibility", {}))
        frameworks["wcag"] = calculate_framework_score(wcag_data)
        all_findings.extend(wcag_data.get("findings", []))

    # AI-HCI guidelines
    if "ai_hci" in evaluation_data or "ai-hci" in evaluation_data:
        ai_data = evaluation_data.get("ai_hci", evaluation_data.get("ai-hci", {}))
        frameworks["ai_hci"] = calculate_framework_score(ai_data)
        all_findings.extend(ai_data.get("findings", []))
    elif not has_ai_features:
        # If no AI features, give perfect AI-HCI score
        frameworks["ai_hci"] = 1.0

    # Rams principles
    if "rams" in evaluation_data:
        rams_data = evaluation_data["rams"]
        frameworks["rams"] = calculate_framework_score(rams_data)
        all_findings.extend(rams_data.get("findings", []))

    # Norman emotional design
    if "norman" in evaluation_data:
        norman_data = evaluation_data["norman"]
        frameworks["norman"] = calculate_framework_score(norman_data)
        all_findings.extend(norman_data.get("findings", []))

    # Calculate weighted score
    overall_score = calculate_weighted_score(frameworks, profile)
    grade, status = get_grade(overall_score)

    # Count findings by severity
    severity_counts = count_findings_by_severity(all_findings)

    # Identify critical blockers
    critical_findings = identify_critical_findings(all_findings)

    # Determine if release should be blocked
    release_blocked = (
        overall_score < 50 or
        len(critical_findings) > 0 or
        severity_counts.get("critical", 0) > 0
    )

    weights = WEIGHTING_PROFILES[profile]

    return {
        "ux_health_score": {
            "overall": round(overall_score, 1),
            "grade": grade,
            "status": status,
            "release_blocked": release_blocked,
            "breakdown": {
                framework: {
                    "score": round(score * 100, 1),
                    "weight": weights.get(framework, 0),
                    "weighted_contribution": round(score * weights.get(framework, 0) * 100, 1)
                }
                for framework, score in frameworks.items()
            }
        },
        "findings_summary": {
            "total": len(all_findings),
            "by_severity": severity_counts,
            "critical_count": len(critical_findings)
        },
        "critical_findings": critical_findings,
        "profile_used": profile,
        "calculation_metadata": {
            "frameworks_evaluated": list(frameworks.keys()),
            "has_ai_features": has_ai_features,
            "calculated_at": datetime.utcnow().isoformat() + "Z"
        }
    }


def generate_score_from_file(input_path: str, profile: str = "balanced") -> dict:
    """Load evaluation data from file and calculate UX health score.

    Reads ``has_ai_features`` from the input JSON using a two-step lookup
    (A-007 — canonical field location):

    1. CANONICAL: ``evaluation_data["context"]["has_ai_features"]``  (preferred)
    2. FALLBACK:  ``evaluation_data["metadata"]["has_ai_features"]``
    3. DEFAULT:   ``False`` when neither key is present

    Framework keys inside ``evaluation_data`` use underscores (e.g. ``ai_hci``),
    not hyphens.  Each framework value must contain ``passed``, ``total``, and
    ``findings`` fields.

    Args:
        input_path: Path to a JSON file containing evaluation data.
        profile: Weighting profile name (default: ``"balanced"``).

    Returns:
        dict: Full UX health score result from :func:`calculate_ux_score`.
    """
    with open(input_path, 'r') as f:
        evaluation_data = json.load(f)

    # Check if AI features present in context
    has_ai = False
    if "context" in evaluation_data:
        has_ai = evaluation_data["context"].get("has_ai_features", False)
    elif "metadata" in evaluation_data:
        has_ai = evaluation_data["metadata"].get("has_ai_features", False)

    return calculate_ux_score(evaluation_data, profile, has_ai)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate UX health score from evaluation data"
    )
    parser.add_argument(
        "--profile", "-p",
        choices=list(WEIGHTING_PROFILES.keys()),
        default="balanced",
        help="Weighting profile to use (default: balanced)"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input evaluation JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file (default: stdout)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Include detailed breakdown"
    )

    args = parser.parse_args()

    try:
        result = generate_score_from_file(args.input, args.profile)

        output_json = json.dumps(result, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"Score written to {args.output}")
            print(f"UX Health Score: {result['ux_health_score']['overall']} ({result['ux_health_score']['grade']})")
        else:
            print(output_json)

    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
