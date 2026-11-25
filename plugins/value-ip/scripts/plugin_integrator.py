"""
Read outputs from other plugins in the marketplace.

Supports: competitive-intelligence, pricing, corporate-development, product-finance.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

from .artifact_detector import _safe_read_json


class PluginType(Enum):
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    PRICING = "pricing"
    CORPORATE_DEVELOPMENT = "corporate_development"
    PRODUCT_FINANCE = "product_finance"


PLUGIN_SIGNATURES = {
    PluginType.COMPETITIVE_INTELLIGENCE: {"competitive-ecosystem", "jtbd-analysis", "forces-analysis"},
    PluginType.PRICING: {"right_price", "pricing-analysis", "wtp"},
    PluginType.CORPORATE_DEVELOPMENT: {"acquisition", "target-assessment", "due-diligence"},
    PluginType.PRODUCT_FINANCE: {"unit-economics", "financial-model", "roi"},
}


@dataclass
class PluginOutput:
    plugin_type: PluginType
    data: Dict[str, Any]
    source_path: str
    confidence: str  # high/medium/low


def read_plugin_output(path: Path) -> Optional[PluginOutput]:
    return PluginIntegrator._classify_file(path)


def generate_integration_summary(outputs: List[PluginOutput]) -> str:
    if not outputs:
        return "No plugin outputs detected."
    lines = ["## Plugin Integration Context", ""]
    for output in outputs:
        lines.append(f"- **{output.plugin_type.value}**: {output.source_path}")
    return "\n".join(lines)


class PluginIntegrator:
    def __init__(self, search_path: Optional[Path] = None):
        self.search_path = search_path or Path.cwd()
        self.outputs: List[PluginOutput] = []

    def scan(self) -> None:
        self.outputs = []
        for file in self.search_path.rglob("*.json"):
            output = self._classify_file(file)
            if output:
                self.outputs.append(output)

    def generate_summary(self) -> str:
        return generate_integration_summary(self.outputs)

    @staticmethod
    def _classify_file(file: Path) -> Optional[PluginOutput]:
        data = _safe_read_json(file)
        if data is None or not isinstance(data, dict):
            return None

        file_name_lower = file.name.lower()
        all_keys = set(data.keys()) | {file_name_lower}

        for plugin_type, signatures in PLUGIN_SIGNATURES.items():
            matched = sum(1 for sig in signatures for k in all_keys if sig in k)
            if matched >= 1:
                confidence = "high" if matched >= 2 else "medium"
                return PluginOutput(
                    plugin_type=plugin_type,
                    data=data,
                    source_path=str(file),
                    confidence=confidence,
                )
        return None
