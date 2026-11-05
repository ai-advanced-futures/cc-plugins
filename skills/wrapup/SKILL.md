---
name: wrapup
description: >-
  Use when a session's work has LANDED — merged, or intentionally abandoned — and the workspace
  should be cleaned up: "wrap up this session", "tear down the worktree", "close this out".
  Confirms the work reached the default branch, then deletes the local branch and removes the
  worktree it runs in, then moves this session back to the main checkout (outside a worktree it
  returns to the default branch and pulls). Destructive
  — hard-stops on uncommitted work, unpushed commits, or an in-progress merge/rebase. If the PR is
  still open, drive it to green first with a PR-driving skill (e.g. relay:refining-prs).
allowed-tools: AskUserQuestion(*), Bash(*), Read(*), ExitWorktree(*)
---

# wrapup — tear down a finished work session

Remove this session's workspace: branch gone, worktree gone, the work proven to be on the default
branch first. If a gate in step 2 fails, stop, report what failed, and delete nothing.

**Tear down only the checkout you are running in.** If you are in a worktree, remove that worktree
from inside. Run no command against the main checkout and do not move it to another branch, because
a different session usually owns it and can have its own branch and uncommitted work. Read its path
for the report only.

**Branches are shared.** Every worktree of a repository reads one set of refs. Deleting a branch
here deletes it for every other session too, so step 1 refuses to delete the default branch and
step 4 touches no branch but the one you are on.

This skill does not drive a PR. Step 3 proves that the changes reached the default branch. It does
not prove that a PR was approved or closed. Run this skill once you already know the work has
landed or is intentionally abandoned. To drive a PR to merge-ready first, use a PR-driving skill
such as `relay:refining-prs` (if installed).

## 0. How to run the commands

A worktree-isolated session runs behind a guard that inspects every shell command and refuses
anything it cannot prove stays inside this worktree. So run one git command per call, with no
chain, no `$( )`, no variable, and each path pasted literally, because the guard cannot verify
those forms. Do not use `git -C` or `cd` to reach another checkout, because the guard refuses both.
For the same reason, step 3 calls the script by its absolute path.

A refusal is not a git error, and it is not a reason to stop the skill. It means the command was
written in a form the guard cannot verify. Rewrite it as a single plain command with literal paths
and run it again.

## 1. Identify the workspace

Record all five of these before you touch anything. Step 4 destroys the state some of them read.

- **Branch: `git rev-parse --abbrev-ref HEAD`. Write the name down now.** Step 4 detaches HEAD, and
  after that this command prints `HEAD` and the name is gone.
  - If it already prints `HEAD`, this session is detached. Go to "Detached HEAD" at the end of this
    step. `HEAD` is not a branch name, so do not use it as one.
- **Default branch:** run `git remote set-head origin -a`, then read
  `git symbolic-ref --short refs/remotes/origin/HEAD` (strip the `origin/`). Do the refresh first,
  because `symbolic-ref` is a local read: if the upstream renamed its default branch, it returns the
  old name with exit 0 and no warning, and a plain `git fetch` or `git pull` does not correct it.
  Every later step would then use the wrong branch. If the refresh and the read both fail, use the
  one of `main` or `master` that `git branch -r` shows. Do not assume `main`, because many
  repositories use `master`.
- **Are you in a worktree?** Run this command, which prints two lines:

  ```
  git rev-parse --path-format=absolute --git-dir --git-common-dir
  ```

  The two paths are equal in a main checkout and different in a worktree. Keep
  `--path-format=absolute`: without it, below the repository root git prints the first path
  absolute and the second relative (`../.git`). They then differ as text in a main checkout, and
  the skill would take the worktree path against the shared checkout.
- **Worktree path: `git rev-parse --show-toplevel`.** Use this path in step 4, and not `pwd` or the
  directory you started in. `git worktree remove` accepts only the top level of a worktree and
  fails with "is not a working tree" on a subdirectory. In step 4 that failure comes after the
  branch is already deleted.
