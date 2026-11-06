#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Make and delete the temp folders of architecture-assess runs.

A run keeps its files in `.architect-tmp/<id>/` in the current folder.
  new                      make a folder with an ID of 8 hex characters, print its path
  clean --older-than <min> delete each folder that is older than <min> minutes
  remove <id>              delete one folder

The script deletes only folders that are direct children of `.architect-tmp/`.
On a bad value (an ID that is not 8 hex characters, or that is not a direct child of `.architect-tmp/`) it prints 1 line on standard error and exits 1.
On an unknown command or a missing argument, argparse prints its usage and exits 2.
"""
from __future__ import annotations

import argparse
import re
import secrets
import shutil
import sys
import time
from pathlib import Path

TMP_NAME = ".architect-tmp"
ID_PATTERN = re.compile(r"^[0-9a-f]{8}$")


class SessionError(Exception):
    pass


def tmp_root(base: Path) -> Path:
    return base / TMP_NAME


def new(base: Path) -> Path:
    root = tmp_root(base)
    root.mkdir(exist_ok=True)
    for _ in range(10):
        folder = root / secrets.token_hex(4)
        try:
            folder.mkdir()
        except FileExistsError:
            continue
        return folder
    raise SessionError("cannot make a free folder name")


def check_child(base: Path, session_id: str) -> Path:
    """Return the folder for session_id, or raise when it is not a direct child of .architect-tmp/."""
    if not ID_PATTERN.match(session_id):
        raise SessionError(f"not a session ID of 8 hex characters: {session_id}")
    root = tmp_root(base).resolve()
    folder = (root / session_id).resolve()
    if folder.parent != root:
        raise SessionError(f"not a direct child of {TMP_NAME}/: {session_id}")
    return folder


def remove(base: Path, session_id: str) -> bool:
    folder = check_child(base, session_id)
    if folder.is_symlink() or not folder.is_dir():
        return False
    shutil.rmtree(folder)
    return True


def clean(base: Path, older_than_minutes: float) -> list[str]:
    root = tmp_root(base)
    if not root.is_dir():
        return []
    limit = time.time() - older_than_minutes * 60
    removed = []
    for folder in sorted(root.iterdir()):
        if not ID_PATTERN.match(folder.name) or folder.is_symlink() or not folder.is_dir():
            continue
        if folder.stat().st_mtime < limit:
            shutil.rmtree(folder)
            removed.append(folder.name)
    return removed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("new", help="make a temp folder and print its path")
    clean_parser = sub.add_parser("clean", help="delete old temp folders")
    clean_parser.add_argument("--older-than", type=float, required=True, metavar="MINUTES")
    remove_parser = sub.add_parser("remove", help="delete one temp folder")
    remove_parser.add_argument("id")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    base = Path.cwd()
    try:
        if args.command == "new":
            print(new(base).relative_to(base))
        elif args.command == "clean":
            for name in clean(base, args.older_than):
                print(f"removed {TMP_NAME}/{name}")
        else:
            if remove(base, args.id):
                print(f"removed {TMP_NAME}/{args.id}")
    except SessionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
