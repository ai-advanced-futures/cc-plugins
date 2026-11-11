# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
ML evaluation metric calculations.
Grounded in: Géron Ch.3 (precision, recall, F1, ROC/AUC)
"""


def precision(tp: float, fp: float) -> float:
    """Precision = TP / (TP + FP). Returns 0 if denominator is 0."""
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0


def recall(tp: float, fn: float) -> float:
    """Recall = TP / (TP + FN). Returns 0 if denominator is 0."""
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0


def f1_score(precision_val: float, recall_val: float) -> float:
    """F1 = 2 * (P * R) / (P + R). Harmonic mean of precision and recall."""
    denom = precision_val + recall_val
    return 2 * (precision_val * recall_val) / denom if denom > 0 else 0.0


def accuracy(tp: float, tn: float, fp: float, fn: float) -> float:
    """Accuracy = (TP + TN) / total."""
    total = tp + tn + fp + fn
    return (tp + tn) / total if total > 0 else 0.0


def confusion_matrix_stats(tp: float, tn: float, fp: float, fn: float) -> dict:
    """Compute all standard metrics from confusion matrix values."""
    p = precision(tp, fp)
    r = recall(tp, fn)
    return {
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1": round(f1_score(p, r), 4),
        "accuracy": round(accuracy(tp, tn, fp, fn), 4),
    }


def roc_auc_estimate(tpr_fpr_pairs: list) -> float:
    """Estimate AUC using trapezoidal rule from list of (TPR, FPR) pairs."""
    if len(tpr_fpr_pairs) < 2:
        return 0.0
    sorted_pairs = sorted(tpr_fpr_pairs, key=lambda x: x[1])
    auc = 0.0
    for i in range(1, len(sorted_pairs)):
        fpr_delta = sorted_pairs[i][1] - sorted_pairs[i - 1][1]
        tpr_avg = (sorted_pairs[i][0] + sorted_pairs[i - 1][0]) / 2
        auc += fpr_delta * tpr_avg
    return round(auc, 4)


def main(argv=None):
    import argparse
    import json
    import os
    import sys

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
        text = json.dumps(result)
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

    arguments = list(sys.argv[1:] if argv is None else argv)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", help="write the JSON object to this file inside the folder .aiml "
                                      "(the old file is deleted first), and print nothing")

    parser = Parser(description="Evaluation metrics. Prints one JSON object, or writes it to --out.",
                    allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("confusion", parents=[common], allow_abbrev=False,
                       help="Precision, recall, F1 and accuracy from a confusion matrix")
    p.add_argument("--input", help='JSON file, for example {"tp": 80, "tn": 90, "fp": 10, "fn": 20}')
    p.add_argument("--tp", type=float)
    p.add_argument("--tn", type=float)
    p.add_argument("--fp", type=float)
    p.add_argument("--fn", type=float)

    p = sub.add_parser("roc-auc", parents=[common], allow_abbrev=False,
                       help="AUC from (TPR, FPR) pairs by the trapezoidal rule")
    p.add_argument("--input", required=True,
                   help='JSON file, for example {"pairs": [[0, 0], [0.8, 0.2], [1, 1]]}')

    args = parser.parse_args(arguments)

    if args.command == "confusion":
        old = {"tp": args.tp, "tn": args.tn, "fp": args.fp, "fn": args.fn}
        if args.input is not None:
            given = [f"--{name}" for name, value in old.items() if value is not None]
            if given:
                fail(f"confusion: --input does not go with {', '.join(given)}")
            discard_old(args.out)
            data = read_input(args.input, {name: (is_number, "a number") for name in old})
            values = [data[name] for name in old]
        else:
            if any(value is None for value in old.values()):
                fail("confusion: give --input, or each of --tp, --tn, --fp and --fn")
            discard_old(args.out)
            values = list(old.values())
        result = confusion_matrix_stats(*values)
    else:
        discard_old(args.out)
        data = read_input(args.input, {"pairs": (
            lambda v: isinstance(v, list) and all(
                isinstance(x, list) and len(x) == 2 and all(isinstance(n, (int, float)) for n in x)
                for x in v
            ),
            "a list of [tpr, fpr] pairs")})
        result = {"auc": roc_auc_estimate(data["pairs"])}
    emit(result, args.out)


if __name__ == "__main__":
    main()
