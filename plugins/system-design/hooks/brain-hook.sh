#!/usr/bin/env bash
# brain-hook.sh: the PostToolUse hook of a brain (standard section 9).
#
# hooks/brain-hook.conf names GRAPHS (the graph names of the brain in
# .claude/knowledge.json), SAVE_SCRIPT (the save script in scripts/), and
# PYTHON_VAR (the variable that names the Python; the tests set it). A brain
# with its own config file also sets BRAIN_CONFIG (the file) and
# BRAIN_CONFIG_KEY (the key of the bundle folder). That value wins.
#
# For a Write or an Edit of a file in a bundle of the brain, or for a Bash
# command that runs the save script, run three steps in this order:
#   1. <save script> regen
#   2. <save script> check                                      (the brain check)
#   3. knowledge.py check --graph <each graph> --cache-only     (the general check)
# Claude Code runs the hooks of one event in parallel, so one hook does the
# three steps. Any other tool call ends the hook at once.
#
# A Bash command runs the save script when the script is in command position:
# at the start of the command, after ; & | ( $( or a new line, or after
# variable assignments and uv run, python, python3, bash, env, or exec. A
# command that only names the script (grep, sed, cat, a PR text) does nothing.
# Text in quotes is not a command: before the match, the hook removes each
# quoted span (see strip_quoted), so a page fact in a quoted argument, such as
# "(prd.py github pull ...)", is not a run. The hook also drops each heredoc body
# and each # comment (a # at the start of a word, up to the end of the line).
# Known limits. The hook does nothing for these, though each one runs the script:
# a script path in quotes, a script that a variable holds (G="uv run .../prd.py";
# $G regen), a command in "$(...)" inside double quotes, and a script that a
# heredoc body feeds to a shell. An apostrophe outside quotes opens a span, so the
# text up to the next apostrophe is not scanned.
# The root of a Bash command is the git root of the session folder (the cwd
# of the hook input), so a session in a worktree checks that worktree. A root
# with no bundle of the brain does nothing.
#
#   no finding                    exit 0, no output
#   warnings or SKIP lines only   exit 0, the lines as additionalContext
#   an error, or a failed step    exit 2, the output on stderr
#
# The same file ships in system-design, architecture, and product. Change all copies together.
set -uo pipefail

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
# shellcheck source=/dev/null
. "$plugin_root/hooks/brain-hook.conf"

json_get() {
  if command -v jq >/dev/null 2>&1; then
    jq -r "$1 // empty" 2>/dev/null
  else
    python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print($2 or '')
except Exception:
    print('')
" 2>/dev/null
  fi
}

# Print the folder of each bundle of the brain that exists under the root $1.
bundle_dirs() {
  local root="$1" registry="$1/.claude/knowledge.json" brain_config="${BRAIN_CONFIG:+$1/$BRAIN_CONFIG}"
  local graph bundle
  for graph in $GRAPHS; do
    bundle=""
    # The brain config wins over the registry (standard section 5).
    if [ -n "$brain_config" ] && [ -f "$brain_config" ]; then
      bundle="$(json_get ".$BRAIN_CONFIG_KEY" "d.get('$BRAIN_CONFIG_KEY')" < "$brain_config")"
    fi
    if [ -z "$bundle" ] && [ -f "$registry" ]; then
      bundle="$(json_get ".graphs[\"$graph\"].path" "d.get('graphs', {}).get('$graph', {}).get('path')" < "$registry")"
    fi
    [ -n "$bundle" ] || continue
    (cd "$root/$bundle" 2>/dev/null && pwd -P) || continue
  done
}

