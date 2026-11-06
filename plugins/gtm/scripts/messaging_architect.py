from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MessageHierarchy:
    tagline: str
    elevator_pitch: str
    value_props: list[str]
    proof_points: list[str]

    def to_dict(self) -> dict:
        if not self.tagline:
            raise ValueError("tagline is required")
        return {
            "tagline": self.tagline,
            "elevator_pitch": self.elevator_pitch,
            "value_props": self.value_props,
            "proof_points": self.proof_points,
        }


class ValuePropGenerator:
    def generate(self, capability: str, outcome: str) -> str:
        return f"{capability.capitalize()} so you can {outcome}."
