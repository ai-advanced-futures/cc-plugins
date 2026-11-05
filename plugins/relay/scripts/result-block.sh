#!/usr/bin/env bash
# relay: print one relay.implement-result/1 block (spec §8, D13).
#
# Usage:
#   result-block.sh --status ok|blocked|error [--run-id <wf_id>] [--branch <name>]
#                   [--commit <sha>] [--reason <text>]
#
# Prints one fenced json block on stdout, with the JSON on one line, and nothing
# else. The keys come in this order: schema, status, run_id, branch, commit, and
# then reason only when the status is not ok. An absent run_id, branch or commit
# prints null. With no --branch, the branch is `git rev-parse --abbrev-ref HEAD`
# of the current directory, and a detached HEAD or a directory outside git gives
# null. python3 writes the JSON, as scripts/record-run-intent.sh does, so every
# string is escaped correctly.
#
# The script refuses a block that breaks the contract. It then prints one line
# on stderr, prints nothing on stdout, and exits 2:
#   - the status is absent or not ok, blocked or error;
#   - ok has no --run-id or no --commit, or has a --reason;
#   - blocked or error has no --reason, or an empty one;
#   - --run-id does not match ^wf_[A-Za-z0-9][A-Za-z0-9._-]*$ (so the
#     placeholder `wf_...` fails and a real id such as wf_e327bc81-b13 passes).
set -uo pipefail

_rb_die() {
  echo "result-block.sh: $1" >&2
  exit 2
}

status=""
run_id=""
branch=""
branch_set=0
commit=""
reason=""
reason_set=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --status|--run-id|--branch|--commit|--reason)
      [ "$#" -ge 2 ] || _rb_die "$1 takes a value"
      ;;
  esac
  case "$1" in
    --status) status="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    --branch) branch="$2"; branch_set=1; shift 2 ;;
    --commit) commit="$2"; shift 2 ;;
    --reason) reason="$2"; reason_set=1; shift 2 ;;
    *) _rb_die "unknown argument: $1" ;;
  esac
done

case "$status" in
  ok|blocked|error) ;;
  "") _rb_die "--status is required (ok, blocked or error)" ;;
  *) _rb_die "invalid status '$status' (expected ok, blocked or error)" ;;
esac

_rb_re='^wf_[A-Za-z0-9][A-Za-z0-9._-]*$'
if [ -n "$run_id" ] && ! [[ "$run_id" =~ $_rb_re ]]; then
  _rb_die "invalid run id '$run_id' (expected wf_<id>)"
fi

if [ "$status" = "ok" ]; then
  [ -n "$run_id" ] || _rb_die "status ok needs --run-id"
  [ -n "$commit" ] || _rb_die "status ok needs --commit"
  [ "$reason_set" = 0 ] || _rb_die "status ok takes no --reason"
else
  [ -n "$reason" ] || _rb_die "status $status needs a non-empty --reason"
fi

if [ "$branch_set" = 0 ]; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || branch=""
  if [ "$branch" = "HEAD" ]; then
    branch=""
  fi
fi

json="$(RB_STATUS="$status" RB_RUN_ID="$run_id" RB_BRANCH="$branch" RB_COMMIT="$commit" \
  RB_REASON="$reason" PYTHONIOENCODING=utf-8 python3 -c '
import json
import os


def opt(key):
    value = os.environ.get(key, "")
    return value if value else None


block = {
    "schema": "relay.implement-result/1",
    "status": os.environ["RB_STATUS"],
    "run_id": opt("RB_RUN_ID"),
    "branch": opt("RB_BRANCH"),
    "commit": opt("RB_COMMIT"),
}
if block["status"] != "ok":
    block["reason"] = os.environ["RB_REASON"]
print(json.dumps(block, ensure_ascii=False))
')" || _rb_die "python3 could not write the block"

printf '```json\n%s\n```\n' "$json"
