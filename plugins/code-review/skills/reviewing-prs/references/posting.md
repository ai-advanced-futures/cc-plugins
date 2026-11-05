# Posting the review to GitHub

Read this when `--comment` or `--approve` was passed. With no flag, the report stays in the
session and none of this runs.

**Two places in code-review write a review verdict, and this is one of them.** This file posts the
automated verdicts. `scheduling-pr-reviews` picks the posture and calls this skill with the
matching flag, so ad-hoc runs and scheduled runs agree on a PR and share one dedupe ledger. Add
new automated posting behavior here, behind a flag. A second `gh pr comment` in an automated path
splits the ledger.

The other writer is the review pane (`/code-review:review-pane`). It posts the reviewer's own
approval from one key press. Dedupe does not apply there, because a person makes each post and can
see what they already posted. The pane never calls this file, and this file never posts for the
pane.

**Post the findings verbatim**, because Step 6 already wrote them in ASD-STE100. A clean review
posts its header and its coverage receipt.

**The posted body describes the diff and nothing else.** Other skills own the checks and the
merge state, and this skill does not read them. So do not state that a check failed, that CI is
red, that the branch is behind its base, that it needs a rebase, or that it has a conflict, because
this skill has no data for that. The only path for such a line is the **Run caveat** line, and
*Post* removes it.

## Contents
- Preconditions
- Dedupe
- Approve condition
- Post
- Receipt

## Preconditions

All of these must hold **for the post**. A failure disables posting only. Still run the full
review, still emit the Step 6 report, and append `**Posted:** not posted — <reason>` to it. Under
the Step 0 hoist, "stop" means stop posting, not stop the run. The one exception is a dedupe hit,
which ends the run.

**GitHub access works** — per [../../../references/github-access.md](../../../references/github-access.md).
Reuse the path the caller already uses, so that the access probe runs one time.

**A PR resolves** — `--pr <number>` if passed, else the current branch's. Fetch every field in one
call. Nothing below fetches again:

```bash
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
ME="$(gh api user -q .login)"
TARGET="${PR:-$(git rev-parse --abbrev-ref HEAD)}"        # --pr N, else this branch
PR_JSON="$(gh pr view "$TARGET" --repo "$REPO" \
  --json number,author,headRefOid,isDraft,body,title,commits)" || PR_JSON=""
N="$(printf '%s' "$PR_JSON"      | jq -r '.number')"
HEAD="$(printf '%s' "$PR_JSON"   | jq -r '.headRefOid')"  # full 40-char OID
AUTHOR="$(printf '%s' "$PR_JSON" | jq -r '.author.login')"
IS_DRAFT="$(printf '%s' "$PR_JSON" | jq -r '.isDraft')"
TITLE="$(printf '%s' "$PR_JSON" | jq -r '.title')"
BODY="$(printf '%s' "$PR_JSON"   | jq -r '.body')"
COMMITS="$(printf '%s' "$PR_JSON" | jq -c '.commits')"

# The issues this PR closes. `gh pr view --json` has no field for them, so GraphQL is
# the only source. GitHub computes this list from the closing keywords in the body and
# from the sidebar link, so never parse the body for `fixes #N` yourself.
# `[]` means the PR closes no issue. An empty string means the call failed. The two are
# different answers, and Step 2 of the lens treats them differently.
ISSUES="$(gh api graphql -f owner="${REPO%%/*}" -f name="${REPO##*/}" -F number="$N" -f query='
  query($owner:String!,$name:String!,$number:Int!){
    repository(owner:$owner,name:$name){ pullRequest(number:$number){
      closingIssuesReferences(first:20){
        nodes{ number title body url repository{nameWithOwner} } } } } }' \
  --jq '.data.repository.pullRequest.closingIssuesReferences.nodes')" || ISSUES=""

