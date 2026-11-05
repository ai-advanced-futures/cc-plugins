"""The cross-graph code of the knowledge plugin (spec section 7.3)."""


class UsageError(Exception):
    """Wrong input or configuration. The command exits 2."""


class DataError(Exception):
    """A graph data error. The command exits 1."""
