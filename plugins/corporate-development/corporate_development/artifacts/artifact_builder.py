"""Artifact building utilities."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class ArtifactBuilder:
    """Build and write phase artifacts to organized directory structure."""

    def __init__(self, target_name: str, phase_name: str, output_base: Optional[str] = None):
        """Initialize artifact builder for specific target and phase.

        Args:
            target_name: Name of target company
            phase_name: Name of phase (e.g., "phase_3_operational_dd")
            output_base: Base output directory (defaults to .corporate-development)
        """
        self.target_name = target_name
        self.phase_name = phase_name

        # Build target-based directory structure
        base_dir = Path(output_base or ".corporate-development")
        target_slug = target_name.lower().replace(" ", "-").replace("/", "-").replace("_", "-")
        self.target_dir = base_dir / "targets" / target_slug
        self.phase_dir = self.target_dir / phase_name

        # Archive previous run if exists
        if self.phase_dir.exists():
            self._archive_previous_run()

        # Create fresh phase directory
        self.phase_dir.mkdir(parents=True, exist_ok=True)

    def _archive_previous_run(self):
        """Archive previous phase run to history directory."""
        # Include microseconds to ensure uniqueness when tests run quickly
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        history_dir = self.target_dir / "history" / f"{self.phase_name}_{timestamp}"
        history_dir.parent.mkdir(parents=True, exist_ok=True)

        # Use shutil.move to handle non-empty directories
        shutil.move(str(self.phase_dir), str(history_dir))

    def write_markdown(self, name: str, content: str) -> Path:
        """Write markdown artifact to phase directory.

        Args:
            name: Name of file (without extension)
            content: Markdown content

        Returns:
            Path to written file
        """
        filename = f"{name}.md"
        path = self.phase_dir / filename
        path.write_text(content)
        return path

    def write_json(self, name: str, data: dict) -> Path:
        """Write JSON artifact to phase directory.

        Args:
            name: Name of file (without extension)
            data: Data to serialize as JSON

        Returns:
            Path to written file
        """
        filename = f"{name}.json"
        path = self.phase_dir / filename
        path.write_text(json.dumps(data, indent=2))
        return path

    def write_csv(self, name: str, content: str) -> Path:
        """Write CSV artifact to phase directory.

        Args:
            name: Name of file (without extension)
            content: CSV content as string

        Returns:
            Path to written file
        """
        filename = f"{name}.csv"
        path = self.phase_dir / filename
        path.write_text(content)
        return path
