#!/usr/bin/env python3
"""Write one marked router block into the repository's CLAUDE.md.

The block sits between `<!-- <plugin>:router start -->` and
`<!-- <plugin>:router end -->`. The script replaces the block when both markers
exist, appends it when neither exists, and creates CLAUDE.md when the file is
absent. Text outside the markers is never changed. A second run with the same
body changes no bytes.

`--keep-if-contains TEXT` keeps a block that an earlier version wrote without
markers: when the file holds TEXT and no markers for this plugin, the script
changes nothing and says so.

The body comes from stdin. Exit 0 on success. Exit 2 when the input is wrong:
a half marker pair, a duplicate pair, an empty body, a body that holds a marker,
or a repo root that is not a directory. The script then writes nothing.

Usage:
    claude_md_router.py --plugin adr --repo-root "$(git rev-parse --show-toplevel)" <<'EOF'
    ## ADRs
    ...
    EOF

This same file ships in four plugins: architecture, wiki, code-review, and product. Change all
four copies together.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MARKER = re.compile(r"<!-- [a-z0-9-]+:router (start|end) -->")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def fail(message: str) -> int:
    print(f"claude_md_router: {message}", file=sys.stderr)
    return 2


def render(plugin: str, body: str) -> str:
    return (f"<!-- {plugin}:router start -->\n"
            f"{body.strip()}\n"
            f"<!-- {plugin}:router end -->\n")


def read_text(path: Path) -> str:
    """Read the file as it is on disk, line endings included, or "" when absent."""
    if not path.exists():
        return ""
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path: Path, text: str) -> None:
    """Write the text as it is, with no line-ending translation."""
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def merge(text: str, plugin: str, block: str) -> str:
    """Return the new file text, or raise ValueError on a broken marker pair.

    The block uses LF line endings. In a file that uses CRLF, the block gets
    CRLF too, so the lines outside the markers keep their line endings."""
    start = f"<!-- {plugin}:router start -->"
    end = f"<!-- {plugin}:router end -->"
    eol = "\r\n" if "\r\n" in text else "\n"
    block = block.replace("\n", eol)
    starts = text.count(start)
    ends = text.count(end)
    if starts == 0 and ends == 0:
        if not text:
            return block
        if not text.endswith("\n"):
            text += eol
        return text + eol + block
    if starts != 1 or ends != 1:
        raise ValueError(
            f"CLAUDE.md holds {starts} start marker(s) and {ends} end marker(s) "
            f"for {plugin}; expected one of each")
    first = text.index(start)
    last = text.index(end)
    if last < first:
        raise ValueError(f"the end marker for {plugin} comes before the start marker")
    tail = text[last + len(end):]
    for line_end in ("\r\n", "\n"):
        if tail.startswith(line_end):
            tail = tail[len(line_end):]
            break
    return text[:first] + block + tail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--plugin", required=True, help="the plugin name used in the markers")
    parser.add_argument("--repo-root", required=True, help="the repository root")
    parser.add_argument("--file", default="CLAUDE.md",
                        help="the file to write, relative to the repo root (default: CLAUDE.md)")
    parser.add_argument("--keep-if-contains", metavar="TEXT", default=None,
                        help="when the file holds no markers for this plugin but holds TEXT "
                             "(a block from an earlier version), change nothing")
    args = parser.parse_args(argv)

    if not SLUG.match(args.plugin):
        return fail(f"--plugin must be a plain slug, got {args.plugin!r}")
    root = Path(args.repo_root)
    if not root.is_dir():
        return fail(f"--repo-root is not a directory: {root}")
    body = sys.stdin.read()
    if not body.strip():
        return fail("the body on stdin is empty")
    if MARKER.search(body):
        return fail("the body must not hold a router marker")

    path = root / args.file
    before = read_text(path)
    legacy = args.keep_if_contains
    if (legacy and legacy in before
            and f"<!-- {args.plugin}:router start -->" not in before
            and f"<!-- {args.plugin}:router end -->" not in before):
        print(f"CLAUDE.md router: unchanged {path} (a block from an earlier setup is present)")
        return 0
    try:
        after = merge(before, args.plugin, render(args.plugin, body))
    except ValueError as error:
        return fail(str(error))
    if after == before:
        print(f"CLAUDE.md router: unchanged {path}")
        return 0
    write_text(path, after)
    print(f"CLAUDE.md router: written {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
