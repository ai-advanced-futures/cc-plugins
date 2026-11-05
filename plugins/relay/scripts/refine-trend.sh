#!/usr/bin/env bash
# relay: the measured facts of one refine step.
# EXECUTED, never sourced:
#   bash "${CLAUDE_PLUGIN_ROOT}/scripts/refine-trend.sh" <findings_path> [<subject_path>]
#
# Read-only, deterministic, and it holds no model. It writes no file.
#
# <findings_path> has the form <dir>/<step>-<tail>.findings.md. <step> is
# `refine-spec` or `refine-plan`. <tail> is r<N>, then an optional -b<B>, then
# an optional -retry. N is the round number of the path.
#
# THE PASSES THAT COUNT. The script reads <dir>/<step>-r*.findings.md.
#   - A file of another step never counts.
#   - A file with a round number higher than N never counts.
#   - A file counts only when `refine-verdict.sh --single` labels it `clean` or
#     `findings`.
#   - For round N the pass is the file given as <findings_path>. When --single
#     labels that file `no-answer`, round N has no pass, and `since` is 0.
#   - For each lower round the pass is the newest file, by modification time,
#     among the files of that round that --single labels `clean` or `findings`.
#     A file left by an earlier run is older than this run's file for that
#     round, so it does not count.
#
# THE NUMBERS. For each pass, `total` is critical plus important.
#   - `low` is the lowest total of all passes; `low_round` is the first round
#     that reached it.
#   - `reset_round` is the highest round whose pass file has -b in its tail, or
#     0. A -b pass opens a block after a person answered continue.
#   - `since` is N minus the higher of low_round and reset_round.
#   - The step is `stalled` when `since` is 5 or more. _FLOOR is that one
#     constant. It has no flag.
#
# THE OUTPUT. A table, then one last line, then exit 0:
#   REFINE_TREND=<ok|stalled> rounds=<N> low=<L> low_round=<R> since=<K> words_first=<W1> words_last=<W2>
# A bad argument, a missing file, or a path of another form prints only the
# line with rounds=0. The script never prints `stalled` for a step it cannot
# read.
#
# It calls `refine-verdict.sh --single` and nothing else of relay, so the two
# scripts never call each other in a circle.
#
# EXIT CODE: 0, always.
set -u

_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The stall floor. One constant, no flag.
_FLOOR=5

_zero() {
  printf 'REFINE_TREND=ok rounds=0 low=0 low_round=0 since=0 words_first=0 words_last=0\n'
  exit 0
}

# The word count of one file, or `-` when the file is absent. BSD `wc` pads its
# number with leading spaces, which command substitution does not strip, so the
# `tr` is what makes the number the same on every platform.
_words() {
  if [ -f "$1" ]; then wc -w < "$1" | tr -d ' '; else printf '%s' '-'; fi
}

# A literal copy of the MASTER COPY OF THE LINE GRAMMAR in refine-verdict.sh.
# Only the first four groups are read here, but the alternation is what keeps a
# label this script does not know from reading as a pass.
_vline_re='^REFINE_VERDICT=(clean|findings|stalled|no-answer) critical=([0-9]+) important=([0-9]+) minor=([0-9]+) reason=([^ ]+) fingerprints=(.*)$'
_single() {
  local _line
  _line="$(bash "$_here/refine-verdict.sh" --single "$1" 2>/dev/null)"
  if [[ "$_line" =~ $_vline_re ]]; then
    printf '%s %s %s %s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" \
      "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}"
  else
    printf 'no-answer 0 0 0\n'
  fi
}

# The `verdict:` line under the `lookback:` block of one findings file, or `-`.
_lookback() {
  [ -f "$1" ] || { printf '%s\n' '-'; return; }
  awk '
    /^[[:space:]]*lookback:[[:space:]]*$/ { seen = 1; next }
    seen && /^[[:space:]]*verdict:[[:space:]]*(progress|churn)[[:space:]]*$/ {
      v = $0
      sub(/^[[:space:]]*verdict:[[:space:]]*/, "", v)
      sub(/[[:space:]]*$/, "", v)
      print v
      found = 1
      exit
    }
    END { if (!found) print "-" }
  ' "$1"
}

_path="${1:-}"
_subject="${2:-}"
[ -n "$_path" ] && [ -f "$_path" ] || _zero

