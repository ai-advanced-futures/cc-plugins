#!/usr/bin/env python3
"""
Evaluation Report Generator

Generates comprehensive UX evaluation reports from multi-framework findings,
synthesizing accessibility, AI-HCI, and usability evaluations into unified reports.

Usage:
    python generate_evaluation_report.py --input FINDINGS_DIR --output REPORT_FILE [--format FORMAT]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Import score calculator if available
try:
    from calculate_ux_score import (
        WEIGHTING_PROFILES,
        calculate_ux_score,
        get_grade,
        normalize_severity,
    )
except ImportError:
    # Define inline if not available as module
    WEIGHTING_PROFILES = {
        "balanced": {"nielsen": 0.25, "wcag": 0.25, "ai_hci": 0.20, "rams": 0.15, "norman": 0.15},
        "ai-heavy": {"nielsen": 0.20, "wcag": 0.20, "ai_hci": 0.35, "rams": 0.10, "norman": 0.15},
        "accessibility-first": {"nielsen": 0.20, "wcag": 0.45, "ai_hci": 0.15, "rams": 0.10, "norman": 0.10},
    }

    def normalize_severity(severity):
        if isinstance(severity, int):
            return {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(severity, "medium")
        return severity.lower()

    def get_grade(score):
        for threshold, grade, status in [(90, "A", "Excellent"), (80, "B", "Good"),
                                          (70, "C", "Acceptable"), (60, "D", "Needs Work"),
                                          (50, "F", "Poor"), (0, "Block", "Cannot Release")]:
            if score >= threshold:
                return grade, status
        return "Block", "Cannot Release"


def load_findings_from_directory(findings_dir: str) -> dict:
    """Load all finding files from a directory."""
    path = Path(findings_dir)
    findings = {}

    file_mapping = {
        "accessibility": ["accessibility", "wcag", "a11y"],
        "ai_hci": ["ai-hci", "ai_hci", "human-ai"],
        "nielsen": ["nielsen", "usability", "heuristics"],
        "rams": ["rams", "design-principles"],
        "norman": ["norman", "emotional"]
    }

    for file_path in path.glob("*.json"):
        name = file_path.stem.lower()

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Map to standard framework name
        for framework, patterns in file_mapping.items():
            if any(p in name for p in patterns):
                findings[framework] = data
                break

    return findings


def merge_findings(framework_findings: dict) -> List[dict]:
    """Merge findings from all frameworks into unified list."""
    all_findings = []

    for framework, data in framework_findings.items():
        framework_findings_list = data.get("findings", [])

        for finding in framework_findings_list:
            # Ensure framework is tagged
            finding["framework"] = framework

            # Normalize severity
            if "severity" in finding:
                finding["normalized_severity"] = normalize_severity(finding["severity"])

            all_findings.append(finding)

    return all_findings


def prioritize_findings(findings: List[dict]) -> List[dict]:
    """Sort findings by priority (severity + impact)."""
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def sort_key(finding):
        severity = finding.get("normalized_severity", finding.get("severity", "medium"))
        if isinstance(severity, str):
            return severity_order.get(severity.lower(), 2)
        return severity

    return sorted(findings, key=sort_key)


def generate_recommendations(findings: List[dict], max_recommendations: int = 10) -> List[dict]:
    """Generate prioritized recommendations from findings."""
    recommendations = []

    # Group by remediation to avoid duplicates
    seen_recommendations = set()

    for finding in findings:
        remediation = finding.get("remediation", {})
        rec_text = remediation.get("recommendation", "")

        if not rec_text or rec_text in seen_recommendations:
            continue

        seen_recommendations.add(rec_text)

        effort = remediation.get("effort", "medium")
        severity = finding.get("normalized_severity", finding.get("severity", "medium"))

        # Calculate priority score (higher = more urgent)
        severity_score = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
            severity if isinstance(severity, str) else normalize_severity(severity), 2
        )
        effort_score = {"low": 3, "medium": 2, "high": 1}.get(effort, 2)
        priority = severity_score * effort_score

        recommendations.append({
            "priority": priority,
            "recommendation": rec_text,
            "effort": effort,
            "impact": severity,
            "finding_ids": [finding.get("finding_id", finding.get("id", "unknown"))],
            "frameworks": [finding.get("framework", "unknown")]
        })

    # Sort by priority (descending) and limit
    recommendations.sort(key=lambda x: x["priority"], reverse=True)

    # Assign priority numbers
    for i, rec in enumerate(recommendations[:max_recommendations], 1):
        rec["priority_rank"] = i

    return recommendations[:max_recommendations]


def calculate_framework_summary(framework_data: dict, framework_name: str) -> dict:
    """Calculate summary statistics for a framework."""
    findings = framework_data.get("findings", [])

    # Get evaluation summary if available
    summary = framework_data.get("evaluation_summary", {})

    passed = summary.get("passed", 0)
    failed = summary.get("failed", len(findings))
    total = summary.get("total", summary.get("total_criteria", passed + failed))

    if total == 0:
        total = passed + failed if (passed + failed) > 0 else 1

    score = (passed / total) * 100 if total > 0 else 100

    # Count by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        sev = normalize_severity(finding.get("severity", "medium"))
        if sev in severity_counts:
            severity_counts[sev] += 1

    return {
        "framework": framework_name,
        "score": round(score, 1),
        "passed": passed,
        "failed": failed,
        "total_criteria": total,
        "findings_count": len(findings),
        "by_severity": severity_counts
    }


def generate_executive_summary(score_data: dict, findings: List[dict]) -> str:
    """Generate executive summary text."""
    score = score_data.get("ux_health_score", {})
    overall = score.get("overall", 0)
    grade = score.get("grade", "?")
    status = score.get("status", "Unknown")

    critical_count = score_data.get("findings_summary", {}).get("critical_count", 0)
    total_findings = score_data.get("findings_summary", {}).get("total", 0)

    summary_parts = [
        f"UX Health Score: {overall}/100 (Grade: {grade} - {status})"
    ]

    if critical_count > 0:
        summary_parts.append(f"CRITICAL: {critical_count} blocking issue(s) require immediate attention.")

    summary_parts.append(f"Total findings: {total_findings}")

    # Framework highlights
    breakdown = score.get("breakdown", {})
    if breakdown:
        lowest_framework = min(breakdown.items(), key=lambda x: x[1].get("score", 100))
        if lowest_framework[1].get("score", 100) < 70:
            summary_parts.append(
                f"Focus area: {lowest_framework[0].upper()} ({lowest_framework[1].get('score', 0)}%) needs improvement."
            )

    return "\n".join(summary_parts)


def generate_evaluation_report(
    framework_findings: dict,
    profile: str = "balanced",
    artifacts_evaluated: Optional[List[str]] = None,
    context: dict = None
) -> dict:
    """
    Generate comprehensive evaluation report.

    Args:
        framework_findings: Dict of framework name to evaluation data
        profile: Weighting profile to use
        artifacts_evaluated: List of artifact IDs evaluated
        context: Additional context (platform, features, etc.)

    Returns:
        Complete evaluation report as dict
    """
    context = context or {}
    artifacts_evaluated = artifacts_evaluated or []

    # Merge all findings
    all_findings = merge_findings(framework_findings)
    prioritized_findings = prioritize_findings(all_findings)

    # Calculate framework summaries
    framework_details = {}
    for framework, data in framework_findings.items():
        framework_details[framework] = calculate_framework_summary(data, framework)

    # Prepare data for score calculation
    score_input = {}
    for framework, data in framework_findings.items():
        summary = data.get("evaluation_summary", {})
        score_input[framework] = {
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", len(data.get("findings", []))),
            "total": summary.get("total", summary.get("total_criteria", 0)),
            "findings": data.get("findings", [])
        }

    # Calculate UX health score
    has_ai = context.get("has_ai_features", "ai_hci" in framework_findings)

    try:
        score_data = calculate_ux_score(score_input, profile, has_ai)
    except Exception:
        # Fallback calculation
        total_score = sum(
            framework_details[f].get("score", 0) * WEIGHTING_PROFILES.get(profile, {}).get(f, 0.2)
            for f in framework_details
        )
        grade, status = get_grade(total_score)
        score_data = {
            "ux_health_score": {
                "overall": round(total_score, 1),
                "grade": grade,
                "status": status,
                "breakdown": {f: {"score": d["score"]} for f, d in framework_details.items()}
            },
            "findings_summary": {
                "total": len(all_findings),
                "critical_count": sum(1 for f in all_findings if f.get("normalized_severity") == "critical")
            }
        }

    # Generate recommendations
    recommendations = generate_recommendations(prioritized_findings)

    # Identify critical findings
    critical_findings = [
        f for f in prioritized_findings
        if f.get("normalized_severity") == "critical" or f.get("severity") in ["critical", 4, "catastrophe"]
    ]

    # Generate executive summary
    executive_summary = generate_executive_summary(score_data, all_findings)

    # Build report
    report = {
        "schema_version": "1.0",
        "evaluation": {
            "evaluation_id": f"EVAL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "artifacts_evaluated": artifacts_evaluated,
            "context": {
                "platform": context.get("platform", "web"),
                "has_ai_features": has_ai,
                "weighting_profile": profile
            },
            "executive_summary": executive_summary,
            "ux_health_score": score_data.get("ux_health_score", {}),
            "findings_summary": {
                "total": len(all_findings),
                "by_severity": score_data.get("findings_summary", {}).get("by_severity", {}),
                "critical_count": len(critical_findings)
            },
            "critical_findings": [
                {
                    "finding_id": f.get("finding_id", f.get("id")),
                    "framework": f.get("framework"),
                    "criterion": f.get("criterion", f.get("heuristic", f.get("guideline"))),
                    "title": f.get("title", f.get("name", f.get("description", "")[:50])),
                    "severity": "critical"
                }
                for f in critical_findings
            ],
            "recommendations": recommendations,
            "framework_details": framework_details,
            "all_findings": prioritized_findings
        },
        "metadata": {
            "generated_by": "UX Evaluation Report Generator",
            "frameworks_evaluated": list(framework_findings.keys()),
            "profile_used": profile,
            "generation_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }

    return report


def format_markdown_report(report: dict) -> str:
    """Generate Markdown version of report."""
    eval_data = report.get("evaluation", {})
    score_data = eval_data.get("ux_health_score", {})

    lines = [
        "# UX Evaluation Report",
        "",
        f"**Evaluation ID**: {eval_data.get('evaluation_id', 'N/A')}",
        f"**Date**: {eval_data.get('timestamp', 'N/A')}",
        "",
        "## Executive Summary",
        "",
        eval_data.get("executive_summary", "No summary available."),
        "",
        "## UX Health Score",
        "",
        f"**Overall Score**: {score_data.get('overall', 'N/A')}/100",
        f"**Grade**: {score_data.get('grade', 'N/A')} ({score_data.get('status', 'N/A')})",
        "",
        "### Framework Breakdown",
        "",
        "| Framework | Score | Weight |",
        "|-----------|-------|--------|"
    ]

    breakdown = score_data.get("breakdown", {})
    for framework, data in breakdown.items():
        lines.append(f"| {framework.upper()} | {data.get('score', 'N/A')}% | {data.get('weight', 0) * 100}% |")

    # Critical findings
    critical = eval_data.get("critical_findings", [])
    if critical:
        lines.extend([
            "",
            "## Critical Findings (Must Fix)",
            ""
        ])
        for cf in critical:
            lines.append(f"- **{cf.get('finding_id')}**: {cf.get('title')} ({cf.get('framework')}: {cf.get('criterion')})")

    # Recommendations
    recommendations = eval_data.get("recommendations", [])
    if recommendations:
        lines.extend([
            "",
            "## Top Recommendations",
            ""
        ])
        for rec in recommendations[:5]:
            lines.append(f"{rec.get('priority_rank', '?')}. **{rec.get('recommendation')}** (Effort: {rec.get('effort')}, Impact: {rec.get('impact')})")

    # Findings summary
    summary = eval_data.get("findings_summary", {})
    lines.extend([
        "",
        "## Findings Summary",
        "",
        f"- Total Findings: {summary.get('total', 0)}",
        f"- Critical: {summary.get('by_severity', {}).get('critical', 0)}",
        f"- High: {summary.get('by_severity', {}).get('high', 0)}",
        f"- Medium: {summary.get('by_severity', {}).get('medium', 0)}",
        f"- Low: {summary.get('by_severity', {}).get('low', 0)}",
        "",
        "---",
        "*Generated by UX Evaluation Report Generator*"
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate UX evaluation report from framework findings"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input directory containing framework finding files OR single combined JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output report file"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown", "md"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--profile", "-p",
        choices=list(WEIGHTING_PROFILES.keys()),
        default="balanced",
        help="Weighting profile (default: balanced)"
    )
    parser.add_argument(
        "--artifacts",
        nargs="*",
        help="List of artifact IDs that were evaluated"
    )

    args = parser.parse_args()

    try:
        input_path = Path(args.input)

        if input_path.is_dir():
            framework_findings = load_findings_from_directory(args.input)
        else:
            with open(args.input, 'r') as f:
                framework_findings = json.load(f)

        if not framework_findings:
            print("Error: No findings found in input", file=sys.stderr)
            sys.exit(1)

        report = generate_evaluation_report(
            framework_findings,
            profile=args.profile,
            artifacts_evaluated=args.artifacts or []
        )

        # Format output
        if args.format in ["markdown", "md"]:
            output_content = format_markdown_report(report)
        else:
            output_content = json.dumps(report, indent=2)

        # Write output
        with open(args.output, 'w') as f:
            f.write(output_content)

        print(f"Report generated: {args.output}")
        print(f"UX Health Score: {report['evaluation']['ux_health_score'].get('overall', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
