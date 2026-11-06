# Competitive Intelligence Plugin - Design Document

**Version:** 1.0.0 (Draft)
**Author:** Luis F. Amadeo
**Date:** 2026-01-22
**Status:** Design Phase

---

## Table of Contents

1. [Plugin Overview & Core Principles](#1-plugin-overview--core-principles)
2. [Multi-Dimensional Framework Design](#2-multi-dimensional-framework-design)
3. [Workflow & User Experience](#3-workflow--user-experience)
4. [Technical Architecture & Outputs](#4-technical-architecture--outputs)
5. [Implementation Considerations](#5-implementation-considerations)

---

## 1. Plugin Overview & Core Principles

### 1.1 Plugin Purpose

The Competitive Intelligence plugin enables product teams and business leaders to perform comprehensive, AI-native competitive analysis across the full market ecosystem. It combines multiple strategic frameworks (JTBD, Forces, Value Economics, Strategic Positioning, Technology Disruption) into a unified, context-adaptive intelligence system.

### 1.2 Target Users

**Primary Personas:**
- Product Managers validating feature decisions against competitive landscape
- Product Analysts conducting strategic market analysis
- Tech Leaders assessing technology disruption threats
- Business Strategists performing competitive assessments

**Supporting Personas:**
- Sales teams using intelligence for positioning and enablement
- Executives making strategic investment decisions

### 1.3 Core Design Principles

**1. AI-Native Intelligence**
- Primary outputs are structured data and executable code for AI tool consumption
- Human artifacts (reports, summaries) are secondary
- Designed for integration with Claude Code plugin ecosystem

**2. Context-Adaptive Analysis**
- Automatically adjusts depth, lens priority, and focus based on user context
- Feature validation ≠ Competitive response ≠ Strategic planning ≠ Ongoing monitoring
- Different contexts get different analytical emphasis

**3. Multi-Lens Strategic Framework**
- Six analytical lenses: JTBD Performance, Forces, Economic Value, Strategic Positioning, Technology Disruption, Loss/Churn
- Priority-based execution with intelligent cascading (lenses inform each other)
- Cross-validation and triangulation across lenses

**4. Confidence-Weighted Intelligence**
- Every finding has a confidence score (High / Medium / Low / Speculative)
- Multi-source triangulation to validate claims
- Transparent about gaps and uncertainty
- Recommendations weighted by confidence level

**5. Mode Separation: Objectivity vs Positioning**
- **Strategic Planning Mode:** Brutal honesty, pure objectivity, acknowledge own weaknesses
- **Sales Enablement Mode:** Positioning-focused, competitive framing, objection handling
- Never blend modes - clear declaration of which mode is active

**6. Ecosystem-Wide Coverage**
- Direct competitors + indirect competitors + substitutes + non-consumption
- Technology disruption (AI platforms as competitors)
- Adjacent players who could pivot into market
- Multi-dimensional classification (Type, JTBD Alternative, Threat Level, Stage, Market Overlap)

**7. Flexible, Non-Linear Workflow**
- Users can enter at any phase based on context
- Can iterate back for deeper analysis
- Parallelization where possible (multi-competitor analysis)
- User checkpoints prevent runaway automation

**8. Platform-Optimized**
- **Claude Code:** Full execution (Python scripts, file system, plugin integration)
- **Claude.ai Web:** Full analysis capability, generates scripts user runs elsewhere
- Maximum feature parity with context-appropriate adaptations

---

## 2. Multi-Dimensional Framework Design

### 2.1 Competitive Ecosystem Mapping

The plugin maps competitors across six dimensions to create a nuanced understanding of the competitive landscape:

**Dimension 1: Type (Market Relationship)**
- **Direct:** Same solution, same market, head-to-head competition
- **Indirect:** Different solution, same customer job (alternative approaches)
- **Substitute:** Non-product alternatives (manual processes, workarounds, spreadsheets)
- **Non-consumption:** Customers struggling without any solution (greenfield opportunity)

**Dimension 2: JTBD Alternative (How They Help)**
- **Same Approach:** Solving the job in similar ways (direct functional competition)
- **Different Approach:** Solving same job with fundamentally different method
- **Partial Solution:** Addresses subset of job steps (point solution vs platform)
- **Workaround:** Customer cobbles together multiple tools to accomplish job
- **Non-consumption:** Customer attempts job without proper tooling

**Dimension 3: Threat Level (Competitive Danger)**
- **High:** Win/loss data shows frequent losses, strong capabilities, market momentum
- **Medium:** Occasional competitive pressure, some capability gaps, moderate presence
- **Low:** Niche player, limited overlap, weak competitive performance
- Assessed using: Win/loss rates, JTBD performance, market signals, customer feedback

**Dimension 4: Stage (Market Timing)**
- **Current:** Actively competing today, established presence
- **Emerging:** Building capability, entering market, early traction
- **Potential:** Adjacent player with resources/motive to pivot into market

**Dimension 5: Market Overlap (Customer/Segment Overlap)**
- **High:** Targeting same customers, same segments, same use cases
- **Medium:** Some customer overlap, different segment emphasis
- **Low:** Minimal overlap, different ICP, tangential market presence

**Dimension 6: Technology Disruption Factor**
- Assessed separately for AI platforms and emerging technologies
- Multi-factor assessment framework (see Lens 5)

### 2.2 The Six Analytical Lenses

#### Lens 1: JTBD Performance Analysis

*"How well do solutions help customers accomplish their jobs?"*

**Framework:**
- Decompose the customer job into sequential steps (8-15 steps across 6 phases: Understand → Plan → Execute → Assess → Revise → Conclude)
- For each job step, assess competitors on:
  - **Speed:** How quickly solution completes this step (1=very slow, 5=instant/automated)
  - **Accuracy:** How correctly solution completes this step (1=many errors, 5=perfect)
- Calculate performance gaps (2+ point advantages are significant)
- Map to feature capabilities and customer outcomes

**Outputs:**
- Job step performance matrix (your product vs competitors)
- Performance gap analysis (where you lead, where you lag)
- Customer impact assessment (what gaps mean in practice)
- Feature-to-job-step mapping

**Confidence Factors:**
- Direct product access/testing = High confidence
- Customer feedback/reviews = Medium confidence
- Marketing claims only = Low confidence

#### Lens 2: Forces Analysis (Switching Dynamics)

*"What creates momentum for customers to switch solutions?"*

**Framework (Christensen's Forces):**
- **Push of the Current Situation:** Pain with existing solution driving search for alternatives
- **Pull of the New Solution:** Attraction to competitor's capabilities/promises
- **Anxiety of Change:** Concerns about switching (implementation, risk, cost, learning curve)
- **Habit of the Present:** Inertia keeping customers with current solution

**Application:**
- Assess each force's strength for each competitor
- Identify which forces favor which competitors
- Understand switching barriers and accelerators
- Map forces to specific job steps and pain points

**Outputs:**
- Forces diagram for each key competitor
- Switching barrier analysis
- Customer decision dynamics
- Churn risk assessment (if your customer base)

**Informed By:** JTBD analysis (push/pull directly relate to job performance gaps)

#### Lens 3: Economic Value Analysis

*"Who delivers the most economic value, and at what cost?"*

**Framework (Economic Value to Customer):**
- **Time Savings:** Hours saved × hourly cost
- **Error Reduction:** Errors avoided × cost per error
- **Revenue Impact:** Additional revenue × margin
- **Risk Reduction:** Probability reduction × cost if risk occurs

**Analysis:**
- Quantify value creation for each competitor
- Compare value delivered per job step
- Assess pricing vs value relationship
- Calculate customer ROI for each solution

**Outputs:**
- Economic value comparison ($/month or $/year)
- Value-to-price ratio analysis
- ROI comparison matrix
- Pricing competitiveness assessment

**Informed By:** JTBD analysis (value derives from job performance improvements)

#### Lens 4: Strategic Positioning Analysis

*"How do competitors position in the market, and what are their moats?"*

**Framework:**
- **Business Model:** Pricing, packaging, revenue model, go-to-market strategy
- **Target Market:** ICP, segments, company size, industry focus
- **Product Strategy:** Platform vs point solution, integration approach, innovation posture
- **Competitive Moats:** Sustainable advantages (network effects, switching costs, brand, technology, scale)
- **Strategic Vulnerabilities:** Weaknesses in strategy, dependencies, execution risks

**Analysis:**
- How do competitors differentiate?
- What are their defensible advantages?
- Where are strategic misalignments?
- What's their theory of winning?

**Outputs:**
- Business model comparison
- Market positioning map
- Moat assessment (which are real, which are claimed)
- Strategic vulnerability identification

#### Lens 5: Technology Disruption Assessment

*"Can AI platforms or emerging technologies disrupt this market?"*

**Multi-Factor Assessment Framework:**

**Factor 1: Capability Maturity**
- Can AI/technology do this job today? (Current state)
- Can it do this job well in 12-24 months? (Emerging state)
- Could it eventually make this category obsolete? (Structural risk)

**Factor 2: Economic Feasibility**
- Is AI/tech solution more cost-effective than existing products?
- What's the total cost of ownership (API costs, infrastructure, maintenance)?
- Does economics favor disruption or sustain incumbent advantage?

**Factor 3: Adoption Barriers**
- Technical barriers (integration complexity, reliability, security)
- Organizational barriers (change management, trust, compliance)
- Workflow barriers (fits existing processes vs requires reimagining)

**Factor 4: Timing**
- How quickly could disruption occur?
- What are leading indicators of adoption?
- What's the window for incumbent response?

**Specific Assessments:**

**A. Job Replaceability**
- Which job steps can AI platforms do directly?
- Example: "Claude, manage leave approvals" vs dedicated software

**B. Feature Commoditization**
- Which features become trivial with AI?
- What remains differentiating?

**C. DIY Enablement**
- Can customers build their own with AI + basic tools?
- What's the effort vs buying?

**D. Unbundling Risk**
- Can AI do specific job steps better than integrated product?
- Does integration remain valuable?

**E. Integration Bypass**
- Can AI eliminate need for connectors/middleware?
- Does AI make integration infrastructure obsolete?

**Outputs:**
- Disruption risk score (High / Medium / Low) with timeline
- Job-level vulnerability mapping
- Defensible vs at-risk capabilities
- Strategic recommendations for AI era

#### Lens 6: Loss/Churn Analysis (if data available)

*"Why do we actually lose, and what does reality tell us?"*

**Framework:**
- Analyze deals lost to each competitor (competitive losses)
- Analyze customers who churned to each competitor (competitive churn)
- Analyze non-competitive losses/churn (reveals internal gaps)
- Cross-validate all other lens findings with actual customer decisions

**Analysis:**
- Do loss reasons align with JTBD performance gaps?
- Do customers cite the features/capabilities competitors claim?
- Are there patterns revealing systemic issues?
- Do losses validate or contradict strategic assumptions?

**Critical Role:**
- **Reality Check:** Loss/churn data trumps marketing claims and perceptions
- **Validation:** If customers don't choose based on claimed advantages, are they real advantages?
- **Gap Identification:** Non-competitive losses reveal issues independent of competition

**Outputs:**
- Loss frequency and reasons by competitor
- Churn frequency and reasons by competitor
- Pattern analysis (what causes most damage)
- Cross-lens validation (do findings align with customer reality?)

### 2.3 Context-Based Lens Prioritization

Different contexts emphasize different lenses:

**Feature Validation Context:**
- **Primary:** JTBD Performance (does competitor do this job better?)
- **Primary:** Economic Value (what's the ROI of building this?)
- **Secondary:** Technology Disruption (will AI make this irrelevant?)
- **Secondary:** Loss/Churn (do we lose because we lack this?)

**Competitive Response Context:**
- **Primary:** Strategic Positioning (what's their move and intent?)
- **Primary:** Forces Analysis (why are customers switching?)
- **Primary:** SWOT (immediate threats and opportunities)
- **Secondary:** JTBD Performance (where do they now lead?)

**Strategic Planning Context:**
- **Equal Weight:** All lenses executed comprehensively
- **Focus:** Synthesis and integration across lenses
- **Depth:** Comprehensive assessment

**Ongoing Monitoring Context:**
- **Primary:** Loss/Churn (what's changing in win rates?)
- **Secondary:** JTBD Performance (are they improving?)
- **Secondary:** Technology Disruption (emerging threats?)
- **Low:** Other lenses (check for major changes only)

### 2.4 Intelligent Cascading (How Lenses Inform Each Other)

**Dependencies:**
1. **JTBD Analysis** runs early → Informs Forces (push/pull tied to job performance) → Informs Value (quantifies job improvements)
2. **Loss/Churn Data** validates everything → Reality-checks all lens findings
3. **Strategic Positioning** provides context for interpreting other lenses
4. **Technology Disruption** examined after understanding current competitive dynamics

**Cross-Validation:**
- When lenses agree → High confidence in findings
- When lenses contradict → Investigate why, reveals insights
- When loss/churn contradicts other lenses → Prioritize customer reality

---

## 3. Workflow & User Experience

### 3.1 Invocation Model (Hybrid Commands)

**Primary Command:**
```
/competitive-intelligence:competitive-intelligence
```
Launches guided dialogue to determine context, scope, and approach

**Specialized Commands (as context becomes understood):**
```
/competitive-intelligence:discover          # Full ecosystem mapping
/competitive-intelligence:analyze [name]    # Deep dive on specific competitor
/competitive-intelligence:validate [feature] # Feature validation context
/competitive-intelligence:respond [threat]   # Competitive response context
/competitive-intelligence:monitor           # Ongoing monitoring update
```

**Contextual Suggestions:**
- Plugin detects when competitive intel might be valuable
- Example: User discussing feature → "Want competitive analysis for this feature?"
- Never intrusive, always optional

### 3.2 The 6-Phase Adaptive Workflow

**Design Philosophy:**
- **Flexible Entry:** Can start at any phase based on context
- **Non-Linear:** Can iterate back for deeper analysis
- **Checkpoint-Driven:** User validates before proceeding
- **Parallelizable:** Multiple activities run concurrently when possible

#### Phase 1: Context Discovery & Scoping

**Purpose:** Understand what the user needs and configure the analysis appropriately

**Key Questions (Socratic Approach):**

1. What triggered this analysis?
2. What's your scope?
3. What mode do you need? (Strategic Planning vs Sales Enablement)
4. What's your timeline?
5. What data do you have?

**Adaptive Configuration:**
Based on responses, plugin determines:
- Which lenses to prioritize
- Depth level (quick scan / standard / comprehensive)
- Deliverable priorities (code + data / reports / both)

**Output:** Analysis plan with estimated approach

**Checkpoint:** "Here's how I'll approach this analysis. Does this match what you need?"

#### Phase 2: Competitive Ecosystem Mapping

**Purpose:** Map the competitive landscape with multi-dimensional classification

**Activities:**

**Step 1: Competitor Identification**
- Start with user-provided competitors or discover via research
- Include technology disruption threats

**Step 2: Multi-Dimensional Classification**
For each competitor: Type, JTBD Alternative, Threat Level, Stage, Market Overlap, Technology Disruption Factor

**Step 3: Tiered Prioritization**
- High threat (deep dive)
- Medium threat (standard analysis)
- Low threat (quick scan)

**Checkpoint:** "Does this ecosystem map look right?"

#### Phase 3: Intelligence Gathering & Validation

**Purpose:** Collect, validate, and triangulate competitive data

**Activities (parallelized):**

**A. Data Collection**
- User uploads (files, existing analyses)
- Web research
- Plugin integration (JTBD, financial data)

**B. Multi-Source Triangulation**
- Cross-reference claims
- Flag contradictions
- Identify unverified claims

**C. Confidence Scoring**
- High / Medium / Low / Speculative
- Track data quality, recency, credibility

**D. Gap Analysis**
- Critical / Important / Nice-to-have

**Checkpoint:** "Here's what I found and confidence levels. Proceed or gather more?"

#### Phase 4: Multi-Lens Analysis

**Purpose:** Execute comprehensive analysis through context-appropriate lenses

**Execution Model:**
1. Lens prioritization (based on context)
2. Intelligent cascading (respect dependencies)
3. Parallel execution (multiple competitors)
4. Cross-validation (consistency checks)

**Per-Lens Outputs:** Structured findings for each lens

**Checkpoint:** "Here are the multi-lens findings. Any areas to explore deeper?"

#### Phase 5: Synthesis & Strategic Assessment

**Purpose:** Integrate insights, assess implications, generate recommendations

**Activities:**

**A. SWOT Analysis (Evidence-Based)**
- Competitor SWOT (with evidence)
- Your SWOT relative to competitor

**B. Strategic Implications**
- Answer context-specific questions
- Product strategy, GTM, risks, opportunities

**C. Confidence-Weighted Recommendations**
- High confidence (execute now)
- Medium confidence (strategic bets)
- Low confidence (research needed)

**D. Mode-Appropriate Framing**
- Strategic Planning: Objective, honest
- Sales Enablement: Positioning-focused

**Checkpoint:** "Does this assessment answer your questions?"

#### Phase 6: Deliverable Generation

**Purpose:** Create AI-native and human artifacts

**Primary Deliverables (AI-Native):**
1. Modular structured data (JSON/YAML)
2. Executable analysis scripts (Python)
3. Integration artifacts

**Secondary Deliverables (Human Collaboration):**
4. Spreadsheets/reports
5. Documentation

**Deliverable Customization:** User selects what they need

**Platform Adaptations:**
- Claude Code: Saves files, executes scripts, commits to git
- Claude.ai Web: Generates downloadable artifacts, provides instructions

**Checkpoint:** "Here are your deliverables. Need anything else?"

### 3.3 Workflow Flexibility Features

**Entry Point Flexibility:**
- Can start at any phase based on available context/data

**Iteration Patterns:**
- Can return to earlier phases for deeper analysis
- Can pause and resume (if session persistence available)

**Parallelization Opportunities:**
- Multiple competitors analyzed simultaneously
- Multiple deliverable types generated concurrently

**User Control:**
- Every checkpoint offers: Proceed / Go deeper / Change direction / Generate deliverables

### 3.4 Conversational Handoffs (Plugin Integration)

**Recognition Patterns:**
- Plugin detects other plugin outputs
- "I see `jtbd-analysis.json`. Want me to use it?"

**Suggestion Patterns:**
- Recommend complementary analyses
- "To strengthen this, consider running `/jtbd:discover` first"

**Handoff Instructions:**
- Provide clear integration guidance for downstream plugins

---

## 4. Technical Architecture & Outputs

### 4.1 Modular Output Schema

**Primary AI-Native Outputs:**

```
/output/competitive-intelligence/[timestamp]/
  ├── competitive-ecosystem.json       # Multi-dimensional competitor map
  ├── jtbd-analysis.json               # Job step performance comparison
  ├── forces-analysis.json             # Switching dynamics per competitor
  ├── value-analysis.json              # Economic value comparison
  ├── strategic-analysis.json          # Business model, positioning, moats
  ├── technology-disruption.json       # AI/tech disruption assessment
  ├── loss-churn-analysis.json         # Win/loss patterns (if available)
  ├── swot-analysis.json               # Evidence-based SWOT
  ├── recommendations.json             # Confidence-weighted actions
  └── metadata.json                    # Analysis config, sources, confidence
```

**Schema Standards:**
- Consistent structure across sessions
- Versioned schemas for backward compatibility
- Plugin consumption guidelines embedded
- Cross-references between modules

### 4.2 Executable Analysis Scripts

```
/scripts/competitive-intelligence/[timestamp]/
  ├── value_calculation.py             # Economic value models
  ├── jtbd_comparison.py               # Performance gap analysis
  ├── statistical_analysis.py          # Significance testing
  ├── visualization.py                 # Generate charts from data
  ├── update_pipeline.py               # Refresh analysis with new data
  ├── requirements.txt                 # Dependencies
  └── README.md                        # Usage instructions
```

**Jupyter Notebooks** (for exploration):
```
  ├── competitive_analysis.ipynb       # Interactive exploration
  └── scenario_modeling.ipynb          # What-if analysis
```

### 4.3 Integration Architecture

**Loose Coupling:**
- Plugins recognize each other's schemas
- No hard dependencies
- Everything works standalone

**Conversational Handoffs:**
- Suggest integrations
- Provide clear instructions
- Manual or automated orchestration

**Schema Contracts:**
- Well-documented interfaces
- Version compatibility
- Consumption examples

### 4.4 Platform Adaptations

**Claude Code:**
- Full Python execution
- File system integration
- Direct plugin data passing
- Git commit artifacts

**Claude.ai Web:**
- Generate scripts (user runs elsewhere)
- Downloadable artifacts
- Copy-paste data transfer
- Clear usage instructions

### 4.5 Data Quality & Validation

**Confidence Scoring:**
- High / Medium / Low / Speculative
- Applied to all findings

**Multi-Source Triangulation:**
- Cross-reference claims
- Flag contradictions
- Validate with multiple sources

**Source Transparency:**
- Always cite sources
- Note data age
- Track credibility

**Sensitive Data Handling:**
- Warnings about confidentiality
- Best practices reminders
- No API keys in outputs

### 4.6 Persistence & Historical Tracking

**MVP Approach (Stateless):**
- Version-controllable outputs
- Timestamped modular files
- User manages history (git, etc.)

**The graph (STORY-88):**
- Each run ends with `ci_graph.py ingest`. The files of the run become pages in `docs/competitive-intelligence/`, a bundle of the brain standard. Git keeps the bundle.
- Only `scripts/ci_graph.py` writes the bundle. A PostToolUse hook runs `regen` and both checks after each write.
- A later run reads a file of an earlier run with `ci_graph.py view`.
- The skills `setup`, `learn` and `ask` make the graph, confirm the pages, and answer questions from it.

**Future Enhancement:**
- Native historical tracking
- Trend analysis
- Prediction accuracy tracking

---

## 5. Implementation Considerations

### 5.1 Phase 1 MVP Scope

**Core Capabilities:**
1. Context discovery and scoping
2. Ecosystem mapping (6 dimensions)
3. Intelligence gathering (file-based + web research)
4. Multi-lens analysis (all 6 lenses)
5. SWOT and strategic assessment
6. Modular JSON outputs
7. Basic Python scripts

**Deferred to Future Phases:**
- MCP integrations for CI platforms
- Native historical tracking
- Advanced statistical models
- Automated competitive monitoring

### 5.2 Technology Stack

**Core:**
- Python 3.11 (pinned via `.python-version`) for analysis scripts. See pyproject.toml for exact dependency requirements.
- JSON/YAML for structured outputs
- Markdown for documentation

**Analysis Libraries:**
- pandas (data manipulation)
- numpy (numerical calculations)
- matplotlib/seaborn (visualization)
- scikit-learn (clustering, if JTBD segmentation)

**Web Research:**
- WebFetch tool for competitor websites
- WebSearch tool for market research

**Integration:**
- File system I/O for Claude Code
- Copy-paste for Claude.ai Web
- Git for version control

### 5.3 Quality Gates

**Analysis Quality:**
- Minimum confidence thresholds
- Multi-source validation
- Cross-lens consistency checks

**Output Quality:**
- Schema validation
- Script executability testing
- Documentation completeness

**User Experience:**
- Checkpoint effectiveness
- Context adaptation accuracy
- Deliverable relevance

### 5.4 Testing Strategy

**Unit Tests:**
- Schema validation
- Analysis calculations
- Confidence scoring

**Integration Tests:**
- Multi-lens cascading
- Plugin handoffs
- File I/O operations

**End-to-End Tests:**
- Full workflow scenarios
- Context adaptation
- Deliverable generation

**User Acceptance Tests:**
- Real competitor analysis
- Validate with product teams
- Refine based on feedback

### 5.5 Documentation Requirements

**User-Facing:**
- skills/competitive-intelligence/SKILL.md (the workflow of the full run)
- README.md (quick start, installation)
- Examples (complete end-to-end scenarios)
- Templates (input formats, data structures)

**Developer-Facing:**
- DESIGN.md (this document)
- ADR-001 (architecture decisions)
- Schema documentation
- API/integration guide

**Reference Material:**
- Framework guides (JTBD, Forces, EVC, etc.)
- Methodology best practices
- Confidence scoring guidelines
- Data source recommendations

### 5.6 Success Metrics

**Adoption:**
- Plugin invocations per week
- Repeat usage rate
- Cross-plugin integration usage

**Quality:**
- Confidence score distribution
- User validation rate (checkpoints)
- Deliverable usage rate

**Impact:**
- Feature decisions influenced
- Competitive responses informed
- Strategic plans incorporating findings

### 5.7 Future Enhancements (Post-MVP)

**v1.1: Enhanced Data Sources**
- MCP integrations (Klue, Crayon, etc.)
- Automated competitor monitoring
- News/announcement tracking

**v1.2: Advanced Analytics**
- Predictive models
- Trend analysis
- Market simulation

**v1.3: Historical Intelligence**
- Native tracking system
- Comparison over time
- Prediction accuracy tracking

**v2.0: AI-Powered Automation**
- Auto-detect competitive moves
- Proactive threat alerts
- Continuous monitoring mode

---

## Appendices

### Appendix A: Key Decisions & Rationale

**Decision 1: AI-Native First, Human Artifacts Second**
- Rationale: Enables product development workflows, not just strategy reports
- Trade-off: More complex output structure

**Decision 2: Context-Adaptive vs Fixed Depth**
- Rationale: Different triggers need different analyses
- Trade-off: More complex workflow logic

**Decision 3: Priority-Based Lenses with Cascading**
- Rationale: Efficiency + accuracy (lenses inform each other)
- Trade-off: Can't run all lenses fully in parallel

**Decision 4: Modular vs Unified Output Schema**
- Rationale: Granular sharing, standardized consumption
- Trade-off: More files to manage

**Decision 5: Stateless MVP with Version Control**
- Rationale: Simplicity, leverage existing tools
- Trade-off: No native historical comparison

**Decision 6: Hybrid Invocation (Primary + Specialized)**
- Rationale: Easy entry, power-user efficiency
- Trade-off: More commands to learn

### Appendix B: Schema Definitions (Detailed)

*See separate schema documentation files in `/docs/schemas/`*

### Appendix C: Integration Patterns

*See separate integration guide in `/docs/INTEGRATION_GUIDE.md`*

### Appendix D: Methodology References

**JTBD & ODI:**
- Tony Ulwick's Outcome-Driven Innovation
- Clayton Christensen's Jobs To Be Done Theory

**Switching Dynamics:**
- Bob Moesta's Forces of Progress

**Economic Value:**
- McKinsey EVC Framework

**Strategic Analysis:**
- Hamilton Helmer's 7 Powers
- Porter's Five Forces (adapted)

**Technology Disruption:**
- Christensen's Disruption Theory
- Platform Economics (Parker, Van Alstyne)

---

**Document Status:** Design Complete - Ready for Implementation Planning

**Next Steps:**
1. Create Phase 1 Implementation Plan
2. Setup Quality Gates
3. Execute implementation with parallel workstreams
4. Iterate based on testing and feedback

---

**Document History:**
- 2026-01-22: Initial design based on brainstorming session
