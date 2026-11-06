"""Bootstrap script — pins sha256 of Charter cost-coverage-readout.schema.json
into cost_coverage_readout.py.

Idempotent: re-running with no schema change exits cleanly with no modification.

Usage:
    cd plugins/product-finance && uv run python -m scripts.bootstrap_cost_coverage_schema_hash
    cd plugins/product-finance && uv run python -m scripts.bootstrap_cost_coverage_schema_hash \
        --confirm-audited <new-sha256-hex>
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SERIALIZER_PATH = PLUGIN_ROOT / "scripts" / "cost_coverage_readout.py"
SCHEMA_PATH = (
    PLUGIN_ROOT / "schemas" / "agentic-pricing" / "cost-coverage-readout.schema.json"
)

# Regex requires the `# noqa: E501  # bootstrap fills` suffix as a capture group.
# Absent → bootstrap silently no-ops. Do not change without updating the
# serializer's constant declaration shape.
_SHA_PATTERN = re.compile(
    r'(_SCHEMA_SHA256_PINNED: str = )"(?P<sha>[^"]*)"'
    r'(  # noqa: E501  # bootstrap fills)'
)


def _compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _current_pin(source: str) -> str:
    m = _SHA_PATTERN.search(source)
    return m.group("sha") if m else ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Pin Charter schema sha256.")
    parser.add_argument(
        "--confirm-audited",
        metavar="SHA256HEX",
        help="Required when re-pinning over a non-empty existing hash.",
    )
    args = parser.parse_args()

    new_sha = _compute_sha256(SCHEMA_PATH)
    source = SERIALIZER_PATH.read_text()
    existing = _current_pin(source)

    # Idempotency: pin already current — exit cleanly.
    if existing == new_sha and existing:
        print("[bootstrap] Pin already current — no changes needed.")
        print(f"  cost-coverage-readout.schema.json sha256: {new_sha}")
        return

    # Audit-checkpoint when re-pinning over non-empty value
    if existing and existing != new_sha:
        print("[bootstrap] cost-coverage-readout.schema.json sha256 has CHANGED.")
        print(f"  Old: {existing}")
        print(f"  New: {new_sha}")
        print(f"  Audit the diff: git log -p {SCHEMA_PATH}")
        if args.confirm_audited != new_sha:
            print(
                f"\nERROR: Re-pinning requires --confirm-audited={new_sha}\n"
                f"       Copy the NEW sha256 above and pass it as the flag value."
            )
            sys.exit(1)

    new_source = _SHA_PATTERN.sub(
        lambda m: f'{m.group(1)}"{new_sha}"{m.group(3)}', source
    )

    if new_source == source:
        print(
            "ERROR: regex substitution did not match — has the constant "
            "declaration shape changed? Verify the `# noqa: E501  # bootstrap fills`"
            " suffix is present in cost_coverage_readout.py."
        )
        sys.exit(1)

    SERIALIZER_PATH.write_text(new_source)
    print(f"[bootstrap] Pinned cost-coverage-readout.schema.json sha256: {new_sha}")
    print("Next step: uv run pytest plugins/product-finance/tests/unit/ -q")


if __name__ == "__main__":
    main()
