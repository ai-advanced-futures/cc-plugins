"""File parsing utilities for operational assessment."""

import csv
import json
from pathlib import Path
from typing import Dict, Any


class FileParser:
    """Parse uploaded files into assessment input data."""

    def parse_org_chart(self, file_path: str) -> Dict[str, Any]:
        """Parse org chart file (CSV/JSON) to extract team data."""
        path = Path(file_path)

        if path.suffix.lower() == '.csv':
            return self._parse_org_chart_csv(path)
        elif path.suffix.lower() == '.json':
            return self._parse_org_chart_json(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    def _parse_org_chart_csv(self, path: Path) -> Dict[str, Any]:
        """Parse CSV org chart."""
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        headcount = len(rows)
        leadership_roles = [row for row in rows if not row.get('Manager')]

        return {
            'headcount': headcount,
            'leadership_count': len(leadership_roles)
        }

    def _parse_org_chart_json(self, path: Path) -> Dict[str, Any]:
        """Parse JSON org chart."""
        with open(path, 'r') as f:
            data = json.load(f)

        if isinstance(data, list):
            headcount = len(data)
        elif isinstance(data, dict) and 'employees' in data:
            headcount = len(data['employees'])
        else:
            headcount = 0

        return {'headcount': headcount}

    def parse_tech_docs(self, file_path: str) -> Dict[str, Any]:
        """Parse tech documentation to extract technology data."""
        path = Path(file_path)

        if path.suffix.lower() == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
            return {
                'tech_stack': data.get('technologies', []),
                'architecture_quality': data.get('architecture_score', 50)
            }
        else:
            return {'tech_stack': [], 'architecture_quality': 50}
