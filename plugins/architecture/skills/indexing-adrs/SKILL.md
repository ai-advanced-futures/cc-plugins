---
name: indexing-adrs
description: Regenerates the ADR register and lints the corpus. Use for "/architecture:index", "regenerate the ADR register", "the register is stale", "reindex the ADRs", and fires after an ADR is added, renamed, or retitled, and whenever CI reports the index stale.
argument-hint: "[--nav] [config path]"
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# indexing-adrs

Regenerate the register from the corpus, then lint.

## Method

1. Run the write step from the repository root and print its receipt verbatim. When the
   arguments hold `--nav`, run the first form. If not, run the second form. When the arguments
   hold a config path, add `--config <path>` to the form you run.

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_index.py --write --nav
   python3 ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_index.py --write
   ```

   `--nav` writes `index.md`, `links.tsv` and the archive `index.md`, and it turns navigation
   on. Run it one time for a corpus. After that, a plain `--write` keeps the 3 files current.
   `--nav` without `--write` is a usage error and exits 2.

2. Read the receipt.
   - A `dropped row:` line means a hand-authored summary lost its file. Put the summary back under
     the right ADR if the file moved or was renamed, or say plainly that the ADR is gone.
   - An `unparsed row:` line means a row nobody can key. Repair it by hand into the
     `- [label](href) — status — summary` shape.
   - A `wrote <path>` line names one generated file that changed. No `wrote` line means that
     the generated files were already current, but only when the command exits 0.
   - An `ERROR: superseded_by chain is a cycle` line gives exit 1. The command then writes no
     navigation file and prints no `wrote` line, and the 3 files stay stale. Break the cycle in
     the `superseded_by` keys that the line names, then run the command again.

3. Replace each `<!-- TODO: summary -->` placeholder with one line of meaning. The machine keeps
   the structure honest; the human keeps the meaning.

4. Make hand edits only above `<!-- ADR-INDEX:BEGIN (generated — do not edit) -->` or below
   `<!-- ADR-INDEX:END -->`, because the next run overwrites all text between the markers.

5. Run the lint and report every error and warning:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_lint.py
   ```

   Never report success while the lint exits non-zero, because a red lint means the register
   does not match the corpus. Report the run as failed and name each failing check.
