---
name: ai-hci-audit
description: Use to audit the AI features of a design against the 18 Microsoft guidelines for human-AI interaction, alone or in the test phase. Checks transparency, user control and error handling.
---

# AI-HCI Audit Skill

## Purpose

Evaluate AI-powered features and interactions against Microsoft's 18 Human-AI Interaction Guidelines. Assess transparency, user control, error handling, and AI behavior that fits the context, so the AI experience is trustworthy and human-centered.

## Theoretical Foundation

This skill implements AI-HCI evaluation based on:

- **Microsoft Research**: 18 Guidelines for Human-AI Interaction (Amershi et al., CHI 2019)
- **Ben Shneiderman**: Human-Centered AI principles
- **HAX Toolkit**: Human-AI eXperience Design Toolkit
- **Google PAIR**: People + AI Research guidelines
- **IBM Design for AI**: Everyday Ethics for AI

## The 18 Guidelines

### Initially (Before Interaction)

Guidelines that apply before users interact with AI.

```markdown
## G1: Make clear what the system can do

### Requirements
- Capabilities clearly communicated
- Feature discovery helps understanding
- Limitations explicitly stated
- AI vs non-AI features distinguishable

### Audit Checklist
- [ ] Onboarding explains AI capabilities
- [ ] Help content describes AI features
- [ ] Limitations documented
- [ ] AI-powered features labeled

### Evidence Questions
- Can users understand what the AI can help with?
- Are there examples of good/bad use cases?
- Is it clear what the AI cannot do?

## G2: Make clear how well the system can do what it can do

### Requirements
- Confidence indicators shown
- Accuracy expectations set
- Performance limitations disclosed
- Uncertainty communicated

### Audit Checklist
- [ ] Confidence scores displayed
- [ ] Accuracy ranges documented
- [ ] "AI may make mistakes" messaging
- [ ] Known failure modes disclosed

### Evidence Questions
- Does the user know how reliable the AI is?
- Are confidence levels shown for suggestions?
- Is the AI honest about its limitations?
```

### During Interaction

Guidelines for active AI engagement.

```markdown
## G3: Time services based on context

### Requirements
- AI suggestions at appropriate times
- Not interrupting focused work
- Respects user preferences
- Context-aware triggering

### Audit Checklist
- [ ] Suggestions appear at natural pauses
- [ ] No interruption during typing
- [ ] User can control timing
- [ ] Different modes available (proactive/reactive)

### Evidence Questions
- Does the AI know when to help vs stay quiet?
- Can users adjust how proactive the AI is?
- Does it respect "do not disturb" signals?

## G4: Show contextually relevant information

### Requirements
- AI output relates to current task
- Suggestions are actionable
- Information is timely
- High relevance maintained

### Audit Checklist
- [ ] Suggestions relate to current context
- [ ] Information is actionable now
- [ ] No irrelevant AI outputs
- [ ] Context understood correctly

### Evidence Questions
- Is the AI's output relevant to what the user is doing?
- Does it understand the current task?
- Is the information useful right now?

## G5: Match relevant social norms

### Requirements
- Appropriate tone and formality
- Cultural sensitivity
- Professional context awareness
- User preference alignment

### Audit Checklist
- [ ] Tone matches context
- [ ] No inappropriate language
- [ ] Culturally neutral
- [ ] Formal/informal as appropriate

### Evidence Questions
- Does the AI communicate appropriately?
- Is the tone consistent with the product?
- Would users find the communication comfortable?

## G6: Mitigate social biases

### Requirements
- No discriminatory outputs
- Diverse representation
- Fairness in suggestions
- Bias testing documented

### Audit Checklist
- [ ] No stereotyping in outputs
- [ ] Diverse examples used
- [ ] No demographic-based differences
- [ ] Bias review conducted

### Evidence Questions
- Could the AI output harm any group?
- Are suggestions fair across demographics?
- Has bias testing been performed?
```

### When Wrong

Guidelines for handling AI errors and mistakes.

