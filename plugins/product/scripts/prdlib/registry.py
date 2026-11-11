"""Where each type lives on disk.

The LinkML schema owns the fields of a type. It cannot say which directory
holds the pages of that type, so this table does. test_registry.py asserts the
two agree on the set of type names: a new class in the schema cannot land
without a home here.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TypeSpec:
    name: str
    prefix: str | None
    directory: str | None
    bundle: str
    level: int | None = None


_SPECS = (
    TypeSpec("Product", None, None, "prd"),
    TypeSpec("Problem", "PROBLEM", "problems", "prd"),
    TypeSpec("Persona", "PERSONA", "personas", "prd"),
    TypeSpec("Need", "NEED", "needs", "prd"),
    TypeSpec("Journey", "JOURNEY", "journeys", "prd"),
    TypeSpec("Capability", "CAPABILITY", "capabilities", "prd"),
    TypeSpec("Experience", "EXPERIENCE", "experiences", "prd"),
    TypeSpec("Scope", "SCOPE", "scope", "prd"),
    TypeSpec("Metric", "METRIC", "metrics", "prd"),
    TypeSpec("Business", "BUSINESS", "business", "prd"),
    TypeSpec("GTM", "GTM", "gtm", "prd"),
    TypeSpec("Risk", "RISK", "risks", "prd"),
    TypeSpec("Constraint", "CONSTRAINT", "constraints", "prd"),
    TypeSpec("Decision", "DECISION", "decisions", "prd"),
    TypeSpec("Question", "QUESTION", "questions", "prd"),
    TypeSpec("Project", "PROJECT", "projects", "roadmap"),
    TypeSpec("Milestone", "MILESTONE", "milestones", "roadmap"),
    TypeSpec("Epic", "EPIC", "epics", "roadmap", level=1),
    TypeSpec("Feature", "FEATURE", "features", "roadmap", level=2),
    TypeSpec("Story", "STORY", "stories", "roadmap", level=3),
    TypeSpec("Task", "TASK", "tasks", "roadmap", level=4),
    TypeSpec("AcceptanceCriterion", "CRITERION", "criteria", "roadmap"),
    TypeSpec("Run", "RUN", "runs", "roadmap"),
    TypeSpec("ClosedItems", None, None, "roadmap"),
)

TYPES = {spec.name: spec for spec in _SPECS}
BY_PREFIX = {spec.prefix: spec for spec in _SPECS if spec.prefix}
BY_DIRECTORY = {(spec.bundle, spec.directory): spec
                for spec in _SPECS if spec.directory}
WORK_ITEMS = ("Epic", "Feature", "Story", "Task")
PRD_TYPES = tuple(s.name for s in _SPECS
                  if s.bundle == "prd" and s.name != "Product")

# The order of the Layout section of the spec. The root index uses it.
# _SPECS is already in that order, so the directories are read from it: a
# type added there cannot lose its index by a second edit that nobody makes.
DIRECTORY_ORDER = {
    bundle: tuple(s.directory for s in _SPECS
                  if s.bundle == bundle and s.directory)
    for bundle in ("prd", "roadmap")
}

CLOSED_STATES = ("done", "released", "cancelled")
# The two states of delivered work: `released` follows `done` in the flow.
DELIVERED_STATES = ("done", "released")
STATES = ("backlog", "ready", "claimed", "in_progress", "in_review",
          "blocked", "done", "released", "cancelled")

ID_RE = re.compile(r"^([A-Z]+)-(\d{2,})$")
RUN_ID_RE = re.compile(r"^RUN-(\d{8})-(\d{6})-([0-9a-f]{4})$")


def spec_for_path(bundle: str, directory: str) -> TypeSpec | None:
    return BY_DIRECTORY.get((bundle, directory))
