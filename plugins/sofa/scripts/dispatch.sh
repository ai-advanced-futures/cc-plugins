#!/usr/bin/env bash
# Start one background Claude Code session for one role of the team.
#
#   dispatch.sh --adlc <path to docs/adlc.md> --role <role> [--n <number>]
#               (--prompt-file <file> | --prompt <text>) [--resume <session id>]
#               [--cwd <main folder>] [--dry-run]
#
# The script reads the team prefix and the row of the role from the ADLC file,
# then runs `claude --bg` with the model, effort, compact value and output style
# of that row. It prints one line: `<session id> <session name>`.
# With --resume it runs only `claude --bg --resume <id> <prompt>`: the session
# keeps its saved options, and any other option starts a copy.
#
# The --settings value comes from `sofa-github settings`. When the state store has
# the GitHub App values of the team, the value also holds an env object, so each gh
# and each git of the session acts as the App (STORY-148). With no App values
# (exit 3 of sofa-github) the value is the output style alone, as before. Any other
# exit of sofa-github stops the script, so a team never starts as the person when
# the App setup is broken. DISPATCH_SOFA_GITHUB names another command in tests.
#
# Exit 0 when the session started (or on --dry-run), 1 when claude gave no
# session id, 2 on a bad argument, a bad ADLC file or a broken App setup.
set -euo pipefail

usage='usage: dispatch.sh --adlc <path to docs/adlc.md> --role <role> [--n <number>] (--prompt-file <file> | --prompt <text>) [--resume <session id>] [--cwd <main folder>] [--dry-run]'

fail() { echo "dispatch.sh: $*" >&2; exit 2; }

adlc='' role='' n='' prompt_file='' prompt='' resume='' cwd="$PWD" dry_run=0
while [ $# -gt 0 ]; do
  case "$1" in
    --adlc) adlc="${2:-}"; shift 2 ;;
    --role) role="${2:-}"; shift 2 ;;
    --n) n="${2:-}"; shift 2 ;;
    --prompt-file) prompt_file="${2:-}"; shift 2 ;;
    --prompt) prompt="${2:-}"; shift 2 ;;
    --resume) resume="${2:-}"; shift 2 ;;
    --cwd) cwd="${2:-}"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) echo "$usage"; exit 0 ;;
    *) fail "unknown argument: $1"$'\n'"$usage" ;;
  esac
done

[ -n "$adlc" ] || fail "--adlc is required"$'\n'"$usage"
[ -n "$role" ] || fail "--role is required"$'\n'"$usage"
[ -f "$adlc" ] || fail "ADLC file not found: $adlc"
if [ -n "$n" ] && ! [[ "$n" =~ ^[1-9][0-9]*$ ]]; then
  fail "--n must be a positive integer, got: $n"
fi
if [ -n "$prompt_file" ]; then
  [ -f "$prompt_file" ] || fail "prompt file not found: $prompt_file"
  # $(cat) drops the newlines at the end of the file. The read loop keeps the
  # text as it is in the file, with its newlines in the middle.
  prompt="$(cat "$prompt_file"; printf x)"; prompt="${prompt%x}"
fi
[ -n "$prompt" ] || fail "no prompt: give --prompt-file or --prompt"

# Section 1 row: | Team prefix | `<prefix>` (session names are ...) |
prefix="$(sed -n 's/^| *Team prefix *| *`\([^`]*\)`.*/\1/p' "$adlc" | head -1 || true)"
[ -n "$prefix" ] || fail "no team prefix in $adlc"

# Roles table: find the columns by header name, then the row of the role.
# Output: model, effort, compact, style, separated by the unit separator byte
# (\037). A tab would not work: `read` collapses two tabs around an empty cell
# into one, and the values shift. An absent column gives an empty field.
row="$(awk -F'|' -v role="$role" -v SEP=$'\037' '
  function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
  function cell(i) { if (i == 0) return ""; s = trim($i); gsub(/`/, "", s); return s }
  in_table && !/^\|/ { in_table = 0 }
  !in_table && /^\| *Role *\|/ {
    in_table = 1; m = e = c = o = 0
    for (i = 2; i <= NF; i++) {
      h = trim($i)
      if (h == "Model") m = i
      else if (h == "Effort") e = i
      else if (h == "Compact at") c = i
      else if (h == "Output style") o = i
    }
    # Section 1 has a "Tools per role" table that also starts with "Role".
    # Only the table with a Model column is the roles table.
    if (m == 0) in_table = 0
    next
  }
  in_table && cell(2) == role { print cell(m) SEP cell(e) SEP cell(c) SEP cell(o); exit }
' "$adlc" || true)"
[ -n "$row" ] || fail "role not in the roles table of $adlc: $role"
IFS=$'\037' read -r model effort compact style <<<"$row"
[ -n "$model" ] || fail "no Model value for role $role in $adlc"
[ -n "$compact" ] || fail "no Compact at value for role $role in $adlc"

name="$prefix-$role"
[ -z "$n" ] || name="$name-$n"

if [ -n "$resume" ]; then
  # A background session keeps its own saved options. Any other option with
  # --resume makes Claude Code start a copy under a new id ("Without flags,
  # the same command continues <id> itself"), so a resume passes none.
  cmd=(claude --bg --resume "$resume" "$prompt")
else
  cmd=(claude --bg -n "$name" --model "$model")
  if [ -n "$effort" ] && [ "$effort" != "—" ]; then cmd+=(--effort "$effort"); fi
  cmd+=(--autocompact "$compact")
  settings=""
  [ -z "$style" ] || settings="{\"outputStyle\":\"$style\"}"
  github_cmd="${DISPATCH_SOFA_GITHUB:-$(cd "$(dirname "$0")" && pwd)/sofa-github}"
  github_err="$(mktemp)"
  github_rc=0
  github_json="$( (cd "$cwd" 2>/dev/null || true; "$github_cmd" settings --output-style "$style") 2>"$github_err")" || github_rc=$?
  case "$github_rc" in
    0) settings="$github_json" ;;
    3) ;;
    *) github_msg="$(cat "$github_err")"; rm -f "$github_err"; fail "the GitHub App setup of the team is broken (sofa-github exit $github_rc): ${github_msg:-no message}" ;;
  esac
  rm -f "$github_err"
  [ -z "$settings" ] || cmd+=(--settings "$settings")
  cmd+=(--permission-mode bypassPermissions)
  cmd+=("$prompt")
fi

if [ "$dry_run" -eq 1 ]; then
  printf '%q\n' "${cmd[@]}"
  exit 0
fi

out="$(cd "$cwd" && "${cmd[@]}" 2>&1 || true)"

# `claude --bg` prints `  claude attach <id>    open in this terminal`.
# Some builds print `backgrounded · <id> · <name>` instead.
id="$(printf '%s\n' "$out" | sed -n 's/.*claude attach \([^[:space:]]*\).*/\1/p' | head -1 || true)"
if [ -z "$id" ]; then
  id="$(printf '%s\n' "$out" | sed -n 's/.*backgrounded[^[:alnum:]]*\([[:alnum:]_-]*\).*/\1/p' | head -1 || true)"
fi
if [ -z "$id" ]; then
  echo "dispatch.sh: claude gave no session id for $name:" >&2
  printf '%s\n' "$out" >&2
  exit 1
fi
echo "$id $name"
