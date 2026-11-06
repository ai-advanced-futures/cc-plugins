"""
Competitive Intelligence Plugin - Phase 6: Deliverable Generation

Generates final deliverables from workflow results.

Key Features:
- 10 JSON module generation
- Output directory management
- Schema validation integration
- Delivery packaging
- Error handling and partial delivery support

Output Modules:
1. metadata.json - Analysis metadata
2. context.json - Analysis context
3. competitor_profiles.json - Competitor data
4. jtbd_performance.json - JTBD analysis
5. forces.json - Forces analysis
6. economic_value.json - Economic value analysis
7. strategic_positioning.json - Positioning analysis
8. technology_disruption.json - Technology analysis
9. loss_churn.json - Loss/churn analysis
10. insights.json - Key insights
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.io_manager import IOManager, OutputLocation, generate_metadata
from scripts.schema_validator import SchemaType


class DeliveryStatus(Enum):
    """
    Delivery completion status.

    - SUCCESS: All modules generated successfully
    - PARTIAL: Some modules generated
    - FAILED: No modules generated
    """
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class DeliveryResult:
    """
    Deliverable generation result.

    Attributes:
        status: Delivery status
        output_directory: Path to output directory
        modules_written: List of successfully written modules
        modules_failed: List of failed modules
        validation_errors: List of validation errors
    """
    status: DeliveryStatus
    output_directory: Optional[Path]
    modules_written: List[SchemaType]
    modules_failed: List[SchemaType]
    validation_errors: List[Dict[str, Any]] = field(default_factory=list)


class DeliverableGenerator:
    """
    Deliverable generator.

    Generates all output modules from workflow engine state.

    Workflow:
    1. Prepare all modules from engine state
    2. Create timestamped output directory
    3. Write modules with validation
    4. Track success/failures
    5. Return delivery result
    """

    def __init__(
        self,
        engine,
        base_dir: Optional[str] = None,
        location: OutputLocation = OutputLocation.CODE
    ):
        """
        Initialize deliverable generator.

        Args:
            engine: WorkflowEngine instance
            base_dir: Base directory for outputs
            location: Output location (CODE or WEB)
        """
        self.engine = engine
        self.io_manager = IOManager(location=location, base_dir=base_dir)
        self.modules_data: Dict[SchemaType, Dict[str, Any]] = {}

    def prepare_metadata_module(self) -> Dict[str, Any]:
        """
        Prepare metadata module.

        Returns:
            Metadata dict
        """
        context = self.engine.state.data.get("context", {})
        phases = self.engine.state.data.get("phases_executed", [])
        lenses = self.engine.state.data.get("lenses_applied", [])
        sources = self.engine.state.data.get("data_sources", [])
        confidence = self.engine.state.data.get("overall_confidence", "low")
        warnings = self.engine.state.data.get("warnings", None)

        return generate_metadata(
            context=context,
            phases_executed=phases,
            lenses_applied=lenses,
            data_sources=sources,
            overall_confidence=confidence,
            warnings=warnings
        )

    def prepare_ecosystem_module(self) -> Dict[str, Any]:
        """
        Prepare competitive ecosystem module.

        Returns:
            Ecosystem dict
        """
        competitors = self.engine.state.data.get("competitors", [])
        gathered_data = self.engine.state.data.get("gathered_data", {})
        context = self.engine.state.data.get("context", {})

        profiles = []
        for competitor in competitors:
            profile = {
                "competitor_id": competitor,
                "data_sources": gathered_data.get(competitor, [])
            }
            profiles.append(profile)

        return {
            "context": context,
            "competitors": profiles
        }

    def prepare_jtbd_analysis_module(self) -> Dict[str, Any]:
        """
        Prepare JTBD analysis module.

        Returns:
            JTBD analysis dict
        """
        results = self.engine.state.data.get("jtbd_performance_results", {})
        return results if results else {}

    def prepare_forces_analysis_module(self) -> Dict[str, Any]:
        """
        Prepare forces analysis module.

        Returns:
            Forces analysis dict
        """
        results = self.engine.state.data.get("forces_results", {})
        return results if results else {}

    def prepare_value_analysis_module(self) -> Dict[str, Any]:
        """
        Prepare value analysis module.

        Returns:
            Value analysis dict
        """
        results = self.engine.state.data.get("economic_value_results", {})
        return results if results else {}

    def prepare_strategic_analysis_module(self) -> Dict[str, Any]:
        """
        Prepare strategic analysis module.

        Returns:
            Strategic analysis dict
        """
        results = self.engine.state.data.get("strategic_positioning_results", {})
        return results if results else {}

    def prepare_tech_disruption_module(self) -> Dict[str, Any]:
        """
        Prepare technology disruption module.

        Returns:
            Technology disruption dict
        """
        results = self.engine.state.data.get("technology_disruption_results", {})
        return results if results else {}

    def prepare_loss_churn_analysis_module(self) -> Dict[str, Any]:
        """
        Prepare loss/churn analysis module.

        Returns:
            Loss/churn analysis dict
        """
        results = self.engine.state.data.get("loss_churn_results", {})
        return results if results else {}

    def prepare_swot_module(self) -> Dict[str, Any]:
        """
        Prepare SWOT analysis module.

        Returns:
            SWOT dict
        """
        insights = self.engine.state.data.get("insights", [])

        # Group insights by type
        swot = {
            "strengths": [i for i in insights if i.get("insight_type") == "strength"],
            "weaknesses": [i for i in insights if i.get("insight_type") == "weakness"],
            "opportunities": [i for i in insights if i.get("insight_type") == "opportunity"],
            "threats": [i for i in insights if i.get("insight_type") == "threat"]
        }

        return swot

    def prepare_recommendations_module(self) -> Dict[str, Any]:
        """
        Prepare recommendations module.

        Returns:
            Recommendations dict
        """
        insights = self.engine.state.data.get("insights", [])

        return {
            "recommendations": [],
            "summary": self.engine.state.data.get("synthesis_summary", ""),
            "insights_count": len(insights)
        }

    def prepare_all_modules(self):
        """
        Prepare all modules from engine state.
        """
        # Map schema types to preparation methods
        preparers = {
            SchemaType.METADATA: self.prepare_metadata_module,
            SchemaType.ECOSYSTEM: self.prepare_ecosystem_module,
            SchemaType.JTBD_ANALYSIS: self.prepare_jtbd_analysis_module,
            SchemaType.FORCES_ANALYSIS: self.prepare_forces_analysis_module,
            SchemaType.VALUE_ANALYSIS: self.prepare_value_analysis_module,
            SchemaType.STRATEGIC_ANALYSIS: self.prepare_strategic_analysis_module,
            SchemaType.TECH_DISRUPTION: self.prepare_tech_disruption_module,
            SchemaType.LOSS_CHURN: self.prepare_loss_churn_analysis_module,
            SchemaType.SWOT: self.prepare_swot_module,
            SchemaType.RECOMMENDATIONS: self.prepare_recommendations_module
        }

        # Prepare each module
        for schema_type, preparer in preparers.items():
            try:
                data = preparer()
                self.modules_data[schema_type] = data
            except Exception as e:
                # Log error but continue with other modules
                print(f"Error preparing {schema_type.value}: {e}")

    def generate_deliverables(self, validate: bool = True) -> DeliveryResult:
        """
        Generate all deliverables.

        Args:
            validate: Whether to validate modules

        Returns:
            DeliveryResult
        """
        # Prepare all modules
        self.prepare_all_modules()

        # Create output directory
        output_dir = self.io_manager.create_session_directory()

        # Write modules
        modules_written = []
        modules_failed = []
        validation_errors = []

        for schema_type, data in self.modules_data.items():
            try:
                self.io_manager.write_module(
                    schema_type=schema_type,
                    data=data,
                    output_dir=output_dir,
                    validate=validate
                )
                modules_written.append(schema_type)
            except Exception as e:
                modules_failed.append(schema_type)
                validation_errors.append({
                    "module": schema_type.value,
                    "error": str(e)
                })

        # Determine delivery status
        total_modules = len(SchemaType)
        if len(modules_written) == total_modules:
            status = DeliveryStatus.SUCCESS
        elif len(modules_written) > 0:
            status = DeliveryStatus.PARTIAL
        else:
            status = DeliveryStatus.FAILED

        # Update engine state
        self.engine.update_data({
            "deliverables_generated": True,
            "output_directory": str(output_dir),
            "delivery_status": status.value
        })

        return DeliveryResult(
            status=status,
            output_directory=output_dir,
            modules_written=modules_written,
            modules_failed=modules_failed,
            validation_errors=validation_errors
        )


# Convenience functions

def create_metadata_module(
    context: Dict[str, Any],
    phases_executed: List[str],
    lenses_applied: List[str],
    data_sources: List[Dict[str, Any]],
    overall_confidence: str,
    warnings: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create metadata module.

    Args:
        context: Analysis context
        phases_executed: List of phase names
        lenses_applied: List of lens names
        data_sources: List of data sources
        overall_confidence: Overall confidence level
        warnings: Optional warnings

    Returns:
        Metadata dict
    """
    return generate_metadata(
        context=context,
        phases_executed=phases_executed,
        lenses_applied=lenses_applied,
        data_sources=data_sources,
        overall_confidence=overall_confidence,
        warnings=warnings
    )




def generate_deliverables(
    engine,
    base_dir: Optional[str] = None,
    validate: bool = True
) -> DeliveryResult:
    """
    Generate deliverables from workflow engine.

    Args:
        engine: WorkflowEngine instance
        base_dir: Base directory for outputs
        validate: Whether to validate modules

    Returns:
        DeliveryResult
    """
    generator = DeliverableGenerator(engine, base_dir=base_dir)
    return generator.generate_deliverables(validate=validate)
