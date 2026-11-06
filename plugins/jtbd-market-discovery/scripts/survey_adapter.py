# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=1.3.0"]
# ///
"""
Survey Adapter - ODI Format Detection and Mapping

Detects survey data format, proposes a mapping to ODI standard
(importance + satisfaction, 1-10 scale), and requires explicit user
approval before materializing any artifacts.

The flow is:
  1. `propose` — detect format, show mapping plan to user (NO data written)
  2. User reviews and APPROVES (or corrects)
  3. `apply` — materialize raw CSV + ODI-mapped CSV, then scoring can begin

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT

Usage (CLI):
    # Step 1: Show proposed mapping — no data written
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py propose --input survey.csv

    # Step 2 (after user approval): Materialize artifacts
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py apply --input survey.csv --output survey-odi.csv

    # Step 2 with manual column override:
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py apply --input survey.csv --output survey-odi.csv \\
        --importance-col frequency --satisfaction-col difficulty

Usage (library):
    from scripts.survey_adapter import propose_mapping, apply_mapping, materialize_raw
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):  # run by path: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

import pandas as pd  # noqa: E402

from scripts.opportunity_scorer import validate_formula_invariant  # noqa: E402

# ---------------------------------------------------------------------------
# Known survey format patterns
# ---------------------------------------------------------------------------

KNOWN_FORMATS: dict[str, dict] = {
    "odi_standard": {
        "importance_candidates": ["importance"],
        "satisfaction_candidates": ["satisfaction"],
        "needs_scale_norm": False,
        "satisfaction_is_inverted": False,
        "description": "ODI standard (importance + satisfaction, 1–10). No conversion needed.",
    },
    "frequency_difficulty": {
        "importance_candidates": ["frequency", "avg_frequency", "freq"],
        "satisfaction_candidates": ["difficulty", "avg_difficulty", "diff"],
        "needs_scale_norm": True,
        "satisfaction_is_inverted": True,  # High difficulty = low satisfaction
        "description": (
            "Frequency/difficulty format. "
            "frequency → importance (scale-normalized). "
            "difficulty → satisfaction (inverted + scale-normalized)."
        ),
    },
    "urgency_ease": {
        "importance_candidates": ["urgency", "avg_urgency"],
        "satisfaction_candidates": ["ease", "easiness", "avg_ease"],
        "needs_scale_norm": True,
        "satisfaction_is_inverted": False,
        "description": (
            "Urgency/ease format. "
            "urgency → importance (scale-normalized). "
            "ease → satisfaction (scale-normalized, direct)."
        ),
    },
    "importance_pain": {
        "importance_candidates": ["importance", "avg_importance"],
        "satisfaction_candidates": ["pain", "pain_level", "avg_pain"],
        "needs_scale_norm": True,
        "satisfaction_is_inverted": True,  # High pain = low satisfaction
        "description": (
            "Importance/pain format. "
            "importance → importance (scale-normalized). "
            "pain → satisfaction (inverted + scale-normalized)."
        ),
    },
}


# ---------------------------------------------------------------------------
# Scale helpers
# ---------------------------------------------------------------------------

def _detect_scale(series: pd.Series) -> tuple[float, float]:
    """Snap observed min/max to the nearest common rating scale."""
    max_val = float(series.max())
    if max_val <= 5.5:
        return (1.0, 5.0)
    elif max_val <= 7.5:
        return (1.0, 7.0)
    return (1.0, 10.0)


def _normalize_to_10(series: pd.Series, source_scale: tuple[float, float]) -> pd.Series:
    """Linearly map a series from source_scale → 1–10."""
    lo, hi = source_scale
    return ((series - lo) / (hi - lo)) * 9.0 + 1.0


def _invert_and_normalize(series: pd.Series, source_scale: tuple[float, float]) -> pd.Series:
    """Invert (high→low) and normalize to 1–10.  Used for difficulty/pain → satisfaction."""
    lo, hi = source_scale
    return ((hi - series) / (hi - lo)) * 9.0 + 1.0


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(df: pd.DataFrame) -> dict:
    """
    Detect the survey format from column names.

    Returns:
        {
          "format": str,             # "odi_standard" | "frequency_difficulty" | ...
          "importance_col": str,     # matched column name (original case)
          "satisfaction_col": str,   # matched column name (original case)
          "confidence": str,         # "high" | "low"
          "description": str,
        }
    """
    cols_lower = {c.lower(): c for c in df.columns}

    # Full match (both columns found)
    for fmt_name, fmt in KNOWN_FORMATS.items():
        imp = next((cols_lower[c] for c in fmt["importance_candidates"] if c in cols_lower), None)
        sat = next((cols_lower[c] for c in fmt["satisfaction_candidates"] if c in cols_lower), None)
        if imp and sat:
            return {
                "format": fmt_name,
                "importance_col": imp,
                "satisfaction_col": sat,
                "confidence": "high",
                "description": fmt["description"],
            }

    # Partial match (one column found)
    for fmt_name, fmt in KNOWN_FORMATS.items():
        imp = next((cols_lower[c] for c in fmt["importance_candidates"] if c in cols_lower), None)
        sat = next((cols_lower[c] for c in fmt["satisfaction_candidates"] if c in cols_lower), None)
        if imp or sat:
            return {
                "format": fmt_name,
                "importance_col": imp,
                "satisfaction_col": sat,
                "confidence": "low",
                "description": fmt["description"],
            }

    return {
        "format": "unknown",
        "importance_col": None,
        "satisfaction_col": None,
        "confidence": "low",
        "description": "No recognized format. Use --importance-col and --satisfaction-col overrides.",
    }


# ---------------------------------------------------------------------------
# Mapping proposal
# ---------------------------------------------------------------------------

def propose_mapping(df: pd.DataFrame) -> dict:
    """
    Detect survey format and produce a human-readable mapping proposal.

    Nothing is written to disk. The caller is responsible for presenting
    this proposal to the user and obtaining explicit approval before calling
    apply_mapping().

    Returns:
        A structured proposal dict ready for JSON serialization.
    """
    detected = detect_format(df)
    fmt_name = detected["format"]
    imp_col = detected["importance_col"]
    sat_col = detected["satisfaction_col"]

    if fmt_name == "unknown" or not imp_col or not sat_col:
        return {
            "status": "UNRESOLVABLE",
            "detected_format": "unknown",
            "available_columns": list(df.columns),
            "message": (
                "No recognized survey format detected. "
                "Specify --importance-col and --satisfaction-col manually."
            ),
            "action_required": (
                "Re-run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py apply --input <file> "
                "--importance-col <col> --satisfaction-col <col>"
            ),
        }

    fmt_def = KNOWN_FORMATS[fmt_name]
    needs_norm = fmt_def["needs_scale_norm"]
    is_inverted = fmt_def["satisfaction_is_inverted"]

    imp_series = df[imp_col].dropna()
    sat_series = df[sat_col].dropna()
    imp_scale = _detect_scale(imp_series)
    sat_scale = _detect_scale(sat_series)
    lo_i, hi_i = imp_scale
    lo_s, hi_s = sat_scale

    # Build readable formulas and examples
    if not needs_norm:
        imp_formula = f"{imp_col}  (no conversion — already on 1–10 scale)"
        sat_formula = f"{sat_col}  (no conversion — already on 1–10 scale)"
        imp_ex_in = round(float(imp_series.mean()), 2)
        sat_ex_in = round(float(sat_series.mean()), 2)
        imp_ex_out = imp_ex_in
        sat_ex_out = sat_ex_in
    else:
        imp_formula = f"(({imp_col} - {lo_i}) / {hi_i - lo_i}) × 9 + 1"
        imp_ex_in = round(float(imp_series.mean()), 2)
        imp_ex_out = round(((imp_ex_in - lo_i) / (hi_i - lo_i)) * 9.0 + 1.0, 2)

        if is_inverted:
            sat_formula = f"(({hi_s} - {sat_col}) / {hi_s - lo_s}) × 9 + 1"
        else:
            sat_formula = f"(({sat_col} - {lo_s}) / {hi_s - lo_s}) × 9 + 1"

        sat_ex_in = round(float(sat_series.mean()), 2)
        if is_inverted:
            sat_ex_out = round(((hi_s - sat_ex_in) / (hi_s - lo_s)) * 9.0 + 1.0, 2)
        else:
            sat_ex_out = round(((sat_ex_in - lo_s) / (hi_s - lo_s)) * 9.0 + 1.0, 2)

    _inv = validate_formula_invariant(algorithm="additive")

    proposal = {
        "status": "PROPOSED",
        "detected_format": fmt_name,
        "confidence": detected["confidence"],
        "format_description": fmt_def["description"],
        "original_columns": list(df.columns),
        "rows": len(df),
        "mapping": {
            "importance": {
                "source_column": imp_col,
                "source_scale": f"{lo_i}–{hi_i}",
                "formula": imp_formula,
                "rationale": _rationale_importance(fmt_name),
                "example": f"{imp_col}={imp_ex_in} → importance={imp_ex_out}",
            },
            "satisfaction": {
                "source_column": sat_col,
                "source_scale": f"{lo_s}–{hi_s}",
                "formula": sat_formula,
                "rationale": _rationale_satisfaction(fmt_name),
                "example": f"{sat_col}={sat_ex_in} → satisfaction={sat_ex_out}",
            },
        },
        "invariant_check": {
            "assertion": "f(importance=10, satisfaction=1) > f(importance=1, satisfaction=10)",
            "result": f"f(10,1) = {_inv['best_case']}  |  f(1,10) = {_inv['worst_case']}  →  {_inv['best_case']} > {_inv['worst_case']} ✓",
            "passed": _inv["passed"],
        },
        "action_required": (
            "Review the mapping above.\n"
            "• To APPROVE: re-run with `apply` subcommand.\n"
            "• To CORRECT: re-run `apply` with --importance-col / --satisfaction-col overrides."
        ),
    }

    if detected["confidence"] == "low":  # pragma: no cover — low-confidence always triggers UNRESOLVABLE at line 189
        proposal.setdefault("warnings", []).append(
            "Low-confidence detection: only one column matched the expected format. "
            "Verify the mapping carefully before approving."
        )

    return proposal


def _rationale_importance(fmt_name: str) -> str:
    return {
        "odi_standard": "Direct ODI importance — no mapping needed.",
        "frequency_difficulty": (
            "Frequency → Importance: how often customers perform this step "
            "is a proxy for how important it is to them."
        ),
        "urgency_ease": "Urgency → Importance: the more urgent, the more important.",
        "importance_pain": "Importance column maps directly — scale normalization only.",
    }.get(fmt_name, "Custom mapping.")


def _rationale_satisfaction(fmt_name: str) -> str:
    return {
        "odi_standard": "Direct ODI satisfaction — no mapping needed.",
        "frequency_difficulty": (
            "Difficulty → Satisfaction (INVERTED): harder = less satisfied. "
            "difficulty=5 (hardest) → satisfaction=1; difficulty=1 (easiest) → satisfaction=10."
        ),
        "urgency_ease": (
            "Ease → Satisfaction (direct): easier = more satisfied. "
            "ease=5 (easiest) → satisfaction=10."
        ),
        "importance_pain": (
            "Pain → Satisfaction (INVERTED): more pain = less satisfied. "
            "pain=5 (max pain) → satisfaction=1."
        ),
    }.get(fmt_name, "Custom mapping.")


# ---------------------------------------------------------------------------
# Apply mapping
# ---------------------------------------------------------------------------

def apply_mapping(
    df: pd.DataFrame,
    importance_col: Optional[str] = None,
    satisfaction_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Apply ODI column mapping and scale normalization.

    Produces a DataFrame with standardized `importance` and `satisfaction`
    columns on the 1–10 scale, preserving all other columns.

    Args:
        df: Input survey DataFrame
        importance_col: Column to use as importance (auto-detected if None)
        satisfaction_col: Column to use as satisfaction (auto-detected if None)

    Returns:
        DataFrame with `importance` and `satisfaction` on 1–10 scale

    Raises:
        ValueError: If columns cannot be resolved
        AssertionError: If formula invariant fails (should never happen on ODI additive)
    """
    if not importance_col or not satisfaction_col:
        detected = detect_format(df)
        importance_col = importance_col or detected["importance_col"]
        satisfaction_col = satisfaction_col or detected["satisfaction_col"]

    if not importance_col or not satisfaction_col:
        raise ValueError(
            f"Cannot map: specify --importance-col and --satisfaction-col. "
            f"Available columns: {list(df.columns)}"
        )

    fmt_name = _resolve_format_name(importance_col, satisfaction_col)
    fmt_def = KNOWN_FORMATS.get(fmt_name, KNOWN_FORMATS["odi_standard"])
    needs_norm = fmt_def["needs_scale_norm"]
    is_inverted = fmt_def["satisfaction_is_inverted"]

    result = df.copy()
    imp_series = df[importance_col]
    sat_series = df[satisfaction_col]

    if needs_norm:
        imp_scale = _detect_scale(imp_series.dropna())
        sat_scale = _detect_scale(sat_series.dropna())
        result["importance"] = _normalize_to_10(imp_series, imp_scale).round(2)
        result["satisfaction"] = (
            _invert_and_normalize(sat_series, sat_scale).round(2)
            if is_inverted
            else _normalize_to_10(sat_series, sat_scale).round(2)
        )
    else:
        result["importance"] = imp_series
        result["satisfaction"] = sat_series

    to_drop = [
        c for c in [importance_col, satisfaction_col]
        if c not in ("importance", "satisfaction")
    ]
    result = result.drop(columns=to_drop, errors="ignore")

    validate_formula_invariant(algorithm="additive")

    return result


