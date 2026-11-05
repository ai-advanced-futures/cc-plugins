"""`ddd.py init`: `.claude/ddd.json`, the bundle directory, and `log.md`.

regen writes the root index, so init writes no index itself. A second run
finds each file and changes no byte.
"""
from pathlib import Path

from . import UsageError
from . import logbook, regen, standard
from .config import DEFAULT_DIR, bundle_dir, check_dir, config_path, read_config, write_config
from .schema import plugin_actor, plugin_version


def init(root: Path, directory: str | None) -> list:
    """Make the bundle. Returns each path written, in write order."""
    written = []
    if config_path(root).is_file():
        configured = read_config(root)["dir"]
        if directory and check_dir(directory) != configured:
            raise UsageError(f".claude/ddd.json names {configured}, not "
                             f"{directory}. Edit the file to move the bundle.")
        directory = configured
    else:
        directory = check_dir(directory or DEFAULT_DIR)
        written.append(write_config(root, directory, plugin_version()))
    bundle = root / directory
    bundle.mkdir(parents=True, exist_ok=True)
    log = bundle / "log.md"
    if not log.exists():
        when = logbook.now()
        logbook.append(log, logbook.entry(
            "Setup", f"made the bundle {directory}", plugin_actor(), when), when)
        written.append(log)
    for path in regen.write(root):
        if path not in written:
            written.append(path)
    changes = standard.finish(root)
    if "wrote manifest.md" in changes:
        written.append(bundle_dir(root) / "manifest.md")
    if "wrote the registry entry ddd" in changes:
        written.append(root / ".claude" / "knowledge.json")
    return written
