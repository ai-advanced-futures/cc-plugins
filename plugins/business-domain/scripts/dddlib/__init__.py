"""The modules of ddd.py. ddd.py puts this directory's parent on sys.path."""


class UsageError(Exception):
    """Wrong input: no bundle, an unreadable file, a bad argument. Exit 2."""


class DataError(Exception):
    """An error in the bundle data. Exit 1."""
