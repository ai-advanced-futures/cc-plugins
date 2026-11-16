---
description: Answers questions about past architectural decisions from the ADR graph, read-only. Use for "/architecture:ask", "why did we choose X over Y", "remind me why we did X", "is this still true", "did we ever decide X", "what's our stance on X", and fires before an architectural boundary changes so past decisions are read before new ones are made.
allowed-tools: Read, Grep, Glob, AskUserQuestion, Skill
---

# ask

Answer a question from what the ADR corpus already records. This skill is read-only. The normal evidence reader
is `knowledge:ask` (knowledge 2.0.0 or later). Keep the source and history checks below: ranked search alone
cannot establish a current decision. The inputs are `question`, and `mode`: `human` for `/architecture:ask`, or
`subagent` for a delegated lookup.

For source and edge searches in steps 4 to 8 or exact routing, use the search form in
[resources/corpus-and-status.md](resources/corpus-and-status.md). The initial navigation flag check
needs only a match for `^okf_version:`, not a term search.

## Procedure

1. **Entry.** Read `.claude/adr.json`. Get `dir`, `register.path`, `archive_dir` and
   `extra_corpora`. If `dir` is empty or missing, put that fact first in Gaps and stop.
2. **Evidence first.** Read the `adr` entry of `.claude/knowledge.json` and check only whether `<dir>/index.md`
   has `^okf_version:`. Leave term searches for exact routing. For a normal question with a local registered ADR
   corpus and generated navigation, load `knowledge:ask` with the question unchanged, before term searches or
   ADR body reads. Use its cited ADRs as candidates in step 3. Pass only the question, because the reader
   accepts no caller-selected nodes or filters. A graph name is a search term, not a filter. Reject evidence
   outside the configured corpora. Then do steps 4 to 8 and the output contract here, not the reader's short
   answer alone. Check the index lines only for the selected candidates and neighbours. For a complete set,
   missing registration, remote entry, legacy register, or no useful ADR evidence, use **Exact routing** below,
   because ranked search can omit a recorded decision. Keep `extra_corpora` in step 8 even when the shared
   reader cannot search them.

   **Exact routing.** Search `<dir>/index.md` for `^okf_version:`.
   - **a. The search has a hit. Navigation is on.**
     1. Select the most exact term of the question: a product name, a technology name, or the
        least frequent noun. Search `index.md` for it, and ignore letter case. For a term with
        2 spellings, use the pattern `a|b`.
     2. If the search gives more than 10 lines, select a second term and search one time more with
        the pattern `a.*b|b.*a`. `a` is term 1 and `b` is term 2. Do not Read the hits, because
        the index lines already hold what step 3 ranks.
     3. If the result still has more than 10 lines, run no more searches. Select the candidates
        from the lines that the search returned, because they are already loaded.
     4. If the first search gives 0 lines, try one time with other words for the same subject.
     5. If there is still no hit, or if the question names a decision, do items 1 to 3 on
        `<dir>/<archive_dir>/index.md`.
     6. If there is still no hit, Read the `## Areas` list. If no area name bears on the
        question, the corpus is silent on this part. Run one search
        for file names, ignore letter case, for term 1 in `<dir>` with `--include='*.md'`, and
        one in `<dir>/<archive_dir>`. Gaps then says: "N bodies name the term,
        and no index line does." When a result has 60 files, write "60 or more". Then stop for
        this part.
     7. If an area bears on the question, Read only its `### accepted` lines first. A search for
        `^##` gives the line numbers.
   - **b. The search has no hit, or the file does not exist.**
     1. **Read the register first**, at `register.path`, by search for the same terms, with the
        form of items a.1 to a.3. Never Read the register in full, because a search returns only
        the matching lines, and a full Read loads one line for each ADR in the corpus.
     2. If the register gives nothing, search `^title:.*<term>` in `<dir>` with `--include='*.md'`,
        and ignore letter case. `<term>` is term 1. A plain `^title:` search gives one line for
        each ADR, and `head -n 60` cuts it.
     3. Add to Gaps: "No generated index. Run `/architecture:index --nav`."
