"""Find another plugin with probe-plugin.sh (standard section 9)."""
from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "probe-plugin.sh"


def find(name: str, probe_path: str) -> Path | None:
    result = subprocess.run(["bash", str(SCRIPT), name, probe_path], capture_output=True, text=True)
    out = result.stdout.strip()
    return Path(out) if result.returncode == 0 and out else None
