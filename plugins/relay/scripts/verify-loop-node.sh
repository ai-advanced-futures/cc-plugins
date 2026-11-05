#!/usr/bin/env bash
# One node of the relay verify-until-clean loop.
#
# The loop's node bodies live here, not inline in the Workflow script, for three
# reasons. Inline bash in a generated script cannot be unit-tested, so the shape the
# skill documents and the shape the run executes could drift apart. Each inline body
# also had to be restated in every node prompt, which cost about 35000 tokens per node
# to run a single command. And a Claude Code session that is isolated in a git worktree
# refuses a Bash command it judges too complex to verify, which every inline body was.
#
# Read the containment note in skills/verifying-until-clean/SKILL.md before adding a
# step here. Every git call is scoped with `-C "$worktree"` on purpose: a node's working
# directory is not guaranteed to be the worktree, which is why the path is an argument
# and never derived from the caller's cwd.
#
# Every exit path prints `NODE_STATUS=` as the LAST line, and prints it exactly once.
# The node that runs this script is a model, and it relays what it reads. When the status
# line sat above 25 to 40 lines of child output, nodes summarised the whole block instead
# of relaying the line: run wf_8ad76eec-5ac returned invented detail values, one of them
# the literal word `placeholder`, and reported `ran` for a step that had run nothing.
# Last means "read the last line" is a mechanical rule that needs no judgement. Keep it
# last when you add a path.
set -uo pipefail

usage() {
  cat >&2 <<'EOF'
usage: verify-loop-node.sh --phase <phase> <kind> <worktree> <round> <rounds>
       verify-loop-node.sh init   <worktree> <rounds>
       verify-loop-node.sh report <worktree> <rounds>

A round kind is simplify, review, check or fix. Every round kind needs a
phase; init and report take none.

The acpx engine splits a step into a launch call and one or more watch calls:
  launch  start the helper detached, wait for its session, report `launched`
  watch   read the helper's session, complete the step when it settles, and
          report `running` while it still works
The in-session engine splits a step into two calls of its own:
  pre   read the state, print the command to invoke
  post  read the reply the caller wrote, parse it, record it
EOF
}

# Every round kind is two calls or more. `launch` and `watch` are the acpx engine: a
# node runs as one Bash call with the tool's 600 second ceiling, while the child runs
# with an 1800 second acpx timeout, so one call cannot hold a whole step. `pre` and
# `post` are the in-session engine — a slash command is reached through a tool call, and
# Bash cannot make one. The state, the verdict parse, the commits and the records stay
# here in both engines. Only the way the step reaches the command moves.
# One allow-list for both spellings. A copy per spelling accepts a newly added phase
# in one syntax and refuses it in the other.
require_known_phase() {
  case "${1:-}" in
    pre|post|launch|watch) return 0 ;;
  esac
  usage
  echo "NODE_STATUS=failed:64 reason=bad-phase:${1:-<empty>}"
  exit 64
}

PHASE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --phase)
      PHASE="${2:-}"
      require_known_phase "$PHASE"
      shift 2
      ;;
    --phase=*)
      PHASE="${1#--phase=}"
      require_known_phase "$PHASE"
      shift
      ;;
    *) break ;;
  esac
done

if [ "$#" -lt 3 ]; then
  usage
  echo "NODE_STATUS=failed:64 reason=bad-arguments"
  exit 64
fi

kind="$1"
worktree="$2"

# init and report start no child, so there is no command for `pre` to print, no reply for
# `post` to read, nothing for `launch` to start and nothing for `watch` to follow.
# Accepting the flag and ignoring it would let a caller believe it had split a step that
# was never split.
#
# An unknown kind is named by the `*` arm of the main case below, so it is not listed
# here: a bare `teleport` must read `unknown-kind`, not `phase-required`.
case "$kind" in
  init|report)
    if [ -n "$PHASE" ]; then
      usage
      echo "NODE_STATUS=failed:64 reason=phase-not-supported-for-kind:$kind"
      exit 64
    fi
    ;;
  simplify|review|check|fix)
    # A round kind with no phase used to run the whole step in one Bash call. That call
    # is cut off after ten minutes while the child runs with an 1800 second acpx timeout,
    # so the step was killed before the script wrote its record.
    if [ -z "$PHASE" ]; then
      usage
      echo "NODE_STATUS=failed:64 reason=phase-required"
      exit 64
    fi
    ;;
esac

if [ ! -d "$worktree" ]; then
  echo "verify-loop-node.sh: worktree not found: $worktree" >&2
  echo "NODE_STATUS=failed:66 reason=worktree-not-found"
  exit 66
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

git_dir="$(git -C "$worktree" rev-parse --absolute-git-dir 2>/dev/null)"
if [ -z "$git_dir" ]; then
  echo "verify-loop-node.sh: not a git checkout: $worktree" >&2
  echo "NODE_STATUS=failed:66 reason=not-a-git-checkout"
  exit 66
fi

# State lives under the git directory, never in the working tree. Git tracks nothing
# there, so `git add -A` cannot sweep the run's own logs into a commit and
# `git status --short` stays honest. A scratch directory inside the working tree would
# make every round look as if it changed files, which silently defeats the fix-noop
# check below.
STATE_ROOT="$git_dir/relay-verify"

read_state() {
  [ -f "$STATE_ROOT/state" ] || return 0
  sed -nE "s/.*$1=([A-Za-z0-9_-]*).*/\1/p" "$STATE_ROOT/state" 2>/dev/null | tail -1
}

write_state() {
  printf 'LABEL=%s ROUND=%s NOOPS=%s EXIT=%s\n' "$1" "$2" "$3" "$4" > "$STATE_ROOT/state"
}

# Commit whatever the step just changed. The scope derivation and the commit live in
# scripts/verify-commit-scope.sh, which prints one line: a sha, `commit-failed`, or
# `no changes`. A commit that exits non-zero is never folded into a normal commit result.
commit_step() {
  bash "$here/verify-commit-scope.sh" "$worktree" "$1"
}

# A missing state file means the init node never ran, so the loop never started. That is
# not a skip: a skipped node says the loop decided to stop, and recording both the same
# way hides a refused init node behind an orderly-looking record.
require_state() {
  local key="$1" round_dir="$2"
  if [ ! -f "$STATE_ROOT/state" ]; then
    if claim_step "$round_dir" "$key"; then
      echo "$key=failed:no-state" >> "$round_dir/record"
    fi
    echo "NODE_STATUS=failed:no-state reason=verify-init-did-not-run"
    exit 0
  fi
}

