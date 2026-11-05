#!/usr/bin/env bash
# Regenerates schema/product.schema.json from schema/product.yaml.
#
# The generated file is in git on purpose: prd.py validates page frontmatter
# with jsonschema at run time, so the LinkML tools stay a build-time
# dependency. tests/test_schema_generated.py fails when the two disagree.
set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The exact version that wrote the committed file, read from the one file
# that holds the pin. The CI workflow installs that same file.
requirements="$plugin_root/requirements-dev.txt"
LINKML_VERSION="$(sed -n 's/^linkml==\(.*\)$/\1/p' "$requirements")"
if [ -z "$LINKML_VERSION" ]; then
  echo "$requirements holds no 'linkml==' pin, so the generator version is" >&2
  echo "unknown. Add the pin back before you regenerate the schema." >&2
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

# --closed makes each generated class reject a key the schema does not
# declare, which is what gives rule E2 an unknown-key finding.
#
# The output goes to a temporary file first. A redirection into the committed
# file truncates it before the generator runs, so a generator that fails part
# way leaves an empty or half-written schema in the working tree, and every
# subcommand that validates a page then exits 2.
temporary="$(mktemp)"
trap 'rm -f "$temporary"' EXIT
gen-json-schema --closed "$plugin_root/schema/product.yaml" > "$temporary"
# mktemp gives 0600. The committed schema is a readable file, so say so.
chmod 644 "$temporary"
mv "$temporary" "$plugin_root/schema/product.schema.json"
trap - EXIT
echo "Wrote $plugin_root/schema/product.schema.json"
