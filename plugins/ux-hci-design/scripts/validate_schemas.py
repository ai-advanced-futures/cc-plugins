#!/usr/bin/env python3
"""
Schema Validator for UX/HCI Design Plugin
Validates all schema types: Nielsen, Rams, Norman, WCAG, and AI-HCI schemas.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SchemaValidator:
    """Validates UX/HCI schema files with type-specific validation."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate any schema by detecting its type and applying appropriate validation.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Detect schema type and validate accordingly
        schema_type = self._detect_schema_type(schema, schema_path)

        if schema_type == "nielsen":
            return self.validate_nielsen_schema(schema_path)
        elif schema_type == "rams":
            return self.validate_rams_schema(schema_path)
        elif schema_type == "norman":
            return self.validate_norman_schema(schema_path)
        elif schema_type == "wcag":
            return self.validate_wcag_schema(schema_path)
        elif schema_type == "ai-hci":
            return self.validate_ai_hci_schema(schema_path)
        elif schema_type == "output":
            return self.validate_output_schema(schema_path)
        elif schema_type == "ai-paradigm":
            return self.validate_ai_paradigm_schema(schema_path)
        else:
            self.errors.append(f"Unknown schema type: {schema_path}")
            return False, self.errors, self.warnings

    def _detect_schema_type(self, schema: Dict[str, Any], schema_path: Path) -> Optional[str]:
        """Detect the type of schema based on its structure and content."""
        # Check for Nielsen schema
        if 'heuristics' in schema and 'severity_scale' in schema:
            return "nielsen"

        # Check for Rams schema
        if 'principles' in schema and any(p.get('original_german') for p in schema.get('principles', [])):
            return "rams"

        # Check for Norman schema
        if 'principles' in schema and any(p.get('name') == 'Affordances' for p in schema.get('principles', [])):
            return "norman"

        # Check for WCAG schema
        if schema.get('title', '').startswith('WCAG') or 'conformance_levels' in schema:
            return "wcag"

        # Check for AI-HCI schema
        if 'guidelines' in schema and schema.get('organization') == 'Microsoft Research':
            return "ai-hci"

        # Check for AI paradigm schemas (2025-2026 thought leader frameworks)
        if 'paradigm_shift' in schema or 'thought_leader' in schema:
            return "ai-paradigm"
        if schema.get('title', '').startswith(('Outcome-Value', 'AI-Native', 'Intent-Based',
                                                'AI Integration Maturity', 'Human-AI Orchestration',
                                                'Background Agent', 'Hybrid AI-GUI')):
            return "ai-paradigm"

        # Check for output schemas (JSON Schema format)
        if schema.get('$schema', '').startswith('http://json-schema.org/') or \
           schema.get('$schema', '').startswith('https://json-schema.org/'):
            return "output"

        # Check filename as fallback
        filename = schema_path.name.lower()
        if 'nielsen' in filename:
            return "nielsen"
        elif 'rams' in filename:
            return "rams"
        elif 'norman' in filename:
            return "norman"
        elif 'wcag' in filename:
            return "wcag"
        elif 'microsoft' in filename or 'ai-hci' in filename:
            return "ai-hci"

        return None

    def validate_nielsen_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Nielsen's 10 Usability Heuristics schema.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate top-level metadata
        self._validate_metadata(schema)

        # Validate severity scale
        self._validate_severity_scale(schema)

        # Validate heuristics array
        self._validate_heuristics(schema)

        # Validate usage guide
        self._validate_usage_guide(schema)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_metadata(self, schema: Dict[str, Any]) -> None:
        """Validate top-level metadata fields."""
        required_fields = ['title', 'description', 'version', 'author', 'year', 'source']

        for field in required_fields:
            if field not in schema:
                self.errors.append(f"Missing required metadata field: {field}")
            elif not schema.get(field):
                self.errors.append(f"Empty metadata field: {field}")

        # Validate specific field types
        if 'version' in schema and not isinstance(schema['version'], str):
            self.errors.append("'version' must be a string")

        if 'year' in schema and not isinstance(schema['year'], int):
            self.errors.append("'year' must be an integer")

    def _validate_severity_scale(self, schema: Dict[str, Any]) -> None:
        """Validate severity scale structure."""
        if 'severity_scale' not in schema:
            self.errors.append("Missing 'severity_scale' field")
            return

        severity_scale = schema['severity_scale']

        if 'levels' not in severity_scale:
            self.errors.append("Missing 'severity_scale.levels' field")
            return

        levels = severity_scale['levels']
        expected_levels = ['0', '1', '2', '3', '4']

        for level in expected_levels:
            if level not in levels:
                self.errors.append(f"Missing severity level: {level}")
            else:
                level_data = levels[level]
                if 'label' not in level_data:
                    self.errors.append(f"Missing 'label' for severity level {level}")
                if 'description' not in level_data:
                    self.errors.append(f"Missing 'description' for severity level {level}")

    def _validate_heuristics(self, schema: Dict[str, Any]) -> None:
        """Validate heuristics array and individual heuristics."""
        if 'heuristics' not in schema:
            self.errors.append("Missing 'heuristics' field")
            return

        heuristics = schema['heuristics']

        if not isinstance(heuristics, list):
            self.errors.append("'heuristics' must be an array")
            return

        if len(heuristics) != 10:
            self.errors.append(f"Expected 10 heuristics, found {len(heuristics)}")

        seen_numbers = set()

        for idx, heuristic in enumerate(heuristics):
            self._validate_single_heuristic(heuristic, idx, seen_numbers)

    def _validate_single_heuristic(self, heuristic: Dict[str, Any],
                                   idx: int, seen_numbers: set) -> None:
        """Validate a single heuristic entry."""
        context = f"Heuristic at index {idx}"

        # Required top-level fields
        required_fields = [
            'number', 'name', 'short_description', 'detailed_description',
            'key_principles', 'evaluation_criteria', 'common_violations',
            'best_practices', 'remediation_guidance'
        ]

        for field in required_fields:
            if field not in heuristic:
                self.errors.append(f"{context}: Missing required field '{field}'")

        # Validate number field
        if 'number' in heuristic:
            number = heuristic['number']
            if not isinstance(number, int):
                self.errors.append(f"{context}: 'number' must be an integer")
            elif number < 1 or number > 10:
                self.errors.append(f"{context}: 'number' must be between 1 and 10")
            elif number in seen_numbers:
                self.errors.append(f"{context}: Duplicate heuristic number {number}")
            else:
                seen_numbers.add(number)

        # Validate string fields
        string_fields = ['name', 'short_description', 'detailed_description']
        for field in string_fields:
            if field in heuristic:
                if not isinstance(heuristic[field], str):
                    self.errors.append(f"{context}: '{field}' must be a string")
                elif not heuristic[field].strip():
                    self.errors.append(f"{context}: '{field}' cannot be empty")

        # Validate array fields
        array_fields = ['key_principles', 'best_practices']
        for field in array_fields:
            if field in heuristic:
                if not isinstance(heuristic[field], list):
                    self.errors.append(f"{context}: '{field}' must be an array")
                elif len(heuristic[field]) == 0:
                    self.warnings.append(f"{context}: '{field}' is empty")

        # Validate evaluation_criteria
        if 'evaluation_criteria' in heuristic:
            self._validate_evaluation_criteria(heuristic['evaluation_criteria'], context)

        # Validate common_violations
        if 'common_violations' in heuristic:
            self._validate_violations(heuristic['common_violations'], context)

        # Validate remediation_guidance
        if 'remediation_guidance' in heuristic:
            self._validate_remediation(heuristic['remediation_guidance'], context)

    def _validate_evaluation_criteria(self, criteria: Dict[str, Any], context: str) -> None:
        """Validate evaluation criteria structure."""
        if not isinstance(criteria, dict):
            self.errors.append(f"{context}: 'evaluation_criteria' must be an object")
            return

        if 'questions' not in criteria:
            self.errors.append(f"{context}: 'evaluation_criteria' missing 'questions'")
        elif not isinstance(criteria['questions'], list):
            self.errors.append(f"{context}: 'evaluation_criteria.questions' must be an array")
        elif len(criteria['questions']) == 0:
            self.warnings.append(f"{context}: 'evaluation_criteria.questions' is empty")

        if 'what_to_look_for' not in criteria:
            self.errors.append(f"{context}: 'evaluation_criteria' missing 'what_to_look_for'")
        elif not isinstance(criteria['what_to_look_for'], list):
            self.errors.append(f"{context}: 'evaluation_criteria.what_to_look_for' must be an array")

    def _validate_violations(self, violations: List[Dict[str, Any]], context: str) -> None:
        """Validate common violations array."""
        if not isinstance(violations, list):
            self.errors.append(f"{context}: 'common_violations' must be an array")
            return

        if len(violations) == 0:
            self.warnings.append(f"{context}: 'common_violations' is empty")
            return

        for idx, violation in enumerate(violations):
            v_context = f"{context}, violation {idx}"

            required_fields = ['issue', 'example', 'severity']
            for field in required_fields:
                if field not in violation:
                    self.errors.append(f"{v_context}: Missing '{field}'")

            # Validate severity value
            if 'severity' in violation:
                severity = violation['severity']
                if not isinstance(severity, int):
                    self.errors.append(f"{v_context}: 'severity' must be an integer")
                elif severity < 0 or severity > 4:
                    self.errors.append(f"{v_context}: 'severity' must be between 0 and 4")

    def _validate_remediation(self, remediation: Dict[str, Any], context: str) -> None:
        """Validate remediation guidance structure."""
        if not isinstance(remediation, dict):
            self.errors.append(f"{context}: 'remediation_guidance' must be an object")
            return

        required_fields = ['quick_fixes', 'comprehensive_solutions', 'testing_approach']
        for field in required_fields:
            if field not in remediation:
                self.errors.append(f"{context}: 'remediation_guidance' missing '{field}'")
            elif not isinstance(remediation[field], list):
                self.errors.append(f"{context}: 'remediation_guidance.{field}' must be an array")

    def _validate_usage_guide(self, schema: Dict[str, Any]) -> None:
        """Validate usage guide structure."""
        if 'usage_guide' not in schema:
            self.warnings.append("Missing 'usage_guide' field (optional but recommended)")
            return

        usage_guide = schema['usage_guide']

        recommended_fields = [
            'how_to_conduct_evaluation',
            'severity_rating_guidance',
            'reporting_best_practices'
        ]

        for field in recommended_fields:
            if field not in usage_guide:
                self.warnings.append(f"'usage_guide' missing recommended field: {field}")

    def validate_rams_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Dieter Rams' 10 Principles of Good Design schema.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate top-level fields
        required_fields = ['title', 'description', 'version', 'author', 'year', 'principles']
        for field in required_fields:
            if field not in schema:
                self.errors.append(f"Missing required field: {field}")

        # Validate principles array
        if 'principles' in schema:
            principles = schema['principles']
            if not isinstance(principles, list):
                self.errors.append("'principles' must be an array")
            elif len(principles) != 10:
                self.errors.append(f"Expected 10 principles, found {len(principles)}")
            else:
                seen_numbers = set()
                for idx, principle in enumerate(principles):
                    self._validate_rams_principle(principle, idx, seen_numbers)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_rams_principle(self, principle: Dict[str, Any], idx: int, seen_numbers: set) -> None:
        """Validate a single Rams principle."""
        context = f"Principle at index {idx}"

        required_fields = ['number', 'name', 'original_german', 'short_description',
                           'detailed_description', 'key_principles', 'evaluation_criteria',
                           'common_violations', 'best_practices']

        for field in required_fields:
            if field not in principle:
                self.errors.append(f"{context}: Missing required field '{field}'")

        # Validate number
        if 'number' in principle:
            number = principle['number']
            if not isinstance(number, int):
                self.errors.append(f"{context}: 'number' must be an integer")
            elif number < 1 or number > 10:
                self.errors.append(f"{context}: 'number' must be between 1 and 10")
            elif number in seen_numbers:
                self.errors.append(f"{context}: Duplicate principle number {number}")
            else:
                seen_numbers.add(number)

        # Validate evaluation criteria
        if 'evaluation_criteria' in principle:
            criteria = principle['evaluation_criteria']
            if not isinstance(criteria, dict):
                self.errors.append(f"{context}: 'evaluation_criteria' must be an object")
            elif 'questions' not in criteria:
                self.errors.append(f"{context}: 'evaluation_criteria' missing 'questions'")

    def validate_norman_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Don Norman's Interaction Design Principles schema.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate top-level fields
        required_fields = ['title', 'description', 'version', 'author', 'principles']
        for field in required_fields:
            if field not in schema:
                self.errors.append(f"Missing required field: {field}")

        # Validate principles array
        if 'principles' in schema:
            principles = schema['principles']
            if not isinstance(principles, list):
                self.errors.append("'principles' must be an array")
            elif len(principles) < 5:
                self.warnings.append(f"Expected at least 5 principles, found {len(principles)}")

            seen_numbers = set()
            for idx, principle in enumerate(principles):
                self._validate_norman_principle(principle, idx, seen_numbers)

        # Validate interaction framework if present
        if 'interaction_framework' in schema:
            framework = schema['interaction_framework']
            if 'seven_stages_of_action' in framework:
                stages = framework['seven_stages_of_action']
                if 'stages' in stages and len(stages['stages']) != 7:
                    self.warnings.append("Seven stages of action should contain 7 stages")

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_norman_principle(self, principle: Dict[str, Any], idx: int, seen_numbers: set) -> None:
        """Validate a single Norman principle."""
        context = f"Principle at index {idx}"

        required_fields = ['number', 'name', 'short_description', 'detailed_description',
                           'key_principles', 'evaluation_criteria', 'common_violations',
                           'best_practices']

        for field in required_fields:
            if field not in principle:
                self.errors.append(f"{context}: Missing required field '{field}'")

        # Validate number
        if 'number' in principle:
            number = principle['number']
            if not isinstance(number, int):
                self.errors.append(f"{context}: 'number' must be an integer")
            elif number in seen_numbers:
                self.errors.append(f"{context}: Duplicate principle number {number}")
            else:
                seen_numbers.add(number)

    def validate_wcag_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate WCAG 2.2 Accessibility Guidelines schema.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate top-level fields
        required_fields = ['title', 'description', 'version', 'principles']
        for field in required_fields:
            if field not in schema:
                self.errors.append(f"Missing required field: {field}")

        # Validate conformance levels
        if 'conformance_levels' in schema:
            levels = schema['conformance_levels']
            if 'A' not in levels or 'AA' not in levels:
                self.errors.append("Missing conformance level definitions for A and/or AA")

        # Validate principles array
        if 'principles' in schema:
            principles = schema['principles']
            if not isinstance(principles, list):
                self.errors.append("'principles' must be an array")
            elif len(principles) != 4:
                self.warnings.append(f"WCAG 2.2 has 4 principles, found {len(principles)}")

            for idx, principle in enumerate(principles):
                self._validate_wcag_principle(principle, idx)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_wcag_principle(self, principle: Dict[str, Any], idx: int) -> None:
        """Validate a single WCAG principle."""
        context = f"Principle at index {idx}"

        required_fields = ['code', 'name', 'description', 'guidelines']
        for field in required_fields:
            if field not in principle:
                self.errors.append(f"{context}: Missing required field '{field}'")

        # Validate guidelines
        if 'guidelines' in principle:
            guidelines = principle['guidelines']
            if not isinstance(guidelines, list):
                self.errors.append(f"{context}: 'guidelines' must be an array")
            else:
                for g_idx, guideline in enumerate(guidelines):
                    g_context = f"{context}, guideline {g_idx}"
                    if 'success_criteria' not in guideline:
                        self.errors.append(f"{g_context}: Missing 'success_criteria'")
                    elif not isinstance(guideline['success_criteria'], list):
                        self.errors.append(f"{g_context}: 'success_criteria' must be an array")
                    else:
                        for sc in guideline['success_criteria']:
                            if 'level' in sc and sc['level'] not in ['A', 'AA', 'AAA']:
                                self.errors.append(f"{g_context}: Invalid conformance level '{sc['level']}'")

    def validate_ai_hci_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Microsoft's 18 Guidelines for Human-AI Interaction schema.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate top-level fields
        required_fields = ['title', 'description', 'version', 'organization', 'guidelines']
        for field in required_fields:
            if field not in schema:
                self.errors.append(f"Missing required field: {field}")

        # Validate guidelines array
        if 'guidelines' in schema:
            guidelines = schema['guidelines']
            if not isinstance(guidelines, list):
                self.errors.append("'guidelines' must be an array")
            elif len(guidelines) != 18:
                self.warnings.append(f"Expected 18 guidelines, found {len(guidelines)}")

            seen_numbers = set()
            for idx, guideline in enumerate(guidelines):
                self._validate_ai_hci_guideline(guideline, idx, seen_numbers)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_ai_hci_guideline(self, guideline: Dict[str, Any], idx: int, seen_numbers: set) -> None:
        """Validate a single AI-HCI guideline."""
        context = f"Guideline at index {idx}"

        required_fields = ['guideline_number', 'guideline_name', 'category',
                           'interaction_phase', 'description', 'evaluation_criteria']

        for field in required_fields:
            if field not in guideline:
                self.errors.append(f"{context}: Missing required field '{field}'")

        # Validate guideline number
        if 'guideline_number' in guideline:
            number = guideline['guideline_number']
            if not isinstance(number, int):
                self.errors.append(f"{context}: 'guideline_number' must be an integer")
            elif number < 1 or number > 18:
                self.errors.append(f"{context}: 'guideline_number' must be between 1 and 18")
            elif number in seen_numbers:
                self.errors.append(f"{context}: Duplicate guideline number {number}")
            else:
                seen_numbers.add(number)

        # Validate category
        valid_categories = ['Initially', 'During', 'During interaction', 'When wrong', 'Over time']
        if 'category' in guideline and guideline['category'] not in valid_categories:
            self.warnings.append(f"{context}: Unusual category '{guideline['category']}'")

    def validate_output_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate output artifact schemas (JSON Schema format).

        These are JSON Schema draft-07 schemas used to validate output artifacts
        like personas, journey maps, evaluation reports, and mental models.

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate JSON Schema structure
        if '$schema' not in schema:
            self.errors.append("Missing '$schema' field (required for JSON Schema)")
        else:
            # Check for valid JSON Schema draft
            valid_drafts = [
                'http://json-schema.org/draft-07/schema#',
                'https://json-schema.org/draft-07/schema#',
                'http://json-schema.org/draft-07/schema',
                'https://json-schema.org/draft-07/schema'
            ]
            if schema['$schema'] not in valid_drafts:
                self.warnings.append(f"Unusual JSON Schema version: {schema['$schema']}")

        # Validate required metadata fields
        if 'title' not in schema:
            self.errors.append("Missing 'title' field")

        if 'description' not in schema:
            self.warnings.append("Missing 'description' field (recommended)")

        # Validate schema has type definition
        if 'type' not in schema:
            self.errors.append("Missing 'type' field")

        # Validate properties exist for object schemas
        if schema.get('type') == 'object':
            if 'properties' not in schema:
                self.errors.append("Object schema missing 'properties' field")
            else:
                # Check that properties is a dict
                if not isinstance(schema['properties'], dict):
                    self.errors.append("'properties' must be an object")
                elif len(schema['properties']) == 0:
                    self.warnings.append("Schema has no properties defined")

            # Check for required fields definition
            if 'required' not in schema:
                self.warnings.append("Missing 'required' field (recommended for object schemas)")

        # Validate examples if present (JSON Schema best practice)
        if 'examples' in schema:
            examples = schema['examples']
            if not isinstance(examples, list):
                self.errors.append("'examples' must be an array")
            elif len(examples) == 0:
                self.warnings.append("'examples' array is empty")

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def validate_ai_paradigm_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate AI Paradigm schemas (2025-2026 thought leader frameworks).

        These schemas encode emerging AI UX patterns from thought leaders like:
        - Phil Gilbert (Outcome-Value Framework)
        - Jakob Nielsen (Intent-Based Interaction)
        - Luke Wroblewski (AI Integration Maturity)
        - Phil Schroeder (AI Orchestration)
        - Birdzhan Hassan (Background Agents)

        Args:
            schema_path: Path to the schema JSON file

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"File not found: {schema_path}")
            return False, self.errors, self.warnings

        # Validate top-level fields
        required_fields = ['title', 'description', 'version']
        for field in required_fields:
            if field not in schema:
                self.errors.append(f"Missing required field: {field}")
            elif not schema.get(field):
                self.errors.append(f"Empty required field: {field}")

        # Validate paradigm shift documentation
        if 'paradigm_shift' in schema:
            shift = schema['paradigm_shift']
            if not isinstance(shift, dict):
                self.errors.append("'paradigm_shift' must be an object")
            else:
                if 'from' not in shift and 'to' not in shift:
                    self.warnings.append("'paradigm_shift' should have 'from' and 'to' fields")

        # Validate thought leader attribution if present
        if 'thought_leader' in schema:
            leader = schema['thought_leader']
            if not isinstance(leader, dict):
                self.errors.append("'thought_leader' must be an object")
            elif 'name' not in leader:
                self.warnings.append("'thought_leader' should have a 'name' field")

        # Validate evaluation dimensions/principles
        dimension_keys = ['evaluation_dimensions', 'principles', 'maturity_stages',
                          'orchestration_dimensions', 'pattern_categories', 'primary_metrics']
        found_dimensions = False
        for key in dimension_keys:
            if key in schema:
                found_dimensions = True
                dimensions = schema[key]
                if not isinstance(dimensions, list):
                    self.errors.append(f"'{key}' must be an array")
                elif len(dimensions) == 0:
                    self.errors.append(f"'{key}' array is empty")
                else:
                    # Validate each dimension/principle has required fields
                    for idx, dim in enumerate(dimensions):
                        if not isinstance(dim, dict):
                            self.errors.append(f"{key}[{idx}] must be an object")
                            continue
                        # Check for name/title field
                        if 'name' not in dim and 'category' not in dim and 'stage' not in dim:
                            self.warnings.append(f"{key}[{idx}] missing 'name' or identifier")
                        # Check for description
                        if 'description' not in dim:
                            self.warnings.append(f"{key}[{idx}] missing 'description'")

        if not found_dimensions:
            self.warnings.append("Schema has no evaluation dimensions, principles, or patterns")

        # Validate metrics if present
        if 'metrics' in schema:
            metrics = schema['metrics']
            if not isinstance(metrics, list):
                self.errors.append("'metrics' must be an array")
            else:
                for idx, metric in enumerate(metrics):
                    if not isinstance(metric, dict):
                        self.errors.append(f"metrics[{idx}] must be an object")
                    elif 'name' not in metric:
                        self.warnings.append(f"metrics[{idx}] missing 'name'")

        # Validate evaluation methodology if present
        if 'evaluation_methodology' in schema:
            methodology = schema['evaluation_methodology']
            if not isinstance(methodology, dict):
                self.errors.append("'evaluation_methodology' must be an object")

        # Validate usage guide if present
        if 'usage_guide' in schema:
            guide = schema['usage_guide']
            if not isinstance(guide, dict):
                self.errors.append("'usage_guide' must be an object")
            elif 'when_to_use' not in guide:
                self.warnings.append("'usage_guide' should have 'when_to_use' field")

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings


