#!/usr/bin/env bash
# relay: L3 Step 0 preflight — dependency gate, --verify/--rounds validation,
# --retro extraction, and engine/agent axis resolution for the six L3 commands
# (implement, refine, execute, drive, verify, diagnose). Extracted out of the
# six inline Step 0 bash blocks (issue #110): a Claude Code session isolated in
# a git worktree refuses an inline Bash command that carries `source`, `$(...)`,
# `case`, or a line starting `if`, and sourcing check-deps.sh under a shell that
# is not bash (e.g. zsh) makes its top-level `return` end the calling shell
# silently — a script called with `bash` avoids both.
#
# This script deliberately does NOT run `set -e`: the --verify and --retro
# probes are `printf ... | grep -qw ... && flag=1`; a false probe returns
# non-zero, and `set -e` would end the script right there with no output —
# the exact silent-failure shape this repo hunts.
# This script deliberately does NOT run `set -o pipefail` either: `grep -q`
# exits at its first match, the upstream `printf` then dies of SIGPIPE (141),
# and `pipefail` would promote that 141 into the pipeline's exit status — so a
# flag that WAS present would read as absent on a random fraction of runs. This
# is the documented flake in
# tests/unit/skill-structure/test_fidelity_check.py::test_l3_check_is_not_flaky.
#
# Invocation:
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/l3-preflight.sh" <command> "<raw $ARGUMENTS string>"
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/l3-preflight.sh" --axis-only <engine> <agent> [--source <label>]
# <command> is one of: implement | refine | execute | drive | verify | diagnose.
#
# Every `[relay] ...` line and every `KEY=value` line goes to stdout — the
# caller reads them from printed stdout, because this Bash call is a fresh
# process and nothing it exports survives to the next tool call. Errors keep
# the stream they use today: check-deps.sh and parse-engine-agent.sh write
# their own messages to stderr; this script's own validation errors (bad
# --rounds, missing oracle, session-tree rejection) go to the same stream the
# original inline block used.
#
# --non-interactive (5.0.0): no person is present. The script reads the flag
# before any check, prints RELAY_NON_INTERACTIVE=0|1 as the last KEY=value line
# of every command block, and on a failure under the flag prints one typed stop
# as the last stdout text: a relay.implement-result/1 block (scripts/result-block.sh)
# for implement, and a `[relay] non-interactive: stop <status>: <reason>` line for
# the other five. The stops of the sourced scripts use an EXIT trap, with the
# reason `preflight: <first error line>`. Without the flag, the output does not change.

