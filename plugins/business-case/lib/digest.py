"""Content digests of the files the judge reads, and the check that a report is still current."""
from __future__ import annotations

import hashlib
from pathlib import Path

from lib import paths


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> dict:
    """{"sha256": hex, "bytes": int} of a file's bytes."""
    return _digest_of(Path(path).read_bytes())


def _read_inputs(case_dir: Path) -> dict:
    """POSIX relative path -> bytes, for every existing file the judge reads, sorted by path.
    Each file is read once."""
    found = {}
    for pattern in paths.JUDGE_INPUT_GLOBS:
        for p in case_dir.glob(pattern):
            if paths.stat_is_file(p):
                found[p.relative_to(case_dir).as_posix()] = p.read_bytes()
    return {rel: found[rel] for rel in sorted(found)}


def _digest_of(data: bytes) -> dict:
    return {"sha256": sha256_hex(data), "bytes": len(data)}


def _is_digest(old) -> bool:
    return (isinstance(old, dict) and isinstance(old.get("sha256"), str)
            and isinstance(old.get("bytes"), int) and not isinstance(old.get("bytes"), bool))


def build_manifest(case_dir: Path) -> dict:
    """POSIX relative path -> digest, for every existing file the judge reads, sorted by path."""
    return {rel: _digest_of(data) for rel, data in _read_inputs(Path(case_dir)).items()}


def is_current(manifest: dict, case_dir: Path) -> tuple:
    """(True, []) when every digest in the manifest still matches. Otherwise (False, paths) with
    the changed, added and removed paths. An append-only file matches while the bytes the manifest
    recorded are still its start. A manifest or entry with the wrong shape matches nothing."""
    now = _read_inputs(Path(case_dir))
    manifest = manifest if isinstance(manifest, dict) else {}
    stale = []
    for rel, old in manifest.items():
        if not _is_digest(old) or rel not in now:
            stale.append(rel)
        elif rel in paths.APPEND_ONLY:
            head = now[rel][: old["bytes"]]
            if len(head) != old["bytes"] or sha256_hex(head) != old["sha256"]:
                stale.append(rel)
        elif _digest_of(now[rel]) != old:
            stale.append(rel)
    stale.extend(rel for rel in now if rel not in manifest)
    stale = sorted(stale)
    return (not stale, stale)
