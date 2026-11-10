# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Data Product Portfolio scorer.

Scores data products against data-as-product rubric and contract maturity.

Command line: product_portfolio_scorer.py <input.json> [--out <output.json>]
The input file holds the list of data products, or an object with a "products" list.
Without --out, the script prints one JSON object.
With --out, the script writes the JSON object to the output file and prints one line.
After an error, the script writes no output file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SHAPE = 'expected a list of product objects, or an object with a "products" list'


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


def products_from(data, source: str) -> list[dict]:
    """Return the products of a products.json value: a list, or the "products" list of an object.

    An agent can put its list in an object with other keys, because a model cannot be forced to give 1 shape.
    """
    if isinstance(data, dict) and isinstance(data.get("products"), list):
        data = data["products"]
    if not isinstance(data, list):
        raise ValueError(f"{source}: {SHAPE}")
    for number, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{source}: item {number} is not a product object: {json.dumps(item)[:60]}")
    return data


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
    if len(argv) == 2:
        out = None
    elif len(argv) == 4 and argv[2] == "--out":
        out = Path(argv[3])
    else:
        print("Usage: product_portfolio_scorer.py <input.json> [--out <output.json>]", file=sys.stderr)
        return 1
    try:
        result = score_portfolio(products_from(json.loads(Path(argv[1]).read_text()), argv[1]))
        if out is not None:
            out.write_text(json.dumps(result))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"product_portfolio_scorer.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result) if out is None else f"portfolio_maturity={result['portfolio_maturity']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
