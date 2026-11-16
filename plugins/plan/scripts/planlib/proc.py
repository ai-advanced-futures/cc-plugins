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


def capture(command, *, cwd, env, timeout=60, stdin=None):
    """Bound the command and its children, including a pipe held by a child."""
    try:
        child = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 encoding="utf-8", errors="replace", start_new_session=True)
    except OSError as exc:
        raise CommandError("cannot start a command") from exc
    try:
        out, err = child.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            child.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream:
                    stream.close()
        raise CommandError("command timed out; its effect is unknown") from exc
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
