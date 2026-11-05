#!/usr/bin/env bash
# wait-for-workflow.sh — hold the turn while a background Workflow runs.
#
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/wait-for-workflow.sh" <runId> [--max-seconds <n>]
#
# The Workflow tool starts a run in the background and returns at once. In an
# interactive session a task notification arrives when the run ends. Under `claude -p`
# the session waits for background work only about 600 s after the model ends its
# turn, and then it kills the run: relay 5.0.0 proof rows wf_c36ba268-29d and
# wf_65b4f5c0-3f5 were both `killed` at about 605 s. So a run with no person present
# must not end its turn while the Workflow runs. It calls this script again and again.
#
# The script reads the run file `workflows/<runId>.json` and waits until its `status`
# is not `running`, or until the budget is spent. It finds the run file the same way
# as scripts/verify-run-completeness.sh: the session directory named by
# CLAUDE_CODE_SESSION_ID first, then a glob over every project. Never from $PWD.
#
# Output, last lines:
#   RELAY_WF_RUN_FILE=<path>        (only when the file was found)
#   RELAY_WF_STATUS=<status>        running | completed | killed | failed | ...
# Exit:
#   0  the run ended (any status that is not `running`) — read RELAY_WF_STATUS
#   3  the run still runs, or its file is not written yet — call the script again
#   2  usage error
#
# macOS has no `timeout`, so the budget is a bash $SECONDS loop. The default budget,
# 540 s, stays under the 600000 ms ceiling of one Bash tool call.
set -uo pipefail

_wf_usage() {
  echo "usage: wait-for-workflow.sh <runId> [--max-seconds <n>]" >&2
  exit 2
}

_wf_run_id=""
_wf_max=540
while [ "$#" -gt 0 ]; do
  case "$1" in
    --max-seconds)
      [ "$#" -ge 2 ] || _wf_usage
      _wf_max="$2"
      shift 2
      ;;
    --*) _wf_usage ;;
    *)
      [ -z "$_wf_run_id" ] || _wf_usage
      _wf_run_id="$1"
      shift
      ;;
  esac
done
[ -n "$_wf_run_id" ] || _wf_usage
case "$_wf_max" in
  ''|*[!0-9]*) _wf_usage ;;
esac
_wf_run_id="${_wf_run_id##*/}"
_wf_run_id="${_wf_run_id%.json}"
case "$_wf_run_id" in
  ''|*[!A-Za-z0-9._-]*) echo "wait-for-workflow: '$_wf_run_id' is not a bare run id" >&2; exit 2 ;;
esac
command -v python3 >/dev/null 2>&1 || { echo "wait-for-workflow: python3 is required" >&2; exit 2; }

_wf_poll="${RELAY_WF_POLL_SECONDS:-15}"
case "$_wf_poll" in
  ''|*[!0-9]*|0) _wf_poll=15 ;;
esac
_wf_projects="${HOME:-}/.claude/projects"

_wf_find() {
  local sid="${CLAUDE_CODE_SESSION_ID:-}" dir cand
  if [ -n "$sid" ]; then
    dir="$(find "$_wf_projects" -mindepth 2 -maxdepth 2 -type d -name "$sid" 2>/dev/null | head -n 1)"
    if [ -n "$dir" ] && [ -f "$dir/workflows/$_wf_run_id.json" ]; then
      echo "$dir/workflows/$_wf_run_id.json"
      return
    fi
  fi
  for cand in "$_wf_projects"/*/*/workflows/"$_wf_run_id".json; do
    if [ -f "$cand" ]; then
      echo "$cand"
      return
    fi
  done
}

_wf_status() {
  python3 - "$1" <<'PY'
import json, sys
try:
    print(json.load(open(sys.argv[1])).get("status") or "running")
except Exception:
    # A file caught in the middle of a write is not yet readable. Read it again later.
    print("running")
PY
}

_wf_start=$SECONDS
_wf_file=""
_wf_state="running"
while :; do
  [ -n "$_wf_file" ] || _wf_file="$(_wf_find)"
  if [ -n "$_wf_file" ]; then
    _wf_state="$(_wf_status "$_wf_file")"
    [ "$_wf_state" = "running" ] || break
  fi
  [ $((SECONDS - _wf_start + _wf_poll)) -le "$_wf_max" ] || break
  sleep "$_wf_poll"
done

[ -z "$_wf_file" ] || echo "RELAY_WF_RUN_FILE=$_wf_file"
echo "RELAY_WF_STATUS=$_wf_state"
[ "$_wf_state" = "running" ] && exit 3
exit 0