# Two budgets, not one. The slice bounds ONE watch call and must stay under the Bash
# tool's 600 second ceiling. The ceiling bounds the whole step, measured from
# <tag>.started, across every watch call: its default is the child's 1800 second acpx
# timeout plus a margin, so acpx's own exit 3 is the normal way a slow child ends and the
# ceiling is the backstop. `0` turns the ceiling off.
#
# Both are forced to base 10 after the digit test, because bash reads a leading zero as
# octal. `0600` becomes 384 seconds — a budget cut by a third with nothing said. `0900`
# is not a legal octal number at all, so the arithmetic fails and leaves the variable
# unset, which `set -u` then turns into a node that prints no status line. `00` passes
# the digit test but is not the string `0`, so a string test for the off-switch misses
# it; in base 10 it is 0, which turns the ceiling off.
# One site for the rule above, so no copy of it can lose its `10#`.
seconds_or_default() {
  case "${1:-}" in
    ''|*[!0-9]*) printf '%s' "$2" ;;
    *) printf '%s' "$(( 10#$1 ))" ;;
  esac
}
SLICE_SECONDS="${RELAY_VERIFY_SLICE_SECONDS:-540}"
SLICE_SECONDS="$(seconds_or_default "$SLICE_SECONDS" 540)"
NODE_CEILING="${RELAY_VERIFY_NODE_TIMEOUT:-1900}"
case "$NODE_CEILING" in
  ''|*[!0-9]*)
    echo "verify-loop-node.sh: RELAY_VERIFY_NODE_TIMEOUT is not a whole number of seconds: $NODE_CEILING (using 1900)" >&2
    ;;
esac
NODE_CEILING="$(seconds_or_default "$NODE_CEILING" 1900)"
# Set only by a path of this script; a value from the caller's environment never counts.
TIMEOUT_REASON=""

# The acpx timeout the helpers give their child. Named here so a status line can say
# which timeout fired: the child's own (acpx exit 3) or this step's ceiling. This one is
# deliberately NOT forced to base 10: the helpers read `RELAY_VERIFY_TIMEOUT` themselves
# and hand it to `acpx --timeout` as written, so the number printed here has to be the
# number acpx was given. It is a label, never an operand.
CHILD_TIMEOUT="${RELAY_VERIFY_TIMEOUT:-${RELAY_POLISH_TIMEOUT:-1800}}"
case "$CHILD_TIMEOUT" in ''|*[!0-9]*) CHILD_TIMEOUT=1800 ;; esac

# The pause before a watch error is reported as `running`. acpx-wait.sh answers an error
# at once, so without it the node re-issues `watch` as fast as it can be called.
WATCH_ERROR_PAUSE="${RELAY_VERIFY_WATCH_ERROR_PAUSE:-5}"
WATCH_ERROR_PAUSE="$(seconds_or_default "$WATCH_ERROR_PAUSE" 5)"

# acpx-wait.sh reports "still running" with 75 (EX_TEMPFAIL). It is deliberately not 3:
# acpx uses 3 for its own timeout, which this script maps to the child-timeout bucket.
RELAY_WAIT_RUNNING=75

# --- the two-call protocol, for the in-session engine only ---------------------
#
# With acpx this script starts the child, so a written record is EVIDENCE that a step
# ran. In-session the caller invokes the command through a tool and hands the reply
# back, so a record is only a CLAIM. That difference is the whole risk of the
# in-session engine, and it is this loop's own named failure mode: run wf_8ad76eec-5ac
# reported `ran` for a step that had run nothing.
#
# Five mechanical guards answer it. None of them needs judgement:
#   1. `pre` deletes the reply file, so a file present at `post` time was written
#      after `pre` ran. A leftover file from an earlier attempt cannot stand in.
#   2. `pre` writes a `.go` marker only on the path where a command must be invoked.
#      `post` refuses without it, so a `post` that follows a SKIPPED `pre` cannot
#      overwrite the skip record with a failure.
#   3. An absent or empty reply is `failed:no-reply`. It is not a skip, and it is
#      never a pass.
#   4. `post` builds the output fence itself, around text it treats as opaque. The
#      caller never writes the fence, so the caller cannot forge one. The parser
#      reads the FIRST begin marker and the LAST end marker, and both of those are
#      this script's, so marker text inside the reply cannot move the region.
#   5. One terminal record line per round and step, claimed with `mkdir`. `mkdir` either
#      makes the directory or fails; it cannot half-succeed, so exactly one caller wins
#      even when two chains of one forked session run the same step at the same time. A
#      caller that finds the claim held is a re-entry, not a new attempt: it must not
#      delete the reply, must not re-arm the marker, must not overwrite the `.out` file,
#      must not append a second value the report would have to guess at, and must not
#      move the loop state.
reply_file() { printf '%s/%s.reply' "$1" "$2"; }
go_marker()  { printf '%s/%s.go' "$1" "$2"; }
done_marker() { printf '%s/%s.done' "$1" "$2"; }
# Guard 5. The marker is keyed on the RECORD KEY (SIMPLIFY, REVIEW, CHECK, FIX), not on
# the lowercase kind, so it cannot collide with `<kind>.go` or `<kind>.reply`, and so
# `simplify` and `review` cannot share one claim through their shared branch. The `init`
# node deletes each round directory, so a new run starts with no claim held.
claim_step()      { mkdir "$(done_marker "$1" "$2")" 2>/dev/null; }
step_done()       { [ -d "$(done_marker "$1" "$2")" ]; }
recorded_status() { sed -nE "s/^$2=(.*)$/\1/p" "$1/record" 2>/dev/null | tail -1; }

# --- the detached-helper protocol, for the acpx engine ------------------------
#
# A node runs as one Bash call, and that call is cut off after ten minutes, while a
# verify child gets 1800 seconds. One call therefore cannot hold a whole step. `launch`
# starts the helper in a session of its own and returns as soon as the helper says its
# acpx session exists; later calls watch that session and complete the step.
launch_marker() { printf '%s/%s.launch' "$1" "$2"; }
# The check retry's mark. The completion path drops the launch marker and sets this one,
# and the next `watch` call starts the second child. One call therefore holds at most one
# ready wait, or one slice plus the helper-exit wait, and never two children.
retry_marker() { printf '%s/%s.retry' "$1" "$2"; }

# The ready wait. A helper signals readiness right after `sessions new` succeeds.
READY_SECONDS="${RELAY_VERIFY_READY_SECONDS:-90}"
READY_SECONDS="$(seconds_or_default "$READY_SECONDS" 90)"

# A pid read from a file is only worth signalling while the process it names is still the
# helper. A finished helper's pid can be reused by anything, and signalling a reused pid
# kills an unrelated process. Three checks: the pid is alive, it is still the session
# leader `setsid` made (its pgid is itself), and its command names a verify helper.
helper_pid_is_live() {
  local pid="${1:-}"
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  kill -0 "$pid" 2>/dev/null || return 1
  [ "$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')" = "$pid" ] || return 1
  ps -o command= -p "$pid" 2>/dev/null | grep -q 'run-claude-\(command\|prompt\)\.sh' || return 1
  return 0
}

