"""Bounded child commands, the Git environment for Beads, and atomic JSON files."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile

from . import PlanError

DATA_REF = "refs/dolt/data"

REPO_ENV_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_OBJECT_DIRECTORY", "GIT_DIR",
    "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR", "GIT_NAMESPACE",
}

MAX_BELOW = 4096  # the most pids that a stop reads below a child

_URL_REWRITE = re.compile(r"url\..*\.(?:push)?insteadof", re.IGNORECASE | re.DOTALL)


class CommandError(PlanError):
    """A child command has an unknown effect, not a validation refusal."""


def git_environment():
    """Keep session credentials and identity; remove only repository routing."""
    env = {key: value for key, value in os.environ.items() if key not in REPO_ENV_KEYS}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": ""})
    count = env.get("GIT_CONFIG_COUNT", "0")
    if not count.isdecimal() or not 0 <= int(count) <= 128:
        raise PlanError("session Git configuration count is invalid")
    count = int(count)
    if any("GIT_CONFIG_KEY_" + str(i) not in env or "GIT_CONFIG_VALUE_" + str(i) not in env for i in range(count)):
        raise PlanError("session Git configuration is incomplete")
    # A session URL rewrite routes the backup remote to another address than Beads saved.
    pairs = [(env.pop("GIT_CONFIG_KEY_" + str(i)), env.pop("GIT_CONFIG_VALUE_" + str(i))) for i in range(count)]
    pairs = [(key, value) for key, value in pairs if not _URL_REWRITE.fullmatch(key)]
    for index, (key, value) in enumerate(pairs):
        env["GIT_CONFIG_KEY_" + str(index)] = key
        env["GIT_CONFIG_VALUE_" + str(index)] = value
    count = len(pairs)
    for key, value in (("core.hooksPath", os.devnull), ("protocol.ext.allow", "never"), ("commit.gpgsign", "false")):
        env["GIT_CONFIG_KEY_" + str(count)] = key
        env["GIT_CONFIG_VALUE_" + str(count)] = value
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)
    return env


def _below(pid):
    """The pids below `pid`, from 1 read of the process table (the parent of each process). No table gives `[]`.

    The table is read row by row while processes start and end, so the walk keeps a set of seen pids and a cap, and it never
    lists the pid of this process or of its parent."""
    try:
        table = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True, timeout=10,
                               env={"PATH": "/bin:/usr/bin"}, start_new_session=True)  # a leaf: no process below it
    except (OSError, subprocess.SubprocessError):
        return []
    children = {}
    for line in table.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            children.setdefault(int(parts[1]), []).append(int(parts[0]))
    skip = {os.getpid(), os.getppid()}
    found, seen, queue = [], {pid}, [pid]
    while queue:
        for child in children.get(queue.pop(), []):
            if child in seen or child in skip or len(found) >= MAX_BELOW:
                continue
            seen.add(child)
            found.append(child)
            queue.append(child)
    return found


def _stop_tree(child):
    """Stop the child and each process below it by pid, and never the group of the caller.

    A child that stays in the group of its caller leads no group. `SIGSTOP` first, so it starts no new child while the table is
    read. Accepted: a process that double-forked before the limit has no parent that leads to the child."""
    if child.returncode is not None:  # reaped already (the wait of `communicate` at a Ctrl-C can do it): its pid may be another process
        return
    try:
        os.kill(child.pid, signal.SIGSTOP)
    except (ProcessLookupError, PermissionError):
        pass
    below = []
    try:
        below = _below(child.pid)  # no table: the child still gets its kill below
    finally:
        try:
            os.kill(child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    for pid in below:
        if pid > 1:  # a bad row of the table must not reach init
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass  # gone, or (macOS: EPERM) a zombie


def _reap(child):
    try:
        child.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        for stream in (child.stdin, child.stdout, child.stderr):
            if stream:
                stream.close()


def capture(command, *, cwd, env, timeout=60, stdin=None, own_group=True, pass_fds=()):
    """Bound the command and its children, including a pipe held by a child.

    `own_group=False` keeps the child in the process group of the caller, so a stop of that group (or a Ctrl-C) also stops it.
    The limit then stops the child and each process below it by pid. `pass_fds` keeps these descriptors open in the child (the
    store lock): the child and each process that it starts hold the lock until they end."""
    try:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 encoding="utf-8", errors="replace", start_new_session=own_group, pass_fds=pass_fds)
    except OSError as exc:
        raise CommandError("cannot start a command") from exc
    try:
        out, err = child.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if own_group:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        else:
            _stop_tree(child)
        _reap(child)
        raise CommandError("command timed out; its effect is unknown") from exc
    except KeyboardInterrupt:
        if not own_group:  # a SIGINT to this process alone: the child is not in a group that gets it
            _stop_tree(child)
            _reap(child)
        raise
    return subprocess.CompletedProcess(command, child.returncode, out, err)


def atomic_json(path: Path, value: dict):
    if path.is_symlink():
        raise PlanError("a Plan state file cannot be a symbolic link")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".plan-state-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def dolt_url(url: str) -> str:
    """Use only native Git transports, not Git external helper commands."""
    if url.startswith("/"):
        return "git+" + Path(url).resolve().as_uri()
    if url.startswith(("file://", "https://", "ssh://")):
        return "git+" + url
    match = re.fullmatch(r"([A-Za-z0-9_.@-]+):([^\s:]+)", url)
    if match and "@" in match[1]:
        return "git+ssh://" + match[1] + "/" + match[2]
    raise PlanError("backup needs an absolute file, HTTPS, or SSH Git remote")
