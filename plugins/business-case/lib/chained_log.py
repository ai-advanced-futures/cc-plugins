"""An append-only JSONL file with a sha256 chain.

Each line is one JSON object whose `prev` is the sha256 hex of every byte before that line
(line 1: the sha256 of no bytes). A reader refuses the file when a `prev` does not match, so a
change to any line that has a later line is caught. A change to the last line, or a cut of whole
trailing lines, leaves a valid chain and is not caught here (ADR-007).
"""
from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl  # POSIX only
except ImportError:  # Windows: append without the lock
    fcntl = None


class LogRefused(ValueError):
    """The file breaks the chain or the line rules, or a record cannot be appended."""


class _RepeatedKey(Exception):
    pass


def _no_repeated_keys(pairs: list) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise _RepeatedKey(key)
        out[key] = value
    return out


def _load(path: Path, upto: int | None = None) -> tuple[list, bytes]:
    """(records, the file's bytes), the file cut at `upto` bytes (None: the whole file). A missing
    file is ([], b"")."""
    name = path.name
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return [], b""
    except OSError as exc:
        raise LogRefused(f"{name}: cannot read the file: {exc}") from exc
    if upto is not None:
        data = data[:upto]
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LogRefused(f"{name}: the file is not UTF-8: {exc}") from exc
    if not data:
        return [], data
    if not data.endswith(b"\n"):
        raise LogRefused(f"{name}: the last line has no newline; cut the file back to its last full line")
    chain = hashlib.sha256()
    records = []
    for n, raw in enumerate(data[:-1].split(b"\n"), 1):
        try:
            obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_repeated_keys)
        except _RepeatedKey as exc:
            raise LogRefused(f"{name}: line {n} repeats the key {exc.args[0]!r}") from exc
        except ValueError:
            obj = None
        if not isinstance(obj, dict):
            raise LogRefused(f"{name}: line {n} is not a JSON object")
        if obj.get("prev") != chain.hexdigest():
            if n == 1:
                raise LogRefused(f"{name}: line 1's prev does not match: line 1 was changed, "
                                 "a line before it was removed, or the lines were reordered")
            raise LogRefused(f"{name}: line {n}'s prev does not match: "
                             f"line {n - 1} or an earlier line was changed")
        chain.update(raw + b"\n")
        records.append(obj)
    return records, data


def read(path, upto: int | None = None) -> list:
    """Every record in file order, the file cut at `upto` bytes (None: the whole file); [] when the
    file does not exist. Refuses a broken file, and a cut that ends inside a line."""
    return _load(Path(path), upto)[0]


def _encode(path: Path, record, prev: str) -> tuple:
    """(stored record, its line) for a record that follows bytes whose sha256 hex is prev."""
    if not isinstance(record, dict):
        raise LogRefused(f"{path.name}: a record must be a JSON object")
    if "prev" in record:
        raise LogRefused(f"{path.name}: a new record must not carry prev; the log adds it")
    stored = dict(record, prev=prev)
    try:
        line = (json.dumps(stored, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:  # not JSON-able, NaN or Infinity, or a lone surrogate
        raise LogRefused(f"{path.name}: the record cannot be written as one UTF-8 JSON line: {exc}") from exc
    # The line must read back, through read's own parse, as exactly the record returned. This refuses
    # non-string keys (which json.dumps renames, and which can then collide) and tuples (read as lists).
    try:
        back = json.loads(line.decode("utf-8"), object_pairs_hook=_no_repeated_keys)
    except _RepeatedKey as exc:
        raise LogRefused(f"{path.name}: the record would be written with the key {exc.args[0]!r} twice") from exc
    if back != stored:
        raise LogRefused(f"{path.name}: the record would not read back as written; "
                         "use string keys and JSON types only")
    return stored, line


@contextmanager
def locked_append(path, refusal=LogRefused):
    """Open path to append (created when absent) and yield the descriptor under an exclusive lock.

    The lock is held until the block ends, so a read of the file inside the block and the write
    that follows it are one step for every caller that takes this lock. On Windows `fcntl` does
    not exist and the block runs without the lock. Every open or lock error is raised as
    `refusal`, the calling module's refusal type."""
    path = Path(path)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(str(path), flags, 0o644)
    except OSError as exc:
        raise refusal(f"{path.name}: cannot append: {exc}") from exc
    try:
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX)
        except OSError as exc:
            raise refusal(f"{path.name}: cannot lock the file: {exc}") from exc
        yield fd
    finally:
        os.close(fd)  # closing the file releases the lock


def append(path, record) -> dict:
    """Check the whole file, add `prev` to the record, write it as one line, return what was stored.

    On macOS and Linux the read, the chain check and the write happen under an exclusive lock on
    the file, so two appends at once never share a prev. On Windows the appends are not locked:
    `fcntl` does not exist there, and two appends at once can share a prev.
    `record` is the record, or a callable that builds it from the file. A callable is called once
    before the file is opened, so a refused record leaves the file untouched (or absent), and again
    under the lock, so a record numbered from the file's lines is numbered from the lines it
    follows. When the second call refuses and this call created the file, the file stays, empty.
    An empty file reads as no lines."""
    path = Path(path)
    build = record if callable(record) else (lambda: record)
    _encode(path, build(), hashlib.sha256(b"").hexdigest())
    with locked_append(path) as fd:
        _, data = _load(path)
        stored, line = _encode(path, build(), hashlib.sha256(data).hexdigest())
        try:
            written = os.write(fd, line)  # one write of one line
        except OSError as exc:
            raise LogRefused(f"{path.name}: cannot append: {exc}") from exc
    if written != len(line):
        raise LogRefused(f"{path.name}: only {written} of {len(line)} bytes were written; "
                         "cut the file back to its last full line")
    return stored
