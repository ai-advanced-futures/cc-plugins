# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=1.3.0"]
# ///
"""
Report Exporter - Structured CSV Output for JTBD Analysis

Generates named CSV files from JTBD phase outputs. These are the
"math contract" artifacts — plain text, git-diffable, and ingestible by
any tool (pandas, R, Google Sheets, BI tools) without binary dependencies.

What was multi-sheet XLSX becomes multiple named CSV files per phase:
  Phase 6 → opportunity-scores.csv + opportunity-category-summary.csv
  Phase 8 → segmentation-profiles.csv + segmentation-respondents.csv
  Phase 9 → wtp-summary.csv + wtp-layers.csv + wtp-warnings.csv

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT

Usage (CLI):
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/report_exporter.py opportunity --input .jtbd-market-discovery/session/p6.json --output-dir reports/
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/report_exporter.py segmentation --input .jtbd-market-discovery/session/p8.json --output-dir reports/
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/report_exporter.py wtp --input .jtbd-market-discovery/session/p9.json --output-dir reports/

Usage (library):
    from scripts.report_exporter import export_opportunity_report, export_wtp_report
    paths = export_opportunity_report(scored_df, output_dir="reports/", session_id="s001")
    # Returns: {"scores": "/abs/path/scores.csv", "category_summary": "/abs/path/summary.csv"}
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


def _prefix_stamp(session_id: str) -> tuple[str, str]:
    """Return (file prefix, date stamp) for consistent naming."""
    prefix = f"{session_id}-" if session_id else ""
    stamp = datetime.now().strftime("%Y%m%d")
    return prefix, stamp


def _write(df: pd.DataFrame, path: Path) -> str:
    """Write DataFrame to CSV and return absolute path string."""
    df.to_csv(path, index=False)
    return str(path.resolve())


def _prepare_output_dir(output_dir: str, session_id: str) -> tuple[Path, str, str]:
    """Create output directory and return (path, prefix, datestamp)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    prefix, stamp = _prefix_stamp(session_id)
    return out, prefix, stamp


# ---------------------------------------------------------------------------
# Phase 6 — Opportunity scoring
# ---------------------------------------------------------------------------

def export_opportunity_report(
    scored_df: pd.DataFrame,
    output_dir: str,
    session_id: str = "",
    metadata: Optional[dict] = None,
) -> dict[str, str]:
    """
    Export opportunity scoring results to CSV files.

    Writes:
      - <prefix>opportunity-scores-<date>.csv     — all needs, ranked
      - <prefix>opportunity-category-summary-<date>.csv  — per-category aggregation
      - <prefix>opportunity-metadata-<date>.csv   — job/session metadata (if provided)

    Args:
        scored_df: DataFrame with at minimum an 'opportunity_score' column.
                   Ideally also has: need_id, need/need_statement, job_step,
                   importance, satisfaction, gap, category.
        output_dir: Directory to write output files (created if absent)
        session_id: Optional session prefix for file naming
        metadata: Optional dict written as a two-column (Field, Value) CSV

    Returns:
        Dict mapping logical name → absolute CSV path.
        Keys always present: "scores"
        Keys conditionally present: "category_summary", "metadata"

    Raises:
        ValueError: If opportunity_score column is missing
    """
    if "opportunity_score" not in scored_df.columns:
        raise ValueError(
            "scored_df must contain 'opportunity_score'. "
            "Run score_needs_dataframe() from opportunity_scorer.py first."
        )

    out, prefix, stamp = _prepare_output_dir(output_dir, session_id)

    # Canonical column order
    priority_cols = [
        "rank", "need_id", "need", "need_statement", "job_step",
        "importance", "satisfaction", "gap", "opportunity_score", "category",
    ]
    ordered = [c for c in priority_cols if c in scored_df.columns]
    ordered += [c for c in scored_df.columns if c not in ordered]
    export_df = scored_df[ordered].copy()

    if "rank" not in export_df.columns:
        export_df.insert(0, "rank", range(1, len(export_df) + 1))

    result: dict[str, str] = {}

    # scores CSV (always)
    result["scores"] = _write(
        export_df, out / f"{prefix}opportunity-scores-{stamp}.csv"
    )

    # category summary CSV (when category column present)
    if "category" in export_df.columns:
        summary = (
            export_df.groupby("category", observed=True)
            .agg(
                count=("opportunity_score", "count"),
                avg_score=("opportunity_score", "mean"),
                max_score=("opportunity_score", "max"),
                min_score=("opportunity_score", "min"),
            )
            .reset_index()
            .sort_values("avg_score", ascending=False)
            .round(2)
        )
        result["category_summary"] = _write(
            summary, out / f"{prefix}opportunity-category-summary-{stamp}.csv"
        )

    # metadata CSV (when provided)
    if metadata:
        meta_df = pd.DataFrame(
            [{"field": k, "value": str(v)} for k, v in metadata.items()]
        )
        result["metadata"] = _write(
            meta_df, out / f"{prefix}opportunity-metadata-{stamp}.csv"
        )

    return result


