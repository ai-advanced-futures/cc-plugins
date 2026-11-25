"""The save code and the brain check of the value-ip graph (standard section 8).

These modules are adapted copies of the general modules of the system-design brain.
No file can read a path outside its plugin, so each brain keeps its own copy.

The code reads no file of another plugin when it runs. Only the tests read other plugins, and `READS` of
`scripts/ci-changes.py` names each edge.
"""


class UsageError(Exception):
    """Wrong input or configuration. The command exits 2."""


class DataError(Exception):
    """A graph data error. The command exits 1."""
