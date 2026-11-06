"""Base class for domain-specific integration planning analyzers."""

from typing import List, Optional
from corporate_development.integration_planning.types import (
    IntegrationPlanningInput,
    Activity,
    Priority,
)
from corporate_development.integration_planning.templates import TemplateLibrary


class BaseDomainAnalyzer:
    """Base class for all domain analyzers.

    Subclasses must implement generate_activities() and set DOMAIN_NAME.
    """

    DOMAIN_NAME: str = ""  # Override in subclass

    def __init__(self, template_library: Optional[TemplateLibrary] = None):
        self.template_library = template_library or TemplateLibrary()

    def generate_activities(self, input_data: IntegrationPlanningInput) -> List[Activity]:
        """Generate activities for this domain. Override in subclass if needed."""
        templates = self.template_library.get_templates_by_domain(self.DOMAIN_NAME)
        selected = self._select_templates(templates, input_data)
        return [self._template_to_activity(t) for t in selected]

    def _select_templates(self, templates, input_data):
        return [t for t in templates if self._should_include_template(t, input_data)]

    def _should_include_template(self, template, input_data):
        conditions = template.get("conditions", [])
        if not conditions:
            return True
        return all(self._evaluate_condition(c, input_data) for c in conditions)

    def _evaluate_condition(self, condition: str, input_data: IntegrationPlanningInput) -> bool:
        """Evaluate a single condition string."""
        condition = condition.strip()

        if " == " in condition:
            field, value = condition.split(" == ")
            return getattr(input_data, field.strip(), None) == value.strip().strip("'\"")

        if " != " in condition:
            field, value = condition.split(" != ")
            return getattr(input_data, field.strip(), None) != value.strip().strip("'\"")

        for op in (" <= ", " >= ", " < ", " > "):
            if op in condition:
                field, value = condition.split(op)
                field = field.strip()
                raw = value.strip()
                try:
                    num = int(raw)
                except ValueError:
                    num = float(raw)
                input_value = getattr(input_data, field, None)
                if input_value is None:
                    return False
                if op == " < ":
                    return input_value < num
                if op == " > ":
                    return input_value > num
                if op == " <= ":
                    return input_value <= num
                if op == " >= ":
                    return input_value >= num

        return True  # unknown condition format — skip

    def _template_to_activity(self, template: dict) -> Activity:
        """Convert a template dictionary to an Activity instance."""
        return Activity(
            id=template["id"],
            domain=template["domain"],
            title=template["title"],
            description=template["description"],
            owner=template["owner"],
            day_range=template["default_day_range"],
            priority=Priority(template["priority"]),
            dependencies=template.get("dependencies", []),
            success_criteria=template.get("success_criteria", ""),
            estimated_hours=template.get("estimated_hours"),
        )