INTENT="$(printf '%s\n%s\n%s' "$TITLE" "$BODY" "$ISSUES" | git hash-object --stdin)"  # 40-char
```

reviewing-prs Step 4 passes `$TITLE`, `$BODY`, `$COMMITS`, and `$ISSUES` to
`code-review:reviewing-goal-achievement`. An empty `$PR_JSON` binds the first three to an empty
value; Step 4 states what to do then.

`$INTENT` is a 40-character digest of the title, the body, and the closed issues. It is one part
of the *Dedupe* key. An author fixes a `not achieved` or an `undetermined` verdict with an edit to
the title, the body, or a closed issue. That edit does not move `$HEAD`, but it moves `$INTENT`.

`$HEAD` is the only name for the PR's head OID. Do not add a second variable for it, because two
names can hold two values. An empty `$HEAD` counts as "no PR resolved", because it turns the
dedupe grep into a prefix that matches everything. No open PR is the normal case for a branch that
has no PR yet, not an error:
`**Posted:** not posted — no open PR for this branch`.

**The reviewed tree is the PR head** — `test "$(git rev-parse HEAD)" = "$HEAD"`. A mismatch puts
the verdict for one tree on another tree, and nothing shows the error.
`**Posted:** not posted — local HEAD <a> ≠ PR #N head <b>; check out the PR head first`

**No tracked file has uncommitted changes** —
`D="$(git status --porcelain --untracked-files=no)" || D=failed; echo "code-review: tracked-changes=${D:-none}"; test -z "$D"`.
A failed `git status` fails this check. Read the printed `tracked-changes=` value to select the
receipt below, because shell variables do not stay from one command to the next. Run the check
again at post time, beside *The review actually ran*, because the tree can change during the
review. The check exists because every lens can open working-tree files, so a finding can cite a
line that is not in the PR head. Untracked files do not fail this check, because `git stash` does
not remove them and Step 5 drops a finding only when git confirms its file is untracked. Tell the
user to commit or stash the changes. This skill never stashes, because the changes belong to the
user.
`**Posted:** not posted — uncommitted changes to tracked files; commit or stash them first`
(when it printed `tracked-changes=failed`: `**Posted:** not posted — git status failed`)

**The PR is not a draft** — for both flags. The scheduled loop skips drafts at inventory, and for
one PR the same result is to write nothing.
`**Posted:** not posted — PR #N is a draft (the scheduled loop skips drafts)`

**The review actually ran** — Step 2 did not abort and the diff was not empty. Do not post a
verdict from an empty or aborted diff, because that run reviewed nothing. Check this at post time,
because the Step 0 hoist cannot answer it early.

## Dedupe

Every body this skill posts ends with a marker line:

```
<!-- pr-flow:reviewing-prs head=<headRefOid> lenses=<N> intent=<INTENT> cr=<ok|none> -->
```

`head` is the full 40-char OID. `lenses` is the registry row count from the coverage receipt.
`intent` is the `$INTENT` digest from *Preconditions*. `head` and `intent` are both parts of the
key. A new commit moves `head`. An edit to the PR title, the PR body, or a closed issue moves
`intent`, and that edit alone can change the goal verdict. So a run at the same head with a new
`intent` is a new verdict, not a duplicate.

`cr` is `none` when the `code-review` receipt row reads `no result`, and `ok` otherwise. **Only a
`cr=ok` marker is a dedupe hit.** A `cr=none` run did not look for bugs and withheld the approval,
so the next run at the same head and intent reviews again. Without this rule, one `/code-review`
timeout blocks approval at that head until a new commit.

Run the check only when `$HEAD` is a 40-char OID. An empty one makes the pattern a bare `head=`
prefix. That prefix matches every earlier code-review comment and disables this skill on that PR
forever:

```bash
[ ${#HEAD} -eq 40 ] || { echo "code-review: no head OID — skipping dedupe, not posting"; }
gh api "repos/$REPO/issues/$N/comments" --paginate --jq \
  '.[]|select(.user.login=="'"$ME"'")|.body' | grep -q "pr-flow:reviewing-prs head=$HEAD .*intent=$INTENT cr=ok "
gh api "repos/$REPO/pulls/$N/reviews" --paginate --jq \
  '.[]|select(.user.login=="'"$ME"'")|.body' | grep -q "pr-flow:reviewing-prs head=$HEAD .*intent=$INTENT cr=ok "
```

Run the comments check first, because most posts are comments. On a hit, skip the reviews call.
One hit is enough.

