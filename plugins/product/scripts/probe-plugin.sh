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
# of a skills install; the home install; the marketplace folder of this plugin
# in the plugin cache; then all of the plugin cache, the highest version first.
# The home install and the cache are in the Claude config folder:
# $CLAUDE_CONFIG_DIR when it is set and not empty, else $HOME/.claude (STORY-281).
# It never tries a folder of the project, because Claude Code installs no plugin
# there, and a project can hold files that the person did not write (STORY-202).
# It exits 1 with 1 line on stderr and no stdout when the name is not a-z, 0-9
# and - (a letter or a digit first), or the probe path is absolute or has an
# empty, . or .. part.
#
# The same file ships in architecture, architecture-assess, business-case,
# business-domain, competitive-intelligence, gtm, jtbd-market-discovery,
# knowledge, pricing, product, product-finance, and system-design. Change the 12 copies together.
# A knowledge test keeps them identical.
set -uo pipefail

name="${1:?a plugin name is required}"
probe="${2:?a probe path is required}"
bad() { printf 'probe-plugin.sh: the %s is not valid: %s\n' "$1" "$2" >&2; exit 1; }
[[ "$name" =~ ^[a-z0-9][a-z0-9-]*$ ]] || bad "plugin name" "$name"
[[ "$probe" =~ ^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$ ]] || bad "probe path" "$probe"
case "/$probe/" in */./*|*/../*) bad "probe path" "$probe" ;; esac
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
# A relative config folder would name a folder of the current project
# (STORY-202), so it gives no candidate.
config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
case "$config_dir" in /*) ;; *) exit 1 ;; esac
plugins_dir="$config_dir/plugins"
try "$plugins_dir/$name"

# The marketplace folder of this plugin comes first in the cache: own_root is
# cache/<marketplace>/<plugin>/<version> for a plugin in the cache.
cache_root="$(cd "$plugins_dir/cache" 2>/dev/null && pwd -P)"
own_market="$(dirname "$(dirname "$own_root")")"
if [ -n "$cache_root" ] && [ "$(dirname "$own_market")" = "$cache_root" ]; then
  while IFS= read -r vdir; do
    [ -z "$vdir" ] && continue
    try "${vdir%/}"
  done <<< "$(ls -d "$own_market/$name"/*/ 2>/dev/null | sort -rV)"
fi

while IFS= read -r cache; do
  [ -z "$cache" ] && continue
  try "$cache"
  while IFS= read -r vdir; do
    [ -z "$vdir" ] && continue
    try "${vdir%/}"
  done <<< "$(ls -d "$cache"/*/ 2>/dev/null | sort -rV)"
done <<< "$(find "$plugins_dir/cache" -maxdepth 6 -type d -name "$name" 2>/dev/null)"

exit 1