3. **Candidates.** Keep a maximum of 5 candidates. Rank them by a match in the title or the
   text, then accepted before proposed, then the newer date. A `(derived)` line has less weight.
   A proposed ADR is a candidate, not a decision in force. If 2 or more candidates give
   different answers, and the question does not select one, use the clarification behavior.
4. **Successor first.** Do this for each candidate, and not only for a candidate whose line says
   superseded. Search `<dir>/links.tsv` with the pattern `^<arch><file>[[:blank:]]superseded_by[[:blank:]]`. Skip
   this search only when the candidate came from the archive index, and its line shows one `Now:`
   target and no `(partial)`.
   - Look at `target_status`, column 5, of each row. If it is `superseded`, search again for the
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
   - If no `links.tsv` exists, search the ADR file for `^superseded_by:` with `-A 2`. 2 lines
     after the key show a list of 2 values. If the second line after the key is a list item, the
     list can be longer: Read the front matter lines of the file.
5. **Open only the matching ADRs, by section.** For each candidate, do these steps in order.
   1. Run this search on the ADR file, with `-A 2`: `^(lifecycle|amended|superseded_by|amended_by):`
   2. If the ADR file does not agree with the index, the ADR file is correct.
      Add to Gaps: "The generated index is stale. Run `/architecture:index`."
   3. If the search shows a `superseded_by` value that step 4 did not see, do step 4 for this file.
   4. Search `^## ` in the file, then Read the `## Decision` section.
   5. If the file has no `## Decision` heading, Read from the H1 line to the first `## ` heading,
      with a limit of 60 lines.
   6. If the search of item 1 shows `amended` or `amended_by`, also Read each `^## Amendment`
      section. The Decision section alone is not the decision in force.
   7. Read one more section only when the question asks for it. The reason is
      `^## (Why|Decision journey|Decision drivers|Rationale)`. The options are
      `^## (Alternatives|Rejected alternatives|Options)`. The cost is
      `^## (Consequences|Operational consequences)`.
   8. Check that the first line that each Read returns is the expected heading.
   9. Report what was recorded, not what the code now does. When a decision looks stale against
      the code, say so in Gaps. Do not correct the record, because this skill only reports it.
6. **Graph walk.** The hop limit is 1. For each opened ADR, run these 2 searches on
   `<dir>/links.tsv`. The first pattern finds the out-edges, and the second finds the in-edges:

   ```
   ^<arch><file>[[:blank:]](supersedes|superseded_by|amends|amended_by|deviates_from|refines|parent_spec)[[:blank:]]
   [[:blank:]](deviates_from|refines)[[:blank:]]<arch><file>[[:blank:]]
   ```

   - The 4 keys with two stored sides are already in the out-edge rows. Thus the in-edge pattern
     names only the 2 keys with one stored side.
   - Search `related` rows only when the question asks for context. Use `^<arch><file>[[:blank:]]related[[:blank:]]`
     and `[[:blank:]]related[[:blank:]]<arch><file>[[:blank:]]`.
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
8. **extra_corpora.** Expand each `extra_corpora` glob relative to the repository root. Search the
   matches for the terms, then open only the matching artifacts and the cited lines near the
   hit. An extra corpus has no index and no edge file. A missing extra corpus is a gap, not an
   error. An unresolved or empty ADR corpus is a misconfiguration: lead Gaps with that fact.
   Never answer as though the ADR record was read, because a caller reads Decision recall as
   the record.
9. **Set question.** If the question is about all the decisions of one area, Read
   [resources/graph-walk.md](resources/graph-walk.md) and use its set-question procedure in place
   of steps 3 to 6. Select this path before the shared reader; ranked search is not a full set.
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
"reached by", with one of these values: `knowledge:ask`, `index`, `register`,
`title grep`, or `edge:<key> from <file>`. Add "now", with each chain end.

## The rest of the question

For a remaining cross-graph question, load `knowledge:ask` with that question only if it has not already run. A
`parent_spec`, such as `system-design:/areas/data.md`, is source evidence to check locally, not a caller control
for the shared reader. Read necessary linked sources directly. Keep recommendations separate from the ADR
record. In Sources, use `reached by: knowledge:ask` for candidates from the shared reader, then record each
checked successor or amendment as usual. Give all citations as `path:line`.