def validate_all_schemas(plugin_root: Path) -> Tuple[int, int, int]:
    """
    Validate all schemas in the plugin.

    Args:
        plugin_root: Root directory of the plugin

    Returns:
        Tuple of (total_schemas, passed_schemas, failed_schemas)
    """
    validator = SchemaValidator()
    schema_paths = []

    # Find all JSON schemas
    schemas_dir = plugin_root / 'schemas'
    for schema_file in schemas_dir.rglob('*.json'):
        if schema_file.name != 'README.md':
            schema_paths.append(schema_file)

    total = len(schema_paths)
    passed = 0
    failed = 0

    print(f"Found {total} schema(s) to validate")
    print("=" * 80)

    for schema_path in sorted(schema_paths):
        relative_path = schema_path.relative_to(plugin_root)
        print(f"\nValidating: {relative_path}")
        print("-" * 80)

        is_valid, errors, warnings = validator.validate_schema(schema_path)

        if errors:
            print("\n  ERRORS:")
            for error in errors:
                print(f"    • {error}")

        if warnings:
            print("\n  WARNINGS:")
            for warning in warnings:
                print(f"    • {warning}")

        if is_valid:
            print("\n  ✅ PASSED")
            if warnings:
                print(f"     ({len(warnings)} warning(s))")
            passed += 1
        else:
            print(f"\n  ❌ FAILED ({len(errors)} error(s))")
            failed += 1

    return total, passed, failed