usage() {
  cat >&2 <<'EOF'
usage: l3-preflight.sh <command> "<raw $ARGUMENTS string>"
       l3-preflight.sh --axis-only <engine> <agent> [--source <label>]

<command> is one of: implement | refine | execute | drive | verify | diagnose
EOF
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --non-interactive state and the typed stop (spec §8.3). These functions sit above
# the argument line because _ni_emit and _stop take positional arguments.
_ni=0
_ni_done=0
_ni_capturing=0
_ni_err=""
_ni_wt_note=0

# Print the one typed stop, once. implement prints a result block; the other five
# commands print one stop line.
_ni_emit() {
  [ "$_ni" = 1 ] || return 0
  [ "$_ni_done" = 1 ] && return 0
  _ni_done=1
  if [ "$COMMAND" = "implement" ]; then
    bash "$HERE/result-block.sh" --status "$1" --reason "$2"
  else
    echo "[relay] non-interactive: stop $1: $2"
  fi
}

# A check of this script failed: print the typed stop under the flag, then exit 1.
_stop() {
  _ni_emit "$1" "$2"
  exit 1
}

# Send the stderr of one sourced call to the temp file, so the EXIT trap can read
# its first error line. _ni_capture_end writes the file back to stderr.
_ni_capture_begin() {
  [ "$_ni" = 1 ] || return 0
  exec 9>&2 2>"$_ni_err"
  _ni_capturing=1
}

_ni_capture_end() {
  [ "$_ni_capturing" = 1 ] || return 0
  exec 2>&9 9>&-
  _ni_capturing=0
  cat "$_ni_err" >&2
  : > "$_ni_err"
}

# A sourced script ended the process. Read the reason while the capture is still
# open, write the captured text back to stderr, then print the typed stop.
_ni_on_exit() {
  _ni_rc=$?
  _ni_line=""
  if [ "$_ni_capturing" = 1 ]; then
    _ni_line="$(grep -m1 -E '^\[relay\] (error|BLOCKING)' "$_ni_err" 2>/dev/null)"
    [ -n "$_ni_line" ] || _ni_line="$(grep -m1 -v '^[[:space:]]*$' "$_ni_err" 2>/dev/null)"
  fi
  _ni_capture_end
  if [ "$_ni_rc" -ne 0 ] && [ "$_ni_done" != 1 ]; then
    [ -n "$_ni_line" ] || _ni_line="exit $_ni_rc"
    _ni_emit error "preflight: $_ni_line"
  fi
  rm -f "$_ni_err"
  exit "$_ni_rc"
}

# Q2: under the flag, no --worktree means `current` (run in place, never ask).
_ni_worktree_default() {
  [ "$_ni" = 1 ] || return 0
  [ -z "$_worktree" ] || return 0
  _worktree="current"
  _ni_wt_note=1
}

_print_ni_lines() {
  [ "$_ni" = 1 ] || return 0
  echo "[relay] non-interactive: on"
  if [ "$_ni_wt_note" = 1 ]; then
    echo "[relay] non-interactive: --worktree current"
  fi
}

# The acpx version floor. Only the acpx engine dispatches through the acpx CLI —
# in-session, bg-sessions, and session-tree never call it, so they do not pay the
# check. Runs after the axis is resolved, because the resolved engine is what
# decides whether acpx matters at all. scripts/acpx-floor.sh owns the number.
_acpx_floor_gate() {
    [ "${RELAY_ENGINE:-}" = "acpx" ] || return 0
    # shellcheck source=./acpx-floor.sh
    source "$HERE/acpx-floor.sh"
    _ni_capture_begin
    relay_acpx_floor_check >/dev/null || exit 1
    _ni_capture_end
}

# --axis-only: re-resolve the axis with two given literal values (the Step 0.25
# ask-when-unpinned re-resolution blocks). Still sources parse-engine-agent.sh
# so the enums and cross-arg invariants run; only the printed provenance label
# differs from what the parser itself would emit. `prompt` is a command-layer
# provenance value the parser never emits.
if [ "${1:-}" = "--axis-only" ]; then
  shift
  _ao_engine="${1:-}"; shift 2>/dev/null || true
  _ao_agent="${1:-}"; shift 2>/dev/null || true
  _ao_source="prompt"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --source) _ao_source="${2:-prompt}"; shift 2 ;;
      --source=*) _ao_source="${1#--source=}"; shift ;;
      *) shift ;;
    esac
  done
  source "$HERE/parse-engine-agent.sh" "$_ao_engine" "$_ao_agent" || exit 1
  _acpx_floor_gate
  echo "[relay] dispatch axis: engine=$RELAY_ENGINE agent=$RELAY_AGENT (source: $_ao_source)"
  echo "RELAY_ENGINE=$RELAY_ENGINE"
  echo "RELAY_AGENT=$RELAY_AGENT"
  echo "RELAY_AXIS_SOURCE=$_ao_source"
  echo "RELAY_IN_SESSION_TIERS=$RELAY_IN_SESSION_TIERS"
  exit 0
fi

COMMAND="${1:-}"
case "$COMMAND" in
  implement|refine|execute|drive|verify|diagnose) ;;
  *)
    usage
    exit 2
    ;;
esac
RAW_ARGS="${2-}"

# --non-interactive is read before any check, so a failure in a later check can
# still print the typed stop.
printf '%s' "$RAW_ARGS" | grep -qw -- '--non-interactive' && _ni=1
if [ "$_ni" = 1 ]; then
  _ni_err="$(mktemp "${TMPDIR:-/tmp}/relay-l3-preflight.XXXXXX")"
  trap _ni_on_exit EXIT
fi

