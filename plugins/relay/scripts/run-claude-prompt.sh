#!/usr/bin/env bash
# Run one raw acpx Claude free-form-prompt turn for /relay:verify's fix step.
#
# Free-form sibling of run-claude-command.sh: both call the same `acpx-turn.sh`
# body, so they share the session lifecycle, the POLISH_CMD_OUTPUT_BEGIN/END
# fencing, and the rc semantics (64/66/69). The difference is the payload guard
# below: this helper accepts arbitrary prompt text instead of requiring a leading
# `/`, because the fix step sends a report body built from a /verify reply, not a
# slash command.
set -uo pipefail

usage() {
  echo "usage: run-claude-prompt.sh <worktree> <session> <prompt> [timeout_seconds]" >&2
}

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  usage
  echo "POLISH_CMD_RC=64"
  exit 64
fi

worktree="$1"
session="$2"
prompt="$3"
timeout_seconds="${4:-${RELAY_VERIFY_TIMEOUT:-${RELAY_POLISH_TIMEOUT:-1800}}}"

# An empty (or whitespace-only) prompt starts a child turn with nothing to do.
# That turn returns rc 0, which reads as a success report with no work behind
# it. Reject it here instead of letting a silent no-op look like a pass.
# No slash-prefix guard: a free-form prompt may legitimately start with `/`
# (a file path), so that check does not belong in this helper.
# A bash builtin regex test is used instead of `tr`/`sed`, so this guard has
# no external-command dependency to fail before the acpx-on-PATH check runs.
if [[ ! "$prompt" =~ [^[:space:]] ]]; then
  echo "run-claude-prompt.sh: prompt must not be empty" >&2
  echo "POLISH_CMD_RC=64"
  exit 64
fi

# `dirname` is an external command, and the acpx-on-PATH guard inside the shared
# body must still run when PATH holds no acpx and no coreutils. Locate the sibling
# with parameter expansion only.
self_dir="${BASH_SOURCE[0]%/*}"
[ "$self_dir" = "${BASH_SOURCE[0]}" ] && self_dir="."
# shellcheck source=acpx-turn.sh
. "$self_dir/acpx-turn.sh"
run_acpx_turn run-claude-prompt.sh "$worktree" "$session" "$prompt" "$timeout_seconds"
