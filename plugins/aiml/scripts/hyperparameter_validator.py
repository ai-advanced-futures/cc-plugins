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
    import sys as _sys
    parser = argparse.ArgumentParser(description="Hyperparameter search space validation. Prints one JSON object for each check.")
    parser.add_argument("--validate", action="store_true", help="Smoke test — exits 0 if module loads correctly")
    parser.add_argument("--lr", type=float, help="Validate learning rate value")
    parser.add_argument("--batch-size", type=int, help="Validate batch size value")
    parser.add_argument("--epochs", type=int, help="Validate epoch count")
    parser.add_argument("--lora-rank", type=int, help="LoRA rank R (use with --lora-alpha and --lora-dropout)")
    parser.add_argument("--lora-alpha", type=float, help="LoRA alpha A")
    parser.add_argument("--lora-dropout", type=float, help="LoRA dropout D")
    args = parser.parse_args(argv)

    if args.validate:
        print("hyperparameter_validator.py OK")
        _sys.exit(0)

    lora = (args.lora_rank, args.lora_alpha, args.lora_dropout)
    if any(v is not None for v in lora) and any(v is None for v in lora):
        print("error: --lora-rank, --lora-alpha and --lora-dropout go together", file=_sys.stderr)
        _sys.exit(1)

    if args.lr is not None:
        print(json.dumps(validate_learning_rate(args.lr)))
    if args.batch_size is not None:
        print(json.dumps(validate_batch_size(args.batch_size, dataset_size=10000)))
    if args.epochs is not None:
        print(json.dumps(validate_epochs(args.epochs, dataset_size=10000, batch_size=32)))
    if args.lora_rank is not None:
        print(json.dumps(validate_lora_config(args.lora_rank, args.lora_alpha, args.lora_dropout)))


if __name__ == "__main__":
    main()
