"""
Competitive Intelligence Plugin - Workflow Engine

Phase management system for the 6-phase competitive intelligence workflow:
1. Context Discovery & Scoping
2. Competitive Ecosystem Mapping
3. Intelligence Gathering & Validation
4. Multi-Lens Analysis
5. Synthesis & Strategic Assessment
6. Deliverable Generation

Features:
- State machine for phase transitions
- Checkpoint system for validation
- Flexible entry points (start at any phase)
- Iteration support (go back to earlier phases)
- State persistence (snapshot/restore)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class Phase(Enum):
    """Six phases of competitive intelligence workflow."""
    CONTEXT_DISCOVERY = 1
    ECOSYSTEM_MAPPING = 2
    INTELLIGENCE_GATHERING = 3
    MULTI_LENS_ANALYSIS = 4
    SYNTHESIS = 5
    DELIVERABLE_GENERATION = 6


@dataclass
class WorkflowState:
    """
    Current state of the workflow.

    Attributes:
        current_phase: The phase currently being executed
        context: User context (trigger, analysis_mode, scope, timeline, etc.)
        data: Data accumulated through the workflow
        phase_history: List of phases visited (for iteration tracking)
        checkpoints_passed: List of checkpoint names that passed
    """
    current_phase: Phase
    context: Dict[str, Any]
    data: Dict[str, Any]
    phase_history: List[Phase] = field(default_factory=list)
    checkpoints_passed: List[str] = field(default_factory=list)


class InvalidTransitionError(Exception):
    """Raised when an invalid phase transition is attempted."""
    pass


class CheckpointFailedError(Exception):
    """Raised when a checkpoint validation fails."""
    pass


class WorkflowEngine:
    """
    Core workflow engine managing phase transitions and state.

    The engine supports:
    - Linear progression through phases
    - Flexible entry at any phase
    - Iteration back to earlier phases
    - Checkpoint validation
    - State persistence
    """

    def __init__(
        self,
        entry_phase: Phase = Phase.CONTEXT_DISCOVERY,
        context: Optional[Dict[str, Any]] = None,
        state: Optional[WorkflowState] = None
    ):
        """
        Initialize workflow engine.

        Args:
            entry_phase: Phase to start at (default: Phase 1)
            context: Initial context dict (default: empty)
            state: Existing state to resume from (overrides entry_phase and context)
        """
        if state is not None:
            self.state = state
        else:
            self.state = WorkflowState(
                current_phase=entry_phase,
                context=context or {},
                data={}
            )

    def transition_to(self, target_phase: Phase, iteration: bool = False) -> None:
        """
        Transition to a different phase.

        Args:
            target_phase: Phase to transition to
            iteration: If True, this is a backward iteration (refinement)

        Raises:
            InvalidTransitionError: If transition is invalid (currently not enforced)
        """
        # No-op if already in target phase
        if self.state.current_phase == target_phase:
            return

        # Record current phase in history before transitioning
        if self.state.current_phase not in self.state.phase_history:
            self.state.phase_history.append(self.state.current_phase)
        elif iteration:
            # If iterating back, add the phase we're leaving to history
            self.state.phase_history.append(self.state.current_phase)

        # Transition to new phase
        self.state.current_phase = target_phase

    def run_checkpoint(
        self,
        checkpoint_name: str,
        validator: Callable[[WorkflowState], Tuple[bool, str]]
    ) -> bool:
        """
        Run a checkpoint validation.

        Args:
            checkpoint_name: Name of the checkpoint
            validator: Function that validates state and returns (passed, message)

        Returns:
            True if checkpoint passed

        Raises:
            CheckpointFailedError: If checkpoint fails
        """
        passed, message = validator(self.state)

        if passed:
            self.state.checkpoints_passed.append(checkpoint_name)
            return True
        else:
            raise CheckpointFailedError(
                f"Checkpoint '{checkpoint_name}' failed: {message}"
            )

    def get_phase_requirements(self, phase: Phase) -> List[str]:
        """
        Get list of required data/context keys for a phase.

        Args:
            phase: Phase to get requirements for

        Returns:
            List of required keys
        """
        requirements = {
            Phase.CONTEXT_DISCOVERY: ["context", "trigger"],
            Phase.ECOSYSTEM_MAPPING: ["context"],  # Identifies competitors
            Phase.INTELLIGENCE_GATHERING: ["context", "competitors"],  # Needs competitors from Phase 2
            Phase.MULTI_LENS_ANALYSIS: ["competitors", "intelligence"],
            Phase.SYNTHESIS: ["analysis"],
            Phase.DELIVERABLE_GENERATION: ["recommendations"]
        }

        # Return requirements or empty list if phase not found
        return requirements.get(phase, [])

    def can_execute_phase(self, phase: Phase) -> bool:
        """
        Check if a phase has required data to execute.

        Args:
            phase: Phase to check

        Returns:
            True if phase can be executed with current state
        """
        requirements = self.get_phase_requirements(phase)

        # Special case: Phase 1 always executable
        if phase == Phase.CONTEXT_DISCOVERY:
            return True

        # Special case: Phase 2 executable if context has been discovered (Phase 1 complete)
        # Note: get_phase_requirements() is advisory; full prerequisite validation happens
        # via agents reading output files from disk (e.g., competitive-context.json).
        if phase == Phase.ECOSYSTEM_MAPPING:
            return len(self.state.context) > 0

        # Check if all requirements are met
        for req in requirements:
            # Check in both context and data
            if req not in self.state.context and req not in self.state.data:
                return False

        return True

    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get current state as a serializable dict.

        Returns:
            Dict representation of current state
        """
        snapshot = {
            "current_phase": self.state.current_phase.name,
            "context": self.state.context.copy(),
            "data": self.state.data.copy(),
            "phase_history": [p.name for p in self.state.phase_history],
            "checkpoints_passed": self.state.checkpoints_passed.copy()
        }
        return snapshot

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> 'WorkflowEngine':
        """
        Restore engine from a state snapshot.

        Args:
            snapshot: Dict created by get_state_snapshot()

        Returns:
            New WorkflowEngine with restored state
        """
        state = WorkflowState(
            current_phase=Phase[snapshot["current_phase"]],
            context=snapshot["context"],
            data=snapshot["data"],
            phase_history=[Phase[p] for p in snapshot["phase_history"]],
            checkpoints_passed=snapshot["checkpoints_passed"]
        )
        return cls(state=state)

    def get_current_phase(self) -> Phase:
        """Get current phase."""
        return self.state.current_phase

    def get_phase_history(self) -> List[Phase]:
        """Get list of phases visited."""
        return self.state.phase_history.copy()

    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return self.state.context.copy()

    def get_data(self) -> Dict[str, Any]:
        """Get current data."""
        return self.state.data.copy()

    def update_context(self, updates: Dict[str, Any]) -> None:
        """
        Update context with new values.

        Args:
            updates: Dict of context updates
        """
        self.state.context.update(updates)

    def update_data(self, updates: Dict[str, Any]) -> None:
        """
        Update data with new values.

        Args:
            updates: Dict of data updates
        """
        self.state.data.update(updates)

    def clear_checkpoints(self) -> None:
        """Clear all checkpoints (useful for re-running phases)."""
        self.state.checkpoints_passed.clear()

    def has_passed_checkpoint(self, checkpoint_name: str) -> bool:
        """
        Check if a checkpoint has been passed.

        Args:
            checkpoint_name: Name of checkpoint to check

        Returns:
            True if checkpoint has been passed
        """
        return checkpoint_name in self.state.checkpoints_passed


