---
name: bootstrapping
description: Generates a repo-specific PR-review system for the repository it is invoked in. Mines the repo's PR review history, docs, and codebase shape to infer the review concerns that matter here, confirms them with the user, then writes .claude/code-review/contract.md (The Bar + deterministic gates + repo invariants + lens registry), scaffolds one .claude/skills/reviewing-* lens skill per confirmed concern, and writes a REVIEW.md block for Anthropic's Code Review service on GitHub. Idempotent. Use for "/code-review:setup", "bootstrap code-review", "set up PR review for this repo", "generate review lenses", or "write a REVIEW.md".
argument-hint: "[concerns to emphasise]"
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, AskUserQuestion
---

# bootstrapping

This skill makes a PR-review system in the repository it runs in. It writes these files there:

- `.claude/code-review/contract.md` — the single source of truth (four sections).
- `.claude/skills/reviewing-<concern>/SKILL.md` — one generated lens per confirmed concern.
- `REVIEW.md` — one marked block at the repo root, built from the contract (Step 5d).
- `CLAUDE.md` — one marked router block (Step 5c).

`code-review:reviewing-prs` and the lifecycle skills read the contract at review time. Show the
user only the draft checklist (Step 3) and the questions (Step 4).

Read both templates before you generate: `${CLAUDE_PLUGIN_ROOT}/templates/the-bar.md` is the
contract archetype, and `${CLAUDE_PLUGIN_ROOT}/templates/lens-shape.md` is the lens shape. The
plugin has no domain lens catalog. Take the content of each lens from the evidence of this repo and
the answers of the user. The shape template fixes only the structure.

Every review runs two built-in lenses. `code-review:reviewing-goal-achievement` compares the PR's
stated goal (title, body, closed issues, changed plans or specs, commit bodies) with the diff.
Claude Code's `/code-review` skill finds generic correctness bugs. Step 5b says which lenses not to
generate because of them.

## Step 0 — Resolve the target repo

```bash
git rev-parse --show-toplevel                      # abort if this fails: not a repo
gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null \
  || git remote get-url origin 2>/dev/null          # may be empty — that's fine
```

With no GitHub remote, skip Source 1 and continue. Do not
write into the plugin directory, because the files belong to this repo and a plugin update
replaces that directory.

## Step 1 — Detect prior state (idempotent)

```bash
ls .claude/code-review/contract.md .claude/pr-flow/contract.md 2>/dev/null
ls -d .claude/skills/reviewing-* 2>/dev/null
grep -c -- '<!-- pr-flow:router ' CLAUDE.md 2>/dev/null
```

The old `pr-flow` plugin wrote `.claude/pr-flow/contract.md` and
`<!-- pr-flow:router start -->` / `<!-- pr-flow:router end -->` markers in `CLAUDE.md`. Before you
continue, move an old install:

1. When `.claude/pr-flow/contract.md` exists and `.claude/code-review/contract.md` does not, move
   the file and remove the empty `.claude/pr-flow/` directory:

   ```bash
   mkdir -p .claude/code-review
   git mv .claude/pr-flow/contract.md .claude/code-review/contract.md 2>/dev/null \
     || mv .claude/pr-flow/contract.md .claude/code-review/contract.md
   rmdir .claude/pr-flow 2>/dev/null || true
   ```

   When both files exist, keep both files and use the new one. Say in the receipt that
   `.claude/pr-flow/contract.md` is stale and the user can delete it.
2. When `CLAUDE.md` holds the `pr-flow:router` markers, change only the two marker lines to
   `code-review:router` before Step 5c runs. Otherwise Step 5c adds a second router block below
   the old one.

   ```bash
   sed -i.bak -e 's/<!-- pr-flow:router start -->/<!-- code-review:router start -->/' \
              -e 's/<!-- pr-flow:router end -->/<!-- code-review:router end -->/' CLAUDE.md \
     && rm CLAUDE.md.bak
   ```

Say each move in the receipt. After the moves, an old install counts as "something exists".

When nothing exists, do a fresh install. When something exists, ask the user one AskUserQuestion
question with these two choices:

