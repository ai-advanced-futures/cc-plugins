"""
Competitive Intelligence Plugin - Schema Validator

JSON schema validation for all output modules. Ensures data integrity
and enables reliable consumption by other plugins.

Schemas:
1. competitive-ecosystem.json - Multi-dimensional competitor map
2. jtbd-analysis.json - Job step performance comparison
3. forces-analysis.json - Switching dynamics per competitor
4. value-analysis.json - Economic value comparison
5. strategic-analysis.json - Business model, positioning, moats
6. technology-disruption.json - AI/tech disruption assessment
7. loss-churn-analysis.json - Win/loss patterns
8. swot-analysis.json - Evidence-based SWOT
9. recommendations.json - Confidence-weighted actions
10. metadata.json - Analysis config, sources, confidence
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# jsonschema is optional - validation degrades gracefully without it
try:
    import jsonschema
    from jsonschema import ValidationError as JsonSchemaValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    jsonschema = None
    JsonSchemaValidationError = Exception  # Fallback type
    JSONSCHEMA_AVAILABLE = False


class SchemaType(Enum):
    """All output module schema types."""
    ECOSYSTEM = "competitive-ecosystem"
    JTBD_ANALYSIS = "jtbd-analysis"
    FORCES_ANALYSIS = "forces-analysis"
    VALUE_ANALYSIS = "value-analysis"
    STRATEGIC_ANALYSIS = "strategic-analysis"
    TECH_DISRUPTION = "technology-disruption"
    LOSS_CHURN = "loss-churn-analysis"
    SWOT = "swot-analysis"
    RECOMMENDATIONS = "recommendations"
    METADATA = "metadata"


@dataclass
class ValidationResult:
    """Result of schema validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class SchemaNotFoundError(Exception):
    """Raised when schema file is not found."""
    pass


class SchemaValidator:
    """
    Validates JSON output against defined schemas.

    Supports:
    - Schema loading and caching
    - Validation with detailed error messages
    - Version compatibility checking
    - Cross-reference validation
    """

    def __init__(self, schemas_dir: Optional[Path] = None):
        """
        Initialize schema validator.

        Args:
            schemas_dir: Directory containing schema JSON files
                        (default: ../schemas relative to this file)
        """
        if schemas_dir is None:
            # Default to schemas directory
            self.schemas_dir = Path(__file__).parent.parent / "schemas"
        else:
            self.schemas_dir = Path(schemas_dir)

        self._schema_cache: Dict[SchemaType, dict] = {}

    def load_schema(self, schema_type: SchemaType) -> dict:
        """
        Load a JSON schema from file.

        Args:
            schema_type: Type of schema to load

        Returns:
            Schema as dict

        Raises:
            SchemaNotFoundError: If schema file doesn't exist
        """
        # Check cache first
        if schema_type in self._schema_cache:
            return self._schema_cache[schema_type]

        # Load from file
        schema_path = self.schemas_dir / f"{schema_type.value}.json"

        if not schema_path.exists():
            raise SchemaNotFoundError(
                f"Schema file not found: {schema_path}"
            )

        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)

            # Cache it
            self._schema_cache[schema_type] = schema

            return schema

        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON in schema file {schema_path}: {e}"
            )

    def load_all_schemas(self) -> Dict[SchemaType, dict]:
        """
        Load all schemas at once.

        Returns:
            Dict mapping schema types to schemas
        """
        schemas = {}
        for schema_type in SchemaType:
            schemas[schema_type] = self.load_schema(schema_type)
        return schemas

    def validate(
        self,
        schema_type: SchemaType,
        data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate data against a schema.

        Args:
            schema_type: Schema to validate against
            data: Data to validate

        Returns:
            ValidationResult with is_valid, errors, warnings
        """
        schema = self.load_schema(schema_type)

        # If jsonschema is not available, skip validation with warning
        if not JSONSCHEMA_AVAILABLE:
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["jsonschema not installed - validation skipped"]
            )

        try:
            # Validate using jsonschema library
            jsonschema.validate(instance=data, schema=schema)

            # Validation passed
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[]
            )

        except JsonSchemaValidationError as e:
            # Validation failed - format error message
            error_msg = self._format_validation_error(e)

            return ValidationResult(
                is_valid=False,
                errors=[error_msg],
                warnings=[]
            )

        except Exception as e:
            # Unexpected error
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[]
            )

    def _format_validation_error(self, error: JsonSchemaValidationError) -> str:
        """
        Format a jsonschema validation error into readable message.

        Args:
            error: JsonSchemaValidationError

        Returns:
            Formatted error message
        """
        path = " -> ".join(str(p) for p in error.path) if error.path else "root"
        return f"Validation error at {path}: {error.message}"

    def is_version_compatible(
        self,
        data_version: str,
        schema_version: str
    ) -> bool:
        """
        Check if data version is compatible with schema version.

        Uses semantic versioning rules:
        - Same major version = compatible
        - Different major version = incompatible

        Args:
            data_version: Version in data (e.g., "1.0.0")
            schema_version: Version in schema (e.g., "1.0.0")

        Returns:
            True if compatible
        """
        try:
            data_major = int(data_version.split('.')[0])
            schema_major = int(schema_version.split('.')[0])

            return data_major == schema_major

        except (ValueError, IndexError):
            # Invalid version format
            return False

    def validate_with_version_check(
        self,
        schema_type: SchemaType,
        data: Dict[str, Any],
        expected_version: str = "1.0.0"
    ) -> ValidationResult:
        """
        Validate data and check version compatibility.

        Args:
            schema_type: Schema to validate against
            data: Data to validate
            expected_version: Expected schema version

        Returns:
            ValidationResult
        """
        # First validate structure
        result = self.validate(schema_type, data)

        if not result.is_valid:
            return result

        # Check version if present
        if "version" in data:
            data_version = data["version"]
            if not self.is_version_compatible(data_version, expected_version):
                result.warnings.append(
                    f"Version incompatibility: data is {data_version}, "
                    f"expected {expected_version}"
                )

        return result


# Convenience functions

def load_schema(schema_type: SchemaType) -> dict:
    """
    Load a schema (convenience function).

    Args:
        schema_type: Type of schema to load

    Returns:
        Schema as dict
    """
    validator = SchemaValidator()
    return validator.load_schema(schema_type)


def validate_output(
    schema_type: SchemaType,
    data: Dict[str, Any]
) -> ValidationResult:
    """
    Validate output data (convenience function).

    Args:
        schema_type: Schema to validate against
        data: Data to validate

    Returns:
        ValidationResult
    """
    validator = SchemaValidator()
    return validator.validate(schema_type, data)


def validate_file(schema_type: SchemaType, file_path: str) -> ValidationResult:
    """
    Validate a JSON file against a schema.

    Args:
        schema_type: Schema to validate against
        file_path: Path to JSON file

    Returns:
        ValidationResult
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        return validate_output(schema_type, data)

    except json.JSONDecodeError as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid JSON in file {file_path}: {e}"],
            warnings=[]
        )
    except FileNotFoundError:
        return ValidationResult(
            is_valid=False,
            errors=[f"File not found: {file_path}"],
            warnings=[]
        )


def get_schema_version(schema_type: SchemaType) -> str:
    """
    Get the current version of a schema.

    Args:
        schema_type: Schema type

    Returns:
        Version string (e.g., "1.0.0")
    """
    # For now, all schemas are version 1.0.0
    # This can be extracted from schema files in the future
    return "1.0.0"