# TERM the helper's whole process group, then KILL what is left. The group is the helper
# and its acpx child, which `setsid` made a session of its own.
end_helper_group() {
  local pid="${1:-}" grace="${2:-5}" waited=0
  helper_pid_is_live "$pid" || return 0
  kill -TERM -- "-$pid" 2>/dev/null || true
  while [ "$waited" -lt "$grace" ]; do
    kill -0 "$pid" 2>/dev/null || return 0
    sleep 1
    waited=$(( waited + 1 ))
  done
  kill -KILL -- "-$pid" 2>/dev/null || true
  return 0
}

read_pid() { head -1 "$1/$2.pid" 2>/dev/null | tr -d ' '; }

# The lowercase tag of a record key. The round directory holds <tag>.out, <tag>.pid and
# the rest under the tag; the record and the markers use the key.
key_tag() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

# A step whose node ended its turn holds a launch or retry marker and has no record line.
# A reap never runs the completion path: it does not parse <tag>.out, does not start a
# retry, does not write the state line, does not commit, and prints no NODE_STATUS of its
# own. It makes the step visible and it stops the child.
reap_abandoned() {
  local record_it="$1" d k tag
  for d in "$STATE_ROOT"/round-*; do
    [ -d "$d" ] || continue
    for k in SIMPLIFY REVIEW CHECK FIX; do
      if [ -d "$d/$k.launch" ] || [ -d "$d/$k.retry" ]; then
        [ -n "$(recorded_status "$d" "$k")" ] && continue
        tag="$(key_tag "$k")"
        end_helper_group "$(read_pid "$d" "$tag")" 5
        if [ "$record_it" = "record" ]; then
          # Not in the report's approved set, so the run counts it as a failed step and
          # cannot print `clean`.
          echo "$k=failed:abandoned reason=launch-orphaned" >> "$d/record"
        fi
      fi
    done
  done
  return 0
}

# The first other step, anywhere under this state root, that holds a launch or retry
# marker with no record line beside it. Live helper or not: the record is what says
# whether a step is accounted for.
prior_step_running() {
  local self_dir="$1" self_key="$2" d k n
  for d in "$STATE_ROOT"/round-*; do
    [ -d "$d" ] || continue
    n="${d##*/round-}"
    for k in SIMPLIFY REVIEW CHECK FIX; do
      [ "$d" = "$self_dir" ] && [ "$k" = "$self_key" ] && continue
      if [ -d "$d/$k.launch" ] || [ -d "$d/$k.retry" ]; then
        [ -n "$(recorded_status "$d" "$k")" ] && continue
        printf '%s-r%s\n' "$(key_tag "$k")" "$n"
        return 0
      fi
    done
  done
  return 1
}

# The rc of a detached helper, read from the last line it printed. An absent or empty
# file is 65, `no reply`, exactly as the in-session path reads an empty reply file.
helper_rc_from_out() {
  local f="$1/$2.out" rc
  [ -s "$f" ] || { echo 65; return 0; }
  rc="$(sed -nE 's/^POLISH_CMD_RC=([0-9]+)[[:space:]]*$/\1/p' "$f" | tail -1)"
  [ -n "$rc" ] || rc=65
  echo "$rc"
}

# Start the helper in a session of its own, so the node's Bash call can return while the
# child keeps working, and so one `kill -- -<pid>` ends the helper and its acpx child
# together. perl ships with macOS and with the CI image; `setsid` the binary does not ship
# with macOS. The child writes its own pid from inside the new session, so no output
# stream has to carry it back and the parent can exit at once.
HELPER_PID=""
launch_helper() {
  local round_dir="$1" tag="$2" helper="$3" session="$4" text="$5"
  # Every time, so a relaunch never reads the first child's ready file, resumes from its
  # cursor, or completes against its output.
  rm -f "$round_dir/$tag.ready" "$round_dir/$tag.cursor" "$round_dir/$tag.pid" \
        "$round_dir/$tag.ndjson" "$round_dir/$tag.out" \
        2>/dev/null || true
  # `<tag>.started` is the ONE clock of the whole step, so a relaunch keeps it. Resetting
  # it on the check retry would give the second child a full ceiling of its own, and the
  # step could then run for twice the ceiling — the per-child limit that broke this
  # promise once before (run wf_918a4deb-aba, two 540 second children under a 600 second
  # ceiling, CHECK=missing in all three rounds). The `init` node deletes the round
  # directories, so a new run always starts with no file here.
  [ -s "$round_dir/$tag.started" ] || date +%s > "$round_dir/$tag.started"
  perl -e 'use POSIX; my $p = fork; if ($p) { exit 0 }
           open(STDIN, "<", "/dev/null"); open(STDOUT, ">", $ARGV[0]); open(STDERR, ">&STDOUT");
           POSIX::setsid() or die "setsid: $!";
           open(my $pf, ">", $ARGV[1]) or die "pidfile: $!"; print $pf "$$\n"; close $pf;
           shift @ARGV; shift @ARGV; exec @ARGV or die "exec: $!"' -- \
    "$round_dir/$tag.out" "$round_dir/$tag.pid" \
    env RELAY_HELPER_NDJSON="$round_dir/$tag.ndjson" \
        RELAY_HELPER_READY_FILE="$round_dir/$tag.ready" \
        "$here/$helper" "$worktree" "$session" "$text"
  # The pid write races the parent's exit by a few milliseconds.
  local waited=0
  HELPER_PID="$(read_pid "$round_dir" "$tag")"
  while [ -z "$HELPER_PID" ] && [ "$waited" -lt 5 ]; do
    sleep 1
    waited=$(( waited + 1 ))
    HELPER_PID="$(read_pid "$round_dir" "$tag")"
  done
  waited=0
  while [ "$waited" -lt "$READY_SECONDS" ]; do
    [ -e "$round_dir/$tag.ready" ] && return 0
    # `kill -0` alone here, not helper_pid_is_live: the pid was created moments ago, so
    # it cannot be a reused one, and the command-name check in that guard reads `perl`
    # during the few milliseconds between the pid write and the exec.
    kill -0 "$HELPER_PID" 2>/dev/null || return 1
    sleep 1
    waited=$(( waited + 1 ))
  done
  end_helper_group "$HELPER_PID" 5
  return 2
}

# One field of acpx-wait.sh's keyed output. The key set is that script's contract, so it
# is read through one rule here rather than a pipeline per field.
wait_field() { printf '%s\n' "$1" | sed -nE "s/^$2=(.*)$/\1/p" | tail -1; }

