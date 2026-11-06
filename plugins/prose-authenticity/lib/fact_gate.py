#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Parse grounded-synthesis coverage output into the missing-fact list the
loop controller consumes (ADR-002). The orchestrator never parses coverage
JSON itself — it runs this CLI and forwards --missing to loop_controller.

Contract (verified against the grounded-synthesis agent docs): the coverage
file is {session_dir}/source-{i}-coverage.json with a top-level `verdicts`
array of {fact_id, verdict, rationale} per coverage-checker.md. The
output_dir_override we dispatch with receives ONLY gap-report.md +
handoff.json (orchestrator doc, ADR-006), so resolve_coverage_path() walks
handoff.json's outputs.session_dir to find the real coverage file. Fixture
copied verbatim; tests/unit/test_fact_gate.py is the cross-plugin
doc-contract test."""
import json
from pathlib import Path


class GroundedSynthesisFailed(Exception):
    """handoff.json has status "failed": the fact check did not run."""


def resolve_coverage_path(facts_dir, source_index=0):
    """facts_dir is the output_dir_override handed to grounded-synthesis; it
    contains handoff.json, NOT the coverage files. Resolve the real coverage
    path deterministically via outputs.session_dir."""
    handoff = Path(facts_dir) / "handoff.json"
    if not handoff.exists():
        raise FileNotFoundError(f"no handoff.json in {facts_dir} — grounded-synthesis dispatch failed?")
    data = json.loads(handoff.read_text())
    if data.get("status") == "failed":
        raise GroundedSynthesisFailed(
            f"grounded-synthesis failed: {data.get('failure_reason', 'no reason given')}")
    session_dir = (data.get("outputs") or {}).get("session_dir")
    if not session_dir:
        raise ValueError(f"{handoff}: no outputs.session_dir — cannot locate coverage files")
    return Path(session_dir) / f"source-{source_index}-coverage.json"


def _verdicts(coverage_path):
    data = json.loads(Path(coverage_path).read_text())
    verdicts = data.get("verdicts") if isinstance(data, dict) else None
    if not isinstance(verdicts, list):
        # Shape drift must fail LOUDLY — silently returning [] would read as
        # "all facts present" and defeat the guard.
        raise ValueError(f"unrecognized coverage shape in {coverage_path}")
    return verdicts


def missing_facts(coverage_path):
    return [v for v in _verdicts(coverage_path) if v.get("verdict") == "MISSING"]


def missing_fact_ids(coverage_path):
    return [str(v.get("fact_id", f"fact-{i}"))
            for i, v in enumerate(missing_facts(coverage_path))]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Coverage -> missing-fact list")
    ap.add_argument("target", help="Path to source-N-coverage.json, or (with "
                                   "--from-handoff) the facts dir holding handoff.json")
    ap.add_argument("--from-handoff", action="store_true",
                    help="treat target as the output_dir_override dir; resolve "
                         "the coverage path via handoff.json outputs.session_dir")
    ap.add_argument("--source-index", type=int, default=0)
    ap.add_argument("--ids-only", action="store_true")
    args = ap.parse_args()
    try:
        cov = (resolve_coverage_path(args.target, args.source_index)
               if args.from_handoff else args.target)
    except GroundedSynthesisFailed as exc:
        raise SystemExit(str(exc))
    if args.ids_only:
        print(",".join(missing_fact_ids(cov)))
    else:
        print(json.dumps(missing_facts(cov), indent=2))
