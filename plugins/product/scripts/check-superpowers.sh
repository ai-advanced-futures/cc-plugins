#!/usr/bin/env bash
# product: the superpowers presence check.
#
# /product:specifying-stories copies the design-doc shape and the self-review
# list of the superpowers `brainstorming` skill, so the plugin must be on
# disk. The script prints the root it found and exits 0. It exits 1 when no
# candidate holds the probe file. The caller reads the exit code.
#
# scripts/check-plugin.sh holds the candidate search. This script holds the
# probe path and the install message. The probe file rejects the other noise
# under `cache`, such as the `docs/superpowers` directories that relay vendors
# in its own installs, so the order of the hits does not matter for a presence
# test.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if root="$("$here/check-plugin.sh" superpowers skills/brainstorming/SKILL.md)"; then
  echo "$root"
  exit 0
fi

echo "the superpowers plugin is missing. Install the superpowers plugin first:" >&2
echo "  /plugin marketplace add obra/superpowers-marketplace" >&2
echo "  /plugin install superpowers" >&2
exit 1
