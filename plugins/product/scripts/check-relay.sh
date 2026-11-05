#!/usr/bin/env bash
# product: the relay presence and version check.
#
# /product:specifying-stories Step 1 item 5 dispatches the relay `scout` agent,
# and /product:work calls `/relay:implement --spec`, which needs relay 5.0.0 or
# later. The script prints the root of the first candidate that holds the
# probe file, a readable manifest, and a version at the floor or later, then
# exits 0. It exits 1 when every candidate fails. The caller reads the exit
# code; the printed root is for the operator and for the /product:work message.
#
# scripts/check-plugin.sh holds the candidate search. This script holds the
# probe path, the version floor, and the install message.
set -uo pipefail

floor="5.0.0"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if root="$("$here/check-plugin.sh" relay commands/implement.md "$floor")"; then
  echo "$root"
  exit 0
fi

echo "the relay plugin is missing, or every install is older than $floor." >&2
echo "Install the relay plugin first, at version $floor or later." >&2
exit 1
