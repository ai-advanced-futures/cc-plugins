"""
Competitive Intelligence Plugin - File I/O Manager

Handles all file output operations including:
- Modular JSON writing for all 10 output modules
- File system abstraction (Code vs Web environments)
- Timestamped output directory management
- Metadata generation
- Output validation

Supports both Claude Code (filesystem) and Claude Web (in-memory) environments.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.schema_validator import SchemaType, validate_output


class OutputLocation(Enum):
    """
    Output location environment.

    CODE: Claude Code CLI (filesystem access)
    WEB: Claude Web (in-memory, limited filesystem)
    """
    CODE = "code"
    WEB = "web"


class IOManager:
    """
    Manages file I/O operations for competitive intelligence outputs.

    Handles:
    - Creating timestamped output directories
    - Writing individual JSON modules
    - Writing all modules in batch
    - Validating outputs against schemas
    - Abstracting filesystem vs in-memory storage
    """

    def __init__(
        self,
        location: OutputLocation = OutputLocation.CODE,
        base_dir: Optional[str] = None
    ):
        """
        Initialize IO manager.

        Args:
            location: Output location (CODE or WEB)
            base_dir: Base directory for outputs (default: current dir)
        """
        self.location = location

        if base_dir is None:
            # Default to current directory / output
            self.base_dir = Path.cwd() / "output"
        else:
            self.base_dir = Path(base_dir)

        # Ensure base directory exists
        if self.location == OutputLocation.CODE:
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def supports_filesystem(self) -> bool:
        """
        Check if environment supports filesystem operations.

        Returns:
            True if filesystem is available
        """
        return self.location == OutputLocation.CODE

    def create_session_directory(self) -> Path:
        """
        Create timestamped output directory for this session.

        Format: competitive-intelligence-YYYYMMDD-HHMMSS

        Returns:
            Path to created directory
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dir_name = f"competitive-intelligence-{timestamp}"

        output_dir = self.base_dir / dir_name

        if self.location == OutputLocation.CODE:
            output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir

    def write_module(
        self,
        schema_type: SchemaType,
        data: Dict[str, Any],
        output_dir: Path,
        validate: bool = True
    ) -> Path:
        """
        Write a single JSON module.

        Args:
            schema_type: Type of module to write
            data: Module data
            output_dir: Output directory
            validate: Whether to validate against schema (default: True)

        Returns:
            Path to written file

        Raises:
            ValidationError: If validation fails
            TypeError: If data is not JSON serializable
        """
        # Validate against schema if requested
        if validate:
            result = validate_output(schema_type, data)
            if not result.is_valid:
                raise ValueError(
                    f"Validation failed for {schema_type.value}: {result.errors}"
                )

        # Ensure output directory exists
        if self.location == OutputLocation.CODE:
            output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from schema type
        filename = f"{schema_type.value}.json"
        file_path = output_dir / filename

        # Write JSON file
        if self.location == OutputLocation.CODE:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Web environment: could write to in-memory storage
            # For now, still write to file if possible
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

        return file_path

    def write_all_modules(
        self,
        modules_data: Dict[SchemaType, Dict[str, Any]],
        output_dir: Path,
        validate: bool = True
    ) -> List[Path]:
        """
        Write all modules at once.

        Args:
            modules_data: Dict mapping schema types to data
            output_dir: Output directory
            validate: Whether to validate each module

        Returns:
            List of paths to written files
        """
        written_files = []

        for schema_type, data in modules_data.items():
            try:
                file_path = self.write_module(
                    schema_type=schema_type,
                    data=data,
                    output_dir=output_dir,
                    validate=validate
                )
                written_files.append(file_path)
            except Exception as e:
                # Log error but continue with other modules
                print(f"Error writing {schema_type.value}: {e}")

        return written_files

    def get_output_summary(self, output_dir: Path) -> Dict[str, Any]:
        """
        Get summary of outputs in directory.

        Args:
            output_dir: Output directory to summarize

        Returns:
            Dict with summary information
        """
        summary = {
            "output_directory": str(output_dir),
            "files_written": [],
            "total_size_bytes": 0
        }

        if output_dir.exists():
            for file_path in output_dir.glob("*.json"):
                file_info = {
                    "filename": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "path": str(file_path)
                }
                summary["files_written"].append(file_info)
                summary["total_size_bytes"] += file_info["size_bytes"]

        summary["file_count"] = len(summary["files_written"])

        return summary


