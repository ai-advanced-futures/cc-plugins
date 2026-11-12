---
name: accessibility-audit
description: Use to audit a design for WCAG 2.2 Level AA accessibility, alone or in the test phase. Checks the artifacts against the POUR principles and gives a fix for each barrier.
---

# Accessibility Audit Skill

## Purpose

Evaluate design artifacts against WCAG 2.2 Level AA requirements. Report each WCAG 2.2 barrier with its POUR principle (Perceivable, Operable, Understandable, Robust), its success criterion, and a fix with a code example.

## Theoretical Foundation

This skill implements accessibility evaluation based on:

- **W3C WCAG 2.2**: Web Content Accessibility Guidelines (2023)
- **Section 508**: U.S. Federal accessibility requirements
- **EN 301 549**: European accessibility standard
- **ARIA 1.2**: Accessible Rich Internet Applications
- **WebAIM**: Practical accessibility guidance

## WCAG 2.2 Conformance Levels

| Level | Description | Requirements |
|-------|-------------|--------------|
| A | Minimum | 31 success criteria (essential) |
| AA | Standard | 24 additional criteria (recommended) |
| AAA | Enhanced | 28 additional criteria (optimal) |

**Target**: Level AA conformance (55 total criteria)

## POUR Principles

### Perceivable (17 criteria at AA)

Content must be presentable to users in ways they can perceive.

#### 1.1 Text Alternatives

```markdown
## 1.1.1 Non-text Content (A)

### Requirements
- All images have appropriate alt text
- Decorative images use alt=""
- Complex images have long descriptions
- Form inputs have accessible labels
- CAPTCHA provides alternatives

### Audit Checklist
- [ ] img elements have alt attribute
- [ ] alt text describes image purpose
- [ ] Decorative images have empty alt
- [ ] Icons have text alternatives
- [ ] Background images don't convey information
```

#### 1.3 Adaptable

```markdown
## 1.3.1 Info and Relationships (A)

### Requirements
- Heading hierarchy (h1→h2→h3) correct
- Lists use proper list markup
- Tables have header associations
- Form labels programmatically associated

### Audit Checklist
- [ ] Headings follow logical order
- [ ] No skipped heading levels
- [ ] Data tables have th elements
- [ ] table has caption or aria-labelledby
- [ ] Form fields have associated labels
```

#### 1.4 Distinguishable

```markdown
## 1.4.3 Contrast (Minimum) (AA)

### Requirements
- Normal text: 4.5:1 contrast ratio
- Large text (18pt/14pt bold): 3:1 ratio
- Placeholder text meets requirements

### Audit Checklist
- [ ] Body text has 4.5:1 contrast
- [ ] Headings have sufficient contrast
- [ ] Links distinguishable from text
- [ ] Placeholder text readable
- [ ] Disabled states still visible

## 1.4.11 Non-text Contrast (AA)

### Requirements
- UI components: 3:1 contrast
- Focus indicators: 3:1 contrast
- Graphical objects: 3:1 contrast

### Audit Checklist
- [ ] Button borders visible
- [ ] Form field boundaries clear
- [ ] Icons have sufficient contrast
- [ ] Focus ring clearly visible
- [ ] Charts/graphs readable
```

### Operable (20 criteria at AA)

User interface and navigation must be operable.

#### 2.1 Keyboard Accessible

```markdown
## 2.1.1 Keyboard (A)

### Requirements
- All functionality via keyboard
- No keyboard traps
- Logical focus order
- Custom widgets keyboard operable

### Audit Checklist
- [ ] Tab reaches all interactive elements
- [ ] Enter/Space activates buttons
- [ ] Arrow keys navigate menus
- [ ] Escape closes modals
- [ ] No focus traps exist

## 2.1.2 No Keyboard Trap (A)

### Requirements
- Focus can move away from any component
- Instructions provided if non-standard

### Critical Test
- Tab through entire page
- Verify focus never gets stuck
- Test modal dialogs specifically
```

#### 2.4 Navigable