# ---------------------------------------------------------------------------
# Phase 8 — Segmentation
# ---------------------------------------------------------------------------

def export_segmentation_report(
    profiles: list[dict],
    segmented_df: Optional[pd.DataFrame] = None,
    output_dir: str = ".",
    session_id: str = "",
) -> dict[str, str]:
    """
    Export segmentation results to CSV files.

    Writes:
      - <prefix>segmentation-profiles-<date>.csv    — one row per segment
      - <prefix>segmentation-respondents-<date>.csv — respondent-level data (if provided)

    Args:
        profiles: List of segment profile dicts from
                  SegmentationEngine.generate_segment_profiles()
        segmented_df: Optional respondent-level DataFrame with 'segment' column
        output_dir: Directory to write output files
        session_id: Optional session prefix for file naming

    Returns:
        Dict mapping logical name → absolute CSV path.
        Keys always present: "profiles"
        Keys conditionally present: "respondents"

    Raises:
        ValueError: If profiles list is empty
    """
    if not profiles:
        raise ValueError(
            "profiles list is empty. "
            "Run SegmentationEngine.generate_segment_profiles() first."
        )

    out, prefix, stamp = _prepare_output_dir(output_dir, session_id)

    profiles_df = pd.DataFrame([
        {
            "segment_id": p["segment_id"],
            "size": p["size"],
            "percentage_pct": round(p["percentage"] * 100, 1),
            "avg_importance": round(p["avg_importance"], 2),
            "avg_satisfaction": round(p["avg_satisfaction"], 2),
            "gap": round(p["gap"], 2),
            "characteristics": p["characteristics"],
            "top_needs": ", ".join(p.get("top_needs", [])[:5]),
        }
        for p in profiles
    ])

    result: dict[str, str] = {}

    result["profiles"] = _write(
        profiles_df, out / f"{prefix}segmentation-profiles-{stamp}.csv"
    )

    if segmented_df is not None and not segmented_df.empty:
        result["respondents"] = _write(
            segmented_df, out / f"{prefix}segmentation-respondents-{stamp}.csv"
        )

    return result


# ---------------------------------------------------------------------------
# Phase 9 — WTP validation
# ---------------------------------------------------------------------------

