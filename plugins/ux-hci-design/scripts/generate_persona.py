#!/usr/bin/env python3
"""
Persona Generation Helper for UX/HCI Design Plugin.

Generates personas from research findings and/or JTBD data.
Validates output against persona-schema.json.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PersonaGenerator:
    """Generates UX personas from research findings and JTBD data."""

    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize generator with optional schema path."""
        self.schema_path = schema_path or (
            Path(__file__).parent.parent / "schemas" / "outputs" / "persona-schema.json"
        )
        self._load_schema()

    def _load_schema(self) -> None:
        """Load the persona schema for validation."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            self.schema = None
            print(f"Warning: Schema not found at {self.schema_path}")

    def generate_from_research(
        self,
        research_findings: Dict[str, Any],
        segment_index: int = 0
    ) -> Dict[str, Any]:
        """
        Generate persona from research findings.

        Args:
            research_findings: Structured research findings from EMPATHIZE phase
            segment_index: Which user segment to generate persona for

        Returns:
            Persona object validated against schema
        """
        segments = research_findings.get("user_segments", [])
        if not segments:
            raise ValueError("No user segments found in research findings")

        if segment_index >= len(segments):
            raise IndexError(f"Segment index {segment_index} out of range")

        segment = segments[segment_index]
        findings = research_findings.get("key_findings", [])
        pain_points = research_findings.get("pain_points", [])
        accessibility = research_findings.get("accessibility_findings", [])
        ai_hci = research_findings.get("ai_interaction_findings", [])

        # Generate persona name from segment
        name = self._generate_name(segment)

        # Extract goals from findings
        goals = self._extract_goals(findings, segment)

        # Transform pain points
        transformed_pain_points = self._transform_pain_points(pain_points, segment)

        # Extract behaviors
        behaviors = self._extract_behaviors(findings, segment)

        # Extract needs
        needs = self._extract_needs(findings, segment)

        # Build persona
        persona = {
            "schema_version": "1.0",
            "persona": {
                "name": name,
                "tagline": segment.get("name", "User persona"),
                "demographics": self._infer_demographics(segment),
                "goals": goals,
                "pain_points": transformed_pain_points,
                "behaviors": behaviors,
                "needs": needs,
                "context": self._infer_context(segment, findings),
                "quote": self._generate_quote(segment, pain_points),
                "accessibility_needs": self._transform_accessibility(accessibility),
                "ai_interaction_preferences": self._transform_ai_preferences(ai_hci),
                "segments": [segment.get("name", "Primary")],
                "related_personas": []
            },
            "metadata": {
                "created_date": datetime.utcnow().isoformat() + "Z",
                "created_by": "UX/HCI Design Plugin - Persona Generator",
                "research_basis": research_findings.get("research_summary", {}).get("methodology", "User research"),
                "confidence_level": self._determine_confidence(research_findings),
                "version": "1.0",
                "tags": self._generate_tags(segment)
            }
        }

        return persona

    def generate_from_jtbd(
        self,
        jtbd_data: Dict[str, Any],
        segment_index: int = 0
    ) -> Dict[str, Any]:
        """
        Generate proto-persona from JTBD data.

        Args:
            jtbd_data: JTBD opportunity analysis data
            segment_index: Which market segment to use

        Returns:
            Proto-persona object (requires research enrichment)
        """
        segments = jtbd_data.get("market_segments", [])
        if not segments:
            # Create default segment from job statement
            segment = {
                "segment_name": "Primary User",
                "characteristics": []
            }
        else:
            segment = segments[segment_index] if segment_index < len(segments) else segments[0]

        job_statement = jtbd_data.get("job_statement", {})
        customer_needs = jtbd_data.get("customer_needs", [])

        # Generate name
        name = f"Proto-{segment.get('segment_name', 'User').replace(' ', '')}"

        # Transform job statement to goal
        primary_goal = {
            "description": job_statement.get("outcome", "Accomplish their goals"),
            "priority": "critical",
            "context": job_statement.get("situation", ""),
            "success_criteria": f"Successfully {job_statement.get('motivation', 'completes task')}"
        }

        # Transform customer needs to persona needs
        needs = []
        pain_points = []

        for need in customer_needs:
            opp_score = need.get("opportunity_score", 0)

            # High opportunity = unmet need = pain point
            if opp_score >= 10:
                pain_points.append({
                    "description": need.get("need_statement", ""),
                    "severity": self._score_to_severity(opp_score),
                    "frequency": "frequently" if opp_score >= 15 else "occasionally",
                    "context": job_statement.get("situation", ""),
                    "current_workaround": "Unknown - requires research"
                })

            needs.append({
                "description": need.get("need_statement", ""),
                "type": self._map_need_type(need.get("need_type", "functional")),
                "priority": self._score_to_priority(opp_score),
                "unmet": need.get("satisfaction", 5) < 5
            })

        persona = {
            "schema_version": "1.0",
            "persona": {
                "name": name,
                "tagline": segment.get("description", job_statement.get("full_statement", ""))[:200],
                "demographics": self._infer_demographics_from_segment(segment),
                "goals": [primary_goal],
                "pain_points": pain_points[:10],  # Limit to schema max
                "behaviors": self._infer_behaviors_from_segment(segment),
                "needs": needs[:15],  # Limit to schema max
                "context": {
                    "environment": "To be determined through research",
                    "devices": ["laptop", "smartphone"],
                    "time_constraints": "Unknown",
                    "cognitive_constraints": "Unknown",
                    "social_context": "Unknown"
                },
                "quote": f'"I need to {job_statement.get("motivation", "get things done")}"',
                "accessibility_needs": [],
                "ai_interaction_preferences": {
                    "comfort_level": "neutral",
                    "trust_level": "moderate_trust",
                    "transparency_needs": "moderate",
                    "control_preferences": "balanced",
                    "concerns": []
                },
                "jtbd_integration": {
                    "primary_job": job_statement.get("full_statement", ""),
                    "job_context": job_statement.get("situation", ""),
                    "success_outcomes": [
                        need.get("need_statement", "")
                        for need in customer_needs[:5]
                        if need.get("need_type") == "functional"
                    ],
                    "switch_triggers": []
                },
                "segments": [segment.get("segment_name", "Primary")],
                "related_personas": []
            },
            "metadata": {
                "created_date": datetime.utcnow().isoformat() + "Z",
                "created_by": "UX/HCI Design Plugin - JTBD Transformer",
                "research_basis": "JTBD opportunity analysis - requires research validation",
                "confidence_level": "hypothesis",
                "version": "1.0",
                "tags": ["proto-persona", "jtbd-derived", "needs-research"]
            }
        }

        return persona

    def _generate_name(self, segment: Dict[str, Any]) -> str:
        """Generate a descriptive persona name."""
        base_name = segment.get("name", "User")
        # Add alliterative first name
        first_names = {
            "a": "Alex", "b": "Blake", "c": "Casey", "d": "Dana",
            "e": "Ellis", "f": "Frankie", "g": "Gray", "h": "Harper",
            "i": "Indigo", "j": "Jordan", "k": "Kelly", "l": "Lee",
            "m": "Morgan", "n": "Nico", "o": "Oakley", "p": "Parker",
            "q": "Quinn", "r": "Riley", "s": "Sam", "t": "Taylor",
            "u": "Uma", "v": "Val", "w": "Wesley", "x": "Xen",
            "y": "Yuri", "z": "Zion"
        }
        first_letter = base_name[0].lower() if base_name else "p"
        first_name = first_names.get(first_letter, "Pat")
        return f"{base_name} {first_name}"

    def _extract_goals(
        self,
        findings: List[Dict],
        segment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract goals from research findings."""
        goals = []
        for finding in findings:
            if finding.get("category") == "goal":
                goals.append({
                    "description": finding.get("description", "")[:200],
                    "priority": self._finding_to_priority(finding),
                    "context": finding.get("context", ""),
                    "success_criteria": ""
                })
        # Ensure at least one goal
        if not goals:
            goals.append({
                "description": "Accomplish primary task efficiently",
                "priority": "high",
                "context": "Daily workflow",
                "success_criteria": "Task completed successfully"
            })
        return goals[:10]  # Schema limit

    def _transform_pain_points(
        self,
        pain_points: List[Dict],
        segment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Transform pain points to persona format."""
        transformed = []
        segment_id = segment.get("segment_id")

        for pp in pain_points:
            # Filter by segment if specified
            if segment_id and segment_id not in pp.get("affected_segments", [segment_id]):
                continue

            transformed.append({
                "description": pp.get("description", "")[:200],
                "severity": pp.get("severity", "medium"),
                "frequency": pp.get("frequency", "occasionally"),
                "context": pp.get("root_cause", ""),
                "current_workaround": pp.get("current_workaround", "")
            })

        # Ensure at least one pain point
        if not transformed:
            transformed.append({
                "description": "Difficulty completing tasks efficiently",
                "severity": "medium",
                "frequency": "occasionally",
                "context": "Regular usage",
                "current_workaround": "Manual workarounds"
            })

        return transformed[:15]  # Schema limit

    def _extract_behaviors(
        self,
        findings: List[Dict],
        segment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract behaviors from research findings."""
        behaviors = []
        for finding in findings:
            if finding.get("category") == "behavior":
                behaviors.append({
                    "description": finding.get("description", "")[:200],
                    "category": "usage_pattern",
                    "frequency": "daily",
                    "triggers": [],
                    "impact": ""
                })
        # Ensure at least one behavior
        if not behaviors:
            behaviors.append({
                "description": "Uses product regularly for core tasks",
                "category": "usage_pattern",
                "frequency": "daily",
                "triggers": ["Work requirements"],
                "impact": "Core usage pattern"
            })
        return behaviors[:20]  # Schema limit

    def _extract_needs(
        self,
        findings: List[Dict],
        segment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract needs from research findings."""
        needs = []
        for finding in findings:
            if finding.get("category") == "need":
                needs.append({
                    "description": finding.get("description", "")[:200],
                    "type": "functional",
                    "priority": self._finding_to_need_priority(finding),
                    "unmet": True
                })
        # Ensure at least one need
        if not needs:
            needs.append({
                "description": "Efficient task completion",
                "type": "functional",
                "priority": "must_have",
                "unmet": False
            })
        return needs[:15]  # Schema limit

    def _infer_demographics(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Infer demographics from segment data."""
        return {
            "age_range": "25-45",
            "location": "Urban",
            "occupation": segment.get("name", "Professional"),
            "education_level": "bachelors",
            "tech_proficiency": "intermediate"
        }

    def _infer_demographics_from_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Infer demographics from JTBD segment."""
        characteristics = segment.get("characteristics", [])
        tech_level = "intermediate"
        for char in characteristics:
            if "technical" in char.lower() or "expert" in char.lower():
                tech_level = "expert"
            elif "novice" in char.lower():
                tech_level = "novice"

        return {
            "age_range": "25-45",
            "location": "Urban",
            "occupation": segment.get("segment_name", "Professional"),
            "tech_proficiency": tech_level
        }

    def _infer_behaviors_from_segment(self, segment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Infer behaviors from JTBD segment characteristics."""
        behaviors = []
        for char in segment.get("characteristics", [])[:5]:
            behaviors.append({
                "description": char,
                "category": "usage_pattern",
                "frequency": "daily",
                "triggers": [],
                "impact": "Characteristic behavior"
            })
        if not behaviors:
            behaviors.append({
                "description": "Uses product for primary job tasks",
                "category": "usage_pattern",
                "frequency": "daily",
                "triggers": ["Work requirements"],
                "impact": "Core behavior"
            })
        return behaviors

    def _infer_context(
        self,
        segment: Dict[str, Any],
        findings: List[Dict]
    ) -> Dict[str, Any]:
        """Infer context from segment and findings."""
        return {
            "environment": "Office and home hybrid",
            "devices": ["laptop", "smartphone"],
            "time_constraints": "Moderate time pressure",
            "cognitive_constraints": "Variable attention availability",
            "social_context": "Works with team"
        }

    def _generate_quote(
        self,
        segment: Dict[str, Any],
        pain_points: List[Dict]
    ) -> str:
        """Generate representative quote."""
        if pain_points:
            pp = pain_points[0]
            return f'"I wish I could {pp.get("description", "do this more easily").lower()[:50]}..."'
        return '"I want things to work smoothly and efficiently."'

    def _transform_accessibility(
        self,
        accessibility_findings: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Transform accessibility findings to persona format."""
        needs = []
        for finding in accessibility_findings:
            needs.append({
                "category": finding.get("category", "situational"),
                "description": finding.get("description", ""),
                "severity": "moderate",
                "assistive_technology": []
            })
        return needs

    def _transform_ai_preferences(
        self,
        ai_findings: List[Dict]
    ) -> Dict[str, Any]:
        """Transform AI-HCI findings to persona format."""
        preferences = {
            "comfort_level": "neutral",
            "trust_level": "moderate_trust",
            "transparency_needs": "moderate",
            "control_preferences": "balanced",
            "concerns": []
        }

        for finding in ai_findings:
            if finding.get("category") == "trust":
                if "low" in finding.get("description", "").lower():
                    preferences["trust_level"] = "low_trust"
                elif "high" in finding.get("description", "").lower():
                    preferences["trust_level"] = "high_trust"

            if finding.get("concerns"):
                preferences["concerns"].extend(finding["concerns"])

        return preferences

    def _determine_confidence(self, research_findings: Dict[str, Any]) -> str:
        """Determine confidence level based on research quality."""
        summary = research_findings.get("research_summary", {})
        participant_count = summary.get("participants", {}).get("count", 0)

        if participant_count >= 15:
            return "high"
        elif participant_count >= 8:
            return "medium"
        elif participant_count >= 3:
            return "low"
        else:
            return "hypothesis"

    def _generate_tags(self, segment: Dict[str, Any]) -> List[str]:
        """Generate categorization tags."""
        tags = []
        name = segment.get("name", "").lower()
        if "enterprise" in name:
            tags.append("b2b")
        if "consumer" in name:
            tags.append("b2c")
        priority = segment.get("priority", "secondary")
        tags.append(priority)
        return tags

    def _finding_to_priority(self, finding: Dict[str, Any]) -> str:
        """Convert finding severity to goal priority."""
        severity = finding.get("severity", "medium")
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        return mapping.get(severity, "medium")

    def _finding_to_need_priority(self, finding: Dict[str, Any]) -> str:
        """Convert finding to need priority."""
        severity = finding.get("severity", "medium")
        if severity in ["critical", "high"]:
            return "must_have"
        elif severity == "medium":
            return "should_have"
        else:
            return "nice_to_have"

    def _score_to_severity(self, score: float) -> str:
        """Convert opportunity score to severity."""
        if score >= 15:
            return "critical"
        elif score >= 12:
            return "high"
        elif score >= 10:
            return "medium"
        else:
            return "low"

    def _score_to_priority(self, score: float) -> str:
        """Convert opportunity score to need priority."""
        if score >= 15:
            return "must_have"
        elif score >= 10:
            return "should_have"
        else:
            return "nice_to_have"

    def _map_need_type(self, jtbd_type: str) -> str:
        """Map JTBD need type to persona need type."""
        mapping = {
            "functional": "functional",
            "emotional": "emotional",
            "social": "social",
            "consumption_chain": "experiential"
        }
        return mapping.get(jtbd_type, "functional")


def main():
    """CLI interface for persona generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate personas from research findings or JTBD data"
    )
    parser.add_argument(
        "--research",
        type=Path,
        help="Path to research_findings.json"
    )
    parser.add_argument(
        "--jtbd",
        type=Path,
        help="Path to JTBD analysis JSON"
    )
    parser.add_argument(
        "--segment",
        type=int,
        default=0,
        help="Segment index to generate persona for"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path"
    )

    args = parser.parse_args()

    if not args.research and not args.jtbd:
        print("Error: Must provide either --research or --jtbd input")
        sys.exit(1)

    generator = PersonaGenerator()

    if args.research:
        with open(args.research, 'r', encoding='utf-8') as f:
            research = json.load(f)
        persona = generator.generate_from_research(research, args.segment)
    else:
        with open(args.jtbd, 'r', encoding='utf-8') as f:
            jtbd = json.load(f)
        persona = generator.generate_from_jtbd(jtbd, args.segment)

    output = json.dumps(persona, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Persona written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