def generate_metadata(
    context: Dict[str, Any],
    phases_executed: List[str],
    lenses_applied: List[str],
    data_sources: List[Dict[str, Any]],
    overall_confidence: str,
    warnings: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate metadata module from workflow information.

    Args:
        context: Analysis context dict
        phases_executed: List of phase names
        lenses_applied: List of lens names
        data_sources: List of data source dicts
        overall_confidence: Overall confidence level
        warnings: Optional warnings list

    Returns:
        Metadata dict ready for writing
    """
    metadata = {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat() + "Z",
        "analysis_context": context,
        "phases_executed": phases_executed,
        "lenses_applied": lenses_applied,
        "data_sources": data_sources,
        "overall_confidence": overall_confidence
    }

    if warnings:
        metadata["warnings"] = warnings

    return metadata


def create_output_directory(
    base_dir: Optional[str] = None,
    location: OutputLocation = OutputLocation.CODE
) -> Path:
    """
    Convenience function to create output directory.

    Args:
        base_dir: Base directory (default: current dir / output)
        location: Output location (CODE or WEB)

    Returns:
        Path to created directory
    """
    manager = IOManager(location=location, base_dir=base_dir)
    return manager.create_session_directory()


def write_module(
    schema_type: SchemaType,
    data: Dict[str, Any],
    output_dir: Path,
    validate: bool = True
) -> Path:
    """
    Convenience function to write a single module.

    Args:
        schema_type: Type of module
        data: Module data
        output_dir: Output directory
        validate: Whether to validate

    Returns:
        Path to written file
    """
    manager = IOManager(location=OutputLocation.CODE)
    return manager.write_module(
        schema_type=schema_type,
        data=data,
        output_dir=output_dir,
        validate=validate
    )


def write_all_modules(
    modules_data: Dict[SchemaType, Dict[str, Any]],
    output_dir: Path,
    validate: bool = True
) -> List[Path]:
    """
    Convenience function to write all modules.

    Args:
        modules_data: Dict mapping schema types to data
        output_dir: Output directory
        validate: Whether to validate

    Returns:
        List of paths to written files
    """
    manager = IOManager(location=OutputLocation.CODE)
    return manager.write_all_modules(
        modules_data=modules_data,
        output_dir=output_dir,
        validate=validate
    )


# Helper functions for common operations

def get_module_filename(schema_type: SchemaType) -> str:
    """
    Get filename for a schema type.

    Args:
        schema_type: Schema type

    Returns:
        Filename (e.g., "metadata.json")
    """
    return f"{schema_type.value}.json"


def list_output_directories(base_dir: Optional[str] = None) -> List[Path]:
    """
    List all competitive intelligence output directories.

    Args:
        base_dir: Base directory to search (default: current dir / output)

    Returns:
        List of directory paths
    """
    if base_dir is None:
        base_path = Path.cwd() / "output"
    else:
        base_path = Path(base_dir)

    if not base_path.exists():
        return []

    # Find directories matching pattern
    pattern = "competitive-intelligence-*"
    return sorted(base_path.glob(pattern), reverse=True)  # Most recent first


def get_latest_output_directory(base_dir: Optional[str] = None) -> Optional[Path]:
    """
    Get the most recent output directory.

    Args:
        base_dir: Base directory to search

    Returns:
        Path to latest directory, or None if none exist
    """
    directories = list_output_directories(base_dir)
    return directories[0] if directories else None


def read_module(
    schema_type: SchemaType,
    output_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Read a module from output directory.

    Args:
        schema_type: Type of module to read
        output_dir: Output directory

    Returns:
        Module data dict, or None if file doesn't exist
    """
    filename = get_module_filename(schema_type)
    file_path = output_dir / filename

    if not file_path.exists():
        return None

    with open(file_path, 'r') as f:
        return json.load(f)


def validate_output_directory(output_dir: Path) -> Dict[str, Any]:
    """
    Validate all modules in output directory.

    Args:
        output_dir: Output directory to validate

    Returns:
        Dict with validation results
    """
    results = {
        "valid": True,
        "modules_validated": 0,
        "errors": []
    }

    for schema_type in SchemaType:
        module_data = read_module(schema_type, output_dir)
        if module_data is not None:
            result = validate_output(schema_type, module_data)
            results["modules_validated"] += 1

            if not result.is_valid:
                results["valid"] = False
                results["errors"].append({
                    "module": schema_type.value,
                    "errors": result.errors
                })

    return results
