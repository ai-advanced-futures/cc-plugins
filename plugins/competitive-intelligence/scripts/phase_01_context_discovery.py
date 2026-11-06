"""
Competitive Intelligence Plugin - Phase 1: Context Discovery

Socratic dialogue to understand user needs and configure analysis adaptively.

Key Features:
- Context classification (4 triggers: feature decision, competitor response,
  strategic planning, monitoring)
- Mode selection (Strategic Planning vs Sales Enablement)
- Adaptive configuration based on context
- Integration with workflow engine

Context Dimensions:
- Trigger: What prompted this analysis
- Mode: Strategic (objective) vs Sales (positioning)
- Scope: Single competitor, segment, full market, or specific feature
- Timeline: Immediate, quarterly, annual
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisTrigger(Enum):
    """What triggered this competitive intelligence analysis."""
    FEATURE_DECISION = "feature_decision"
    COMPETITOR_RESPONSE = "competitor_response"
    STRATEGIC_PLANNING = "strategic_planning"
    MONITORING = "monitoring"


class AnalysisMode(Enum):
    """
    Analysis mode determines objectivity vs positioning focus.

    STRATEGIC_PLANNING: Objective analysis, all strengths/weaknesses
    SALES_ENABLEMENT: Competitive positioning, emphasize advantages
    """
    STRATEGIC_PLANNING = "strategic_planning"
    SALES_ENABLEMENT = "sales_enablement"


class AnalysisScope(Enum):
    """Scope of competitive analysis."""
    SINGLE_COMPETITOR = "single_competitor"
    COMPETITOR_SEGMENT = "competitor_segment"
    FULL_MARKET = "full_market"
    SPECIFIC_FEATURE = "specific_feature"


class Timeline(Enum):
    """Timeline for analysis."""
    IMMEDIATE = "immediate"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


@dataclass
class AnalysisContext:
    """
    Complete context for competitive intelligence analysis.

    Required fields determine analysis depth, breadth, and lens priority.
    Optional fields provide additional specificity.
    """
    trigger: AnalysisTrigger
    mode: AnalysisMode
    scope: AnalysisScope
    timeline: Timeline

    # Optional fields for specificity
    feature_name: Optional[str] = None
    competitors: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)


class ContextDiscovery:
    """
    Interactive context discovery through Socratic dialogue.

    Guides user through questions to understand:
    - What triggered the analysis
    - What mode (strategic vs sales)
    - What scope (competitor, segment, market, feature)
    - What timeline (immediate, quarterly, annual)

    Builds AnalysisContext and updates workflow engine.
    """

    def __init__(self, engine):
        """
        Initialize context discovery.

        Args:
            engine: WorkflowEngine instance to update with context
        """
        self.engine = engine
        self.context = None
        self._trigger = None
        self._mode = None
        self._scope = None
        self._timeline = None

    def _set_trigger(self, trigger: AnalysisTrigger):
        """Set trigger (simulates user selection)."""
        self._trigger = trigger
        if self.context is None:
            self.context = AnalysisContext(
                trigger=trigger,
                mode=AnalysisMode.STRATEGIC_PLANNING,  # default
                scope=AnalysisScope.SINGLE_COMPETITOR,  # default
                timeline=Timeline.IMMEDIATE  # default
            )
        else:
            self.context.trigger = trigger

    def _set_mode(self, mode: AnalysisMode):
        """Set analysis mode (simulates user selection)."""
        self._mode = mode
        if self.context is None:
            self.context = AnalysisContext(
                trigger=AnalysisTrigger.FEATURE_DECISION,  # default
                mode=mode,
                scope=AnalysisScope.SINGLE_COMPETITOR,  # default
                timeline=Timeline.IMMEDIATE  # default
            )
        else:
            self.context.mode = mode

    def _set_scope(self, scope: AnalysisScope):
        """Set analysis scope (simulates user selection)."""
        self._scope = scope
        if self.context is None:
            self.context = AnalysisContext(
                trigger=AnalysisTrigger.FEATURE_DECISION,  # default
                mode=AnalysisMode.STRATEGIC_PLANNING,  # default
                scope=scope,
                timeline=Timeline.IMMEDIATE  # default
            )
        else:
            self.context.scope = scope

    def _set_timeline(self, timeline: Timeline):
        """Set timeline (simulates user selection)."""
        self._timeline = timeline
        if self.context is None:
            self.context = AnalysisContext(
                trigger=AnalysisTrigger.FEATURE_DECISION,  # default
                mode=AnalysisMode.STRATEGIC_PLANNING,  # default
                scope=AnalysisScope.SINGLE_COMPETITOR,  # default
                timeline=timeline
            )
        else:
            self.context.timeline = timeline

    def get_context(self) -> AnalysisContext:
        """
        Get the discovered context.

        Returns:
            AnalysisContext with user selections
        """
        return self.context

    def run_discovery(self) -> AnalysisContext:
        """
        Run the full discovery flow (would use AskUserQuestion in real implementation).

        Returns:
            Completed AnalysisContext
        """
        # In real implementation, this would use AskUserQuestion tool
        # For now, returns default context if none set
        if self.context is None:
            self.context = AnalysisContext(
                trigger=AnalysisTrigger.FEATURE_DECISION,
                mode=AnalysisMode.STRATEGIC_PLANNING,
                scope=AnalysisScope.SINGLE_COMPETITOR,
                timeline=Timeline.IMMEDIATE
            )

        # Update engine context
        self.engine.update_context({
            "trigger": self.context.trigger.value,
            "analysis_mode": self.context.mode.value,
            "scope": self.context.scope.value,
            "timeline": self.context.timeline.value
        })

        return self.context


def classify_context(context: AnalysisContext) -> Dict[str, Any]:
    """
    Classify context to determine analysis characteristics.

    Determines:
    - Depth: How deep to analyze (focused, deep, comprehensive, surface)
    - Breadth: How wide to analyze (narrow, moderate, wide)
    - Urgency: How urgent (high, medium, low)
    - Lens priority: Which lenses to prioritize

    Args:
        context: AnalysisContext to classify

    Returns:
        Dict with classification results
    """
    classification = {}

    # Depth based on trigger
    depth_map = {
        AnalysisTrigger.FEATURE_DECISION: "focused",
        AnalysisTrigger.COMPETITOR_RESPONSE: "deep",
        AnalysisTrigger.STRATEGIC_PLANNING: "comprehensive",
        AnalysisTrigger.MONITORING: "surface"
    }
    classification["depth"] = depth_map[context.trigger]

    # Breadth based on scope
    breadth_map = {
        AnalysisScope.SPECIFIC_FEATURE: "narrow",
        AnalysisScope.SINGLE_COMPETITOR: "narrow",
        AnalysisScope.COMPETITOR_SEGMENT: "moderate",
        AnalysisScope.FULL_MARKET: "wide"
    }
    classification["breadth"] = breadth_map[context.scope]

    # Urgency based on timeline
    urgency_map = {
        Timeline.IMMEDIATE: "high",
        Timeline.QUARTERLY: "medium",
        Timeline.ANNUAL: "low"
    }
    classification["urgency"] = urgency_map[context.timeline]

    # Lens priority based on trigger
    lens_priority_map = {
        AnalysisTrigger.FEATURE_DECISION: [
            "jtbd_performance",
            "economic_value",
            "forces"
        ],
        AnalysisTrigger.COMPETITOR_RESPONSE: [
            "forces",
            "strategic_positioning",
            "jtbd_performance",
            "economic_value"
        ],
        AnalysisTrigger.STRATEGIC_PLANNING: [
            "strategic_positioning",
            "technology_disruption",
            "jtbd_performance",
            "economic_value",
            "forces",
            "loss_churn"
        ],
        AnalysisTrigger.MONITORING: [
            "strategic_positioning",
            "technology_disruption"
        ]
    }
    classification["lens_priority"] = lens_priority_map[context.trigger]

    # Frequency for monitoring
    if context.trigger == AnalysisTrigger.MONITORING:
        classification["frequency"] = "recurring"

    return classification


def generate_adaptive_config(context: AnalysisContext) -> Dict[str, Any]:
    """
    Generate adaptive configuration based on context.

    Determines:
    - Which lenses to use
    - Which phases to execute
    - Depth of analysis per lens
    - Output formats
    - Mode-specific settings

    Args:
        context: AnalysisContext

    Returns:
        Configuration dict for the workflow
    """
    classification = classify_context(context)

    config = {
        "analysis_mode": context.mode.value,
        "lenses": classification["lens_priority"],
        "phases": [
            "context_discovery",
            "ecosystem_mapping",
            "intelligence_gathering",
            "multi_lens_analysis",
            "synthesis",
            "deliverable_generation"
        ]
    }

    # Mode-specific settings
    if context.mode == AnalysisMode.STRATEGIC_PLANNING:
        config["objectivity"] = "high"
        config["include_weaknesses"] = True
        config["include_threats"] = True
        config["framing"] = "objective_assessment"
    else:  # SALES_ENABLEMENT
        config["objectivity"] = "moderate"
        config["positioning_focus"] = True
        config["framing"] = "competitive_advantage"
        config["include_weaknesses"] = False  # Only where relevant to positioning

    # Depth settings
    if classification["depth"] == "comprehensive":
        config["analysis_depth"] = "full"
        config["all_lenses"] = True
    elif classification["depth"] == "deep":
        config["analysis_depth"] = "detailed"
        config["lens_count"] = 4
    elif classification["depth"] == "focused":
        config["analysis_depth"] = "targeted"
        config["lens_count"] = 2
    else:  # surface
        config["analysis_depth"] = "overview"
        config["lens_count"] = 2

    # Timeline settings
    config["timeline"] = context.timeline.value
    config["urgency"] = classification["urgency"]

    return config


def discover_context(engine, user_inputs: Dict[str, str]) -> AnalysisContext:
    """
    Convenience function to discover context from user inputs.

    Args:
        engine: WorkflowEngine instance
        user_inputs: Dict with trigger, analysis_mode, scope, timeline

    Returns:
        AnalysisContext
    """
    discovery = ContextDiscovery(engine)

    # Map string inputs to enums
    trigger_map = {
        "feature_decision": AnalysisTrigger.FEATURE_DECISION,
        "competitor_response": AnalysisTrigger.COMPETITOR_RESPONSE,
        "strategic_planning": AnalysisTrigger.STRATEGIC_PLANNING,
        "monitoring": AnalysisTrigger.MONITORING
    }

    mode_map = {
        "strategic_planning": AnalysisMode.STRATEGIC_PLANNING,
        "sales_enablement": AnalysisMode.SALES_ENABLEMENT
    }

    scope_map = {
        "single_competitor": AnalysisScope.SINGLE_COMPETITOR,
        "competitor_segment": AnalysisScope.COMPETITOR_SEGMENT,
        "full_market": AnalysisScope.FULL_MARKET,
        "specific_feature": AnalysisScope.SPECIFIC_FEATURE
    }

    timeline_map = {
        "immediate": Timeline.IMMEDIATE,
        "quarterly": Timeline.QUARTERLY,
        "annual": Timeline.ANNUAL
    }

    # Set context from inputs
    discovery._set_trigger(trigger_map[user_inputs["trigger"]])
    discovery._set_mode(mode_map[user_inputs["analysis_mode"]])
    discovery._set_scope(scope_map[user_inputs["scope"]])
    discovery._set_timeline(timeline_map[user_inputs["timeline"]])

    return discovery.get_context()


# Context validation helpers

def validate_context(context: AnalysisContext) -> tuple[bool, Optional[str]]:
    """
    Validate that context has all required fields.

    Args:
        context: AnalysisContext to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if context.trigger is None:
        return False, "Trigger is required"

    if context.mode is None:
        return False, "Mode is required"

    if context.scope is None:
        return False, "Scope is required"

    if context.timeline is None:
        return False, "Timeline is required"

    # Mode validation: strategic planning vs sales should be clear
    if context.mode == AnalysisMode.SALES_ENABLEMENT:
        # Sales mode requires specific scope
        if context.scope == AnalysisScope.FULL_MARKET:
            return False, "Sales enablement should focus on specific competitors, not full market"

    return True, None


def get_suggested_competitors(context: AnalysisContext) -> List[str]:
    """
    Suggest competitors based on context.

    In real implementation, this would query databases or use ML.
    For now, returns empty list (to be populated in Phase 2).

    Args:
        context: AnalysisContext

    Returns:
        List of suggested competitor names
    """
    # Placeholder - real implementation would query data sources
    return []
