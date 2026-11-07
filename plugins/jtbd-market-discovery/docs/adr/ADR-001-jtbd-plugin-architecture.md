# ADR-001: JTBD Market Discovery Plugin Architecture

**Status:** Accepted
**Date:** 2026-01-21
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Architect:** Luis F. Amadeo

---

## Context

Product teams and developers need a structured, data-driven approach to identify market opportunities using Jobs To Be Done (JTBD) methodology. Current challenges include:

1. **Lack of Structure** - Ad-hoc job discovery leads to incomplete analysis
2. **Unrealistic Pricing** - Willingness-to-pay (WTP) estimates often miss economic reality
3. **Fake Segments** - Demographic segmentation doesn't predict behavior
4. **Missing Value Quantification** - Can't justify opportunity with dollar amounts
5. **No Integration** - Discovery insights don't connect to downstream product development

Existing JTBD tools focus on theory but lack:
- Systematic workflow guidance
- Statistical analysis capabilities
- Economic validation frameworks
- Integration with product development tools

This ADR documents the architectural decisions for building a JTBD Market Discovery plugin that addresses these gaps.

---

## Decision

We will build a **hybrid methodology plugin** combining:

1. **Outcome-Driven Innovation (ODI)** by Tony Ulwick - for structured need identification
2. **Economic Value to Customer (EVC)** - for value quantification
3. **Christensen's Forces** - for understanding switching dynamics
4. **Multi-dimensional Segmentation** - for behavioral clusters
5. **6-Layer WTP Validation** - for realistic pricing

The plugin will be implemented as:
- **Primary Platform:** Claude Code plugin (full Python analysis)
- **Secondary Platform:** Claude.ai web skill (AI-powered fallbacks)
- **Output Format:** Structured JSON/YAML compatible with downstream plugins
- **User Experience:** Socratic dialogue with inline education

---

## Architecture Decisions

### 1. Methodology Stack

**Decision:** Use hybrid approach combining 5 complementary methodologies

**Rationale:**
- **ODI alone is insufficient** - Great for need identification but lacks value quantification
- **EVC alone is incomplete** - Quantifies value but doesn't identify which needs matter
- **Hybrid provides completeness** - Each methodology fills gaps in others

**Trade-offs:**
- ✅ **Pro:** Comprehensive analysis, realistic outputs
- ✅ **Pro:** Best practices from multiple proven frameworks
- ❌ **Con:** More complex to implement (5 methodologies vs 1)
- ❌ **Con:** Longer workflow (10 phases vs simpler approach)

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **ODI Only** | Simple, well-documented | No value quantification, no pricing validation | ❌ Rejected |
| **Lean/Agile Discovery** | Fast, flexible | Too ad-hoc, hard to validate | ❌ Rejected |
| **Traditional Market Research** | Familiar to analysts | Expensive, slow, demographic focus | ❌ Rejected |
| **Hybrid (ODI + EVC + Forces)** | Comprehensive, data-driven | Complex implementation | ✅ **Selected** |

### 2. Technical Implementation

**Decision:** Python scripts (scikit-learn) for Claude Code, AI-powered fallbacks for web

