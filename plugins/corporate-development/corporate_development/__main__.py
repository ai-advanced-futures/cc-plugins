"""CLI entry point for corporate-development plugin."""

import json
import sys
from corporate_development.main import run_investigation

def main():
    """CLI main function."""
    if len(sys.argv) < 2:
        print("Usage: python -m corporate_development <input_json>")
        sys.exit(1)

    try:
        input_file = sys.argv[1]
        with open(input_file) as f:
            user_input = json.load(f)

        results = run_investigation(user_input)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
