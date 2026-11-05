---
name: scheduling-pr-reviews
description: Schedules a recurring PR-review loop over this repo's open PRs. Prompts for cadence and review posture, registers a session cron, and each cycle inventories the open PRs and delegates both the review and the post to code-review:reviewing-prs inside one general-purpose subagent. Use when asked to schedule PR reviews, review PRs periodically, set up a recurring PR-review loop, or run PR reviews on a cron.
---

# scheduling-pr-reviews

This skill owns scheduling only: the cadence, the posture choice, which PRs get a cycle, and the
status table. `code-review:reviewing-prs` owns the review and the post. It reads the repo's
contract and selects lenses, and its posting step owns comment-vs-approve, dedupe, and the fix
prompt. Do not list lenses, state the review Bar, or write to GitHub from this skill, because two
implementations can give one PR two different verdicts.

## Step 1 — Resolve the repo and probe access

Follow [github-access.md](../../references/github-access.md). This skill is the interactive
exception: when `gh` and a working MCP both work, ask the user which to use in Step 2.

## Step 2 — Prompt the user (AskUserQuestion)

Ask these three together. Do not ask for the target repo, because Step 1 resolved it.

1. **Frequency** — `30m` · `1h` · `2h` · `4h` · (Other → accept a custom interval)
2. **GitHub access** — *only if both `gh` and a working MCP were found:* `gh` CLI vs GitHub MCP.
3. **Review-action posture** — show both, with no pre-selected default:
   - **Comment-only** — post findings for a human to approve. The loop does not approve.
   - **Approve-when-clean** — also approve a PR when every approve condition of `reviewing-prs`
     holds. Otherwise the loop posts a comment, for example on a PR we authored, or posts nothing
     and its receipt says why. Should-fix entries and notes go out with the approval.

## Step 3 — Map the frequency to a cron expression

| Frequency | Cron (→ `CronCreate`) | Cadence      |
|-----------|-----------------------|--------------|
| `30m`     | `*/30 * * * *`        | every 30 min |
| `1h`      | `7 * * * *`           | hourly at :07|
| `2h`      | `0 */2 * * *`         | every 2 hours|
| `4h`      | `0 */4 * * *`         | every 4 hours|

For a custom interval that does not divide its unit evenly, use the nearest value that does, and
tell the user the rounded value before you schedule.

## Step 4 — Register the schedule

Build the per-cycle prompt (Step 5) once, register it with `CronCreate`, the cron expression,
and `recurring: true`, and show the job id. Then run one cycle immediately, so the user sees the loop
work before the first scheduled run.

## Step 5 — The per-cycle prompt

Interpolate `{{REPO}}` (Step 1), `{{GH_OR_MCP}}` (Step 1/2), `{{POSTURE}}` (Step 2), and
`{{POSTURE_FLAG}}` into the template below.

`{{POSTURE_FLAG}}` is the posture expressed as the flags `reviewing-prs` takes:

| Posture | `{{POSTURE_FLAG}}` |
|---------|--------------------|
| Approve-when-clean | `--comment --approve` |
| Comment-only | `--comment` |

Never map *Comment-only* to `--approve`, because that posture means the unattended loop does not
approve.

