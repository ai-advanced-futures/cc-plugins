from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass


class PhaseGate(Enum):
    """Phase gate decision outcomes."""
    GO = "GO"  # Proceed to next phase
    NO_GO = "NO_GO"  # Stop investigation
    CONDITIONAL = "CONDITIONAL"  # Proceed with conditions


@dataclass
class PhaseInput:
    """Input data for a phase."""
    phase: str  # Phase name (e.g., "Phase 1: Target Assessment")
    user_input: Dict[str, Any]  # User-provided data
    prior_outputs: Optional[Dict[str, Any]] = None  # Outputs from previous phases


@dataclass
class PhaseOutput:
    """Output from a phase execution."""
    data: Dict[str, Any]  # Analysis results and findings
    gate: PhaseGate  # Decision (GO/NO_GO/CONDITIONAL)
    artifacts: Dict[str, str]  # Artifact paths {artifact_type: file_path}
    reasoning: Optional[str] = None  # Explanation of gate decision
    next_actions: Optional[list[str]] = None  # Recommended next steps


class Phase:
    """Base class for M&A investigation phases."""

    name: str  # Override in subclass
    description: str = ""  # Override in subclass

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute phase investigation. Override in subclass."""
        raise NotImplementedError(f"{self.__class__.__name__}.run() must be implemented")
