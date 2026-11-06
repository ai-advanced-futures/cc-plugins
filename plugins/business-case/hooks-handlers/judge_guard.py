#!/usr/bin/env python3
"""business-case judge guard (ADR-006). One handler, three hook entries in hooks/hooks.json:
  pre-write     PreToolUse   Write|Edit|MultiEdit|NotebookEdit   no file tool writes a case folder; the judge writes only its reply
  pre-dispatch  PreToolUse   Agent|Task                           the judge's prompt is a brief, exactly
  post-write    PostToolUse  Write                                receipt of a completed judge Write
It runs under whatever python3 Claude Code finds, which may be macOS's 3.9: this file and
every lib module it imports keep to 3.9 syntax."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MODES = ("pre-write", "pre-dispatch", "post-write")
# A literal copy of judge_receipt.GUARDED_TOOLS + DISPATCH_TOOLS: when lib cannot be imported the
# handler still has to know which calls it guards. A test pins the copy equal to the library's sets.
FAIL_CLOSED_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit", "Agent", "Task")
_TOOL_NAME = re.compile(r'"tool_name"\s*:\s*"([^"\\]*)"')


def _allow(reason: str) -> str:
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "allow",
                                              "permissionDecisionReason": reason}})


def _guarded_call(raw: str) -> bool:
    """True when a failed PreToolUse must refuse: the call's tool is one this guard covers. When the
    tool name cannot be read at all, any mention of a judge or of business-cases, in any letter case, counts."""
    try:
        tool = json.loads(raw).get("tool_name")
    except Exception:
        match = _TOOL_NAME.search(raw)
        tool = match.group(1) if match else None
    if isinstance(tool, str):
        return tool in FAIL_CLOSED_TOOLS
    return "judge" in raw.casefold() or "business-cases" in raw.casefold()


def main(argv: list) -> int:
    raw = sys.stdin.read()
    mode = argv[1] if len(argv) > 1 else ""
    try:
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}")
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from lib import judge_receipt  # inside the try: an import error fails closed
        hook_input = json.loads(raw)
        if mode == "post-write":
            judge_receipt.record_write(hook_input)
            return 0
        if mode == "pre-write":
            decision = judge_receipt.decide_write(hook_input)
        else:
            decision = judge_receipt.decide_dispatch(hook_input)
        if decision.verdict not in ("allow", "deny", "pass"):
            raise ValueError(f"unknown verdict {decision.verdict!r}")
    except Exception as exc:
        # PreToolUse fails closed on any call of a tool this guard covers, a judge path or not.
        # PostToolUse never blocks: a missing receipt already makes save-report refuse the reply.
        if mode != "post-write" and _guarded_call(raw):
            print(f"business-case judge guard refused (failed closed): {exc}", file=sys.stderr)
            return 2
        return 0
    if decision.verdict == "deny":
        print(decision.reason, file=sys.stderr)
        return 2
    if decision.verdict == "allow":
        print(_allow(decision.reason))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
