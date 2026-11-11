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
    if minority == 0:
        return {"balanced": False, "reason": "A class has 0 samples", "imbalance_ratio": None, "minority_pct": 0.0,
                "recommendation": "Collect samples of each class that has 0, or remove the class"}
    ratio = majority / minority
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
    import os
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _safe_input import InputFileError, finite_float, finite_int, read_json

    def fail(message):
        print(f"error: {message}", file=sys.stderr)
        sys.exit(1)

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            fail(message)

    def discard_old(out):
        """Check `--out`, then delete its old file, so that a file that exists after exit 0 is from this run.

        `--out` must be a file inside the folder `.aiml` of the current directory. A `..`, an absolute path
        outside it, and a link to an outside folder are refused. Call this after the arguments pass.
        """
        if out is None:
            return
        if not os.path.realpath(out).startswith(os.path.join(os.path.realpath("."), ".aiml") + os.sep):
            fail(f"{out}: --out must be a file inside the folder .aiml of the current directory")
        try:
            os.unlink(out)
        except FileNotFoundError:
            pass
        except OSError as exc:
            fail(f"{out}: cannot remove the old file: {exc.strerror}")

    def emit(result, out):
        """Print the JSON object, or write it to `out` (the object and a new line) and print nothing."""
        try:
            text = json.dumps(result, allow_nan=False)
        except ValueError:
            fail("the result holds a number that is not finite")
        if out is None:
            print(text)
            return
        try:
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            with open(out, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
        except OSError as exc:
            fail(f"{out}: cannot write the file: {exc.strerror}")

    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def read_input(path, keys, optional=None):
        """Read the input file. Each key of `keys` maps to a check that returns True for a good value.

        A key of `optional` may be missing; when it is there, its value must pass its check.
        """
        try:
            data = read_json(path)
        except OSError as exc:
            fail(f"{path}: cannot read the file: {exc.strerror}")
        except InputFileError as exc:
            fail(str(exc))
        if not isinstance(data, dict):
            fail(f"{path}: must be a JSON object")
        for key, (is_good, kind) in keys.items():
            if key not in data:
                fail(f'{path}: no key "{key}"')
            if not is_good(data[key]):
                fail(f'{path}: key "{key}" must be {kind}')
        for key, (is_good, kind) in (optional or {}).items():
            if key in data and not is_good(data[key]):
                fail(f'{path}: key "{key}" must be {kind}')
        return data

    def no_old_option(args, command, names):
        """`--input` and an old option do not go together."""
        given = [f"--{name.replace('_', '-')}" for name in names if getattr(args, name) is not None]
        if given:
            fail(f"{command}: --input does not go with {', '.join(given)}")

    arguments = list(sys.argv[1:] if argv is None else argv)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", help="write the JSON object to this file inside the folder .aiml "
                                      "(the old file is deleted first), and print nothing")

    parser = Parser(description="Dataset quality checks. Prints one JSON object, or writes it to --out.",
                    allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("split", parents=[common], allow_abbrev=False,
                       help="Check that train, val and test ratios sum to 1")
    p.add_argument("--input", help='JSON file, for example {"train": 0.7, "val": 0.15, "test": 0.15}; '
                                   'the key "tolerance" is optional (default 0.01)')
    p.add_argument("--train", type=finite_float)
    p.add_argument("--val", type=finite_float)
    p.add_argument("--test", type=finite_float)
    p.add_argument("--tolerance", type=finite_float)

    p = sub.add_parser("balance", parents=[common], allow_abbrev=False, help="Check the class balance")
    p.add_argument("--input", required=True,
                   help='JSON file, for example {"class_counts": {"a": 900, "b": 100}}')

    p = sub.add_parser("min-samples", parents=[common], allow_abbrev=False,
                       help="Estimate the minimum number of samples")
    p.add_argument("--input", help='JSON file, for example {"task": "classification", "num_classes": 3}; '
                                   'the keys "num_classes" (default 2) and "target_accuracy" (default 0.90) are optional')
    p.add_argument("--task", help="classification, regression or llm_finetune")
    p.add_argument("--num-classes", type=finite_int)
    p.add_argument("--target-accuracy", type=finite_float)

    p = sub.add_parser("leakage", parents=[common], allow_abbrev=False,
                       help="Flag features that can leak the target")
    p.add_argument("--input", required=True,
                   help='JSON file, for example {"features": ["age", "outcome_flag"], "target": "churn"}')

    args = parser.parse_args(arguments)

    if args.command == "split":
        if args.input is not None:
            no_old_option(args, "split", ("train", "val", "test", "tolerance"))
            discard_old(args.out)
            data = read_input(args.input, {
                "train": (is_number, "a number"),
                "val": (is_number, "a number"),
                "test": (is_number, "a number"),
            }, {"tolerance": (is_number, "a number")})
            result = validate_split_ratios(data["train"], data["val"], data["test"], data.get("tolerance", 0.01))
        else:
            if args.train is None or args.val is None or args.test is None:
                fail("split: give --input, or each of --train, --val and --test")
            discard_old(args.out)
            tolerance = 0.01 if args.tolerance is None else args.tolerance
            result = validate_split_ratios(args.train, args.val, args.test, tolerance)
    elif args.command == "balance":
        discard_old(args.out)
        data = read_input(args.input, {"class_counts": (
            lambda v: isinstance(v, dict) and all(
                isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in v.values()),
            "an object of whole numbers of 0 or more")})
        result = check_class_balance(data["class_counts"])
    elif args.command == "min-samples":
        if args.input is not None:
            no_old_option(args, "min-samples", ("task", "num_classes", "target_accuracy"))
            discard_old(args.out)
            data = read_input(args.input, {"task": (lambda v: isinstance(v, str), "a string")}, {
                "num_classes": (lambda v: isinstance(v, int) and not isinstance(v, bool), "an integer"),
                "target_accuracy": (is_number, "a number"),
            })
            result = estimate_minimum_samples(data["task"], data.get("num_classes", 2),
                                              data.get("target_accuracy", 0.90))
        else:
            if args.task is None:
                fail("min-samples: give --input, or --task")
            discard_old(args.out)
            result = estimate_minimum_samples(
                args.task,
                2 if args.num_classes is None else args.num_classes,
                0.90 if args.target_accuracy is None else args.target_accuracy)
    else:
        discard_old(args.out)
        data = read_input(args.input, {
            "features": (lambda v: isinstance(v, list) and all(isinstance(f, str) for f in v), "a list of strings"),
            "target": (lambda v: isinstance(v, str), "a string"),
        })
        result = detect_leakage_risk(data["features"], data["target"])
    emit(result, args.out)


if __name__ == "__main__":
    main()
