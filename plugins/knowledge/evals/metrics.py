"""Read native evaluation results without treating missing data as zero.

This module starts no model. Pass an explicit expected model ID for a benchmark.
The native case cost includes grading. The trace's result cost covers the answer.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path

from transcripts import agent_task_ids, sandbox_blocked

TOKEN_FIELDS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")


def number(value):
    """Keep finite non-negative measurements; reject booleans and missing fields."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return value
    return None


def quality(run, expected_graders):
    """Return separate scores only when each expected grader has a Boolean result."""
    names = [g["name"] for g in expected_graders]
    actual = run.get("graders", [])
    scores = {g["name"]: g.get("passed") for g in actual}
    if len(scores) != len(actual) or set(names) != set(scores) or not all(type(v) is bool for v in scores.values()):
        return None
    kinds = {g["name"]: g.get("type") for g in expected_graders}
    for grader in actual:
        if kinds[grader["name"]] == "llm":
            votes = grader.get("judgeVotes")
            if not isinstance(votes, list) or len(votes) != 3 or not all(type(v) is bool for v in votes):
                return None
            if grader["passed"] != (sum(votes) >= 2):
                return None
    facts = [v for k, v in scores.items() if k.startswith("fact-")]
    context = [v for k, v in scores.items() if k.startswith("context-")]
    if "accuracy" not in scores or not facts or not context:
        return None
    return {"accuracy": int(scores["accuracy"]), "fact_retrieval": sum(facts) / len(facts),
            "context_retrieval": sum(context) / len(context)}


USAGE_TOTAL_FIELDS = (*TOKEN_FIELDS, "costUSD", "thinkingTokens", "webSearchRequests",
                      "cacheCreationEphemeral5mInputTokens", "cacheCreationEphemeral1hInputTokens")
SESSION_TIME_VERSIONS = ("2.1.323", "2.1.325")
# Allow up to two seconds for startup and final record writes, not for model work.
SESSION_TIME_TOLERANCE_MS = 2000


def costs_equal(left, right):
    return (number(left) is not None and number(right) is not None
            and math.isclose(left, right, rel_tol=0, abs_tol=1e-6))


def model_totals(usage):
    """Keep only measured cumulative fields, not model limits or price metadata."""
    if not isinstance(usage, dict) or not usage:
        return None
    totals = {}
    for model, row in usage.items():
        if not isinstance(row, dict) or not all(key in row for key in (*TOKEN_FIELDS, "costUSD")):
            return None
        values = {key: number(row[key]) for key in USAGE_TOTAL_FIELDS if key in row}
        if any(value is None for value in values.values()):
            return None
        totals[model] = values
    return totals


def final_result(results, events):
    """Accept one result or a complete chain of automatic task follow-up results."""
    if not results or any(event.get("type") == "conversation_reset" for event in events):
        return {}
    if len(results) == 1:
        return results[0]
    session = results[0].get("session_id")
    if not isinstance(session, str) or not session:
        return {}
    previous, previous_cost = {}, 0
    for index, result in enumerate(results):
        origin = result.get("origin")
        if (result.get("session_id") != session
                or type(result.get("result_index")) is not int or result["result_index"] != index
                or result.get("subtype") != "success" or result.get("is_error") is not False
                or result.get("terminal_reason") != "completed"
                or (index and (not isinstance(origin, dict)
                               or origin.get("kind") != "task-notification"
                               or origin.get("producer") != "session-task"))):
            return {}
        current = model_totals(result.get("modelUsage"))
        cost = number(result.get("total_cost_usd"))
        if (current is None or cost is None or cost < previous_cost
                or not previous.keys() <= current.keys()
                or not costs_equal(sum(row["costUSD"] for row in current.values()), cost)):
            return {}
        for model, fields in previous.items():
            if any(key not in current[model] or current[model][key] < value for key, value in fields.items()):
                return {}
        previous, previous_cost = current, cost
    return results[-1]


