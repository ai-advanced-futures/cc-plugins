---
name: reviewing-prs
description: Reviews the current branch's PR diff against this repo's own code-review contract — its bar for what counts as a finding, deterministic-gate exclusions, repo invariants, and a registry of lens skills — then emits a local advisory report, optionally posting it to the PR (--comment) or approving the PR when every approve condition holds, such as no must-fix finding and a goal verdict of achieved or partially achieved (--approve). Every run always includes two built-in lenses — Claude Code's /code-review skill on the PR diff, and the plugin's code-review:reviewing-goal-achievement lens. With no contract, it asks whether to run /code-review:setup first or to review with the two built-in lenses only. Use when asked to review a PR or the current branch, run the code-review review, or post or approve a review on a PR. Repo-agnostic, reading the contract written by /code-review:setup. Reviews the diff only, never the checks or the merge state. Advisory only, never blocking.
argument-hint: "[--pr <number>] [--comment | --approve]"
allowed-tools:
  - Bash(git diff:*)
  - Bash(git merge-base:*)
  - Bash(git log:*)
  - Bash(git rev-parse:*)
  - Bash(git symbolic-ref:*)
  - Bash(git status:*)
  - Bash(git ls-files:*)
  - Bash(git show:*)
  - Bash(git hash-object:*)
  - Bash(gh auth status:*)
  - Bash(gh pr view:*)
  - Bash(gh pr comment:*)
  - Bash(gh pr review:*)
  - Bash(gh repo view:*)
  - Bash(gh api user:*)
  - Bash(gh api graphql:*)
  - Bash(gh api repos/*/issues/*/comments:*)
  - Bash(gh api repos/*/pulls/*/reviews:*)
  - Bash(grep:*)
  - Bash(jq:*)
  - Bash(cat:*)
  - Bash(test:*)
  - Bash(mktemp:*)
  - Read
  - Glob
  - AskUserQuestion
  - Workflow
  - Skill
---

# reviewing-prs

Check a PR's changes for bugs with Claude Code's `/code-review` skill, and against **this repo's
own review contract**: the concerns, invariants, and lenses that `/code-review` cannot know
about. This review is advisory. Report real concerns, and do not block a merge, because branch
protection owns the merge gate. Even `--approve` only adds an approval.

**Review the changes, and only the changes.** The diff is the whole subject. Do not report, in
the session or on the PR, that a check failed, that CI is red, that the branch is behind its
base, that it needs a rebase, or that it has a conflict, because `getting-prs-green` and
`getting-prs-merged` own all of that. An author who reads it here reads the rest of the review
with less attention. `--approve` means "this diff passed the review", not "this PR is mergeable".

Hardcode nothing repo-specific and no fixed lens list. Everything you enforce comes from the
contract that `/code-review:setup` generated for this repo. The two built-in lenses (Step 3) are the
only fixed lenses, and neither one is repo-specific.

**References.** Read a file when its step says to:
- [references/posting.md](references/posting.md): Step 7, when a posting flag was passed.
- [../../references/github-access.md](../../references/github-access.md): the shared `gh`/MCP probe.

## Step 0 — Parse arguments

Local and read-only by default. Two flags opt into writing, a third names the target. Parse them
out of the invocation text first, binding `--pr`'s value to `$PR`.

| Flag | Effect |
|------|--------|
| *(none)* | Step 6 report in-session. **No GitHub writes.** The default. |
| `--comment` | Also post the report to the PR as a comment. Uncommitted changes to tracked files disable the post (posting.md *Preconditions*). |
| `--approve` | Post **and** approve when every approve condition in posting.md holds. Otherwise it degrades to a comment, or to no post when a posting precondition fails. This is the scheduled loop's *Approve-when-clean* posture for one PR. Implies `--comment`. |
| `--pr <number>` | Names which PR the posting flags target, when the branch doesn't resolve to one — e.g. a loop reviewing someone else's PR from a temp worktree. Writes nothing on its own, and does **not** fetch that PR: the diff still comes from the working tree, so its head must already be checked out. Step 7 verifies that. |

- `--comment --approve` together is the normal scheduled call. Treat the pair as `--approve`.
- With a posting flag, read [references/posting.md](references/posting.md) now, and run its
  *Preconditions* and *Dedupe* before Step 1. A dedupe hit then stops the run before the
  contract read, the diff, and the lens fan-out, which are the cost of this skill.
- Stop early only on a dedupe hit or on the Step 1 choice to set up code-review first. A failed
  precondition disables posting only: the review still runs, and the report still ships with its
  `**Posted:** not posted — …` line.
- Echo the parsed flags in the report header, so the reader knows what the run was allowed to do.

## Step 1 — Read the contract

