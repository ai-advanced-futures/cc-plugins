"""`.claude/ddd.json`: the one file that names the bundle directory."""
import json
from pathlib import Path, PurePosixPath

from . import UsageError

CONFIG = Path(".claude") / "ddd.json"
DEFAULT_DIR = "docs/domain"
OKF_VERSION = "0.2"


def config_path(root: Path) -> Path:
    return root / CONFIG


def check_dir(directory: str) -> str:
    """The bundle directory is relative to the repository root and stays
    inside it. Returns it with no `./` part, no `//`, and no trailing slash."""
    clean = directory.strip()
    parts = PurePosixPath(clean).parts
    # No parts is "" or ".": the bundle would be the whole repository.
    if not parts or clean.startswith("/") or ".." in parts:
        raise UsageError(f"the bundle directory must be a path inside the "
                         f"repository, as in {DEFAULT_DIR}: got {directory!r}")
    return PurePosixPath(*parts).as_posix()


def read_config(root: Path) -> dict:
    path = config_path(root)
    if not path.is_file():
        raise UsageError(f"{CONFIG} is missing in {root}. Run /business-domain:setup first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise UsageError(f"cannot read {path}: {error}")
    if not isinstance(data, dict) or not isinstance(data.get("dir"), str):
        raise UsageError(f"{path} has no 'dir' string")
    data["dir"] = check_dir(data["dir"])
    return data


def bundle_dir(root: Path) -> Path:
    """The bundle directory. Exit 2 when the config or the directory is
    absent: that is wrong input, not a finding."""
    bundle = root / read_config(root)["dir"]
    if not bundle.is_dir():
        raise UsageError(f"the bundle {bundle} does not exist. "
                         f"Run /business-domain:setup first.")
    return bundle


def write_config(root: Path, directory: str, plugin_version: str) -> Path:
    path = config_path(root)
    data = {"dir": check_dir(directory), "okf_version": OKF_VERSION,
            "plugin_version": plugin_version}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path
