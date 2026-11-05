---
description: Answers questions about past architectural decisions from the ADR graph, read-only. Use for "/architecture:ask", "why did we choose X over Y", "remind me why we did X", "is this still true", "did we ever decide X", "what's our stance on X", and fires before an architectural boundary changes so past decisions are read before new ones are made.
allowed-tools: Read, Grep, Glob, AskUserQuestion, Skill
---

# ask

Answer a question from what the ADR corpus already records. This skill is read-only: it reads
the generated index `index.md` first. When no index exists, it reads the register first. It
opens an ADR body only after that. The inputs are `question`, and `mode`: `human` for `/architecture:ask`, or
`subagent` for a delegated lookup.

## Grep form

Each Grep of the procedure uses this form.

- `pattern`: one ripgrep pattern. Use a plain `|` for "or". The tool has no "and" of terms.
- `path`: the one file, or the directory with a `glob` value.
- `output_mode: content` and `-n: true`, unless the step says `files_with_matches`.
- `-i: true` only when the step says "ignore letter case". `-A: <n>` only when the step gives it.
- `head_limit: 60`. A result of 60 lines is possibly cut. Make the pattern narrower, or write in
  Gaps that the result was cut.
- `\t` in a pattern is the 2 characters backslash and `t`. ripgrep reads them as a tab.
- `<file>` in a pattern is the file name with each `.` written as `\.`. An unescaped `.` matches
  each character.
- `<arch>` in a pattern is `(<archive_dir>/)?` with the value from `.claude/adr.json`, for
  example `(archive/)?`. When `archive_dir` is null, leave `<arch>` out, and skip each step that
  names the archive index.

## Procedure

1. **Entry.** Read `.claude/adr.json`. Get `dir`, `register.path`, `archive_dir` and
   `extra_corpora`. If `dir` is empty or missing, put that fact first in Gaps and stop.
2. **Routing.** Grep `<dir>/index.md` for `^okf_version:`.
   - **a. The Grep has a hit. Navigation is on.**
     1. Select the most exact term of the question: a product name, a technology name, or the
        least frequent noun. Grep `index.md` for it, and ignore letter case. For a term with
        2 spellings, use the pattern `a|b`.
     2. If the Grep gives more than 10 lines, select a second term and Grep one time more with
        the pattern `a.*b|b.*a`. `a` is term 1 and `b` is term 2. Do not Read the hits, because
        the index lines already hold what step 3 ranks.
     3. If the result still has more than 10 lines, run no more Greps. Select the candidates
        from the lines that the Grep returned, because they are already loaded.
     4. If the first Grep gives 0 lines, try one time with other words for the same subject.
     5. If there is still no hit, or if the question names a decision, do items 1 to 3 on
        `<dir>/<archive_dir>/index.md`.
     6. If there is still no hit, Read the `## Areas` list. If no area name bears on the
        question, the corpus is silent on this part. Run one Grep with
        `output_mode: files_with_matches`, ignore letter case, for term 1 in `<dir>` with the
        glob `*.md`, and one in `<dir>/<archive_dir>`. Gaps then says: "N bodies name the term,
        and no index line does." When a result has 60 files, write "60 or more". Then stop for
        this part.
     7. If an area bears on the question, Read only its `### accepted` lines first. A Grep for
        `^##` gives the line numbers.
   - **b. The Grep has no hit, or the file does not exist.**
     1. **Read the register first**, at `register.path`, by Grep for the same terms, with the
        form of items a.1 to a.3. Never Read the register in full, because a Grep returns only
        the matching lines, and a full Read loads one line for each ADR in the corpus.
     2. If the register gives nothing, Grep `^title:.*<term>` in `<dir>` with the glob `*.md`,
        and ignore letter case. `<term>` is term 1. A plain `^title:` Grep gives one line for
        each ADR, and the `head_limit` cuts it.
     3. Add to Gaps: "No generated index. Run `/architecture:index --nav`."
