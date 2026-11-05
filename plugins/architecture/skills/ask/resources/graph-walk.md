# architecture:ask — graph walk rules

Read this file only for a `partial` note, a `now=` note, or a set question. The 2 edge Grep
patterns and the classification rules are in [`../SKILL.md`](../SKILL.md).

## The `partial` rule

`partial` means that the source and the target stay in force together. Keep the two. If the
partial target has the status `superseded` and the row has `now=`, use each file that `now=`
names in place of the target.

## The `now=` rule

`now=` names each chain end of the target, with commas between the files. When it names 2
files, the two replace the target. `now=` never names the source of the row, because the source
is not its own successor. It is absent when the source is the one chain end. A file that `now=`
names can be proposed: look at its index line before you give it as a decision in force.

## A set question about one area `Z`

1. Read the `### accepted` lines of `## Z` in `index.md`.
2. Grep `links.tsv` with this pattern:

   ```
   ^[^\t]+\t(supersedes|amends|deviates_from|refines)\t[^\t]+\tlive\t.*\tZ\t
   ```

3. Answer from the index lines.
4. Open a maximum of 5 bodies, and only those that the question words select.
5. List in Gaps each accepted ADR that was not opened. Name the proposed ADRs of the area as
   candidates, not as constraints.

A Grep for `\tZ\t` alone gives too many rows. On a large corpus it gave 394 rows and
20,065 tokens, which is more than the stop rule and the `head_limit` permit. The pattern above
gave 41 rows and 1,986 tokens. The worst-case degrees of the corpus are 20 out and 38 in.
