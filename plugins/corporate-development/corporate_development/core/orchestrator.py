from typing import Dict, List, Any
from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate


class MAOrchestrator:
    """Orchestrates M&A investigation across phases."""

    def __init__(self):
        self.phases: List[Phase] = []
        self.results: Dict[str, PhaseOutput] = {}

    def register_phase(self, phase: Phase) -> None:
        """Register a phase in execution order."""
        self.phases.append(phase)

    def get_phases(self) -> List[Phase]:
        """Get registered phases."""
        return self.phases

    def run(self, user_input: Dict[str, Any]) -> List[PhaseOutput]:
        """
        Execute phases sequentially.
        Stop on NO_GO gate.
        Pass prior outputs to next phase.
        """
        results = []
        prior_outputs = {}

        for phase in self.phases:
            # Build input for this phase
            phase_input = PhaseInput(
                phase=phase.name,
                user_input=user_input,
                prior_outputs=prior_outputs if prior_outputs else None
            )

            # Execute phase
            output = phase.run(phase_input)
            results.append(output)

            # Store output for next phase
            prior_outputs[phase.name] = output.data

            # Stop if NO_GO
            if output.gate == PhaseGate.NO_GO:
                break

        self.results = {phase.name: output for phase, output in zip(self.phases, results)}
        return results