# One watch call. It either completes the step or reports that the step is still running.
# `complete_step` is defined per kind, further down, and resolves at call time.
watch_step() {
  local round_dir="$1" tag="$2" key="$3" session="$4"
  local pid; pid="$(read_pid "$round_dir" "$tag")"
  if ! helper_pid_is_live "$pid"; then
    complete_step "$(helper_rc_from_out "$round_dir" "$tag")"
    return 0
  fi
  local started now elapsed slice left
  started="$(head -1 "$round_dir/$tag.started" 2>/dev/null)"
  case "$started" in ''|*[!0-9]*) started="$(date +%s)" ;; esac
  now="$(date +%s)"
  elapsed=$(( now - started ))
  slice="$SLICE_SECONDS"
  if [ "$NODE_CEILING" != "0" ]; then
    left=$(( NODE_CEILING - elapsed ))
    if [ "$left" -le 0 ]; then
      # The ceiling is spent. End the helper's whole group, then record what landed;
      # for `fix` the completion path commits it.
      end_helper_group "$pid" 5
      complete_step 124
      return 0
    fi
    [ "$left" -lt "$slice" ] && slice="$left"
  fi
  local wait_out wait_rc result events idle cursor reason waited
  wait_out="$(bash "$here/acpx-wait.sh" --session "$session" --cwd "$worktree" \
              --cursor-file "$round_dir/$tag.cursor" --budget "$slice" 2>/dev/null)"
  wait_rc=$?
  result="$(wait_field "$wait_out" WAIT_RESULT)"
  events="$(wait_field "$wait_out" WAIT_EVENTS)"
  idle="$(wait_field "$wait_out" WAIT_IDLE_SECONDS)"
  cursor="$(wait_field "$wait_out" WAIT_CURSOR)"
  reason="$(wait_field "$wait_out" WAIT_ERROR)"
  if [ "$wait_rc" -eq 0 ]; then
    # settled or closed. The helper still has to close its session and print its fence,
    # which takes well under a second.
    waited=0
    while [ "$waited" -lt 30 ] && helper_pid_is_live "$pid"; do
      sleep 1
      waited=$(( waited + 1 ))
    done
    if helper_pid_is_live "$pid"; then
      end_helper_group "$pid" 5
      # A killed helper leaves whatever it already wrote on disk. The completion path
      # records it as a timeout, exactly as the ceiling path does: it claims the key,
      # removes the pid file, writes every line the step owns (FIX_TRUNCATED included),
      # and for `fix` commits what landed, so the next step's commit cannot sweep this
      # step's edits under its own label.
      TIMEOUT_REASON="helper-did-not-exit-after-settle"
      complete_step 124
      return 0
    fi
    complete_step "$(helper_rc_from_out "$round_dir" "$tag")"
    return 0
  fi
  if [ "$wait_rc" -eq "$RELAY_WAIT_RUNNING" ]; then
    echo "NODE_STATUS=running cursor=$cursor events=$events idle=${idle}s elapsed=${elapsed}s ceiling=${NODE_CEILING}s"
    exit 0
  fi
  # A watch error is not a child failure.
  if helper_pid_is_live "$pid"; then
    # acpx-wait.sh answers a watch error at once, so this call would return in
    # milliseconds and the node would re-issue `watch` just as fast. A reason that does
    # not clear — `owner_unsupported`, a corrupt journal — then spends the whole ceiling
    # in a tight loop of node calls. Pause first, so a retry costs one tick, not a turn.
    sleep "$WATCH_ERROR_PAUSE"
    echo "NODE_STATUS=running watch=error:${reason:-unknown} result=${result:-error} elapsed=${elapsed}s ceiling=${NODE_CEILING}s"
    exit 0
  fi
  complete_step "$(helper_rc_from_out "$round_dir" "$tag")"
  return 0
}

# The launch result, for every caller that starts a helper. `retry_note` is the extra
# token the check retry prints on its second child; every other caller passes none.
start_helper() {
  local round_dir="$1" tag="$2" key="$3" helper="$4" session="$5" text="$6" noops="$7"
  local retry_note="${8:-}"
  launch_helper "$round_dir" "$tag" "$helper" "$session" "$text"
  case $? in
    0) echo "NODE_STATUS=launched${retry_note} pid=$HELPER_PID session=$session"
       exit 0 ;;
    1) complete_step "$(helper_rc_from_out "$round_dir" "$tag")" ;;
    *) claim_step "$round_dir" "$key" \
         && echo "$key=failed:launch" >> "$round_dir/record"
       write_state no-answer "$round" "$noops" unverified
       echo "NODE_STATUS=failed:launch reason=session-not-ready-in-${READY_SECONDS}s"
       exit 0
       ;;
  esac
}

# The whole `launch` phase, for every round kind. One body, because the three copies of
# it differed only in the record key, the tag, the helper and the payload — and they had
# already drifted apart.
launch_phase() {
  local round_dir="$1" tag="$2" key="$3" helper="$4" session="$5" text="$6" noops="$7"
  local other
  other="$(prior_step_running "$round_dir" "$key")"
  if [ -n "$other" ]; then
    # Every commit stays attributable to the step that made it. An unaccounted-for step
    # can still be editing the worktree, and this step's commit would sweep its changes
    # under this step's label.
    if claim_step "$round_dir" "$key"; then
      echo "$key=failed:prior-step-running reason=$other-launch-held" >> "$round_dir/record"
      write_state no-answer "$round" "$noops" unverified
      echo "NODE_STATUS=failed:prior-step-running reason=$other-launch-held"
      exit 0
    fi
    echo "NODE_STATUS=already-done key=$key value=$(recorded_status "$round_dir" "$key")"
    exit 0
  fi
  if ! mkdir "$(launch_marker "$round_dir" "$key")" 2>/dev/null; then
    # A held marker is a second launch call, never a second child.
    echo "NODE_STATUS=running launch=held"
    exit 0
  fi
  start_helper "$round_dir" "$tag" "$key" "$helper" "$session" "$text" "$noops"
}

# The whole `watch` phase, for every round kind. The retry arm is generic: only a
# completion path that wants a second child sets the retry marker, so a kind that never
# retries never reaches it.
watch_phase() {
  local round_dir="$1" tag="$2" key="$3" helper="$4" session="$5" text="$6" noops="$7"
  if [ ! -d "$(launch_marker "$round_dir" "$key")" ]; then
    if [ -d "$(retry_marker "$round_dir" "$key")" ]; then
      # The retry's second child. `sessions new` closes the first record, and a fresh
      # child is what a retry wants. `launch_helper` deletes the first child's ready
      # file, cursor, pid and output, so nothing of it is read as the second child's.
      #
      # Claimed with a plain `mkdir`, exactly as `launch_phase` does. `mkdir -p` succeeds
      # for every caller, so two `watch` calls that reached the retry state together each
      # started a child on one session, and the second pid write hid the first child from
      # every later kill.
      if ! mkdir "$(launch_marker "$round_dir" "$key")" 2>/dev/null; then
        echo "NODE_STATUS=running launch=held"
        exit 0
      fi
      start_helper "$round_dir" "$tag" "$key" "$helper" "$session" "$text" "$noops" " retry=1"
    fi
    echo "NODE_STATUS=failed:no-launch reason=watch-without-a-launch"
    exit 0
  fi
  watch_step "$round_dir" "$tag" "$key" "$session"
}