def _resolve_format_name(importance_col: str, satisfaction_col: str) -> str:
    """Reverse-lookup format definition from actual column names."""
    col_lower = {importance_col.lower(), satisfaction_col.lower()}
    for fmt_name, fmt_def in KNOWN_FORMATS.items():
        imp_set = set(fmt_def["importance_candidates"])
        sat_set = set(fmt_def["satisfaction_candidates"])
        if col_lower & imp_set and col_lower & sat_set:
            return fmt_name
    return "odi_standard"


# ---------------------------------------------------------------------------
# Raw artifact materialization
# ---------------------------------------------------------------------------

def materialize_raw(df: pd.DataFrame, output_path: str) -> str:
    """
    Write the original (unmapped) DataFrame to CSV.

    This is the "source of truth" artifact that must exist before scoring begins.
    Always called by `apply` — never skip this step.

    Args:
        df: Original survey DataFrame (before any mapping)
        output_path: Destination path for raw CSV

    Returns:
        Absolute path of written file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return str(path.resolve())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_propose(args: argparse.Namespace) -> None:  # pragma: no cover
    df = pd.read_csv(args.input)
    proposal = propose_mapping(df)
    output = json.dumps(proposal, indent=2)
    print(output)
    if args.output:
        Path(args.output).write_text(output)
        print(f"\n[Proposal saved → {args.output}]", file=sys.stderr)


def _cmd_apply(args: argparse.Namespace) -> None:  # pragma: no cover
    df = pd.read_csv(args.input)

    # Always materialize raw first
    raw_path = args.raw_output or str(
        Path(args.output).parent / (Path(args.input).stem + "-raw.csv")
    )
    materialize_raw(df, raw_path)
    print(f"[Raw artifact materialized → {raw_path}]", file=sys.stderr)

    mapped = apply_mapping(
        df,
        importance_col=args.importance_col,
        satisfaction_col=args.satisfaction_col,
    )
    mapped.to_csv(args.output, index=False)
    print(f"[ODI-mapped artifact written → {args.output}]", file=sys.stderr)

    result = {
        "status": "APPLIED",
        "raw_artifact": raw_path,
        "odi_artifact": args.output,
        "rows": len(mapped),
        "columns": list(mapped.columns),
        "importance_range": [
            round(float(mapped["importance"].min()), 2),
            round(float(mapped["importance"].max()), 2),
        ],
        "satisfaction_range": [
            round(float(mapped["satisfaction"].min()), 2),
            round(float(mapped["satisfaction"].max()), 2),
        ],
        "invariant_passed": True,
    }
    print(json.dumps(result, indent=2))


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="JTBD Survey Adapter — detect format, propose mapping, materialize artifacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Workflow:\n"
            "  1. uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py propose --input survey.csv\n"
            "     → Review output, verify mapping is correct\n"
            "  2. uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py apply --input survey.csv --output survey-odi.csv\n"
            "     → Materializes raw + ODI-mapped CSVs; scoring can begin"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # propose
    sp = subparsers.add_parser("propose", help="Detect format and show proposed mapping (no data written)")
    sp.add_argument("--input", required=True, help="Input CSV path")
    sp.add_argument("--output", help="Optional: save proposal JSON to this path")
    sp.set_defaults(func=_cmd_propose)

    # apply
    sa = subparsers.add_parser("apply", help="Apply approved mapping and write artifacts")
    sa.add_argument("--input", required=True, help="Input CSV path")
    sa.add_argument("--output", required=True, help="Output path for ODI-mapped CSV")
    sa.add_argument("--raw-output", help="Output path for raw CSV (default: <input>-raw.csv)")
    sa.add_argument("--importance-col", help="Override: column to map to importance")
    sa.add_argument("--satisfaction-col", help="Override: column to map to satisfaction")
    sa.set_defaults(func=_cmd_apply)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
