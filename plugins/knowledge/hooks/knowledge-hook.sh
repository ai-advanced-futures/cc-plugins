#!/usr/bin/env bash
# knowledge-hook.sh: the PostToolUse hook of the knowledge plugin (standard section 9).
#
# For a Write or an Edit of a file in the knowledge graph, or for a Bash
# command that runs knowledge_graph.py, run three steps in this order:
#   1. knowledge_graph.py regen
#   2. knowledge_graph.py check                            (the brain check)
#   3. knowledge.py check --graph knowledge --cache-only   (the general check)
# Claude Code runs the hooks of one event in parallel, so one hook does the
# three steps. Any other tool call ends the hook at once, with no Python start.
#
# A Bash command runs knowledge_graph.py when the script is in command position:
# at the start of the command, after ; & | ( $( or a new line, or after
# variable assignments and uv run, python, python3, bash, env, or exec. A
# command that only names the script (grep, sed, cat, a PR text) does nothing,
# and text in quotes is not a command (see strip_quoted). The hook also drops
# each heredoc body and each # comment (a # at the start of a word, up to the end
# of the line).
# Known limits. The hook does nothing for these, though each one runs the script:
# a script path in quotes, a script that a variable holds
# (G="uv run .../knowledge_graph.py"; $G new ...), a command in "$(...)" inside
# double quotes, and a script that a heredoc body feeds to a shell. An apostrophe
# outside quotes opens a span, so the text up to the next apostrophe is not scanned.
#
# The hook runs the steps only when a file of the graph changed. The changed
# files are the files in the change list of knowledge_graph.py
# (<git dir>/knowledge-changed, one path for each line), and the file of an Edit
# or a Write. The hook takes the list with one mv, so a second hook run never
# reads it twice. A list with no changed file ends the hook with no output.
# When a Bash command leaves no list (a run that could not write it), the hook
# checks everything and shows every warning, as it did before the list.
# The hook keeps the K-size warnings of the changed files, and it counts the others.
#
#   no finding                    exit 0, no output
#   warnings or SKIP lines only   exit 0, the lines as additionalContext
#   an error, or a failed step    exit 2, the output on stderr
#
# KNOWLEDGE_PYTHON names the Python to use. The tests set it. When it is not
# set, the hook uses `uv run`, or python3 when uv is absent.
set -uo pipefail

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
SAVE_SCRIPT=knowledge_graph.py
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
plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
save="$plugin_root/scripts/knowledge_graph.py"
general="$plugin_root/scripts/knowledge.py"

changed=""
case "$tool" in
  Bash)
    command="$(printf '%s' "$input" | json_get '.tool_input.command' 'd.get("tool_input", {}).get("command")')"
    runs_save_script "$command" || exit 0
    root="$(git -C "${CLAUDE_PROJECT_DIR:-$PWD}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
    [ -f "$root/.claude/knowledge.json" ] || exit 0
    ;;
  Write|Edit)
    path="$(printf '%s' "$input" | json_get '.tool_input.file_path' 'd.get("tool_input", {}).get("file_path")')"
    [ -n "$path" ] || exit 0
    case "$path" in /*) ;; *) path="$PWD/$path" ;; esac
    dir="$(cd "$(dirname "$path")" 2>/dev/null && pwd -P)" || exit 0
    root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
    [ -f "$root/.claude/knowledge.json" ] || exit 0
    ;;
  *) exit 0 ;;
esac
bundle="$(json_get '.graphs.knowledge.path' 'd.get("graphs", {}).get("knowledge", {}).get("path")' < "$root/.claude/knowledge.json")"
[ -n "$bundle" ] || exit 0
bundle_dir="$(cd "$root/$bundle" 2>/dev/null && pwd -P)" || exit 0
if [ "$tool" != Bash ]; then
  case "$dir/" in "$bundle_dir/"*) ;; *) exit 0 ;; esac
  changed="${dir#"$root"}/$(basename "$path")"
  changed="${changed#/}"
fi

# Take the change list. After the mv, no other hook run can read it.
list="$(git -C "$root" rev-parse --absolute-git-dir 2>/dev/null)/knowledge-changed"
took_list=0
if [ -f "$list" ] && mv "$list" "$list.$$" 2>/dev/null; then
  took_list=1
  changed="$(printf '%s\n%s\n' "$changed" "$(cat "$list.$$")")"
  rm -f "$list.$$"
fi
changed="$(printf '%s\n' "$changed" | sed '/^$/d')"
# A list with no changed file means that the command changed nothing.
# No list at all means that no run wrote one, so check everything.
if [ -z "$changed" ] && [ "$took_list" = 1 ]; then exit 0; fi

run() {
  if [ -n "${KNOWLEDGE_PYTHON:-}" ]; then "$KNOWLEDGE_PYTHON" "$@"
  elif command -v uv >/dev/null 2>&1; then uv run --quiet "$@"
  else python3 "$@"
  fi
}

# No step of the hook writes a list, so a list never holds the writes of the hook.
export KNOWLEDGE_NO_CHANGE_LIST=1
if ! out="$(run "$save" --root "$root" regen 2>&1)"; then
  printf 'knowledge hook: knowledge_graph.py regen failed:\n%s\n' "$out" >&2
  exit 2
fi
if ! brain="$(run "$save" --root "$root" check 2>&1)"; then
  printf 'knowledge hook: the brain check found errors. Correct the page:\n%s\n' "$brain" >&2
  exit 2
fi
if ! general_out="$(run "$general" --root "$root" check --graph knowledge --cache-only 2>&1)"; then
  printf 'knowledge hook: the general check found errors. Correct the page:\n%s\n' "$general_out" >&2
  exit 2
fi
# Keep a K-size warning only for a changed file. Count the others.
notes=""
skipped=0
while IFS= read -r line; do
  case "$line" in
    "WARN: "*"[K-size]"*)
      file="$(printf '%s' "$line" | sed -E 's/^WARN: (.*):[0-9]+ \[K-size\].*/\1/')"
      if [ -z "$changed" ] || printf '%s\n' "$changed" | grep -Fxq -- "$file"; then notes="$notes$line"$'\n'
      else skipped=$((skipped + 1)); fi
      ;;
    "WARN: "*|"SKIP: "*) notes="$notes$line"$'\n' ;;
  esac
done <<EOF_CHECKS
$(printf '%s\n%s\n' "$brain" "$general_out")
EOF_CHECKS
notes="${notes%$'\n'}"
if [ "$skipped" -gt 0 ]; then
  notes="${notes:+$notes$'\n'}K-size warnings on pages that did not change: $skipped."
fi
[ -n "$notes" ] || exit 0
context="The knowledge checks gave notes after the change:
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
