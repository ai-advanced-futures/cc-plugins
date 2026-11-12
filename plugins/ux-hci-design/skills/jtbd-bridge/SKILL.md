---
name: jtbd-bridge
description: Use when the person has a Jobs-to-be-Done JSON file and wants personas and journey maps from it. Holds the rules that map the JTBD data to UX artifacts.
---

# JTBD Bridge Skill

## Purpose

Transform Jobs-to-be-Done framework outputs into UX design artifacts. This bridge enables teams using JTBD for opportunity identification to seamlessly generate personas, journey maps, and design requirements.

## JTBD → UX Transformation Map

| JTBD Input | UX Output | Transformation |
|------------|-----------|----------------|
| Job Statement | Design Goal | Extract outcome, add context |
| Job Steps | Journey Map Stages | Map to journey phases |
| Customer Needs | Persona Needs | Categorize and prioritize |
| Outcome Statements | Success Criteria | Make measurable |
| Market Segments | Proto-Personas | Enrich with research |
| Opportunity Scores | Design Priority | Apply to pain points |
| Job Differentiators | Unique Value Props | Inform positioning |
| Emotional Jobs | Emotional Needs | Add to persona needs |
| Social Jobs | Social Context | Inform context section |

## Input Schema: JTBD Data

Expected JTBD input format:

```json
{
  "job_statement": {
    "job_executor": "string",
    "situation": "string",
    "motivation": "string",
    "outcome": "string",
    "full_statement": "When [situation], I want to [motivation], so I can [outcome]"
  },
  "job_steps": [
    {
      "step_number": 1,
      "step_name": "string",
      "description": "string",
      "substeps": []
    }
  ],
  "customer_needs": [
    {
      "need_id": "string",
      "need_statement": "string",
      "need_type": "functional|emotional|social|consumption_chain",
      "importance": 1-10,
      "satisfaction": 1-10,
      "opportunity_score": 0-20
    }
  ],
  "outcome_statements": [
    {
      "outcome_id": "string",
      "direction": "minimize|maximize",
      "metric": "string",
      "object": "string",
      "full_statement": "[Direction] the [metric] of [object]"
    }
  ],
  "market_segments": [
    {
      "segment_id": "string",
      "segment_name": "string",
      "description": "string",
      "size": "string",
      "characteristics": [],
      "unmet_needs": []
    }
  ],
  "opportunity_analysis": {
    "total_opportunities": "number",
    "high_opportunity_needs": [],
    "prioritized_opportunities": []
  }
}
```

## Transformation Logic

### 1. Job Statement → Design Goals

```python
def transform_job_to_goals(job_statement):
    """Transform JTBD job statement into persona design goals."""
    return {
        "description": job_statement["outcome"],
        "priority": "critical",  # Job statement = critical goal
        "context": job_statement["situation"],
        "success_criteria": f"Successfully {job_statement['motivation']}"
    }
```

**Example**:
```
JTBD: "When I'm preparing a presentation, I want to quickly find relevant
       data, so I can make compelling arguments"

Design Goal: {
  "description": "Make compelling arguments in presentations",
  "priority": "critical",
  "context": "Preparing for important presentations",
  "success_criteria": "Successfully finds and incorporates relevant data quickly"
}
```

### 2. Job Steps → Journey Stages

```python
def transform_job_steps_to_stages(job_steps):
    """Transform JTBD job steps into journey map stages."""
    stages = []
    for step in job_steps:
        stages.append({
            "stage_name": step["step_name"],
            "stage_number": step["step_number"],
            "description": step["description"],
            "user_goals": [f"Successfully {step['step_name'].lower()}"],
            "touchpoints": [],  # To be filled from research
            "emotions": [],     # To be filled from research
            "pain_points": [],  # Map from high-opportunity needs
            "opportunities": [] # Map from opportunity analysis
        })
    return stages
```

**Standard Job Step Mapping**:

| JTBD Universal Job Steps | Journey Stage Equivalent |
|-------------------------|-------------------------|
| 1. Define the problem | Discovery/Awareness |
| 2. Locate resources | Research/Exploration |
| 3. Prepare to act | Setup/Preparation |
| 4. Confirm readiness | Validation |
| 5. Execute | Core Action |
| 6. Monitor | Feedback/Review |
| 7. Modify | Iteration |
| 8. Conclude | Completion |

### 3. Customer Needs → Persona Needs

