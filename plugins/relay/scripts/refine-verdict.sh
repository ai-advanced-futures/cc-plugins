#!/usr/bin/env bash
# relay: the verdict of one critic pass over one findings file.
# EXECUTED, never sourced:
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/refine-verdict.sh" <findings_path>
#
# Prints exactly one line to stdout and exits 0, always:
#   REFINE_VERDICT=<clean|findings|stalled|no-answer> critical=<N> important=<M> minor=<P> reason=<word> fingerprints=<f1;f2;...>
#
# MASTER COPY OF THE LINE GRAMMAR (POSIX ERE). The same characters work
# unchanged in bash [[ =~ ]], grep -E, and the generated Workflow script's
# JavaScript parser, which is a literal copy of this expression:
#   ^REFINE_VERDICT=(clean|findings|stalled|no-answer) critical=([0-9]+) important=([0-9]+) minor=([0-9]+) reason=([^ ]+) fingerprints=(.*)$
#
# RULES:
#   - missing file          -> no-answer reason=missing, all counts 0
#   - empty file            -> no-answer reason=empty, all counts 0
#   - first non-blank line is not `FINDINGS: critical=<N> important=<M> minor=<P>`
#                           -> no-answer reason=bad-header, all counts 0
#   - a severity header (`critical:` / `important:` / `minor:`) is matched
#     loosely: case-insensitive, with optional leading `#`, `*`, `_` and
#     spaces, optional text in parentheses before the colon, and optional
#     `*`/`_` after the colon (so `**critical:**`, `critical (blocking):`,
#     and `## Critical:` all count).
#   - a line is a list entry when, after its leading spaces, it opens with a
#     bullet (`-`, `*`, `+`) or an ordinal (`1.`, `1)`), then spaces. Take
#     the rest of the line, lower-case it, and delete the characters
#     * _ ` " ' from it. The entry is a finding entry when that normalized
#     rest starts with the word `section` or `task`, followed by a colon, a
#     space, or the end of the text. This one rule decides an entry for the
#     count, for its fingerprint, and for the bad-list check below — a
#     decorated form like `**section**: A` or `1. section: A` counts the
#     same as the plain `- section: A` form.
#   - the entry NAME is what is left of that entry after the opener, the
#     keyword, and the decoration around both. The colon after the keyword is
#     optional, and a trailing colon is dropped, so `- section: A`,
#     `- **section:** A` and `- Section "A":` all name the same `a`. The name
#     is half of the fingerprint, so a critic that decorates one round and not
#     the next must still give the same token for the same finding.
#   - a `concern:` line is matched as loosely as an entry opener: an optional
#     bullet or ordinal, then the word `concern` case-insensitively with
#     `* _ ` " '` deleted (so `**concern:**` and `- Concern: x` both count).
#     Without this, two findings in one section both take an empty concern
#     part and collapse onto one fingerprint.
#   - a finding entry that appears before the first recognized severity
#     header (sev not yet set)
#                           -> no-answer reason=bad-list, all counts 0.
#     Such a file is never clean. An entry after an unrecognized header
#     line counts under the last severity header the script did
#     recognize, not bad-list.
#   - for critical and important, the larger of the header count and the
#     number of `- section:` / `- task:` entries under that severity wins.
#   - clean when critical is 0 and important is 0. minor never blocks.
#   - `findings` becomes `stalled` with reason=no-new-low when
#     `refine-trend.sh` reports `stalled` for this findings path: the count of
#     critical plus important findings set no new low in 5 rounds. The counts
#     and the fingerprints stay the values of the `--single` line. `clean` and
#     `no-answer` are never `stalled`.
#   - `--single` makes the verdict of one file and runs no trend. The trend
#     script calls this mode, so the two scripts never call each other in a
#     circle.
#   - `RELAY_REFINE_TREND` names the trend script. It defaults to the file
#     beside this one. A test points it at a stub, so no test has to replace
#     the shipped script to drive the failure paths below. [inferred]
#   - When the trend call exits non-zero or prints no `REFINE_TREND=` line,
#     reason becomes `no-trend` and the label stays `findings`, never
#     `stalled`: a trend failure must be visible, not silent. [inferred]
#   - reason is `ok` for clean and findings.
# The script is deterministic and holds no model.
set -u

