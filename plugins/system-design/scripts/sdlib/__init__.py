"""The save code and the brain check of the system-design graph (spec section 8)."""


class UsageError(Exception):
    """Wrong input or configuration. The command exits 2."""


class DataError(Exception):
    """A graph data error. The command exits 1."""