```markdown
## 2.4.1 Bypass Blocks (A)

### Requirements
- Skip to main content link
- Landmark regions defined
- Heading navigation available

### Audit Checklist
- [ ] Skip link as first focusable element
- [ ] Skip link visible on focus
- [ ] Main landmark present
- [ ] Navigation landmark present

## 2.4.6 Headings and Labels (AA)

### Requirements
- Headings describe topic/purpose
- Labels describe purpose
- Consistent labeling

### Audit Checklist
- [ ] Headings are descriptive
- [ ] Form labels clear
- [ ] Button labels indicate action
- [ ] Link text meaningful

## 2.4.7 Focus Visible (AA)

### Requirements
- Keyboard focus indicator visible
- Focus indicator has 3:1 contrast
- Focus visible for all interactive elements

### Audit Checklist
- [ ] Focus ring visible on buttons
- [ ] Focus ring visible on links
- [ ] Focus ring visible on form fields
- [ ] Focus never hidden by CSS
- [ ] Custom focus styles adequate
```

#### 2.5 Input Modalities (New in WCAG 2.1/2.2)

```markdown
## 2.5.3 Label in Name (A)

### Requirements
- Accessible name contains visible text
- Voice control can activate by label

### Audit Checklist
- [ ] Button text in aria-label
- [ ] No icon-only buttons without label
- [ ] Visible label matches accessible name

## 2.5.8 Target Size (Minimum) (AA) - New in 2.2

### Requirements
- Touch targets at least 24x24 CSS pixels
- Adequate spacing between targets
- Exceptions for inline, user agent, essential

### Audit Checklist
- [ ] Buttons meet 24x24 minimum
- [ ] Links in text have adequate spacing
- [ ] Form controls adequately sized
- [ ] Mobile targets 44x44 recommended
```

### Understandable (8 criteria at AA)

Information and UI operation must be understandable.

#### 3.1 Readable

```markdown
## 3.1.1 Language of Page (A)

### Requirements
- Page has lang attribute
- Language code valid

### Audit Checklist
- [ ] html has lang attribute
- [ ] Language code correct (en, es, fr)
- [ ] Passages in other languages marked
```

#### 3.2 Predictable

```markdown
## 3.2.1 On Focus (A)

### Requirements
- Focus doesn't cause unexpected changes
- No auto-submission on focus
- Context preserved

### Audit Checklist
- [ ] No page refresh on focus
- [ ] No popup on focus
- [ ] No form submission on focus

## 3.2.2 On Input (A)

### Requirements
- Input doesn't cause unexpected changes
- User warned before context change

### Audit Checklist
- [ ] Select doesn't auto-submit
- [ ] Radio buttons don't navigate
- [ ] User controls submission
```

#### 3.3 Input Assistance

```markdown
## 3.3.1 Error Identification (A)

### Requirements
- Errors described in text
- Error field identified
- Error near field or in summary

### Audit Checklist
- [ ] Error message in text (not just color)
- [ ] Field with error indicated
- [ ] Error describes problem
- [ ] Error near problematic field

## 3.3.2 Labels or Instructions (A)

### Requirements
- Required fields marked
- Format requirements stated
- Examples provided when helpful

### Audit Checklist
- [ ] Required marked with text/asterisk
- [ ] Date format shown
- [ ] Input constraints explained
- [ ] Examples for complex inputs

## 3.3.7 Redundant Entry (A) - New in 2.2

### Requirements
- Previously entered info auto-populated
- User can select from previous entries

### Audit Checklist
- [ ] Shipping/billing can copy
- [ ] Autocomplete supported
- [ ] Previous entries accessible

## 3.3.8 Accessible Authentication (AA) - New in 2.2

### Requirements
- No cognitive function test
- Password managers supported
- Alternative methods available

### Audit Checklist
- [ ] CAPTCHA has alternatives
- [ ] Password paste enabled
- [ ] Biometric option available
- [ ] No memory-based auth required
```

### Robust (5 criteria at AA)

Assistive technologies parse and operate the content.

