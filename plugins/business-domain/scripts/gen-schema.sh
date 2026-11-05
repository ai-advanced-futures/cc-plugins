#!/usr/bin/env bash
# Write the two generated files from schema/domain.yaml:
# schema/domain.schema.json and schema/domain.slots.json.
#
#     bash plugins/business-domain/scripts/gen-schema.sh [output root]
#
# Development only. ddd.py reads the two outputs and never the LinkML source.
# The output root defaults to the plugin root. A test gives a temporary
# directory, compares the bytes with the committed files, and writes nothing
# into the tree.
#
# Exit 2 when gen-json-schema is absent, when requirements-dev.txt has no
# linkml pin, or when the generator does not use the pinned packages.
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_root="${1:-$plugin_root}"
source_file="$plugin_root/schema/domain.yaml"

# The exact version that wrote the committed file, read from the one file
# that holds the pin. The CI workflow installs that same file.
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

# Each output goes to a temporary file first. A redirection into the
# committed file truncates it before the generator runs, so a failed run
# would leave an empty schema in the tree.
schema_tmp="$(mktemp)"
slots_tmp="$(mktemp)"
trap 'rm -f "$schema_tmp" "$slots_tmp"' EXIT

# --closed makes each class reject a key that the schema does not declare.
# That is what gives rule E2 an unknown-key finding.
gen-json-schema --closed "$source_file" > "$schema_tmp"
python3 "$plugin_root/scripts/gen_slots.py" "$source_file" > "$slots_tmp"

mkdir -p "$out_root/schema"
chmod 644 "$schema_tmp" "$slots_tmp"
mv "$schema_tmp" "$out_root/schema/domain.schema.json"
mv "$slots_tmp" "$out_root/schema/domain.slots.json"
trap - EXIT
echo "Wrote $out_root/schema/domain.schema.json"
echo "Wrote $out_root/schema/domain.slots.json"