```python
def transform_needs_to_persona(customer_needs):
    """Transform JTBD customer needs into persona needs."""
    persona_needs = []
    for need in customer_needs:
        priority = calculate_priority(need["opportunity_score"])
        persona_needs.append({
            "description": need["need_statement"],
            "type": map_need_type(need["need_type"]),
            "priority": priority,
            "unmet": need["satisfaction"] < 5
        })
    return persona_needs

def calculate_priority(opportunity_score):
    if opportunity_score >= 15:
        return "must_have"
    elif opportunity_score >= 10:
        return "should_have"
    else:
        return "nice_to_have"

def map_need_type(jtbd_type):
    mapping = {
        "functional": "functional",
        "emotional": "emotional",
        "social": "social",
        "consumption_chain": "experiential"
    }
    return mapping.get(jtbd_type, "functional")
```

### 4. Opportunity Scores → Pain Point Severity

```python
def transform_opportunity_to_severity(opportunity_score):
    """Map JTBD opportunity score to pain point severity."""
    # Opportunity Score = Importance + (Importance - Satisfaction)
    # Scale: 0-20, where 10+ indicates opportunity

    if opportunity_score >= 15:
        return "critical"
    elif opportunity_score >= 12:
        return "high"
    elif opportunity_score >= 10:
        return "medium"
    else:
        return "low"
```

### 5. Market Segments → Proto-Personas

```python
def transform_segment_to_proto_persona(segment):
    """Transform JTBD market segment into proto-persona."""
    return {
        "name": f"Proto-{segment['segment_name']}",
        "tagline": segment["description"][:100],
        "demographics": {
            "occupation": "Derived from segment characteristics"
        },
        "goals": [],  # To be enriched from job statement
        "pain_points": [],  # To be enriched from unmet needs
        "behaviors": extract_behaviors(segment["characteristics"]),
        "needs": transform_unmet_needs(segment["unmet_needs"]),
        "segments": [segment["segment_name"]],
        "_proto": True,  # Flag indicating needs research enrichment
        "_source": "jtbd_segment"
    }
```

## Complete Transformation Pipeline

```python
def jtbd_to_ux_artifacts(jtbd_data, research_findings=None):
    """
    Complete pipeline to transform JTBD data into UX artifacts.

    Args:
        jtbd_data: JTBD analysis output
        research_findings: Optional research to enrich proto-artifacts

    Returns:
        {
            "personas": [],
            "journey_maps": [],
            "requirements": []
        }
    """

    # Step 1: Create proto-personas from segments
    proto_personas = []
    for segment in jtbd_data.get("market_segments", []):
        proto = transform_segment_to_proto_persona(segment)

        # Add job-derived goals
        proto["goals"].append(
            transform_job_to_goals(jtbd_data["job_statement"])
        )

        # Add needs from customer needs
        for need in jtbd_data.get("customer_needs", []):
            if is_relevant_to_segment(need, segment):
                proto["needs"].append(transform_need(need))

        proto_personas.append(proto)

    # Step 2: Enrich with research if available
    if research_findings:
        personas = enrich_proto_personas(proto_personas, research_findings)
    else:
        personas = proto_personas

    # Step 3: Generate journey maps from job steps
    journey_maps = []
    for persona in personas:
        journey = {
            "title": f"{persona['name']} - {jtbd_data['job_statement']['outcome']}",
            "persona": {"name": persona["name"]},
            "scenario": {
                "description": jtbd_data["job_statement"]["full_statement"],
                "goal": jtbd_data["job_statement"]["outcome"]
            },
            "stages": transform_job_steps_to_stages(jtbd_data["job_steps"])
        }

        # Add pain points from high-opportunity needs
        for stage in journey["stages"]:
            relevant_needs = find_needs_for_stage(
                stage,
                jtbd_data["opportunity_analysis"]["high_opportunity_needs"]
            )
            stage["pain_points"] = [
                transform_need_to_pain_point(n) for n in relevant_needs
            ]

        journey_maps.append(journey)

    # Step 4: Generate prioritized requirements
    requirements = []
    for need in jtbd_data.get("customer_needs", []):
        if need["opportunity_score"] >= 10:
            requirements.append({
                "requirement_id": f"REQ-{need['need_id']}",
                "description": need["need_statement"],
                "priority": calculate_priority(need["opportunity_score"]),
                "source": "jtbd_analysis",
                "opportunity_score": need["opportunity_score"]
            })

    return {
        "personas": personas,
        "journey_maps": journey_maps,
        "requirements": sorted(
            requirements,
            key=lambda x: x["opportunity_score"],
            reverse=True
        )
    }
```

## Usage Scenarios

### Scenario 1: JTBD Only (No Research)

When only JTBD data is available:

```markdown
Input: JTBD opportunity analysis
Output: Proto-personas, proto-journey maps

Note: Outputs are flagged as "hypothesis" confidence level
      and require research validation
```

### Scenario 2: JTBD + Research

When both JTBD and research are available:

```markdown
Input: JTBD opportunity analysis + the research findings of the `inputs` list
Output: Enriched personas, validated journey maps

Process:
1. Generate proto-artifacts from JTBD
2. Overlay research findings
3. Validate/adjust priorities
4. Fill in gaps (emotions, touchpoints)
5. Mark confidence as "validated"
```