def main():
    """Main validation entry point with CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate UX/HCI Design Plugin schemas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all schemas
  python validate_schemas.py

  # Validate specific schema
  python validate_schemas.py --schema schemas/heuristics/nielsen-usability-10.json

  # Validate with verbose output
  python validate_schemas.py --verbose
        """
    )
    parser.add_argument(
        '--schema',
        type=Path,
        help='Path to specific schema file to validate'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output'
    )

    args = parser.parse_args()

    # Determine plugin root
    script_dir = Path(__file__).parent
    plugin_root = script_dir.parent

    if args.schema:
        # Validate single schema
        schema_path = args.schema if args.schema.is_absolute() else plugin_root / args.schema

        if not schema_path.exists():
            print(f"❌ Schema file not found: {schema_path}")
            return 1

        print(f"Validating schema: {schema_path}")
        print("=" * 80)

        validator = SchemaValidator()
        is_valid, errors, warnings = validator.validate_schema(schema_path)

        if errors:
            print("\nERRORS:")
            for error in errors:
                print(f"  • {error}")

        if warnings:
            print("\nWARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")

        if is_valid:
            print("\n✅ Schema validation passed!")
            if warnings:
                print(f"   ({len(warnings)} warning(s))")
            return 0
        else:
            print(f"\n❌ Schema validation failed with {len(errors)} error(s)")
            return 1
    else:
        # Validate all schemas
        total, passed, failed = validate_all_schemas(plugin_root)

        print("\n" + "=" * 80)
        print("\nSUMMARY:")
        print(f"  Total schemas:  {total}")
        print(f"  ✅ Passed:      {passed}")
        print(f"  ❌ Failed:      {failed}")

        if failed == 0:
            print("\n🎉 All schemas validated successfully!")
            return 0
        else:
            print(f"\n❌ {failed} schema(s) failed validation")
            return 1


if __name__ == '__main__':
    sys.exit(main())