A hit in either store means these commits, with this stated intent, already got this review. Do
not post again, because the review has not changed. Record
`**Posted:** skipped — already reviewed at head <short-sha>`.

**A retry that again gets no code-review result posts nothing.** Before you post a `cr=none`
report, run the two checks above again with `cr=none` in place of `cr=ok`. A hit means this head
and intent already carry the same withheld report. Record
`**Posted:** skipped — code review still gave no result at head <short-sha>`, and do not post. A
`cr=ok` retry posts as normal.

The key is the head OID and not `updatedAt`, because a comment moves `updatedAt` and does not
change the verdict. Without dedupe, a repeating caller posts the same review on every cycle.

## Approve condition (`--approve` only)

Approve only when every condition in the canonical list under *Post* holds. Two of them are about
content: the report has no `### Must fix` entry, and the `**Goal check:**` line reads `achieved` or
`partially achieved`. Do not add a gate here, because the caller that passed the flag already
decided that approval is in scope.

These never withhold approval:

- **A `### Should fix` entry.** It is a real defect that failed the Bar's four-part must-fix test.
  The author decides whether to fix it in this PR.
- **A `### Notes` entry.** Do not read a should-fix or a note again and promote it, because Step 5
  already made that call with the diff in front of it.
- **An `UNVERIFIED` lens.** It describes how one lens ran, and the other lenses still read the
  right diff.

Each case below withholds approval. Post a comment instead, and record the receipt it names.

- **A Run caveat line.** The base may be wrong, so the reviewed diff may not be the PR's changes,
  and "no must-fix" then means nothing. Step 7 strips the caveat, so an approval would carry no
  trace of the doubt. Say nothing about a rebase in the comment. Receipt:
  `**Posted:** commented, approval withheld — review scope uncertain (stale base)`.
- **We authored the PR** (`$AUTHOR == $ME`). GitHub rejects self-approval, so detect it before the
  API call. Name it in the receipt, because a silent change of action misleads the user. Receipt:
  `**Posted:** commented, approval withheld — we authored this PR`.
- **`/code-review` gave no result.** Its receipt row reads `no result`. The run did not look for
  bugs, so "no must-fix" proves nothing. Receipt:
  `**Posted:** commented, approval withheld — code review gave no result`.
- **A goal verdict of `not achieved` or `undetermined`, or no-contract mode.** This table gives the
  result for each verdict:

| `**Goal check:**` verdict | `--approve` result | Receipt |
|---|---|---|
| `achieved` or `partially achieved` | approves, when no must-fix entry | `approved with notes` |
| `not achieved` | comments | `commented, approval withheld — goal not achieved` |
| `undetermined` | comments | `commented, approval withheld — goal undetermined` |
| no-contract mode, any verdict | comments, always | `commented, approval withheld — no contract, built-in lenses only` |

The Goal check sentence names the missing source, so the author knows to write the PR body.

## Post

**Build the body in a file. Do not inline it into `--body "…"`**, because bash runs command
substitution on backticks and `$` inside double quotes, and that executes finding text as shell.
Use a **quoted** heredoc and `--body-file`:

```bash
BODYFILE="$(mktemp)"
cat >"$BODYFILE.raw" <<'PRFLOW_EOF'
…the Step 6 report, verbatim, then the marker line…
PRFLOW_EOF
grep -v '^\*\*Run caveat:\*\*' "$BODYFILE.raw" >"$BODYFILE"    # strip the one local-only line
```

**Run that `grep -v`. Do not remove the line by eye**, because a missed line posts the caveat. It
removes the `**Run caveat:**` line and only that line. On the PR, "base may be stale" reads as
"rebase this branch", which is another skill's verdict. Step 6 defines the label and this command
consumes it, so keep the two spellings identical. The `**Goal check:**` line stays in the body
verbatim, in an approval and in a comment.

**The approve conditions.** This list is canonical. Every other statement of the rule in this
plugin points here. Approve only when every condition below holds:

- the report has no `### Must fix` entry
- `--approve` applies
- we did not author the PR
- the run is not in no-contract mode
- the report carries no `**Run caveat:**` line
- the `code-review` receipt row does not read `no result`
- the `**Goal check:**` line reads `achieved` or `partially achieved`