```markdown
## G7: Support efficient invocation

### Requirements
- Clear trigger for AI assistance
- Optional AI suggestions
- User can request help
- AI not intrusive

### Audit Checklist
- [ ] Clear "ask AI" button/command
- [ ] AI assistance is opt-in
- [ ] Easy to request AI help
- [ ] Not forced on users

### Evidence Questions
- Can users easily get AI help when wanted?
- Is it obvious how to invoke the AI?
- Is AI assistance optional?

## G8: Support efficient dismissal

### Requirements
- Single-action dismiss
- Keyboard accessible dismiss
- Dismissal persists appropriately
- "Don't show again" option

### Audit Checklist
- [ ] X button or swipe to dismiss
- [ ] Escape key dismisses
- [ ] Dismissal state remembered
- [ ] Permanent dismiss option exists

### Evidence Questions
- How many actions to dismiss AI output?
- Can keyboard users dismiss easily?
- Does the AI respect "no thanks"?

## G9: Support efficient correction

### Requirements
- Easy to edit AI output
- Correction mechanism clear
- Changes take effect immediately
- Can undo AI actions

### Audit Checklist
- [ ] Edit button on AI output
- [ ] Direct text editing possible
- [ ] Corrections reflected immediately
- [ ] Undo available for AI actions

### Evidence Questions
- How hard is it to fix AI mistakes?
- Can users modify AI suggestions?
- Is there an undo for AI actions?

## G10: Scope services when in doubt

### Requirements
- Conservative AI engagement
- Asks for clarification when uncertain
- Avoids overconfident outputs
- Graceful degradation

### Audit Checklist
- [ ] AI admits uncertainty
- [ ] Asks clarifying questions
- [ ] Doesn't guess when unsure
- [ ] Falls back gracefully

### Evidence Questions
- Does the AI know what it doesn't know?
- Does it ask for help when confused?
- Is it appropriately humble?

## G11: Make clear why the system did what it did

### Requirements
- Explanations available for AI decisions
- Reasoning understandable to users
- Evidence/sources cited
- Uncertainty communicated

### Audit Checklist
- [ ] "Why this suggestion?" available
- [ ] Explanation in plain language
- [ ] Sources/evidence shown
- [ ] Confidence indicated

### Evidence Questions
- Can users understand AI reasoning?
- Is the explanation helpful?
- Does it cite sources when relevant?
```

### Over Time

Guidelines for long-term AI behavior.

```markdown
## G12: Remember recent interactions

### Requirements
- Context preserved in session
- Previous inputs considered
- Conversation continuity
- No unnecessary repetition

### Audit Checklist
- [ ] Session context maintained
- [ ] Recent history available
- [ ] No repeated questions
- [ ] Builds on prior interactions

### Evidence Questions
- Does the AI remember what just happened?
- Does it build on previous context?
- Is there conversation continuity?

## G13: Learn from user behavior

### Requirements
- Personalization improves over time
- User patterns recognized
- Preferences respected
- Learning is transparent

### Audit Checklist
- [ ] Suggestions improve with use
- [ ] Preferences remembered
- [ ] Patterns recognized
- [ ] Learning disclosed

### Evidence Questions
- Does the AI get better over time?
- Does it learn user preferences?
- Is personalization transparent?

## G14: Update and adapt cautiously

### Requirements
- Changes are gradual
- User notified of changes
- Can revert changes
- Stability maintained

### Audit Checklist
- [ ] No sudden behavior changes
- [ ] Updates announced
- [ ] Revert option available
- [ ] Core behavior stable

### Evidence Questions
- Would sudden changes surprise users?
- Are AI updates communicated?
- Can users revert to old behavior?

## G15: Encourage granular feedback

### Requirements
- Specific feedback options
- Thumbs up/down available
- Comment/explain feedback
- Feedback is easy

### Audit Checklist
- [ ] Like/dislike on AI output
- [ ] "Why?" follow-up option
- [ ] Text feedback possible
- [ ] Feedback < 2 clicks

### Evidence Questions
- Can users give specific feedback?
- Is feedback low-friction?
- Does feedback feel impactful?

## G16: Convey consequences of user actions

### Requirements
- Feedback impact explained
- User understands effects
- Preview of changes
- Confirmation for significant actions

### Audit Checklist
- [ ] "This will..." explanations
- [ ] Preview of AI learning
- [ ] Confirmation dialogs
- [ ] Impact communicated

### Evidence Questions
- Do users know what their feedback does?
- Are consequences clear?
- Is there appropriate confirmation?

## G17: Provide global controls

### Requirements
- AI settings accessible
- Can disable AI features
- Personalization controls
- Privacy controls

### Audit Checklist
- [ ] AI settings page exists
- [ ] Master AI toggle
- [ ] Data/privacy controls
- [ ] Personalization settings

### Evidence Questions
- Can users control AI globally?
- Can they turn AI off entirely?
- Are there privacy settings?

## G18: Notify about changes

### Requirements
- AI updates communicated
- Changelog available
- Notification timing appropriate
- Changes can be reviewed

### Audit Checklist
- [ ] Update notifications
- [ ] What's new content
- [ ] Non-intrusive timing
- [ ] Detail available

### Evidence Questions
- How are AI changes communicated?
- Can users see what changed?
- Is the timing appropriate?
```

