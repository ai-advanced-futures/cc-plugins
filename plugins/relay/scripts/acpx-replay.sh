#!/usr/bin/env bash
# Print what a closed acpx session did.
#
# This is the supported way to read a child's journal. Reading `.stream.ndjson` directly
# is not: 0.17.0 mixes local records into that file.
set -uo pipefail

usage() {
  echo "usage: acpx-replay.sh <session> [--cwd <dir>] [--engine claude]" >&2
}

session="${1:-}"
[ -n "$session" ] || { usage; exit 2; }
shift
cwd="$PWD"
engine="claude"
while [ "$#" -gt 0 ]; do
  # Both flags carry a value. `shift 2` on a one-element argv does not shift and does
  # not stop the loop, so a trailing flag spins here forever instead of printing usage.
  case "$1" in
    --cwd|--engine) [ "$#" -ge 2 ] || { usage; exit 2; } ;;
  esac
  case "$1" in
    --cwd)    cwd="${2:-}"; shift 2 ;;
    --engine) engine="${2:-}"; shift 2 ;;
    *) usage; exit 2 ;;
  esac
done

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
events="$work/events.ndjson"
: > "$events"

# No cursor file on disk: a replay reads the whole retained window.
out="$(bash "$here/acpx-wait.sh" --session "$session" --cwd "$cwd" --engine "$engine" \
       --cursor-file "$work/cursor" --budget "${RELAY_REPLAY_BUDGET:-60}" \
       --events-file "$events")"
result="$(printf '%s\n' "$out" | sed -nE 's/^WAIT_RESULT=(.*)$/\1/p' | tail -1)"
reason="$(printf '%s\n' "$out" | sed -nE 's/^WAIT_ERROR=(.*)$/\1/p' | tail -1)"

case "$result" in
  settled|closed) ;;
  running)
    echo "acpx-replay.sh: session $session is still open, or was made by an acpx" >&2
    echo "  older than 0.17.0, which holds no watch history. Follow it instead:" >&2
    echo "  acpx --cwd $cwd $engine sessions watch -s $session" >&2
    exit 1
    ;;
  *)
    echo "acpx-replay.sh: watch failed: ${reason:-unknown}" >&2
    exit 1
    ;;
esac

# One line per turn, then the rebuilt text of the turns. The `message` field of a
# `message` event is the raw ACP JSON-RPC message, which is what the envelope reads.
jq -r 'select(.type == "turn_result")
       | "TURN \(.requestId) \(.result.status // "unknown")"' < "$events"
jq -c 'select(.type == "message") | .message' < "$events" \
  | bash "$here/../skills/dispatching-acpx-agents/acpx-envelope.sh" --join all
