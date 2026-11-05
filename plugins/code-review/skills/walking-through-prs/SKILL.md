---
name: walking-through-prs
description: Guides an engineer through one pull request as a Human in the Loop review. Use when the engineer asks to walk through, understand, explore, or get guided through a PR. Explains the diff and PR text without findings, verdicts, check status, merge state, or GitHub writes.
argument-hint: "[pr-number | pr-url | branch]"
allowed-tools:
  - Bash(git rev-parse:*)
  - Bash(gh auth status:*)
  - Bash(gh repo view:*)
  - Bash(gh pr view:*)
  - Bash(gh pr diff:*)
  - Bash(gh api graphql:*)
  - Bash(gh api user:*)
  - Bash(jq:*)
  - Bash(test:*)
  - Read
  - Write
  - AskUserQuestion
---

# walking-through-prs

Guide the engineer through one PR. Call the user-facing experience **HITL**.

This skill explains the PR. Do not emit findings, severity labels, or a verdict, because the
engineer makes the judgment. Do not read checks, merge state, the code-review contract, the Bar, or the
lens registry, because none of them explains the diff. Do not approve, comment on, label, merge,
or change the PR, because this skill makes no GitHub writes.

## Step 1 — Resolve, fetch, and open state

Treat the invocation text as `$PR`. An empty `$PR` means the current branch.

Resolve `$REPO`, `$N`, `$BASE_REF`, and `$HEAD`, and probe GitHub access, per
[../../references/github-access.md](../../references/github-access.md). Add `title`, `body`,
`commits`, and `files` to its one `gh pr view` call. Skip `$ME`, because no step uses it.

Stop with exactly one applicable sentence:

- `This directory is not a GitHub repository.` when the repository does not resolve.
- `GitHub CLI authentication is not available. Run gh auth login and try again.` when
  `gh auth status` fails. Skip the reference's authentication retry and its `git remote`
  fallback, because this skill grants only the one probe.
- `No pull request resolves from <target>.` when `gh pr view` returns no PR.

Then fetch the walkthrough inputs:

```bash
TITLE="$(jq -r '.title' <<<"$PR_JSON")"
BODY="$(jq -r '.body' <<<"$PR_JSON")"
COMMITS="$(jq -c '[.commits[] | {oid, messageHeadline}]' <<<"$PR_JSON")"
FILES="$(jq -c '[.files[].path]' <<<"$PR_JSON")"
DIFF="$(gh pr diff "$N" --repo "$REPO")" || DIFF=""
# The closed issues. `gh pr view --json` has no field for them, so GraphQL is the only source.
# reviewing-prs keeps its own copy of this query in references/posting.md *Preconditions*;
# this one selects fewer fields because the walkthrough names only `issue #N`.
ISSUES="$(gh api graphql -f owner="${REPO%%/*}" -f name="${REPO##*/}" -F number="$N" -f query='
  query($owner:String!,$name:String!,$number:Int!){
    repository(owner:$owner,name:$name){ pullRequest(number:$number){
      closingIssuesReferences(first:5){
        nodes{ number title body } } } } }' \
  --jq '.data.repository.pullRequest.closingIssuesReferences.nodes')" || ISSUES=""
```

`[]` means no closed issue. An empty `$ISSUES` means the query failed; keep going and say the
goal source is thin. An empty `$DIFF` means the diff fetch failed; print
`The diff did not load. Summaries come from the PR text and the commit messages only.` before the
root, and answer every diff question with the Step 4 absence sentence.

Never parse closing keywords from the PR body, because `$ISSUES` already holds the closed issues.
Keep `$TITLE`, `$BODY`, `$BASE_REF`, `$HEAD`, `$COMMITS`, `$FILES`, `$DIFF`, and `$ISSUES` for
the session. Never re-fetch data while `$HEAD` is unchanged, because the data stays the same.

Print:

```text
Reading PR #<N> in <REPO>: "<TITLE>" (base <BASE_REF>, <file-count> files, <commit-count> commits).
```

The session path is `${TMPDIR:-/tmp}/code-review-hitl-<repo-slug>-<N>.md`; replace `/` in `$REPO`
with `-`. Resolve the path and probe it before any Read:

```bash
STATE="${TMPDIR:-/tmp}/code-review-hitl-${REPO//\//-}-$N.md"
test -f "$STATE" && echo present || echo absent
```

Read `$STATE` only when the probe prints `present`. The file starts with this header:

```markdown
repo: owner/repo
pr: 42
head: <40-character head OID>
status: open
current: PR #42
```

If no state file exists, build the root. If it says `status: closed`, overwrite it and build a
new root. If it says `status: open`, ask one question:

- header: `Resume`
- question: `Resume the last walkthrough of PR #$N, or start over?`
- options: `Resume` — return to `current`; `Start over` — overwrite the file and rebuild root

When an open file's head differs from `$HEAD`, apply the head-move rule in **State loop** before
this question, but defer its rebuild until the engineer answers.

