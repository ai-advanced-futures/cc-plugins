"""
TargetManager - Helper for managing target-based directory structures.

This module provides utilities for organizing Phase 3 artifacts by target company
within the .corporate-development/targets/{target-slug}/ directory structure.
"""
from pathlib import Path
from typing import Optional


class TargetManager:
    """
    Manages target-based directory structures for operational DD artifacts.

    This class provides utilities for creating and accessing target-specific
    directories within .corporate-development/targets/{target-slug}/.

    Attributes:
        cd_dir (Path): Path to the .corporate-development directory
    """

    def __init__(self, cd_dir: Path):
        """
        Initialize TargetManager.

        Args:
            cd_dir: Path to the .corporate-development directory
        """
        self.cd_dir = Path(cd_dir)

    def get_target_dir(self, target_slug: str) -> Path:
        """
        Get the directory path for a target, creating it if it doesn't exist.

        Args:
            target_slug: Slugified name of the target company (e.g., "acme-corp")

        Returns:
            Path: Path object pointing to .corporate-development/targets/{target-slug}/

        Example:
            >>> manager = TargetManager(Path(".corporate-development"))
            >>> target_dir = manager.get_target_dir("acme-corp")
            >>> print(target_dir)
            .corporate-development/targets/acme-corp
        """
        target_dir = self.cd_dir / "targets" / target_slug
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def get_subfolder(self, target_slug: str, subfolder: str) -> Path:
        """
        Get a subfolder within a target directory, creating it if it doesn't exist.

        Args:
            target_slug: Slugified name of the target company
            subfolder: Name of the subfolder (e.g., "analysis", "reports")

        Returns:
            Path: Path object pointing to the subfolder

        Example:
            >>> manager = TargetManager(Path(".corporate-development"))
            >>> reports_dir = manager.get_subfolder("acme-corp", "reports")
            >>> print(reports_dir)
            .corporate-development/targets/acme-corp/reports
        """
        subfolder_path = self.get_target_dir(target_slug) / subfolder
        subfolder_path.mkdir(parents=True, exist_ok=True)
        return subfolder_path

    def list_targets(self) -> list[str]:
        """
        List all target slugs that have directories.

        Returns:
            list[str]: List of target slugs (directory names)

        Example:
            >>> manager = TargetManager(Path(".corporate-development"))
            >>> targets = manager.list_targets()
            >>> print(targets)
            ['acme-corp', 'techco-inc', 'startup-xyz']
        """
        targets_dir = self.cd_dir / "targets"
        if not targets_dir.exists():
            return []

        return [
            d.name for d in targets_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

    def target_exists(self, target_slug: str) -> bool:
        """
        Check if a target directory already exists.

        Args:
            target_slug: Slugified name of the target company

        Returns:
            bool: True if the target directory exists, False otherwise

        Example:
            >>> manager = TargetManager(Path(".corporate-development"))
            >>> if manager.target_exists("acme-corp"):
            ...     print("Target already exists")
        """
        target_dir = self.cd_dir / "targets" / target_slug
        return target_dir.exists() and target_dir.is_dir()

    def get_target_file(self, target_slug: str, filename: str,
                       subfolder: Optional[str] = None) -> Path:
        """
        Get the path to a file within a target directory.

        Args:
            target_slug: Slugified name of the target company
            filename: Name of the file
            subfolder: Optional subfolder within the target directory

        Returns:
            Path: Path object pointing to the file

        Note:
            This method does NOT create the file, only returns its path.

        Example:
            >>> manager = TargetManager(Path(".corporate-development"))
            >>> report_path = manager.get_target_file("acme-corp", "analysis.md")
            >>> print(report_path)
            .corporate-development/targets/acme-corp/analysis.md

            >>> detailed_report = manager.get_target_file(
            ...     "acme-corp", "detailed.md", subfolder="reports"
            ... )
            >>> print(detailed_report)
            .corporate-development/targets/acme-corp/reports/detailed.md
        """
        if subfolder:
            base_dir = self.get_subfolder(target_slug, subfolder)
        else:
            base_dir = self.get_target_dir(target_slug)

        return base_dir / filename
