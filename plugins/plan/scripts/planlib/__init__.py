"""Beads-backed planning, independent of Product installation and Sofa."""


class PlanError(ValueError):
    """A refused operation with no implied successful write."""