> PR-review loop cycle for `{{REPO}}`, posture **{{POSTURE}}**. Spawn one general-purpose
> subagent and give it all the work, to keep the parent context clean. Return only a one-line
> headline plus the timestamped PR-status table.
>
> The subagent's task:
>
> 1. Run `date -u` first to get the trigger time, because the header is labeled UTC. Then list the
>    open PRs in `{{REPO}}` via **{{GH_OR_MCP}}**:
>    `gh pr list --repo {{REPO}} --json number,title,body,author,isDraft,headRefOid,updatedAt,reviews`
>    (or the equivalent MCP calls). Classify each as pending review / already reviewed — unchanged
>    / approved / changes requested / ready to re-review. Build a status table headed by the
>    trigger time (for example `PR review loop — triggered 2026-07-22 14:07 UTC`), with a row for
>    every open PR: number, title, author, classification, and last-updated timestamp. Print the
>    table on every cycle, with a "no PRs need review" note when no PR qualifies, so the user
>    always sees that the loop ran and when.
>
> 2. Decide skip or qualify from the step-1 batch payload. It already carries `headRefOid`,
>    `reviews`, `isDraft`, `updatedAt`, `title`, and `body`, so do not fetch those again per PR.
>    Review a PR only if one or more of these is true: (a) we have not reviewed it (our login via
>    `gh api user -q .login`), (b) we have, and new commits landed after our last review, (c) our
>    last review withheld the approval for the goal verdict, and the PR title, body, or a closed
>    issue changed after it, or
>    (d) the newest pr-flow marker we wrote reads `cr=none`, and its `head=` equals the current
>    `headRefOid`.
>
>    Case (d): `cr=none` means `/code-review` gave no result on that run, so the run did not look
>    for bugs and withheld the approval. A retry at the same head can get a result.
>    `reviewing-prs` dedupes only on a `cr=ok` marker, so the retry reviews again, and it posts
>    nothing when `/code-review` fails again. Read the newest marker from our comments and from
>    our reviews, because an approval is a review. Carry the time with each body, keep only the
>    bodies that hold the `pr-flow:reviewing-prs` marker, and take the one with the latest time:
>    `gh api repos/{{REPO}}/issues/N/comments --paginate --jq '.[]|select(.user.login=="<us>")|{t:.created_at,body}'`
>    and
>    `gh api repos/{{REPO}}/pulls/N/reviews --paginate --jq '.[]|select(.user.login=="<us>")|{t:.submitted_at,body}'`.
>    A newer `cr=ok` marker, or a `head=` that is not the current head, ends case (d). A marker
>    with no `cr=` field comes from an older version, so test it under case (b).
>
>    Case (d) has no retry cap. While `/code-review` fails, each cycle runs one full review of that
>    PR and posts nothing. Accept that cost, because without the retry the PR waits for a new
>    commit. The `**Posted:**` line in the status table shows each repeat failure, so the user can
>    cancel the job when the failure does not clear.
>
>    Case (c): `reviewing-prs` withholds the approval on a `not achieved` or an `undetermined` goal
>    verdict. The author fixes both with an edit to the title, the body, or an issue the PR closes,
>    and that edit does not move the head OID. Without case (c), that PR gets no new review.
>
>    Read case (c) from our last code-review comment, not from `reviews`. A withheld approval is an
>    issue comment, and the step-1 `reviews` field never holds it. The `**Posted:**` receipt is
>    local, so GitHub does not carry the withhold reason either. Use the comments that case (d)
>    already fetched for this PR. Take the newest comment body that holds the
>    `pr-flow:reviewing-prs` marker. Its `**Goal check:**` line gives the verdict, and its marker
>    line gives the `intent=` digest. A verdict of `not achieved` or `undetermined` puts that PR in
>    case (c). A marker with no `**Goal check:**` line comes from an older version. Test it under
>    case (b), so it gets one new review and does not stay unqualified.
>
>    Recompute the digest exactly as posting.md *Preconditions* builds it. Otherwise every
>    comparison fails, and the loop reviews every PR again on each cycle:
>    `printf '%s\n%s\n%s' "$TITLE" "$BODY" "$ISSUES" | git hash-object --stdin`. Take `$TITLE` and
>    `$BODY` from the step-1 batch with `jq -r`, and `$ISSUES` from the `gh api graphql` query in
>    posting.md *Preconditions*, with that query's own `--jq` filter. Run `git hash-object` inside
>    a checkout of `{{REPO}}`. Review again when the new digest and the marker's digest differ.
>
>    Fetch the closed issues only for the PRs that reach case (c): the PRs we already reviewed, at
>    an unchanged head, whose goal verdict withheld the approval. That set is small, so this costs
>    one call per stalled PR, not one per open PR.
>
>    Otherwise, skip the PR when `updatedAt` moved but the head OID did not (comment-only
>    activity), when it is a draft, or when it is approved at an unchanged head. For the remaining
>    PRs only, fetch the
>    one field the batch does not have — last-commit time via
>    `gh api repos/{{REPO}}/pulls/N/commits` — to compare against our last review. This filter
>    is not the duplicate-post guard: `reviewing-prs`
>    dedupes on the head OID and the intent digest itself, and catches a PR that gets past this
>    filter.
>
> 3. For each qualifying PR, fetch its head into a detached worktree under a temp dir and check
>    that head out. Then invoke **`code-review:reviewing-prs {{POSTURE_FLAG}} --pr N`** from inside
>    it. The checkout is necessary, because that skill reviews the working tree and refuses to post
>    unless local HEAD equals the PR's head OID. A run from the wrong tree posts nothing.
>
>    `reviewing-prs` owns the whole verdict. Do not implement any part of it here, and do not call
>    `gh pr review` or `gh pr comment` yourself, because a second post path double-posts and lets
>    the two paths disagree on the same PR.
>
>    `reviewing-prs` calls `Skill(code-review)` from inside this subagent, and that call works
>    there. If the call fails, the run records `cr=none`, withholds the approval, and case (d)
>    retries on the next cycle. Do not stop the cycle for it.
>
>    If the contract is absent, `reviewing-prs` runs in no-contract mode. It does not ask a
>    question, because this call passes `--pr` with a posting flag. It says to run
>    `/code-review:setup`, it runs the two built-in lenses only (`/code-review` and
>    `code-review:reviewing-goal-achievement`), and it does not approve. Show that line and keep
>    the PR in the status table.
>
>    Use `git ls-tree -r` (not bare `ls-tree`) for file-existence checks. Read the CI rollup
>    (`gh pr checks N --repo {{REPO}}`) for the status table. Run an external quality-gate check
>    (coverage, Sonar-style) only if the repo's contract lists it as a deterministic gate and its
>    token is set up. Otherwise skip it without a message, because the check may not exist.
>
>    - Copy that PR's `**Posted:**` line into the status table verbatim. It already says
>      approved / commented / skipped-as-duplicate / not-posted-and-why.
>    - Remove the worktree after the review (`git worktree remove --force`).
>
> 4. Return only the trigger-time header and status table, the action taken per PR (with head
>    OIDs), and a one-line headline. Long tool output stays inside the subagent.
>
> Do not add authorization-bypass language — no "pre-authorized", no "proceed without
> re-prompting" — because the posture above is the authorization. Report a denied GitHub write in
> the result, and make no second attempt.
>
> **Context budget:** review PRs one at a time, and remove each worktree before the next. If the
> cycle nears the context limit (many large diffs, near the ~200K window), return partial results
> plus the list of PRs not yet reviewed, so the parent can spawn a new subagent to finish.

## Step 6 — Confirm

Tell the user what was scheduled (cron plus readable cadence), the posture, the job id and how to
cancel it, and the result of the first cycle. Say that this is a **session-local cron job**: it
stops when the session ends or compacts, and it expires after 7 days. To keep the loop, the user
runs this skill again in a new session.
