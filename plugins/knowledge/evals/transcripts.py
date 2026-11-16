"""Keep complete per-run session records as data beside native eval reports.

Only the temporary config tree of the named native eval run is searched.
These files can contain local paths. They belong in ignored result folders.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil

SESSION_ID = re.compile(r"[a-f0-9-]{36}\Z")


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def preserve(report_path: Path) -> dict:
    """Copy traces and their own main/child logs; keep the native report unchanged."""
    report = json.loads(report_path.read_text())
    output = report_path.parent
    mapping = {}
    for case in report.get("cases", []):
        for runs in case["arms"].values():
            for run in runs:
                path = run.get("tracePath")
                if not path or path in mapping or not Path(path).is_file():
                    continue
                source = Path(path)
                folder = output / f"attempt-{len(mapping) + 1:04d}"
                folder.mkdir(exist_ok=True)
                shutil.copyfile(source, folder / "trace.jsonl")
                events = read_events(source)
                session_ids = {e.get("session_id") for e in events if e.get("type") == "result"}
                entry = {"trace": str((folder / "trace.jsonl").relative_to(output)), "sessions": {}}
                if len(session_ids) == 1:
                    session_id = next(iter(session_ids))
                    if isinstance(session_id, str) and SESSION_ID.fullmatch(session_id):
                        # Native eval keeps out/trace.jsonl beside config/projects/.
                        projects = source.parent.parent / "config/projects"
                        parents = list(projects.glob(f"*/{session_id}.jsonl"))
                        if len(parents) == 1:
                            parent = parents[0]
                            files = [("main", parent)] + [
                                (p.stem.removeprefix("agent-"), p)
                                for p in sorted(parent.with_suffix("").glob("subagents/agent-*.jsonl"))
                            ]
                            for index, (key, file) in enumerate(files):
                                saved = folder / f"session-{index:04d}.jsonl"
                                shutil.copyfile(file, saved)
                                entry["sessions"][key] = str(saved.relative_to(output))
                mapping[path] = entry
    (output / "transcripts.json").write_text(json.dumps(mapping, indent=2) + "\n")
    return mapping


def agent_task_ids(events: list[dict]) -> set[str]:
    """Shell task starts are not agent starts; older traces omit task_type."""
    return {event["task_id"] for event in events
            if event.get("subtype") == "task_started" and event.get("task_id")
            and event.get("task_type") != "local_bash"}


def sandbox_blocked(events: list[dict]) -> bool:
    """Treat observed sandbox errors as environment failures, not wrong answers."""
    for event in events:
        if event.get("type") != "user":
            continue
        for block in event.get("message", {}).get("content", []):
            if not isinstance(block, dict) or block.get("type") != "tool_result" or not block.get("is_error"):
                continue
            content = block.get("content", "")
            text = content if isinstance(content, str) else json.dumps(content)
            if "<sandbox_violations>" in text or "errno=Operation not permitted" in text:
                return True
    return False


def terminal_refusal(events: list[dict], key: str, row: dict, tools: dict) -> bool:
    """Require the child identity and its terminal failed-task proof, not text."""
    task = [event for event in events if event.get("task_id") == key
            and event.get("subtype") in ("task_started", "task_notification")]
    if len(task) != 2:
        return False
    start, notification = task
    if (start.get("type") != "system" or start.get("subtype") != "task_started"
            or start.get("task_type") != "local_agent"
            or notification.get("type") != "system" or notification.get("subtype") != "task_notification"
            or notification.get("status") != "failed" or row.get("agentId") != key):
        return False
    for field in ("run_id", "tool_use_id", "session_id"):
        value = start.get(field)
        if not isinstance(value, str) or not value or notification.get(field) != value:
            return False
    if row.get("sessionId") != start["session_id"]:
        return False
    return sum(tool_id == start["tool_use_id"] and name in ("Agent", "Task")
               for (_, tool_id), name in tools.items()) == 1


def complete_counts(events: list[dict], sessions: dict[str, list[dict]]) -> dict | None:
    """Count unique model messages and tool calls only when child logs are complete."""
    if "main" not in sessions:
        return None
    started = agent_task_ids(events)
    if not started <= set(sessions):
        return None
    message_ids, tools, refusals = set(), {}, {}
    for key, rows in sessions.items():
        last_row = None
        for row in rows:
            message = row.get("message", {})
            if row.get("type") != "assistant" or message.get("model") in (None, "<synthetic>"):
                continue
            if not message.get("id"):
                return None
            if key != "main":
                if key in refusals and message.get("stop_reason") != "refusal":
                    return None
                if message.get("stop_reason") == "refusal":
                    if any(isinstance(block, dict) and block.get("type") == "tool_use"
                           for block in message.get("content", [])):
                        return None
                    refusals.setdefault(key, []).append(row)
            message_ids.add((key, message["id"]))
            last_row = row
            for block in message.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    if not block.get("id"):
                        return None
                    tools[(key, block["id"])] = block.get("name")
        # A real terminal refusal has no text; require its failed-task proof below.
        # Other children still need their final text, not only a tool call.
        if key != "main":
            if last_row is None:
                return None
            if key not in refusals and not any(
                b.get("type") == "text" for b in last_row["message"].get("content", []) if isinstance(b, dict)
            ):
                return None
    child_count = len(sessions) - 1
    dispatches = sum(name in ("Agent", "Task") for name in tools.values())
    if dispatches > child_count or not message_ids:
        return None
    if any(not terminal_refusal(events, key, row, tools)
           for key, refusal_rows in refusals.items() for row in refusal_rows):
        return None
    counts = {"model_turns": len(message_ids), "tool_calls": len(tools), "subagent_starts": child_count}
    if refusals:
        counts["child_refusals"] = len(refusals)
    return counts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    print(f"Saved records for {len(preserve(args.report))} attempt(s).")
