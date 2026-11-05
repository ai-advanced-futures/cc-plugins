#!/usr/bin/env bash
# Write schema/system-design.schema.json and schema/system-design.slots.json
# from schema/system-design.yaml, which imports the knowledge base schema.
#
#     bash plugins/system-design/scripts/gen-schema.sh [output root]
#
# Development only. A test gives a temporary folder and compares the bytes.
# Exit 2 when gen-json-schema is absent, when requirements-dev.txt has no
# linkml pin, or when the generator does not use the pinned packages.
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_root="${1:-$plugin_root}"
source_file="$plugin_root/schema/system-design.yaml"
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
schema_tmp="$(mktemp)"
slots_tmp="$(mktemp)"
trap 'rm -f "$schema_tmp" "$slots_tmp"' EXIT
gen-json-schema --closed "$source_file" > "$schema_tmp"
python3 "$plugin_root/scripts/gen_slots.py" "$source_file" > "$slots_tmp"
mkdir -p "$out_root/schema"
chmod 644 "$schema_tmp" "$slots_tmp"
mv "$schema_tmp" "$out_root/schema/system-design.schema.json"
mv "$slots_tmp" "$out_root/schema/system-design.slots.json"
trap - EXIT
echo "Wrote $out_root/schema/system-design.schema.json"
echo "Wrote $out_root/schema/system-design.slots.json"
