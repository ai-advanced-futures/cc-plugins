# ask — corpus locations and status normalization

Normative detail for the decision corpus and status handling. The operative procedure lives in
[`../SKILL.md`](../SKILL.md).

## Corpus

Search the configured ADR corpus and every `extra_corpora` match present on disk. Missing specs or
product documents are not errors; report their absence in **Gaps** when it affects the answer.

This tolerance does **not** extend to an unresolved ADR corpus. A repo with no spec for a topic is
a normal state; an ADR directory that is absent or empty is a misconfiguration, and answering as if
the ADR record had been read would misreport the decision record. When the corpus is unresolved,
lead **Gaps** with that fact.

| Type | Location | Status read rule |
|---|---|---|
| ADRs | Configured `dir` — use its frontmatter | Read `lifecycle`; expected values are `accepted`, `proposed`, `deprecated`, `superseded`. `status` holds the OKF value, derived from `lifecycle`: `proposed` is `draft`, `accepted` is `stable`, `superseded` and `deprecated` are `deprecated`. An absent or zero-file corpus is a **Gaps** entry, never a silent empty answer. |
| PRDs | `docs/product/**/prd.md` when included by `extra_corpora` | Prefer frontmatter `lifecycle_state`; fall back to legacy `lifecycle-state` only when `lifecycle_state` is absent. |
| Product documents | `docs/product/*.md` when included by `extra_corpora` | Read `lifecycle_state`, then `lifecycle-state`; if neither exists, cite as `status: unknown` and note that in **Gaps**. |
| Specs | `docs/superpowers/specs/` when included by `extra_corpora` | Read frontmatter `status`, then body `**Status:**`; if both exist and differ, report both in **Sources** and mention the mismatch in **Gaps**. |

## Status normalization

Preserve the raw status string in **Sources** and also report its normalized treatment.

| Raw status signal | Normalized treatment |
|---|---|
| ADR `accepted` | authoritative / in force |
| ADR `proposed` | under consideration / not yet in force |
| ADR `deprecated` or `superseded` | no longer in force; name the superseding artifact if known |
| Product `saved` | current recorded lifecycle state and authoritative for completed-product decisions |
| Product `analyzed`, `simulated`, `estimated` | current recorded lifecycle state but not authoritative for completed-product decisions |
| Spec `ready`, `converged`, `saved`, `implemented`, `approved`, `design` | current / in force |
| Spec `draft`, `proposed`, `refinement` | under consideration / not yet in force |
| Any unmatched status, including `review` | unknown / not authoritative; add a **Gaps** note |

Normalize compound status strings case-insensitively while preserving the raw string. When multiple
lifecycle words appear, choose the strongest signal in this order: `superseded` or `deprecated`;
then `implemented`, `converged`, `approved`, `design`, `ready`, or `saved`; then `draft`,
`proposed`, or `refinement`. Match recognized word stems, so `Drafted` normalizes to `draft`.

## Search form

Each search of the procedure is one `grep` command through Bash, in this form. `grep` is a
read-only command, so it runs with no permission prompt.

- `grep -n -E '<pattern>' <path> | head -n 60`. Put the pattern in single quotes: write each `'`
  of a term as `'\''`. Use a plain `|` for "or". A pattern has no "and" of terms.
- Write each path in full. Use no loop and no shell variable, because Claude Code cannot check
  such a command before it runs: it asks the person, and `claude -p` refuses it.
- `<path>` is the one file. For a directory, use `-r --include='*.md' <dir>`.
- `-l` in place of `-n` only when the step says "file names".
- `-i` only when the step says "ignore letter case". `-A <n>` only when the step gives it.
- `head -n 60` keeps 60 lines. A result of 60 lines is possibly cut. Make the pattern narrower,
  or write in Gaps that the result was cut.
- `[[:blank:]]` in a pattern matches a tab of `links.tsv`: `grep -E` has no tab escape.
- `<file>` in a pattern is the file name with each `.` written as `\.`. An unescaped `.` matches
  each character.
- `<arch>` in a pattern is `(<archive_dir>/)?` with the value from `.claude/adr.json`, for
  example `(archive/)?`. When `archive_dir` is null, leave `<arch>` out, and skip each step that
  names the archive index.