# --spec is only for /relay:implement (spec §6.1).
if [ "$COMMAND" != "implement" ] && printf '%s' "$RAW_ARGS" | grep -qw -- '--spec'; then
  echo "[relay] error: --spec is only for /relay:implement" >&2
  _stop error "--spec is only for /relay:implement"
fi

# check-deps.sh ends in a top-level `return`, so it must be SOURCED, never
# executed. Run BEFORE the axis is resolved, exactly as every command body does
# today — its probe set is derived from $RELAY_AGENT, which is unset at this
# point, so it always probes the claude set here. Do not reorder this behind
# axis resolution: that would change which probe set runs.
_run_deps_gate() {
  _ni_capture_begin
  source "$HERE/check-deps.sh" || exit 1
  _ni_capture_end
}

# Sets _engine and _agent from RAW_ARGS's --engine/--agent flags. Repeated
# identically across implement/verify/refine/execute/drive, so this is the
# one place that regex lives.
_extract_engine_agent() {
  _engine="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--engine[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
  _agent="$(printf '%s' "$RAW_ARGS"  | sed -nE "s/.*--agent[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
}

# Sets _retro and _retro_target from RAW_ARGS's --retro flag. --retro is a
# post-run audit, not a dispatch axis: never forward it to
# parse-engine-agent.sh. Target = wf_<id> (trailing text ok) or bare 'last' at
# end of string; anything else is task/problem text: `--retro add a login
# form` must not read "add" as a run id.
_extract_retro() {
  _retro=0
  printf '%s' "$RAW_ARGS" | grep -qw -- '--retro' && _retro=1
  _retro_target="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--retro[ =]+(wf_[A-Za-z0-9._-]+)([ ].*)?$/\1/p; s/.*--retro[ =]+(last) *$/\1/p")"
}

# --worktree pre-answers the Step 0.5 isolation gate with `current`, a path, or a
# branch name. A bare --worktree, or one whose next word is another flag, is an
# error: the gate has nothing to resolve. Call this after _extract_retro — a
# retro-only run is read-only, so it announces that it ignores the value.
_extract_worktree() {
  _worktree="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--worktree[ =]+[\"']?([^\"' ]+).*/\1/p")"
  case "$_worktree" in --*) _worktree="" ;; esac
  if printf '%s' "$RAW_ARGS" | grep -qw -- '--worktree' && [ -z "$_worktree" ]; then
    echo "[relay] error: --worktree takes a value: current, a path, or a branch name" >&2
    _stop error "--worktree takes a value: current, a path, or a branch name"
  fi
  if [ "$_retro" = 1 ] && [ -n "$_retro_target" ] && [ -n "$_worktree" ]; then
    echo "[relay] --worktree ignored: retro is read-only"
  fi
}

# Printed only when the flag carried a value, so Step 0.5 can tell "no --worktree"
# from "--worktree with a value" without a sentinel.
_print_worktree() {
  if [ -n "$_worktree" ]; then
    echo "RELAY_WT_ARG=$_worktree"
  fi
}

