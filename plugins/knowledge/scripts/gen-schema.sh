#!/usr/bin/env bash
# Write schema/knowledge.schema.json from schema/knowledge.yaml, which
# imports schema/base.yaml.
#
#     bash plugins/knowledge/scripts/gen-schema.sh [output root]
#
# Development only. knowledge_graph.py reads the output and never the LinkML
# source. The output root defaults to the plugin root. A test gives a
# temporary folder and compares the bytes with the committed file.
#
# Exit 2 when gen-json-schema is absent, when requirements-dev.txt has no
# linkml pin, or when the generator does not use the pinned packages.
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_root="${1:-$plugin_root}"
requirements="$plugin_root/requirements-dev.txt"
LINKML_VERSION="$(sed -n 's/^linkml==\(.*\)$/\1/p' "$requirements")"
if [ -z "$LINKML_VERSION" ]; then
  echo "$requirements holds no 'linkml==' pin. Add the pin back first." >&2
  exit 2
fi
if ! command -v gen-json-schema >/dev/null 2>&1; then
  echo "gen-json-schema is missing. Run: pip install -r $requirements" >&2
  exit 2
fi

# Every exact pin must match the package that the generator imports. A
# generator with a different linkml-runtime writes a different
# metamodel_version, and CI then rejects the committed file. The packages
# that count are those of the interpreter on the first line of gen-json-schema.
python="$(sed -n '1s/^#!//p' "$(command -v gen-json-schema)")"
# $python stays unquoted: a "/usr/bin/env python3" line is two words.
# shellcheck disable=SC2086
mismatch="$($python - "$requirements" <<'EOF'
import importlib.metadata
import re
import sys

for line in open(sys.argv[1]):
    pin = re.match(r"^([A-Za-z0-9_.-]+)==(\S+)$", line.strip())
    if not pin:
        continue
    name, wanted = pin.groups()
    try:
        installed = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        installed = "missing"
    if installed != wanted:
        print(f"  {name}: installed {installed}, pinned {wanted}")
EOF
)"
if [ -n "$mismatch" ]; then
  echo "The generator does not use the pinned packages:" >&2
  echo "$mismatch" >&2
  echo "Run: pip install -r $requirements" >&2
  exit 2
fi

# The output goes to a temporary file first, so a failed run never leaves an
# empty schema in the tree. --closed makes each class refuse an unknown key.
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
gen-json-schema --closed "$plugin_root/schema/knowledge.yaml" > "$tmp"
mkdir -p "$out_root/schema"
chmod 644 "$tmp"
mv "$tmp" "$out_root/schema/knowledge.schema.json"
trap - EXIT
echo "Wrote $out_root/schema/knowledge.schema.json"