Read `.claude/code-review/contract.md`. If it does not exist but `.claude/pr-flow/contract.md` exists,
read that older path instead, and use it as the contract for this whole run. Say once, under the
report, that `/code-review:setup` moves it to `.claude/code-review/contract.md`. Keep that line off
the PR, because it is about the repo setup and not about the diff.

If neither file exists, say this first:

> No code-review contract found at `.claude/code-review/contract.md`. Run `/code-review:setup` to
> generate this repo's review contract and lens skills.

Then ask the user with `AskUserQuestion`. Give these two options, in this order:

1. **Review with the built-in lenses now** — run `/code-review` and the goal lens on this diff, in
   no-contract mode. This is the recommended option.
2. **Set up code-review first** — invoke the `code-review:bootstrapping` skill (the skill that
   the `/code-review:setup` command runs) and stop this review. Tell the user to run the review again after setup writes the contract.

Go straight to no-contract mode without the question when no person can answer it:

- The invocation passes `--pr` together with a posting flag. That is the scheduled loop's call
  shape (`scheduling-pr-reviews`). A person who types that shape also gets no question. To get
  the question, run without `--pr` from the PR's branch.
- The `AskUserQuestion` tool is not available, or it returns no answer (a headless `-p` run).

**No-contract mode.** Do these steps instead of the rest of Step 1:

- Run Step 2 (obtain the diff) as normal.
- Read `REVIEW.md` as the **REVIEW.md** subsection at the end of Step 1 states.
- Treat the missing contract as an empty registry (Step 3).
- Emit the Step 6 report.
- Apply the four-part must-fix test from Step 5 and the Voice rule from Step 6. This mode has no
  Bar, no gate list, and no invariant list.
- The coverage receipt reads `triaged 0 registry rows → selected 0`, plus the two built-in lens
  rows. The dedupe marker's `lenses` count (posting.md) is `0`.
- Write `no-contract mode` on the report's `**Mode:**` line, so that no reader takes the report
  as a full review.
- `--approve` degrades to a comment in this mode, because no contract set the bar. posting.md
  owns the receipt wording for that case.

With a contract present, hold all four sections for the whole session:

1. **The Bar** — a finding must be *real* (concretely true in this diff, with evidence) **and**
   *impactful if left unattended*. Report or drop, silently. Each reported finding is then
   **must-fix**, **should-fix**, or **note** by the Bar's four-part must-fix test; that label
   decides approval only.
2. **Deterministic gates** — the repo's own lint/typecheck/CI/secret-scan commands. Drop what a
   listed gate already owns, because the gate reports it already.
3. **Repo invariants** — the repo-specific rules the lenses defend.
4. **Lens registry** — the active lenses (Step 3).

An older contract can say "no severity ladder", and its section 3 invariants can carry no
`[blocking]` or `[advisory]` marker. Apply the Step 5 four-part test to it anyway; "no severity
ladder" does not mean that every finding withholds approval. Treat an unmarked invariant as
`[advisory]`: a broken invariant alone is then should-fix or note, unless it also hits one of the
other five damage classes. Say once, under the report, that `/code-review:setup` refreshes the
Bar. Keep that line off the PR, because it is about the repo setup and not about the diff.

### REVIEW.md — the code owners' rules

Read `REVIEW.md` at the repository root at HEAD, if it exists. After Step 2, also read each
`REVIEW.md` in a parent directory of a changed file; its rules apply only to changes under its
directory. Anthropic's Code Review service on GitHub reads these files, and the code owners write
them to say what matters in their part of the code.

- **Skip the generated block.** Ignore the text between `<!-- code-review:router start -->` and
  `<!-- code-review:router end -->`. `/code-review:setup` built it from the contract you already
  hold. In no-contract mode, read the whole file, because that block is then the only bar the repo
  has.
- **A "do not report" rule drops findings.** When a line tells the reviewer not to report a path
  or a class of issue, drop each finding it covers, the same way a deterministic gate does.
- **Any other rule is advisory.** A finding that breaks a REVIEW.md rule is should-fix or note.
  It reaches must-fix only through the four-part test in Step 5, which has a fixed list of six
  damage classes.
- **Evidence and summary rules.** When REVIEW.md asks for a `file:line` for each finding or for a
  count at the start of the summary, the Step 6 report already gives both. Write one summary only.
- **The contract wins.** When a REVIEW.md rule disagrees with the contract, apply the contract
  and say once, under the report, which REVIEW.md line disagrees.

Pass the rules you kept to every lens dispatch (Step 4). Write `REVIEW.md: <n> rules` in the
coverage receipt, or `REVIEW.md: none` when no file exists.

## Step 2 — Obtain the diff