_dir="$(cd "$(dirname "$_path")" 2>/dev/null && pwd)" || _zero
_base="$(basename "$_path")"
_name_re='^(refine-spec|refine-plan)-r([0-9]+)(-b[0-9]+)?(-retry)?\.findings\.md$'
[[ "$_base" =~ $_name_re ]] || _zero
_step="${BASH_REMATCH[1]}"
_round=$((10#${BASH_REMATCH[2]}))
_self="$_dir/$_base"

# --- one pass for each round from 1 to _round -------------------------------
# words_first is the first row that has a snapshot. words_last is the `now` row
# when the second argument names a file that exists; if not, it is the last row
# that has a snapshot. Each is 0 when no such row exists. Both take the count
# the row already holds, so no file is counted twice.
_rows=''
_low=-1
_low_round=0
_reset=0
_snaps=()
_has_n=0
# Empty until the first row that has a snapshot, so a snapshot of 0 words is
# still the first one. Both become 0 when no row has a snapshot.
_wfirst=''
_wlast=0

_r=1
while [ "$_r" -le "$_round" ]; do
  _pick=''
  if [ "$_r" -eq "$_round" ]; then
    read -r _lab _c _i _m <<< "$(_single "$_self")"
    if [ "$_lab" = clean ] || [ "$_lab" = findings ]; then _pick="$_self"; _has_n=1; fi
  else
    # The plain file plus one pattern for every -b<B> and -retry tail. A bare
    # `*` after the digits would run on into a higher round number, and a
    # separate -retry pattern would hand the same file to `ls` twice.
    shopt -s nullglob
    _cands=("$_dir/$_step-r$_r"-*.findings.md)
    shopt -u nullglob
    [ -f "$_dir/$_step-r$_r.findings.md" ] &&
      _cands=("$_dir/$_step-r$_r.findings.md" ${_cands[@]+"${_cands[@]}"})
    if [ "${#_cands[@]}" -gt 0 ]; then
      while IFS= read -r _f; do
        [ -n "$_f" ] || continue
        read -r _lab _c _i _m <<< "$(_single "$_f")"
        if [ "$_lab" = clean ] || [ "$_lab" = findings ]; then _pick="$_f"; break; fi
      done < <(ls -t "${_cands[@]}" 2>/dev/null)
    fi
  fi
  # The pick loop above left _lab _c _i _m holding this file's own line.
  [ -n "$_pick" ] || { _r=$((_r + 1)); continue; }

  _total=$((_c + _i))
  _snap="${_pick%.findings.md}.subject.md"
  _w="$(_words "$_snap")"
  _lb="$(_lookback "$_pick")"
  _rows="${_rows}$(printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' \
    "$_r" "$_total" "$_c" "$_i" "$_m" "$_w" "$_lb" "$_pick" "$_snap")
"
  if [ "$_w" != '-' ]; then
    _snaps+=("$_snap")
    [ "$_wfirst" = '' ] && _wfirst="$_w"
    _wlast="$_w"
  else
    _snaps+=('-')
  fi
  if [ "$_low" -lt 0 ] || [ "$_total" -lt "$_low" ]; then
    _low="$_total"; _low_round="$_r"
  fi
  # The test is on the file name, never on the whole path: a directory named
  # `...-b2` is not a block pass, and reading the path here would reset the
  # count on every round and switch the stall floor off in silence.
  case "$(basename "$_pick")" in *-b[0-9]*) _reset="$_r" ;; esac
  _r=$((_r + 1))
done

[ "$_low" -ge 0 ] || _low=0

# --- the table -------------------------------------------------------------
printf '# round\ttotal\tcritical\timportant\tminor\twords\tlookback\tfindings\tsnapshot\n'
printf '%s' "$_rows"

_now_words=''
if [ -n "$_subject" ] && [ -f "$_subject" ]; then
  _now_words="$(_words "$_subject")"
  printf 'now\t-\t-\t-\t-\t%s\t-\t-\t-\n' "$_now_words"
fi

# The `now` row, when there is one, is the last word count.
[ -n "$_now_words" ] && _wlast="$_now_words"
[ -n "$_wfirst" ] || _wfirst=0

# --- the section table -----------------------------------------------------
# A section is the text from one markdown heading line to the next heading
# line of any level. One row for each section whose word count differs between
# the first snapshot and the last snapshot, the largest growth first, at most
# 15 rows. The table is left out when fewer than two snapshots exist. A
# section's word count excludes the `#` marker of its own heading line, so it
# counts only the heading text and the body; `words_first` and `words_last` of
# the row table use a different counter (`wc -w` over the whole file, marker
# included) and the two numbers are not expected to agree. [inferred] A line
# that opens a fenced code block (three backticks or three tildes) toggles a
# fence flag; a `#` line inside a fence is body text of the enclosing section,
# never a new heading, since the subjects this script measures are specs and
# plans full of fenced bash. [inferred]
_present=()
for _s in ${_snaps[@]+"${_snaps[@]}"}; do
  [ "$_s" = '-' ] || _present+=("$_s")
done

if [ "${#_present[@]}" -ge 2 ]; then
  # Column 1 is the first snapshot and column 2 is the last snapshot: the two
  # the growth test compares. Column 2 is never displayed. Columns 3 and up are
  # the displayed ones — the first snapshot, the last up to four rows (`-` for
  # a row whose snapshot is missing), and `now` when the second argument names
  # a file that exists.
  _cols=("${_present[0]}" "${_present[${#_present[@]} - 1]}" "${_present[0]}")
  _start=$(( ${#_snaps[@]} - 4 ))
  [ "$_start" -lt 0 ] && _start=0
  _k="$_start"
  while [ "$_k" -lt "${#_snaps[@]}" ]; do
    _cols+=("${_snaps[$_k]}")
    _k=$((_k + 1))
  done
  [ -n "$_now_words" ] && _cols+=("$_subject")

  # The distinct files behind those columns. One file can fill more than one
  # column — column 1 and column 3 are both the first snapshot — and its word
  # counts do not depend on the column, so each file is read one time.
  _files=()
  for _s in "${_cols[@]}"; do
    { [ "$_s" = '-' ] || [ ! -f "$_s" ]; } && continue
    _dup=0
    for _g in ${_files[@]+"${_files[@]}"}; do
      [ "$_g" = "$_s" ] && { _dup=1; break; }
    done
    [ "$_dup" -eq 0 ] && _files+=("$_s")
  done

  # One `<col> <heading> <words>` record for each heading of each column that
  # exists, plus one `__PRESENT__` record per existing column so the pivot can
  # tell an absent column from a heading with no words in a column that is
  # there.
  _stream=''
  if [ "${#_files[@]}" -gt 0 ]; then
    _stream="$(awk '
      function words(line,   n, w, i, c) {
        n = split(line, w, /[[:space:]]+/)
        c = 0
        for (i = 1; i <= n; i++) if (w[i] != "") c++
        return c
      }
      # An empty file has no first record, so mark every file here: a
      # snapshot of 0 words is present, not missing.
      BEGIN { for (i = 1; i < ARGC; i++) present[ARGV[i]] = 1 }
      FNR == 1 { cur = ""; infence = 0 }
      /^(```|~~~)/ {
        infence = !infence
        if (cur != "") count[FILENAME SUBSEP cur] += words($0)
        next
      }
      infence {
        if (cur != "") count[FILENAME SUBSEP cur] += words($0)
        next
      }
      /^#+[[:space:]]/ {
        cur = $0
        sub(/[[:space:]]+$/, "", cur)
        text = cur
        sub(/^#+[[:space:]]*/, "", text)
        count[FILENAME SUBSEP cur] += words(text)
        next
      }
      cur != "" { count[FILENAME SUBSEP cur] += words($0) }
      END {
        for (f in present) printf "%s\t%s\t%s\n", f, "__PRESENT__", "1"
        for (k in count) {
          split(k, part, SUBSEP)
          printf "%s\t%s\t%d\n", part[1], part[2], count[k]
        }
      }
    ' "${_files[@]}")
"
  fi

  # The stream is keyed by path, so the pivot maps each column to its file.
  # `sort` compares whole lines when the first key ties, so the row order does
  # not depend on the order awk walked its arrays in.
  _sections="$(printf '%s' "$_stream" | awk -F'\t' -v ncol="${#_cols[@]}" \
    -v colpaths="$(printf '%s\n' "${_cols[@]}")" '
    BEGIN { split(colpaths, colpath, "\n") }
    $2 == "__PRESENT__" { present[$1] = 1; next }
    {
      v[$1 SUBSEP $2] = $3 + 0
      if (!($2 in known)) { known[$2] = 1; order[++n] = $2 }
    }
    END {
      for (i = 1; i <= n; i++) {
        h = order[i]
        a = ((colpath[1] SUBSEP h) in v) ? v[colpath[1] SUBSEP h] : 0
        b = ((colpath[2] SUBSEP h) in v) ? v[colpath[2] SUBSEP h] : 0
        if (a == b) continue
        line = h
        for (c = 3; c <= ncol; c++) {
          if (!(colpath[c] in present)) { line = line "\t-"; continue }
          line = line "\t" (((colpath[c] SUBSEP h) in v) ? v[colpath[c] SUBSEP h] : 0)
        }
        printf "%d\t%s\n", b - a, line
      }
    }
  ' | sort -k1,1nr | head -15 | cut -f2-)"

  if [ -n "$_sections" ]; then
    printf '# section\twords\n'
    printf '%s\n' "$_sections"
  fi
fi

_base_round="$_low_round"
[ "$_reset" -gt "$_base_round" ] && _base_round="$_reset"
# Round N is itself a pass when _has_n is 1, so low_round is then at least 1
# and never above N. With no pass for round N there is no base to count from.
_since=$((_round - _base_round))
[ "$_has_n" -eq 1 ] || _since=0

_state=ok
[ "$_since" -ge "$_FLOOR" ] && _state=stalled

printf 'REFINE_TREND=%s rounds=%s low=%s low_round=%s since=%s words_first=%s words_last=%s\n' \
  "$_state" "$_round" "$_low" "$_low_round" "$_since" "$_wfirst" "$_wlast"
exit 0