# Print the command the caller must invoke, then stop the step. The caller writes the
# whole reply to the named file and calls `post`.
emit_pre() {
  local round_dir="$1" tag="$2" command_text="$3"
  rm -f "$(reply_file "$round_dir" "$tag")" 2>/dev/null || true
  : > "$(go_marker "$round_dir" "$tag")"
  echo "PRE_REPLY_FILE=$(reply_file "$round_dir" "$tag")"
  echo "PRE_COMMAND_BEGIN"
  printf '%s\n' "$command_text"
  echo "PRE_COMMAND_END"
  echo "NODE_STATUS=pre kind=$tag reply=$(reply_file "$round_dir" "$tag")"
  exit 0
}

# Read what the caller wrote and shape it like a helper reply, so every consumer below —
# the verdict parser, the fix body, the tail — reads one format and needs no engine of
# its own.
#
# 65 is "no usable reply". It is deliberately not 0: a caller that invoked nothing
# still leaves an empty file behind on some shells, and an empty reply read as a
# success is exactly the fabricated pass this loop must never record.
read_caller_reply() {
  local round_dir="$1" tag="$2" file body
  file="$(reply_file "$round_dir" "$tag")"
  [ -f "$file" ] || return 65
  # A reply of only whitespace is no reply. `tr -d` collapses the test to "did the
  # caller write any visible character at all".
  body="$(tr -d '[:space:]' < "$file" 2>/dev/null)"
  [ -n "$body" ] || return 65
  printf 'POLISH_CMD_OUTPUT_BEGIN\n'
  cat "$file"
  printf '\nPOLISH_CMD_OUTPUT_END\n'
  printf 'POLISH_CMD_RC=0\n'
  return 0
}

# The in-session seam. It reads the reply the caller already produced, so the record,
# commit and state code after it is shared with the acpx engine and cannot drift. The
# acpx engine reaches the same code through `launch` and `watch`, which read the
# detached helper's own output file, so this function serves `post` alone: a call from
# any other phase is a caller that asked for a reply nobody was asked to write, and 70
# is the same answer a `post` with no `pre` behind it gets.
obtain_reply() {
  local round_dir="$1" tag="$2"
  [ "$PHASE" = "post" ] || return 70
  if [ ! -f "$(go_marker "$round_dir" "$tag")" ]; then
    return 70
  fi
  rm -f "$(go_marker "$round_dir" "$tag")" 2>/dev/null || true
  read_caller_reply "$round_dir" "$tag"
  return $?
}

# Name the cause of a 124. A child is always started, in `launch`, so the only cause left
# is the step's own ceiling.
# A path that ends the helper for another cause sets TIMEOUT_REASON first, so the record
# names that cause and not the ceiling.
timeout_reason() { echo "${TIMEOUT_REASON:-child-exceeded-${NODE_CEILING}s}"; }

# Every failure a completion path records: one record line, an optional commit of what
# the child left on disk, the loop state, one status line, exit. Each branch held its own
# copy of this shape, once per rc it answered.
#   $1 round_dir  $2 record key  $3 record value, which is also the status word
#   $4 state label  $5 noops  $6 status reason (empty prints none)
#   $7 commit tag (empty commits nothing)
fail_step() {
  local round_dir="$1" key="$2" value="$3" state_label="$4" noops="$5" reason="$6"
  local commit_tag="${7:-}"
  echo "$key=$value" >> "$round_dir/record"
  [ -n "$commit_tag" ] && echo "${key}_COMMIT=$(commit_step "$commit_tag")" >> "$round_dir/record"
  write_state "$state_label" "$round" "$noops" unverified
  local status_reason=""
  [ -n "$reason" ] && status_reason=" reason=$reason"
  echo "NODE_STATUS=$value$status_reason"
  exit 0
}

# The three rc buckets every branch answers the same way: this step's own ceiling, the
# child's acpx timeout, and a session record that does not exist. Only a step with
# half-applied work on disk names a commit tag; rc 4 started no child, so it commits
# nothing whatever the caller asks. Returns non-zero on any other rc, so the caller keeps
# the arms only it has.
fail_timeout_or_no_session() {
  local round_dir="$1" key="$2" rc="$3" noops="$4" commit_tag="${5:-}"
  case "$rc" in
    124) fail_step "$round_dir" "$key" failed:timeout no-answer "$noops" \
           "$(timeout_reason)" "$commit_tag" ;;
    3) fail_step "$round_dir" "$key" failed:timeout no-answer "$noops" \
         "child-exceeded-acpx-timeout-${CHILD_TIMEOUT}s" "$commit_tag" ;;
    4) fail_step "$round_dir" "$key" failed:4 no-answer "$noops" no-session ;;
    *) return 1 ;;
  esac
}

