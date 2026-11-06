# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Training and inference cost projection.
Grounded in: Iusztin & Labonne (LLM cost modeling),
             public cloud GPU pricing (A100/H100 rates 2025)
Note: Order-of-magnitude estimates only.
"""

GPU_COST_PER_HOUR = {"a100": 3.0, "h100": 6.0, "t4": 0.35}
FRONTIER_LLM_COST_PER_1M_TOKENS = 5.0
AVG_TOKENS_PER_REQUEST = 500


def estimate_training_cost(approach: str, params_billions: float,
                            hours: float, gpu: str = "a100") -> dict:
    """Estimate training cost based on approach, model size, and duration."""
    gpu_rate = GPU_COST_PER_HOUR.get(gpu, GPU_COST_PER_HOUR["a100"])
    gpu_count = max(1, int(params_billions / 7))
    multiplier = {"pretrain": 10, "finetune": 1, "sft": 1.5, "rlhf": 3}.get(approach, 1)
    gpu_hours = hours * gpu_count * multiplier
    return {
        "approach": approach,
        "gpu_hours": round(gpu_hours, 1),
        "usd": round(gpu_hours * gpu_rate, 2),
        "note": "Order-of-magnitude estimate",
    }


def estimate_inference_cost(model_type: str, requests_per_day: int,
                             tokens_per_request: int = AVG_TOKENS_PER_REQUEST) -> dict:
    """Estimate daily inference cost by model type."""
    if model_type == "frontier_llm":
        tokens_per_day = requests_per_day * tokens_per_request
        usd = (tokens_per_day / 1_000_000) * FRONTIER_LLM_COST_PER_1M_TOKENS
    elif model_type == "hosted_oss":
        usd = requests_per_day * 0.0001
    elif model_type == "classifier":
        usd = requests_per_day * 0.000001
    else:
        usd = requests_per_day * 0.00005
    return {
        "model_type": model_type,
        "requests_per_day": requests_per_day,
        "usd_per_day": round(usd, 4),
        "usd_per_month": round(usd * 30, 2),
    }


def compare_approaches(requests_per_day: int, training_hours: float = 8) -> list:
    """Compare cost across model approaches, sorted cheapest first."""
    options = [
        {**estimate_inference_cost("classifier", requests_per_day), "label": "Local classifier"},
        {**estimate_inference_cost("hosted_oss", requests_per_day), "label": "Hosted OSS model"},
        {**estimate_inference_cost("frontier_llm", requests_per_day), "label": "Frontier LLM API"},
    ]
    return sorted(options, key=lambda x: x["usd_per_day"])


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

    parser = Parser(description="Cost estimates (order of magnitude). Prints one JSON object.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("training", help="Estimate the training cost")
    p.add_argument("--approach", required=True, help="pretrain, finetune, sft or rlhf")
    p.add_argument("--params-billions", type=float, required=True)
    p.add_argument("--hours", type=float, required=True)
    p.add_argument("--gpu", default="a100", help="a100, h100 or t4")

    p = sub.add_parser("inference", help="Estimate the daily inference cost")
    p.add_argument("--model-type", required=True, help="frontier_llm, hosted_oss or classifier")
    p.add_argument("--requests-per-day", type=int, required=True)
    p.add_argument("--tokens-per-request", type=int, default=AVG_TOKENS_PER_REQUEST)

    p = sub.add_parser("compare", help="Compare the inference cost of the three approaches")
    p.add_argument("--requests-per-day", type=int, required=True)
    p.add_argument("--training-hours", type=float, default=8)

    args = parser.parse_args(argv)

    if args.command == "training":
        result = estimate_training_cost(args.approach, args.params_billions, args.hours, args.gpu)
    elif args.command == "inference":
        result = estimate_inference_cost(args.model_type, args.requests_per_day, args.tokens_per_request)
    else:
        result = {"options": compare_approaches(args.requests_per_day, args.training_hours)}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
