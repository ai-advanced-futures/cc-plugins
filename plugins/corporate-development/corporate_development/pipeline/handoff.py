"""Compact phase handoff and pipeline result types.

PhaseHandoff replaces passing full PhaseOutput.data between phases.
A handoff is ~1KB (gate + score + artifact paths).
Full phase data can be 100KB+ which accumulates in LLM context.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from corporate_development.core.phase import PhaseGate


@dataclass
class PhaseHandoff:
    """Compact summary of one phase's output.

    Contains exactly what the next phase and final synthesizer need:
    - gate: decision to continue or stop
    - score: numeric health/fit score for quick comparison
    - critical_risks: at most 5 risk titles (not full descriptions)
    - artifact_paths: where to find full results on disk (lazy loading)
    - next_phase_inputs: pre-computed minimal fields for downstream phases
    """

    phase_num: int
    phase_name: str
    gate: PhaseGate
    score: Optional[float]
    critical_risks: List[str]
    artifact_paths: Dict[str, str]
    next_phase_inputs: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict (no enums, no Path objects)."""
        return {
            "phase_num": self.phase_num,
            "phase_name": self.phase_name,
            "gate": self.gate.value,
            "score": self.score,
            "critical_risks": self.critical_risks,
            "artifact_paths": self.artifact_paths,
            "next_phase_inputs": self.next_phase_inputs,
        }


@dataclass
class PipelineResult:
    """Aggregated result of running the full M&A pipeline.

    Designed for minimal LLM context consumption:
    - handoff_chain: one PhaseHandoff per completed phase (~1KB each)
    - to_summary(): returns a flat dict (~2KB total) for LLM consumption
    - all_artifact_paths(): lazy-load index — full artifacts remain on disk
    """

    handoff_chain: List[PhaseHandoff]
    final_gate: PhaseGate
    stopped_at_phase: Optional[str]  # phase_name of NO_GO, or None if completed

    def all_artifact_paths(self) -> Dict[str, str]:
        """Merge artifact paths from all phases with phase-prefixed keys."""
        combined: Dict[str, str] = {}
        for h in self.handoff_chain:
            for artifact_key, path in h.artifact_paths.items():
                combined[f"phase{h.phase_num}_{artifact_key}"] = path
        return combined

    def to_summary(self) -> Dict[str, Any]:
        """Return a compact JSON-safe dict for LLM context.

        Use this instead of passing full handoff_chain to LLM agents.
        Contains gate decisions, scores, and artifact paths — not full data.
        """
        return {
            "final_gate": self.final_gate.value,
            "stopped_at": self.stopped_at_phase,
            "phases_completed": len(self.handoff_chain),
            "phase_gates": {h.phase_name: h.gate.value for h in self.handoff_chain},
            "phase_scores": {
                h.phase_name: h.score
                for h in self.handoff_chain
                if h.score is not None
            },
            "artifact_paths": self.all_artifact_paths(),
        }
