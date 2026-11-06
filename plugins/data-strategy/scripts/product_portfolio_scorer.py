# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Data Product Portfolio scorer.

Scores data products against data-as-product rubric and contract maturity.

Command line: product_portfolio_scorer.py <input.json>
The input file holds the list of data products. The script prints one JSON object.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def classify_contract_maturity(product: dict) -> str:
    count = sum(bool(product.get(k)) for k in ("schema_defined", "sla_documented", "deprecation_policy"))
    if count == 3:
        return "defined"
    if count > 0:
        return "partial"
    return "none"


def score_product(product: dict) -> dict:
    if not product.get("name"):
        raise ValueError("Product must have a 'name' field")

    score_attrs = [
        bool(product.get("owner")),
        bool(product.get("consumers")),
        bool(product.get("quality_sla")),
        bool(product.get("versioned")),
        bool(product.get("documented")),
        bool(product.get("schema_defined")),
    ]
    completeness = round(sum(score_attrs) / len(score_attrs), 2)
    return {
        "name": product["name"],
        "completeness": completeness,
        "contract_maturity": classify_contract_maturity(product),
    }


def score_portfolio(products: list[dict]) -> dict:
    if not products:
        return {"products": [], "portfolio_maturity": "nascent"}

    scored = [score_product(p) for p in products]
    avg = sum(p["completeness"] for p in scored) / len(scored)

    if avg >= 0.7:
        maturity = "mature"
    elif avg >= 0.4:
        maturity = "developing"
    else:
        maturity = "nascent"

    return {"products": scored, "portfolio_maturity": maturity}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: product_portfolio_scorer.py <input.json>", file=sys.stderr)
        return 1
    try:
        result = score_portfolio(json.loads(Path(argv[1]).read_text()))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"product_portfolio_scorer.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
