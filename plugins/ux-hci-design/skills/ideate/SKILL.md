---
name: ideate
description: Use in the ideate phase of Design Thinking, after the define phase. Holds the method that makes design concepts, with the 10 principles of Dieter Rams as quality limits. The agent ux-concept-designer reads it.
---

# IDEATE Phase Skill

## Purpose

Generate innovative design concepts through divergent thinking while maintaining quality through Dieter Rams' 10 Principles of Good Design. Transform insights from DEFINE phase into actionable design directions.

## Theoretical Foundation

This skill draws from foundational design methodologies:

- **Dieter Rams**: 10 Principles of Good Design - "Less, but better"
- **Tim Brown (IDEO)**: Design Thinking - diverge before converging
- **Don Norman**: Emotional design levels - visceral, behavioral, reflective
- **Edward de Bono**: Lateral thinking and Six Thinking Hats

## Divergent Thinking Framework

### How Might We (HMW) Questions

Transform insights into opportunities:

```markdown
## HMW Question Template

For each pain point or need:
1. Reframe as opportunity: "How might we [help users] [achieve goal] [despite constraint]?"
2. Generate variations:
   - HMW make it easier...
   - HMW make it faster...
   - HMW make it more enjoyable...
   - HMW remove the need to...
   - HMW automate...
   - HMW simplify...
```

### Concept Generation Protocol

Generate 3-5 distinct concepts:

```markdown
## Concept Types to Explore

1. **Evolutionary** (Safe)
   - Incremental improvement on current state
   - Low risk, faster implementation
   - Questions: What if we just improved X?

2. **Revolutionary** (Bold)
   - Fundamentally new approach
   - Higher risk, potentially transformative
   - Questions: What if we started from scratch?

3. **Hybrid** (Balanced)
   - Combines best of existing solutions
   - Moderate risk, good value
   - Questions: What if we combined A and B?

4. **Minimal Viable** (Lean)
   - Simplest solution meeting core needs
   - Fast validation, learning-focused
   - Questions: What's the simplest thing that could work?

5. **Full Vision** (Aspirational)
   - Ideal solution without constraints
   - North star for incremental work
   - Questions: If we had unlimited resources?
```

## Dieter Rams' 10 Principles Evaluation

### Scoring Framework

| Principle | Question to Ask | Score (1-10) |
|-----------|-----------------|--------------|
| Innovative | Does it advance the state of the art? | |
| Useful | Does it solve real user problems? | |
| Aesthetic | Is it visually pleasing and harmonious? | |
| Understandable | Is it self-explanatory? | |
| Unobtrusive | Does it stay out of the way? | |
| Honest | Does it avoid deception? | |
| Long-lasting | Will it remain relevant? | |
| Thorough | Are edge cases considered? | |
| Environmentally friendly | Does it minimize waste/resources? | |
| Minimal | Is everything essential? | |

### Applying Rams to Digital Design

```markdown
## Principle Translations

### Innovative
- Uses new interaction patterns appropriately
- Leverages AI capabilities thoughtfully
- Doesn't innovate for innovation's sake

### Useful
- Directly addresses user goals
- Reduces time and cognitive load
- Provides clear value

### Aesthetic
- Visual hierarchy guides attention
- Consistent, harmonious design language
- Appropriate use of whitespace

### Understandable
- Clear affordances
- Predictable behavior
- Minimal learning curve

### Unobtrusive
- Respects user attention
- No dark patterns
- Supports task focus

### Honest
- Transparent about capabilities
- Clear about AI involvement
- No manipulative design

### Long-lasting
- Flexible architecture
- Graceful evolution path
- Avoids trend-dependency

### Thorough
- Edge cases handled
- Accessibility built in
- Error states designed

### Environmentally Friendly (Digital)
- Performance optimized
- Bandwidth conscious
- Device battery friendly

### Minimal
- Every element justified
- No feature bloat
- "Less, but better"
```

## Don Norman's Design Principles

### Applying Norman to Concepts

