# Syncing a PR branch with its base

Shared by `getting-prs-green` and `getting-prs-merged`. Needs `$N`, `$REPO`, `$HEAD_REF`, and
`$BASE_REF` from [github-access.md](github-access.md).

## Contents
- Which path to take
- Behind and clean → update-branch
- Conflicted → temp-worktree rebase
- After the sync lands

## Which path to take

| PR state | Path |
|---|---|
| `mergeStateStatus == BEHIND`, no conflict | `gh pr update-branch` |
| `mergeable == CONFLICTING` / `mergeStateStatus == DIRTY` | temp-worktree rebase |

**Take `update-branch` for a merely-behind branch, and rebase for conflicts only.** Both paths
give CI the same head+base merge tree, but the rebase needs a force-push, and under *Dismiss stale
pull request approvals* a force-push dismisses the approvals `getting-prs-approved` got.

## Behind and clean

```bash
gh pr update-branch "$N" --repo "$REPO"
```

Squash-merge collapses the resulting merge commit, so merge-vs-rebase is immaterial to final
history.

## Conflicted → temp-worktree rebase

```bash
WT="${CLAUDE_JOB_DIR:-/tmp}/tmp/pr-merge-rebase-$N"
git fetch origin
git worktree add "$WT" "$HEAD_REF"
cd "$WT"
git rebase "origin/$BASE_REF"
```

- **Trivial/mechanical conflict** — lockfiles, generated files, import ordering, non-overlapping
  hunks → resolve, `git rebase --continue`, run the contract's full gate, then
  `git push --force-with-lease`.
- **Semantic conflict** — real logic overlap → `git rebase --abort`, escalate.
- **Gate red after a resolution** → do not push; abort, escalate.
- Unsure whether a conflict is mechanical? Treat it as semantic. A wrong autonomous resolution is
  worse than a stop.

**Destroy the worktree on every path, including both escalations.** This is the step that leaks,
because the shell is still inside `$WT` when you stop:

```bash
cd - && git worktree remove --force "$WT"
```

Push with `--force-with-lease` always, not bare `--force`, because bare `--force` overwrites
commits that someone else pushed. A stale lease means someone else pushed: stop and report.

## After the sync lands

- **Re-sync the local checkout.** Both paths leave the working tree stale — `update-branch` is
  server-side, and the rebase happens in a worktree that then gets destroyed. Committing on a
  stale checkout either trips the stale-lease rule (blaming a third party for our own sync) or
  force-pushes the sync away:
  ```bash
  git fetch origin "$HEAD_REF" && git reset --hard "origin/$HEAD_REF"
  ```
- **Re-assess before acting.** A base sync re-triggers CI, so any failing-check list you were
  holding is now stale. Re-read the PR state and work from the new list.
