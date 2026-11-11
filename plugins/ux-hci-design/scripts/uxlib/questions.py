"""Remove the open-questions file of an agent before the skill starts the agent again.

The skill ux-design runs this through ux_graph.py, because its allowed-tools
approve ux_graph.py and approve no `rm` (STORY-136, STORY-343).

The command holds the folder open from the check to the delete (STORY-370). It opens each part of the
path below the project root with O_NOFOLLOW, refuses each link, and deletes the file relative to the
open folder. So a swap of a folder for a link after the check does not change which file it deletes.
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import NamedTuple

from uxlib import DataError, UsageError
from uxlib.bundle import shown

QUESTIONS_FILE = "open-questions.md"
REVIEWERS = ("accessibility-reviewer", "usability-reviewer", "ai-hci-reviewer")

# The open folder needs these calls. Windows has no dir_fd for open, stat and unlink, and no O_NOFOLLOW.
HELD = (all(call in os.supports_dir_fd for call in (os.open, os.stat, os.unlink))
        and os.stat in os.supports_follow_symlinks
        and hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY"))


class Folder(NamedTuple):
    """A checked folder: its path below the root, and its open handle (None where HELD is False)."""
    path: Path
    fd: int | None
    exists: bool = True


def close(folder) -> None:
    if folder is not None and folder.fd is not None:
        os.close(folder.fd)


def _is_link(path) -> bool:
    return path.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(path))


def _link_text(root, link) -> str:
    return f"{shown(root, link)} is a link to {shown(root, link.resolve())}"


def _link_error(root, link, kind=DataError, base=None) -> Exception:
    line = _link_text(root, link)
    if base is not None:  # the folder of a reviewer keeps the words of STORY-343
        return kind(f"{shown(root, base)} is a symbolic link, or is in one: {line}. Remove the file yourself")
    return kind(f"{line}: remove the file yourself")


def _parts_below_root(root, output) -> tuple[str, ...] | None:
    """The parts of the output path below the root, as given. None when the path does not go into the root.

    A link above the root is followed (for example /tmp -> /private/tmp). A link that goes into the root is refused.
    """
    given = Path(str(output))
    if not given.is_absolute():
        return given.parts
    for count in range(1, len(given.parts) + 1):
        prefix = Path(*given.parts[:count])
        real = prefix.resolve()
        if real == root:
            return given.parts[count:]
        if root in real.parents:
            raise _link_error(root, prefix)
    return None


def _open_below(root, parent, part, kind=DataError, base=None) -> Folder | None:
    """Open the folder `part` in `parent` with no link followed. None when it does not exist."""
    path = parent.path / part
    if parent.fd is None:
        if _is_link(path):
            raise _link_error(root, path, kind, base)
        return Folder(path, None) if path.is_dir() else None
    try:
        return Folder(path, os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent.fd))
    except OSError as error:
        if os.path.islink(path):  # O_DIRECTORY with O_NOFOLLOW gives ENOTDIR for a link (macOS, Linux), ELOOP on some systems
            raise _link_error(root, path, kind, base) from None
        if isinstance(error, (FileNotFoundError, NotADirectoryError)):
            return None
        raise


def _holds_pages_of_a_run(folder) -> bool:
    from uxlib.ingest import PAGES_FILE

    try:
        if folder.fd is None:
            if (folder.path / PAGES_FILE).is_symlink():
                return False
            text = (folder.path / PAGES_FILE).read_bytes()
        else:
            fd = os.open(PAGES_FILE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder.fd)
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    return False
                with os.fdopen(fd, "rb", closefd=False) as handle:
                    text = handle.read()
            finally:
                os.close(fd)
        data = json.loads(text.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and isinstance(data.get("run"), str) and isinstance(data.get("files"), dict)


def run_folder(root, output) -> Folder:
    """The output folder, open, only when it is a folder of a ux-design run (STORY-366, STORY-370).

    A folder of a run has the name `.ux-artifacts`, or holds the `pages.json` of a run, and no part of its
    path below the root is a link. The skill writes in `<project>/.ux-artifacts`, and `<project>` can be a
    folder below the git root. So a folder of the person, such as `docs/`, or a link `.ux-artifacts -> docs`,
    is refused, also when `docs` holds a `pages.json`. The caller closes the folder.
    """
    from uxlib.ingest import ARTIFACTS, output_folder

    root = Path(root).resolve()
    parts = _parts_below_root(root, output)
    link = None  # the first link of the path, found before the checks that follow it
    if parts is not None and ".." not in parts:
        link = next((root.joinpath(*parts[:count]) for count in range(1, len(parts) + 1)
                     if _is_link(root.joinpath(*parts[:count]))), None)
    try:
        output_folder(root, output)  # the usage checks of main: inside the root, not the root, a folder
    except UsageError as error:
        if link is None:
            raise
        raise UsageError(f"{error} ({_link_text(root, link)})") from None  # exit 2, as on main (STORY-343)
    if link is not None:
        raise _link_error(root, link)
    assert parts is not None  # output_folder refused each path that does not go into the root
    if ".." in parts:
        raise UsageError(f"the output folder must be a path with no '..': {output!r}")
    folder = Folder(root, os.open(root, os.O_RDONLY | os.O_DIRECTORY) if HELD else None)
    try:
        for part in parts:
            below = _open_below(root, folder, part)
            if below is None:  # the handler below closes the folder that is still open
                raise UsageError(f"{output} is not a folder")
            close(folder)
            folder = below
        if folder.path.name != ARTIFACTS and not _holds_pages_of_a_run(folder):
            raise DataError(f"{shown(root, folder.path)} is not a folder of a ux-design run: its name is not "
                            f"{ARTIFACTS}, and it holds no pages.json of a run. Remove the file yourself")
    except BaseException:
        close(folder)
        raise
    return folder


def path_of(root, output, reviewer=None) -> Folder:
    """The open folder that holds the open-questions file of the run, or of 1 reviewer.

    `exists` is False when the folder of the reviewer does not exist. The caller closes the folder.
    """
    root = Path(root).resolve()
    if reviewer is not None and reviewer not in REVIEWERS:
        raise UsageError(f"{reviewer!r} is not a reviewer: use {', '.join(REVIEWERS)}")
    folder = run_folder(root, output)
    if reviewer is None:
        return folder
    path = folder.path / "reviews" / reviewer
    for part in ("reviews", reviewer):
        try:
            below = _open_below(root, folder, part, UsageError, path)  # exit 2, as on main (STORY-343)
        finally:
            close(folder)
        if below is None:
            return Folder(path, None, exists=False)
        folder = below
    return folder


def remove(root, output, reviewer=None) -> str:
    root = Path(root).resolve()
    folder = path_of(root, output, reviewer)
    target = folder.path / QUESTIONS_FILE
    try:
        if not folder.exists:
            return f"no file {shown(root, target)}"
        try:
            if folder.fd is None:
                mode = os.lstat(target).st_mode
            else:
                mode = os.stat(QUESTIONS_FILE, dir_fd=folder.fd, follow_symlinks=False).st_mode
        except FileNotFoundError:
            return f"no file {shown(root, target)}"
        if stat.S_ISLNK(mode):
            raise DataError(f"{shown(root, target)} is a symbolic link: remove it yourself")
        if not stat.S_ISREG(mode):
            raise DataError(f"{shown(root, target)} is not a file: remove it yourself")
        try:
            if folder.fd is None:
                os.unlink(target)
            else:
                os.unlink(QUESTIONS_FILE, dir_fd=folder.fd)
        except FileNotFoundError:  # the file went away between the stat and the unlink
            return f"no file {shown(root, target)}"
        except OSError as error:
            raise DataError(f"{shown(root, target)} is not removed ({error.strerror}): remove it yourself") from None
        return f"removed {shown(root, target)}"
    finally:
        close(folder)