def export_wtp_report(
    validation_report: dict,
    output_dir: str = ".",
    session_id: str = "",
) -> dict[str, str]:
    """
    Export WTP validation results to CSV files.

    Writes:
      - <prefix>wtp-summary-<date>.csv   — one-row summary with validated price range
      - <prefix>wtp-layers-<date>.csv    — one row per validation layer
      - <prefix>wtp-warnings-<date>.csv  — warnings list (only if warnings present)

    Args:
        validation_report: Output from WTPValidator.validate_all_layers()
        output_dir: Directory to write output files
        session_id: Optional session prefix for file naming

    Returns:
        Dict mapping logical name → absolute CSV path.
        Keys always present: "summary", "layers"
        Keys conditionally present: "warnings"

    Raises:
        ValueError: If required keys are missing from validation_report
    """
    required = {"overall_passed", "layers", "validated_wtp_range", "median_wtp", "evc"}
    missing = required - set(validation_report.keys())
    if missing:
        raise ValueError(
            f"validation_report is missing required keys: {missing}. "
            "Run WTPValidator.validate_all_layers() first."
        )

    out, prefix, stamp = _prepare_output_dir(output_dir, session_id)

    wtp_min, wtp_max = validation_report["validated_wtp_range"]

    summary_df = pd.DataFrame([{
        "overall_passed": validation_report["overall_passed"],
        "median_wtp": round(validation_report["median_wtp"], 2),
        "evc": round(validation_report["evc"], 2),
        "validated_wtp_min": round(wtp_min, 2),
        "validated_wtp_max": round(wtp_max, 2),
        "confidence": validation_report["confidence"],
        "sample_size": validation_report.get("sample_size", ""),
        "recommendation": validation_report.get("recommendation", ""),
    }])

    layer_rows = []
    for layer_name, layer_data in validation_report.get("layers", {}).items():
        row: dict = {"layer": layer_name, "passed": layer_data.get("passed", "")}
        for k, v in layer_data.items():
            if k == "passed" or not isinstance(v, (int, float, str, bool)):
                continue
            row[k] = round(v, 4) if isinstance(v, float) else v
        layer_rows.append(row)
    layers_df = pd.DataFrame(layer_rows)

    result: dict[str, str] = {}

    result["summary"] = _write(summary_df, out / f"{prefix}wtp-summary-{stamp}.csv")
    result["layers"] = _write(layers_df, out / f"{prefix}wtp-layers-{stamp}.csv")

    warnings = validation_report.get("warnings", [])
    if warnings:
        warnings_df = pd.DataFrame([{"warning": w} for w in warnings])
        result["warnings"] = _write(
            warnings_df, out / f"{prefix}wtp-warnings-{stamp}.csv"
        )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_json(path: str) -> dict:  # pragma: no cover
    return json.loads(Path(path).read_text())


def _cmd_opportunity(args: argparse.Namespace) -> None:  # pragma: no cover
    data = _load_json(args.input)
    top_opps = data.get("top_opportunities", [])
    if not top_opps:
        print("ERROR: 'top_opportunities' key not found in input JSON", file=sys.stderr)
        raise SystemExit(1)

    df = pd.DataFrame(top_opps)
    if "odi_score" in df.columns and "opportunity_score" not in df.columns:
        df = df.rename(columns={"odi_score": "opportunity_score"})

    metadata = {k: v for k, v in data.items() if k != "top_opportunities"}
    paths = export_opportunity_report(df, args.output_dir, args.session_id, metadata)
    print(json.dumps({"status": "OK", **paths}, indent=2))


def _cmd_segmentation(args: argparse.Namespace) -> None:  # pragma: no cover
    data = _load_json(args.input)
    profiles = data.get("segments", data.get("profiles", []))
    if not profiles:
        print("ERROR: 'segments' or 'profiles' key not found in input JSON", file=sys.stderr)
        raise SystemExit(1)

    paths = export_segmentation_report(
        profiles, output_dir=args.output_dir, session_id=args.session_id
    )
    print(json.dumps({"status": "OK", **paths}, indent=2))


def _cmd_wtp(args: argparse.Namespace) -> None:  # pragma: no cover
    report = _load_json(args.input)
    paths = export_wtp_report(report, output_dir=args.output_dir, session_id=args.session_id)
    print(json.dumps({"status": "OK", **paths}, indent=2))


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="JTBD Report Exporter — write named CSV artifacts from phase outputs"
    )
    parser.add_argument("--output-dir", default="reports/", help="Output directory")
    parser.add_argument("--session-id", default="", help="Session ID prefix for filenames")

    subparsers = parser.add_subparsers(dest="command", required=True)
    for cmd, func, help_text in [
        ("opportunity", _cmd_opportunity, "Export Phase 6 opportunity scores"),
        ("segmentation", _cmd_segmentation, "Export Phase 8 segmentation profiles"),
        ("wtp", _cmd_wtp, "Export Phase 9 WTP validation"),
    ]:
        sp = subparsers.add_parser(cmd, help=help_text)
        sp.add_argument("--input", required=True, help="Phase output JSON path")
        sp.set_defaults(func=func)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