- **Update (fold in)** — keep the existing contract as the base, mine again, and merge the new
  signal in. **Fold-in rule:** dedup by concern name (registry `name` = `reviewing-<concern>`
  basename). Where a concern already exists, the human-edited row and lens are the authority:
  propose only additions. Hand-edited repo invariants and gate commands stay as written: show a
  proposed change to them for confirmation.

  Step 5a names four parts of plugin policy to copy unchanged. Update mode also replaces these
  four parts with the current template's wording, because an old copy is stale. The other parts,
  including the impact categories, follow the normal fold-in rule.

  A lens holds no policy text. Its body is the fixed body paragraph and the `flag:` /
  `do not flag:` list. An old lens has a `## Step 1` block, a `**The rule**` section, and
  `**Flag if:**` / `**Do not flag:**` bullet lists. Rewrite each old lens into the new shape, also
  in Update mode, because the executor's dispatch prompt now owns the rules that the old text
  stated. The new shape is the fixed body paragraph, then one `- flag:` line per Flag-if bullet
  and one `- do not flag:` line per Do-not-flag bullet, with no `## Step 1` block, no rule prose,
  and no heading below the title. Say in the receipt which files you refreshed.
- **Fresh (regenerate)** — rebuild from nothing. Tell the user that this replaces the contract and
  the generated `reviewing-*` lenses.

## Step 2 — Mine four sources

Mine the four sources at the same time, so the network `gh` call (Source 1) does not block the
three local sources. When a source fails or is absent, note it in the receipt and continue with
the others.

### Source 1 — GitHub PR review history (richest; graceful-skip)

This source shows what reviewers in this repo flag. Probe `gh` per
[references/github-access.md](../../references/github-access.md) § *Probe access*. Retry a failed
`gh auth status` as `env -u GH_TOKEN gh auth status`, because a stale `GH_TOKEN` is the usual
cause of a false skip. If `gh` is still not authenticated, is absent, or there is no GitHub remote,
note "PR history: skipped (no gh/auth/remote)" and continue.

```bash
gh pr list --state merged --limit 40 --json number -q '.[].number'   # tune limit to repo volume
for n in $PR_NUMBERS; do
  gh api "repos/OWNER/REPO/pulls/$n/comments" --jq '.[].body'
  gh api "repos/OWNER/REPO/pulls/$n/reviews"  --jq '.[] | select(.state=="CHANGES_REQUESTED" or .body!="") | .body'
done
```

Sort the bodies into recurring themes (naming, tests, security, PHI/data-handling, module
boundaries, GraphQL/API contracts, infra, ADRs, UI, …). Count how often each theme occurs. The
count is the evidence.

### Source 2 — Repo docs & conventions (local)

Read the files that state rules: `CLAUDE.md`, `CONTRIBUTING.md`, `README`,
`.github/PULL_REQUEST_TEMPLATE*`, `CODEOWNERS`, `docs/adr/**` or `docs/decisions/**`, any
`STYLE`/`CONVENTIONS` doc, and every `REVIEW.md`.

```bash
ls CLAUDE.md CONTRIBUTING.md .github/PULL_REQUEST_TEMPLATE* 2>/dev/null
git ls-files 'docs/adr/*' 'docs/decisions/*' 'CODEOWNERS' '.github/CODEOWNERS' 2>/dev/null
git ls-files 'REVIEW.md' '**/REVIEW.md' 2>/dev/null
```

A stated rule becomes a **repo invariant** in the contract. In a `REVIEW.md`, read only the text
outside the `<!-- code-review:router start -->` / `<!-- code-review:router end -->` markers,
because an earlier run of this skill wrote the text inside them (Source 4 reads it). A person's
REVIEW.md rule becomes an invariant, a skip path, or a failure statement for Step 3.

### Source 3 — Git history & codebase shape (local)

Find likely risk areas from structure and tooling: languages and package managers
(`package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`); a GraphQL schema (`*.graphql`, `*.sdl`),
IaC (`*.tf`, `k8s/**`, `helm/**`), UI packages (`apps/**`, `packages/**/ui*`, `*.tsx`); test setup
and CI config; monorepo/service boundaries.

```bash
git ls-files | sed 's#/.*##' | sort -u          # top-level shape
ls .github/workflows/ 2>/dev/null                # CI = likely gate source
```

CI workflow steps and `package.json`/`Makefile` scripts are the main source of the
**deterministic gates** that you confirm in Step 4.

### Source 4 — Existing review artifacts (local)