```markdown
## Norman Principle Checklist

### Visibility
- [ ] Key actions visible without searching
- [ ] Status clearly indicated
- [ ] Important info not hidden

### Feedback
- [ ] Every action acknowledged
- [ ] Appropriate feedback timing
- [ ] Multi-modal feedback (visual + audio/haptic)

### Constraints
- [ ] Impossible actions prevented
- [ ] Guidance toward correct actions
- [ ] Clear error prevention

### Mapping
- [ ] Natural relationships between controls and effects
- [ ] Spatial layouts match mental models
- [ ] Sequential flows are logical

### Consistency
- [ ] Similar elements behave similarly
- [ ] Industry conventions followed
- [ ] Internal consistency maintained

### Affordance
- [ ] Elements suggest their use
- [ ] Clickable things look clickable
- [ ] Interactive elements are obvious
```

## Feature Prioritization

### MoSCoW Framework

| Priority | Description | Criteria |
|----------|-------------|----------|
| Must Have | Critical for launch | Blocks user goals if missing |
| Should Have | Important but not critical | Significantly improves experience |
| Could Have | Desirable enhancements | Nice-to-have features |
| Won't Have | Out of scope | Defer to future iterations |

### Accessibility-First Feature Definition

```json
{
  "feature_id": "F-001",
  "name": "Feature Name",
  "priority": "must_have",
  "user_story": "As a [user], I want [feature], so that [benefit]",
  "acceptance_criteria": [
    "Functional criteria",
    "Performance criteria"
  ],
  "accessibility_requirements": [
    "Keyboard operable",
    "Screen reader compatible",
    "4.5:1 contrast minimum"
  ],
  "ai_capabilities": []
}
```

## Concept Documentation

### Required Elements

1. **Value Proposition**
   - Primary benefit
   - Target users (persona references)
   - Differentiation from alternatives

2. **Key Features** (3-10)
   - Prioritized list
   - User stories
   - Accessibility requirements

3. **Interaction Model**
   - Primary modality
   - Input methods
   - AI interaction style

4. **Visual Direction**
   - Style intent
   - Density (spacious/balanced/compact)
   - Motion philosophy

5. **Risks and Mitigations**
   - Technical risks
   - Usability risks
   - Accessibility risks

## AI Integration Considerations

### AI Feature Definition

```markdown
## Questions for AI Features

1. **What problem does AI solve?**
   - Could this be done without AI?
   - What's the AI-specific value?

2. **How transparent should it be?**
   - Explicit AI indication?
   - Confidence display?
   - Explanation available?

3. **What control do users have?**
   - Can they override?
   - Can they disable?
   - Can they provide feedback?

4. **What if AI fails?**
   - Graceful degradation path
   - User notification
   - Manual fallback
```

## Output Generation

Generate design concepts in JSON format:

```json
{
  "schema_version": "1.0",
  "concept": {
    "concept_id": "DC-001",
    "title": "Concept Title",
    "tagline": "One-line essence",
    "description": "Detailed description...",
    "concept_type": "hybrid",
    "value_proposition": {...},
    "design_principles": {
      "rams_alignment": {...},
      "norman_principles": {...},
      "accessibility_commitment": {
        "wcag_target": "AA"
      }
    },
    "key_features": [...],
    "interaction_model": {...},
    "visual_direction": {...},
    "constraints": {...},
    "risks_and_mitigations": [...]
  },
  "metadata": {...}
}
```

## Handoff Checklist

Before transitioning to PROTOTYPE phase:

- [ ] 3-5 distinct concepts generated
- [ ] Rams evaluation complete for each
- [ ] Norman principles applied
- [ ] Features prioritized
- [ ] Accessibility requirements defined
- [ ] AI interactions specified
- [ ] Recommended concept selected
- [ ] design_concepts.json generated and validated

## Quality Criteria

Ideation is complete when:

1. **Divergent**: Multiple distinct approaches explored
2. **Grounded**: Concepts address real user needs
3. **Principled**: Rams scores documented
4. **Accessible**: WCAG commitment specified
5. **AI-Aware**: AI features thoughtfully designed
6. **Prioritized**: Clear recommendation with rationale

---

**Previous Phase**: DEFINE (personas, journey maps)
**Next Phase**: PROTOTYPE (wireframes)
**Agent**: ux-concept-designer
**Output**: design_concepts.json

---

## Tailwind Plus Context

When the project has `.ux-config.json` with `tailwind_plus: true`, the concept designer
adds a `tailwind_plus_vocabulary` block to each concept's `visual_direction` section,
specifying kit, template reference, color scheme, and font combo. Design decisions
(Rams scores, Norman principles) take precedence over template defaults. Optional: the
paid tailwind-plus plugin, not in this marketplace.
