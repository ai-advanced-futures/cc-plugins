# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas==3.1.1", "numpy==2.4.6", "scikit-learn==1.9.1"]
# ///
"""Phase 8: cluster the respondents of a survey file into segments.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_8.py --input '<survey>' --segment-count <n> --id-col 'respondent_id' --out '<session_dir>/p8-clusters.json'

The input is a CSV with one row for each respondent and numeric columns for the ratings. The script
keeps the rows that are 80% complete or better, takes out the id column, and fills a missing value
with the mean of its column. It calls `find_optimal_k(k_range=(2, min(8, rows)))` of
`scripts/segmentation_engine.py`, and then clusters twice: at --segment-count, and at the optimal k.
For each clustering it calls `generate_segment_profiles()`.

--out gets both clusterings. Each segment has `segment_id` (from 1) and `size_percent`
(`percentage` times 100). The file `p8-respondents.json` in the folder of --out gets the segment
of each respondent for both clusterings.
Exit 0: the files are written, and one line `k_used=<n> optimal_k=<n>` is on stdout. Exit 1: an
input error (1 line on stderr, no file). Exit 2: usage.
"""
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.segmentation_engine import SegmentationEngine  # noqa: E402

MIN_COMPLETE = 0.8
MAX_K = 8


def prepare(df, id_col):
    """The rows to cluster and the id of each row. Raises ValueError when no row is left."""
    ids = df[id_col] if id_col in df.columns else pd.Series(range(1, len(df) + 1), index=df.index)
    features = df.drop(columns=[id_col], errors="ignore")
    complete = features.notna().mean(axis=1) >= MIN_COMPLETE
    features, ids = features[complete], ids[complete]
    features = features.loc[features.select_dtypes(include=[np.number]).notna().any(axis=1)]
    ids = ids.loc[features.index]
    numeric = features.select_dtypes(include=[np.number]).columns
    features = features.copy()
    features[numeric] = features[numeric].fillna(features[numeric].mean())
    if features.empty:
        raise ValueError("no row is 80% complete with a number in it")
    return features.reset_index(drop=True), ids.reset_index(drop=True)


def _segments(engine, k):
    """Cluster at k. Returns the segments (ids from 1) and the segment of each row (from 1)."""
    clustered = engine.cluster(k=k)
    segments = []
    for profile in engine.generate_segment_profiles():
        segments.append(
            {
                "segment_id": int(profile["segment_id"]) + 1,
                "size": int(profile["size"]),
                "size_percent": round(float(profile["percentage"]) * 100, 1),
                "top_needs": list(profile["top_needs"]),
                "avg_importance": round(float(profile["avg_importance"]), 2),
                "avg_satisfaction": round(float(profile["avg_satisfaction"]), 2),
                "gap": round(float(profile["gap"]), 2),
                "characteristics": profile["characteristics"],
            }
        )
    return segments, [int(s) + 1 for s in clustered["segment"]]


def run(input_path, segment_count, id_col, out_path):
    """Cluster the file and write both result files. Returns (k_used, optimal_k)."""
    features, ids = prepare(pd.read_csv(input_path), id_col)
    max_k = min(MAX_K, len(features))
    engine = SegmentationEngine(features)
    optimal = engine.find_optimal_k(k_range=(2, max_k))
    optimal_k = int(optimal["optimal_k"])
    silhouette = dict(zip(optimal["k_values"], optimal["silhouette_scores"]))

    def clustering(k):
        segments, assignment = _segments(engine, k)
        score = silhouette.get(k)
        return {
            "k": k,
            "silhouette_at_k": None if score is None else round(float(score), 4),
            "segments": segments,
        }, assignment

    chosen, chosen_rows = clustering(segment_count)
    best, best_rows = clustering(optimal_k)
    payload = {
        "rows_used": len(features),
        "feature_columns": list(engine.feature_columns),
        "optimal_k": optimal_k,
        "recommendation": optimal["recommendation"],
        "segment_count_clustering": chosen,
        "optimal_clustering": best,
    }
    respondents = [
        {"respondent": None if pd.isna(i) else (i.item() if hasattr(i, "item") else i), "segment_id": a, "optimal_segment_id": b}
        for i, a, b in zip(ids, chosen_rows, best_rows)
    ]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out.parent / "p8-respondents.json").write_text(json.dumps(respondents, indent=2), encoding="utf-8")
    return segment_count, optimal_k


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_phase_8.py", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the survey CSV, one row for each respondent")
    parser.add_argument("--segment-count", required=True, type=int, help="the number of segments to start with")
    parser.add_argument("--id-col", default="respondent_id", help="the id column to leave out of the clustering")
    parser.add_argument("--out", required=True, help="the result file")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    try:
        used, optimal_k = run(args.input, args.segment_count, args.id_col, args.out)
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as err:
        print("run_phase_8.py: %s" % err, file=sys.stderr)
        return 1
    print("k_used=%d optimal_k=%d" % (used, optimal_k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
