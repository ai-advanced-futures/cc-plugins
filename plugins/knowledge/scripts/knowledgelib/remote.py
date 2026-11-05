"""The cache of remote graphs: a shallow clone of the default branch (standard section 5)."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from knowledgelib import DataError, UsageError, registry

REFRESH_SECONDS = 900
STAMP = "knowledge-fetched"


def cache_root() -> Path:
    if os.environ.get("KNOWLEDGE_CACHE_DIR"):
        return Path(os.environ["KNOWLEDGE_CACHE_DIR"])
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "claude-knowledge"


def clone_url(repo: str) -> str:
    if repo.startswith(("file://", "https://", "http://", "ssh://", "git@", "/")):
        return repo
    return f"https://{repo.rstrip('/')}.git"


def slug(repo: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", repo.strip("/")).strip("_")


def cache_dir(repo: str) -> Path:
    return cache_root() / slug(repo)


def git(*args, cwd=None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise DataError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def age(clone: Path) -> float:
    stamp = clone / ".git" / STAMP
    return time.time() - stamp.stat().st_mtime if stamp.is_file() else float("inf")


def ensure_cache(repo: str, refresh: bool = False) -> Path:
    clone = cache_dir(repo)
    if not (clone / ".git").is_dir():
        clone.parent.mkdir(parents=True, exist_ok=True)
        if clone.exists():
            shutil.rmtree(clone)
        git("clone", "--depth", "1", "--quiet", clone_url(repo), str(clone))
    elif refresh or age(clone) > REFRESH_SECONDS:
        git("fetch", "--depth", "1", "--quiet", "origin", "HEAD", cwd=clone)
        git("reset", "--hard", "--quiet", "FETCH_HEAD", cwd=clone)
    else:
        return clone
    (clone / ".git" / STAMP).write_text(str(int(time.time())), encoding="utf-8")
    return clone


def cmd_fetch(args) -> int:
    graph = registry.require(registry.read(args.root), args.graph)
    if not graph.remote:
        raise UsageError(f"{args.graph} is a local graph")
    print(ensure_cache(graph.repo, refresh=args.refresh) / graph.path)
    return 0


def register(sub) -> None:
    parser = sub.add_parser("fetch", help="clone or update the cache of a remote graph")
    parser.add_argument("graph")
    parser.add_argument("--refresh", action="store_true", help="fetch even when the cache is new")
    parser.set_defaults(run=cmd_fetch)
