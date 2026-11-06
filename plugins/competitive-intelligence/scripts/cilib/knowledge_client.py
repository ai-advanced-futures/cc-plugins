"""Read other graphs through the knowledge plugin: the probe, then a subprocess (A10)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cilib import DataError

PROBE = Path(__file__).resolve().parents[1] / "probe-plugin.sh"


class Knowledge:
    def __init__(self, root, script):
        self.root = Path(root)
        self.script = Path(script)

    @classmethod
    def find(cls, root):
        result = subprocess.run(["bash", str(PROBE), "knowledge", "scripts/knowledge.py"], capture_output=True, text=True)
        out = result.stdout.strip()
        return cls(root, Path(out) / "scripts" / "knowledge.py") if result.returncode == 0 and out else None

    def _run(self, *args):
        return subprocess.run([sys.executable, str(self.script), "--root", str(self.root), *args],
                              capture_output=True, text=True)

    def show(self, links) -> dict:
        links = sorted(set(links))
        if not links:
            return {}
        result = self._run("show", "--cache-only", *links)
        if result.returncode != 0:
            raise DataError(f"knowledge.py show failed: {result.stderr.strip()}")
        return {entry["link"]: entry for entry in json.loads(result.stdout)}

    def pages(self, graph, type_name=None):
        result = self._run("pages", graph, *(["--type", type_name] if type_name else []))
        if result.returncode == 2:
            return None
        if result.returncode != 0:
            raise DataError(f"knowledge.py pages failed: {result.stderr.strip()}")
        return json.loads(result.stdout)