```markdown
## 4.1.1 Parsing (A)

### Requirements
- No duplicate IDs
- Elements properly nested
- Tags properly closed

### Audit Checklist
- [ ] HTML validates
- [ ] IDs unique on page
- [ ] ARIA attributes valid

## 4.1.2 Name, Role, Value (A)

### Requirements
- Custom widgets have ARIA roles
- State changes announced
- Name and value accessible

### Audit Checklist
- [ ] Custom controls have roles
- [ ] aria-expanded used correctly
- [ ] aria-checked for toggles
- [ ] Live regions for updates
```

## ARIA Guidelines

### Common ARIA Patterns

```markdown
## Modal Dialog
role="dialog"
aria-modal="true"
aria-labelledby="[title-id]"
Focus trap with tab cycling

## Tab Panel
role="tablist" on container
role="tab" on tab buttons
role="tabpanel" on panels
aria-selected on active tab
aria-controls linking

## Accordion
role="button" on headers
aria-expanded="true/false"
aria-controls="[panel-id]"
Keyboard: Enter/Space toggle

## Alert/Toast
role="alert" or aria-live="assertive"
Auto-announce to screen readers
Don't auto-dismiss critical info
```

## Testing Procedures

### Automated Testing

```markdown
## Tools
- axe DevTools
- WAVE
- Lighthouse Accessibility
- Pa11y
- HTML validator

## Scope
- Color contrast
- Alt text presence
- Heading structure
- ARIA validity
- Label associations
```

### Manual Testing

```markdown
## Keyboard Testing
1. Tab through entire page
2. Verify all controls reachable
3. Test Enter/Space activation
4. Test arrow key navigation
5. Verify Escape closes modals

## Screen Reader Testing
1. Test with NVDA (Windows)
2. Test with VoiceOver (Mac/iOS)
3. Test with TalkBack (Android)
4. Verify all content announced
5. Test form interactions

## Visual Testing
1. Zoom to 200%
2. Test high contrast mode
3. Test color blindness simulation
4. Test with reduced motion
```

## Severity Classification

| Severity | Impact | WCAG Level | Examples |
|----------|--------|------------|----------|
| Critical | Blocks access | A failure | Keyboard trap, no alt text |
| High | Major barrier | AA failure | Low contrast, no focus visible |
| Medium | Significant issue | Best practice | Unclear labels |
| Low | Minor issue | Enhancement | Missing lang attribute |

## Output Format

### Finding Structure

```json
{
  "finding_id": "A11Y-001",
  "criterion": "2.4.7",
  "criterion_name": "Focus Visible",
  "level": "AA",
  "principle": "operable",
  "severity": "high",
  "status": "fail",
  "affected_components": ["C-001", "C-005"],
  "description": "Focus indicator not visible on buttons",
  "impact": "Keyboard users cannot see current position",
  "remediation": {
    "recommendation": "Add visible focus indicator",
    "technique": "G195: Using visible focus indicator",
    "code_example": "button:focus-visible { outline: 2px solid #005fcc; outline-offset: 2px; }"
  }
}
```

### Evaluation Report

The reviewer writes this object to `<output_dir>/findings.json`. The list of findings is under the key `findings`.

```json
{
  "framework": "wcag",
  "version": "2.2",
  "target_level": "AA",
  "evaluation_summary": {
    "total_criteria": 55,
    "passed": 47,
    "failed": 6,
    "not_applicable": 2,
    "conformance_score": 0.84
  },
  "by_principle": {
    "perceivable": {"passed": 20, "failed": 2},
    "operable": {"passed": 16, "failed": 3},
    "understandable": {"passed": 7, "failed": 1},
    "robust": {"passed": 4, "failed": 0}
  },
  "critical_barriers": [...],
  "findings": [...]
}
```

## Quality Criteria

Accessibility audit is complete when:

1. **All criteria checked**: 55 Level AA criteria evaluated
2. **Evidence-based**: Each finding has component reference
3. **Actionable**: Clear remediation with code examples
4. **Prioritized**: Findings ranked by severity
5. **Documented**: Testing methods noted

---

**Started by**: the skill ux-design (the agent ux-evaluator reads the findings)
**Framework**: WCAG 2.2 Level AA
**Output**: Accessibility findings for synthesis
**Helper skill**: accessibility-reviewer