```bash
BASE=""
for c in refs/remotes/origin/HEAD refs/remotes/origin/main refs/remotes/origin/master \
         refs/heads/main refs/heads/master; do
  git rev-parse --verify --quiet "$c" >/dev/null 2>&1 && { BASE="$c"; break; }
done
[ -z "$BASE" ] && { echo "code-review: cannot resolve a base branch — aborting review"; exit 1; }
MB="$(git merge-base HEAD "$BASE")" || { echo "code-review: no merge-base with $BASE — aborting"; exit 1; }
DISP="${BASE#refs/*/}"          # refs/remotes/origin/main -> origin/main
WARN=""
case "$BASE" in refs/remotes/*) ;; *) WARN=" (WARNING: local branch, not remote-tracking — may be stale)" ;; esac
echo "code-review: base=$DISP merge-base=$MB$WARN"
git --no-pager diff --no-ext-diff "$MB"..HEAD || { echo "code-review: git diff failed — aborting"; exit 1; }
```

Keep three details of this block. Each one, if changed, gives an **empty diff that looks like a
clean PR**:

- **Fully-qualified refs.** A bare `main` can resolve a *tag* named main, and a bare `origin/main`
  can resolve a local branch named `origin/main`.
- **No `sed` pipeline** from `git symbolic-ref`. `sed` exits 0 on empty input, so a `|| fallback`
  never fires and the command becomes `git diff ..HEAD`, which gives an empty diff.
- **`--no-ext-diff`.** Without it, a configured `diff.external` (difftastic, delta) makes
  `git diff` fail with "external diff died".

If the block aborts, stop the whole review and report the abort, because Step 3 needs a diff. If
the diff is empty, report "no changes against `<base>`" and stop. An empty diff never gives
"PR looks ok", because an empty diff can come from a failed command.

Carry the printed `base=… merge-base=…` values into the report's **Base** line. Also read the
branch name, `git log --oneline "$MB"..HEAD`, and the changed-file list.

**Then check for uncommitted changes to tracked files.** Every lens can open working-tree files,
and none of those changes is in the PR head:

```bash
DIRTY="$(git status --porcelain --untracked-files=no)" || DIRTY="git status failed"
echo "code-review: dirty=${DIRTY:+yes}"
```

A failed `git status` counts as dirty, so the check cannot pass on an empty value. Untracked files
are not counted here, because `git stash` does not remove them; Step 5 drops a finding only when
git confirms its file is untracked. When Step 2 printed `dirty=yes`, add this text to the
**Run caveat** line: `uncommitted changes to tracked files — findings on those lines dropped`. With a dirty tree,
posting.md *Preconditions* disables the post, so this text appears only in a local report.

If Step 2 printed the warning, put it on its own **Run caveat** line in the report, verbatim, and
nowhere else. A stale base gives a wrong diff that is not empty, so the local reader must see the
warning. Step 7 removes the line before posting; posting.md holds that rule and its reason.

`**Run caveat:**` is the exact label that posting.md's *Post* section removes with `grep -v`. It
is the one local-only line inside the report fence. Put every other local-only line under the
report, outside the fence. If you rename the label, rename it in posting.md too, or the caveat
goes to the PR.

**A Run caveat also withholds approval**, because a stale base can give a diff that is not the
PR's changes. posting.md degrades the run to a comment.

Three report lines change what Step 7 does, and none of them is a finding: the Run caveat, the
Goal check line, and a `no result` code-review row. Step 5 drops none of them.

## Step 3 — Triage from the lens registry

The registry is a Markdown table, one row per lens (canonical grammar in
`${CLAUDE_PLUGIN_ROOT}/templates/the-bar.md` §4):

```
| name | when | skill path |
|------|------|------------|
| reviewing-<concern> | `<glob>`, `<change-type>` | `.claude/skills/reviewing-<concern>` |
```

Decide per row whether it applies to **this** diff by its `when` clause, which has two forms and
may mix them:

- **File globs** (`**/*.ts`, `auth/**`) — applies if any changed file matches.
- **Change-type keywords** (`touches-data-model`, `adds-migration`) — not path matches. Select
  the lens when the diff touches at least one file that is not purely generated or mechanical
  (lock files, vendored dirs, generated clients, pure formatting). The lens returns clean if its
  change type is absent. A clean lens costs little, and a dropped concern that no path pattern
  can express (a naming convention, a compliance rule) is a missed finding.

With an empty registry, select the two built-in lenses only, say so in the receipt, and continue.

Invoke each lens by the **bare basename of its registry skill path** (`reviewing-<concern>`).
Generated lenses are native repo skills, so they are **not** `code-review:`-namespaced: registry path
`.claude/skills/reviewing-naming` → invoke `reviewing-naming`.

### The built-in lenses (always selected)