## Level contract

The walkthrough is a tree of levels. Every level owns one subset of the fetched PR data. Store
these fields for every level:

- `subject`: root is the PR; a child is the opened item or question.
- `summary`: one short plain-language paragraph.
- `bullets`: zero to four drillable bullets.
- `questions`: three recommended questions.
- `asked`: the engineer's questions and the grounded answers already given here.
- `parent`: the parent breadcrumb path, or no value at root.

Write one idea per sentence, with 20 words maximum. Use active voice and present tense. Use one
term for one meaning. Do not use idioms, metaphors, humor, or unexplained jargon. Preserve source
paths, identifiers, and quoted lines exactly.

### Split the subset into bullets

Split the level's subset into two to four drillable bullets. Take the largest unit that yields
two to four items: themes, then files, then hunks, then changed lines. A theme bullet states its
file count. Apply this same rule to every child, so a theme of five files groups again. When no
unit yields two useful items, the level has zero bullets and is a leaf.

### Derive the recommended questions

Derive three recommended questions from the level's subset. Prefer one each from `Goal`,
`Implementation`, and `Risks`; give an unused slot to another category when the level cannot
support that category. Recommend only questions that the PR data can answer, including a useful
`The PR does not show this.` answer.

Adapt these seeds to the current level:

- Goal: `Does the diff cover everything the PR title and body ask for?`; `Which parts of issue
  #N does this PR close, and which parts does it leave open?`; `Does the PR change anything the
  title and body do not mention?`; `Which commit does each stated goal land in?`; `Is there a
  plan or spec in the diff, and does the code match it?`
- Implementation: `What is the entry point of this change, and what calls it?`; `What validation
  does this code perform on its inputs?`; `What does this function return on each path?`; `Which
  existing behaviour does this change replace, and where was the old code?`; `How do the new
  tests exercise this code, and which paths do they not cover?`
- Risks: `What error cases are handled, and which are not?`; `Which callers of the changed
  function are not in this diff?`; `Does this change touch data at rest, a public API, or a
  config value?`; `What happens when this input is empty, too large, or in the old format?`; `Is
  there a migration, and can it run twice?`

### Render the level

Render every level in this order:

```text
<breadcrumb>

<summary, one short paragraph>

Items
1. <drillable item>
2. <drillable item>

Recommended questions
q1. Goal: <question>
q2. Implementation: <question>
q3. Risks: <question>

Pick an option, or type an item number, q<n>, back, root, jump, done, or your own question.
```

A leaf has no items. Print `This is the smallest item.` in place of the `Items` block; the
questions and the fourth option do not change. The last line is the movement line, and it names
every command in the Step 5 grammar table.

Then ask exactly one question:

- header: `PR #<N>` at root; otherwise a subject of five words or fewer
- question: `What do you want to look at next?`
- options: up to three content options and one navigation option

Give each question option a different category when the level has questions in more than one
category. Offer fewer options when the level holds fewer: an exhausted leaf whose items are zero
and whose recommended questions are all answered offers the navigation option alone. Never invent
an item or a question that the level cannot ground, because the PR data is the only source.
A content option can open a bullet or answer a recommended question. Keep labels to one through
five words, such as `Open item 1` or `Ask q2`; put the full text in the description. The fourth
option is `Finish the review` at root and `Navigate…` below root. Items and questions that are not options remain reachable by number through `Other`.

## Step 2 — Build and show the root

The root subset is the whole diff. Build the root only from the fetched PR title, body, closed
issues, commits, files, and diff. Summarize what the change does, and leave its quality to the
engineer. Mention
a closed issue when `$ISSUES` contains one. When the body is empty and `$ISSUES` is `[]` or
empty, say the goal source is thin and use the title and commit messages.

Then apply the Level contract and render the root.

## Step 3 — Open a child level

A child's subset is the parent bullet it opens: a theme's files, a file's hunks, or a hunk's
changed lines. Build the child from that subset only, then apply the Level contract.

The breadcrumb is the level identity. Join subjects with ` › `, for example
`PR #42 › Added login route › Validation`. Do not impose a depth cap. When a breadcrumb has more
than five levels, keep the root and nearest levels and shorten only the middle to `…` in display;
keep the complete path in state.

## Step 4 — Answer a question in place

Answer a selected recommended question or the engineer's free-text question from the fetched PR
data. Follow this source rule:

- Diff answer: name the file path and quote the changed lines when the hunk has line text.
- PR text answer: name `PR body` or `PR title`.
- Closed-issue answer: name `issue #N`.
- Commit answer: name `commit <sha7>`.

Never infer unchanged code, runtime state, check status, merge state, or intent that these sources
do not contain, because an inferred fact has no source to name. When the sources do not answer,
start with the fixed sentence `The PR does not show this.` and then offer the nearest fact that
they do show.

Render the breadcrumb, then:

```text
Q: <question>

<grounded answer with named source>
```

