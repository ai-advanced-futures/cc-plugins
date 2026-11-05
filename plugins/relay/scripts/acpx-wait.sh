#!/usr/bin/env bash
# Bounded reader for `acpx <engine> sessions watch`.
#
# One implementation for every relay caller: the delegate-and-watch watcher and the
# verify loop's `watch` phase. acpx's own --timeout does not bound a watch, and this Mac
# has no `timeout` binary, so the bound is the shell's SECONDS counter plus a kill at the
# end. The watch is passive: it starts no agent and does not touch the running turn, so
# ending it changes nothing.
#
# This script assumes bash 3.2 (macOS's system `/bin/bash`), where `read -t` returns 1 on
# both a timeout and end of stream. The two are never told apart by `read`'s status
# number; the loop below asks whether the watch process is still alive instead. [inferred]
#
# Cursor rule: the first wait on a fresh session has no cursor, and a session's retained
# window holds only its own events, so the previous turn's `turn_result` can never settle
# a new wait. A caller that reuses a session across turns keeps the cursor file for the
# life of the session; a caller that starts a fresh session starts with no cursor file.
set -uo pipefail

usage() {
  cat >&2 <<'USAGE'
usage: acpx-wait.sh --session <name> --cwd <dir> --cursor-file <path> --budget <seconds>
                    [--engine claude] [--events-file <path>]

Exit map:
  0   WAIT_RESULT=settled  a turn_result arrived (WAIT_TURN_STATUS=completed|cancelled|failed)
  0   WAIT_RESULT=closed   the watch ended by itself with no result
  75  WAIT_RESULT=running  the budget ran out with no result
  1   WAIT_RESULT=error    acpx reported an error (WAIT_ERROR=<reason>)
  2   usage error
USAGE
}

session=""; cwd=""; cursor_file=""; budget="540"; engine="claude"; events_file=""
while [ "$#" -gt 0 ]; do
  # Every flag this script takes carries a value. `shift 2` on a one-element argv does
  # not shift and does not stop the loop, so a trailing flag spins here forever instead
  # of printing the usage line. Refuse it before the arm runs.
  case "$1" in
    --session|--cwd|--cursor-file|--budget|--engine|--events-file)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      ;;
  esac
  case "$1" in
    --session)     session="${2:-}"; shift 2 ;;
    --cwd)         cwd="${2:-}"; shift 2 ;;
    --cursor-file) cursor_file="${2:-}"; shift 2 ;;
    --budget)      budget="${2:-}"; shift 2 ;;
    --engine)      engine="${2:-}"; shift 2 ;;
    --events-file) events_file="${2:-}"; shift 2 ;;
    *) usage; exit 2 ;;
  esac
done
if [ -z "$session" ] || [ -z "$cwd" ] || [ -z "$cursor_file" ]; then usage; exit 2; fi
case "$budget" in ''|*[!0-9]*) usage; exit 2 ;; esac
# Force base 10: bash reads a leading zero as octal, and 0900 is not legal octal.
budget=$(( 10#$budget ))

# 75 is EX_TEMPFAIL, and deliberately not 3: acpx uses 3 for its own timeout, and the
# verify node maps a helper rc of 3 to the child-timeout bucket.
EXIT_RUNNING=75

cursor=""
if [ -s "$cursor_file" ]; then cursor="$(tr -d '[:space:]' < "$cursor_file")"; fi

pipe_dir="$(mktemp -d)"
pipe="$pipe_dir/events"
mkfifo "$pipe"
watch_pid=""
cleanup() {
  if [ -n "$watch_pid" ] && kill -0 "$watch_pid" 2>/dev/null; then
    kill -TERM "$watch_pid" 2>/dev/null || true
    sleep 2
    if kill -0 "$watch_pid" 2>/dev/null; then kill -KILL "$watch_pid" 2>/dev/null || true; fi
  fi
  rm -rf "$pipe_dir"
}
trap cleanup EXIT

set -- --format json --json-strict --cwd "$cwd" "$engine" sessions watch -s "$session"
[ -n "$cursor" ] && set -- "$@" --cursor "$cursor"
acpx "$@" > "$pipe" 2>"$pipe_dir/stderr" &
watch_pid=$!
exec 3< "$pipe"

# One reason from a closed set, never the raw code, so callers match a closed set. The
# seven WATCH_* detail codes are acpx's own (dist/watch-Cz6jbrRs.js:6, :10;
# dist/ipc-DAApJ5mi.js:671-685, :1007-1008).
classify_reason() {
  local detail="$1" code="$2" msg="$3"
  case "$detail" in
    WATCH_OUTCOME_UNKNOWN)   echo outcome_unknown; return 0 ;;
    WATCH_OWNER_UNSUPPORTED) echo owner_unsupported; return 0 ;;
    WATCH_CURSOR_INVALID)    echo cursor_invalid; return 0 ;;
    WATCH_CURSOR_FOREIGN)    echo cursor_foreign; return 0 ;;
    WATCH_CURSOR_FUTURE)     echo cursor_future; return 0 ;;
    WATCH_CURSOR_EXPIRED)    echo cursor_expired; return 0 ;;
    WATCH_JOURNAL_CORRUPT)   echo journal_corrupt; return 0 ;;
  esac
  case "$msg" in *"No named session"*) echo no_session; return 0 ;; esac
  if [ -n "$code" ]; then printf '%s\n' "$code" | tr '[:upper:]' '[:lower:]'; return 0; fi
  echo unknown
}

