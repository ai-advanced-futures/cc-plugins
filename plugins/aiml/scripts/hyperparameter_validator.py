# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Hyperparameter search space sanity checks.
Grounded in: Géron Ch.11 (training deep nets, hyperparameters, gradient issues),
             Iusztin & Labonne (fine-tuning hyperparameters for LLMs)
"""


def validate_learning_rate(lr: float) -> dict:
    """Check if learning rate is in a reasonable range."""
    warnings = []
    valid = True
    if lr <= 0:
        return {"valid": False, "reason": "Learning rate must be positive", "warnings": []}
    if lr > 0.1:
        warnings.append(f"lr={lr} is very high — risk of divergence. Consider ≤ 0.01")
    if lr < 1e-6:
        warnings.append(f"lr={lr} is very low — training may be extremely slow")
    if lr > 1e-2:
        warnings.append("For fine-tuning LLMs, typical range is 1e-5 to 5e-4")
    return {"valid": valid, "lr": lr, "warnings": warnings}


def validate_batch_size(batch_size: int, dataset_size: int) -> dict:
    """Check batch size is sensible relative to dataset size."""
    warnings = []
    if batch_size <= 0:
        return {"valid": False, "reason": "Batch size must be positive", "warnings": []}
    if batch_size > dataset_size:
        return {"valid": False, "reason": "Batch size exceeds dataset size", "warnings": []}
    if batch_size > dataset_size * 0.1:
        warnings.append("Batch size is >10% of dataset — full-batch gradient may overfit")
    if batch_size not in [8, 16, 32, 64, 128, 256, 512]:
        warnings.append("Non-power-of-2 batch sizes are less GPU-efficient")
    return {"valid": True, "batch_size": batch_size, "warnings": warnings}


def validate_epochs(epochs: int, dataset_size: int, batch_size: int) -> dict:
    """Estimate total gradient steps and warn about over/underfitting risk."""
    if epochs <= 0:
        return {"valid": False, "reason": "Epochs must be positive", "warnings": []}
    steps_per_epoch = max(1, dataset_size // batch_size)
    total_steps = epochs * steps_per_epoch
    warnings = []
    if epochs > 100 and dataset_size < 10000:
        warnings.append("High epoch count on small dataset — overfitting risk")
    if total_steps < 100:
        warnings.append("Very few total steps — model may underfit")
    return {
        "valid": True,
        "epochs": epochs,
        "steps_per_epoch": steps_per_epoch,
        "total_steps": total_steps,
        "warnings": warnings,
    }


def validate_lora_config(rank: int, alpha: float, dropout: float) -> dict:
    """Validate LoRA fine-tuning hyperparameters. Iusztin & Labonne Ch. on PEFT/LoRA."""
    warnings = []
    if rank <= 0:
        return {"valid": False, "reason": "LoRA rank must be positive", "warnings": []}
    if rank > 256:
        warnings.append("rank > 256 approaches full fine-tuning; consider smaller rank")
    if alpha <= 0:
        return {"valid": False, "reason": "LoRA alpha must be positive", "warnings": []}
    if alpha / rank > 2:
        warnings.append(f"alpha/rank ratio is {alpha/rank:.1f} — typical is 0.5–2.0")
    if not 0.0 <= dropout < 1.0:
        return {"valid": False, "reason": "Dropout must be in [0, 1)", "warnings": []}
    return {
        "valid": True,
        "rank": rank,
        "alpha": alpha,
        "dropout": dropout,
        "scaling_factor": alpha / rank,
        "warnings": warnings,
    }


def suggest_search_space(model_type: str) -> dict:
    """Return recommended hyperparameter search ranges by model type."""
    spaces = {
        "classifier": {
            "learning_rate": [1e-4, 1e-2],
            "batch_size": [32, 256],
            "epochs": [10, 100],
        },
        "llm_finetune": {
            "learning_rate": [1e-5, 5e-4],
            "batch_size": [4, 32],
            "epochs": [1, 5],
            "lora_rank": [8, 64],
        },
        "deep_neural_net": {
            "learning_rate": [1e-4, 1e-2],
            "batch_size": [32, 512],
            "epochs": [20, 200],
            "dropout": [0.0, 0.5],
        },
    }
    return spaces.get(model_type, spaces["classifier"])


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

    def show(result):
        emit(result, None)

    def is_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def is_integer(value):
        return isinstance(value, int) and not isinstance(value, bool)

    def is_lora(value):
        return (isinstance(value, dict) and set(value) == {"rank", "alpha", "dropout"}
                and is_integer(value["rank"]) and is_number(value["alpha"]) and is_number(value["dropout"]))

    # Each key of the input file: the check of a value, what the value must be, and the function of today.
    checks = {
        "lr": (is_number, "a number", lambda v: validate_learning_rate(v)),
        "batch_size": (is_integer, "an integer", lambda v: validate_batch_size(v, dataset_size=10000)),
        "epochs": (is_integer, "an integer", lambda v: validate_epochs(v, dataset_size=10000, batch_size=32)),
        "lora": (is_lora, 'an object with the keys "rank" (an integer), "alpha" and "dropout" (numbers)',
                 lambda v: validate_lora_config(v["rank"], v["alpha"], v["dropout"])),
    }

    def read_input(path):
        """Read the input file: each key is 1 or 2 values to check, in order. Returns the results in the same order."""
        try:
            data = read_json(path)
        except OSError as exc:
            fail(f"{path}: cannot read the file: {exc.strerror}")
        except InputFileError as exc:
            fail(str(exc))
        if not isinstance(data, dict):
            fail(f"{path}: must be a JSON object")
        for key, values in data.items():
            if key not in checks:
                fail(f'{path}: key "{key}" is not one of {", ".join(checks)}')
            if not isinstance(values, list) or not 1 <= len(values) <= 2:
                fail(f'{path}: key "{key}" must be a list of 1 or 2 values')
            is_good, kind, _ = checks[key]
            if not all(is_good(v) for v in values):
                fail(f'{path}: each value of key "{key}" must be {kind}')
        return {key: [checks[key][2](v) for v in values] for key, values in data.items()}

    arguments = list(sys.argv[1:] if argv is None else argv)

    parser = Parser(description="Hyperparameter search space validation. Prints one JSON object for each check, "
                                "or, with --input, one JSON object for the whole file.",
                    allow_abbrev=False)
    parser.add_argument("--validate", action="store_true", help="Smoke test — exits 0 if module loads correctly")
    parser.add_argument("--input", help='JSON file, for example {"lr": [0.0003, 0.0001], "batch_size": [32]}: '
                                        'each key (lr, batch_size, epochs, lora) holds 1 or 2 values, in order')
    parser.add_argument("--out", help="with --input: write the JSON object to this file inside the folder .aiml "
                                      "(the old file is deleted first), and print nothing")
    parser.add_argument("--lr", type=finite_float, help="Validate learning rate value")
    parser.add_argument("--batch-size", type=finite_int, help="Validate batch size value")
    parser.add_argument("--epochs", type=finite_int, help="Validate epoch count")
    parser.add_argument("--lora-rank", type=finite_int, help="LoRA rank R (use with --lora-alpha and --lora-dropout)")
    parser.add_argument("--lora-alpha", type=finite_float, help="LoRA alpha A")
    parser.add_argument("--lora-dropout", type=finite_float, help="LoRA dropout D")
    args = parser.parse_args(arguments)

    if args.validate:
        print("hyperparameter_validator.py OK")
        sys.exit(0)

    old = {"--lr": args.lr, "--batch-size": args.batch_size, "--epochs": args.epochs,
           "--lora-rank": args.lora_rank, "--lora-alpha": args.lora_alpha, "--lora-dropout": args.lora_dropout}
    if args.input is not None:
        given = [name for name, value in old.items() if value is not None]
        if given:
            fail(f"--input does not go with {', '.join(given)}")
        discard_old(args.out)
        emit(read_input(args.input), args.out)
        return
    if args.out is not None:
        fail("--out goes with --input")

    lora = (args.lora_rank, args.lora_alpha, args.lora_dropout)
    if any(v is not None for v in lora) and any(v is None for v in lora):
        fail("--lora-rank, --lora-alpha and --lora-dropout go together")

    if args.lr is not None:
        show(validate_learning_rate(args.lr))
    if args.batch_size is not None:
        show(validate_batch_size(args.batch_size, dataset_size=10000))
    if args.epochs is not None:
        show(validate_epochs(args.epochs, dataset_size=10000, batch_size=32))
    if args.lora_rank is not None:
        show(validate_lora_config(args.lora_rank, args.lora_alpha, args.lora_dropout))


if __name__ == "__main__":
    main()
