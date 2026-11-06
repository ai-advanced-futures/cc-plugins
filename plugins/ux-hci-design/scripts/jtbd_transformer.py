#!/usr/bin/env python3
"""
JTBD Transformer for UX/HCI Design Plugin.

Transforms Jobs-to-be-Done (JTBD) opportunity analysis outputs into UX artifacts.
Bridges JTBD methodology with persona and journey map generation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class JTBDTransformer:
    """Transforms JTBD data into UX design artifacts."""

    # JTBD need type to UX need type mapping
    NEED_TYPE_MAP = {
        "functional": "functional",
        "emotional": "emotional",
        "social": "social",
        "consumption_chain": "experiential",
        "related": "informational"
    }

    # Universal job steps to journey stage mapping
    UNIVERSAL_JOB_STEPS = {
        "define": "Discovery",
        "locate": "Research",
        "prepare": "Setup",
        "confirm": "Validation",
        "execute": "Core Action",
        "monitor": "Review",
        "modify": "Iteration",
        "conclude": "Completion"
    }

    def __init__(self):
        """Initialize transformer."""
        self.warnings: List[str] = []

    def transform(
        self,
        jtbd_data: Dict[str, Any],
        research_findings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform JTBD data into UX artifacts.

        Args:
            jtbd_data: JTBD opportunity analysis data
            research_findings: Optional research for enrichment

        Returns:
            Dict containing personas, journey_maps, requirements
        """
        self.warnings = []

        # Validate input
        self._validate_jtbd_input(jtbd_data)

        # Transform to personas
        personas = self._transform_to_personas(jtbd_data, research_findings)

        # Transform to journey maps
        journey_maps = self._transform_to_journey_maps(jtbd_data, personas, research_findings)

        # Extract prioritized requirements
        requirements = self._extract_requirements(jtbd_data)

        # Check for accessibility relevance
        accessibility_flags = self._check_accessibility_relevance(jtbd_data)

        result = {
            "personas": personas,
            "journey_maps": journey_maps,
            "requirements": requirements,
            "accessibility_flags": accessibility_flags,
            "transformation_metadata": {
                "source": "jtbd_analysis",
                "transformed_at": datetime.utcnow().isoformat() + "Z",
                "enriched_with_research": research_findings is not None,
                "warnings": self.warnings
            }
        }

        return result

    def _validate_jtbd_input(self, jtbd_data: Dict[str, Any]) -> None:
        """Validate JTBD input data structure."""
        if "job_statement" not in jtbd_data:
            self.warnings.append("Missing job_statement - using defaults")

        if "customer_needs" not in jtbd_data:
            self.warnings.append("Missing customer_needs - limited transformation")

    def _transform_to_personas(
        self,
        jtbd_data: Dict[str, Any],
        research: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform JTBD segments to personas."""
        personas = []
        segments = jtbd_data.get("market_segments", [])

        if not segments:
            # Create single persona from job statement
            segments = [{
                "segment_id": "S0",
                "segment_name": "Primary User",
                "characteristics": [],
                "unmet_needs": []
            }]

        job_statement = jtbd_data.get("job_statement", {})
        customer_needs = jtbd_data.get("customer_needs", [])

        for segment in segments:
            persona = self._create_persona_from_segment(
                segment, job_statement, customer_needs, research
            )
            personas.append(persona)

        return personas

    def _create_persona_from_segment(
        self,
        segment: Dict[str, Any],
        job_statement: Dict[str, Any],
        customer_needs: List[Dict],
        research: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a persona from a market segment."""
        segment_name = segment.get("segment_name", "User")

        # Transform job statement to primary goal
        primary_goal = self._job_to_goal(job_statement)

        # Transform customer needs
        needs = []
        pain_points = []

        for need in customer_needs:
            transformed_need = self._transform_need(need)
            needs.append(transformed_need)

            # High opportunity needs become pain points
            if need.get("opportunity_score", 0) >= 10:
                pain_point = self._need_to_pain_point(need, job_statement)
                pain_points.append(pain_point)

        # Filter needs relevant to this segment
        # unmet_needs contains need IDs (e.g., "N1", "N2"), not descriptions
        segment_need_ids = segment.get("unmet_needs", [])
        if segment_need_ids:
            # Build mapping from customer_needs to filter by need_id
            need_statements_by_id = {
                n.get("need_id"): n.get("need_statement", "")
                for n in customer_needs
            }
            relevant_statements = {
                need_statements_by_id.get(nid)
                for nid in segment_need_ids
                if need_statements_by_id.get(nid)
            }
            needs = [n for n in needs if n.get("description") in relevant_statements]

        # Build persona
        persona = {
            "schema_version": "1.0",
            "persona": {
                "name": self._generate_persona_name(segment_name),
                "tagline": segment.get("description", f"User from {segment_name} segment")[:200],
                "demographics": self._infer_demographics(segment),
                "goals": [primary_goal] if primary_goal else [],
                "pain_points": pain_points[:15],
                "behaviors": self._infer_behaviors(segment),
                "needs": needs[:15],
                "context": self._default_context(),
                "quote": self._generate_quote(job_statement),
                "accessibility_needs": [],
                "ai_interaction_preferences": self._default_ai_preferences(),
                "jtbd_integration": {
                    "primary_job": job_statement.get("full_statement", ""),
                    "job_context": job_statement.get("situation", ""),
                    "success_outcomes": [
                        n.get("need_statement", "")
                        for n in customer_needs[:5]
                        if n.get("need_type") == "functional"
                    ],
                    "switch_triggers": []
                },
                "segments": [segment_name],
                "related_personas": []
            },
            "metadata": {
                "created_date": datetime.utcnow().isoformat() + "Z",
                "created_by": "UX/HCI Design Plugin - JTBD Transformer",
                "research_basis": "JTBD opportunity analysis",
                "confidence_level": "hypothesis",
                "version": "1.0",
                "tags": ["jtbd-derived", "proto-persona"]
            }
        }

        # Enrich with research if available
        if research:
            persona = self._enrich_persona(persona, research, segment)

        return persona

    def _job_to_goal(self, job_statement: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform JTBD job statement to persona goal."""
        if not job_statement:
            return None

        return {
            "description": job_statement.get("outcome", "Accomplish their goals"),
            "priority": "critical",
            "context": job_statement.get("situation", ""),
            "success_criteria": f"Successfully {job_statement.get('motivation', 'complete task')}"
        }

    def _transform_need(self, need: Dict[str, Any]) -> Dict[str, Any]:
        """Transform JTBD customer need to persona need."""
        opp_score = need.get("opportunity_score", 0)

        return {
            "description": need.get("need_statement", ""),
            "type": self.NEED_TYPE_MAP.get(need.get("need_type", "functional"), "functional"),
            "priority": self._score_to_priority(opp_score),
            "unmet": need.get("satisfaction", 5) < 5
        }

    def _need_to_pain_point(
        self,
        need: Dict[str, Any],
        job_statement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform high-opportunity need to pain point."""
        opp_score = need.get("opportunity_score", 0)

        return {
            "description": need.get("need_statement", ""),
            "severity": self._score_to_severity(opp_score),
            "frequency": "frequently" if opp_score >= 15 else "occasionally",
            "context": job_statement.get("situation", ""),
            "current_workaround": "Unknown - requires research validation"
        }

    def _transform_to_journey_maps(
        self,
        jtbd_data: Dict[str, Any],
        personas: List[Dict],
        research: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform JTBD job steps to journey maps."""
        journey_maps = []
        job_steps = jtbd_data.get("job_steps", [])
        job_statement = jtbd_data.get("job_statement", {})
        customer_needs = jtbd_data.get("customer_needs", [])

        for persona in personas:
            persona_data = persona.get("persona", persona)
            persona_name = persona_data.get("name", "User")

            # Build stages from job steps
            if job_steps:
                stages = self._job_steps_to_stages(job_steps, customer_needs)
            else:
                stages = self._default_stages()

            journey_map = {
                "schema_version": "1.0",
                "journey_map": {
                    "title": f"{persona_name} - {job_statement.get('outcome', 'Journey')}",
                    "description": job_statement.get("full_statement", ""),
                    "persona": {
                        "name": persona_name,
                        "reference": ""
                    },
                    "scenario": {
                        "description": job_statement.get("full_statement", "Completing the job"),
                        "goal": job_statement.get("outcome", ""),
                        "context": job_statement.get("situation", ""),
                        "triggers": []
                    },
                    "journey_type": "current_state",
                    "time_scope": self._estimate_total_duration(job_steps),
                    "stages": stages,
                    "overall_sentiment": "mixed",
                    "key_insights": self._generate_insights(stages, customer_needs),
                    "recommendations": self._generate_recommendations(customer_needs)
                },
                "metadata": {
                    "created_date": datetime.utcnow().isoformat() + "Z",
                    "created_by": "UX/HCI Design Plugin - JTBD Transformer",
                    "research_basis": f"JTBD analysis ({len(job_steps)} job steps)",
                    "validation_status": "hypothesis",
                    "version": "1.0",
                    "tags": ["jtbd-derived"]
                }
            }

            journey_maps.append(journey_map)

        return journey_maps

    def _job_steps_to_stages(
        self,
        job_steps: List[Dict],
        customer_needs: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Convert JTBD job steps to journey stages."""
        stages = []

        for step in job_steps:
            step_name = step.get("step_name", "Step")
            step_number = step.get("step_number", len(stages) + 1)

            # Find relevant needs for this step
            relevant_needs = self._find_needs_for_step(step, customer_needs)
            pain_points = [
                {
                    "description": n.get("need_statement", ""),
                    "severity": self._score_to_severity(n.get("opportunity_score", 0)),
                    "impact": "",
                    "root_cause": ""
                }
                for n in relevant_needs
                if n.get("opportunity_score", 0) >= 10
            ]

            stage = {
                "stage_name": self._map_step_to_stage_name(step_name),
                "stage_number": step_number,
                "duration": self._estimate_step_duration(step),
                "description": step.get("description", ""),
                "user_goals": [f"Successfully {step_name.lower()}"],
                "user_actions": self._extract_actions(step),
                "touchpoints": [
                    {
                        "name": "Product Interface",
                        "type": "digital",
                        "channel": "application",
                        "description": f"User interacts to {step_name.lower()}",
                        "current_experience": "adequate"
                    }
                ],
                "emotions": self._infer_emotions(step_number, len(job_steps)),
                "thoughts": [f"How do I {step_name.lower()}?"],
                "pain_points": pain_points[:3],
                "delights": [],
                "opportunities": [
                    {
                        "description": n.get("need_statement", ""),
                        "priority": self._score_to_priority(n.get("opportunity_score", 0)),
                        "expected_impact": "moderate",
                        "effort_estimate": "medium"
                    }
                    for n in relevant_needs[:2]
                ],
                "experience_score": self._calculate_stage_score(relevant_needs)
            }

            stages.append(stage)

        return stages

    def _find_needs_for_step(
        self,
        step: Dict,
        needs: List[Dict]
    ) -> List[Dict]:
        """Find customer needs relevant to a job step."""
        step_text = (step.get("step_name", "") + " " + step.get("description", "")).lower()
        relevant = []

        for need in needs:
            need_text = need.get("need_statement", "").lower()
            # Simple keyword matching
            if any(word in need_text for word in step_text.split() if len(word) > 3):
                relevant.append(need)

        return relevant

    def _map_step_to_stage_name(self, step_name: str) -> str:
        """Map job step name to journey stage name."""
        step_lower = step_name.lower()
        for keyword, stage_name in self.UNIVERSAL_JOB_STEPS.items():
            if keyword in step_lower:
                return stage_name
        return step_name  # Return original if no match

    def _extract_requirements(self, jtbd_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract prioritized requirements from JTBD data."""
        requirements = []
        customer_needs = jtbd_data.get("customer_needs", [])

        for need in customer_needs:
            opp_score = need.get("opportunity_score", 0)
            if opp_score >= 10:  # Only include opportunities
                requirements.append({
                    "requirement_id": f"REQ-{need.get('need_id', len(requirements))}",
                    "description": need.get("need_statement", ""),
                    "priority": self._score_to_priority(opp_score),
                    "source": "jtbd_customer_need",
                    "opportunity_score": opp_score,
                    "importance": need.get("importance", 0),
                    "satisfaction": need.get("satisfaction", 0)
                })

        # Sort by opportunity score descending
        requirements.sort(key=lambda x: x["opportunity_score"], reverse=True)

        return requirements

    def _check_accessibility_relevance(self, jtbd_data: Dict[str, Any]) -> Dict[str, List]:
        """Check for accessibility-relevant JTBD elements."""
        a11y_keywords = [
            "vision", "visual", "see", "blind", "color",
            "hearing", "deaf", "audio", "sound",
            "motor", "mobility", "hand", "click", "touch",
            "cognitive", "memory", "attention", "learn",
            "screen reader", "keyboard", "voice",
            "disability", "accessible", "inclusive"
        ]

        flags = {
            "segments": [],
            "needs": [],
            "steps": []
        }

        # Check market segments
        for segment in jtbd_data.get("market_segments", []):
            segment_text = str(segment).lower()
            if any(kw in segment_text for kw in a11y_keywords):
                flags["segments"].append(segment.get("segment_id", ""))

        # Check customer needs
        for need in jtbd_data.get("customer_needs", []):
            need_text = need.get("need_statement", "").lower()
            if any(kw in need_text for kw in a11y_keywords):
                flags["needs"].append(need.get("need_id", ""))

        # Check job steps
        for step in jtbd_data.get("job_steps", []):
            step_text = str(step).lower()
            if any(kw in step_text for kw in a11y_keywords):
                flags["steps"].append(step.get("step_number", ""))

        return flags

    # Helper methods

    def _generate_persona_name(self, segment_name: str) -> str:
        """Generate persona name from segment."""
        # Create alliterative name
        first_letter = segment_name[0].lower() if segment_name else "p"
        names = {
            "a": "Ambitious Alex", "b": "Busy Blake", "c": "Careful Casey",
            "d": "Decisive Dana", "e": "Efficient Ellis", "f": "Focused Frankie",
            "g": "Goal-Oriented Gray", "h": "Hardworking Harper",
            "i": "Innovative Indigo", "j": "Just-Get-It-Done Jordan",
            "k": "Knowledge-Seeking Kelly", "l": "Logical Lee",
            "m": "Methodical Morgan", "n": "No-Nonsense Nico",
            "o": "Organized Oakley", "p": "Pragmatic Parker",
            "q": "Quality-Focused Quinn", "r": "Results-Driven Riley",
            "s": "Strategic Sam", "t": "Task-Focused Taylor",
            "u": "User-Centric Uma", "v": "Value-Seeking Val",
            "w": "Work-Smart Wesley", "x": "Expert Xen",
            "y": "Yes-We-Can Yuri", "z": "Zero-Waste Zion"
        }
        return names.get(first_letter, f"Proto-{segment_name.replace(' ', '')}")

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
        """Convert opportunity score to priority."""
        if score >= 15:
            return "must_have"
        elif score >= 10:
            return "should_have"
        else:
            return "nice_to_have"

    def _infer_demographics(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """Infer demographics from segment."""
        chars = " ".join(segment.get("characteristics", [])).lower()
        tech_level = "intermediate"
        if "technical" in chars or "expert" in chars or "developer" in chars:
            tech_level = "expert"
        elif "novice" in chars or "beginner" in chars:
            tech_level = "novice"

        return {
            "occupation": segment.get("segment_name", "Professional"),
            "tech_proficiency": tech_level
        }

    def _infer_behaviors(self, segment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Infer behaviors from segment characteristics."""
        behaviors = []
        for char in segment.get("characteristics", [])[:5]:
            behaviors.append({
                "description": char,
                "category": "usage_pattern",
                "frequency": "daily",
                "triggers": [],
                "impact": ""
            })
        if not behaviors:
            behaviors.append({
                "description": "Uses product for primary job tasks",
                "category": "usage_pattern",
                "frequency": "daily",
                "triggers": [],
                "impact": ""
            })
        return behaviors

    def _default_context(self) -> Dict[str, Any]:
        """Return default context."""
        return {
            "environment": "To be determined",
            "devices": ["laptop", "smartphone"],
            "time_constraints": "Unknown",
            "cognitive_constraints": "Unknown",
            "social_context": "Unknown"
        }

    def _default_ai_preferences(self) -> Dict[str, Any]:
        """Return default AI preferences."""
        return {
            "comfort_level": "neutral",
            "trust_level": "moderate_trust",
            "transparency_needs": "moderate",
            "control_preferences": "balanced",
            "concerns": []
        }

    def _generate_quote(self, job_statement: Dict[str, Any]) -> str:
        """Generate representative quote from job statement."""
        motivation = job_statement.get("motivation", "get things done")
        return f'"I need to {motivation}"'

    def _enrich_persona(
        self,
        persona: Dict[str, Any],
        research: Dict[str, Any],
        segment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich persona with research findings."""
        # Add research-based pain points
        for pp in research.get("pain_points", []):
            if len(persona["persona"]["pain_points"]) < 15:
                persona["persona"]["pain_points"].append({
                    "description": pp.get("description", ""),
                    "severity": pp.get("severity", "medium"),
                    "frequency": pp.get("frequency", "occasionally"),
                    "context": pp.get("root_cause", ""),
                    "current_workaround": pp.get("current_workaround", "")
                })

        # Update confidence level
        persona["metadata"]["confidence_level"] = "low"
        persona["metadata"]["research_basis"] = "JTBD analysis + user research"

        return persona

    def _default_stages(self) -> List[Dict[str, Any]]:
        """Return default journey stages."""
        defaults = ["Discovery", "Research", "Decision", "Setup", "First Use"]
        return [
            {
                "stage_name": name,
                "stage_number": i + 1,
                "description": f"User {name.lower()} stage",
                "user_goals": [f"Complete {name.lower()}"],
                "touchpoints": [
                    {"name": "Product", "type": "digital", "channel": "app", "current_experience": "adequate"}
                ],
                "emotions": [{"emotion": "neutral", "valence": "neutral", "intensity": "moderate"}],
                "thoughts": [],
                "pain_points": [],
                "opportunities": [],
                "experience_score": {"score": 5, "scale": "1-10", "rationale": "Default baseline"}
            }
            for i, name in enumerate(defaults)
        ]

    def _estimate_step_duration(self, step: Dict) -> str:
        """Estimate duration for a step."""
        desc = step.get("description", "").lower()
        if "quick" in desc or "simple" in desc:
            return "1-2 minutes"
        elif "complex" in desc or "detailed" in desc:
            return "10-15 minutes"
        return "5 minutes"

    def _estimate_total_duration(self, steps: List[Dict]) -> str:
        """Estimate total journey duration."""
        count = len(steps) if steps else 5
        if count <= 3:
            return "15 minutes"
        elif count <= 6:
            return "30 minutes"
        else:
            return "1 hour"

    def _extract_actions(self, step: Dict) -> List[Dict]:
        """Extract actions from step."""
        return [
            {
                "action": step.get("description", step.get("step_name", "Action")),
                "channel": "application"
            }
        ]

    def _infer_emotions(self, step_number: int, total_steps: int) -> List[Dict]:
        """Infer emotions based on position in journey."""
        progress = step_number / total_steps if total_steps else 0.5
        if progress < 0.3:
            return [{"emotion": "curious", "valence": "positive", "intensity": "moderate"}]
        elif progress < 0.7:
            return [{"emotion": "focused", "valence": "neutral", "intensity": "moderate"}]
        else:
            return [{"emotion": "accomplished", "valence": "positive", "intensity": "moderate"}]

    def _calculate_stage_score(self, relevant_needs: List[Dict]) -> Dict[str, Any]:
        """Calculate experience score based on relevant needs."""
        if not relevant_needs:
            return {"score": 5, "scale": "1-10", "rationale": "No relevant needs found"}

        # Lower scores for high opportunity (unmet) needs
        avg_opp = sum(n.get("opportunity_score", 5) for n in relevant_needs) / len(relevant_needs)
        score = max(1, min(10, 10 - (avg_opp - 10)))  # 10=opportunity threshold

        return {
            "score": round(score),
            "scale": "1-10",
            "rationale": f"Based on {len(relevant_needs)} relevant needs (avg opp score: {avg_opp:.1f})"
        }

    def _generate_insights(
        self,
        stages: List[Dict],
        needs: List[Dict]
    ) -> List[str]:
        """Generate insights from stages and needs."""
        insights = []

        # Count high-opportunity needs
        high_opp = [n for n in needs if n.get("opportunity_score", 0) >= 12]
        if high_opp:
            insights.append(f"{len(high_opp)} high-opportunity needs identified for design focus")

        # Find lowest scoring stages
        if stages:
            scores = [(s.get("stage_name"), s.get("experience_score", {}).get("score", 5)) for s in stages]
            min_stage = min(scores, key=lambda x: x[1])
            if min_stage[1] < 5:
                insights.append(f"'{min_stage[0]}' stage needs attention (score: {min_stage[1]}/10)")

        if not insights:
            insights.append("JTBD analysis provides opportunity-driven design priorities")

        return insights

    def _generate_recommendations(self, needs: List[Dict]) -> List[Dict]:
        """Generate recommendations from needs analysis."""
        recommendations = []

        # Top 3 opportunities
        sorted_needs = sorted(needs, key=lambda x: x.get("opportunity_score", 0), reverse=True)

        for need in sorted_needs[:3]:
            if need.get("opportunity_score", 0) >= 10:
                recommendations.append({
                    "recommendation": f"Address: {need.get('need_statement', '')[:80]}",
                    "priority": self._score_to_severity(need.get("opportunity_score", 0)),
                    "stages_affected": [],
                    "expected_impact": "Based on high opportunity score"
                })

        return recommendations


def main():
    """CLI interface for JTBD transformation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Transform JTBD data into UX artifacts"
    )
    parser.add_argument(
        "jtbd_file",
        type=Path,
        help="Path to JTBD analysis JSON file"
    )
    parser.add_argument(
        "--research",
        type=Path,
        help="Optional path to research_findings.json for enrichment"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path"
    )
    parser.add_argument(
        "--format",
        choices=["json", "summary"],
        default="json",
        help="Output format"
    )

    args = parser.parse_args()

    # Load JTBD data
    with open(args.jtbd_file, 'r', encoding='utf-8') as f:
        jtbd_data = json.load(f)

    # Load research if provided
    research = None
    if args.research:
        with open(args.research, 'r', encoding='utf-8') as f:
            research = json.load(f)

    # Transform
    transformer = JTBDTransformer()
    result = transformer.transform(jtbd_data, research)

    # Output
    if args.format == "summary":
        print("=== JTBD Transformation Summary ===")
        print(f"Personas generated: {len(result['personas'])}")
        print(f"Journey maps generated: {len(result['journey_maps'])}")
        print(f"Requirements extracted: {len(result['requirements'])}")
        print(f"Accessibility flags: {result['accessibility_flags']}")
        if result['transformation_metadata']['warnings']:
            print(f"Warnings: {result['transformation_metadata']['warnings']}")
    else:
        output = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Output written to {args.output}")
        else:
            print(output)


if __name__ == "__main__":
    main()
