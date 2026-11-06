"""Shared I/O helpers for product-finance scripts."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(target: Path, payload: dict) -> None:
    """Write `payload` as indented JSON to `target` atomically.

    Writes to a temp file in the SAME directory (so os.replace is atomic on the
    same filesystem), then renames. Creates parent dirs. Cleans up the temp file
    on any failure before re-raising.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(payload, indent=2))
        os.replace(tmp_name, target)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