case "$kind" in
  init)
    mkdir -p "$STATE_ROOT"
    # A killed earlier run can have left a helper running under a round directory this
    # reset is about to delete.
    reap_abandoned no-record
    # Clear only the round directories this loop owns. Deleting the whole state root
    # also removes files this loop did not create.
    rm -rf "${STATE_ROOT:?}"/round-*
    mkdir -p "$STATE_ROOT/round-1"
    write_state "" 1 0 continue
    cat "$STATE_ROOT/state"
    echo "NODE_STATUS=ran detail=state-seeded"
    exit 0
    ;;

  simplify|review)
    round="$3"
    round_dir="$STATE_ROOT/round-$round"
    mkdir -p "$round_dir"
    if [ "$kind" = "simplify" ]; then key="SIMPLIFY"; slash="/simplify"
    else key="REVIEW"; slash="/code-review medium --fix"; fi
    require_state "$key" "$round_dir"
    if step_done "$round_dir" "$key"; then
      echo "NODE_STATUS=already-done key=$key value=$(recorded_status "$round_dir" "$key")"
      exit 0
    fi
    if [ "$(read_state EXIT)" != "continue" ]; then
      claim_step "$round_dir" "$key" && echo "$key=skipped" >> "$round_dir/record"
      echo "NODE_STATUS=skipped reason=round-already-ended"
      exit 0
    fi
    [ "$PHASE" = "pre" ] && emit_pre "$round_dir" "$kind" "$slash"
    session="relay-verify-$kind-r$round"

    # The completion path. `launch` calls it when the helper dies before it signals
    # ready; a later `watch` call uses it when the session settles or the helper is gone.
    # The reply is always `<tag>.out`: the helper writes it directly, and the in-session
    # `post` phase writes it from the text the caller handed back.
    complete_step() {
      local rc="$1"
      # A post with no `pre` behind it must not add a record line of its own, and a
      # re-entry that finds the claim held must not append a second value the report
      # would have to guess at. The step keeps whatever record it already had, which
      # for a skipped step is the skip.
      if ! claim_step "$round_dir" "$key"; then
        echo "NODE_STATUS=already-done key=$key value=$(recorded_status "$round_dir" "$key")"
        exit 0
      fi
      rm -f "$round_dir/$kind.pid" 2>/dev/null || true
      local noops; noops="$(read_state NOOPS)"
      # Nothing to commit on any of these: this step edits the worktree only when it
      # reports, and a step that reported nothing is recorded as the failure it was.
      [ "$rc" -eq 65 ] \
        && fail_step "$round_dir" "$key" failed:no-reply no-answer "$noops" caller-wrote-no-reply
      [ "$rc" -eq 69 ] \
        && fail_step "$round_dir" "$key" failed:69 no-answer "$noops" acpx-unavailable
      fail_timeout_or_no_session "$round_dir" "$key" "$rc" "$noops" || true
      [ "$rc" -ne 0 ] \
        && fail_step "$round_dir" "$key" "failed:$rc" no-answer "$noops" ""
      echo "$key=ran" >> "$round_dir/record"
      sha="$(commit_step "$kind")"
      echo "${key}_COMMIT=$sha" >> "$round_dir/record"
      tail -25 "$round_dir/$kind.out"
      echo "NODE_STATUS=ran commit=$sha"
      exit 0
    }

    [ "$PHASE" = "launch" ] && launch_phase "$round_dir" "$kind" "$key" \
      run-claude-command.sh "$session" "$slash" "$(read_state NOOPS)"
    [ "$PHASE" = "watch" ] && watch_phase "$round_dir" "$kind" "$key" \
      run-claude-command.sh "$session" "$slash" "$(read_state NOOPS)"

    out="$(obtain_reply "$round_dir" "$kind")"
    rc=$?
    # Before the write: a post with no `pre` behind it must not overwrite the file that
    # the real attempt left.
    if [ "$rc" -eq 70 ]; then
      echo "NODE_STATUS=failed:no-pre reason=post-ran-without-a-pre-that-asked-for-a-command"
      exit 0
    fi
    printf '%s\n' "$out" > "$round_dir/$kind.out"
    complete_step "$rc"
    ;;

  check)
    round="$3"
    rounds="$4"
    round_dir="$STATE_ROOT/round-$round"
    mkdir -p "$round_dir"
    require_state CHECK "$round_dir"
    if step_done "$round_dir" CHECK; then
      echo "NODE_STATUS=already-done key=CHECK value=$(recorded_status "$round_dir" CHECK)"
      exit 0
    fi
    if [ "$(read_state EXIT)" != "continue" ]; then
      claim_step "$round_dir" CHECK && echo "CHECK=skipped" >> "$round_dir/record"
      echo "NODE_STATUS=skipped reason=round-already-ended"
      exit 0
    fi
    noops="$(read_state NOOPS)"
    [ -z "$noops" ] && noops=0
    retried=0
    reason=""
    # /verify is not relay's command. It resolves to whatever the repository defines, and a
    # repository that holds its own verify skill can prescribe no report format at all. In
    # run wf_918a4deb-aba the child answered "## Verify result: productivity v0.7.0 — PASS",
    # which holds no verdict token, so the parser read no-answer and all three rounds bought
    # nothing. State the line the loop needs here. Do not assume the child prints it.
    #
    # The shape below is the enum template on purpose. A child that copies the contract into
    # its reply writes four verdict tokens on one line, and the one-token rule in
    # parse-verify-verdict.sh rejects that line. An example that holds one token, such as
    # "**Verdict:** PASS", is read as a real pass when a child copies it — the one error this
    # loop must never make.
    #
    # The text starts with "/", so the slash-only guard in run-claude-command.sh accepts it:
    # that guard reads the first character only. Keep this text free of apostrophes. It is a
    # single-quoted shell string, and skills/verifying-until-clean/SKILL.md holds a copy that
    # a test compares with this one.
    check_command='/verify

End your reply with a verdict line. Use this shape:

**Verdict:** PASS | FAIL | BLOCKED | SKIP