### Scenario 3: Research First, JTBD Validation

When research was conducted first:

```markdown
Input: the research findings of the `inputs` list + JTBD data
Output: Research-based personas with JTBD validation

Process:
1. Generate personas from research
2. Validate goals against job statement
3. Verify needs against customer needs
4. Adjust priorities based on opportunity scores
5. Ensure coverage of high-opportunity needs
```

## Accessibility Integration

When transforming JTBD data, ensure:

1. **Segment Accessibility**: Check if any segments have accessibility-related characteristics
2. **Need Accessibility**: Flag accessibility-related needs
3. **Journey Accessibility**: Consider accessibility at each job step

```python
def check_accessibility_relevance(jtbd_data):
    """Flag accessibility-relevant JTBD elements."""

    accessibility_keywords = [
        "vision", "hearing", "motor", "cognitive",
        "screen reader", "keyboard", "voice",
        "disability", "accessibility", "inclusive"
    ]

    flags = {
        "segments": [],
        "needs": [],
        "steps": []
    }

    # Check segments
    for segment in jtbd_data.get("market_segments", []):
        for char in segment.get("characteristics", []):
            if any(kw in char.lower() for kw in accessibility_keywords):
                flags["segments"].append(segment["segment_id"])
                break

    # Check needs
    for need in jtbd_data.get("customer_needs", []):
        if any(kw in need["need_statement"].lower() for kw in accessibility_keywords):
            flags["needs"].append(need["need_id"])

    return flags
```

## AI-HCI Integration

For AI-heavy products, map JTBD to AI-HCI concerns:

| JTBD Element | AI-HCI Consideration |
|--------------|---------------------|
| Functional Needs | AI capability requirements |
| Emotional Needs | Trust and transparency needs |
| Social Needs | Privacy and sharing concerns |
| Job Steps | AI involvement at each step |
| Outcome Statements | AI success metrics |

## Output Validation

All transformed artifacts must:

1. **Schema Validation**: Pass schema validation
2. **Traceability**: Link back to JTBD source
3. **Completeness**: Include all required fields
4. **Confidence**: Be marked with appropriate confidence level

## Example Transformation

### Input (JTBD Data)

```json
{
  "job_statement": {
    "situation": "reviewing code changes",
    "motivation": "understand what changed and why",
    "outcome": "make confident approval decisions"
  },
  "job_steps": [
    {"step_number": 1, "step_name": "Open PR", "description": "Navigate to pull request"},
    {"step_number": 2, "step_name": "Review changes", "description": "Examine code diff"},
    {"step_number": 3, "step_name": "Understand context", "description": "Read description and comments"},
    {"step_number": 4, "step_name": "Evaluate quality", "description": "Check for issues"},
    {"step_number": 5, "step_name": "Make decision", "description": "Approve, request changes, or comment"}
  ],
  "customer_needs": [
    {
      "need_id": "N1",
      "need_statement": "Minimize time to understand what changed",
      "importance": 9,
      "satisfaction": 4,
      "opportunity_score": 14
    },
    {
      "need_id": "N2",
      "need_statement": "Minimize risk of missing critical issues",
      "importance": 10,
      "satisfaction": 5,
      "opportunity_score": 15
    }
  ],
  "market_segments": [
    {
      "segment_id": "S1",
      "segment_name": "Senior Engineers",
      "characteristics": ["High technical expertise", "Time constrained", "Review many PRs daily"]
    }
  ]
}
```

### Output (UX Artifacts)

```json
{
  "persona": {
    "name": "Rapid Reviewer Rachel",
    "tagline": "Senior engineer who reviews many PRs daily and values efficiency",
    "goals": [
      {
        "description": "Make confident approval decisions on code reviews",
        "priority": "critical",
        "context": "When reviewing code changes",
        "success_criteria": "Can quickly understand changes and catch issues"
      }
    ],
    "needs": [
      {
        "description": "Quickly understand what code changed",
        "type": "functional",
        "priority": "must_have",
        "unmet": true
      },
      {
        "description": "Catch critical issues before approval",
        "type": "functional",
        "priority": "must_have",
        "unmet": true
      }
    ],
    "jtbd_integration": {
      "primary_job": "Make confident approval decisions on code reviews",
      "job_context": "Reviewing code changes from team members",
      "success_outcomes": ["Minimize time to understand changes", "Minimize missed issues"]
    }
  }
}
```

---

**Invocation**: `/ux-hci-design:ux-design integrate` or during DEFINE phase with JTBD input
**Input**: JTBD opportunity analysis JSON
**Output**: Personas, journey maps, prioritized requirements
**Helper skill**: ux-artifact-generator (with JTBD bridge logic)