# Convenience functions for common operations

def create_engine(
    trigger: str,
    analysis_mode: str = "strategic_planning",
    entry_phase: Phase = Phase.CONTEXT_DISCOVERY
) -> WorkflowEngine:
    """
    Create a new workflow engine with basic context.

    Args:
        trigger: Analysis trigger (feature_decision, competitor_response, etc.)
        analysis_mode: Analysis mode (strategic_planning or sales_enablement)
        entry_phase: Phase to start at

    Returns:
        New WorkflowEngine instance
    """
    context = {
        "trigger": trigger,
        "analysis_mode": analysis_mode
    }
    return WorkflowEngine(entry_phase=entry_phase, context=context)


def create_phase_checkpoint(
    required_keys: List[str],
    location: str = "data"
) -> Callable[[WorkflowState], Tuple[bool, str]]:
    """
    Create a checkpoint validator that checks for required keys.

    Args:
        required_keys: List of keys that must be present
        location: Where to check ("data" or "context")

    Returns:
        Validator function
    """
    def validator(state: WorkflowState) -> Tuple[bool, str]:
        target = state.data if location == "data" else state.context
        missing = [key for key in required_keys if key not in target]

        if missing:
            return False, f"Missing required keys: {', '.join(missing)}"
        return True, f"All required keys present: {', '.join(required_keys)}"

    return validator


def phase_from_name(name: str) -> Phase:
    """
    Convert phase name string to Phase enum.

    Args:
        name: Phase name (e.g., "CONTEXT_DISCOVERY" or "context_discovery")

    Returns:
        Phase enum

    Raises:
        ValueError: If name is not a valid phase
    """
    return Phase[name.upper()]


def phase_to_name(phase: Phase) -> str:
    """
    Convert Phase enum to name string.

    Args:
        phase: Phase enum

    Returns:
        Phase name as string
    """
    return phase.name
