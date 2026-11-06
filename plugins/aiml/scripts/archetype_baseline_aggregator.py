"""Pure median aggregator for archetype baseline telemetry.

Per Charter sub-spec 4c §6.1. NO I/O. Mirrors 4b's statistics.median baseline
aggregation (ADR-004 D14). Omits not-present / empty archetypes (defensive;
schema-valid inputs cannot have empty cost_samples per §7.12 minItems:1).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from archetype_baseline_input_loader import ArchetypeCostSamples

# sibling-module import — callers (tests, emitter) put scripts/ on sys.path (4a/4b convention)


@dataclass(frozen=True)
class BaselineReading:
    baseline_cost_per_interaction: float
    sample_size_n: int
    aggregation: str = "median"


def aggregate(samples: ArchetypeCostSamples) -> dict[str, BaselineReading]:
    """Per archetype where present and cost_samples non-empty, median of cost_samples."""
    out: dict[str, BaselineReading] = {}
    for name, entry in samples.archetypes.items():
        if not entry.present or not entry.cost_samples:
            continue  # COUNT guard (defensive); $0 VALUE blocked at input by exclusiveMinimum:0
        out[name] = BaselineReading(
            baseline_cost_per_interaction=statistics.median(entry.cost_samples),
            sample_size_n=entry.sample_size_n,
            aggregation="median",
        )
    return out