3. **Candidates.** Keep a maximum of 5 candidates. Rank them by a match in the title or the
   text, then accepted before proposed, then the newer date. A `(derived)` line has less weight.
   A proposed ADR is a candidate, not a decision in force. If 2 or more candidates give
   different answers, and the question does not select one, use the clarification behavior.
4. **Successor first.** Do this for each candidate, and not only for a candidate whose line says
   superseded. Grep `<dir>/links.tsv` with the pattern `^<arch><file>\tsuperseded_by\t`. Skip
   this Grep only when the candidate came from the archive index, and its line shows one `Now:`
   target and no `(partial)`.
   - Look at `target_status`, column 5, of each row. If it is `superseded`, Grep again for the
     target of that row. Stop at a row whose `target_status` is not `superseded`. That target is
     a chain end. Use `target_status` and not `target_state` for this test. A live file can
     have the lifecycle `superseded`.
   - The limit is 5 steps for each branch. A longer chain goes to Gaps. A row with `partial`
     does not stop the chain.
   - If the candidate has the lifecycle `superseded`, each chain end replaces the candidate. Keep
     the old file in Sources with the label "superseded".
   - If the candidate has a different lifecycle and has `superseded_by` rows, it is a partly
     replaced ADR. Keep the candidate, add each target, Read
     [resources/graph-walk.md](resources/graph-walk.md), and obey its `partial` rule.
   - If no `links.tsv` exists, Grep the ADR file for `^superseded_by:` with `-A: 2`. 2 lines
     after the key show a list of 2 values. If the second line after the key is a list item, the
     list can be longer: Read the front matter lines of the file.
5. **Open only the matching ADRs, by section.** For each candidate, do these steps in order.
   1. Run this Grep on the ADR file, with `-A: 2`: `^(lifecycle|amended|superseded_by|amended_by):`
   2. If the ADR file does not agree with the index, the ADR file is correct.
      Add to Gaps: "The generated index is stale. Run `/architecture:index`."
   3. If the Grep shows a `superseded_by` value that step 4 did not see, do step 4 for this file.
   4. Grep `^## ` in the file, then Read the `## Decision` section.
   5. If the file has no `## Decision` heading, Read from the H1 line to the first `## ` heading,
      with a limit of 60 lines.
   6. If the Grep of item 1 shows `amended` or `amended_by`, also Read each `^## Amendment`
      section. The Decision section alone is not the decision in force.
   7. Read one more section only when the question asks for it. The reason is
      `^## (Why|Decision journey|Decision drivers|Rationale)`. The options are
      `^## (Alternatives|Rejected alternatives|Options)`. The cost is
      `^## (Consequences|Operational consequences)`.
   8. Check that the first line that each Read returns is the expected heading.
   9. Report what was recorded, not what the code now does. When a decision looks stale against
      the code, say so in Gaps. Do not correct the record, because this skill only reports it.
6. **Graph walk.** The hop limit is 1. For each opened ADR, run these 2 Greps on
   `<dir>/links.tsv`. The first pattern finds the out-edges, and the second finds the in-edges:

   ```
   ^<arch><file>\t(supersedes|superseded_by|amends|amended_by|deviates_from|refines|parent_spec)\t
   \t(deviates_from|refines)\t<arch><file>\t
   ```

   - The 4 keys with two stored sides are already in the out-edge rows. Thus the in-edge pattern
     names only the 2 keys with one stored side.
   - Grep `related` rows only when the question asks for context. Use `^<arch><file>\trelated\t`
     and `\trelated\t<arch><file>\t`.
   - Walk order: (1) supersede, (2) amend, (3) `deviates_from` in the two directions, (4)
     `refines` in the two directions, (5) `parent_spec`, (6) `related`.
   - Classify each neighbour from its row: `target_state`, `target_status` and `note`. No more
     calls are necessary.
   - For walk orders 1 to 4, get the index line of the neighbour. Open the neighbour by step 5
     only if that line bears on the question. Open a maximum of 3 neighbour bodies. Walk orders
     5 and 6 are lines only.
   - A second hop is permitted only along a supersede edge or an amend edge.
   - Do not open the body of a target whose `target_state` is `url` or `missing`, because the
     corpus holds no body for it. Keep its row, and list a `missing` target in Gaps.