Read any prior `.claude/skills/reviewing-*/SKILL.md`, prior `.claude/code-review/contract.md`, and
saved review reports. In update mode, these are the base registry and invariants.

In update mode, also read the old `code-review:router` block in the repo-root `REVIEW.md`. Use its
failure statements, skip paths, and Nit limit as the defaults for Step 4 item 5, because they are
stored only in that block.

## Step 3 — Reason → draft a checklist of concerns

Make candidate concerns from the four sources. Give each concern its evidence, a proposed
`reviewing-<concern>` name, and a **draft list of `flag:` lines**: two to eight per concern, each
a condition a reviewer can count or match in a diff, in the shape Step 5b defines. `flag: a function
with more than 20 lines` is a flag line. `flag: functions that are too long` is not. Step 5 writes
this draft list into the lens body. The checklist that the user sees has this shape:

```
Proposed review concerns for OWNER/REPO:
- reviewing-graphql-contract  evidence: schema present (api/schema.graphql) + 3 merged PRs flagged breaking changes
    flag: a field, type, or argument removed from `api/schema.graphql`
    flag: a field type changed from nullable to non-null in `api/schema.graphql`
- reviewing-security          evidence: auth/ + gateway/ dirs; 2 PRs requested changes on token handling
    flag: a token, secret, or password value written to a log call under `auth/**` or `gateway/**`
    flag: a new route under `gateway/**` with no call to `requireAuth`
- reviewing-tests             evidence: CONTRIBUTING requires tests for new routes
    flag: a new file under `api/routes/**` with no new or changed file under `api/routes/**/__tests__/**`
    flag: a changed handler under `api/routes/**` with no changed file under `api/routes/**/__tests__/**`
- reviewing-naming            evidence: CLAUDE.md "canonical component naming" section
    flag: a component name in `**/*.tsx` that is not in the repo's component inventory doc
    flag: a file under `src/components/**` whose basename does not equal its default export name
Deterministic gates detected (candidates to exclude): pnpm build, pnpm lint, pnpm typecheck, pnpm test
What failure looks like here (for REVIEW.md):
    docs/** lies: it states a command, flag, or path that the code does not have
    gateway/** misroutes: a request reaches the wrong service or tenant
Paths to skip (for REVIEW.md): src/gen/**, pnpm-lock.yaml
```

Write two to five **failure statements**. Each is one plain sentence: the paths, then how that
part of the repo fails, in the words a code owner uses ("docs lie", "config misroutes", "the
migration loses rows"). Take them from the contract's §1 impact categories and from the review
history. A **skip path** is a generated, vendored, or lockfile path that a reviewer does not read.
Take skip paths from `.gitattributes` (`linguist-generated`, `linguist-vendored`), from
generated-file headers, and from lockfiles in `git ls-files`.

Propose only a concern that has evidence from this repo. Do not propose a generic-bug concern,
because the built-in `/code-review` lens finds generic bugs on every review. Name any skipped
source here.

## Step 4 — Interrogate the user (AskUserQuestion)

Ask five questions, with defaults from the mining. `AskUserQuestion` takes at most four questions
in one call, so ask items 1–4 in the first call and item 5 in a second call. Step 5 writes each
confirmed answer unchanged into the contract or into `REVIEW.md`.

1. **Confirm / drop concerns** — multi-select over the proposed set, plus an "add another" path for
   a concern the mining missed (capture its name and at least two `flag:` lines, each with a threshold).
2. **Repo invariants, each marked `[blocking]` or `[advisory]`** — confirm the mined ones and let
   the user add repo-specific rules (e.g. "gateway-only persistence", "no secrets in fixtures",
   "public API changes need an ADR"). `[blocking]` means a
   break can hold up approval: it is damage class 6 in the Bar. `[advisory]` means a break is
   reported and does not hold up approval. The default is `[advisory]`, so the user chooses
   `[blocking]` on purpose. A process rule (commit-message style, changelog wording) is
   `[advisory]`. Mark `[blocking]` only where a break causes one of the Bar's other five damage
   classes.
3. **Deterministic gates (the exclusion set)** — the exact commands that the repo's CI runs
   (build, lint, typecheck, test, format-check, secret-scan). Pre-fill from Source 3 and ask the
   user to correct the exact invocation (e.g. `pnpm turbo run build lint typecheck test`,
   `go vet ./... && go test ./...`, `make ci`). A wrong command makes the lenses report lint and
   type errors that a gate owns, and those reports hide the real findings.
4. **The CLAUDE.md router** — tell the user that Step 5c adds a short router block to `CLAUDE.md`,
   and give one way to decline it. Default: add it.
5. **REVIEW.md** — tell the user that Step 5d writes a block into the repo-root `REVIEW.md` for
   Anthropic's Code Review service on GitHub. Confirm the failure statements and the skip paths
   from Step 3, and ask for the nit limit. Default: 5. Give the user one way to decline the
   REVIEW.md block. Default: write it.

## Step 5 — Generate

Make the parent directories first (`mkdir -p .claude/code-review .claude/skills`).

### 5a — The contract (`.claude/code-review/contract.md`)

Fill the four-section archetype from `${CLAUDE_PLUGIN_ROOT}/templates/the-bar.md`:

1. **The Bar** — keep the archetype's generic definition (a finding must be *real* AND *impactful*).
   Change its impact categories to the concerns and invariants of this repo. Remove the template's
   healthcare example rows.

   Copy these parts unchanged: the "report or drop" paragraph, the "default answer is silence"
   paragraph, the whole "Three labels: must-fix, should-fix, note" subsection (its heading through
   its use-the-lower-label rule), and the "Voice — ASD-STE100" subsection. An older contract names
   the silence paragraph "Report important findings only", and the label subsection "Three
   severities" or "Must-fix, or note?". Find each part by name, not by
   position. They are plugin policy, because a repo that changes the labels or the caps gets an
   executor that withholds approval for small things or a review that nobody reads.

   Keep the six damage classes as written: add no class, remove no class, and change no wording,
   because they are the closed must-fix test.
2. **Deterministic gates (never re-flag)** — the exact commands from Step 4, one per line. Follow
   each command with a short scope note that names what it owns: `` `npm run lint` — formatting, style,
   unused vars, import order `` / `` `npm run typecheck` — type errors, missing/incompatible
   signatures ``. The executor uses the note to decide if a gate owns a finding, because it cannot
   find that from the command alone. Where a gate covers something unusual (a lint config that
   also checks doc comments or naming), say so.
3. **Repo invariants** — the confirmed invariants from Step 4. Write the `[blocking]` or
   `[advisory]` marker first on every bullet, as `templates/the-bar.md` §3 shows, because an
   invariant with no marker reads as `[advisory]`.
4. **Lens registry** — one row per confirmed concern, in the Markdown table that
   `${CLAUDE_PLUGIN_ROOT}/templates/the-bar.md` §4 defines. Write no
   row for the two built-in lenses, `code-review` and `code-review:reviewing-goal-achievement`,
   because they run on every review. The executor parses this table, so use only this shape.
   Columns are `| name | when | skill path |`.
   - `name` = the basename of the skill path = `reviewing-<concern>` = the lens's frontmatter
     `name` = the token the orchestrator passes to the Skill tool. Keep all four identical, or
     triage breaks.
   - `when` holds file globs (`**/*.ts`, `api/**`), change-type keywords (`touches-data-model`,
     `renames-component`, `changes-public-api`), or both. The orchestrator always considers a
     lens with a change-type keyword, and the lens filters itself.

   ```
   ## 4. Lens registry

   | name | when | skill path |
   |------|------|------------|
   | reviewing-naming | `**/*.ts`, `docs/**`, `renames-component` | `.claude/skills/reviewing-naming` |
   | reviewing-security | `auth/**`, `gateway/**` | `.claude/skills/reviewing-security` |
   | reviewing-graphql-contract | `**/*.graphql`, `changes-public-api` | `.claude/skills/reviewing-graphql-contract` |
   ```

