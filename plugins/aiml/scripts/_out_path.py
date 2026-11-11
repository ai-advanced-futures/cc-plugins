"""Shared check of the output path for the 3 emitters of the aiml plugin.

A skill runs an emitter with a grant for the script only, so the grant cannot limit the value of the
output option. The emitter limits it: the output file must be inside the folder `.aiml` of the current
directory. A `..`, an absolute path outside it, and a link to an outside folder are refused.
"""
from __future__ import annotations

import os


def out_path_error(flag: str, path) -> str | None:
    """Return one line of text when `path` is not inside the folder `.aiml` of the current directory, else None."""
    root = os.path.join(os.path.realpath("."), ".aiml")
    if os.path.realpath(path).startswith(root + os.sep):
        return None
    return f"error: {path}: {flag} must be a file inside the folder .aiml of the current directory"