- **Main checkout path:** the first `worktree` line of `git worktree list --porcelain`. It is for
  the report and for step 5, where this session moves back there.

Then branch on what you found:

- **The branch IS the default branch.** There is no work branch to delete, and deleting it would
  break every other session in the repository: their `git rebase <default>`, `git log <default>..`,
  and `git diff <default>` all stop working. So:
  - In a worktree: run step 2, skip step 3, and in step 4 path A run only item 1 (classify the
    lock), item 5 (prune) and item 6 (remove the worktree). Skip the detach and the delete,
    because the branch is the default branch.
  - Not in a worktree: there is nothing to tear down. Check that `git status --porcelain` is
    empty first, because a pull onto a dirty tree can fail or conflict. If it is clean, run
    `git pull origin <default-branch>` then `git fetch --prune origin`; if it is dirty, report the
    changes and stop without pulling. Go to step 5 and report `nothing-to-remove`.
- **Detached HEAD** (`git rev-parse --abbrev-ref HEAD` printed `HEAD`). A previous run of this
  skill probably stopped between detaching and removing the worktree, so the branch is already
  gone. Record the sha with `git rev-parse HEAD`. Apply only the first two gates of step 2. The
  third cannot run, because a detached HEAD has no upstream, and that does not mean the work exists
  only locally. Run step 3 with the SHA in place of the branch name; the check accepts one. Show
  the user the verdict and ask once. On a yes, run only item 1 and item 6 of path A.
- **Anything else:** continue to step 2.

## 2. Safety gates

Each gate must pass. When one fails, list what failed and stop.

- **Working tree clean:** `git status --porcelain` is empty. An uncommitted or untracked change
  fails the gate.
- **No operation in progress:** check for `MERGE_HEAD`, `rebase-merge`, `rebase-apply`,
  `CHERRY_PICK_HEAD`, or `REVERT_HEAD` in the worktree's git dir. Read the directory printed by
  `git rev-parse --path-format=absolute --git-dir` in step 1. Inside a worktree `.git` is a file,
  not a directory, so `<worktree>/.git/MERGE_HEAD` finds nothing even during a merge. Any of them
  fails the gate. `git status --porcelain` does not catch this: a conflict resolved in favour of
  HEAD leaves the tree identical to HEAD, so porcelain prints nothing while the merge is still
  open. The removal of the worktree then discards the resolution with no warning and no way back.
- **Nothing unpushed:** run `git rev-parse --abbrev-ref @{u}`.
  - **It succeeds:** `git log @{u}..HEAD --oneline` must be empty. A listed commit fails the gate.
  - **It errors:** the error alone does not say why, and the two causes need opposite answers. Run
    `git config --get branch.<branch>.merge`, with the branch name from step 1.
    - **Empty output:** the branch never had an upstream. The work exists only locally, so the gate
      fails.
    - **It prints a ref:** the branch was pushed, and its remote-tracking ref is gone. A deleted
      remote branch does this, and so does `git fetch --prune` in any worktree, because remote refs
      are shared. The work is not local-only. Record that this gate could not run. Step 3 then
      accepts only exit 0.

When this gate passes normally it proves every commit is on the remote, and that is what makes the
deletions in step 4 safe.

## 3. Confirm the work landed

Run this before you delete or detach anything, every time. Step 4 detaches HEAD on the branch
tip, so `git branch -d` after it always succeeds and proves nothing. This check is the only
evidence the skill has that the work landed.

First refresh the ref you are about to compare against:

```
git fetch origin <default-branch>
```

Nothing earlier in the skill fetched, and a local default branch that has not seen the squash
commit reads as "never merged". If the fetch fails, stop and report the failure, because a check
against a stale ref is not evidence.

Then run the equivalence check. The script lives in this skill, not in the user's repository. Call
it by this absolute path, with no `bash` prefix and no variable:

