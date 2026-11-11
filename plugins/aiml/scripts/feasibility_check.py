# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Feasibility check of the design flow: training cost, inference cost and minimum samples.
Reads one JSON file that the design-analyst agent writes, and writes one JSON file.
Order-of-magnitude estimates only (see cost_estimator.py and data_validator.py).

Input:  {"training": null | {"approach", "params_billions", "hours", "gpu"?},
         "inference": {"model_type", "requests_per_day"},
         "data": {"task", "num_classes"?, "target_accuracy"?}}
Output: {"ok": true, "training": ..., "inference": ..., "min_samples": ...}
        {"ok": false, "errors": [...]}
"""

APPROACHES = ("pretrain", "finetune", "sft", "rlhf")
GPUS = ("a100", "h100", "t4")
MODEL_TYPES = ("frontier_llm", "hosted_oss", "classifier")
TASKS = ("classification", "regression", "llm_finetune")


def _finite_number(value):
    """False for NaN (it is not equal to itself) and for Infinity."""
    return value == value and abs(value) != float("inf")


def _number(value):
    """True for a real number. A bool, NaN and Infinity are not numbers here."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and _finite_number(value)


def _enum(errors, where, obj, key, allowed):
    if obj.get(key) not in allowed:
        errors.append(f"{where}.{key} must be one of {', '.join(allowed)}")


def _positive(errors, where, obj, key, whole=False):
    value = obj.get(key)
    kind_ok = isinstance(value, int) and not isinstance(value, bool) if whole else _number(value)
    if not kind_ok or value <= 0:
        errors.append(f"{where}.{key} must be a {'whole ' if whole else ''}number greater than 0")


def _finite(value):
    """True when each number inside the value is finite."""
    if isinstance(value, float):
        return _finite_number(value)
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(v) for v in value)
    return True


def check_input(data):
    """Return the list of errors of the input object. An empty list means the input is good."""
    if not isinstance(data, dict):
        return ["the input must be a JSON object"]
    errors = []
    training = data.get("training")
    if "training" not in data:
        errors.append("training is missing: use null when the approach trains no model")
    elif training is not None:
        if not isinstance(training, dict):
            errors.append("training must be null or an object")
        else:
            _enum(errors, "training", training, "approach", APPROACHES)
            _positive(errors, "training", training, "params_billions")
            _positive(errors, "training", training, "hours")
            if "gpu" in training:
                _enum(errors, "training", training, "gpu", GPUS)
    inference = data.get("inference")
    if not isinstance(inference, dict):
        errors.append("inference must be an object")
    else:
        _enum(errors, "inference", inference, "model_type", MODEL_TYPES)
        _positive(errors, "inference", inference, "requests_per_day", whole=True)
    sample = data.get("data")
    if not isinstance(sample, dict):
        errors.append("data must be an object")
    else:
        _enum(errors, "data", sample, "task", TASKS)
        if "num_classes" in sample:
            _positive(errors, "data", sample, "num_classes", whole=True)
        if "target_accuracy" in sample:
            _positive(errors, "data", sample, "target_accuracy")
            if _number(sample["target_accuracy"]) and sample["target_accuracy"] >= 1:
                errors.append("data.target_accuracy must be below 1")
    return errors


def main(argv=None):
    import argparse
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from cost_estimator import estimate_inference_cost, estimate_training_cost
    from data_validator import estimate_minimum_samples
    from _safe_input import InputFileError, read_json

    def finish(result, out, code):
        text = json.dumps(result, allow_nan=False)  # the check at "too large to calculate" keeps it finite
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        if code:
            print("error: " + "; ".join(result["errors"]), file=sys.stderr)
        else:
            print(text)
        sys.exit(code)

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            print(f"error: {message}", file=sys.stderr)
            sys.exit(1)

    parser = Parser(description="Feasibility check. Reads one JSON file, writes one JSON file.")
    parser.add_argument("--input", required=True, help="the JSON input file")
    parser.add_argument("--out", required=True, help="the JSON output file")
    args = parser.parse_args(argv)
    out = Path(args.out)

    try:
        data = read_json(args.input)
    except OSError as exc:
        finish({"ok": False, "errors": [f"cannot read {args.input}: {exc}"]}, out, 1)
    except InputFileError as exc:
        finish({"ok": False, "errors": [f"cannot read {exc}"]}, out, 1)
    errors = check_input(data)
    if errors:
        finish({"ok": False, "errors": errors}, out, 1)

    training = data["training"]
    if training is not None:
        training = estimate_training_cost(
            training["approach"], training["params_billions"], training["hours"], training.get("gpu", "a100")
        )
    inference = estimate_inference_cost(data["inference"]["model_type"], data["inference"]["requests_per_day"])
    sample = data["data"]
    min_samples = estimate_minimum_samples(
        sample["task"], sample.get("num_classes", 2), sample.get("target_accuracy", 0.90)
    )
    result = {"ok": True, "training": training, "inference": inference, "min_samples": min_samples}
    if not _finite(result):
        finish({"ok": False, "errors": ["a cost is too large to calculate: use smaller numbers"]}, out, 1)
    finish(result, out, 0)


if __name__ == "__main__":
    main()
