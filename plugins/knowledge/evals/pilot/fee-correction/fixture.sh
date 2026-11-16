#!/usr/bin/env bash
# Build only the invented graph. The case and graders stay outside the workspace.
set -euo pipefail
case_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
uv run --python 3.12 --with 'PyYAML==6.0.3' --with 'jsonschema==4.25.1' python \
  "$case_dir/../../../eval/kq_fixture.py" "$PWD"