```
${CLAUDE_SKILL_DIR}/scripts/branch-landed.sh origin/<default-branch> <branch>
```

If the path does not exist, say so and stop: without the script there is no check, and a missing
check is not a pass.

The exit code is the verdict. The text is one evidence line for the report, so do not parse it.
The script compares content and not ancestry, because a squash merge leaves none of the original
commits as an ancestor of the default branch.

- **Exit 0, CONTAINED.** The changes are on the default branch. Go to step 4 with no question. Keep
  the evidence line: it names the squash commit, so the report cites a sha and not only a verdict.
- **Exit 1, NOT-CONTAINED.** No content match. Get evidence and ask, below.
- **Exit 2, INCONCLUSIVE.** A git call failed, or the two histories have no merge base. Treat it as
  exit 1, because no answer is not a negative answer.

If step 2's unpushed gate could not run, exit 1 and exit 2 stop the skill here, and you do not ask.
Without a remote ref, a commit made after the last push exists nowhere else, and the question would
lead the user to delete it.

Two properties of the check go into your report:
- CONTAINED proves the work landed. NOT-CONTAINED does not prove it did not land: the patch identity
  includes the diff context lines, so an edit to the same lines on the default branch before the
  squash, or a conflict resolution during the merge, reads NOT-CONTAINED for a branch that merged.
  That is why exit 1 asks and does not refuse.
- A branch that was squash-merged and then reverted reads CONTAINED. The changes did land, and the
  revert is a later act. Step 2 already proved every commit is on the remote, so nothing is lost.

**On exit 1 or exit 2, gather evidence and ask.** Run `git ls-remote --heads origin <branch>` and
read it in this order:
- **Exit code nonzero** (128 on an unreachable remote, bad auth, wrong remote name): the result is
  inconclusive. Stop and report. An unreachable remote prints nothing on stdout, the same as a
  deleted branch, so "gone" from it would delete unmerged work after a short network failure.
- **Exit 0 with a ref line:** the branch still exists on the remote, so the work possibly did not
  land.
- **Exit 0 with empty output:** the remote branch is gone, which usually means a completed merge
  with auto-delete.

Show the user both results — the equivalence verdict and the remote-branch state — and get explicit
confirmation before you continue to step 4. This is the one place the skill asks.

## 4. Tear down the checkout you are in

Take path A if step 1 found a worktree, path B if it did not. Skip this whole step if step 1
already reported there was nothing to tear down.

### Path A — you are in a worktree: remove it from inside

You can remove the worktree you are in. `git worktree remove` accepts its own path and deletes
the directory, so stay where you are.

Remove the worktree with `git worktree remove`, and not with **ExitWorktree**. ExitWorktree acts
only on a worktree that `EnterWorktree` made in the same session, and it does nothing to any other
worktree, with no warning. Step 5 calls ExitWorktree only to move this session back.

Run these in order. The removal is last because it deletes the directory the shell is in, and each
command after it fails with "Unable to read current working directory".

1. **Classify the lock, before you change anything.** Run `git worktree list --porcelain`. It lists
   all the worktrees in the repository. Find the block whose `worktree` line is the path from
   step 1, and read only the `locked <reason>` line in that block. No such line means no lock. Go
   to item 2.
   - The reason reads `claude session <name> (pid <N> start <date>)` → the harness wrote it for the
     session that works here, and you are the session closing it. Run
     `git worktree unlock <worktree path>` and continue.
   - The reason is any other text → a person locked it on purpose. Stop and report the reason.
   - `locked` lines on other worktrees are for the report only. They do not block
     `git worktree remove <your own path>`, so do not stop for one or unlock one.
   - Do not use `remove -f -f`, because force hides the question of who owns the lock. A single
     `--force` does not override a lock.