_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The trend script the full mode calls. The override is a test seam: a test
# points it at a stub and the shipped file stays untouched. [inferred]
_trend_script="${RELAY_REFINE_TREND:-$_here/refine-trend.sh}"

# `--single` reads one file and nothing else. The normal mode adds the stall
# floor of `refine-trend.sh`, and that script calls this one with `--single`,
# so the two never call each other in a circle.
_mode=full
if [ "${1:-}" = "--single" ]; then
  _mode=single
  shift
fi

_emit() {
  local _label="$1" _reason="$5" _trend_full _trend _trend_rc
  if [ "$_mode" = full ] && [ "$_label" = findings ]; then
    _trend_full="$(bash "$_trend_script" "$_path" 2>/dev/null)"
    _trend_rc=$?
    _trend="${_trend_full##*$'\n'}"
    if [ "$_trend_rc" -ne 0 ] || [[ "$_trend" != REFINE_TREND=* ]]; then
      # A trend call that cannot run, or that does not end in its own last
      # line, must be visible, not silently reason=ok. The status comes
      # straight off the command substitution, with no pipe behind it, so it
      # is the trend script's own exit code. [inferred]
      _reason=no-trend
    else
      case "$_trend" in
        REFINE_TREND=stalled*) _label=stalled; _reason=no-new-low ;;
      esac
    fi
  fi
  printf 'REFINE_VERDICT=%s critical=%s important=%s minor=%s reason=%s fingerprints=%s\n' \
    "$_label" "$2" "$3" "$4" "$_reason" "$6"
  exit 0
}

_path="${1:-}"
if [ -z "$_path" ] || [ ! -f "$_path" ]; then
  _emit no-answer 0 0 0 missing ""
fi

# The first non-blank line. A file with no non-blank line is empty.
_header="$(awk 'NF { print; exit }' "$_path")"
if [ -z "$_header" ]; then
  _emit no-answer 0 0 0 empty ""
fi

_header_re='^FINDINGS: critical=([0-9]+) important=([0-9]+) minor=([0-9]+)[[:space:]]*$'
if [[ ! "$_header" =~ $_header_re ]]; then
  _emit no-answer 0 0 0 bad-header ""
fi
_hc="${BASH_REMATCH[1]}"
_hi="${BASH_REMATCH[2]}"
_hm="${BASH_REMATCH[3]}"

# Count the entries under `critical:` and `important:` and build one
# fingerprint token per entry. An entry opens with a bullet or an ordinal,
# then the word `section` (spec findings) or `task` (plan findings), matched
# loosely: see the normalizing rule in the header comment above. A token is
# <severity>:<section-or-task>:<first six concern words>, each part
# lower-cased with every character that is not a letter or digit replaced by
# `-`, runs collapsed, leading and trailing `-` stripped, then cut to 80
# characters. Tokens are joined with `;`.
_counts="$(awk '
BEGIN {
  QUOTE = sprintf("%c", 39)
  sev = ""; nc = 0; ni = 0; nf = 0; cur = 0; bad_list = 0
  OPENER = "^[[:space:]]*([-*+]|[0-9]+[.)])[[:space:]]+"
  DECO = "[*_`\"" QUOTE "]"
  SEC_CI = "[Ss][Ee][Cc][Tt][Ii][Oo][Nn]"
  TASK_CI = "[Tt][Aa][Ss][Kk]"
  CONCERN_CI = "[Cc][Oo][Nn][Cc][Ee][Rr][Nn]"
  # The colon is optional here because is_entry() accepts the colonless
  # `- section A` form too; without the `?` that form keeps the keyword in
  # its own name and fingerprints differently from `- section: A`.
  NAME_RE = "^" DECO "*(" SEC_CI "|" TASK_CI ")" DECO "*:?" DECO "*[[:space:]]*"
  CONCERN_RE = "^[[:space:]]*" DECO "*" CONCERN_CI DECO "*:" DECO "*[[:space:]]*"
}

