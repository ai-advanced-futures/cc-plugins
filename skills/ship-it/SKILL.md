---
name: ship-it
description: >-
  Use when the user wants a change on the default branch now: "ship it", "get this to main",
  "commit, PR and merge this", "/ship-it". Moves the change into a worktree if it is not in one,
  commits it, pushes it, opens a pull request, waits for the checks, squash merges (with --admin
  when the plain merge is refused), runs the wrapup skill, and pulls the latest default branch.
argument-hint: "[commit message or PR title]"
allowed-tools: AskUserQuestion(*), Bash(*), Read(*), Skill(*), EnterWorktree(*), ExitWorktree(*)
---

# ship-it: get one change onto the default branch

Take the current change from the working tree to a squash merge on the default branch. Then
clean up the workspace and bring the main checkout up to date. Each step has a gate. When a gate
fails, stop at that step and report what failed, because a later step can merge or delete work
that the failed step did not save.

The user approved the merge and the `--admin` flag when they started this skill. Ask no question
about them again.

## 0. How to run the commands

In a worktree session, a guard reads each shell command. It refuses a command that it cannot
prove stays inside the worktree. So run one git command per call, with no `&&` chain, no `$( )`,
no shell variable, and each path written literally. A refusal is not a git error. Write the
command again as one plain command, and continue.

The `CLAUDE.md` files of the repository can set a commit format, a branch name format, a version
bump, or a check to run before a commit. Obey them in each step.

## 1. Get the change into a worktree

Record these values first:

- Branch: `git rev-parse --abbrev-ref HEAD`.
- Default branch: run `git remote set-head origin -a`, then
  `git symbolic-ref --short refs/remotes/origin/HEAD`, and remove the `origin/` prefix.
- In a worktree or not: `git rev-parse --path-format=absolute --git-dir --git-common-dir`. The two
  lines are different in a worktree and equal in the main checkout.
- The change: `git status --porcelain` and `git log --oneline origin/<default>..HEAD`.

If the status and the log are both empty, there is no change to ship. Stop and say so.

Then take the first case that matches:

- **In a worktree, on a branch that is not the default branch.** Go to step 2.
- **In a worktree, on the default branch.** Run `git switch -c <new-branch>`. The new branch takes
  the uncommitted change and the local commits with it. Go to step 2.
- **In the main checkout, on the default branch.** Carry the change into a new worktree:
  1. If `git log origin/<default>..HEAD` shows commits, stop and tell the user. A local commit on
     the default branch does not move with the steps below, and to move it changes the main
     checkout.
  2. `git stash push -u -m ship-it-<short-slug>`. Each worktree shares one stash list, so use a
     tag that no other session uses.
  3. `git stash list --format='%H %gs'`. Record the SHA on the line with your tag.
  4. Call `EnterWorktree` with a name made from the change, for example `fix-login-timeout`.
  5. In the worktree: `git stash apply <sha>`. If it shows a conflict, stop. Tell the user that
     the change is safe in the stash entry with that SHA.
  6. `git stash list --format='%gd %gs'`. Find the line with your tag again, because its
     `stash@{n}` number can change. Then run `git stash drop stash@{n}` for that line.
  7. `git status --porcelain` must show the change. Go to step 2.
- **In the main checkout, on another branch.** Stop and ask the user what to do. That branch can
  belong to work that is not part of this change.

If the repository sets a branch name format, run `git branch -m <name>` before the first push.

## 2. Commit

1. Read `git diff`. If a changed file looks like it belongs to other work, ask the user before
   you add it.
2. Do the checks that `CLAUDE.md` requires before a commit. If a check fails, stop and report it.
3. Add the files by name. Do not use `git add -A`, because it can add a secret or a build file.
4. Commit. If the user gave an argument, use it as the subject.
5. `git status --porcelain` must be empty.

## 3. Push

`git push -u origin HEAD`. If the push is refused because the remote branch moved, stop and
report it. Do not force-push, because that can delete commits that someone else pushed.

## 4. Open the pull request

1. `gh pr view --json number,url,state`. If a pull request is already open for this branch, use
   it.
2. If not: `gh pr create --base <default> --title "<title>" --body "<body>"`. Write the title in
   the commit message format of the repository, because the squash commit takes it. Write in the
   body what changed, why, and how you checked it.

## 5. Wait for the checks, then squash merge

1. `gh pr checks <number> --watch --fail-fast`. If a check fails, stop and report the check name
   and its URL. The `--admin` flag skips the branch rules, but it does not make a failed check
   correct. If the command says that no checks are reported, continue.
2. `gh pr view <number> --json mergeable,mergeStateStatus`. If `mergeable` is `CONFLICTING`, stop.
   Tell the user to run `/rebase` and then this skill again.
3. Merge:

   ```
   gh pr merge <number> --squash --subject "<title>" --body "<body>"
   ```

   Give the subject and the body yourself. If you give no subject, GitHub makes one that can break
   the commit format of the repository. Do not add `--delete-branch`, because from a worktree it
   tries to check out the default branch, and that branch is already checked out in the main
   checkout.
4. If the merge is refused because of a review rule or a branch rule, run the same command again
   with `--admin` added. If it is refused for a different reason, stop and report it.
5. `gh pr view <number> --json state,mergeCommit` must show `MERGED`. Record the merge commit SHA.
6. `git push origin --delete <branch>`. If the remote branch is already gone, that is a success.

## 6. Wrap up

Run the `wrapup` skill with the Skill tool. It proves that the work is on the default branch,
deletes the local branch, removes the worktree, and moves the session back to the main checkout.
If wrapup stops on a gate, stop here and give its report.

## 7. Pull the latest default branch

Do this step in the main checkout, after wrapup moves the session there.

1. If wrapup took the `return-to-default` path, it already pulled. Go to step 8.
2. `git rev-parse --abbrev-ref HEAD`. If it is not the default branch, do not pull, because the
   main checkout is on another branch for other work. Tell the user, and go to step 8.
3. `git pull --ff-only origin <default>`. If it fails, report the error and let the user decide.
4. `git log -1 --oneline` must show the squash commit from step 5.

## 8. Report

Give one short block:

- The PR number and URL, and the merge commit SHA.
- If the merge used `--admin`, and why.
- The wrapup path, and that the worktree and the branch are gone.
- The commit that the main checkout is on now, or the reason it was not pulled.