Two lenses run on every review: the **code-review lens** and the **goal lens**. Select both when
the registry lists them, when the registry does not list them, and when the registry is empty.
Each one has its own receipt row, marked `built-in`.

#### The code-review lens

This lens runs Claude Code's built-in `/code-review` skill on the Step 2 diff. `/code-review`
finds correctness bugs, and at some effort levels it also finds reuse, simplification, and
efficiency cleanups. Step 4 states how to start it.

`/code-review` is a Claude Code skill, not a plugin skill and not a repo skill. Invoke it as
`code-review`, with no namespace.

An older contract can carry a registry row for a repo lens that also hunts generic bugs:
`reviewing-bugs`, `reviewing-correctness`, or a similar name. Keep that row when its `flag:` list
names a repo-specific rule. Drop it when it only repeats generic bug hunting. Count a dropped row
as triaged, and write `not selected (the code-review lens owns this concern)` on its receipt row.

#### The goal lens

Add `code-review:reviewing-goal-achievement` to the selected set on every review.

This lens is a plugin skill, so invoke it as `code-review:reviewing-goal-achievement`. The bare
name `reviewing-goal-achievement` does not resolve, because the bare-basename rule above covers
generated repo lenses only.

An older contract can carry a registry row for a repo lens that also compares the PR body with
the diff: `reviewing-goal-achievement`, `reviewing-pr-intent`, or a similar name. Drop that row
and run the goal lens alone, because the report holds one `**Goal check:**` line. Count the
dropped row as triaged, and write `not selected (the goal lens owns this concern)` on its receipt
row.

## Step 4 — Fan the lenses out

Author a Workflow in-context (not written to disk, because this review is read-only) that gives each selected lens its own
subagent, invoked by the Skill tool, run in parallel. Skills use no nesting level, so the fan-out
is flat.

**The code-review lens is not in `SELECTED`, and it gets no `agent()` call.** `/code-review` runs
as a forked skill, and that fork is not tested inside a Workflow `agent()`. Start it from this
session, in the same turn as the Workflow, as *Start the code-review lens* below states.

**Run every lens subagent on Sonnet.** Set `model: 'sonnet'` on each lens `agent()` call, whatever
model this session runs. A lens reads one diff against one written rule, and the fan-out is the
main cost of this skill. The pin covers the Step 4 fan-out and the Step 5 single-lens re-dispatch
only. Step 5's filter pass and Step 6's report stay inline, on this session's model.

```js
await parallel(SELECTED.map(lens => () =>
  agent(lensPrompt(lens), {
    label: lens.name,
    model: 'sonnet',
    schema: lens.goal ? GOAL_SCHEMA : FINDINGS_SCHEMA,
  })))
```

`GOAL_SCHEMA` carries the verdict word, the one-sentence rationale, **and** a `findings` array in
the same shape `FINDINGS_SCHEMA` uses — label, file, text. `FINDINGS_SCHEMA` carries only the
finding list. Give the goal lens `GOAL_SCHEMA`, because `FINDINGS_SCHEMA` has no field for the
verdict, and a schema with no `findings` field drops the goal lens's should-fix and note entries.
Give every other lens `FINDINGS_SCHEMA`. Step 5 and Step 6 treat the goal lens's `findings` like
the findings of any other lens.

**Hand the goal lens the Step 2 diff, the PR title, body, commits, and closed issues.** Its
dispatch prompt carries the same diff text every other lens gets. The goal lens must not compute
its own diff, because the Step 2 diff has the merge-base and stale-ref guards. With a posting
flag, posting.md already fetched the other four values before Step 1: pass `$TITLE`, `$BODY`,
`$COMMITS`, and `$ISSUES` from it, and fetch nothing again.

Fetch the four values yourself when no posting flag was passed, **and** when a posting flag was
passed but posting.md's fetch returned an empty `$PR_JSON`. Run these calls only when `gh` is
authenticated and the branch resolves to an open PR. One call gets the first three:
`gh pr view "${PR:-$(git rev-parse --abbrev-ref HEAD)}" --json title,body,commits`. It reads the
`--pr` target when one was passed, and the current branch otherwise.

**The closed issues need a second call, and it is not optional.** A PR body that only says
`Fixes #7` states no goal by itself; issue 7 holds the goal. `gh pr view --json` has no field for
these issues, so run the `gh api graphql` query in posting.md *Preconditions* and pass its output
as `$ISSUES`. Keep its two failure answers apart: `[]` means the PR closes no issue, and an empty
string means the call failed.

**Bind `$REPO` and `$N` before you run that query.** posting.md binds them in its own
*Preconditions* block, which does not run on this path:

```bash
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
N="$(gh pr view "${PR:-$(git rev-parse --abbrev-ref HEAD)}" --repo "$REPO" --json number -q .number)"
```

