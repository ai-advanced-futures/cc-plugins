# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Dataset quality validation for ML projects.
Grounded in: Géron Ch.2 (end-to-end ML project, data strategy),
             Iusztin & Labonne (data collection for LLMs)
"""


def validate_split_ratios(train: float, val: float, test: float,
                           tolerance: float = 0.01) -> dict:
    """Validate train/val/test split ratios sum to 1.0."""
    total = train + val + test
    warnings = []
    if abs(total - 1.0) > tolerance:
        return {"valid": False, "reason": f"Splits sum to {total:.3f}, not 1.0", "warnings": []}
    if test < 0.10:
        warnings.append(f"Test set is {test*100:.0f}% — recommend at least 10%")
    if val > 0 and val < 0.05:
        warnings.append(f"Validation set is {val*100:.0f}% — may be too small")
    return {"valid": True, "warnings": warnings}


def check_class_balance(class_counts: dict) -> dict:
    """Check if class distribution is balanced enough for training."""
    total = sum(class_counts.values())
    if total == 0:
        return {"balanced": False, "reason": "No samples", "imbalance_ratio": 0, "minority_pct": 0}
    counts = list(class_counts.values())
    minority = min(counts)
    majority = max(counts)
    ratio = majority / minority if minority > 0 else float("inf")
    minority_pct = (minority / total) * 100
    return {
        "balanced": ratio <= 10,
        "imbalance_ratio": round(ratio, 2),
        "minority_pct": round(minority_pct, 2),
        "recommendation": "Consider SMOTE or class weighting" if ratio > 10 else None,
    }


def estimate_minimum_samples(task: str, num_classes: int = 2,
                              target_accuracy: float = 0.90) -> dict:
    """Rule-of-thumb minimum sample estimates. Géron Ch.2 + Andrew Ng data-centric guidance."""
    base = 1000
    if task == "classification":
        minimum = base * num_classes * (1 + (target_accuracy - 0.80) * 10)
    elif task == "regression":
        minimum = base * (1 + (target_accuracy - 0.80) * 5)
    elif task == "llm_finetune":
        minimum = 500
    else:
        minimum = base
    return {"minimum": int(minimum), "task": task, "note": "Rule-of-thumb — actual needs vary"}


def detect_leakage_risk(feature_names: list, target_name: str) -> dict:
    """Flag features that may cause data leakage into the target variable."""
    risky = []
    risk_keywords = ["future", "post", "after", "result", "outcome", "label", "target"]
    target_lower = target_name.lower()
    for feat in feature_names:
        feat_lower = feat.lower()
        if target_lower in feat_lower:
            risky.append(feat)
        elif any(kw in feat_lower for kw in risk_keywords):
            risky.append(feat)
    return {
        "leakage_risk": len(risky) > 0,
        "risky_features": risky,
        "recommendation": "Remove or investigate these features before training" if risky else None,
    }


def main(argv=None):
    import argparse
    import json
    import sys

    def fail(message):
        print(f"error: {message}", file=sys.stderr)
        sys.exit(1)

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            fail(message)

    def read_input(path, keys):
        """Read the input file. Each key of `keys` maps to a check that returns True for a good value."""
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError as exc:
            fail(f"{path}: cannot read the file: {exc.strerror}")
        except ValueError as exc:
            fail(f"{path}: not valid JSON: {exc}")
        if not isinstance(data, dict):
            fail(f"{path}: must be a JSON object")
        for key, (is_good, kind) in keys.items():
            if key not in data:
                fail(f'{path}: no key "{key}"')
            if not is_good(data[key]):
                fail(f'{path}: key "{key}" must be {kind}')
        return data

    parser = Parser(description="Dataset quality checks. Prints one JSON object.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("split", help="Check that train, val and test ratios sum to 1")
    p.add_argument("--train", type=float, required=True)
    p.add_argument("--val", type=float, required=True)
    p.add_argument("--test", type=float, required=True)
    p.add_argument("--tolerance", type=float, default=0.01)

    p = sub.add_parser("balance", help="Check the class balance")
    p.add_argument("--input", required=True,
                   help='JSON file, for example {"class_counts": {"a": 900, "b": 100}}')

    p = sub.add_parser("min-samples", help="Estimate the minimum number of samples")
    p.add_argument("--task", required=True, help="classification, regression or llm_finetune")
    p.add_argument("--num-classes", type=int, default=2)
    p.add_argument("--target-accuracy", type=float, default=0.90)

    p = sub.add_parser("leakage", help="Flag features that can leak the target")
    p.add_argument("--input", required=True,
                   help='JSON file, for example {"features": ["age", "outcome_flag"], "target": "churn"}')

    args = parser.parse_args(argv)

    if args.command == "split":
        result = validate_split_ratios(args.train, args.val, args.test, args.tolerance)
    elif args.command == "balance":
        data = read_input(args.input, {"class_counts": (
            lambda v: isinstance(v, dict) and all(isinstance(n, (int, float)) for n in v.values()),
            "an object of numbers")})
        result = check_class_balance(data["class_counts"])
    elif args.command == "min-samples":
        result = estimate_minimum_samples(args.task, args.num_classes, args.target_accuracy)
    else:
        data = read_input(args.input, {
            "features": (lambda v: isinstance(v, list) and all(isinstance(f, str) for f in v), "a list of strings"),
            "target": (lambda v: isinstance(v, str), "a string"),
        })
        result = detect_leakage_risk(data["features"], data["target"])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