In update mode, apply the Step 1 fold-in rule.

### 5b — The lens skills (`.claude/skills/reviewing-<concern>/SKILL.md`)

Fill `${CLAUDE_PLUGIN_ROOT}/templates/lens-shape.md` for each confirmed concern. Fill every
`<placeholder>`.

- Make the frontmatter `name:` equal to the directory basename `reviewing-<concern>`. Write a
  repo-specific one-line `description`.
- Keep the shape's `metadata:` block with `internal: true`. `npx skills add` does not list a skill
  that has `internal: true`, so nobody installs a lens into another repo by mistake.
- Write no policy text into a lens, because a copy drifts from its source. The Bar, the three
  labels, the note cap, the voice rule, the `ATTEMPTED-BUT-HELD` list, and the "say nothing about
  the checks" rule are in the contract and in the `reviewing-prs` dispatch prompt. Keep the
  shape's body paragraph as written. Write no `${CLAUDE_PLUGIN_ROOT}` path and no
  `code-review:`-namespaced reference, because a generated lens is a bare-name skill of this repo.
- Write the `flag:` / `do not flag:` list only from this repo's evidence. The lens body is the
  body paragraph and that list: no source citation, no "read first" pointer, no rule essay, no
  quoted paragraphs, no history. Where a line needs a file to judge it, name the file inside the
  line (`… against `ls plugins/relay/roles/*.md``). The Step 3 draft is the input, and the Step 4
  answers can add or remove lines.
  - Each `flag:` line is one condition a reviewer can count or match in a diff. Put the threshold
    in the line when one exists: a number (`more than 20 lines`, `5 or more identical
    lines in 2 or more files`), a path pattern (`src/api/**`), a key (`"version"`), a command, an
    identifier. When the evidence gives no measurable part, name the observable that two
    reviewers would agree on.
  - Each `do not flag:` line names one adjacent change the list does not govern, or one thing a
    command in the contract's Deterministic-gates section owns. Name that command, or the other
    lens that owns it.
  - A lens has two to eight `flag:` lines. A lens that needs more than eight is two concerns.

  When you cannot write the lines from the repo's evidence and the Step 4 answers, go back to
  Step 4 for that concern, because a generic list is not evidence. Delete the shape's worked-example comment
  block.
- In update mode, keep a hand-edited lens unless the user chose fresh, because the human edit is
  the authority. If a lens has no `metadata:` block with `internal: true`,
  add that block to its frontmatter, and change no other line of that lens.
- Do not generate a lens that compares the PR body with the diff or checks the diff against a
  closed issue, because `code-review:reviewing-goal-achievement` does both and two goal lenses
  give two verdicts on one pull request.
- Do not generate a lens that finds only generic bugs, because the built-in `/code-review` lens
  does that. A lens needs at least one repo-specific `flag:` line.

**Proofread each generated lens before you write the next one.** The executor follows these files
literally, so an error in a marker breaks the review with no warning. For example, a broken
`do not flag:` prefix removes the exclusion list, and the lens then reports gate-owned problems.
Read each file again and confirm: the frontmatter parses, `name:` matches the directory,
`metadata.internal` is `true`, every list item starts with `- flag: ` or `- do not flag: `, at
least two `- flag: ` items and one `- do not flag: ` item exist, the body holds no heading below
the title and no paragraph other than the fixed body paragraph, and no `<placeholder>` or
worked-example block is left.

### 5c — The CLAUDE.md router

Skip this step only when the user declined it in Step 4, and say so in the receipt. The block
tells a future session where the review contract is and which command runs it. The block does not
import the contract, so `CLAUDE.md` stays short and a session reads the contract only when it
reviews.

The script replaces the block between its own markers when one exists, appends it when none
exists, and creates `CLAUDE.md` when the file is absent. It changes no text outside its markers.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin code-review \
  --repo-root "$(git rev-parse --show-toplevel)" <<'EOF'
## PR review

The PR review contract is `.claude/code-review/contract.md`. Read it first: it gives the bar for a finding, the deterministic gates, the repo invariants, and the lens registry. The lens skills are in `.claude/skills/reviewing-*/`.
To review a branch or a PR against the contract, run `code-review:reviewing-prs`. To refresh the contract, run `/code-review:setup`.
EOF
```

The script prints `CLAUDE.md router: written <path>` or `CLAUDE.md router: unchanged <path>` and
exits 0. Any other exit code is a failure: show its stderr in the receipt. Do not edit `CLAUDE.md`
by hand to go around a failure, because the script owns the markers.

### 5d — REVIEW.md

Skip this step only when the user declined it in Step 4, and say so in the receipt.

Anthropic's Code Review service on GitHub reads the repo-root `REVIEW.md`. The local
`/code-review` command does not read it. This step writes one marked block into that file, so the
service applies the same bar as this plugin. The code owners own the text outside the block.

#### Fill the template

Read `${CLAUDE_PLUGIN_ROOT}/templates/review-md.md`. Fill each
`<placeholder>` and delete the template's comment line:

- **What failure looks like here** — the failure statements confirmed in Step 4.
- **Cap the nits** — the nit limit confirmed in Step 4.
- **Do not report** — the gate commands from contract §2, and the skip paths confirmed in Step 4.
- **Always check** — each `[blocking]` invariant from contract §3, then each `flag:` line from
  each generated lens, without the `flag:` prefix. Leave out `[advisory]` invariants and
  `do not flag:` lines, because they do not change what is Important.
- Keep the **Evidence** and **Summary** sections as written.

Keep the block at 60 lines or fewer, because the service follows a short file better. When the
lens lines make it longer than 60 lines, keep the lines that name a path or a number and remove
the others. Write no Markdown link to a repo file, because the service ignores the whole file when
it holds more than 64 links. Write no `@` include line, because the service reads includes only
from a protected branch.

#### Write the block

Use the same script as Step 5c, with `--file REVIEW.md`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin code-review \
  --repo-root "$(git rev-parse --show-toplevel)" --file REVIEW.md <<'EOF'
<the filled template>
EOF
```

The script prints `CLAUDE.md router: written <path>` or `CLAUDE.md router: unchanged <path>` for
any file, and exits 0. Write the outcome in the receipt as `REVIEW.md: written <path>` or
`REVIEW.md: unchanged <path>`. Any other exit code is a failure: show its stderr in the receipt.

#### Check the limits

Count the bytes and the Markdown links in the whole file:

```bash
python3 - REVIEW.md <<'EOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
links = [u for u in re.findall(r"\]\(([^)\s]*)", text)
         if not re.match(r"(https?:|mailto:|#)", u)]
print(f"bytes={len(text.encode())} links={len(links)}")
EOF
```

When `links` is more than 64 or `bytes` is 150000 or more, the service ignores the file. Write
`REVIEW.md: OVER LIMIT` and the numbers in the receipt, and tell the user which limit the file
breaks. Keep the code owners' text, because they own it.

#### Check branch protection

The service reads `REVIEW.md` from the default branch or the pull
request's base branch, never from the pull request. It applies severity changes, exclusions, and
the nit limit only when it reads the file from a protected default branch. When it cannot confirm
protection, it reads no `REVIEW.md` at all. Check the default branch:

```bash
DEFAULT=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
gh api "repos/OWNER/REPO/branches/$DEFAULT" --jq .protected
gh api "repos/OWNER/REPO/rules/branches/$DEFAULT" --jq length
```

The branch is protected when the first call prints `true` or the second prints a number above 0.
Write one of these in the receipt:

- `Branch protection: <default> protected`
- `Branch protection: <default> NOT protected — Code Review ignores the Nit limit, the "Do not report" list, and lower severities until you protect it`
- `Branch protection: unknown (<no gh | no auth | no GitHub remote>)`

Do not change any branch setting, because this step only reports.

### 5e — Receipt

```
code-review setup complete for OWNER/REPO (mode: fresh|update)

Contract:  .claude/code-review/contract.md
  Gates:      pnpm build, pnpm lint, pnpm typecheck, pnpm test
  Invariants: 3
  Lenses:     4

CLAUDE.md router: written <path> | unchanged <path> | skipped (declined) | FAILED exit <n>
REVIEW.md:        written <path> | unchanged <path> | skipped (declined) | FAILED exit <n> | OVER LIMIT (bytes=<n> links=<n>)
  Branch protection: <default> protected | <default> NOT protected — ... | unknown (<reason>)

Generated lenses:
  .claude/skills/reviewing-naming/SKILL.md
  .claude/skills/reviewing-security/SKILL.md
  .claude/skills/reviewing-tests/SKILL.md
  .claude/skills/reviewing-graphql-contract/SKILL.md

Built-in lenses (always run, never generated):
  code-review (Claude Code's /code-review skill)
  code-review:reviewing-goal-achievement

Sources: PR history (28 PRs), docs (CLAUDE.md, CONTRIBUTING.md), codebase shape, prior artifacts (none)
Next: run code-review:reviewing-prs on a branch to review a PR against this contract.
      Commit REVIEW.md and merge it to <default>. Code Review reads it only from that branch.
```

Name each skipped source (e.g. "PR history: skipped — gh not authenticated"), so the user knows
the contract uses only local signal and can run setup again after `gh auth login`.
