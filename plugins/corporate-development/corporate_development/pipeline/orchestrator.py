"""PipelineOrchestrator: context-efficient M&A pipeline runner.

Key design decisions vs the existing MAOrchestrator:
1. Produces PhaseHandoff (~1KB) instead of accumulating full PhaseOutput.data
2. Parallelizes Phase 3 (Operational DD) + Phase 4 (Financial DD) — independent, safe
3. Returns PipelineResult with handoff chain + to_summary() for minimal LLM context
4. Same user_input passed to all phases — each reads only its required keys
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from corporate_development.core.phase import PhaseGate, PhaseInput, PhaseOutput
from corporate_development.phases.phase_0_readiness import Phase0AcquisitionReadiness
from corporate_development.phases.phase_1_sourcing import Phase1DealSourcing
from corporate_development.phases.phase_2_assessment import Phase2TargetAssessment
from corporate_development.phases.phase_3_operational_dd import Phase3OperationalDD
from corporate_development.phases.phase_4_financial_dd import Phase4FinancialDD
from corporate_development.phases.phase_5_integration import Phase5IntegrationPlanning
from corporate_development.phases.phase_6_decision import Phase6DealDecision
from corporate_development.pipeline.handoff import PhaseHandoff, PipelineResult

_PHASE_NAMES = {
    0: "Phase 0: Acquisition Readiness",
    1: "Phase 1: Deal Sourcing",
    2: "Phase 2: Target Assessment",
    3: "Phase 3: Operational Due Diligence",
    4: "Phase 4: Financial Due Diligence",
    5: "Phase 5: Integration Planning",
    6: "Phase 6: Deal Decision",
}

_DEFAULT_PHASES = list(range(7))


class PipelineOrchestrator:
    """Context-efficient M&A pipeline with Phase 3+4 parallelism.

    Improvements over MAOrchestrator:
    - Passes PhaseHandoff (~1KB) between phases, not full PhaseOutput.data (100KB+)
    - Phases 3 and 4 run in parallel (ThreadPoolExecutor) — write to separate dirs
    - Returns PipelineResult.to_summary() (~2KB) for LLM consumption
    - Supports phases_to_run parameter for partial pipeline execution
    """

    def __init__(self) -> None:
        self._phases = {
            0: Phase0AcquisitionReadiness(),
            1: Phase1DealSourcing(),
            2: Phase2TargetAssessment(),
            3: Phase3OperationalDD(),
            4: Phase4FinancialDD(),
            5: Phase5IntegrationPlanning(),
            6: Phase6DealDecision(),
        }

    def run(
        self,
        user_input: Dict[str, Any],
        phases_to_run: Optional[List[int]] = None,
    ) -> PipelineResult:
        """Execute M&A pipeline and return a compact PipelineResult.

        Args:
            user_input: All phase inputs in a single flat dict. Each phase
                        reads only the keys it needs; missing keys trigger
                        phase-specific placeholder or NO_GO responses.
            phases_to_run: Which phase numbers to execute (default: 0-6).
                           Useful for partial pipeline runs (e.g., just [3, 4]).

        Returns:
            PipelineResult with handoff_chain, final_gate, stopped_at_phase.
            Call .to_summary() for a minimal dict safe for LLM consumption.
        """
        if phases_to_run is None:
            phases_to_run = _DEFAULT_PHASES

        handoffs: List[PhaseHandoff] = []

        # Sequential: Phase 0, 1, 2
        for phase_num in [p for p in [0, 1, 2] if p in phases_to_run]:
            output = self._run_phase(phase_num, user_input)
            handoff = self._extract_handoff(phase_num, output)
            handoffs.append(handoff)
            if output.gate == PhaseGate.NO_GO:
                return PipelineResult(
                    handoff_chain=handoffs,
                    final_gate=PhaseGate.NO_GO,
                    stopped_at_phase=handoff.phase_name,
                )

        # Parallel: Phase 3 + Phase 4
        run_3 = 3 in phases_to_run
        run_4 = 4 in phases_to_run
        if run_3 or run_4:
            parallel_outputs = self._run_phases_parallel(
                user_input, run_3=run_3, run_4=run_4
            )
            for phase_num in [p for p in [3, 4] if p in phases_to_run]:
                output = parallel_outputs[phase_num]
                handoff = self._extract_handoff(phase_num, output)
                handoffs.append(handoff)
                if output.gate == PhaseGate.NO_GO:
                    return PipelineResult(
                        handoff_chain=handoffs,
                        final_gate=PhaseGate.NO_GO,
                        stopped_at_phase=handoff.phase_name,
                    )

        # Sequential: Phase 5, 6
        for phase_num in [p for p in [5, 6] if p in phases_to_run]:
            output = self._run_phase(phase_num, user_input)
            handoff = self._extract_handoff(phase_num, output)
            handoffs.append(handoff)
            if output.gate == PhaseGate.NO_GO:
                return PipelineResult(
                    handoff_chain=handoffs,
                    final_gate=PhaseGate.NO_GO,
                    stopped_at_phase=handoff.phase_name,
                )

        final_gate = handoffs[-1].gate if handoffs else PhaseGate.NO_GO
        return PipelineResult(
            handoff_chain=handoffs,
            final_gate=final_gate,
            stopped_at_phase=None,
        )

    def _run_phase(self, phase_num: int, user_input: Dict[str, Any]) -> PhaseOutput:
        """Run a single phase, converting ValidationError to a NO_GO PhaseOutput.

        Phases with strict Pydantic models (e.g., Phase 0) raise ValidationError
        when required fields are missing. The pipeline treats this as NO_GO so
        callers can rely on PhaseOutput.gate without catching exceptions.
        """
        phase = self._phases[phase_num]
        try:
            return phase.run(PhaseInput(phase=phase.name, user_input=user_input))
        except ValidationError as exc:
            return PhaseOutput(
                data={
                    "status": "validation_error",
                    "error": str(exc),
                    "missing_fields": [
                        e["loc"][0] for e in exc.errors() if e.get("loc")
                    ],
                },
                gate=PhaseGate.NO_GO,
                artifacts={},
                reasoning=f"Phase {phase_num} input validation failed: {exc.error_count()} required fields missing.",
            )

    def _run_phases_parallel(
        self,
        user_input: Dict[str, Any],
        run_3: bool,
        run_4: bool,
    ) -> Dict[int, PhaseOutput]:
        """Run Phase 3 and/or Phase 4 in parallel via ThreadPoolExecutor."""
        futures = {}

        with ThreadPoolExecutor(max_workers=2) as executor:
            if run_3:
                futures[3] = executor.submit(self._run_phase, 3, user_input)
            if run_4:
                futures[4] = executor.submit(self._run_phase, 4, user_input)

        return {phase_num: future.result() for phase_num, future in futures.items()}

    def _extract_handoff(self, phase_num: int, output: PhaseOutput) -> PhaseHandoff:
        """Extract compact PhaseHandoff from a full PhaseOutput."""
        data = output.data or {}
        phase_name = _PHASE_NAMES.get(phase_num, f"Phase {phase_num}")
        score: Optional[float] = None
        next_phase_inputs: Dict[str, Any] = {}

        if phase_num == 0:
            score = data.get("overall_readiness_score")
            next_phase_inputs = {"readiness_score": score, "gate": output.gate.value}
        elif phase_num == 1:
            next_phase_inputs = {"pipeline_gate": output.gate.value}
        elif phase_num == 2:
            strategic_fit = data.get("strategic_fit")
            if isinstance(strategic_fit, dict):
                score = strategic_fit.get("score")
            next_phase_inputs = {
                "assessment_gate": output.gate.value,
                "assessment_mode": data.get("assessment_mode", "PLACEHOLDER"),
            }
        elif phase_num == 3:
            score = data.get("overall_score")
            next_phase_inputs = {
                "operational_health": score,
                "operational_gate": output.gate.value,
                "operational_critical_count": data.get("critical_count", 0),
                "operational_warning_count": data.get("warning_count", 0),
            }
        elif phase_num == 4:
            score = data.get("overall_score")
            next_phase_inputs = {
                "financial_health": score,
                "financial_gate": output.gate.value,
                "financial_critical_count": data.get("critical_count", 0),
            }
        elif phase_num == 5:
            next_phase_inputs = {"integration_complete": True}
        elif phase_num == 6:
            next_phase_inputs = {}

        return PhaseHandoff(
            phase_num=phase_num,
            phase_name=phase_name,
            gate=output.gate,
            score=score,
            critical_risks=[],
            artifact_paths={k: str(v) for k, v in (output.artifacts or {}).items()},
            next_phase_inputs=next_phase_inputs,
        )
