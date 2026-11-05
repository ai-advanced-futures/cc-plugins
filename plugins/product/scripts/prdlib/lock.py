"""One exclusive lock file for every write.

The file sits in the git directory, so it is never in a commit and each
working tree has its own lock. Outside a git repository it sits in
docs/product/.lock. The lock covers one working tree only: between clones,
git is the check, because two claims change the same lines.
"""
import os
import time
from contextlib import contextmanager
from pathlib import Path

from . import UsageError, git
from .tree import product_dir

TIMEOUT_SECONDS = 10.0
STALE_SECONDS = 60.0


def lock_path(root: Path) -> Path:
    found = git.output(root, "rev-parse", "--git-dir")
    if not found:
        return product_dir(root) / ".lock"
    git_dir = Path(found)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return git_dir / "prd.lock"


def _held_since(path: Path):
    """The time in the lock file, or the file's own mtime when the line
    cannot be read, or None when the file is gone. A second process can open
    the file between the holder's exclusive create and its write of the time
    line; the mtime of that half-written file is still a live, recent time,
    so this race must not read as a stale lock to delete."""
    try:
        return float(path.read_text(encoding="utf-8").split()[1])
    except (OSError, IndexError, ValueError):
        try:
            return path.stat().st_mtime
        except OSError:
            return None


@contextmanager
def write_lock(root: Path, *, timeout: float = TIMEOUT_SECONDS,
               stale: float = STALE_SECONDS):
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
            if since is None or time.time() - since > stale:
                path.unlink(missing_ok=True)
                continue
            if time.time() >= deadline:
                raise UsageError(
                    f"{path} is held by another prd.py process. "
                    f"Wait for it to finish, then run the command again.")
            time.sleep(0.1)
    try:
        yield path
    finally:
        _release(path)


def held(path: Path) -> bool:
    """True while the lock file still names this process."""
    try:
        return path.read_text(encoding="utf-8").split()[0] == str(os.getpid())
    except (OSError, IndexError):
        return False


def refresh(path: Path) -> None:
    """Write the time line again, so a long run keeps its own lock.

    A lock older than `stale` is deleted and taken by the next process. A
    holder that runs network calls is longer than that, so it says it is
    still alive after each one. The write is the whole line: a reader that
    catches the file half written falls back to the mtime, which is live.

    The holder can already have lost the lock to a process that found it
    stale. A write then would give one lock to two writers, so the refresh
    stops the run instead. Each change that ran before is on its page.
    """
    if not held(path):
        raise UsageError(
            f"{path} is no longer held by this process: another prd.py "
            f"took it. Run the command again.")
    path.write_text(f"{os.getpid()} {time.time()}\n", encoding="utf-8")


def _release(path: Path) -> None:
    """Remove the lock file, but only while it is still this process's own.

    A writer that runs longer than `stale` has its lock deleted and taken by
    the next process. An unconditional unlink here would then delete that
    second writer's lock and let a third one in beside it.
    """
    try:
        held_by = path.read_text(encoding="utf-8").split()[0]
    except (OSError, IndexError):
        return
    if held_by == str(os.getpid()):
        path.unlink(missing_ok=True)
