# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""One-shot script to set _YAML_SHA256_PINNED in pattern_catalogue.py.

Usage: uv run plugins/pricing/scripts/bootstrap_pattern_catalogue_hash.py

Computes the current sha256 of schemas/agentic-pricing/pattern_catalogue.yaml
and writes it into pattern_catalogue.py's _YAML_SHA256_PINNED constant. Idempotent.
"""
import hashlib
import re
import sys
from pathlib import Path


def main() -> int:
    plugin_root = Path(__file__).resolve().parents[1]
    yaml_path = plugin_root / "schemas/agentic-pricing/pattern_catalogue.yaml"
    py_path = plugin_root / "pricing/lib/pattern_catalogue.py"

    if not yaml_path.is_file():
        print(f"error: missing {yaml_path}", file=sys.stderr)
        return 2
    if not py_path.is_file():
        print(f"error: missing {py_path}", file=sys.stderr)
        return 2

    current_hash = hashlib.sha256(yaml_path.read_bytes()).hexdigest()
    py_text = py_path.read_text()

    new_text = re.sub(
        r'^_YAML_SHA256_PINNED:\s*str\s*=\s*"[0-9a-f]*"$',
        f'_YAML_SHA256_PINNED: str = "{current_hash}"',
        py_text,
        count=1,
        flags=re.MULTILINE,
    )
    if new_text == py_text:
        # Try the empty-string variant
        new_text = py_text.replace(
            '_YAML_SHA256_PINNED: str = ""',
            f'_YAML_SHA256_PINNED: str = "{current_hash}"',
        )

    if new_text == py_text:
        print("error: could not locate _YAML_SHA256_PINNED assignment in pattern_catalogue.py", file=sys.stderr)
        return 2

    py_path.write_text(new_text)
    print(f"Updated _YAML_SHA256_PINNED to {current_hash}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
