"""
Competitive Intelligence Plugin - Plugin Integration

Provides loose coupling interfaces for integrating with other Claude Code plugins.

Key Features:
- JTBD plugin output reading
- Financial plugin output reading
- Plugin handoff instruction generation
- Loose coupling interfaces
- Error handling for missing/invalid plugin data

Supported Plugins:
- JTBD Plugin: Jobs-To-Be-Done analysis
- Financial Plugin: Financial data and metrics (placeholder)
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PluginType(Enum):
    """
    Types of external plugins.

    - JTBD: Jobs-To-Be-Done plugin
    - FINANCIAL: Financial data plugin
    """
    JTBD = "jtbd"
    FINANCIAL = "financial"


@dataclass
class PluginOutput:
    """
    Output from external plugin.

    Attributes:
        plugin_type: Type of plugin
        data: Plugin output data
        source_path: Path to source file
        confidence: Confidence level in data quality
    """
    plugin_type: PluginType
    data: Dict[str, Any]
    source_path: str
    confidence: str  # "high", "medium", "low"


class PluginIntegrator:
    """
    Plugin integration coordinator.

    Manages loose coupling with external Claude Code plugins.

    Workflow:
    1. Read plugin outputs from files
    2. Validate and normalize data
    3. Generate handoff instructions
    4. Track plugin data sources
    """

    def __init__(self):
        """Initialize plugin integrator."""
        self.outputs: List[PluginOutput] = []

    def add_output(self, output: PluginOutput):
        """
        Add plugin output.

        Args:
            output: PluginOutput to add
        """
        self.outputs.append(output)

    def get_outputs_by_type(self, plugin_type: PluginType) -> List[PluginOutput]:
        """
        Get outputs by plugin type.

        Args:
            plugin_type: Plugin type to filter by

        Returns:
            List of matching outputs
        """
        return [o for o in self.outputs if o.plugin_type == plugin_type]

    def generate_handoff_instructions(
        self,
        plugin_type: PluginType,
        context: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate handoff instructions for a plugin.

        Creates instructions for invoking another plugin
        with the current competitive intelligence context.

        Args:
            plugin_type: Type of plugin to hand off to
            context: Current analysis context
            output_path: Optional output path for plugin

        Returns:
            Handoff instructions dict
        """
        instructions = {
            "plugin_type": plugin_type.value,
            "context": context,
            "expected_output": output_path
        }

        # Add plugin-specific instructions
        if plugin_type == PluginType.JTBD:
            instructions["instructions"] = {
                "analyze_job": context.get("job_statement", ""),
                "identify_phases": True,
                "calculate_performance": True
            }
        elif plugin_type == PluginType.FINANCIAL:
            instructions["instructions"] = {
                "analyze_competitors": context.get("competitors", []),
                "include_revenue": True,
                "include_valuation": True
            }

        return instructions


def _read_plugin_output(
    plugin_type: PluginType,
    file_path: str,
    confidence_fn
) -> Optional[PluginOutput]:
    """
    Shared file-read pattern for plugin output readers.

    Args:
        plugin_type: The PluginType enum value for the output
        file_path: Path to the JSON output file
        confidence_fn: Callable(data) -> str that returns "high"/"medium"/"low"

    Returns:
        PluginOutput or None if file doesn't exist/is invalid
    """
    if not file_path:
        return None

    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path, 'r') as f:
            data = json.load(f)

        return PluginOutput(
            plugin_type=plugin_type,
            data=data,
            source_path=file_path,
            confidence=confidence_fn(data)
        )
    except (json.JSONDecodeError, Exception):
        return None


def read_jtbd_output(file_path: str) -> Optional[PluginOutput]:
    """
    Read JTBD plugin output from file.

    Args:
        file_path: Path to JTBD output JSON file

    Returns:
        PluginOutput or None if file doesn't exist/invalid
    """
    def _jtbd_confidence(data):
        if data.get("job_statement") and data.get("job_phases"):
            return "high"
        elif not data:
            return "low"
        return "medium"

    return _read_plugin_output(PluginType.JTBD, file_path, _jtbd_confidence)


def read_financial_output(file_path: str) -> Optional[PluginOutput]:
    """
    Read financial plugin output from file.

    Args:
        file_path: Path to financial output JSON file

    Returns:
        PluginOutput or None if file doesn't exist/invalid
    """
    def _financial_confidence(data):
        if data.get("revenue") or data.get("valuation"):
            return "high"
        elif not data:
            return "low"
        return "medium"

    return _read_plugin_output(PluginType.FINANCIAL, file_path, _financial_confidence)


def generate_handoff_instructions(
    plugin_type: PluginType,
    context: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate handoff instructions for a plugin.

    Args:
        plugin_type: Type of plugin
        context: Analysis context
        output_path: Optional output path

    Returns:
        Handoff instructions dict
    """
    integrator = PluginIntegrator()
    return integrator.generate_handoff_instructions(
        plugin_type=plugin_type,
        context=context,
        output_path=output_path
    )


def create_plugin_output(
    plugin_type: PluginType,
    data: Dict[str, Any],
    source_path: str,
    confidence: str = "medium"
) -> PluginOutput:
    """
    Create plugin output.

    Args:
        plugin_type: Type of plugin
        data: Plugin data
        source_path: Source file path
        confidence: Confidence level

    Returns:
        PluginOutput
    """
    return PluginOutput(
        plugin_type=plugin_type,
        data=data,
        source_path=source_path,
        confidence=confidence
    )


# Convenience functions for common operations

def read_plugin_output(
    plugin_type: PluginType,
    file_path: str
) -> Optional[PluginOutput]:
    """
    Read plugin output based on type.

    Args:
        plugin_type: Type of plugin
        file_path: Path to output file

    Returns:
        PluginOutput or None
    """
    if plugin_type == PluginType.JTBD:
        return read_jtbd_output(file_path)
    elif plugin_type == PluginType.FINANCIAL:
        return read_financial_output(file_path)
    else:
        return None


def create_handoff_for_jtbd(
    job_statement: str,
    context: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create handoff instructions for JTBD plugin.

    Args:
        job_statement: Job statement to analyze
        context: Analysis context
        output_path: Optional output path

    Returns:
        Handoff instructions
    """
    full_context = {**context, "job_statement": job_statement}
    return generate_handoff_instructions(
        plugin_type=PluginType.JTBD,
        context=full_context,
        output_path=output_path
    )


def create_handoff_for_financial(
    competitors: List[str],
    context: Dict[str, Any],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create handoff instructions for financial plugin.

    Args:
        competitors: List of competitors to analyze
        context: Analysis context
        output_path: Optional output path

    Returns:
        Handoff instructions
    """
    full_context = {**context, "competitors": competitors}
    return generate_handoff_instructions(
        plugin_type=PluginType.FINANCIAL,
        context=full_context,
        output_path=output_path
    )
