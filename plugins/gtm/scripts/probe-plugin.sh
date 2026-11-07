#!/usr/bin/env bash
# probe-plugin.sh: find the root of a plugin that this plugin calls.
#
# Usage: probe-plugin.sh <name> <probe-path>
#
# Prints the root of the first candidate that holds <probe-path> and whose
# .claude-plugin/plugin.json names <name>, then exits 0. Exits 1 with no
# output when no candidate passes: the caller owns the message.
#
# The order: the sibling folder of this plugin (<own root>/../<name>), so a
# --plugin-dir run and a pytest run find the plugin; the <name>-runtime skill
# of a skills install; the project install; the
# home install; then the plugin cache, the highest version first.
#
# The same file ships in knowledge, system-design, architecture, business-domain, and product. Change
# all five copies together. A knowledge test keeps them identical.
set -uo pipefail

name="${1:?a plugin name is required}"
probe="${2:?a probe path is required}"
own_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

name_of() {
  python3 -c '
import json, sys
try:
    print(json.load(open(sys.argv[1]))["name"])
except Exception:
    pass
' "$1/.claude-plugin/plugin.json" 2>/dev/null
}

try() {
  local candidate="$1"
  [ -f "$candidate/$probe" ] || return 1
  [ "$(name_of "$candidate")" = "$name" ] || return 1
  (cd "$candidate" && pwd -P)
  exit 0
}

try "$(cd "$own_root/.." && pwd -P)/$name"
# A skills install (D33): <name>-runtime is a sibling of this runtime skill,
# and in this repository it is in skills/<name>/.
try "$(cd "$own_root/.." && pwd -P)/$name-runtime"
try "$(cd "$own_root/../.." && pwd -P)/$name/$name-runtime"
try "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/plugins/$name"
try "$HOME/.claude/plugins/$name"

while IFS= read -r cache; do
  [ -z "$cache" ] && continue
  try "$cache"
  while IFS= read -r vdir; do
    [ -z "$vdir" ] && continue
    try "${vdir%/}"
  done <<< "$(ls -d "$cache"/*/ 2>/dev/null | sort -rV)"
done <<< "$(find "$HOME/.claude/plugins/cache" -maxdepth 6 -type d -name "$name" 2>/dev/null)"

exit 1