2. **Free the branch:** `git checkout --detach`. `git branch -d` refuses while the branch is checked
   out here, and this is the only way to release it from inside. The worktree is about to be
   deleted, so the detached state costs nothing. Skip this item and item 3 if step 1 found you on
   the default branch.
3. **Delete the branch:** `git branch -d <branch>`. Paste the name you wrote down in step 1.
   This succeeds because HEAD is on the branch tip, so it is not evidence that the work merged.
   Step 3 is the evidence. If it refuses, the branch is checked out in ANOTHER worktree: say
   which one and stop, because `-D` will not override that either.
4. **Verify now, while you still have a working directory:** `git branch --list <branch>` must be
   empty. Everything after item 6 is unverifiable, so check here.
5. **Prune the remote-tracking ref:** `git fetch --prune origin`. If it fails, the only cost is a
   stale ref — note it and carry on.
6. **Remove the worktree, last:** `git worktree remove <worktree path>`. Paste the top-level path
   from step 1. Exit 0 is the proof that the directory is gone, because you cannot check after.

**Run no shell command after the remove until step 5 moves this session back.** The working
directory no longer exists. Write the report from what you already recorded.

### Path B — you are not in a worktree

1. `git checkout <default-branch>`.
2. `git branch -d <branch>`. Here a refusal is real, because HEAD is on the default branch. Step 3
   already answered whether the work landed: on exit 0 run `git branch -D <branch>`; on exit 1 or 2
   you already asked the user.
3. `git pull origin <default-branch>`.
4. `git fetch --prune origin` to remove the stale remote-tracking ref. Keep it a separate command,
   because `git pull --prune origin <default-branch>` does not prune the deleted branch: a refspec
   on the command line limits the prune to refs that match it.

If the branch is already gone when you get to it, that is a success.

## 5. Verify and close

Say which path you took: **`self-removal`** (path A), **`return-to-default`** (path B), or
**`nothing-to-remove`** (the step-1 early exit).

Confirm with this evidence:
- Path A: `git branch --list <branch>` was empty at item 4, and `git worktree remove` exited 0.
  If step 1 found you on the default branch, say `self-removal, no branch deleted` and drop the
  branch evidence line — keeping that branch was the correct outcome.
- Path B: `git branch --list <branch>` is empty, `git worktree list` no longer shows the path,
  `git rev-parse --abbrev-ref HEAD` is the default branch, and `git status` reports up to date.

**If a check fails, the teardown is not complete.** Say what is left (a branch, a worktree that is
not removed, a checkout on the wrong branch). Do not tell the user that the session is safe to
close, because a worktree that no one tracks is the failure this skill prevents. Stop there and let
the user decide.

Distinguish which half failed. The branch delete and the worktree removal are irreversible; the
checkout and pull in path B are not. On path A, if the branch is gone but the removal failed, say
so: the worktree is still on disk with a detached HEAD, the commits survive on the remote, and only
the removal needs finishing. Say that re-running this skill will report a detached HEAD and pick up
from there.

Report a one-line summary and the landed-ness evidence line from step 3. State plainly that the
main checkout was not touched.

On path A, this session's folder no longer exists, because you just deleted it. Without help, Claude
Code moves the shell to the home folder, not to the repository. So do these steps now, in order,
with the main checkout path from step 1:

1. Call `ExitWorktree({action: "keep"})`. The worktree is already gone, so "keep" deletes nothing.
   It moves this session back to the folder it started in.
2. Run `pwd`. It must print the main checkout path.
3. If ExitWorktree said no worktree session is active, or `pwd` prints another folder, this session
   started inside the worktree and cannot return to the main checkout. Tell the user to close
   this session and start a new one in the main checkout:
   $ cd <main checkout path> && claude

Use ExitWorktree to move, and not `cd`, because the shell guard of a worktree session resets a
`cd` to the main checkout after the command.

Then tell the user the work is closed. If this session is a background job that is no longer
needed, tell the user to stop it with `claude stop <id>`, because a session cannot stop itself.