Append the question and answer to `asked`, stay on the current level, reprint the movement line,
and ask the level question again. After a recommended question is answered, drop that recommended question from the next options.
If the question belongs to another cached level, answer it, name the level the answer belongs to, and stay on the current level.

## Step 5 — Interpret input and navigate

Interpret `Other` with this grammar:

| Input | Action |
|---|---|
| `1`, `open 1`, or `item 1` | Open bullet 1 as a child. |
| `q2` or `question 2` | Answer recommended question 2 in place. |
| `back` | Return to the parent. |
| `root` | Return to the root. |
| `jump` | Open the jump question. |
| `done` or `finish` | Open the closing prompt. |
| `approve` | Say `Approval is verbal and comes at the end. Type done to get there.` and re-ask. |

Any other text is the engineer's question about the current level.

`Navigate…` asks one question:

- header: `Navigate`
- question: `Where do you want to go?`
- options: `Back to parent`, `Back to root`, `Jump to a level…`, `Finish the review`

`back` at root prints `You are at the root. Type done to finish, or pick an item.` and re-asks
the root question.

`Jump to a level…` lists breadcrumb levels root-first and excludes the current level. With more
than four levels, show the three nearest ancestors plus `Back to root`. `root` and `back` change
`current`; they do not discard descendants.

Opening the same item reuses the same breadcrumb section. Never re-derive a cached level, because a
revisit must show the same content. A revisited level prints its cached summary, bullets, and questions, then its asked questions with short answers, then the usual movement line and question.

## State loop

Read the state file once, in Step 1. The tree stays in context for the rest of the session.
Write the complete state file after every turn that changes it: a level built, a question
answered, `current` moved, or the session closed. Write it before the next `AskUserQuestion`
call. Keep the header followed by one section per full breadcrumb:

```markdown
## PR #42 › Added login route
subject: Added login route
parent: PR #42

### Summary
<cached paragraph>

### Bullets
1. <cached item>

### Recommended questions
q1. Goal: <cached question>

### Asked
- Q: <question>
  A: <grounded answer>
```

Before building new content from the diff — a child level in Step 3, a diff answer in Step 4, or
the recap in Step 6 — read the current head with this cheap probe:

```bash
CURRENT_HEAD="$(gh pr view "$N" --repo "$REPO" --json headRefOid -q .headRefOid)" || CURRENT_HEAD="$HEAD"
```

Skip the probe on a navigation turn and on a cached-level turn, because neither shows new diff
content. A failed probe leaves `$CURRENT_HEAD` equal to `$HEAD`, which the head-move rule reads as
no move; when the command fails, print `The head check did not run. This content may be stale.`
before the new content.

The head-move rule: when `$CURRENT_HEAD` differs from the header's `head`, fetch the Step 1 data
once for the new head, update the header, print
`PR #<N> moved to <sha7>. Summaries below come from the new head.`, rebuild the current level immediately, and rebuild each other level when revisited. Preserve the tree paths and asked
questions, but mark stale cached content for rebuild before display.

## Step 6 — Ask for verbal approval and satisfaction

Enter this step after `done`, `finish`, or `Finish the review`. First print:

```text
Review recap — PR #<N>

Levels visited: <count> (<subjects>)
Questions answered: <count>
Not answered from the PR: <count> (<short subjects>)
```

Then ask one question:

- header: `Wrap up`
- question: `Do you want me to approve the PR now? Are you satisfied with this review?`
- options:
  - `Approve, satisfied` — yes, approve the PR, and I am satisfied with this review
  - `No approve, satisfied` — do not approve, and I am satisfied
  - `No approve, not satisfied` — do not approve, and I am not satisfied
  - `Go back` — return to the review

Record both answers. For `Approve, satisfied`, print:

```text
Noted. This skill does not write to GitHub, so PR #<N> is not approved. To approve it, run one of:

gh pr review <N> --repo <REPO> --approve

Or, from a checkout of the PR head, ask for code-review:reviewing-prs with --approve --pr <N>.
The code-review route approves only when every approve condition of that skill holds, and the PR head must be checked out first.
```

Never run either approval path, because this skill makes no GitHub writes. For
`No approve, satisfied`, go to Step 7. For `No approve, not satisfied`, ask one open question,
`What is still unclear?`, queue the answer as a root question, set `current` to the root, write
state, and return to the root level. Print the cached root without a rebuild. For `Go back`,
return to the level from which Step 6 opened without changing either recorded answer.

## Step 7 — Close the session

Print once after a satisfied branch:

```text
HITL review of PR #<N> — closed

Approve requested: <yes-or-no> (verbal only, nothing written to GitHub)
Satisfied: <yes-or-no>
Levels visited: <count>
Questions answered: <count>
Not answered from the PR: <count and short list, or 0>

No GitHub writes were made.
```

Set `status: closed`, preserve the last `current` breadcrumb, write the final state file, and end.