function slug(s) {
  s = tolower(s)
  gsub(/[^a-z0-9]+/, "-", s)
  sub(/^-/, "", s)
  sub(/-$/, "", s)
  return s
}

function unquote(s,   a, b) {
  a = substr(s, 1, 1)
  b = substr(s, length(s), 1)
  if (length(s) > 1 && a == b && (a == "\"" || a == QUOTE))
    s = substr(s, 2, length(s) - 2)
  return s
}

function flush(   token) {
  if (!cur) return
  token = slug(cur_sev) ":" slug(cur_name) ":" slug(cur_concern)
  fp[++nf] = substr(token, 1, 80)
  cur = 0
}

# A list entry is a bullet or ordinal opener followed by the word
# `section` or `task`, once decoration (* _ ` " '\'') is deleted and the
# text is lower-cased. Same rule for counting, fingerprints, and bad-list.
function is_entry(line_l,   rest) {
  if (line_l !~ OPENER) return 0
  rest = line_l
  sub(OPENER, "", rest)
  gsub(DECO, "", rest)
  return (rest ~ /^section($|[: ])/ || rest ~ /^task($|[: ])/)
}

# Strip the bullet/ordinal opener from the raw (case-preserved) line, then
# the keyword with its surrounding decoration and the colon that follows,
# leaving the entry name as written. A trailing colon goes too, so the
# `- Section "A":` form names the same thing the `- section: A` form does.
function entry_name(line,   name) {
  name = line
  sub(OPENER, "", name)
  sub(NAME_RE, "", name)
  sub(/[[:space:]]*:*[[:space:]]*$/, "", name)
  return name
}

# A concern line, matched as loosely as an entry opener: the bullet or ordinal
# is optional, and the keyword carries any decoration. Same normalizing step
# is_entry() makes, on the lower-cased line.
function is_concern(line_l,   rest) {
  rest = line_l
  sub(OPENER, "", rest)
  sub(/^[[:space:]]*/, "", rest)
  gsub(DECO, "", rest)
  return (rest ~ /^concern:/)
}

{
  line_l = tolower($0)
  if (line_l ~ /^[[:space:]]*[#*_]*[[:space:]]*(critical|important|minor)[[:space:]]*(\([^()]*\))?[[:space:]]*:[[:space:]]*[*_]*[[:space:]]*$/) {
    flush()
    tmp = line_l
    match(tmp, /(critical|important|minor)/)
    sev = substr(tmp, RSTART, RLENGTH)
    next
  }
}

is_entry(line_l) {
  flush()
  if (sev == "critical" || sev == "important") {
    cur = 1
    cur_sev = sev
    cur_name = unquote(entry_name($0))
    cur_concern = ""
    if (sev == "critical") nc++
    else                   ni++
  } else if (sev != "minor") {
    bad_list = 1
  }
  next
}

is_concern(line_l) {
  # Only the concern line itself, never its continuation lines.
  if (cur && cur_concern == "") {
    text = $0
    sub(OPENER, "", text)
    sub(CONCERN_RE, "", text)
    parts = split(text, word, /[[:space:]]+/)
    out = ""
    for (i = 1; i <= parts && i <= 6; i++)
      out = (out == "" ? word[i] : out " " word[i])
    cur_concern = out
  }
  next
}

END {
  flush()
  joined = ""
  for (i = 1; i <= nf; i++)
    joined = (joined == "" ? fp[i] : joined ";" fp[i])
  printf "%d %d %d %s\n", nc, ni, bad_list, joined
}
' "$_path")"

read -r _nc _ni _bad _fps <<< "$_counts"

if [ "$_bad" -eq 1 ]; then
  _emit no-answer 0 0 0 bad-list ""
fi

_crit="$_hc"
[ "$_nc" -gt "$_crit" ] && _crit="$_nc"
_imp="$_hi"
[ "$_ni" -gt "$_imp" ] && _imp="$_ni"

_label=findings
[ "$_crit" -eq 0 ] && [ "$_imp" -eq 0 ] && _label=clean
_emit "$_label" "$_crit" "$_imp" "$_hm" ok "$_fps"