# --spec <path> (implement only, spec §6.1). Sets _spec_path (absolute) and
# _closes_issue (the gh_issue value of the YAML frontmatter, or empty). A bare
# --spec, or one whose next word is another flag, is an error. So is a path that
# is not a regular file, and a gh_issue that is not a positive integer. YAML null
# (`null`, `~`) counts as empty. The script reads no other key: the
# caller checks lifecycle_state (D6).
_extract_spec() {
  _spec_path=""
  _closes_issue=""
  printf '%s' "$RAW_ARGS" | grep -qw -- '--spec' || return 0
  _spec_arg="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--spec[ =]+[\"']?([^\"' ]+).*/\1/p")"
  case "$_spec_arg" in --*) _spec_arg="" ;; esac
  if [ -z "$_spec_arg" ]; then
    echo "[relay] error: --spec takes a path to a spec file" >&2
    _stop error "--spec takes a path to a spec file"
  fi
  if [ ! -f "$_spec_arg" ]; then
    echo "[relay] error: spec-missing: $_spec_arg" >&2
    _stop error "spec-missing: $_spec_arg"
  fi
  _spec_path="$(cd "$(dirname "$_spec_arg")" && pwd -P)/$(basename "$_spec_arg")"
  _gh_issue=""
  if [ "$(head -n 1 "$_spec_path")" = "---" ]; then
    _gh_issue="$(awk 'NR == 1 { next } /^---[[:space:]]*$/ { exit } /^gh_issue:/ { sub(/^gh_issue:[[:space:]]*/, ""); print; exit }' "$_spec_path")"
  fi
  _gh_issue="$(printf '%s' "$_gh_issue" | sed -E "s/[[:space:]]+$//; s/^\"(.*)\"$/\1/; s/^'(.*)'$/\1/")"
  case "$_gh_issue" in null|Null|NULL|"~") _gh_issue="" ;; esac
  if [ -n "$_gh_issue" ]; then
    if printf '%s' "$_gh_issue" | grep -Eq '^[1-9][0-9]*$'; then
      _closes_issue="$_gh_issue"
    else
      echo "[relay] error: spec-gh-issue-invalid: $_gh_issue" >&2
      _stop error "spec-gh-issue-invalid: $_gh_issue"
    fi
  fi
}

# Validates $_rounds is an integer 1-5, exiting 1 with a command-prefixed
# message otherwise. Shared by implement (always, since --rounds now also
# sets the refine-spec and refine-plan ask points) and verify (always).
# Reads the caller's _rounds directly rather than taking a
# positional argument: the harness runs this whole script with zero
# positionals, and a bash positional-parameter reference here would trip the
# same regression guard the command bodies are held to
# (test_the_flag_is_parsed_from_arguments_never_from_positionals).
_validate_rounds() {
  case "$_rounds" in
    1|2|3|4|5) ;;
    *)
      echo "$COMMAND: --rounds takes an integer from 1 to 5 (got: $_rounds)"
      _stop error "--rounds takes an integer from 1 to 5 (got: $_rounds)"
      ;;
  esac
}

# Prints the four axis vars every command block ends its axis resolution
# with, identically. Reads them from the already-exported RELAY_* globals
# parse-engine-agent.sh set, so it takes no arguments.
_print_axis_vars() {
  echo "RELAY_ENGINE=$RELAY_ENGINE"
  echo "RELAY_AGENT=$RELAY_AGENT"
  echo "RELAY_AXIS_SOURCE=$RELAY_AXIS_SOURCE"
  echo "RELAY_IN_SESSION_TIERS=$RELAY_IN_SESSION_TIERS"
}

# session-tree v1 scope is /relay:implement only. Shared by refine, execute,
# and drive — each calls this after axis resolution, with $COMMAND already
# set to its own name.
_reject_session_tree() {
  if [ "$RELAY_ENGINE" = "session-tree" ]; then
    echo "[relay] error: engine=session-tree is not supported by /relay:$COMMAND (v1 scope: /relay:implement only)" >&2
    _stop error "engine=session-tree is not supported by /relay:$COMMAND (v1 scope: /relay:implement only)"
  fi
}