## Trust Indicators

### Trust Component Scores

```markdown
## Trust Model

### Transparency (G1, G2, G11)
- Capabilities clear
- Limitations stated
- Reasoning available

### Control (G7, G8, G9, G17)
- Easy invocation
- Easy dismissal
- Easy correction
- Global settings

### Reliability (G4, G10, G14)
- Relevant output
- Appropriate scope
- Stable behavior

### Respect (G3, G5, G6, G12)
- Good timing
- Social norms
- No bias
- Memory
```

### Trust Score Calculation

```python
trust_score = (
    transparency_score * 0.30 +
    control_score * 0.30 +
    reliability_score * 0.25 +
    respect_score * 0.15
)
```

## Severity Classification

| Severity | Trust Impact | Examples |
|----------|--------------|----------|
| Critical | Trust-breaking | No transparency, irreversible AI action |
| High | Significant erosion | Hard to dismiss, no explanation |
| Medium | Friction | Limited feedback, unclear confidence |
| Low | Enhancement opportunity | Better personalization possible |

## Output Format

### Finding Structure

```json
{
  "finding_id": "AI-001",
  "guideline": "G8",
  "guideline_name": "Support efficient dismissal",
  "category": "when_wrong",
  "severity": "high",
  "status": "partial",
  "score": 5,
  "affected_components": ["C-AI-001"],
  "description": "AI suggestions require multiple steps to dismiss",
  "user_impact": "Users frustrated by persistent suggestions",
  "trust_impact": "Erodes sense of control",
  "remediation": {
    "recommendation": "Add single-click dismiss button",
    "pattern": "Dismissible card with X button",
    "effort": "low"
  }
}
```

### Evaluation Report

```json
{
  "framework": "microsoft_18_guidelines",
  "version": "1.0",
  "evaluation_summary": {
    "total_guidelines": 18,
    "fully_met": 10,
    "partially_met": 5,
    "not_met": 2,
    "not_applicable": 1,
    "compliance_score": 0.72
  },
  "by_category": {
    "initially": {"score": 8.5, "guidelines": ["G1", "G2"]},
    "during_interaction": {"score": 7.0, "guidelines": ["G3", "G4", "G5", "G6"]},
    "when_wrong": {"score": 5.5, "guidelines": ["G7", "G8", "G9", "G10", "G11"]},
    "over_time": {"score": 6.5, "guidelines": ["G12", "G13", "G14", "G15", "G16", "G17", "G18"]}
  },
  "trust_indicators": {
    "transparency_score": 7.5,
    "control_score": 6.0,
    "reliability_score": 7.0,
    "respect_score": 8.0,
    "overall_trust": 7.1
  },
  "critical_issues": [...],
  "findings": [...]
}
```

## Testing Scenarios

### Scenario-Based Evaluation

```markdown
## Test Scenarios

### 1. First-Time User
- Can they understand what AI does?
- Are expectations set correctly?
- Is onboarding adequate?

### 2. Expert User Customization
- Can they control AI behavior?
- Are settings accessible?
- Can they optimize for their workflow?

### 3. AI Makes Mistake
- Can users easily dismiss?
- Can they correct the error?
- Does feedback work?

### 4. User Wants AI to Stop
- Is dismissal single-action?
- Does "don't show again" work?
- Are global controls available?

### 5. Understanding AI Decision
- Is explanation available?
- Is reasoning understandable?
- Does it build trust?
```

## Quality Criteria

AI-HCI audit is complete when:

1. **All guidelines evaluated**: 18 guidelines assessed
2. **Evidence-based**: Findings linked to components
3. **User-centered**: Impact from user perspective
4. **Trust-focused**: Trust implications documented
5. **Actionable**: Clear remediation guidance

---

**Dispatched by**: UX Evaluator
**Framework**: Microsoft 18 Guidelines for Human-AI Interaction
**Output**: AI-HCI findings for synthesis
**Agent**: ai-hci-reviewer

