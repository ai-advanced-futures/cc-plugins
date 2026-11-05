#!/usr/bin/env bash
# Write the two generated files from schema/adr.yaml:
# templates/verbatim/schemas/adr.schema.json and schema/adr.slots.json.
#
#     bash plugins/architecture/scripts/gen-schema.sh [output root]
#
# Development only. No runtime script runs this file, and no vendored script
# reads the LinkML source. The output root defaults to the plugin root. A test
# gives a temporary directory, compares the bytes with the committed files, and
# writes nothing into the tree.
#
# Exit 2 when uvx is absent, or when requirements-dev.txt has no linkml pin.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_ROOT="${1:-$PLUGIN_ROOT}"
SOURCE="$PLUGIN_ROOT/schema/adr.yaml"
REQUIREMENTS="$PLUGIN_ROOT/requirements-dev.txt"

if ! command -v uvx > /dev/null 2>&1; then
  echo "ERROR: uvx is not installed; install uv first" >&2
  exit 2
fi

PIN="$(grep -E '^linkml==' "$REQUIREMENTS" 2> /dev/null | head -n 1 || true)"
if [ -z "$PIN" ]; then
  echo "ERROR: $REQUIREMENTS has no linkml== pin" >&2
  exit 2
fi

# Every generated file is written to a temporary file first and moved into
# place only after its generator succeeded. A plain `>` on the target would
# truncate the committed file before the generator ran, so a failed build
# would leave an empty schema in the tree.
RAW="$(mktemp "${TMPDIR:-/tmp}/adr-raw-schema.XXXXXX")"
STAGED_SCHEMA="$(mktemp "${TMPDIR:-/tmp}/adr-schema.XXXXXX")"
STAGED_SLOTS="$(mktemp "${TMPDIR:-/tmp}/adr-slots.XXXXXX")"
trap 'rm -f "$RAW" "$STAGED_SCHEMA" "$STAGED_SLOTS"' EXIT

# --closed changes only the top-level additionalProperties. --top-class is not
# used: `tree_root: true` in the source gives the same bytes.
mkdir -p "$OUT_ROOT/templates/verbatim/schemas"
uvx --from "$PIN" gen-json-schema --closed "$SOURCE" > "$RAW"
python3 "$PLUGIN_ROOT/scripts/flatten_schema.py" "$RAW" > "$STAGED_SCHEMA"
mv "$STAGED_SCHEMA" "$OUT_ROOT/templates/verbatim/schemas/adr.schema.json"
echo "wrote $OUT_ROOT/templates/verbatim/schemas/adr.schema.json"

# The annotations do not reach the JSON Schema, so read them from the source
# with the LinkML API. `properties` in the JSON Schema is alphabetical, so the
# key order comes from the class slot list.
mkdir -p "$OUT_ROOT/schema"
uvx --from "$PIN" python - "$SOURCE" > "$STAGED_SLOTS" <<'PYTHON'
import json
import sys

from linkml_runtime.utils.schemaview import SchemaView

view = SchemaView(sys.argv[1])
adr = view.get_class("Adr")


def multivalued(slot):
    if slot.multivalued:
        return True
    return any(option.multivalued for option in (slot.any_of or []))


def annotation(slot, name):
    item = slot.annotations.get(name)
    return None if item is None else item.value


slots = {}
for name in adr.slots:
    slot = view.get_slot(name)
    stored = annotation(slot, "stored_inverse")
    kind = annotation(slot, "target_kind")
    order = annotation(slot, "walk_order")
    slots[name] = {
        "multivalued": bool(multivalued(slot)),
        "inlined": bool(slot.inlined),
        "inverse": str(slot.inverse) if slot.inverse else None,
        "stored_inverse": None if stored is None else bool(stored),
        "target_kind": None if kind is None else str(kind),
        "walk_order": None if order is None else int(order),
    }

json.dump({
    "key_order": [str(name) for name in adr.slots],
    "statuses": [str(name) for name in view.get_enum("OkfStatus").permissible_values],
    "lifecycles": [str(name) for name in view.get_enum("AdrLifecycle").permissible_values],
    "model_statuses": [str(name) for name in view.get_enum("ModelStatus").permissible_values],
    "slots": slots,
}, sys.stdout, indent=2)
sys.stdout.write("\n")
PYTHON
mv "$STAGED_SLOTS" "$OUT_ROOT/schema/adr.slots.json"
echo "wrote $OUT_ROOT/schema/adr.slots.json"
