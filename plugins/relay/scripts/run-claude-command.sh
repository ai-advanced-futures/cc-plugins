#!/usr/bin/env bash
# Run one raw acpx Claude slash-command turn for /relay:implement polish leaves.
#
# Only the payload guard is here: a bare slash command. The turn itself — session
# lifecycle, exit trap, JSON stream, envelope join, fenced rc sentinel — is the
# shared `acpx-turn.sh` body, which run-claude-prompt.sh also uses.
set -uo pipefail

usage() {
  echo "usage: run-claude-command.sh <worktree> <session> <command> [timeout_seconds]" >&2
}

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  usage
  echo "POLISH_CMD_RC=64"
  exit 64
fi

worktree="$1"
session="$2"
command_text="$3"
# Same order as run-claude-prompt.sh. The verify loop names this number in its own
# status lines (`child-exceeded-acpx-timeout-<n>s`), and it reads
# `RELAY_VERIFY_TIMEOUT` first, so a helper that ignored that variable would report a
# limit its child never had.
timeout_seconds="${4:-${RELAY_VERIFY_TIMEOUT:-${RELAY_POLISH_TIMEOUT:-1800}}}"

case "$command_text" in
  /*) ;;
  *)
    echo "run-claude-command.sh: command must be a bare slash command" >&2
    echo "POLISH_CMD_RC=64"
    exit 64
    ;;
esac

# `dirname` is an external command, and the acpx-on-PATH guard inside the shared
# body must still run when PATH holds no acpx and no coreutils. Locate the sibling
# with parameter expansion only.
self_dir="${BASH_SOURCE[0]%/*}"
[ "$self_dir" = "${BASH_SOURCE[0]}" ] && self_dir="."
# shellcheck source=acpx-turn.sh
. "$self_dir/acpx-turn.sh"
run_acpx_turn run-claude-command.sh "$worktree" "$session" "$command_text" "$timeout_seconds"
