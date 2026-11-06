"""The save code and the brain check of the competitive-intelligence graph (standard section 8).

These modules are adapted copies of the general modules of plugins/system-design/scripts/sdlib.
No file can read a path outside its plugin, so each brain keeps its own copy.
"""


class UsageError(Exception):
    """Wrong input or configuration. The command exits 2."""


class DataError(Exception):
    """A graph data error. The command exits 1."""
