#!/usr/bin/env bash
# product: find an installed plugin root.
#
# Usage: check-plugin.sh <name> <probe-path> [version-floor]
#
# Prints the root of the first candidate that holds the probe file, whose
# .claude-plugin/plugin.json names the plugin and, with a floor given, has a
# version at the floor or later, then exits 0. It exits 1 when every candidate
# fails, and prints no message: the caller owns the install text, because the
# install command differs per plugin.
#
# The home root and the cache are in the Claude config folder: $CLAUDE_CONFIG_DIR
# when it is set and not empty, else $HOME/.claude (STORY-295, the rule of
# STORY-281). A relative value would name a folder of the current project, so it
# gives no candidate and the script exits 1.
#
# The candidate order is the home root first, and then the cache sweep hits
# with their version directories, the highest version first. It never tries a
# folder of the project, because Claude Code installs no plugin there, and a
# project can hold files that the person did not write (STORY-202). A home root
# that passes ends the search before the sweep runs, so the common case costs a
# few stat calls instead of a walk of the whole cache. The sweep is rooted at `cache`,
# because $HOME/.claude/plugins/marketplaces/ holds source checkouts and not
# installs.
set -uo pipefail

name="${1:?a plugin name is required}"
probe="${2:?a probe path is required}"
floor="${3:-}"

# One field of the manifest of a root, or an empty line when the manifest is
# absent or does not parse. plugins/relay/scripts/record-run-intent.sh reads a
# plugin manifest the same way.
field_of() {
  python3 -c '
import json, sys
try:
    print(json.load(open(sys.argv[1]))[sys.argv[2]])
except Exception:
    pass
' "$1/.claude-plugin/plugin.json" "$2" 2>/dev/null
}

# A candidate passes the probe, the name test, and, with a floor set, the
# manifest read and the floor test. `sort -V` puts the lower version first, so
# the floor passes when it sorts first or is equal.
accepts() {
  local candidate="$1" version
  test -f "$candidate/$probe" || return 1
  [ "$(field_of "$candidate" name)" = "$name" ] || return 1
  [ -n "$floor" ] || return 0
  version="$(field_of "$candidate" version)"
  [ -n "$version" ] || return 1
  [ "$(printf '%s\n%s\n' "$floor" "$version" | sort -V | head -n 1)" = "$floor" ]
}

# Print the root and end the script when this candidate passes. The here-string
# loops below run in this shell, so the exit reaches the caller from inside one.
try() {
  if accepts "$1"; then
    echo "$1"
    exit 0
  fi
}

config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
case "$config_dir" in /*) ;; *) exit 1 ;; esac
plugins_dir="$config_dir/plugins"

try "$plugins_dir/$name"

while IFS= read -r cache; do
  [ -z "$cache" ] && continue
  # The flat layout first, then each version directory of the same hit.
  try "$cache"
  while IFS= read -r vdir; do
    [ -z "$vdir" ] && continue
    try "${vdir%/}"
  done <<< "$(ls -d "$cache"/*/ 2>/dev/null | sort -rV)"
done <<< "$(find "$plugins_dir/cache" -maxdepth 6 -type d \
                 -name "$name" 2>/dev/null)"

exit 1