Write one word in the place of the four words: PASS, FAIL, BLOCKED, or SKIP. Do not copy the four words. Put the verdict line last, and write nothing after it.'
    [ "$PHASE" = "pre" ] && emit_pre "$round_dir" check "$check_command"
    session="relay-verify-check-r$round"
    run_check() {
      out="$(obtain_reply "$round_dir" check)"
      rc=$?
      # Keep the file that the real attempt left. See the simplify branch.
      [ "$rc" -eq 70 ] && return 70
      printf '%s\n' "$out" > "$round_dir/check.out"
      return $rc
    }
    read_verdict() {
      "$here/parse-verify-verdict.sh" "$round_dir/check.out" \
        > "$round_dir/verdict" 2> "$round_dir/verdict-reason"
      verdict="$(sed -nE 's/^VERIFY_VERDICT=(.*)$/\1/p' "$round_dir/verdict" | tail -1)"
      label="$(sed -nE 's/^VERIFY_LABEL=(.*)$/\1/p' "$round_dir/verdict" | tail -1)"
      reason="$(sed -nE 's/^VERIFY_REASON=(.*)$/\1/p' "$round_dir/verdict-reason" | tail -1)"
      [ -z "$label" ] && label="no-answer"
    }

    # The completion path. `launch` calls it when the helper dies before it signals
    # ready; a later `watch` call uses it when the session settles or the helper is gone.
    # The reply is always `check.out`: the helper writes it directly, and the in-session
    # `post` phase writes it from the text run_check captured.
    complete_step() {
      local rc="$1"
      verdict=""
      label="no-answer"
      [ "$rc" -eq 0 ] && read_verdict
      # `retried` has to be true on a second call too, and a shell variable cannot cross
      # two separate script invocations. check-1.out is the only durable evidence that a
      # first reply existed, so it is what the second call reads.
      [ -f "$round_dir/check-1.out" ] && retried=1
      # Two shapes are retried once, in a fresh session, because a second child can change
      # them: a BLOCKED verdict, and a reply with no usable output fence. Three shapes are
      # not, because a second child cannot:
      #   SKIP            — a second run sees the same empty diff.
      #   no reply at all — the caller invoked nothing, or wrote an empty file. That is not
      #                     a verdict of an unusable shape, it is the absence of an attempt.
      #                     Recording it as one more retried shape would leave a record that
      #                     cannot tell "answered badly" from "never answered".
      #   a timeout       — rc 124 is this step's ceiling (RELAY_VERIFY_NODE_TIMEOUT),
      #                     already spent, and rc 3 is the child's own acpx timeout. A
      #                     second child on top of either one only spends the ceiling.
      #   no session      — rc 4 cannot follow a successful `sessions new`; a retry
      #                     cannot conjure the record that is missing.
      #   no verdict line — the reply parsed; its format holds no verdict. The same command
      #                     in the same repository answers in the same format, so the retry
      #                     only spends a child. That retry is what pushed this node past the
      #                     caller's ceiling in run wf_918a4deb-aba.
      # `launch` is not one of the calls that may retry. It reaches this path only when
      # the helper died before it signalled ready, and a second child started from here
      # would be a whole synchronous child inside the launch call — the 600 second
      # ceiling this split exists to stay under. The step records the rc it has, with
      # RETRIED=0. The `watch` phase owns the retry.
      if [ "$PHASE" != "launch" ] \
         && [ "$label" = "no-answer" ] && [ "$verdict" != "SKIP" ] \
         && [ "$reason" != "no-verdict-line" ] \
         && [ "$rc" -ne 69 ] && [ "$rc" -ne 124 ] && [ "$rc" -ne 65 ] \
         && [ "$rc" -ne 3 ] && [ "$rc" -ne 4 ] \
         && [ "$retried" -eq 0 ]; then
        # Keep the first reply: the retry overwrites check.out, and a silent second reply
        # would erase the only evidence of what the first one answered. check-1.out is
        # also what makes `retried` true on the next call, since a shell variable cannot
        # cross two invocations.
        cp "$round_dir/check.out" "$round_dir/check-1.out" 2>/dev/null || true
        # In-session cannot start the second attempt from here: only the caller can invoke
        # the command. Re-arm and ask for one more reply. The decision stays in this
        # script, so the caller holds no state and makes no choice — it reads one line.
        if [ "$PHASE" = "post" ]; then
          rm -f "$(reply_file "$round_dir" check)" 2>/dev/null || true
          : > "$(go_marker "$round_dir" check)"
          echo "PRE_REPLY_FILE=$(reply_file "$round_dir" check)"
          echo "NODE_RETRY=1"
          echo "NODE_STATUS=retry reason=${reason:-no-usable-verdict}"
          exit 0
        fi
        # Never launch from here: one call holds at most one ready wait, or one slice
        # plus the helper-exit wait. The next `watch` call starts the second child.
        rm -rf "$(launch_marker "$round_dir" CHECK)" 2>/dev/null || true
        mkdir -p "$(retry_marker "$round_dir" CHECK)"
        echo "NODE_STATUS=running retry=1 reason=${reason:-no-usable-verdict}"
        exit 0
      fi
      if ! claim_step "$round_dir" CHECK; then
        echo "NODE_STATUS=already-done key=CHECK value=$(recorded_status "$round_dir" CHECK)"
        exit 0
      fi
      rm -f "$round_dir/check.pid" 2>/dev/null || true
      # Only these three end the step here. Every other rc still writes the verdict block
      # below, because the record has to name the label and the reason either way.
      fail_timeout_or_no_session "$round_dir" CHECK "$rc" "$noops" || true
      if [ "$rc" -eq 65 ]; then
        # Name it, rather than leaving a bare 65 that reads like an acpx exit code. The
        # caller invoked nothing, or wrote an empty file. Either way no verdict exists,
        # so the label below stays no-answer and the run ends unverified.
        echo "CHECK=failed:no-reply" >> "$round_dir/record"
      elif [ "$rc" -ne 0 ]; then
        echo "CHECK=failed:$rc" >> "$round_dir/record"
      else
        echo "CHECK=ran" >> "$round_dir/record"
      fi
      {
        echo "VERDICT=$verdict"
        echo "LABEL=$label"
        echo "REASON=$reason"
        echo "RETRIED=$retried"
      } >> "$round_dir/record"
      newexit="continue"
      [ "$label" = "clean" ] && newexit="clean"
      [ "$label" = "no-answer" ] && newexit="unverified"
      if [ "$round" -ge "$rounds" ] && [ "$label" = "findings" ]; then newexit="findings"; fi
      write_state "$label" "$round" "$noops" "$newexit"
      tail -40 "$round_dir/check.out"
      status_reason=""
      [ -n "$reason" ] && status_reason=" reason=$reason"
      # The verdict block above is written either way, so the record still names the
      # label and the reason. The status word carries the child's rc: `done` on a child
      # that failed reads as a check that finished and simply found no verdict, which is
      # the one thing this loop must never say. The names match the record lines.
      node_status="done"
      if [ "$rc" -eq 65 ]; then
        node_status="failed:no-reply"
      elif [ "$rc" -ne 0 ]; then
        node_status="failed:$rc"
      fi
      echo "NODE_STATUS=$node_status verdict=$verdict label=$label exit=$newexit retried=$retried$status_reason"
      exit 0
    }

    [ "$PHASE" = "launch" ] && launch_phase "$round_dir" check CHECK \
      run-claude-command.sh "$session" "$check_command" "$noops"
    [ "$PHASE" = "watch" ] && watch_phase "$round_dir" check CHECK \
      run-claude-command.sh "$session" "$check_command" "$noops"

    run_check
    rc=$?
    if [ "$rc" -eq 70 ]; then
      echo "NODE_STATUS=failed:no-pre reason=post-ran-without-a-pre-that-asked-for-a-command"
      exit 0
    fi
    complete_step "$rc"
    ;;

  fix)
    round="$3"
    rounds="$4"
    round_dir="$STATE_ROOT/round-$round"
    mkdir -p "$round_dir"
    require_state FIX "$round_dir"
    if step_done "$round_dir" FIX; then
      echo "NODE_STATUS=already-done key=FIX value=$(recorded_status "$round_dir" FIX)"
      exit 0
    fi
    label="$(read_state LABEL)"
    noops="$(read_state NOOPS)"
    [ -z "$noops" ] && noops=0
    if [ "$(read_state EXIT)" != "continue" ] || [ "$label" != "findings" ]; then
      claim_step "$round_dir" FIX && echo "FIX=skipped" >> "$round_dir/record"
      echo "NODE_STATUS=skipped reason=label=$label"
      exit 0
    fi
    head -c 16000 "$round_dir/check.out" > "$round_dir/fix-body.txt"
    trunc=0
    # A partial report must stay visible rather than silently standing in for the whole.
    if ! cmp -s "$round_dir/check.out" "$round_dir/fix-body.txt"; then trunc=1; fi
    instr="Fix the problems this report names. Change the code, not the report. Keep the existing tests as they are."
    if [ "$trunc" = "1" ]; then
      instr="(The report above was truncated to fit.)

$instr"
    fi
    prompt="$(cat "$round_dir/fix-body.txt")

