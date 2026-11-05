#!/usr/bin/env bash
# One raw acpx Claude turn: the shared body of run-claude-command.sh and
# run-claude-prompt.sh.
#
# This file is sourced, never executed. Each front door keeps only its usage line
# and its payload guard; everything after those guards is here once — the
# worktree and acpx-on-PATH guards, the `sessions new` record, the
# kill-then-close exit trap, the ready file, the JSON stream, the envelope join,
# and the fenced POLISH_CMD_RC sentinel.
#
# The two front doors held byte-identical copies of all of it. Every change to
# the session lifecycle then had to land twice, and one already landed in only
# one of the two copies.

# Located with parameter expansion, not `dirname`: the acpx-on-PATH guard below has
# to run when PATH holds neither acpx nor coreutils.
acpx_turn_dir="${BASH_SOURCE[0]%/*}"
[ "$acpx_turn_dir" = "${BASH_SOURCE[0]}" ] && acpx_turn_dir="."

# Set before any guard runs, so the exit trap can read them on every exit path.
session_open=0
tmp_ndjson=""
turn_pid=""
turn_worktree=""
turn_session=""

# The trap is the only close. A step killed by the node's ceiling, by the Bash tool, or
# by an operator now stops the acpx child BEFORE closing its session, instead of leaving
# the child running as an orphan under a record the trap already closed. TERM and INT
# exit through the EXIT trap so it runs on a signal too. SIGKILL is not caught.
acpx_turn_cleanup() {
  if [ -n "${turn_pid:-}" ] && kill -0 "$turn_pid" 2>/dev/null; then
    kill -TERM "$turn_pid" 2>/dev/null || true
    sleep 2
    if kill -0 "$turn_pid" 2>/dev/null; then kill -KILL "$turn_pid" 2>/dev/null || true; fi
  fi
  if [ "$session_open" = "1" ]; then
    session_open=0
    acpx --cwd "$turn_worktree" claude sessions close "$turn_session" >/dev/null 2>&1 || true
  fi
  [ -n "${tmp_ndjson:-}" ] && rm -f "$tmp_ndjson"
  return 0
}

# usage: run_acpx_turn <self_name> <worktree> <session> <payload> <timeout_seconds>
#
# `self_name` is only the prefix on the error lines, so each front door keeps its
# own name in its own diagnostics. Exits with the turn's rc; never returns on the
# guard paths.
run_acpx_turn() {
  local self="$1" payload="$4" timeout_seconds="$5"
  turn_worktree="$2"
  turn_session="$3"

  if [ ! -d "$turn_worktree" ]; then
    echo "$self: worktree not found: $turn_worktree" >&2
    echo "POLISH_CMD_RC=66"
    exit 66
  fi

  # 69 (EX_UNAVAILABLE), not 127: acpx itself exits 127 when it cannot spawn the adapter, so
  # passing 127 through would make "acpx missing" byte-identical to a genuine spawn failure.
  if ! command -v acpx >/dev/null 2>&1; then
    echo "$self: acpx not found on PATH" >&2
    echo "POLISH_CMD_RC=69"
    exit 69
  fi

  # `new` looks up at the exact directory, soft-closes a same-name record there, and
  # creates a fresh one. It never walks up to the main checkout. `ensure` would resume a
  # record a killed earlier run of the same round left open, and every step of the verify
  # loop is one turn, so nothing needs the old conversation.
  local new_out new_rc
  new_out="$(acpx --cwd "$turn_worktree" claude sessions new --name "$turn_session" 2>&1)"
  new_rc=$?
  if [ "$new_rc" -ne 0 ]; then
    [ -n "$new_out" ] && printf '%s\n' "$new_out"
    printf 'POLISH_CMD_RC=%s\n' "$new_rc"
    exit "$new_rc"
  fi
  session_open=1

  trap acpx_turn_cleanup EXIT
  trap 'exit 143' TERM
  trap 'exit 130' INT

  # The verify node waits on this file to learn the session exists before it starts
  # polling. Standalone callers leave the variable unset.
  if [ -n "${RELAY_HELPER_READY_FILE:-}" ]; then
    : > "$RELAY_HELPER_READY_FILE"
  fi

  # The raw stream is kept where the caller asked, so a round keeps it for forensics.
  local ndjson="${RELAY_HELPER_NDJSON:-}"
  if [ -z "$ndjson" ]; then
    tmp_ndjson="$(mktemp)"
    ndjson="$tmp_ndjson"
  fi

  # "$payload" is one quoted argv element and never passes through eval. A slash command
  # or a /verify report can hold backticks, quotes, and shell metacharacters;
  # word-splitting it would send a truncated payload while still returning rc 0.
  local turn_rc
  acpx --format json --json-strict --approve-all --cwd "$turn_worktree" \
       --timeout "$timeout_seconds" claude -s "$turn_session" "$payload" > "$ndjson" 2>&1 &
  turn_pid=$!
  wait "$turn_pid"
  turn_rc=$?
  turn_pid=""

  # --join all, because this helper has no first-line sentinel: a /verify child may put
  # its verdict in one message and end with a short closing message. --errors carries a
  # failed turn's reason into the round record. After 0.19.0 a failed turn can still print
  # partial text, so the text alone never proves success — only turn_rc does.
  local turn_out
  turn_out="$("$acpx_turn_dir/../skills/dispatching-acpx-agents/acpx-envelope.sh" \
              --join all --errors < "$ndjson")"

  # The child's reply is fenced so the rc sentinel cannot be forged from inside it. The
  # child runs /simplify, /code-review, or a fix prompt built from a /verify report over a
  # repo that may itself contain the literal string `POLISH_CMD_RC=` (these files do), and
  # an unfenced reply would let the child's own text be read as this helper's exit status.
  # Only the line after POLISH_CMD_OUTPUT_END counts.
  if [ -n "$turn_out" ]; then
    printf 'POLISH_CMD_OUTPUT_BEGIN\n'
    printf '%s\n' "$turn_out"
    printf 'POLISH_CMD_OUTPUT_END\n'
  fi
  printf 'POLISH_CMD_RC=%s\n' "$turn_rc"
  exit "$turn_rc"
}
