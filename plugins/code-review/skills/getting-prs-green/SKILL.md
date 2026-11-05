---
name: getting-prs-green
description: Drives one PR's checks to all-green — syncs the branch with its base, fixes each failing check from its own CI logs, gates locally, pushes, and re-checks until CI passes or a cap stops it. Use when asked to get PR N green, fix the failing checks, drive a PR to green, or make CI pass on a PR. Never merges, never approves, and never suppresses a check to make it pass.
argument-hint: "[pr-number]"
---

# getting-prs-green

Drive **one PR** to all checks green, then stop and report. Each round: sync with the base, read
what CI actually failed on, fix it, prove it locally, push, wait for CI to re-report.

**References** — read the first two before starting:
- [../../references/loop-engine.md](../../references/loop-engine.md) — the shared control loop:
  trigger-once/run-to-completion, the self-pacing wait, worker liveness, the local gate, and the
  escalation model. This skill supplies `TERMINAL`, `NEW_WORK`, the fix action, and the caps.
- [../../references/github-access.md](../../references/github-access.md) — resolving `$REPO`,
  `$N`, `$HEAD_REF`, `$BASE_REF`, `$ME`, and probing access.
- [../../references/base-sync.md](../../references/base-sync.md) — Step 2's procedure.

Take the local gate from the contract (loop-engine). Do not write a build or test command into
this skill, because each repo has its own gates.

**Scope.** This skill owns **red checks** — the job `getting-prs-merged` explicitly delegates
away. Green is the terminal state. This skill does not merge and does not approve, because
`getting-prs-merged` owns the merge and approval belongs to a human or to `reviewing-prs --approve`.

It is safe to run with `getting-prs-approved` and `getting-prs-merged` on the same PR, because
all its state is on GitHub: the pushed commits, their `pr-flow-green:` attempt trailers (Step 4),
and the check rollup. **Two copies of *this* skill on one PR is the unsafe case** — they share no
claim marker and race on `--force-with-lease`. Before the first fix round, read the attempt
trailers on `origin/$HEAD_REF`, and stop if another run is mid-round.

## Step 0 — Resolve and check out the PR

Resolve and probe per [github-access.md](../../references/github-access.md). Stop if there is
no PR, if `state != OPEN`, or if **the PR is a draft**, because the checks of a draft are
advisory. For a draft, tell the user to mark it ready first.

**Then put the working tree on the PR branch.** Every later step commits and pushes. Without
this step, `getting-prs-green 123` from the default branch commits to the default branch:

```bash
git fetch origin "$HEAD_REF"
git checkout "$HEAD_REF" && git reset --hard "origin/$HEAD_REF"
```

If the working tree has uncommitted changes, **stop and report** and keep the changes, because
they are the user's work.

## Step 1 — Read the PR state (the loop hooks)

One call per round supplies the payload that everything below reads:

```bash
gh pr view $N --repo "$REPO" \
  --json headRefOid,mergeable,mergeStateStatus,statusCheckRollup
```

**Normalize the rollup before you judge it.** The rollup has **one entry per workflow run**, so
a check that failed and then passed on a re-run shows twice, and a stale `FAILURE` stays alive.
An entry is a `CheckRun` (`name`, `status`, `conclusion`, `detailsUrl`) **or** a `StatusContext`
(`context`, `state`, `targetUrl` — no `conclusion`, no `detailsUrl`). Without normalization, a
legacy commit status matches neither hook, and the loop sleeps on a red PR.

```bash
jq -r '[.statusCheckRollup[]
        | {name:   (.name // .context),
           at:     (.completedAt // .startedAt // .createdAt // ""),
           state:  (.conclusion // .state // .status),
           url:    (.detailsUrl // .targetUrl // "")}]
       | group_by(.name) | map(max_by(.at))' <<<"$PR_JSON"
```

**`TERMINAL`** — every normalized entry is `SUCCESS`/`NEUTRAL`/`SKIPPED`, none are
`QUEUED`/`IN_PROGRESS`/`PENDING`/`EXPECTED`, and `mergeStateStatus` is not `BEHIND`. Report and
stop. (`BLOCKED` on approval is fine — that's `getting-prs-approved`'s job, not a red check.)

**`NEW_WORK`**, in priority order:

1. **Base drift** — `mergeStateStatus == BEHIND` or `mergeable == CONFLICTING`. Always first,
   because checks run against the merge of the branch and its base: on a stale branch, a red or
   a green result is not reliable.