$instr"
    # The fix step sends prose, not a slash command. In-session the caller does this work
    # with its own tools, so `pre` prints the instruction and the caller answers with a
    # summary. The reply is not the evidence here: the git checks below are.
    [ "$PHASE" = "pre" ] && emit_pre "$round_dir" fix "$prompt"
    session="relay-verify-fix-r$round"

    # The completion path, as in the simplify and check branches. Every record line the
    # step owns — FIX_TRUNCATED included — is written here, never at launch time: a line
    # written at launch would count a step that had not run.
    complete_step() {
      local rc="$1"
      if ! claim_step "$round_dir" FIX; then
        echo "NODE_STATUS=already-done key=FIX value=$(recorded_status "$round_dir" FIX)"
        exit 0
      fi
      rm -f "$round_dir/fix.pid" 2>/dev/null || true
      echo "FIX_TRUNCATED=$trunc" >> "$round_dir/record"
      # A fix that reported nothing may still have changed the tree. Commit what landed,
      # so the next round reads the tree that really exists, and never count it as a pass.
      [ "$rc" -eq 65 ] \
        && fail_step "$round_dir" FIX failed:no-reply no-answer "$noops" caller-wrote-no-reply fix
      # The only path that keeps the verdict label instead of no-answer: acpx never ran,
      # so the label the check step recorded is still the truth about the branch.
      [ "$rc" -eq 69 ] \
        && fail_step "$round_dir" FIX failed:69 "$label" "$noops" acpx-unavailable
      # A killed fix, or one that hit its own acpx timeout, leaves a half-applied tree.
      # Commit it, so the next round sees the tree that really exists and never counts a
      # killed step as a no-op. Naming a commit tag is what asks for that.
      fail_timeout_or_no_session "$round_dir" FIX "$rc" "$noops" fix || true
      dirty="$(git -C "$worktree" status --short)"
      sha="$(commit_step fix)"
      if [ -z "$dirty" ]; then
        echo "FIX=fix-noop" >> "$round_dir/record"
        noops=$((noops + 1))
      else
        echo "FIX=ran" >> "$round_dir/record"
        noops=0
      fi
      echo "FIX_COMMIT=$sha" >> "$round_dir/record"
      newexit="continue"
      # Two fix rounds that changed nothing cannot be moved by a third.
      [ "$noops" -ge 2 ] && newexit="findings"
      [ "$round" -ge "$rounds" ] && newexit="findings"
      write_state "$label" "$round" "$noops" "$newexit"
      echo "NODE_STATUS=done noops=$noops commit=$sha exit=$newexit"
      exit 0
    }

    [ "$PHASE" = "launch" ] && launch_phase "$round_dir" fix FIX \
      run-claude-prompt.sh "$session" "$prompt" "$noops"
    [ "$PHASE" = "watch" ] && watch_phase "$round_dir" fix FIX \
      run-claude-prompt.sh "$session" "$prompt" "$noops"

    out="$(obtain_reply "$round_dir" fix)"
    rc=$?
    if [ "$rc" -eq 70 ]; then
      echo "NODE_STATUS=failed:no-pre reason=post-ran-without-a-pre-that-asked-for-a-command"
      exit 0
    fi
    printf '%s\n' "$out" > "$round_dir/fix.out"
    complete_step "$rc"
    ;;

  report)
    rounds="$3"
    if [ ! -f "$STATE_ROOT/state" ]; then
      echo "NO STATE - the init node did not run"
      echo "RELAY_VERIFY_MISSING=unknown"
      echo "RELAY_VERIFY_RESULT=unverified"
      exit 0
    fi
    reap_abandoned record
    missing=0
    failed=0
    n=1
    while [ "$n" -le "$rounds" ]; do
      d="$STATE_ROOT/round-$n"
      if [ -d "$d" ]; then
        line="round $n:"
        # A node that never ran writes no line at all. Printing only the keys that are
        # present shows a short round as a complete one, so name the absent ones.
        for k in SIMPLIFY REVIEW CHECK FIX; do
          nlines="$(grep -cE "^$k=" "$d/record" 2>/dev/null)"
          v="$(recorded_status "$d" "$k")"
          if [ -z "$v" ]; then
            v="missing"
            missing=$((missing + 1))
          elif [ "${nlines:-0}" -gt 1 ]; then
            # More than one terminal line for one step in one round means the step was
            # entered more than once. The record cannot say which value is the truth, so
            # it proves nothing, and it must not be resolved by keeping the last write.
            v="conflict:$(sed -nE "s/^$k=(.*)$/\1/p" "$d/record" | paste -sd'/' -)"
            failed=$((failed + 1))
          else
            case "$v" in
              ran|skipped) ;;
              fix-noop) [ "$k" = "FIX" ] || failed=$((failed + 1)) ;;
              *) failed=$((failed + 1)) ;;
            esac
          fi
          line="$line $k=$v"
        done
        for k in VERDICT LABEL REASON RETRIED SIMPLIFY_COMMIT REVIEW_COMMIT FIX_COMMIT FIX_TRUNCATED; do
          v="$(recorded_status "$d" "$k")"
          [ -n "$v" ] && line="$line $k=$v"
        done
        echo "$line"
      fi
      n=$((n + 1))
    done
    cat "$STATE_ROOT/state"
    exitv="$(read_state EXIT)"
    labelv="$(read_state LABEL)"
    echo "RELAY_VERIFY_MISSING=$missing"
    echo "RELAY_VERIFY_FAILED=$failed"
    # `clean` needs two things: the last recorded label is clean, AND every step of every
    # round that started wrote a record. `missing` is a gate here, not a note printed beside
    # the result. A step that wrote no record proved nothing, so a run that holds one has not
    # earned a clean result.
    #
    # Before 4.33.0 this counter was computed, printed, and then dropped. Run wf_6f6f4d1a-4d3
    # reported `RELAY_VERIFY_RESULT=clean` next to `RELAY_VERIFY_MISSING=1`: its review step
    # ended its turn between `pre` and `post`, so `/code-review medium --fix` never ran, and
    # the branch was still reported verified. The report was not short of evidence. It had the
    # count on the line above and did not read it.
    passed_verdict=false
    if [ "$exitv" = "clean" ] && [ "$labelv" = "clean" ]; then passed_verdict=true; fi
    result="unverified"
    if [ "$passed_verdict" = true ] && [ "$missing" -eq 0 ] && [ "$failed" -eq 0 ]; then result="clean"; fi
    if [ "$exitv" = "findings" ]; then result="findings"; fi
    if [ "$exitv" = "continue" ] && [ "$labelv" = "findings" ]; then result="findings"; fi
    # Name the cause. A bare `unverified` under a passing verdict reads as a loop that broke,
    # when what happened is that a step is unaccounted for, or a step recorded its own failure.
    # The reason line prints only on the path this gate blocks, so it never appears next to a
    # result it does not explain.
    if [ "$passed_verdict" = true ]; then
      why=""
      [ "$missing" -gt 0 ] && why="incomplete-round steps=$missing"
      if [ "$failed" -gt 0 ]; then
        [ -n "$why" ] && why="$why "
        why="${why}failed-step steps=$failed"
      fi
      [ -n "$why" ] && echo "RELAY_VERIFY_REASON=$why"
    fi
    echo "RELAY_VERIFY_RESULT=$result"
    exit 0
    ;;

  *)
    usage
    echo "NODE_STATUS=failed:64 reason=unknown-kind:$kind"
    exit 64
    ;;
esac
