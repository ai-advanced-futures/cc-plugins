"""One exclusive lock file for each write.

The file sits in the git directory, so it is never in a commit and each
working tree has its own lock. Outside a git repository it sits in
`.claude/ddd.lock`. Two hook runs at the same time take turns.
"""
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from . import UsageError

TIMEOUT_SECONDS = 30.0
STALE_SECONDS = 60.0


def lock_path(root: Path) -> Path:
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--git-dir"],
                                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return root / ".claude" / "ddd.lock"
    git_dir = Path(result.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return git_dir / "ddd.lock"


def _held_since(path: Path):
    """The time in the lock file, or the file's mtime when the line cannot
    be read yet, or None when the file is gone."""
    try:
        return float(path.read_text(encoding="utf-8").split()[1])
    except (OSError, IndexError, ValueError):
        try:
            return path.stat().st_mtime
        except OSError:
            return None


@contextmanager
def write_lock(root: Path, *, timeout: float = TIMEOUT_SECONDS):
    path = lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    while True:
        try:
            handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(handle, f"{os.getpid()} {time.time()}\n".encode())
            os.close(handle)
            break
        except FileExistsError:
            since = _held_since(path)
            if since is None or time.time() - since > STALE_SECONDS:
                path.unlink(missing_ok=True)
                continue
            if time.time() >= deadline:
                raise UsageError(f"{path} is held by another ddd.py process. "
                                 f"Wait for it to finish, then run the "
                                 f"command again.")
            time.sleep(0.1)
    try:
        yield path
    finally:
        try:
            if path.read_text(encoding="utf-8").split()[0] == str(os.getpid()):
                path.unlink(missing_ok=True)
        except (OSError, IndexError):
            pass