case "$COMMAND" in

  implement)
    _run_deps_gate
    _verify=0
    printf '%s' "$RAW_ARGS" | grep -qw -- '--verify' && _verify=1
    _rounds_flag="$(printf '%s' "$RAW_ARGS" | sed -nE 's/.*--rounds[ =]+([0-9]+).*/\1/p')"
    # 4.54.0: one value for three loops — the refine-spec ask point, the
    # refine-plan ask point, and the verify tail. --rounds is valid without
    # --verify, so resolve one value first, validate that assignment, then
    # export it. This arm no longer READS RELAY_VERIFY_ROUNDS; it only writes
    # it, so an inherited value can never beat --rounds or RELAY_ROUNDS.
    _rounds="${_rounds_flag:-${RELAY_ROUNDS:-3}}"
    _validate_rounds
    export RELAY_ROUNDS="$_rounds"
    if [ "$_verify" -eq 1 ]; then
      export RELAY_VERIFY_ROUNDS="$_rounds"
    else
      export RELAY_VERIFY_ROUNDS=""
    fi
    echo "[relay] implement: verify-loop enabled=$_verify rounds=$_rounds"
    _extract_engine_agent
    _extract_retro
    _extract_worktree
    _ni_worktree_default
    _extract_spec
    # --fixes-model / --verification-model replace the model of every role that carries the
    # matching `category:` in bindings/presets.yaml. They reach the parser as environment
    # variables, not as positionals, so the extras check below still sees a stray argument.
    export RELAY_FIXES_MODEL_FLAG="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--fixes-model[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
    export RELAY_VERIFICATION_MODEL_FLAG="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--verification-model[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
    # This command dispatches leaf work out of this session by default. The two exports move
    # the parser's "no flag and no pin" layer off `in-session`; a flag or a `.claude/relay.json`
    # pin still beats them, and the axis line still prints `source: default`.
    export RELAY_DEFAULT_ENGINE="acpx"
    export RELAY_DEFAULT_AGENT="claude"
    _ni_capture_begin
    source "$HERE/parse-engine-agent.sh" "$_engine" "$_agent" || exit 1
    _ni_capture_end
    _acpx_floor_gate
    echo "[relay] dispatch axis: engine=$RELAY_ENGINE agent=$RELAY_AGENT (source: $RELAY_AXIS_SOURCE)"
    echo "[relay] model overrides: fixes=${RELAY_FIXES_MODEL:-<per-role pin>} verification=${RELAY_VERIFICATION_MODEL:-<per-role pin>} ($RELAY_MODEL_SOURCE)"
    echo "[relay] retro: enabled=$_retro target=${_retro_target:-<this run>}"
    # Q7, D9: session-tree needs a person to answer escalations. Stop before any work.
    if [ "$_ni" = 1 ] && [ "$RELAY_ENGINE" = "session-tree" ]; then
      echo "[relay] error: engine=session-tree needs a person to answer escalations, and --non-interactive says no person is present" >&2
      _stop blocked "non-interactive: engine session-tree needs a person to answer escalations; pin in-session or acpx"
    fi
    # --keep-sessions keeps the run's background sessions alive instead of the end-of-run cleanup.
    _keep_sessions=0
    printf '%s' "$RAW_ARGS" | grep -qw -- '--keep-sessions' && _keep_sessions=1
    if [ "$_keep_sessions" -eq 1 ]; then
      case "$RELAY_ENGINE" in
        bg-sessions|session-tree) ;;
        *)
          echo "implement: --keep-sessions keeps the background sessions a run created, and engine '$RELAY_ENGINE' creates none. Use --engine bg-sessions or --engine session-tree, or drop --keep-sessions."
          _stop error "--keep-sessions keeps the background sessions a run created, and engine '$RELAY_ENGINE' creates none"
          ;;
      esac
    fi
    _print_ni_lines
    _print_axis_vars
    echo "RELAY_FIXES_MODEL=$RELAY_FIXES_MODEL"
    echo "RELAY_VERIFICATION_MODEL=$RELAY_VERIFICATION_MODEL"
    echo "RELAY_MODEL_SOURCE=$RELAY_MODEL_SOURCE"
    echo "RELAY_VERIFY=$_verify"
    echo "RELAY_VERIFY_ROUNDS=${RELAY_VERIFY_ROUNDS:-}"
    echo "RELAY_ROUNDS=$RELAY_ROUNDS"
    echo "RELAY_RETRO=$_retro"
    echo "RELAY_RETRO_TARGET=${_retro_target:-}"
    _print_worktree
    echo "RELAY_KEEP_SESSIONS=$_keep_sessions"
    echo "RELAY_SPEC_PATH=$_spec_path"
    echo "RELAY_CLOSES_ISSUE=$_closes_issue"
    echo "RELAY_NON_INTERACTIVE=$_ni"
    ;;

  verify)
    _run_deps_gate
    _rounds="$(printf '%s' "$RAW_ARGS" | sed -nE 's/.*--rounds[ =]+([0-9]+).*/\1/p')"
    _rounds="${_rounds:-${RELAY_VERIFY_ROUNDS:-3}}"
    _validate_rounds
    export RELAY_VERIFY_ROUNDS="$_rounds"
    echo "[relay] verify: round cap = $RELAY_VERIFY_ROUNDS"
    _extract_engine_agent
    # This command dispatches leaf work out of this session by default. The two exports move
    # the parser's "no flag and no pin" layer off `in-session`; a flag or a `.claude/relay.json`
    # pin still beats them, and the axis line still prints `source: default`.
    export RELAY_DEFAULT_ENGINE="acpx"
    export RELAY_DEFAULT_AGENT="claude"
    _ni_capture_begin
    source "$HERE/parse-engine-agent.sh" "$_engine" "$_agent" || exit 1
    _ni_capture_end
    _acpx_floor_gate
    echo "[relay] dispatch axis: engine=$RELAY_ENGINE agent=$RELAY_AGENT (source: $RELAY_AXIS_SOURCE)"
    # Only in-session and acpx carry this loop's deadline, state directory, and commit per round.
    case "$RELAY_ENGINE" in
      in-session|acpx) ;;
      *)
        echo "[relay] error: engine=$RELAY_ENGINE is not supported by /relay:verify (supported: in-session | acpx)" >&2
        _stop error "engine=$RELAY_ENGINE is not supported by /relay:verify (supported: in-session | acpx)"
        ;;
    esac
    export RELAY_VERIFY_ENGINE="$RELAY_ENGINE"
    _print_ni_lines
    _print_axis_vars
    echo "RELAY_VERIFY=1"
    echo "RELAY_VERIFY_ROUNDS=$RELAY_VERIFY_ROUNDS"
    echo "RELAY_RETRO=0"
    echo "RELAY_RETRO_TARGET="
    echo "RELAY_VERIFY_ENGINE=$RELAY_VERIFY_ENGINE"
    echo "RELAY_NON_INTERACTIVE=$_ni"
    ;;

  refine|execute)
    _run_deps_gate
    _extract_engine_agent
    _extract_retro
    _extract_worktree
    _ni_worktree_default
    # --fixes-model / --verification-model replace the model of every role that carries the
    # matching `category:` in bindings/presets.yaml. They reach the parser as environment
    # variables, not as positionals, so the extras check below still sees a stray argument.
    export RELAY_FIXES_MODEL_FLAG="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--fixes-model[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
    export RELAY_VERIFICATION_MODEL_FLAG="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--verification-model[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
    _ni_capture_begin
    source "$HERE/parse-engine-agent.sh" "$_engine" "$_agent" || exit 1
    _ni_capture_end
    _acpx_floor_gate
    echo "[relay] dispatch axis: engine=$RELAY_ENGINE agent=$RELAY_AGENT (source: $RELAY_AXIS_SOURCE)"
    echo "[relay] model overrides: fixes=${RELAY_FIXES_MODEL:-<per-role pin>} verification=${RELAY_VERIFICATION_MODEL:-<per-role pin>} ($RELAY_MODEL_SOURCE)"
    echo "[relay] retro: enabled=$_retro target=${_retro_target:-<this run>}"
    _reject_session_tree
    _print_ni_lines
    _print_axis_vars
    echo "RELAY_FIXES_MODEL=$RELAY_FIXES_MODEL"
    echo "RELAY_VERIFICATION_MODEL=$RELAY_VERIFICATION_MODEL"
    echo "RELAY_MODEL_SOURCE=$RELAY_MODEL_SOURCE"
    echo "RELAY_VERIFY=0"
    echo "RELAY_VERIFY_ROUNDS="
    echo "RELAY_RETRO=$_retro"
    echo "RELAY_RETRO_TARGET=${_retro_target:-}"
    _print_worktree
    echo "RELAY_NON_INTERACTIVE=$_ni"
    ;;

  drive)
    _run_deps_gate
    _extract_engine_agent
    _resume=0
    printf '%s' "$RAW_ARGS" | grep -qw -- '--resume' && _resume=1
    # Oracle = the lone token left after stripping the flags and their values.
    # Strip only the whole `--resume` word so `--resumed` survives.
    _oracle="$(printf '%s' "$RAW_ARGS" \
      | sed -E "s/--engine[ =]+[\"']?[A-Za-z-]+[\"']?//g; s/--agent[ =]+[\"']?[A-Za-z-]+[\"']?//g; s/--fixes-model[ =]+[\"']?[A-Za-z-]+[\"']?//g; s/--verification-model[ =]+[\"']?[A-Za-z-]+[\"']?//g; s/--retro[ =]+(wf_[A-Za-z0-9._-]+|last)//g; s/--worktree[ =]+[\"']?[^\"' ]+[\"']?//g; s/(^| )--retro( |\$)/ /g; s/(^| )--resume( |\$)/ /g; s/(^| )--non-interactive( |\$)/ /g" \
      | tr -s ' ' | sed -E 's/^ +//; s/ +$//')"
    _extract_retro
    _extract_worktree
    _ni_worktree_default
    # --fixes-model / --verification-model replace the model of every role that carries the
    # matching `category:` in bindings/presets.yaml. They reach the parser as environment
    # variables, not as positionals, so the extras check below still sees a stray argument.
    # The oracle strip above removes both flags, so neither one can be read as the oracle path.
    export RELAY_FIXES_MODEL_FLAG="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--fixes-model[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
    export RELAY_VERIFICATION_MODEL_FLAG="$(printf '%s' "$RAW_ARGS" | sed -nE "s/.*--verification-model[ =]+[\"']?([A-Za-z-]+).*/\1/p")"
    _ni_capture_begin
    source "$HERE/parse-engine-agent.sh" "$_engine" "$_agent" || exit 1
    _ni_capture_end
    _acpx_floor_gate
    echo "[relay] dispatch axis: engine=$RELAY_ENGINE agent=$RELAY_AGENT resume=$_resume (source: $RELAY_AXIS_SOURCE)"
    echo "[relay] model overrides: fixes=${RELAY_FIXES_MODEL:-<per-role pin>} verification=${RELAY_VERIFICATION_MODEL:-<per-role pin>} ($RELAY_MODEL_SOURCE)"
    echo "[relay] retro: enabled=$_retro target=${_retro_target:-<this run>}"
    _reject_session_tree
    export RELAY_DRIVE_RESUME="$_resume"
    export RELAY_DRIVE_ORACLE="$_oracle"
    # Retro-only mode generates no Workflow and needs no oracle, so a bare `--retro last` must pass here.
    if [ -z "$RELAY_DRIVE_ORACLE" ] && [ -z "$_retro_target" ]; then
      echo "drive: <oracle-file> is required"
      _stop error "drive: <oracle-file> is required"
    fi
    _print_ni_lines
    _print_axis_vars
    echo "RELAY_FIXES_MODEL=$RELAY_FIXES_MODEL"
    echo "RELAY_VERIFICATION_MODEL=$RELAY_VERIFICATION_MODEL"
    echo "RELAY_MODEL_SOURCE=$RELAY_MODEL_SOURCE"
    echo "RELAY_VERIFY=0"
    echo "RELAY_VERIFY_ROUNDS="
    echo "RELAY_RETRO=$_retro"
    echo "RELAY_RETRO_TARGET=${_retro_target:-}"
    _print_worktree
    echo "RELAY_DRIVE_RESUME=$RELAY_DRIVE_RESUME"
    echo "RELAY_DRIVE_ORACLE=$RELAY_DRIVE_ORACLE"
    echo "RELAY_NON_INTERACTIVE=$_ni"
    ;;

  diagnose)
    # This command has no engine/agent axis and no dependency gate — matching
    # commands/diagnose.md today, which sources neither check-deps.sh nor
    # parse-engine-agent.sh.
    _extract_retro
    echo "[relay] retro: enabled=$_retro target=${_retro_target:-<this run>}"
    _print_ni_lines
    echo "RELAY_RETRO=$_retro"
    echo "RELAY_RETRO_TARGET=${_retro_target:-}"
    echo "RELAY_NON_INTERACTIVE=$_ni"
    ;;

esac

exit 0
