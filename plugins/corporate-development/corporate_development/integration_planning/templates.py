"""Activity template library for integration planning.

This module provides the TemplateLibrary class which loads and manages
activity templates from JSON files. Templates can be filtered by domain
and time period.
"""

import copy
import json
from pathlib import Path
from typing import List, Dict, Optional


class TemplateLibrary:
    """Loads and manages activity templates from JSON.

    Templates are stored in activity_templates.json in the same directory.
    Each template defines a reusable activity with metadata like domain,
    priority, estimated hours, and default time period.
    """

    def __init__(self, template_file: Optional[Path] = None):
        """Initialize template library.

        Args:
            template_file: Path to JSON file with templates.
                          If None, uses default activity_templates.json.
        """
        if template_file is None:
            template_file = Path(__file__).parent / "activity_templates.json"

        self.template_file = template_file
        self.templates = self._load_templates()

    def _load_templates(self) -> List[Dict]:
        """Load templates from JSON file.

        Returns:
            List of template dictionaries.
        """
        if not self.template_file.exists():
            return []

        with open(self.template_file, 'r') as f:
            data = json.load(f)
            return data.get("templates", [])

    def get_all_templates(self) -> List[Dict]:
        """Get all available templates.

        Returns:
            List of all template dictionaries.
        """
        return copy.deepcopy(self.templates)

    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Get a single template by ID.

        Args:
            template_id: Template identifier (e.g., "T-001").

        Returns:
            Template dictionary if found, None otherwise.
        """
        for template in self.templates:
            if template.get("id") == template_id:
                return copy.deepcopy(template)
        return None

    def get_templates_by_domain(self, domain: str) -> List[Dict]:
        """Filter templates by domain.

        Args:
            domain: Domain name (e.g., "Team & Leadership").

        Returns:
            List of templates matching the domain.
        """
        return copy.deepcopy([t for t in self.templates if t.get("domain") == domain])

    def get_templates_by_period(self, period: int) -> List[Dict]:
        """Filter templates by default time period.

        Args:
            period: Period number (1-4).

        Returns:
            List of templates with matching default_period.
        """
        return copy.deepcopy([t for t in self.templates if t.get("default_period") == period])

    def get_templates(self, domain: Optional[str] = None, period: Optional[int] = None) -> List[Dict]:
        """Filter templates by domain and/or period.

        Args:
            domain: Optional domain filter.
            period: Optional period filter (1-4).

        Returns:
            List of templates matching all specified filters.
        """
        results = self.templates

        if domain is not None:
            results = [t for t in results if t.get("domain") == domain]

        if period is not None:
            results = [t for t in results if t.get("default_period") == period]

        return copy.deepcopy(results)
