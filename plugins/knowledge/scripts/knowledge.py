#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""knowledge.py: the cross-graph code of the knowledge plugin.

The registry, link resolution, the remote cache, navigation, the walk state of
an ask run, the general check, the forget plan, and remote writes. Each module
of knowledgelib adds its commands through a register(sub) function.

Exit 0 on success, 1 on a graph data error, a failed check, or a file that cannot be read or written after
5 tries (okf.short_lock), 2 on wrong input.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml  # noqa: F401
except ImportError:
    print("ERROR: the pyyaml package is missing. Run the script with uv run, "
          "or install pyyaml and jsonschema.", file=sys.stderr)
    sys.exit(2)

from knowledgelib import DataError, FileError, UsageError  # noqa: E402
from knowledgelib import (forget, general_check, links, navigate, registry, remote,  # noqa: E402
                          remote_write, rootpath, walk)

REGISTERS = [registry.register, remote.register, links.register, navigate.register, walk.register,
             general_check.register, forget.register, remote_write.register]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knowledge.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=str(Path.cwd()), help="the project root")
    sub = parser.add_subparsers(dest="command", required=True)
    for register in REGISTERS:
        register(sub)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.root = rootpath.resolve(args.root)
    try:
        return args.run(args)
    except UsageError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except (DataError, FileError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