Should-fix entries and notes go into the approval body.

```bash
gh pr review "$N" --repo "$REPO" --approve --body-file "$BODYFILE"
```

When any condition in that list fails, post a comment:

```bash
gh pr comment "$N" --repo "$REPO" --body-file "$BODYFILE"
```

**Append the fix prompt only when there is a `### Must fix` entry.** A fix prompt asks for a
round-trip, and the two lower buckets exist to prevent one.

```
<details><summary>Fix prompt</summary>

Validate each must-fix finding above against the current diff. Fix the ones that hold and
explain the ones that do not. The should-fix entries and the notes are optional. Run this repo's
gates before you push.

</details>
```

**At a *new* head, do not post unchanged findings again.** If our previous comment raised the same
findings and the new commits did not address them, post a brief reply that the prior findings
still stand. Unaddressed notes alone need no reply, because the author already read them. Post a
full comment only when findings changed or resolved. At an unchanged head and intent, this section
runs only as a retry after a `cr=none` run, because *Dedupe* skipped every other such run.

**Every body this skill posts ends with the marker line**, and that includes the reply that the
prior findings still stand. A body with no marker cannot dedupe, so the next cycle posts it again.

This rule removes the full report only. A write always goes to the pull request at a new head. The
rule never removes an approval and never overrides the goal gate:

- When the approve conditions hold, approve at the new head, even when every remaining entry is a
  repeat. That head has no must-fix finding and no approval yet. Put the lower buckets in the
  approval body and record `approved with notes`.
- When the run is in no-contract mode, the `code-review` row reads `no result`, or the
  `**Goal check:**` line reads `not achieved` or `undetermined`, post one comment at the new head.
  Its body is the brief `prior findings still stand` reply, then the `**Goal check:**` line
  verbatim, then the `code-review` row verbatim when it reads `no result`, then the marker line.
  The row tells the author why approval was withheld, because the marker is not visible. Do not
  put the full report in that body. Record `**Posted:** commented, approval withheld — <reason>`,
  with `<reason>` from the *Approve condition* section.

Never `gh pr review --request-changes`, because this review is advisory and never blocks a merge.
If a write is denied, put the denial in the receipt. Do not retry through another path, because
that goes around the denial.

## Receipt

Append exactly one `**Posted:**` line to the Step 6 report. At the post step, it is one of:

```
**Posted:** approved (head 1a2b3c4)
**Posted:** approved with notes — 2 note(s) (head 1a2b3c4)
**Posted:** approved with notes — 1 should-fix, 2 note(s) (head 1a2b3c4)
**Posted:** commented — 2 must-fix, 1 note (head 1a2b3c4)
**Posted:** commented — 2 must-fix, 1 should-fix, 1 note (head 1a2b3c4)
**Posted:** commented — 2 note(s), no must-fix (head 1a2b3c4)
**Posted:** commented — 1 should-fix, 2 note(s), no must-fix (head 1a2b3c4)
**Posted:** commented — prior findings still stand (head 1a2b3c4)
**Posted:** commented, approval withheld — we authored this PR (head 1a2b3c4)
**Posted:** commented, approval withheld — review scope uncertain (stale base) (head 1a2b3c4)
**Posted:** commented, approval withheld — goal not achieved (head 1a2b3c4)
**Posted:** commented, approval withheld — goal undetermined (head 1a2b3c4)
**Posted:** commented, approval withheld — code review gave no result (head 1a2b3c4)
**Posted:** commented, approval withheld — no contract, built-in lenses only (head 1a2b3c4)
**Posted:** skipped — already reviewed at head 1a2b3c4
**Posted:** skipped — code review still gave no result at head 1a2b3c4
**Posted:** write denied — <the denial, verbatim> (head 1a2b3c4)
```

`approval withheld` names the reason approval did not happen. A should-fix or a note is never that
reason. A run that meets every approve condition and does not end in an approval has a bug.

When a precondition failed, the line is `**Posted:** not posted — <reason>` in that precondition's
own words. Quote it from above. Do not restate it, because two copies of one string drift apart.