# Through a temp file and mv, so a killed reader never leaves a half-written cursor.
save_cursor() {
  printf '%s\n' "$1" > "$cursor_file.tmp" && mv -f "$cursor_file.tmp" "$cursor_file"
}

json_field() { printf '%s' "$1" | jq -r "$2" 2>/dev/null; }

SECONDS=0
events=0
last_event=0
outcome="running"
turn_status=""
error_reason=""

# One event line. The main loop and the end-of-stream drain both call it, so a line is
# handled the same way wherever it is read. Returns 0 to keep reading, and 1 when the
# line ended the wait; `outcome` is then `settled` or `error`.
handle_line() {
  local line="$1" ev_cursor
  [ -z "$line" ] && return 0
  # A line that is not JSON is skipped. The strict JSON mode emits none; this is defensive.
  printf '%s' "$line" | jq -e . >/dev/null 2>&1 || return 0
  events=$((events + 1))
  last_event=$SECONDS
  [ -n "$events_file" ] && printf '%s\n' "$line" >> "$events_file"
  ev_cursor="$(json_field "$line" '.cursor // ""')"
  [ -n "$ev_cursor" ] && { cursor="$ev_cursor"; save_cursor "$cursor"; }
  if [ "$(json_field "$line" 'if .error then "1" else "" end')" = "1" ]; then
    error_reason="$(classify_reason \
      "$(json_field "$line" '.error.data.detailCode // ""')" \
      "$(json_field "$line" '.error.data.acpxCode // ""')" \
      "$(json_field "$line" '.error.message // ""')")"
    # A rejected cursor poisons every later wait on the same session: the cursor is on
    # disk, so the next call sends the same value and is rejected the same way, with no
    # event ever read. Drop it here, so the next call restarts from the retained window.
    case "$error_reason" in
      cursor_invalid|cursor_foreign|cursor_future|cursor_expired)
        rm -f "$cursor_file" "$cursor_file.tmp" 2>/dev/null || true
        cursor=""
        ;;
    esac
    outcome="error"
    return 1
  fi
  if [ "$(json_field "$line" '.type // ""')" = "turn_result" ]; then
    turn_status="$(json_field "$line" '.result.status // "unknown"')"
    outcome="settled"
    return 1
  fi
  return 0
}

# `read -t 5` wakes the loop at least every five seconds, so the budget is checked even
# when the stream is silent.
while :; do
  if [ "$SECONDS" -ge "$budget" ]; then outcome="running"; break; fi
  # `read`'s own status is captured here, on the line right after the call: wrapping the
  # read in `if … ; then … fi` and reading `$?` after the `fi` gives the `if` compound's
  # own status (0, when the condition failed and no branch ran), never read's. [inferred]
  IFS= read -r -t 5 line <&3
  rc=$?
  if [ "$rc" -eq 0 ]; then
    handle_line "$line" || break
    continue
  fi
  # On bash 3.2 `read -t` returns 1 on both a timeout and end of stream, so the two are
  # told apart by asking whether the watch process is still alive: alive means this was a
  # timeout (loop again), gone means end of stream. [inferred]
  if kill -0 "$watch_pid" 2>/dev/null; then continue; fi
  # Drain before the stream is read as ended. When `read` timed out and the watch then
  # wrote its last lines and exited before the `kill -0` above, those lines (a
  # `turn_result`, a cursor, an error object) are still in the pipe. Read them through
  # the same handler until a read fails or a line ends the wait; with no terminal line,
  # the outcome is `eof`. [inferred]
  outcome="eof"
  while IFS= read -r -t 1 line <&3; do
    handle_line "$line" || break
  done
  break
done
exec 3<&-

watch_rc=0
if [ -n "$watch_pid" ]; then
  if [ "$outcome" = "eof" ]; then
    wait "$watch_pid"; watch_rc=$?
  else
    kill -TERM "$watch_pid" 2>/dev/null || true
    sleep 2
    if kill -0 "$watch_pid" 2>/dev/null; then kill -KILL "$watch_pid" 2>/dev/null || true; fi
    wait "$watch_pid" 2>/dev/null || true
  fi
  watch_pid=""
fi

idle=$(( SECONDS - last_event ))
report() {
  printf 'WAIT_RESULT=%s\n' "$1"
  [ -n "$turn_status" ] && printf 'WAIT_TURN_STATUS=%s\n' "$turn_status"
  [ -n "$error_reason" ] && printf 'WAIT_ERROR=%s\n' "$error_reason"
  printf 'WAIT_CURSOR=%s\n' "$cursor"
  printf 'WAIT_EVENTS=%s\n' "$events"
  # The stall signal relay has never had: a worker that emits nothing for many minutes
  # is not a worker that is working. Reported here, acted on nowhere in this release.
  printf 'WAIT_IDLE_SECONDS=%s\n' "$idle"
  return 0
}

case "$outcome" in
  settled) report settled; exit 0 ;;
  error)   report error; exit 1 ;;
  running) report running; exit "$EXIT_RUNNING" ;;
  eof)
    if [ "$watch_rc" -eq 0 ]; then report closed; exit 0; fi
    error_reason="${error_reason:-unknown}"
    # The watch died without a JSON error object — acpx missing from PATH, an adapter it
    # could not spawn. Its stderr is the only account of why, so it goes to this script's
    # stderr rather than being deleted with the temp directory.
    if [ -s "$pipe_dir/stderr" ]; then
      echo "acpx-wait.sh: the watch exited $watch_rc. Its last stderr lines:" >&2
      tail -5 "$pipe_dir/stderr" >&2
    fi
    report error
    exit 1
    ;;
esac