**Rationale:**
- **Statistical rigor** - K-means clustering, outlier detection require proper algorithms
- **Performance** - Python/scikit-learn is fast (<30s for 50 respondents)
- **Accessibility** - Web fallbacks ensure everyone can use the plugin
- **Accuracy** - Python gives 100% accuracy, AI fallbacks give ~80% accuracy (acceptable)

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│                   SKILL.md                          │
│            (Socratic Dialogue Layer)                │
└────────────┬────────────────────────────────────────┘
             │
             ├── Claude Code Path
             │   ├── Python Scripts (scripts/*.py)
             │   │   ├── opportunity_scorer.py
             │   │   ├── evc_calculator.py
             │   │   ├── segmentation_engine.py
             │   │   └── wtp_validator.py
             │   └── scikit-learn clustering
             │
             └── Claude.ai Web Path
                 ├── AI-powered conceptual clustering
                 ├── Claude reasoning for calculations
                 └── Graceful degradation messages
```

**Trade-offs:**
- ✅ **Pro:** Best of both worlds (rigor + accessibility)
- ✅ **Pro:** Users can start on web, upgrade to Claude Code for precision
- ❌ **Con:** Maintaining two codepaths
- ❌ **Con:** Web version is ~80% as accurate

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Python Only** | Most accurate, rigorous | Excludes web users | ❌ Rejected |
| **JavaScript Only** | Works everywhere | No scikit-learn, less accurate | ❌ Rejected |
| **Hybrid (Python + AI)** | Accessible + rigorous | Dual maintenance | ✅ **Selected** |

### 3. WTP Validation Framework

**Decision:** 6-layer validation with EVC-based reality checks

**Rationale:**
- **Survey data lies** - People overstate WTP in hypothetical scenarios
- **Need multiple checks** - Single validation method is insufficient
- **Economic grounding** - EVC provides objective ceiling for sustainable pricing
- **Segment-specific** - B2B vs B2C have different value capture norms

**6 Layers:**
1. Statistical Outliers (IQR method)
2. Comparative Benchmarking (vs market pricing)
3. Van Westendorp PSM (if 4-question data available)
4. Value Economics (EVC-based reality check)
5. Confidence Scoring (sample size, consistency)
6. Segment-Specific (industry benchmarks)

**Trade-offs:**
- ✅ **Pro:** Catches unrealistic pricing early
- ✅ **Pro:** Provides defensible pricing recommendations
- ✅ **Pro:** Educates users about value capture
- ❌ **Con:** More complex than single-method validation
- ❌ **Con:** Requires more input data (EVC components)

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Direct Survey Only** | Simple, fast | People lie, unrealistic | ❌ Rejected |
| **Van Westendorp Only** | Industry standard | Still hypothetical bias | ❌ Rejected |
| **Conjoint Analysis** | Most accurate | Complex, expensive, slow | ⏸️ Deferred to v1.1 |
| **6-Layer Framework** | Comprehensive, realistic | Complex implementation | ✅ **Selected** |

### 4. Segmentation Approach

**Decision:** Multi-dimensional (Needs + Circumstances + Behavioral)

**Rationale:**
- **Demographic segmentation is weak** - Age/company size don't predict behavior
- **Needs alone insufficient** - Two segments may prioritize same needs but in different contexts
- **Behavioral patterns reveal reality** - What they do > what they say

**Three Dimensions:**
1. **Needs Profile** (ODI) - Which outcomes matter most (K-means on importance ratings)
2. **Circumstances** (Christensen) - When/why job occurs, switching triggers
3. **Behavioral** (Observational) - Current solutions, workarounds, pain frequency

**Trade-offs:**
- ✅ **Pro:** Segments are actionable (observable behaviors)
- ✅ **Pro:** Predicts actual purchase behavior
- ✅ **Pro:** Reveals hidden opportunities
- ❌ **Con:** Requires more data collection
- ❌ **Con:** More complex analysis

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Demographic** | Easy to collect | Doesn't predict behavior | ❌ Rejected |
| **Needs-Based Only** | ODI standard | Misses context | ❌ Rejected |
| **Psychographic** | Interesting insights | Hard to act on | ❌ Rejected |
| **Multi-Dimensional** | Actionable, predictive | Complex, more data needed | ✅ **Selected** |

### 5. Output Format

**Decision:** Structured JSON/YAML with downstream plugin compatibility

**Rationale:**
- **Integration is key** - Discovery insights must flow to PRD/brainstorm/design
- **Machine-readable** - Enables automation and tool chaining
- **Human-readable** - JSON is easy to inspect and validate
- **Extensible** - Can add fields without breaking compatibility

**Schema Design:**
```json
{
  "analysis_metadata": {...},
  "job_statements": [...],
  "customer_needs": [...],
  "opportunities": [...],
  "segments": [...],
  "evc_analysis": {...},
  "wtp_validation": {...}
}
```

**Trade-offs:**
- ✅ **Pro:** Enables plugin ecosystem (discovery → PRD → design → execution)
- ✅ **Pro:** Structured data is queryable and transformable
- ✅ **Pro:** Version-controlled and diffable
- ❌ **Con:** More rigid than free-form documents
- ❌ **Con:** Schema evolution requires care

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Markdown Only** | Human-friendly | Hard to parse, integrate | ❌ Rejected |
| **PDF Report** | Professional looking | Not machine-readable | ❌ Rejected |
| **CSV Files** | Spreadsheet-friendly | Poor structure for nested data | ❌ Rejected |
| **JSON/YAML** | Machine + human readable | Requires schema design | ✅ **Selected** |

### 6. Educational Approach

**Decision:** Socratic dialogue with inline examples and learning-by-doing

**Rationale:**
- **Target audience is beginners** - Most users don't know JTBD theory
- **Theory is abstract** - Needs concrete examples to understand
- **Learning by doing works** - Reflecting user's inputs back as JTBD concepts
- **Progressive disclosure** - Introduce concepts as needed, not upfront

**Techniques:**
- **Socratic questioning** - "Tell me about a time..." not "Define your job"
- **Inline examples** - "A good job statement is: 'When [situation], I want to [action], so I can [outcome]'"
- **Reflection** - "That's a great outcome statement! Here's how it maps to JTBD..."
- **Error correction** - "That sounds more like a feature than a job. Let's dig deeper..."

**Trade-offs:**
- ✅ **Pro:** Accessible to non-experts
- ✅ **Pro:** Users learn JTBD while using plugin
- ✅ **Pro:** Reduces errors from misunderstanding
- ❌ **Con:** Longer dialogue (more turns required)
- ❌ **Con:** More complex SKILL.md (5,000+ lines)

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Theory-First** | Comprehensive education | Boring, users drop off | ❌ Rejected |
| **Template-Only** | Fast, simple | Users fill incorrectly | ❌ Rejected |
| **Socratic Dialogue** | Engaging, educational | Longer, complex SKILL | ✅ **Selected** |

### 7. Platform Strategy

**Decision:** Dual-platform with feature parity where possible

**Rationale:**
- **Claude Code users** - Developers, analysts with local Python
- **Claude.ai web users** - PMs, executives without dev setup
- **Maximize reach** - Don't exclude web-only users
- **Graceful degradation** - 80% accuracy on web is better than 0%

**Feature Matrix:**

| Feature | Claude Code | Claude.ai Web |
|---------|-------------|---------------|
| Socratic Discovery | ✅ Full | ✅ Full |
| Need Generation | ✅ Full | ✅ Full |
| Statistical Clustering | ✅ K-means | ⚠️ AI-powered conceptual |
| EVC Calculation | ✅ Python | ⚠️ Claude reasoning |
| WTP Validation | ✅ All 6 layers | ⚠️ Layers 2,4,6 (skip 1,5) |
| Codebase Analysis | ✅ Yes | ❌ No (user describes) |
| File I/O | ✅ Yes | ⚠️ Chat-based |

**Trade-offs:**
- ✅ **Pro:** Widest possible audience
- ✅ **Pro:** Users can start on web, upgrade later
- ✅ **Pro:** Both platforms share SKILL.md (single source of truth)
- ❌ **Con:** Dual testing required
- ❌ **Con:** Web version is less accurate

**Alternatives Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Claude Code Only** | Best quality | Excludes non-developers | ❌ Rejected |
| **Web Only** | Max accessibility | Lower accuracy, no Python | ❌ Rejected |
| **Dual Platform** | Balance reach + quality | More complex | ✅ **Selected** |

---

## Consequences

### Positive

1. **Comprehensive Analysis** - Users get complete opportunity validation (needs + value + pricing)
2. **Realistic Outputs** - 6-layer WTP validation prevents unrealistic pricing expectations
3. **Actionable Segments** - Multi-dimensional segmentation reveals observable behaviors
4. **Educational** - Users learn JTBD methodology while using the plugin
5. **Integrative** - Structured output enables downstream workflows (PRD, brainstorm, design)
6. **Accessible** - Works on both platforms with graceful fallbacks

### Negative

1. **Complexity** - 10-phase workflow is longer than simpler alternatives
2. **Development Time** - 9-12 days vs 3-4 days for simpler plugin
3. **Dual Maintenance** - Two codepaths (Python + AI fallbacks)
4. **Learning Curve** - Users must understand multiple methodologies
5. **Data Requirements** - Requires survey data for full analysis

### Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users find workflow too long | Medium | Medium | Add "quick mode" in v1.1 for experienced users |
| Web version accuracy insufficient | Low | High | Set expectations clearly, encourage Claude Code upgrade |
| Survey data quality poor | Medium | High | Provide validation checks, sample size guidance |
| Integration breaks with plugin updates | Low | Medium | Version output schema, maintain backwards compatibility |
| Users misuse EVC calculations | Medium | Medium | Add validation checks, require all components |

---

## Implementation Notes

### Phase Prioritization

**MVP (v1.0):**
- ✅ All 5 methodologies (ODI, EVC, Forces, Multi-dim segments, 6-layer WTP)
- ✅ Dual platform (Claude Code + Web)
- ✅ 2 complete examples
- ✅ Downstream integration (brainstorm, PRD)

**Future (v1.1+):**
- Van Westendorp PSM implementation
- Conjoint analysis support
- Switch interview guide
- Automated competitive pricing

### Testing Requirements

**Unit Tests:**
- All Python scripts >80% coverage
- Each methodology independently testable

**Integration Tests:**
- End-to-end workflow with sample data
- Output schema validation
- Downstream plugin compatibility

**Manual Tests:**
- Claude Code full workflow
- Claude.ai web fallback workflow
- Cross-platform output comparison

### Performance Targets

| Operation | Target | Rationale |
|-----------|--------|-----------|
| K-means clustering (50 respondents) | <30s | Acceptable wait time |
| EVC calculation | <5s | Near-instant |
| WTP validation (6 layers) | <10s | Acceptable wait time |
| Full workflow (discovery → output) | <10 min | Reasonable for comprehensive analysis |

---

## References

### Methodology Sources

1. **Outcome-Driven Innovation (ODI)**
   - Author: Tony Ulwick
   - Book: "Jobs to be Done: Theory to Practice"
   - User's JTBD Course Material

2. **Economic Value to Customer (EVC)**
   - Source: McKinsey & Company frameworks
   - Book: "The Strategy and Tactics of Pricing" by Nagle & Holden

3. **Christensen's JTBD Theory**
   - Author: Clayton Christensen
   - Book: "Competing Against Luck"
   - Framework: Forces of Progress (Push/Pull/Anxiety/Habit)

4. **Value-Based Pricing**
   - Van Westendorp Price Sensitivity Meter
   - Gabor-Granger Direct Price Testing
   - Conjoint Analysis

### Technical References

1. **scikit-learn** - Python machine learning library
   - K-means clustering
   - Silhouette score analysis
   - Elbow method for optimal clusters

2. **pandas** - Data manipulation
   - Survey data processing
   - Opportunity scoring calculations

3. **numpy** - Numerical computing
   - Statistical calculations
   - Outlier detection (IQR method)

### Related ADRs

- ADR-002: (Future) Van Westendorp PSM Integration
- ADR-003: (Future) Conjoint Analysis Support
- ADR-004: (Future) Real-time Survey Analysis

---

## Amendment: v1.2.0 — Sub-Agent Architecture (v1.9.0: the skill runs the phases)

**Status:** Accepted
**Date:** 2026-02-27
**Author:** Luis F. Amadeo (Chief Agentic Officer)

### Context

The original v1.0 architecture specified a single sequential SKILL.md workflow. In practice, users and agents running the full 10-phase workflow accumulated ~143k tokens of context, causing:
1. Context compaction mid-session — precision loss on later phases
2. No resume capability after compaction events
3. Each phase ran in one context, so a long run had no fresh start for a phase

### Decision

The `discover` skill runs the 10 phases in the main conversation (v1.9.0; it replaced an orchestrator agent). The skill:
- Starts each phase as a fresh sub-agent with the `Agent` tool, one at a time, in the foreground (little context accumulates in the skill)
- Runs the scripts with `uv run` between the agent starts. No agent has `Bash`, so no agent runs code that the model writes (D-266, FEATURE-26)
- Persists all state to `.jtbd-market-discovery/{session}/pN.json` files (compact-resilient)
- Runs Phase 3 with 4 agents (one per job-step group), one at a time, then runs `jtbd_state.py merge-needs`. An agent that runs in the background returns in a new turn that has no tool grant from the skill (D-377)
- Runs Phase 8 after Phase 7, because segmentation reads `p7.json`
- Can be resumed: re-reading `state.json` → resuming from `current_phase`

### Architectural Changes

| Component | v1.0 | v1.2.0 |
|-----------|------|--------|
| Execution model | Sequential SKILL.md | Skill + fresh sub-agents |
| State persistence | Context window only | `.jtbd/{session}/pN.json` files |
| Context per session | ~143k tokens | ~5-10k tokens (skill only) |
| Phase 3 | Sequential | 4 agents, one at a time |
| Phases 7+8 | Sequential | Sequential: 8 after 7 |
| Agent tools | Wide | `Read, Write` (`Glob` for two), no `Bash` |
| Resume capability | None | Re-read state.json, resume from current_phase |
| Python helper | None | `scripts/jtbd_state.py` |

### Trade-offs

| Aspect | Pro | Con |
|--------|-----|-----|
| Context efficiency | 95% reduction in context usage | More complex orchestration logic |
| Fresh context | Each phase starts clean | The skill starts the 4 Phase 3 agents one at a time, so Phase 3 is slower |
| Resilience | Zero data loss across compaction events | File I/O dependency (disk required) |
| Resume | Full session resume capability | State schema must be versioned |

### New Files

- `skills/discover/SKILL.md` — the skill that runs the phases
- `scripts/jtbd_state.py` — Python helper for session state I/O
- `tests/unit/test_jtbd_state.py` — 19 unit tests for jtbd_state.py
- `tests/unit/test_orchestrator_state_integration.py` — 5 integration tests

### State Schema

```json
{
  "session_id": "2026-02-27T14:30:00",
  "job_statement": "...",
  "current_phase": 3,
  "phases_complete": [1, 2],
  "created_at": "2026-02-27T14:30:00",
  "updated_at": "2026-02-27T15:00:00"
}
```

### See Also

ADR-002: Orchestrator Architecture — detailed decisions for the phase flow

---

## Approval

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Date:** 2026-01-21
**Status:** Accepted

**Reviewers:**
- [ ] Platform Engineering Team
- [ ] Product Strategy Team
- [ ] Marketplace Maintainers

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-21 | Luis F. Amadeo | Initial ADR for v1.0 architecture |

---

**Document End**
