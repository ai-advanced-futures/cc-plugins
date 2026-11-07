"""The cross-graph code of the knowledge plugin (spec section 7.3)."""


class UsageError(Exception):
    """Wrong input or configuration. The command exits 2."""


class DataError(Exception):
    """A graph data error. The command exits 1."""


class FileError(Exception):
    """A read or a write of a file failed, after the retries of a short lock (okf.short_lock). The command exits 1.
    It is not a DataError, so no caller takes a file that it cannot read for a file with no data."""

    def __init__(self, path, verb, error, tries):
        self.path, self.error = path, error
        self.reason = f"{verb} the file failed after {tries} {'try' if tries == 1 else 'tries'}: {error.strerror or error}"
        super().__init__(f"{self.reason} ({path})")
