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
    import sys

    def fail(message):
        print(f"error: {message}", file=sys.stderr)
        sys.exit(1)

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            fail(message)

    def json_arg(text):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise argparse.ArgumentTypeError(f"not valid JSON: {exc.msg}")

    parser = Parser(description="Evaluation metrics. Prints one JSON object.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("confusion", help="Precision, recall, F1 and accuracy from a confusion matrix")
    p.add_argument("--tp", type=float, required=True)
    p.add_argument("--tn", type=float, required=True)
    p.add_argument("--fp", type=float, required=True)
    p.add_argument("--fn", type=float, required=True)

    p = sub.add_parser("roc-auc", help="AUC from (TPR, FPR) pairs by the trapezoidal rule")
    p.add_argument("--pairs", type=json_arg, required=True,
                   help="JSON list of [tpr, fpr] pairs, for example '[[0,0],[0.8,0.2],[1,1]]'")

    args = parser.parse_args(argv)

    if args.command == "confusion":
        result = confusion_matrix_stats(args.tp, args.tn, args.fp, args.fn)
    else:
        pairs = args.pairs
        if not isinstance(pairs, list) or not all(
            isinstance(x, list) and len(x) == 2 and all(isinstance(v, (int, float)) for v in x)
            for x in pairs
        ):
            fail("--pairs must be a JSON list of [tpr, fpr] pairs")
        result = {"auc": roc_auc_estimate(pairs)}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
