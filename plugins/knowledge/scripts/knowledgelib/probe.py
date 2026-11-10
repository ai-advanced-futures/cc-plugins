"""Find another plugin with probe-plugin.sh (standard section 9).

The script never takes a plugin from the project folder (STORY-202). The checks below apply at each place
that uses a `plugin` or `save_code` value of a manifest: the value is a plugin name or a relative path, the pair
is one of a known brain, the root is an install place, and the save code is inside the root.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from knowledgelib import DataError

SCRIPT = Path(__file__).resolve().parents[1] / "probe-plugin.sh"
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
PART = re.compile(r"[A-Za-z0-9._-]+")
OWN_ROOT = Path(__file__).resolve().parents[2]  # the knowledge plugin, as own_root of the script
# The known pairs of plugin and save_code (issue #829). A PR that adds a brain plugin adds its pair here.
BRAINS = {
    "architecture": "scripts/adr.py",
    "business-case": "scripts/bc_graph.py",
    "business-domain": "scripts/ddd.py",
    "competitive-intelligence": "scripts/ci_graph.py",
    "jtbd-market-discovery": "scripts/jtbd_graph.py",
    "knowledge": "scripts/knowledge_graph.py",
    "product": "scripts/prd.py",
    "system-design": "scripts/system_design.py",
}


def check(name, probe_path) -> None:
    """Refuse a value that is not a plugin name, a path in the plugin, or the pair of a known brain."""
    if not isinstance(name, str) or not NAME.fullmatch(name):
        raise DataError(f"the plugin name is not valid: {name}")
    parts = str(probe_path).split("/")
    if any(part in (".", "..") or not PART.fullmatch(part) for part in parts):
        raise DataError(f"the probe path is not valid: {probe_path}")
    if BRAINS.get(name) != probe_path:
        raise DataError(f"{name} with {probe_path} is not the pair of a known brain")


def config_dir() -> Path | None:
    """The Claude config folder: $CLAUDE_CONFIG_DIR when it is set and not empty, else ~/.claude (STORY-281).

    A relative value gives None, because it would name a folder of the current project (STORY-202). The script
    probe-plugin.sh reads the same variable in the same way.
    """
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return config if config.is_absolute() else None


def install_place(root, name) -> bool:
    root = Path(root).resolve()
    fixed = [OWN_ROOT.parent / name, OWN_ROOT.parent / f"{name}-runtime",
             OWN_ROOT.parent.parent / name / f"{name}-runtime"]
    config = config_dir()
    if config is not None:
        fixed.append(config / "plugins" / name)
    if any(root == place.resolve() for place in fixed):
        return True
    return config is not None and root.is_relative_to((config / "plugins" / "cache").resolve())


def find(name: str, probe_path: str) -> Path | None:
    check(name, probe_path)
    result = subprocess.run(["bash", str(SCRIPT), name, probe_path], capture_output=True, text=True)
    out = result.stdout.strip()
    root = Path(out) if result.returncode == 0 and out else None
    if root is not None and not install_place(root, name):
        raise DataError(f"the probe gave {root}, which is not an install place of {name}")
    return root


def inside(plugin_root, rel) -> Path:
    """The path <plugin_root>/<rel> after symbolic links, which must be in the plugin folder."""
    root = Path(plugin_root).resolve()
    path = (root / rel).resolve()
    if not path.is_relative_to(root):
        raise DataError(f"{rel} is not in the plugin folder {root}")
    return path


def locate(name, save_code, finder=find) -> tuple[Path, Path] | None:
    """The plugin root and the save code of a brain, or None when the plugin is not installed.

    Each caller uses this function, so no caller skips a check. `finder` is a test stand-in, which skips the
    check inside `find`, so this function runs the check too.
    """
    check(name, save_code)
    root = finder(name, save_code)
    return None if root is None else (Path(root), inside(root, save_code))