An unbound `$REPO` or `$N` makes the query fail. The lens then reads the empty `$ISSUES` as a
failed call, and a PR whose body says only `Fixes #7` gets `undetermined`.

The lens never calls `gh` itself, because this step passes it every value. When neither path yields a title and a body, tell the lens
which path failed: an absent PR, or a `gh` call that failed. The lens then uses the other
sources, and it may return `undetermined` — and its one sentence then names that failure, so the
reader does not read a `gh` error as an empty PR body.

Frame every subagent **adversarially — refutation, not "read it and find issues."** Each gets one
lens and is told to attack: break the invariant that lens defends, disprove a claim, construct a
concrete failing case. A "clean" verdict with no shown break-attempt is itself a failure, so
require an `ATTEMPTED-BUT-HELD` list where **each entry names the exact target attacked**
(function, route, schema, symbol) **and the input that should have broken it**. If the concern is
absent, the lens says so (`concern not present: no <X> in this diff`) instead of listing attacks.
"Looked for issues, found none" is a failed dispatch, not a clean verdict.

**The goal lens is the one exception to this paragraph.** `code-review:reviewing-goal-achievement`
compares a stated goal with a diff; it does not attack an invariant, and it carries no
`ATTEMPTED-BUT-HELD` list. Its evidence is the verdict word and the one-sentence rationale that
Step 6 already requires from it. It still gets the Step 2 diff.

**Give the reviewer no summary.** Hand over the diff and let it read. Leave out a summary of the
change, prior "approved" verdicts, and gate results, because a primed reviewer agrees. Scope it
to the *whole* PR, not the slice just written, and require a failure scenario per finding.

**Put these rules in the dispatch prompt itself.** A lens file is a `flag:` / `do not flag:`
list with no policy text, so the dispatch prompt is the only place a lens subagent reads them:

- **Read the Bar first.** Read section 1 of the contract file that Step 1 read and drop any finding
  that does not clear both of its tests. Apply its note cap to every should-fix and note finding.
- **Apply the REVIEW.md rules.** Put the rules that Step 1 kept from `REVIEW.md` here, unchanged.
  Drop a finding that a "do not report" rule covers. Give a `file:line` for each finding, and read
  the code, because a name does not prove what code does.
- **Report the diff only.** Say nothing about a failed check, the CI result, the merge state, or
  the age of the branch. A CI or workflow file the diff changes is part of the diff.
- **Judge tracked content at HEAD only.** Judge a path only when `git show HEAD:<path>` reads it
  or it is in `git diff --name-only <MB>..HEAD`; put the Step 2 merge-base SHA in place of `<MB>`.
  Ignore untracked files. Do not read a path the PR deletes. Ignore uncommitted
  edits: read a file at HEAD with `git show HEAD:<path>` when it may differ. Give every file
  path from the repository root, never as an absolute path.

- **Report only what breaks the rule.** Silence is the correct answer for most diffs.
- **Propose one of three labels: `MUST-FIX`, `SHOULD-FIX`, or `NOTE`.** For a `MUST-FIX`, write
  part 1 of the Bar's must-fix test in full: "After this merge, <who or what> gets <the wrong
  result> at <file>:<symbol>." Step 5 re-runs the full must-fix test on every proposal, so an
  over-strict proposal gains the lens nothing.
- **Write every finding in ASD-STE100**, per the Bar's Voice rule (Step 6 restates it).
- **The `ATTEMPTED-BUT-HELD` list is the proof of work, not a quota.** A lens that reports
  nothing and names what it attacked did its job.

### Start the code-review lens

In the same turn that starts the Workflow, call the Skill tool from this session:

```
Skill(skill: "code-review", args: "medium --max-findings default <MB>...HEAD")
```

Put the full `$MB` value from Step 2 in place of `<MB>`. Pass every part of `args`, each for its
reason:

- **`medium`** — the effort level. With no level, `/code-review` uses the level that the user
  typed last, so two runs on one diff can differ. At `medium` it reports only the findings it is
  most sure about.
- **`--max-findings default`** — the finding cap. A cap that the user set earlier stays until
  someone passes `default`.