2. **Failing checks** — every normalized entry in `FAILURE`, `TIMED_OUT`, `ACTION_REQUIRED`,
   `CANCELLED`, or `ERROR`, minus any that hit the caps in Step 4.

Report a state that is in neither list, because a silent unknown state stops the loop with no
sign. A check that is still running is not work: sleep. `mergeable == UNKNOWN` means GitHub is
still computing: read it again at the next wake.

## Step 2 — Sync the branch with its base

Follow [base-sync.md](../../references/base-sync.md), then return to Step 1 — a sync re-triggers
CI, so the failing set you had is stale.

## Step 3 — Fix the failing checks (one batched round)

Send each failing check to **its own subagent, in parallel**, to keep the logs out of the loop's
context. Each subagent returns a **diagnosis, not a log**: the check name, the file and line the
failure names, the assertion or rule that fired, and at most 20 lines of quoted log. The fix pass
works from this digest, so "it failed" is not a valid return.

- **Get the real failure, not the check name.** For GitHub Actions take the run id from the
  entry's `detailsUrl` — the URL is `…/actions/runs/<run-id>/job/<job-id>`, so match the segment
  after `/runs/`, not the trailing number — then read
  `gh run view <run-id> --repo "$REPO" --log-failed`. For an external check (a `StatusContext` has
  `targetUrl`, not `detailsUrl`) follow that URL. If the contract lists an external quality gate
  with an API, and its token is provisioned, query the API for failing conditions instead of
  its page. **No actionable output → escalate that check**, because a guessed fix
  edits code for no known cause.
- **Known flakes get rerun, not fixed.** If the contract or CLAUDE.md names a check flaky, run
  `gh run rerun <run-id> --failed --repo "$REPO"` and move on. Do not edit code for a flake,
  because the code is not the cause. If you are not sure, read the log: a real failure names a
  file and a line.

Then **one fix pass covers all of them together**, on the PR branch:

1. Diagnose from the digests; apply the **minimal** fix.
2. Run the contract's full gate set (loop-engine's gate), not a filtered subset, because a
   partial run passes on stale artifacts.
3. **Red gate → do not commit, do not push.** Return what's still failing.
4. Green → commit on the PR branch (no new branches), then a **single**
   `git push --force-with-lease`. A stale lease means someone else pushed: **stop and report**.
   Never `--force`, and do not retry, because both overwrite the other person's commits.

**Fix the code, never the evidence**: do not suppress, baseline, or exclude a finding to make
a check green, because a hidden finding is still a defect. This forbids `NOSONAR`-style
pragmas, suppression annotations, rule/exclusion or baseline edits, resolving findings through a
quality-gate API, and deleting or skipping the failing test. A coverage gate wants tests; a
duplication gate wants the duplication refactored. If the only way to pass is to stop the check
from looking, escalate.

## Step 4 — Caps (the anti-thrash rules)

- **4 attempts per check, lifetime.** A 5th is an escalation, not another try.
- **2 revisions per check within one round.** If the first fix doesn't green the gate, revise once;
  then the round ends.
- **4 rounds, then stop and report**, even if the checks are improving, because a check that
  needs a human does not pass with more rounds.

Count attempts **by check name across the whole run**, in commit trailers, because loop-engine
keeps no local state file and a count held in context resets when the loop sleeps. End each fix commit's message with

```
pr-flow-green: attempt <k> <check-name>
```

so `git log --grep='^pr-flow-green:' "origin/$BASE_REF..origin/$HEAD_REF"` reconstructs every
count on wake. No trailer for a check → zero attempts so far.

## Step 5 — Wait for CI, then re-assess

After a push the rollup still shows the old run. Wait with the built-in watcher, because each
manual poll costs a full turn:

```bash
timeout 600 gh pr checks "$N" --repo "$REPO" --watch --interval 30; RC=$?
```

**Branch on `$RC`.** `0` (all passed) and `1` (some check failed) mean CI settled: they are the
input for the next round, not an error. `8` (still pending) and `124` (our `timeout` fired) mean
CI did **not** settle: sleep per loop-engine, because the failure logs do not exist yet. Then
go back to Step 1.

## Step 6 — Report

Terminal or escalated, report **in this session**: the PR number, the head sha, what each round
changed (sha + one line), which checks are green now, and for anything unresolved the check name
plus its specific blocker — the named escalation, not "some checks failed".

Read the head sha again after the last push (`gh pr view "$N" --repo "$REPO" --json headRefOid`),
because the round's first payload is older than the fix commit.

The terminal state comes from GitHub only. A local green gate stops bad pushes, but it does not
prove that CI is green.
