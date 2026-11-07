"""The project root in each form that a Windows shell gives (STORY-179).

Git Bash gives /c/x, Cygwin gives /cygdrive/c/x, and Windows gives C:/x or C:\\x.
Windows Python reads /c/x as a folder c on the current drive, so native()
changes each form to the drive path first. Standard library only.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

IS_WINDOWS = os.name == "nt"
FORMS = (re.compile(r"[/\\](?:cygdrive[/\\])?([A-Za-z])(?:[/\\](.*))?", re.S),
         re.compile(r"([A-Za-z]):[/\\](.*)", re.S))
_GIVEN: dict[Path, str] = {}


def drive(letter: str) -> str:
    """The folder of a drive letter. A test replaces it to map a drive to a temporary folder."""
    return f"{letter.upper()}:/"


def native(raw: str) -> Path:
    """The path of the platform for a root in one of the forms above.
    Off Windows, and for each other form, the text stays as it is."""
    if IS_WINDOWS:
        for form in FORMS:
            match = form.fullmatch(raw)
            if match:
                rest = (match.group(2) or "").replace("\\", "/").strip("/")
                return Path(drive(match.group(1)) + rest)
    return Path(raw)


def resolve(raw: str) -> Path:
    """The resolved root for the text of --root. It keeps the text, so that a message can name both."""
    root = native(raw).resolve()
    _GIVEN[root] = raw
    return root


def given(root) -> str:
    """The text of --root that gave this root, or the root when no text gave it."""
    return _GIVEN.get(Path(root), str(root))
