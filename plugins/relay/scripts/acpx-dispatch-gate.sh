#!/usr/bin/env bash
# acpx-dispatch-gate.sh — the delegate-and-watch sidecar gate (relay 5.1.0).
#
#   bash acpx-dispatch-gate.sh <sidecar> <dispatch output file> [<budget seconds>]
#
# Run right after the backgrounded launch of acpx-dispatch.sh, before any `source` or
# wait. The launch runs `rm -f <sidecar>` first and ends its output with a
# RELAY_DISPATCH_EXIT=<rc> line. The dispatcher refuses some dispatches before it writes
# the sidecar; a refused Codex home also prints one JSON line with
# "status":"engine_error". The dispatcher moves a complete sidecar into place, so a
# sidecar that exists is complete.
#
# Waits (1 s poll, bounded by the budget, default 540) until the sidecar exists or the
# end line appears, then prints the route:
#   GATE=sidecar                                         exit 0: source it and wait
#   GATE=errored / ERRORED_REASON=<error> / ERRORED_DETAIL=<output>
#                                                        exit 1: an engine_error line
#   GATE=errored / ERRORED_REASON=dispatch_no_sidecar / ERRORED_DETAIL=<tail line>...
#                                                        exit 1: any other end, or budget spent
# Exit 2: usage error.
set -uo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "usage: acpx-dispatch-gate.sh <sidecar> <dispatch output file> [<budget seconds>]" >&2
  exit 2
fi
sidecar="$1"
out="$2"
budget="${3:-540}"
case "$budget" in ''|*[!0-9]*) echo "acpx-dispatch-gate.sh: budget must be a whole number of seconds" >&2; exit 2 ;; esac

SECONDS=0
until [ -f "$sidecar" ] || grep -q '^RELAY_DISPATCH_EXIT=' "$out" 2>/dev/null \
   || [ "$SECONDS" -ge "$budget" ]; do
  sleep 1
done

if [ -f "$sidecar" ]; then
  echo "GATE=sidecar"
  exit 0
fi

echo "GATE=errored"
refusal="$(grep '^{' "$out" 2>/dev/null | grep '"status":"engine_error"' | tail -n 1)"
if [ -n "$refusal" ]; then
  printf 'ERRORED_REASON=%s\n' "$(printf '%s' "$refusal" | jq -r '.error // "engine_error"')"
  printf 'ERRORED_DETAIL=%s\n' "$(printf '%s' "$refusal" | jq -r '.output // ""' | tr '\n' ' ')"
else
  echo "ERRORED_REASON=dispatch_no_sidecar"
  tail -n 5 "$out" 2>/dev/null | sed 's/^/ERRORED_DETAIL=/'
fi
exit 1
