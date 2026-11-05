#!/usr/bin/env bash
# close-run-sessions.sh — close the acpx sessions that a run left open in its worktree.
#
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/close-run-sessions.sh" [<worktree>]
#
# Under --non-interactive no session may stay open at the end of a run (D15, spec §9.2
# item 7). The close lives in the delegate-and-watch close block (a PARKED-conditional
# trap in one Bash call at a terminal result), but the watcher node writes that block
# from the skill text, and a watcher that dies mid-loop never runs it. In the relay 5.0.0 acpx proof row the watchers did not
# write it, and 10 sessions stayed open (their driver logs have no close attempt). This
# script is the close that does not depend on the model: the run calls it once, after
# its Workflow ends.
#
# Session names do not all carry the run id (`refine-spec-round1-spec-simulator`), so
# the script selects by folder: every open session whose recorded cwd is the worktree,
# for each acpx agent. `acpx <agent> sessions list --local` prints
# `<uuid>[ [closed]] TAB <name> TAB <cwd> TAB <time>`. Both paths go through realpath,
# because a temp path can show as /private/var/... . The close uses the recorded cwd.
#
# Under --non-interactive no session is parked (Q6), so a close by folder is safe. Do
# not run two relay runs in one worktree at the same time.
#
# No CODEX_HOME here (relay 5.1.0). `sessions list` and `sessions close` read and edit the
# records under ~/.acpx and signal the queue owner, which keeps the Codex home it started
# with. In acpx 0.19.3 neither command starts the adapter.
#
# A list that fails is a failure, not "no open sessions": the sessions it could not read
# can still be open. An agent that is not set up does not fail the list: acpx 0.19.3
# prints "No sessions" and exits 0 for it.
#
# Output: one RELAY_SESSION_CLOSED=<agent>:<name> or
# RELAY_SESSION_CLOSE_FAILED=<agent>:<name> rc=<n> line per open session, one
# RELAY_SESSION_LIST_FAILED=<agent> rc=<n> line per list that failed, then
# RELAY_SESSIONS_CLOSED=<n> and RELAY_SESSIONS_FAILED=<n>. A failed list counts as one
# failure.
# Exit: 0 all closed (or none open, or no acpx), 1 a close or a list failed, 2 usage error.
set -uo pipefail

if [ "$#" -gt 1 ]; then
  echo "usage: close-run-sessions.sh [<worktree>]" >&2
  exit 2
fi
_cs_dir="${1:-}"
if [ -z "$_cs_dir" ]; then
  _cs_dir="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
if [ ! -d "$_cs_dir" ]; then
  echo "close-run-sessions.sh: not a folder: $_cs_dir" >&2
  exit 2
fi

_cs_closed=0
_cs_failed=0
if ! command -v acpx >/dev/null 2>&1; then
  echo "RELAY_SESSIONS_CLOSED=0"
  echo "RELAY_SESSIONS_FAILED=0"
  exit 0
fi

_cs_want="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$_cs_dir")"

for _cs_agent in claude codex opencode; do
  _cs_list="$(acpx "$_cs_agent" sessions list --local 2>/dev/null)"
  _cs_lrc=$?
  if [ "$_cs_lrc" -ne 0 ]; then
    echo "RELAY_SESSION_LIST_FAILED=${_cs_agent} rc=${_cs_lrc}"
    _cs_failed=$((_cs_failed + 1))
    continue
  fi
  _cs_rows="$(printf '%s\n' "$_cs_list" | python3 -c '
import os, sys
want = sys.argv[1]
for line in sys.stdin:
    cols = line.rstrip("\n").split("\t")
    if len(cols) < 3 or cols[0].endswith("[closed]"):
        continue
    if os.path.realpath(cols[2]) == want:
        print(cols[1] + "\t" + cols[2])
' "$_cs_want")"
  [ -n "$_cs_rows" ] || continue
  while IFS="$(printf '\t')" read -r _cs_name _cs_cwd; do
    [ -n "$_cs_name" ] || continue
    acpx --cwd "$_cs_cwd" "$_cs_agent" sessions close "$_cs_name" >/dev/null 2>&1
    _cs_rc=$?
    if [ "$_cs_rc" -eq 0 ]; then
      echo "RELAY_SESSION_CLOSED=${_cs_agent}:${_cs_name}"
      _cs_closed=$((_cs_closed + 1))
    else
      echo "RELAY_SESSION_CLOSE_FAILED=${_cs_agent}:${_cs_name} rc=${_cs_rc}"
      _cs_failed=$((_cs_failed + 1))
    fi
  done <<< "$_cs_rows"
done

echo "RELAY_SESSIONS_CLOSED=${_cs_closed}"
echo "RELAY_SESSIONS_FAILED=${_cs_failed}"
[ "$_cs_failed" -eq 0 ]