def timestamp_ms(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return number(parsed.timestamp() * 1000) if parsed.tzinfo is not None else None
    except (AttributeError, ValueError, OverflowError, OSError):
        return None


def answer_time(results, result, events, cli_version, main_rows, costs_valid):
    """Read elapsed session time, including waits, without adding turn durations.

    The final cost-state is an internal CLI record, not a stable public interface.
    Accept its schema only for verified CLI versions and after checks against
    the result totals and main-log timestamps. A bad present state has no fallback.
    Without a state, only a single result can use the public duration_ms field.
    """
    if not result or not costs_valid:
        return None, None
    states = [row for row in (main_rows or []) if row.get("type") == "cost-state"]
    if not states:
        duration = number(result.get("duration_ms")) if len(results) == 1 else None
        return (duration, "cli_single_result_duration") if duration else (None, None)
    if (cli_version not in SESSION_TIME_VERSIONS or main_rows[-1].get("type") != "cost-state"
            or any(event.get("type") == "system" and event.get("subtype") == "init"
                   and event.get("claude_code_version") != cli_version for event in events)):
        return None, None
    state = states[-1]
    session = result.get("session_id")
    if (not isinstance(session, str) or not session or state.get("sessionId") != session
            or any(row.get("sessionId", session) != session for row in main_rows)
            or state.get("hasUnknownModelCost") is True
            or not costs_equal(state.get("totalCostUSD"), result.get("total_cost_usd"))):
        return None, None
    totals = model_totals(result.get("modelUsage"))
    if totals is None or model_totals(state.get("modelUsage")) != totals:
        return None, None
    if not costs_equal(sum(row["costUSD"] for row in totals.values()), state.get("totalCostUSD")):
        return None, None
    start, duration = number(state.get("startTime")), number(state.get("totalDuration"))
    timestamps = [timestamp_ms(row["timestamp"]) for row in main_rows if "timestamp" in row]
    if (start is None or not duration or len(timestamps) < 2
            or any(value is None for value in timestamps) or min(timestamps) == max(timestamps)):
        return None, None
    if (abs(min(timestamps) - start) > SESSION_TIME_TOLERANCE_MS
            or abs(max(timestamps) - (start + duration)) > SESSION_TIME_TOLERANCE_MS):
        return None, None
    return duration, f"cli_session_cost_state_{cli_version}"


def summarize_run(run, expected_graders, events, expected_models, full_counts=None, blocked=False,
                  *, cli_version=None, main_rows=None):
    """Extract one attempt and mark its limits, including incomplete fork traces."""
    issues = []
    if run.get("error"):
        issues.append("run_error")
    if run.get("aborted"):
        issues.append("run_aborted")
    if run.get("skippedPaidGraders"):
        issues.append("grading_incomplete")
    results = [e for e in events if e.get("type") == "result" and not e.get("parent_tool_use_id")]
    result = final_result(results, events)
    if not result:
        issues.append("missing_or_ambiguous_result")
    answer_error = any(row.get("is_error") or str(row.get("subtype", "")).startswith("error_")
                       or row.get("terminal_reason") not in (None, "completed") for row in results)
    if answer_error:
        issues.append("answer_error")
    usage = result.get("modelUsage", {})
    if not isinstance(usage, dict) or any(not isinstance(row, dict) for row in usage.values()):
        usage = {}
    models = sorted(usage)
    if not models:
        issues.append("missing_model_usage")
    if not expected_models:
        issues.append("expected_models_not_set")
    elif not set(models) <= set(expected_models):
        issues.append("served_model_mismatch")

    tool_ids = set()
    agent_ids = agent_task_ids(events)
    message_ids = set()
    blocked = blocked or sandbox_blocked(events)
    if blocked:
        issues.append("sandbox_blocked")
    for event in events:
        message = event.get("message", {})
        if event.get("type") != "assistant" or message.get("model") in (None, "<synthetic>"):
            continue
        if message.get("id"):
            message_ids.add(message["id"])
        for block in message.get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id"):
                tool_ids.add(block["id"])

    # A fork's final answer can be a synthetic message with no child turn count.
    # Keep observed counts as lower bounds rather than calling them totals.
    has_fork = bool(agent_ids) or any(e.get("parent_tool_use_id") for e in events)
    model_turns = (full_counts["model_turns"] if full_counts else number(result.get("num_turns"))
                   if not has_fork and len(results) == 1 else None)
    if model_turns is None or model_turns == 0:
        model_turns = None
        issues.append("model_turn_total_unavailable")

    tokens = {}
    for key in TOKEN_FIELDS:
        values = [number(row.get(key)) for row in usage.values()]
        tokens[key] = sum(values) if values and all(v is not None for v in values) else None
    if any(v is None for v in tokens.values()):
        issues.append("token_total_unavailable")
    answer_cost = number(result.get("total_cost_usd"))
    grading_cost = number(run.get("judgeCostUsd"))
    attempt_cost = number(run.get("costUsd"))
    costs_valid = (answer_cost is not None and grading_cost is not None and attempt_cost is not None)
    if not costs_valid:
        issues.append("cost_unavailable")
    elif not costs_equal(answer_cost + grading_cost, attempt_cost):
        costs_valid = False
        issues.append("cost_totals_disagree")
    duration_ms, time_basis = answer_time(results, result, events, cli_version, main_rows, costs_valid)
    if duration_ms is None:
        issues.append("answer_duration_unavailable")
    denials_complete = bool(results) and all(isinstance(row.get("permission_denials"), list) for row in results)
    denials = [denial for row in results if isinstance(row.get("permission_denials"), list)
               for denial in row["permission_denials"]]
    if not denials_complete:
        issues.append("permission_denial_count_unavailable")
    if denials:
        issues.append("permission_denied")
    grades = quality(run, expected_graders)
    if grades is None:
        issues.append("grading_incomplete")
    if run.get("error") or run.get("aborted") or answer_error or run.get("skippedPaidGraders") or blocked or denials:
        grades = None
    return {
        "benchmark_eligible": not issues,
        "issues": sorted(set(issues)),
        "quality": grades,
        "expected_models": sorted(expected_models),
        "served_models": models,
        "tokens": tokens,
        "answer_seconds": duration_ms / 1000 if duration_ms is not None else None,
        "answer_time_basis": time_basis,
        "attempt_seconds_including_setup_and_grading": number(run.get("durationSeconds")),
        "answer_cost_usd": answer_cost,
        "grading_cost_usd": grading_cost,
        "grading_source": "native",
        "attempt_cost_usd": attempt_cost,
        "cost_basis_by_model": {m: row.get("costBasis", "unknown") for m, row in usage.items()},
        "model_turns": model_turns,
        "tool_calls": (full_counts["tool_calls"] if full_counts else len(tool_ids)
                       if events and not has_fork and len(results) == 1 else None),
        "subagent_starts": (full_counts["subagent_starts"] if full_counts else 0
                            if events and not has_fork and len(results) == 1 else None),
        "child_refusals": full_counts.get("child_refusals", 0) if full_counts else None,
        "observed_model_messages": len(message_ids) if events else None,
        "observed_tool_calls": len(tool_ids) if events else None,
        "observed_subagent_starts": len(agent_ids) if events else None,
        "counts_are_lower_bounds": (has_fork or len(results) > 1) and full_counts is None,
        "permission_denials": len(denials) if denials_complete else None,
    }


def summarize(report, traces, expected_models, full_counts=None, sandbox_failures=None, main_records=None):
    if report.get("schemaVersion") != 1:
        raise ValueError("Unsupported native evaluation schema")
    rows = []
    for case in report["cases"]:
        for arm, runs in case["arms"].items():
            for index, run in enumerate(runs):
                path = run.get("tracePath")
                row = summarize_run(run, case["graders"], traces.get(path, []), expected_models,
                                    (full_counts or {}).get(path), path in (sandbox_failures or set()),
                                    cli_version=report.get("claudeVersion"), main_rows=(main_records or {}).get(path))
                if report.get("partial"):
                    row["issues"].append("partial_suite")
                    row["benchmark_eligible"] = False
                rows.append({"case": case["name"], "arm": arm, "run": index + 1, **row})
    if not rows:
        raise ValueError("The report contains no attempts")
    return {"schema_version": 1, "claude_version": report.get("claudeVersion"), "attempts": rows}


def checked_failure(row, issue):
    """Keep answer measurements, but do not call missing checked grades a zero."""
    return {**row, "benchmark_eligible": False, "quality": None,
            "issues": sorted(set(row["issues"]) | {issue}),
            "grading_source": "checked_claude_3", "grading_served_models": None,
            "grading_cost_basis_by_model": {}, "grading_cost_usd": None,
            "attempt_cost_usd": None, "attempt_seconds_including_setup_and_grading": None}


def checked_summary(row, case, native, events, directory, expected_models, full_counts, blocked,
                    cli_version, main_rows):
    """Bind three checked votes to this native answer; never start a model here."""
    if number(native.get("judgeCostUsd")) != 0:
        return checked_failure(row, "checked_grading_native_judge_cost")
    if set(row["issues"]) - {"grading_incomplete"}:
        return checked_failure(row, "checked_grading_answer_invalid")
    try:
        request = json.loads((directory / "grading-request.json").read_text())
    except (OSError, ValueError):
        return checked_failure(row, "checked_grading_request_invalid")
    if not isinstance(request, dict):
        return checked_failure(row, "checked_grading_request_invalid")
    question, answer, graders = (request.get(key) for key in ("question", "answer", "graders"))
    if (not isinstance(question, str) or not question.strip()
            or not isinstance(answer, str) or not answer.strip()
            or not isinstance(graders, list) or not graders
            or any(not isinstance(grader, dict) or grader.get("type") != "llm"
                   or not isinstance(grader.get("name"), str) or not grader["name"] for grader in graders)
            or len({grader["name"] for grader in graders}) != len(graders)):
        return checked_failure(row, "checked_grading_request_invalid")
    prompt = case.get("promptMarkdown")
    if not isinstance(prompt, str) or not prompt.startswith("/") or prompt.partition(" ")[2] != question:
        return checked_failure(row, "checked_grading_binding_mismatch")
    results = [event for event in events if event.get("type") == "result" and not event.get("parent_tool_use_id")]
    result = final_result(results, events)
    answers = [result["result"]] if isinstance(result.get("result"), str) else []
    answers.extend(grader["evidence"] for grader in native.get("graders", [])
                   if isinstance(grader.get("evidence"), str))
    if not answers or any(observed != answer for observed in answers):
        return checked_failure(row, "checked_grading_binding_mismatch")
    try:
        from checked_grading import load
        checked = load(directory / "checked-grading", request)
    except (ImportError, OSError, ValueError):
        return checked_failure(row, "checked_grading_unavailable")
    if not isinstance(checked, dict) or checked.get("status") != "ok":
        return checked_failure(row, "checked_grading_invalid")
    judge_cost, judge_duration = number(checked.get("judge_cost_usd")), number(checked.get("duration_seconds"))
    native_cost, native_duration = number(native.get("costUsd")), number(native.get("durationSeconds"))
    models, basis = checked.get("served_models"), checked.get("cost_basis_by_model")
    votes = checked.get("graders")
    if (judge_cost is None or judge_duration is None or native_cost is None or native_duration is None
            or not isinstance(models, list) or not models
            or any(not isinstance(model, str) or not model for model in models)
            or len(set(models)) != len(models) or not isinstance(basis, dict) or set(basis) != set(models)
            or any(not isinstance(value, str) or not value for value in basis.values())
            or not isinstance(votes, list)
            or any(not isinstance(vote, dict) or not isinstance(vote.get("name"), str) for vote in votes)):
        return checked_failure(row, "checked_grading_invalid")
    virtual = {**native, "graders": votes, "judgeCostUsd": judge_cost,
               "costUsd": native_cost + judge_cost, "durationSeconds": native_duration + judge_duration}
    if quality(virtual, graders) is None:
        return checked_failure(row, "checked_grading_invalid")
    measured = summarize_run(virtual, graders, events, expected_models, full_counts, blocked,
                             cli_version=cli_version, main_rows=main_rows)
    return {**row, **measured, "grading_source": "checked_claude_3",
            "grading_served_models": sorted(models), "grading_cost_basis_by_model": basis}


def read_report(report_path, expected_models, *, include_answer=False):
    from transcripts import complete_counts, read_events

    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    map_path = report_path.parent / "trace-map.json"
    saved = json.loads(map_path.read_text()) if map_path.is_file() else {}
    full_path = report_path.parent / "transcripts.json"
    full = json.loads(full_path.read_text()) if full_path.is_file() else {}
    traces, counts, blocked, main_records = {}, {}, set(), {}
    for case in report.get("cases", []):
        for runs in case["arms"].values():
            for run in runs:
                path = run.get("tracePath")
                if path in full:
                    source = report_path.parent / full[path]["trace"]
                elif path in saved:
                    source = report_path.parent / saved[path]
                else:
                    source = Path(path) if path else None
                if source and source.is_file():
                    traces[path] = read_events(source)
                    if path in full:
                        sessions = {key: read_events(report_path.parent / file)
                                    for key, file in full[path]["sessions"].items()
                                    if (report_path.parent / file).is_file()}
                        counts[path] = complete_counts(traces[path], sessions)
                        main_records[path] = sessions.get("main", [])
                        # A fork's tool errors can be absent from the streamed trace.
                        if any(sandbox_blocked(rows) for rows in sessions.values()):
                            blocked.add(path)
    output = summarize(report, traces, expected_models, counts, blocked, main_records)
    if include_answer and len(output["attempts"]) == 1:
        native = next(run for case in report["cases"] for runs in case["arms"].values() for run in runs)
        events = traces.get(native.get("tracePath"), [])
        results = [event for event in events if event.get("type") == "result" and not event.get("parent_tool_use_id")]
        output["answer"] = final_result(results, events).get("result")
    directory = report_path.parent
    if (directory / "grading-request.json").exists() or (directory / "checked-grading").exists():
        if len(output["attempts"]) != 1:
            output["attempts"] = [checked_failure(row, "checked_grading_ambiguous_attempt")
                                  for row in output["attempts"]]
        else:
            case, native = next((case, run) for case in report["cases"]
                                for runs in case["arms"].values() for run in runs)
            path = native.get("tracePath")
            output["attempts"][0] = checked_summary(
                output["attempts"][0], case, native, traces.get(path, []), directory, expected_models,
                counts.get(path), path in blocked, report.get("claudeVersion"), main_records.get(path))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--expected-model", action="append", required=True,
                        help="An allowed served model ID; repeat for subagent models.")
    args = parser.parse_args()
    output = read_report(args.report, args.expected_model)
    print(json.dumps(output, indent=2))
    return 0 if all(row["benchmark_eligible"] for row in output["attempts"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