# The awk program of strip_quoted. It reads the command one time, from left to
# right, so the time is linear in the length of the command (a loop in bash is
# not: ${s:i:1} costs O(i)). At each position, the first quote mark opens a span,
# and the same mark closes it. A backslash hides the next character, except
# inside single quotes. So an apostrophe inside a double-quoted text does not
# open a span. Do not use 2 passes (first '...', then "..."): the first pass
# would take that apostrophe. The program also drops the body of each heredoc
# (<<WORD, <<-WORD, <<'WORD', <<"WORD"), because a body is text and not a command.
# It also stops a line at a # that starts a word, as a shell does.
# "\047" is an apostrophe, because this text is inside single quotes.
STRIP_AWK='
function heredoc(   rest, word) {
  rest = substr(line, i + 2, 200)
  if (!match(rest, "^-?[ \t]*[\"\047\\\\]?[A-Za-z_][A-Za-z0-9_]*")) return 0
  word = substr(rest, 1, RLENGTH)
  nd++; dash[nd] = (substr(word, 1, 1) == "-")
  sub("^-?[ \t]*[\"\047\\\\]?", "", word); delim[nd] = word
  i += 2 + RLENGTH
  if (substr(line, i, 1) == "\047" || substr(line, i, 1) == "\"") i++
  return 1
}
{
  line = $0; len = length(line); i = 1; nd = 0
  while (i <= len) {
    c = substr(line, i, 1)
    if (q != "") {
      if (c == "\\" && q == "\"") { i += 2; continue }
      if (c == q) q = ""
    } else if (c == "\\") {
      printf "%s", substr(line, i, 2); i += 2; continue
    } else if (c == "#" && (i == 1 || substr(line, i - 1, 1) ~ /[ \t;&|(]/)) {
      break
    } else if (c == "\047" || c == "\"") {
      q = c
    } else if (c == "<" && substr(line, i, 2) == "<<" && substr(line, i + 2, 1) != "<" && heredoc()) {
      continue
    } else {
      printf "%s", c
    }
    i++
  }
  printf "\n"
  for (k = 1; k <= nd; k++)
    while ((getline body) > 0) {
      if (dash[k]) sub(/^\t+/, "", body)
      if (body == delim[k]) break
    }
}'

# Print the Bash command $1 with each quoted span and each heredoc body removed.
strip_quoted() {
  printf '%s' "$1" | LC_ALL=C awk "$STRIP_AWK"
}

# Exit 0 when the Bash command $1 runs the save script.
runs_save_script() {
  case "$1" in *"$SAVE_SCRIPT"*) ;; *) return 1 ;; esac # the common case: no quote scan
  local script="${SAVE_SCRIPT//./\\.}"
  local assign='([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*'
  local runner='((uv[[:space:]]+run|python3?|bash|env|exec)([[:space:]]+-[^[:space:]]+)*[[:space:]]+)*'
  # One command for each line: split at ; & | ( and the new line, then match each
  # line at its start. Each step is linear in the length of the command (one big
  # regex with a search from each position is not). grep reads all its input, so
  # pipefail sees no SIGPIPE.
  strip_quoted "$1" | tr ';&|(' '\n\n\n\n' |
    LC_ALL=C grep -E "^[[:space:]]*${assign}${runner}[^[:space:]]*${script}([[:space:])]|\$)" >/dev/null
}

input="$(cat)"
tool="$(printf '%s' "$input" | json_get '.tool_name' 'd.get("tool_name")')"
save="$plugin_root/scripts/$SAVE_SCRIPT"

case "$tool" in
  Bash)
    command="$(printf '%s' "$input" | json_get '.tool_input.command' 'd.get("tool_input", {}).get("command")')"
    runs_save_script "$command" || exit 0
    cwd="$(printf '%s' "$input" | json_get '.cwd' 'd.get("cwd")')"
    root="$(git -C "${cwd:-${CLAUDE_PROJECT_DIR:-$PWD}}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
    [ -n "$(bundle_dirs "$root")" ] || exit 0
    ;;
  Write|Edit)
    path="$(printf '%s' "$input" | json_get '.tool_input.file_path' 'd.get("tool_input", {}).get("file_path")')"
    [ -n "$path" ] || exit 0
    case "$path" in /*) ;; *) path="$PWD/$path" ;; esac
    dir="$(cd "$(dirname "$path")" 2>/dev/null && pwd -P)" || exit 0
    root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
    inside=""
    while IFS= read -r bundle_dir; do
      case "$dir/" in "$bundle_dir/"*) inside="yes" ;; esac
    done < <(bundle_dirs "$root")
    [ -n "$inside" ] || exit 0
    ;;
  *) exit 0 ;;
esac

python_bin="${!PYTHON_VAR:-}"
run() {
  if [ -n "$python_bin" ]; then "$python_bin" "$@"
  elif command -v uv >/dev/null 2>&1; then uv run --quiet "$@"
  else python3 "$@"
  fi
}

if ! out="$(run "$save" --root "$root" regen 2>&1)"; then
  printf '%s hook: regen failed:\n%s\n' "$SAVE_SCRIPT" "$out" >&2
  exit 2
fi
if ! brain="$(run "$save" --root "$root" check 2>&1)"; then
  printf '%s hook: the brain check found errors. Correct the page:\n%s\n' "$SAVE_SCRIPT" "$brain" >&2
  exit 2
fi
knowledge="$(bash "$plugin_root/scripts/probe-plugin.sh" knowledge scripts/knowledge.py)"
if [ -z "$knowledge" ]; then
  general="SKIP: K-general (the knowledge plugin is not installed, so the general check did not run)"
else
  args=()
  for graph in $GRAPHS; do args+=(--graph "$graph"); done
  if ! general="$(run "$knowledge/scripts/knowledge.py" --root "$root" check "${args[@]}" --cache-only 2>&1)"; then
    printf '%s hook: the general check found errors. Correct the page:\n%s\n' "$SAVE_SCRIPT" "$general" >&2
    exit 2
  fi
fi
notes="$(printf '%s\n%s\n' "$brain" "$general" | grep -E '^(WARN|SKIP): ' || true)"
[ -n "$notes" ] || exit 0
context="The checks of $GRAPHS gave notes after the change:
$notes"
if command -v jq >/dev/null 2>&1; then
  jq -cn --arg c "$context" '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $c}}'
else
  python3 -c '
import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": sys.argv[1]}}))
' "$context"
fi
exit 0