7. **Archive.** When a target has the `target_state` `archive` and its `note` has `now=`, use
   each file that `now=` names in place of the target, and cite the archive file name in
   Sources. Open an archived body only when the question is about history.
8. **extra_corpora.** Expand each `extra_corpora` glob relative to the repository root. Grep the
   matches for the terms, then open only the matching artifacts and the cited lines near the
   hit. An extra corpus has no index and no edge file. A missing extra corpus is a gap, not an
   error. An unresolved or empty ADR corpus is a misconfiguration: lead Gaps with that fact.
   Never answer as though the ADR record was read, because a caller reads Decision recall as
   the record.
9. **Set question.** If the question is about all the decisions of one area, Read
   [resources/graph-walk.md](resources/graph-walk.md) and use its set-question procedure in place
   of steps 3 to 6.
10. **Stop rule.** Stop at the first of these conditions:
    - Each part of the question has a cited decision with the lifecycle `accepted`, or a cited
      proposed ADR that the answer gives as a candidate. The neighbours of walk orders 1 to 3 of
      that decision are classified.
    - The index shows that the corpus is silent on that part. A search with no hit is a gap, not
      a "no". Gaps says "no index hit", not "no record".
    - 5 ADR bodies are open.
    - 12 section Reads are done. The agent cannot measure tokens, so the limit is a count.

    In each case, list in Gaps each candidate and each neighbour that was not opened.
11. **Proposed records.** When the chain end of a superseded ADR is proposed, the answer states
    these 3 facts: the old record is superseded, the successor is proposed, and no accepted
    record covers this part. If an accepted ADR amends the proposed successor, the answer names
    it.

## Clarification behavior

- In `human` mode, ask one concrete, plain-language clarification that names the ambiguity and
  offers choices when possible.
- In `subagent` mode, return exactly `CLARIFICATION_NEEDED: <ambiguity>` and stop.
  Do not use AskUserQuestion in `subagent` mode, because no person is there to answer. The
  steps are the same in the two modes.

## Status normalization

Apply the per-corpus rules and strongest-signal ordering in
[resources/corpus-and-status.md](resources/corpus-and-status.md). Unmatched statuses are
unknown / not authoritative and require a Gaps note.

## Output contract

Always return these sections in this order. State the status of each cited ADR.

**Decision recall**

State what was recorded as decided. Cite every claim as `path:line`; a claim with no citation is a
guess, not an answer. Recommendations go in the third section. Never present an inference as
a recorded decision, and never invent a decision that the corpus does not hold, because the
reader acts on this section as fact.

**Why**

Explain recorded rationale, alternatives, consequences, or context from the same cited artifacts.
Cite each claim as `path:line`.

**What this means for your question**

Start with `Inference:`. Give the recommendation or interpretation visibly separate from recorded
decisions.

**Gaps**

State what the record does not cover, including missing artifacts, unknown statuses, status
mismatches, ambiguous supersession, or silence on the user's specific scenario. An unrecorded
decision is a gap, not a "no". Add
each of these 5 lines that applies:

- No index, or a stale index.
- The neighbours that were not opened, with the count and the relation key.
- Each `missing` target that the walk found.
- Each derived index line that was used. A silent result is weaker for a line with no text.
- "No index hit", with the count of bodies that name the term.

**Sources**

List every cited artifact with its `path`, its raw status, and its normalized treatment. Add
"reached by", with one of these values: `index`, `register`, `title grep`, or
`edge:<key> from <file>`. Add "now", with each chain end.

## The rest of the question

When the shortcuts above leave the question unanswered, load the `knowledge:ask`
skill. Give it the question and the start nodes that you found: each ADR as
`adr:/<file name>`, or `adr:/index.md` when you found none. It walks the
graph one step at a time, and it follows a `parent_spec` such as
`system-design:/areas/data.md` into the system design.