- **`<MB>...HEAD`** — the target, a ref range that the Claude Code docs
  (<https://code.claude.com/docs/en/code-review>) list as valid. With no target, `/code-review`
  reviews the commits ahead of the upstream plus the uncommitted changes. That is not the Step 2
  diff, and the scheduled loop's temporary worktree has no upstream.
- **No other flag.** Do not pass `--comment`, because it posts inline comments that go around
  posting.md's dedupe marker and approve gate. Do not pass `--fix`, because it changes the working
  tree and this review is read-only. Do not pass `ultra`, because it is a billed cloud review.

In an interactive session, the level and the cap passed here can become the user's saved values
for later manual `/code-review` runs. Accept this, because the review needs fixed values. The user
changes them back by typing a level, or `--max-findings <n>`.

**Wait for the result before Step 5.** When the Skill call returns the findings, use them. When it
says the review runs in the background, wait for its result notification in the same turn. The
findings come as a JSON list with `file`, `line`, `summary`, and `failure_scenario`. Start Step 5
when the result arrives or the review fails.

Send `/code-review` only the call above: no adversarial framing, no Step 4 dispatch rules, and no
`ATTEMPTED-BUT-HELD` list, because it has its own review method. Its evidence is its finding
list, or its statement that it found nothing.

## Step 5 — Filter and verify

One inline pass over everything the subagents and the code-review lens returned:

- **Clears the Bar?** Real — concretely present in this diff, with evidence — **and** impactful.
  Drop what fails either test.
- **Gate-owned?** Drop anything a listed deterministic gate already covers.
- **In the diff?** Drop anything about the *run*: a check that failed, a red CI result, the merge
  state, the base being behind, a conflict. A lens that returns one of those returned an
  out-of-scope finding, not a finding.
  A CI file that the diff edits is in scope, because the subject is the change. A diff that
  deletes a test step, weakens a gate, or drops a required job gets the same four-part must-fix
  test as any other change. Damage class 5 usually carries it, but run the test. Do not report
  the *state* of a run you did not read.
  The goal verdict is not a finding, so this bullet does not drop it. The goal lens reads the PR
  title and body for the verdict only, and it reports no opinion about them.
- **Tracked content at HEAD?** This bullet covers every lens, the built-in lenses too. Drop a
  finding only when git confirms that its file is untracked.

  First make the path relative to the repository root. `/code-review` does not get the Step 4
  dispatch rules, so it can give an absolute path. When the path starts with the output of
  `git rev-parse --show-toplevel` and a `/`, remove that part. Use the result as `<file>` in this
  bullet and in the report entry.

  Then keep the finding when the file is an exact line match in
  `git diff --no-relative --name-only <MB>..HEAD | grep -Fx -- "<file>"` (a file the PR changes or
  deletes). Otherwise run:

  ```bash
  git ls-files -z --others --exclude-standard --full-name -- ":(top,literal)<file>"
  ```

  Drop the finding only when the output is exactly `<file>` (git ends it with a NUL byte, which
  does not show). `-z` stops git from quoting a name with a non-ASCII byte, a `"`, or a `\`, which
  would stop the match. `literal` stops git from reading `[`, `*`, or `?` in the name as a
  pattern, and `top` reads the path from the repository root.
  Keep every other finding: a tracked file, a path that the command cannot read (an error, no
  output, or other output), and a gitignored file (`--exclude-standard` does not list it). This
  test fails toward withholding approval. Every command here starts with a granted prefix
  (`git diff`, `git ls-files`, `git rev-parse`, `grep`), so an unattended run can call them. A file
  removed with `git rm --cached` is dropped here; that is a dirty tree, so it affects a local
  report only.

  When Step 2 printed `dirty=yes`, also drop a finding whose line falls inside a hunk of
  `git diff --no-ext-diff HEAD`: the uncommitted changes replace that line. A lens subagent reads
  files at HEAD, so compare its line with the HEAD side (`-a,b`) of a hunk in
  `git diff --no-ext-diff HEAD`. `/code-review` can cite a line from the diff or from the
  working-tree file. Drop its finding when the line falls inside either side (`-a,b` or `+c,d`).
  Two cases still pass this filter: a finding on an unchanged line that depends on an uncommitted
  hunk, and a lens subagent's finding on a line that exists only in the working tree (a `-a,0`
  hunk). Leave them, because the Run caveat tells the reader.
- **Duplicated?** Two lenses on one file/line → keep the clearest, drop the rest.
- **Important?** The strict pass, and the one that does the most work. Name the damage in one
  sentence, or drop the finding. Drop preferences, restatements of the diff, and anything the author
  sees without you. From five small remarks by one lens, keep the one that matters. Dropping
  everything is a correct outcome.
- **Must-fix, should-fix, or note?** A lens only **proposes** a label. Run the four-part test
  yourself on every proposed `MUST-FIX` and on every unlabelled finding. Adopt no proposal without
  the test, and do not ask the lens again, because the test needs only the diff.

  The four-part test, in full: write must-fix only when all four parts are true.

  1. You can complete this sentence from the diff: "After this merge, <who or what> gets <the
     wrong result> at <file>:<symbol>."
  2. You can name a trigger that reaches it today — a caller, a command, a user step, or a
     released artifact. A trigger that needs code nobody has written does not count.
  3. You can name the line in this diff that causes it. Evidence outside the diff does not count.
  4. The failure is one of these six: the software gives a wrong result or it stops; private data
     escapes or a security control breaks; data is destroyed or made unrecoverable; a published
     interface breaks for a caller you can name; a check stops running, or a check passes when it must fail; an invariant that the contract's section 3 marks `[blocking]` breaks.

  If any part fails, demote the proposal. Write should-fix when you can still name a real defect.
  Write note when you cannot name a defect at all. None of these reach must-fix on their own:
  wording, tone, grammar, and voice; a missing test for code that already works; naming, layout,
  duplication, and dead code; an input that no current caller sends; a risk that needs a future
  change to become real; prose that no agent and no user follows to a wrong action.

  The size of the fix is not part of the test. When you are not sure between two levels, use the
  lower one. Promote no finding only to make the author act on it, because a wrong must-fix costs
  a human round-trip. Most PRs get zero must-fix. With more than two, read the report again.

  A lens writes `MUST-FIX`, `SHOULD-FIX`, or `NOTE`. These map straight onto the Step 6 buckets:
  `### Must fix`, `### Should fix`, and `### Notes`. A demotion is not a new finding — keep the
  lens's text, change only the label. Anything the bullets above already dropped stays dropped.
- **Is each should-fix and each note two sentences or fewer?** Cut it here, before Step 6 writes it.
- **Clean verdicts only — is the `ATTEMPTED-BUT-HELD` list specific?** It must name targets and
  inputs from this diff, or say "concern not present". If it is generic, re-dispatch that one lens
  **once** with the Step 4 framing and the same `model: 'sonnet'` pin. If it is still generic,
  mark it `UNVERIFIED` and write no digest of your own, because a false "clean" is the risk this
  check exists for. A lens that flagged something already showed its work.
  This bullet does not apply to the two built-in lenses, which carry no `ATTEMPTED-BUT-HELD`
  list. Their evidence is the two bullets below.
- **Code-review findings?** `/code-review` proposes no `MUST-FIX`, `SHOULD-FIX`, or `NOTE` label.
  Treat each of its findings as an unlabelled finding, and send it through every bullet above. A
  listed deterministic gate still drops a finding that it owns, for example a lint rule. A
  correctness bug gets the four-part test like any other finding. A reuse, simplification,
  efficiency, or altitude (code at the wrong layer) cleanup is not one of the six damage classes,
  so it is should-fix or note. A finding that cites a `CLAUDE.md` rule is a convention finding,
  and it is should-fix or note. It can reach must-fix only through a `[blocking]` invariant in
  section 3 of the contract. Write `code-review` as the `[lens]` name of each entry it gives.
- **Code-review result?** `/code-review` that errored, timed out, or gave no result is a failed
  lens. Write `no result (<the failure, in one clause>)` in its Step 6 receipt row, not `clean`,
  because a run with no code-review result has not looked for bugs. Under `--approve`, it
  withholds the approval; posting.md owns that gate.
- **Goal verdict?** The goal lens returns exactly one word: `achieved`, `partially achieved`,
  `not achieved`, or `undetermined`. Copy the word and its sentence into the Step 6
  `**Goal check:**` line unchanged. An unreadable intent gives the verdict `undetermined`. Write
  `achieved` only when the lens read the intent. A goal lens that returns no
  verdict — it errored, timed out, or gave no dispatch result — gives `undetermined`. Write the
  dispatch failure in the Goal check sentence, and write `undetermined (no lens result)` in the
  verdict slot of the Step 6 receipt row. A `not achieved` verdict adds no entry to
  `### Must fix`, because a goal mismatch is not one of the six damage classes. Under `--approve`,
  a `not achieved` verdict and an `undetermined` verdict each withhold the approval; posting.md
  owns that gate.

## Step 6 — Report

Write the whole report in **ASD-STE100 Simplified Technical English**. These five bullets copy
the Voice bullets in `templates/the-bar.md`, so that this step works with an older contract that
has none. Keep the two copies the same:

- Write one idea in one sentence. Use a maximum of 20 words.
- Use the active voice and the present tense.
- Use one word for one meaning, because a reader takes a new word for a new thing.
- Use plain words, because a reader takes an idiom, a metaphor, humor, or jargon literally.
- Name the file, the symbol, and the damage. Write no hedge word such as "might" or "possibly",
  because a hedged claim gives the author nothing to act on.

Paths, identifiers, and quoted source keep their exact spelling.

This step is the last one that can fix the voice, because Step 7 posts the report verbatim. Pass
through a finding that already obeys. Rewrite one that does not: keep the file, the symbol, and
the claim, and change only the wording.

Match the fence below exactly. **Base** (`$DISP` plus the first 7 characters of `$MB` from Step 2,
no extra git command), **Mode**, **Coverage receipt**, and **Goal check** are in every report,
because a silent no-op must be visible in an advisory tool. **Run caveat** appears only when
Step 2 printed the warning or found uncommitted changes. Then write one row per registry lens,
plus the two built-in lens rows:

```
## PR Review

**Base:** `<base>` (merge-base `<short-sha>`)
**Mode:** <`local report only` when no flag was passed, else the flags verbatim, e.g. `--approve --pr 42`; in no-contract mode, prefix it with `no-contract mode`>
**Run caveat:** <the Step 2 WARNING, verbatim, and the uncommitted-changes text when Step 2 printed `dirty=yes` — omit this whole line when there is neither>
**Coverage receipt:** triaged N registry rows → selected M.
- reviewing-<concern-1> — selected (matched `<glob or change-type>`) → clean; held: <one clause
  naming the target you attacked and the input that should have broken it>
- reviewing-<concern-2> — selected (matched `<glob or change-type>`) → clean; concern not present
  (<the change type this lens defends is absent from the diff>)
- reviewing-<concern-3> — selected (matched `<glob or change-type>`) → 1 must-fix, 1 should-fix, 1 note
- reviewing-<concern-4> — not selected (no changed file matched its globs / diff is purely generated)
- code-review — selected (built-in, medium) → 1 should-fix
- code-review:reviewing-goal-achievement — selected (built-in) → verdict `partially achieved`

**Goal check:** <achieved | partially achieved | not achieved | undetermined> — <one sentence, 20 words maximum, naming the source of the intent>
```

When zero registry lenses were selected (a lock-file-only PR, an empty registry), say so in the
receipt; the two built-in lenses still ran. The Goal check line is in every report, clean or not.

Each clean registry lens carries a one-clause `held:` digest **or** a `concern not present` note,
from the list you verified in Step 5. A flagged lens needs neither, because its finding is the
evidence. If Step 5 got no diff-specific attempt even after re-dispatch, write
`clean; UNVERIFIED (no diff-specific attempt)`, so the reader sees the gap.

The two built-in rows never carry a `held:` digest, a `concern not present` note, or
`UNVERIFIED`, because neither lens has an `ATTEMPTED-BUT-HELD` list. Use these row formats:

- `code-review — selected (built-in, medium) → <counts | clean | no result (<the failure>)>`.
  Count only the entries that survived Step 5. When `/code-review` returned findings and Step 5
  dropped them all, write `clean (<N> dropped in Step 5)`. `no result` is only for a lens that
  gave no result.
- `code-review:reviewing-goal-achievement — selected (built-in) → verdict <word>`.

Nothing survived the filter → close with `---` and `PR looks ok as is.`

Otherwise `---`, then the buckets that have entries, in this order: `### Must fix`,
`### Should fix`, `### Notes`. Write a heading only for a bucket that has at least one entry,
because an empty heading reads as a finding. One entry per finding:

```
### Must fix

**[lens]** `path/to/file.ext` — one-line why-it-matters.

### Should fix

**[lens]** `path/to/file.ext` — what is wrong. Why it matters.

### Notes

**[lens]** `path/to/file.ext` — what is wrong. Why it matters.
```

`### Should fix` and `### Notes` are the non-blocking buckets. Write this one sentence directly
under each heading, and no other, so no reader treats either as a change request:

```
### Should fix

These do not need a change before the merge. The author decides.

### Notes

These do not need a change before the merge. Correct them here or later.
```

Both sentences are true in every mode. Do not write "these do not hold up the approval", because
under `--comment` this run posts no approval.

Step 7 decides the approval, not this step. posting.md holds the approve conditions.

## Step 7 — Post to GitHub

Only when `--comment` or `--approve` was passed. Follow
[references/posting.md](references/posting.md) — preconditions, dedupe, the approve condition, the
post itself, and the `**Posted:**` receipt line.

## Reread the stale PR body

**In-session only.** Say what you find in the session, under the report. Keep it out of the
report and off the PR, because the PR body is not the diff: a remark about it goes in no bucket.
The `**Goal check:**` line is not such a remark.

**Skip this section if no PR body is reachable.** That is not a failure, and it never blocks the
report. When Step 4 or Step 7 already fetched the body, reuse it; otherwise fetch one with
`gh pr view --json body -q .body`, only if `gh` is authenticated and the branch has an open PR.

A PR older than one day can have a body written when the work was still a plan. Reconcile the body
against `git log` and the current tree. Check the **"what this does NOT do"** section first,
because it describes absent work and goes false when that work lands.

## What this skill does not cover

This skill does not request changes, block, merge, or fix the findings. `getting-prs-approved` answers
review feedback, and `getting-prs-merged` merges.
