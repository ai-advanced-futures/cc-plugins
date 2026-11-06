#!/usr/bin/env python3
"""
Journey Map Generation Helper for UX/HCI Design Plugin.

Generates journey maps from research findings, personas, and/or JTBD data.
Outputs both JSON (validated against schema) and Mermaid diagram format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class JourneyMapGenerator:
    """Generates customer journey maps from various inputs."""

    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize generator with optional schema path."""
        self.schema_path = schema_path or (
            Path(__file__).parent.parent / "schemas" / "outputs" / "journey-map-schema.json"
        )
        self._load_schema()

    def _load_schema(self) -> None:
        """Load the journey map schema for validation."""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            self.schema = None
            print(f"Warning: Schema not found at {self.schema_path}")

    def generate(
        self,
        persona: Dict[str, Any],
        scenario: Dict[str, Any],
        research_findings: Optional[Dict[str, Any]] = None,
        jtbd_job_steps: Optional[List[Dict]] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Generate a journey map from inputs.

        Args:
            persona: Persona object
            scenario: Scenario definition with description, goal, context
            research_findings: Optional research findings for enrichment
            jtbd_job_steps: Optional JTBD job steps for stage mapping

        Returns:
            Tuple of (journey_map_json, mermaid_diagram)
        """
        # Extract persona info
        persona_data = persona.get("persona", persona)
        persona_name = persona_data.get("name", "User")
        persona_pain_points = persona_data.get("pain_points", [])

        # Build journey title
        title = f"{persona_name} - {scenario.get('goal', 'User Journey')}"

        # Determine stages
        if jtbd_job_steps:
            stages = self._stages_from_jtbd(jtbd_job_steps, persona_pain_points)
        else:
            stages = self._default_stages(scenario, persona_pain_points)

        # Enrich with research if available
        if research_findings:
            stages = self._enrich_with_research(stages, research_findings)

        # Calculate overall sentiment
        overall_sentiment = self._calculate_sentiment(stages)

        # Generate key insights
        key_insights = self._generate_insights(stages, persona_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(stages)

        # Build journey map object
        journey_map = {
            "schema_version": "1.0",
            "journey_map": {
                "title": title,
                "description": scenario.get("description", ""),
                "persona": {
                    "name": persona_name,
                    "reference": persona_data.get("id", "")
                },
                "scenario": {
                    "description": scenario.get("description", ""),
                    "goal": scenario.get("goal", ""),
                    "context": scenario.get("context", ""),
                    "triggers": scenario.get("triggers", [])
                },
                "journey_type": scenario.get("journey_type", "current_state"),
                "time_scope": scenario.get("time_scope", "30 minutes"),
                "stages": stages,
                "overall_sentiment": overall_sentiment,
                "key_insights": key_insights,
                "recommendations": recommendations
            },
            "metadata": {
                "created_date": datetime.utcnow().isoformat() + "Z",
                "created_by": "UX/HCI Design Plugin - Journey Map Generator",
                "research_basis": self._get_research_basis(research_findings, jtbd_job_steps),
                "validation_status": "hypothesis" if not research_findings else "partially_validated",
                "version": "1.0",
                "tags": self._generate_tags(scenario, persona_data)
            }
        }

        # Generate Mermaid diagram
        mermaid = self._generate_mermaid(journey_map["journey_map"])

        return journey_map, mermaid

    def _stages_from_jtbd(
        self,
        job_steps: List[Dict],
        pain_points: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate stages from JTBD job steps."""
        stages = []

        for i, step in enumerate(job_steps):
            stage = {
                "stage_name": step.get("step_name", f"Step {i+1}"),
                "stage_number": step.get("step_number", i + 1),
                "duration": self._estimate_duration(step),
                "description": step.get("description", ""),
                "user_goals": [f"Successfully {step.get('step_name', 'complete step').lower()}"],
                "user_actions": [],
                "touchpoints": [
                    {
                        "name": "Product Interface",
                        "type": "digital",
                        "channel": "web application",
                        "description": f"User interacts with system to {step.get('step_name', 'complete task').lower()}",
                        "current_experience": "adequate"
                    }
                ],
                "emotions": self._default_emotions(i, len(job_steps)),
                "thoughts": [f"How do I {step.get('step_name', 'do this').lower()}?"],
                "pain_points": self._match_pain_points(step, pain_points),
                "delights": [],
                "opportunities": [],
                "experience_score": {
                    "score": 5,
                    "scale": "1-10",
                    "rationale": "Baseline score pending research validation"
                }
            }
            stages.append(stage)

        return stages

    def _default_stages(
        self,
        scenario: Dict[str, Any],
        pain_points: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate default stages when no JTBD data available."""
        default_stage_names = [
            ("Discovery", "User becomes aware of the need"),
            ("Research", "User explores options"),
            ("Decision", "User chooses to proceed"),
            ("Onboarding", "User gets started"),
            ("First Use", "User completes initial task"),
            ("Regular Use", "User establishes patterns")
        ]

        stages = []
        for i, (name, desc) in enumerate(default_stage_names):
            stage = {
                "stage_name": name,
                "stage_number": i + 1,
                "description": desc,
                "user_goals": [f"Successfully complete {name.lower()}"],
                "touchpoints": [
                    {
                        "name": "Product",
                        "type": "digital",
                        "channel": "application",
                        "current_experience": "adequate"
                    }
                ],
                "emotions": self._default_emotions(i, len(default_stage_names)),
                "thoughts": [],
                "pain_points": [],
                "delights": [],
                "opportunities": [],
                "experience_score": {
                    "score": 5,
                    "scale": "1-10",
                    "rationale": "Default baseline"
                }
            }
            stages.append(stage)

        return stages

    def _enrich_with_research(
        self,
        stages: List[Dict],
        research: Dict[str, Any]
    ) -> List[Dict]:
        """Enrich stages with research findings."""
        findings = research.get("key_findings", [])
        pain_points = research.get("pain_points", [])

        for stage in stages:
            # Add relevant pain points
            for pp in pain_points:
                if self._is_relevant_to_stage(pp, stage):
                    stage["pain_points"].append({
                        "description": pp.get("description", ""),
                        "severity": pp.get("severity", "medium"),
                        "impact": pp.get("root_cause", ""),
                        "root_cause": pp.get("root_cause", "")
                    })

            # Add relevant findings as thoughts
            for finding in findings:
                if finding.get("category") == "behavior" and self._is_relevant_to_stage(finding, stage):
                    if finding.get("quotes"):
                        stage["thoughts"].extend(finding["quotes"][:2])

            # Recalculate experience score based on pain points
            if stage["pain_points"]:
                severity_scores = {"critical": 2, "high": 4, "medium": 6, "low": 8}
                avg_score = sum(
                    severity_scores.get(pp.get("severity", "medium"), 5)
                    for pp in stage["pain_points"]
                ) / len(stage["pain_points"])
                stage["experience_score"]["score"] = round(avg_score)
                stage["experience_score"]["rationale"] = f"Adjusted based on {len(stage['pain_points'])} pain points"

        return stages

    def _default_emotions(self, stage_index: int, total_stages: int) -> List[Dict]:
        """Generate default emotional journey."""
        # Typical emotional arc: optimistic start, challenges mid, satisfaction end
        if stage_index == 0:
            return [{"emotion": "curious", "valence": "positive", "intensity": "moderate"}]
        elif stage_index < total_stages * 0.3:
            return [{"emotion": "hopeful", "valence": "positive", "intensity": "low"}]
        elif stage_index < total_stages * 0.6:
            return [{"emotion": "focused", "valence": "neutral", "intensity": "moderate"}]
        elif stage_index < total_stages * 0.8:
            return [{"emotion": "determined", "valence": "neutral", "intensity": "moderate"}]
        else:
            return [{"emotion": "satisfied", "valence": "positive", "intensity": "moderate"}]

    def _match_pain_points(
        self,
        step: Dict,
        pain_points: List[Dict]
    ) -> List[Dict]:
        """Match pain points to a step based on description."""
        matched = []
        step_desc = step.get("description", "").lower()

        for pp in pain_points:
            pp_desc = pp.get("description", "").lower()
            # Simple keyword matching
            if any(word in pp_desc for word in step_desc.split() if len(word) > 4):
                matched.append({
                    "description": pp.get("description", ""),
                    "severity": pp.get("severity", "medium"),
                    "impact": "",
                    "root_cause": pp.get("current_workaround", "")
                })

        return matched[:3]  # Limit per stage

    def _is_relevant_to_stage(self, item: Dict, stage: Dict) -> bool:
        """Check if a finding/pain point is relevant to a stage."""
        item_text = str(item).lower()
        stage_name = stage.get("stage_name", "").lower()
        return stage_name in item_text or any(
            word in item_text
            for word in stage_name.split()
            if len(word) > 3
        )

    def _estimate_duration(self, step: Dict) -> str:
        """Estimate duration for a step."""
        desc = step.get("description", "").lower()
        if any(word in desc for word in ["quick", "simple", "easy"]):
            return "1-2 minutes"
        elif any(word in desc for word in ["complex", "detailed", "thorough"]):
            return "10-15 minutes"
        else:
            return "5 minutes"

    def _calculate_sentiment(self, stages: List[Dict]) -> str:
        """Calculate overall sentiment from stages."""
        scores = [s.get("experience_score", {}).get("score", 5) for s in stages]
        avg = sum(scores) / len(scores) if scores else 5

        if avg >= 8:
            return "very_positive"
        elif avg >= 6:
            return "positive"
        elif avg >= 5:
            return "mixed"
        elif avg >= 4:
            return "negative"
        else:
            return "very_negative"

    def _generate_insights(
        self,
        stages: List[Dict],
        persona: Dict[str, Any]
    ) -> List[str]:
        """Generate key insights from journey analysis."""
        insights = []

        # Analyze pain point distribution
        total_pain_points = sum(len(s.get("pain_points", [])) for s in stages)
        if total_pain_points > 0:
            worst_stage = max(stages, key=lambda s: len(s.get("pain_points", [])))
            insights.append(
                f"The {worst_stage.get('stage_name', 'journey')} stage has the most friction with "
                f"{len(worst_stage.get('pain_points', []))} identified pain points"
            )

        # Analyze emotional journey
        emotions = [e for s in stages for e in s.get("emotions", [])]
        negative_count = sum(1 for e in emotions if e.get("valence") == "negative")
        if negative_count > len(emotions) * 0.3:
            insights.append("Over 30% of emotional touchpoints are negative - significant opportunity for improvement")

        # Analyze scores
        scores = [s.get("experience_score", {}).get("score", 5) for s in stages]
        min_score = min(scores)
        if min_score < 4:
            low_stages = [s for s in stages if s.get("experience_score", {}).get("score", 5) < 4]
            insights.append(
                f"Critical friction at: {', '.join(s.get('stage_name', '') for s in low_stages)}"
            )

        # Add default insight if none generated
        if not insights:
            insights.append("Journey analysis reveals opportunities for optimization across multiple stages")

        return insights[:5]

    def _generate_recommendations(self, stages: List[Dict]) -> List[Dict]:
        """Generate recommendations based on journey analysis."""
        recommendations = []

        # Find stages with highest severity pain points
        for stage in stages:
            critical_pps = [pp for pp in stage.get("pain_points", []) if pp.get("severity") == "critical"]
            if critical_pps:
                recommendations.append({
                    "recommendation": f"Address critical pain points in {stage.get('stage_name', 'this stage')}",
                    "priority": "critical",
                    "stages_affected": [stage.get("stage_name", "")],
                    "expected_impact": "Significant reduction in user friction"
                })

        # Find low-scoring stages
        for stage in stages:
            score = stage.get("experience_score", {}).get("score", 5)
            if score < 5:
                recommendations.append({
                    "recommendation": f"Improve experience in {stage.get('stage_name', 'this stage')} (current score: {score}/10)",
                    "priority": "high",
                    "stages_affected": [stage.get("stage_name", "")],
                    "expected_impact": "Improved user satisfaction and completion rates"
                })

        # Add accessibility recommendation
        recommendations.append({
            "recommendation": "Conduct accessibility audit of all touchpoints",
            "priority": "high",
            "stages_affected": [s.get("stage_name", "") for s in stages],
            "expected_impact": "Ensure inclusive experience for all users"
        })

        return recommendations[:5]

    def _get_research_basis(
        self,
        research: Optional[Dict],
        jtbd: Optional[List]
    ) -> str:
        """Generate research basis string."""
        parts = []
        if research:
            summary = research.get("research_summary", {})
            parts.append(f"User research (n={summary.get('participants', {}).get('count', 'unknown')})")
        if jtbd:
            parts.append(f"JTBD analysis ({len(jtbd)} job steps)")
        return ", ".join(parts) if parts else "Generated from persona data"

    def _generate_tags(self, scenario: Dict, persona: Dict) -> List[str]:
        """Generate tags for the journey map."""
        tags = []
        jtype = scenario.get("journey_type", "current_state")
        tags.append(jtype.replace("_", "-"))

        if "ai" in str(persona).lower():
            tags.append("ai-heavy")
        if "accessibility" in str(persona).lower():
            tags.append("a11y-focus")

        return tags

    def _generate_mermaid(self, journey: Dict[str, Any]) -> str:
        """Generate Mermaid journey diagram."""
        lines = [
            "```mermaid",
            "journey",
            f"    title {journey.get('title', 'User Journey')}"
        ]

        for stage in journey.get("stages", []):
            lines.append(f"    section {stage.get('stage_name', 'Stage')}")

            # Get experience score
            score = stage.get("experience_score", {}).get("score", 5)

            # Add touchpoints as actions
            for tp in stage.get("touchpoints", [])[:2]:
                tp_name = tp.get("name", "Interaction")
                lines.append(f"      {tp_name}: {score}: User")

            # If no touchpoints, add stage action
            if not stage.get("touchpoints"):
                lines.append(f"      {stage.get('stage_name', 'Action')}: {score}: User")

        lines.append("```")
        return "\n".join(lines)


def main():
    """CLI interface for journey map generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate journey maps from persona, scenario, and research data"
    )
    parser.add_argument(
        "--persona",
        type=Path,
        required=True,
        help="Path to persona JSON file"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Scenario description (or path to JSON)"
    )
    parser.add_argument(
        "--goal",
        type=str,
        help="Journey goal"
    )
    parser.add_argument(
        "--research",
        type=Path,
        help="Path to research_findings.json"
    )
    parser.add_argument(
        "--jtbd",
        type=Path,
        help="Path to JTBD data with job_steps"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path for JSON"
    )
    parser.add_argument(
        "--mermaid",
        type=Path,
        help="Output file path for Mermaid diagram"
    )

    args = parser.parse_args()

    # Load persona
    with open(args.persona, 'r', encoding='utf-8') as f:
        persona = json.load(f)

    # Build scenario
    if args.scenario and Path(args.scenario).exists():
        with open(args.scenario, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
    else:
        scenario = {
            "description": args.scenario or "User journey through the product",
            "goal": args.goal or "Complete primary task successfully"
        }

    # Load optional inputs
    research = None
    if args.research:
        with open(args.research, 'r', encoding='utf-8') as f:
            research = json.load(f)

    jtbd_steps = None
    if args.jtbd:
        with open(args.jtbd, 'r', encoding='utf-8') as f:
            jtbd_data = json.load(f)
            jtbd_steps = jtbd_data.get("job_steps", [])

    # Generate
    generator = JourneyMapGenerator()
    journey_map, mermaid = generator.generate(
        persona=persona,
        scenario=scenario,
        research_findings=research,
        jtbd_job_steps=jtbd_steps
    )

    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(journey_map, f, indent=2)
        print(f"Journey map written to {args.output}")

    if args.mermaid:
        with open(args.mermaid, 'w', encoding='utf-8') as f:
            f.write(mermaid)
        print(f"Mermaid diagram written to {args.mermaid}")

    if not args.output and not args.mermaid:
        print("=== Journey Map JSON ===")
        print(json.dumps(journey_map, indent=2))
        print("\n=== Mermaid Diagram ===")
        print(mermaid)


if __name__ == "__main__":
    main()
