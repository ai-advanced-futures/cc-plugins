# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
apollo_extractor.py — Apollo MCP response context firewall for strategic-partnerships.

Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/apollo_extractor.py <raw.json> [--out FILE]
The file holds the raw Apollo answer: a list of companies, or an object with an
`organizations` or `companies` list. The script prints the markdown table. With `--out`, it
writes the table to the file and prints `rows=<n>`.

Raw Apollo API responses can be 2,000–5,000 tokens per company. This module
applies a strict field allowlist and formats the result as a compact markdown
table (~600 tokens for 15 companies), preventing raw Apollo payloads from ever
reaching the main conversation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ALLOWED_FIELDS: list[str] = [
    "name",
    "domain",
    "industry",
    "employee_count",
    "annual_revenue",
    "headquarters_city",
    "headquarters_country",
    "linkedin_url",
    "founded_year",
    "description",
]

MAX_BATCH_SIZE: int = 10

# Markdown table column definitions: (header label, ALLOWED_FIELDS key)
_COLUMNS: list[tuple[str, str]] = [
    ("Name", "name"),
    ("Domain", "domain"),
    ("Industry", "industry"),
    ("Employees", "employee_count"),
    ("Revenue", "annual_revenue"),
    ("City", "headquarters_city"),
    ("Country", "headquarters_country"),
]


def extract_company_fields(raw_company: dict) -> dict:
    """Extract only ALLOWED_FIELDS from a raw Apollo company dict.

    Fields missing from `raw_company` are included with value ``None``.
    The returned dict has exactly the keys listed in ALLOWED_FIELDS — no
    extras, no omissions.

    Args:
        raw_company: Arbitrary dict from an Apollo API response.

    Returns:
        dict with exactly the keys in ALLOWED_FIELDS.
    """
    return {field: raw_company.get(field, None) for field in ALLOWED_FIELDS}


def format_as_markdown_table(companies: list[dict]) -> str:
    """Render a list of extracted company dicts as a markdown table.

    Only the seven display columns are rendered (Name, Domain, Industry,
    Employees, Revenue, City, Country). ``None`` values are displayed as
    ``-``.

    Args:
        companies: List of dicts already filtered through extract_company_fields.

    Returns:
        Markdown table string beginning with ``| Name |``.

    Raises:
        ValueError: If ``companies`` is empty.
    """
    if not companies:
        raise ValueError("companies must not be empty")

    headers = [col[0] for col in _COLUMNS]
    keys = [col[1] for col in _COLUMNS]

    # Header row
    header_row = "| " + " | ".join(headers) + " |"
    # Separator row
    separator_row = "| " + " | ".join("---" for _ in headers) + " |"

    rows = [header_row, separator_row]
    for company in companies:
        cells = []
        for key in keys:
            value = company.get(key)
            cells.append("-" if value is None else str(value))
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)


def process_batch(raw_companies: list[dict]) -> str:
    """Validate batch size, extract fields, and return a markdown table.

    Args:
        raw_companies: List of raw Apollo company dicts.

    Returns:
        Markdown table string.

    Raises:
        ValueError: If ``raw_companies`` is empty or exceeds MAX_BATCH_SIZE.
    """
    if not raw_companies:
        raise ValueError("raw_companies must not be empty")

    if len(raw_companies) > MAX_BATCH_SIZE:
        raise ValueError(
            f"Batch size {len(raw_companies)} exceeds MAX_BATCH_SIZE={MAX_BATCH_SIZE}. "
            "Split the input into smaller batches."
        )

    extracted = [extract_company_fields(c) for c in raw_companies]
    return format_as_markdown_table(extracted)


def load_companies(data) -> list:
    """Return the list of raw companies from the content of `apollo-raw.json`."""
    if isinstance(data, dict):
        for key in ("organizations", "companies"):
            if isinstance(data.get(key), list):
                return data[key]
    if isinstance(data, list):
        return data
    raise ValueError("the file must hold a list of companies, or an object with an 'organizations' or 'companies' list")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("input", help="path of the JSON file")
    parser.add_argument("--out", help="write the table to this file and print one line")
    args = parser.parse_args(argv)
    try:
        companies = load_companies(json.loads(Path(args.input).read_text()))
        table = process_batch(companies)
        if args.out:
            Path(args.out).write_text(table + "\n")
    except (OSError, ValueError, AttributeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"rows={len(companies)}" if args.out else table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
