"""Summarize a complete experiment without starting models or changing README."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean

from metrics import TOKEN_FIELDS

QUALITY = ("accuracy", "fact_retrieval", "context_retrieval")
PERFORMANCE = ("answer_seconds", "tool_calls", "model_turns", "subagent_starts",
               "answer_cost_usd", "grading_cost_usd")
TOKENS = TOKEN_FIELDS


def summarize(config, rows):
    expected = {(r["variant"], r["case"], r["repetition"]) for r in config["schedule"]}
    keys = [(r["variant"], r["case"], r["repetition"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate attempts; a repeated run must not replace an earlier result")
    if set(keys) != expected:
        raise ValueError(f"Incomplete experiment: {len(keys)} attempts, {len(expected)} required")
    if any(not r["measurement"].get("benchmark_eligible") for r in rows):
        raise ValueError("Invalid measurements are present; a benchmark table cannot be produced")
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["variant"]].append(row)
    variants = {}
    for name, group in sorted(grouped.items()):
        measurements = [r["measurement"] for r in group]
        try:
            quality = {key: mean(r["quality"][key] for r in measurements) for key in QUALITY}
            performance = {key: mean(r[key] for r in measurements) for key in PERFORMANCE}
            tokens = {key: mean(r["tokens"][key] for r in measurements) for key in TOKENS}
        except (KeyError, TypeError) as error:
            raise ValueError(f"A required measurement is missing in {name}") from error
        models = sorted({model for r in measurements for model in r["served_models"]})
        variants[name] = {"attempts": len(group), "questions": len({r["case"] for r in group}),
                          "served_models": models, "quality": quality, "performance": performance,
                          "tokens": tokens, "pre_model_searches": mean(r["pre_model_searches"] for r in group),
                          "child_refusals": sum(r.get("child_refusals", 0) for r in measurements),
                          "answer_time_basis": sorted({r.get("answer_time_basis", "unavailable") for r in measurements}),
                          "grading_sources": sorted({r.get("grading_source", "native") for r in measurements}),
                          "grading_served_models": sorted({model for r in measurements
                                                           for model in r.get("grading_served_models", [])}),
                          "cost_basis": sorted({basis for r in measurements
                                                for basis in r["cost_basis_by_model"].values()})}
    return {"schema_version": 1, "dataset": config["dataset"], "dataset_hash": config["dataset_hash"],
            "runtime_hash": config["runtime_hash"], "runs_per_question": config["runs_per_question"],
            "answer_model_requested": config["answer_model"], "judge_model_requested": config["judge_model"],
            "variants": variants}


def readme_table(summary):
    historical = "search-then-walk-3" not in summary["variants"]
    ponder = "page-by-page-1" if historical else "search-then-walk-3"
    names = {"search-then-walk-2": "ask",
             ponder: "ponder (historical page-by-page-1)" if historical else "ponder"}
    if summary["dataset"] != "benchmark-1" or not set(names) <= set(summary["variants"]):
        raise ValueError("The README needs a full benchmark-1 run of ask and ponder")
    lines = ["| Command | Mean seconds | Accuracy | Facts | Context | Tool calls | Model turns | Agents | Tokens | Cost |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, label in names.items():
        row = summary["variants"][name]
        if row["questions"] != 60 or row["attempts"] != 180:
            raise ValueError("The README needs 60 questions and 3 runs per question for each command")
        if row.get("grading_sources") != ["checked_claude_3"] or not row.get("grading_served_models"):
            raise ValueError("The README needs checked grading with recorded judge models")
        if not row.get("answer_time_basis") or "unavailable" in row["answer_time_basis"]:
            raise ValueError("The README needs a recorded answer timing source")
        q, p, t = row["quality"], row["performance"], row["tokens"]
        lines.append(f"| `{label}` | {p['answer_seconds']:.2f} | {q['accuracy']:.1%} | "
                     f"{q['fact_retrieval']:.1%} | {q['context_retrieval']:.1%} | {p['tool_calls']:.1f} | "
                     f"{p['model_turns']:.1f} | {p['subagent_starts']:.1f} | {sum(t.values()):,.0f} | "
                     f"${p['answer_cost_usd']:.4f} |")
    lines += ["", "Each value is a mean over 60 questions, with 3 fresh sessions per question.",
              "Facts and context are the shares of the expected facts returned. Accuracy requires",
              "all required facts and no conflicting answer. Tool calls exclude the scripted search",
              "before the model starts. Model turns include subagents. Tokens include cache reads and writes.",
              "Cost is the CLI estimate for the answer, excluding grading. These are synthetic-data results."]
    if historical:
        lines += ["", "The historical ponder row measures page-by-page-1, not the search-then-walk-3 reader."]
    for name, label in names.items():
        row = summary["variants"][name]
        lines.append(f"Served models for `{label}`: {', '.join(row['served_models'])}.")
        lines.append(f"Answer timing source for `{label}`: {', '.join(row['answer_time_basis'])}.")
        lines.append(f"Checked judge models for `{label}`: {', '.join(row['grading_served_models'])}.")
        if row.get("child_refusals", 0):
            lines.append(f"Recorded child refusals for `{label}`: {row['child_refusals']}; their model responses remain in the counts.")
        lines.append(f"Mean grading cost for `{label}`: ${row['performance']['grading_cost_usd']:.4f}.")
        lines.append(f"Cost basis for `{label}`: {', '.join(row['cost_basis'])}.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", type=Path)
    parser.add_argument("--readme-table", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads((args.experiment / "experiment.json").read_text())
        rows = [json.loads(line) for line in (args.experiment / "attempts.jsonl").read_text().splitlines()]
        summary = summarize(config, rows)
        print(readme_table(summary) if args.readme_table else json.dumps(summary, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
