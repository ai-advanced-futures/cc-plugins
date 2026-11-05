#!/usr/bin/env bash
# regen-hook.sh: the PostToolUse hook of the business-domain plugin, for Write, Edit,
# and Bash.
#
# After an edit of a file inside the domain bundle, or a Bash command that
# runs `ddd.py`, run three steps in this order:
#   1. ddd.py regen
#   2. ddd.py check                                        (the ddd check)
#   3. knowledge.py check --graph ddd --cache-only     (the general check)
# so the LINKS blocks, the indexes, and links.tsv agree with the frontmatter
# again, and the general check reports any cross-graph finding. The hook
# does not undo or block the edit: a PostToolUse hook runs after the tool.
#
# A Bash command runs ddd.py when the script is in command position: at the
# start of the command, after ; & | ( $( or a new line, or after variable
# assignments and uv run, python, python3, bash, env, or exec. A command that
# only names the script (grep, sed, cat, a PR text) does nothing, and text in
# quotes is not a command (see strip_quoted). The hook also drops each heredoc
# body and each # comment (a # at the start of a word, up to the end of the line).
# Known limits. The hook does nothing for these, though each one runs the script:
# a script path in quotes, a script that a variable holds
# (D="uv run .../ddd.py"; $D new ...), a command in "$(...)" inside double
# quotes, and a script that a heredoc body feeds to a shell. An apostrophe outside
# quotes opens a span, so the text up to the next apostrophe is not scanned.
#
# Exit 0 at once when the edited file is not inside a bundle, or the Bash
# command does not run `ddd.py`. This hook runs after each Write, Edit, and
# Bash call in each repository where the plugin is installed, so that path
# starts no Python import.
#
#   check gives no finding            exit 0, no output
#   check gives warnings or SKIP only exit 0, the lines as additionalContext
#   check gives an error              exit 2, the check output on stderr
#   regen fails, or check exit 2      exit 2, the output on stderr
#
# DDD_PYTHON names the Python to run ddd.py and knowledge.py with. The tests
# set it. When it is not set, the hook uses `uv run`, or python3 when uv is
# absent.
set -uo pipefail

# json_get JQ_FILTER PYTHON_EXPR: one string of the JSON on stdin, or empty.
# PYTHON_EXPR reads the parsed JSON as `d`. python3 is used when jq is absent.
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
SAVE_SCRIPT=ddd.py
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
case "$tool" in
  Bash)
    command="$(printf '%s' "$input" | json_get '.tool_input.command' 'd.get("tool_input", {}).get("command")')"
    runs_save_script "$command" || exit 0
    root="$(git -C "${CLAUDE_PROJECT_DIR:-$PWD}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
    [ -f "$root/.claude/ddd.json" ] || exit 0
    path="$root/.claude/ddd.json"
    ;;
  *)
    path="$(printf '%s' "$input" | json_get '.tool_input.file_path' 'd.get("tool_input", {}).get("file_path")')"
    [ -n "$path" ] || exit 0
    case "$path" in
      /*) ;;
      *) path="$PWD/$path" ;;
    esac

    # The physical directory of the file, so a symlink in the path cannot
    # hide that the file is inside the bundle.
    dir="$(cd "$(dirname "$path")" 2>/dev/null && pwd -P)" || exit 0
    root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
    config="$root/.claude/ddd.json"
    [ -f "$config" ] || exit 0

    bundle="$(json_get '.dir' 'd.get("dir")' < "$config")"
    [ -n "$bundle" ] || exit 0
    # The physical bundle directory too, so `./docs/domain`, `docs//domain`,
    # or a symlink in the configured path gives the same text as $dir.
    bundle_dir="$(cd "$root/$bundle" 2>/dev/null && pwd -P)" || exit 0
    case "$dir/" in
      "$bundle_dir/"*) ;;
      *) exit 0 ;;
    esac
    ;;
esac

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
script="$plugin_root/scripts/ddd.py"
if [ -n "${DDD_PYTHON:-}" ]; then
  runner=("$DDD_PYTHON" "$script")
elif command -v uv >/dev/null 2>&1; then
  runner=(uv run --quiet "$script")
else
  runner=(python3 "$script")
fi

if ! out="$("${runner[@]}" --root "$root" regen 2>&1)"; then
  printf 'business-domain hook: `ddd.py regen` failed after the edit of %s:\n%s\n' "$path" "$out" >&2
  exit 2
fi

out="$("${runner[@]}" --root "$root" check 2>&1)"
rc=$?
if [ "$rc" -ne 0 ]; then
  printf 'business-domain hook: `ddd.py check` found errors after the edit of %s. Correct the page:\n%s\n' "$path" "$out" >&2
  exit 2
fi

knowledge="$(bash "$plugin_root/scripts/probe-plugin.sh" knowledge scripts/knowledge.py)"
if [ -z "$knowledge" ]; then
  general="SKIP: K-general (the knowledge plugin is not installed, so the general check did not run)"
else
  if ! general="$("${runner[0]}" "${runner[@]:1:$((${#runner[@]}-2))}" "$knowledge/scripts/knowledge.py" --root "$root" check --graph ddd --cache-only 2>&1)"; then
    printf 'business-domain hook: the general check found errors after the change of %s. Correct the page:\n%s\n' "$path" "$general" >&2
    exit 2
  fi
fi

if printf '%s\n%s\n' "$out" "$general" | grep -q '^\(WARN\|SKIP\): '; then
  context="ddd.py check gave notes after the edit of $path:
$out
$general"
  if command -v jq >/dev/null 2>&1; then
    jq -cn --arg c "$context" '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $c}}'
  else
    python3 -c '
import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                         "additionalContext": sys.argv[1]}}))
' "$context"
  fi
fi
exit 0
