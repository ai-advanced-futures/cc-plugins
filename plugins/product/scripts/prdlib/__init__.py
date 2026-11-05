"""The modules of prd.py. prd.py puts this directory's parent on sys.path."""


class UsageError(Exception):
    """A usage error or an internal error. prd.py exits 2."""


class DataError(Exception):
    """An error in the bundle data. prd.py exits 1."""
