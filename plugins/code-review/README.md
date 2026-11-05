# Code Review

Repo-tailored PR review as an installable Claude Code plugin. Good PR review is
repo-specific — the concerns that matter in a healthcare monorepo (PHI, GraphQL contract
breaks, module boundaries) are not the concerns that matter in a small Go service or a
marketing site. `code-review` **bootstraps** a review system tailored to *your* repo, then
**executes** it.

The plugin ships two halves that meet at a single interface: **the contract file in the
target repo** (`.claude/code-review/contract.md`). Bootstrap writes it; the executor reads it.
Neither half hardcodes the other's concerns.

## Half 1 — Bootstrap: `/code-review:setup`

Interactive, idempotent command (backed by the `bootstrapping` skill) that inspects
your repo and generates a tailored review system into it:

1. **Detect prior state** — if a contract or generated lenses already exist, fold in new
   findings rather than clobbering human edits.
2. **Mine four sources** for candidate concerns:
   - GitHub PR review history via `gh` (past comments, requested changes, recurring
     objections) — the richest "what humans actually flag here" signal; gracefully skipped
     when `gh` is absent/unauthenticated or there is no GitHub remote.
   - Repo docs & conventions (CLAUDE.md, CONTRIBUTING.md, PR/issue templates, ADRs,
     CODEOWNERS, style guides).
   - Git history & codebase shape (languages, layout, tests, CI config, presence of GraphQL
     schema / IaC / UI packages).
   - Existing review artifacts (prior lenses, prior contract, saved reports).
3. **Reason → draft** a candidate concern checklist, each with its evidence.
4. **Interrogate you** — confirm / add / drop each concern, capture repo invariants, and
   record the repo's deterministic gate commands (the exclusion set).
5. **Generate** — write the contract and scaffold one lens skill per confirmed concern, add a
   short router block to the repo `CLAUDE.md` (where the contract is and which skill runs it,
   between `<!-- code-review:router start/end -->` markers; a re-run replaces it in place),
   write a marked block into the repo-root `REVIEW.md`, then emit a receipt of what was written.

### What it writes into the target repo

```
.claude/code-review/contract.md          THE CONTRACT — single source of truth
CLAUDE.md                            one marked router block, appended or replaced in place
REVIEW.md                            one marked block for Anthropic's Code Review service on GitHub
.claude/skills/reviewing-<concern>/  one generated lens skill per confirmed concern
  └── SKILL.md
```

### REVIEW.md

Anthropic's Code Review service on GitHub reads the repo-root `REVIEW.md`. The local
`/code-review` command does not. Setup writes one block into that file from the contract
(`templates/review-md.md`). The block is short and has these parts: what failure looks like in this
repo, a `file:line` evidence rule, a Nit limit, paths and CI checks not to report, the
`[blocking]` invariants and lens `flag:` lines to always check, and a summary that starts with a
count. Text outside the block belongs to the code owners, and setup never changes it.
`reviewing-prs` reads that text too: a "do not report" line drops findings, and any other line
is an advisory rule.

The service reads `REVIEW.md` only from the default branch or the pull request's base branch. It
applies the Nit limit, the exclusions, and lower severities only when that branch is protected.
Setup checks protection and reports it; it does not change branch settings. Merge `REVIEW.md` to
the default branch before you expect a change in reviews.

## The contract — `.claude/code-review/contract.md`

Markdown, human-editable, read by **all** executor skills. Four sections:

1. **The Bar** — what a finding must clear to be reported: *real* (concretely true in this
   diff, with evidence) **and** *impactful if left unattended*. Report or drop, and report the
   important findings only — silence is the default, and no lens is measured by how much it
   returns. A reported finding then gets one of three labels: **must-fix** (the only one that
   holds up approval), **should-fix**, or **note** — should-fix and note are written in two
   short sentences at most and never hold up approval. Must-fix needs all four parts of the
   Bar's must-fix test: a named wrong result, a trigger that exists today, a line in this diff,
   and one of six closed damage classes. When unsure, use the lower label. The Bar also carries
   the ASD-STE100 voice rule that every line of review text obeys.
2. **Deterministic gates (never re-flag)** — the repo's own lint/typecheck/CI/secret-scan
   commands, discovered at setup. A lens must never surface what a gate already owns; the
   lifecycle skills run these as the CI-equivalent gate.
3. **Repo invariants** — the mined, repo-specific rules.
4. **Lens registry** — the authoritative list of active lenses, as a Markdown table
   (`| name | when | skill path |`; see `templates/the-bar.md` §4 for the row grammar), where
   `name = basename(skill path)` (e.g. `reviewing-naming -> .claude/skills/reviewing-naming`). The
   orchestrator reads this to decide which lenses to fan out for a diff, and invokes each by
   its bare skill name (`reviewing-<concern>`) via the Skill tool. The registry lists this repo's
   lenses. The two built-in lenses (`/code-review` and the plugin's own
   `reviewing-goal-achievement`) run on every review and need no row.

## Half 2 — Execute

Shipped skills that run the review against the generated contract:

- **`reviewing-prs`** — repo-agnostic orchestrator. Reads the contract's Bar and Lens
  registry, triages which lenses apply to the diff, fans them out adversarially via the
  Workflow tool, filters/verifies findings against the Bar, and emits a coverage-receipt
  report. Every review also runs two built-in lenses: Claude Code's `/code-review` skill on the
  diff (at `medium` effort, read-only), and the goal lens. With no contract it asks whether to run
  `/code-review:setup` first or to review now with the two built-in lenses (no-contract mode). A
  scheduled run does not ask; it reviews in no-contract mode. No-contract mode never approves.
  A run where `/code-review` gives no result never approves either.
  **Local and read-only by default**; two flags opt into GitHub, and a third names the target:
  | Flag | Effect |
  |------|--------|
  | *(none)* | In-session report. No GitHub writes. |
  | `--comment` | Post the report to the PR as a comment. Uncommitted changes to tracked files disable the post. |
  | `--approve` | Post it **and** approve when the report has no must-fix finding — should-fix entries and notes are posted with the approval, not against it. A must-fix finding degrades it to a comment, and says why. It approves only when the goal verdict is `achieved` or `partially achieved`, and only when `/code-review` gave a result. [posting.md](skills/reviewing-prs/references/posting.md) holds the full list of approve conditions. |
  | `--pr <number>` | Names which PR the posting flags target, when the branch doesn't resolve to one. On its own it writes nothing. It reviews the working tree either way, and refuses to post if that tree isn't the PR's head. |

  These flags are also how `scheduling-pr-reviews` posts: the loop picks a posture and then calls
  this skill with it (`--comment` for *Comment-only*, `--comment --approve` for
  *Approve-when-clean*) rather than carrying its own posting code. So this is the **single** place
  code-review writes a verdict, and ad-hoc and scheduled runs agree on a PR by construction. A
  `head=<sha> lenses=<n> intent=<digest> cr=<ok|none>` marker makes a re-run at an unchanged
  head and an unchanged PR title and body a no-op rather than a duplicate comment — and because both entry
  points post through here, that dedupe covers both. The `intent` digest is in the key because an
  edited title, body, or closed issue can change the goal verdict without moving the head. A
  `cr=none` field (the `/code-review` lens gave no result) is never a dedupe hit, so the next run
  at the same head tries again.

- **`reviewing-goal-achievement`** — the one lens skill the plugin ships. It reads the PR title and
  body, **every issue the PR closes with a `fixes` or `closes` keyword**, every plan or spec the
  diff changes, and the commit messages. A body that only says `Fixes #7` therefore states its
  goal in issue 7, and the lens checks the diff against that issue. It returns one verdict:
  `achieved`, `partially achieved`, `not achieved`, or `undetermined`. Every review runs it, and
  every report carries a `**Goal check:**` line. A `not achieved` verdict and an `undetermined`
  verdict each withhold `--approve`. The verdict alone is never a must-fix finding.
- **`getting-prs-green`** — drives a single PR's checks to all-green: syncs the branch with its
  base first (a stale branch's checks don't describe what merge will produce), then fetches the
  failure logs, fixes, gates locally, and pushes — round after round until CI is green or a cap
  or escalation stops it. Never merges, never approves, never suppresses a finding.
- **`getting-prs-approved`** — drives a single PR to approval by answering every review comment,
  running the contract's discovered gates as the CI-equivalent.
- **`getting-prs-merged`** — drives an approved PR to merged.
- **`scheduling-pr-reviews`** — routine review of open PRs on a cron cadence. Owns *when* and
  *which*; delegates the review **and the post** to `code-review:reviewing-prs` with the chosen
  posture's flags. It never states the Bar, never enumerates lenses, and never writes to GitHub
  itself.

### Shared references

Behaviour common to several executor skills lives once, in `references/`, and each SKILL.md links
what it needs directly — one level deep, so nothing is reached only through another reference:

| File | Owned behaviour | Read by |
|------|-----------------|---------|
| `references/github-access.md` | Resolving `$REPO`/`$N`/`$HEAD_REF`/`$BASE_REF`, and the `gh`-vs-MCP probe | all five executor skills; `bootstrapping` for the `gh` probe |
| `references/loop-engine.md` | The shared control loop: pacing, the GitHub-thread ledger, worker liveness, the local gate, escalation | the three `getting-prs-*` skills |
| `references/base-sync.md` | `update-branch` vs. conflict rebase, worktree hygiene, `--force-with-lease` | `getting-prs-green`, `getting-prs-merged` |

Skill-specific detail stays next to its skill: `reviewing-prs/references/posting.md` (loaded only
when a posting flag is passed) and `getting-prs-approved/references/codeowners.md`.

## Half 3 — Explain

One read-only surface that reads no contract, runs no lens, and writes nothing:

- **`/code-review:hitl <pr-number | pr-url | branch>`** — invokes the `walking-through-prs`
  skill for a Human in the Loop walkthrough. It summarizes the PR, offers grounded goal,
  implementation, and risk questions, lets the engineer drill down or return to any prior
  level, and preserves the walkthrough in a local `${TMPDIR:-/tmp}` state file. Its approval prompt is
  verbal only. It never writes to GitHub, emits findings, reads checks, or reports merge state.

## Half 4 — Review by hand: `/code-review:review-pane`

`/code-review:review-pane [pr-number | pr-url | owner/repo#number]` opens a pane that walks one PR
chunk by chunk. With no argument it uses the last PR that the session names, else the PR of the
current branch. A bare number is a PR of the repo the session runs in; for a PR of another repo,
give its url or `owner/repo#number`. It needs Claude Code 2.1.294 or later.

The pane shows one chunk at a time, in story order. From the top: the PR title in a box of one
line, the PR summary in a box, a position line (a green `1/n` and the viewed and draft counts), the
story heading, the chunk line (`▶ ✓` marks the cursor and an accepted chunk), the "Why" note in a
box, then the diff of the chunk. The diff fills all the rows that are left, and its frame closes
inside the pane. The last line shows "lines a-b of n · j/k scroll" at the left and "press h for
help" at the right. When you write a comment, the input box takes the bottom. The box starts 2
lines tall and grows as you type, to 5 lines at most; after 5 lines the text scrolls up in the box.
Shift+Enter adds a line, and Enter keeps the comment as a draft. If your terminal does not send
Shift+Enter, the hint beside the box shows `\⏎ new line`: type `\`, then press Enter. Under the
chunk, a draft shows 5 lines at most; `c` opens all of it. The model writes the
PR summary and the note on the chunk only when you press `e`. Each shows 3 lines at most, and the
two texts start in the same column. The keys, the questions and the answers show in a dialog, not
in the pane.

When `a` accepts the last open chunk, the chunk part changes to "✅ All n chunks are reviewed." and
an "Approve PR" button. Ctrl+X Shift+A (or Enter on the button) approves the PR. `n` or `p` goes
back to a chunk, and `s` puts the comments in the prompt box.

| Key | Action |
|---|---|
| `n` / `p` | Move the cursor to the next or the previous chunk. |
| `a` | Accept the chunk and move to the next one, as the GitHub "Viewed" box does. Nothing goes to GitHub. |
| `u` | Move to the next chunk that is not accepted. |
| `c` | Write a draft comment on the cursor chunk. A second `c` edits it; an empty Enter on an edit deletes it. Shift+Enter adds a line. |
| `q` | Open a dialog with the full note and the questions on the chunk. Type a new question in "Type something"; the answer shows in the dialog. |
| `e` | Explain the cursor chunk in one sentence. The first `e` also writes a PR summary of 3 lines at most. |
| `s` | Close the pane and put every draft comment in the prompt box, after the text that is already there. Each comment shows under its file, its lines, and its `@@` hunk header. Nothing is sent: you read the text, add to it, and press Enter. The drafts stay, so you can also post them to GitHub. |
| `j` / `k` | Scroll the diff of the cursor chunk down or up half of its window. |
| `r` | Load the new commits after the header shows "New commits". |
| `x` | Close the pane. The accept marks, the drafts and the Q and A stay saved. |
| `h` | Open a dialog with all the keys. A pane key is one letter or one digit, so `?` cannot be the key. |
| Ctrl+X Shift+A | Approve the PR. It works only when every chunk is accepted; before that, the pane says how many chunks are open. |
| Ctrl+X Shift+P | Post every draft comment now, as one comment review. The accept marks stay, and the review goes on. |
| Ctrl+X Shift+C | Post the draft comment of the cursor chunk now, as one comment review. The other drafts stay. |

A hotkey works only while the pane holds the focus. Esc gives the focus back to the prompt, and
Ctrl+X Tab gives it back to the pane.

Ctrl+X P opens and closes the pane from the prompt. A closed pane comes back at the same chunk,
with no new load; with no review to show, it loads as `/code-review:review-pane` with no argument
does. A plugin cannot add a key binding of its own, so add this line to the `Global` block of
`~/.claude/keybindings.json` (`/keybindings` opens the file):

```json
"ctrl+x p": "app:toggleReplTab"
```

The pane reads that chord through the action `app:toggleReplTab`. Only Claude Code's earlier diff
panel uses this action, and the built-in diff mod replaces that panel. Without the line, the chord
does nothing, and the command still works.

Ctrl+X Shift+A approves the PR, Ctrl+X Shift+P posts every draft, and Ctrl+X Shift+C posts the
draft of the cursor chunk. A pane key is one lowercase letter, so Shift+A is the same key as `a`
(accept). A binding of Shift and one letter does not press a plugin button, so each of these keys
must be a chord. Add this block to `~/.claude/keybindings.json`:

```json
{
  "context": "Pane",
  "bindings": {
    "ctrl+x shift+a": "app:toggleDiffNoiseFilter",
    "ctrl+x shift+p": "app:toggleDiffPreSession",
    "ctrl+x shift+c": "app:cycleDiffBase"
  }
}
```

The pane reads each chord through the action beside it. Only the diff panel and the diff dialog of
Claude Code use these actions. Without the block, Enter on the "Approve PR" button still approves,
and the two post keys do nothing.

A post of the drafts is a comment review, never an approval. It sends only the drafts that exist
when you press the key, and then removes them. A draft that cannot attach to a line goes into the
review body as text. A post fails when new commits came since your last `r`; then press `r`.

The approval is one GitHub review: each draft is an inline comment, and a draft that cannot attach
to a line goes into the body as text. It is the reviewer's own approval, not an automated one —
`reviewing-prs` owns those, and `skills/reviewing-prs/references/posting.md` names both writers.
GitHub does not let an author approve their own PR. On your own PR the button is "Post the
comments", and the same key posts your drafts as a comment review.

## Flow

```
/code-review:setup  ─writes─▶  .claude/code-review/contract.md + .claude/skills/reviewing-*
                                     │
                                     ▼
        reviewing-prs (+ lifecycle skills) ─read the contract─▶ tailored review
```

## Templates (generator reference, not active skills)

`templates/the-bar.md` (the contract archetype), `templates/lens-shape.md` (the single
generic lens structure), and `templates/review-md.md` (the REVIEW.md block) are what the
bootstrap generator instantiates. The plugin ships one
process lens (`reviewing-goal-achievement`), runs Claude Code's `/code-review` as a second
built-in lens, and has **no domain lens catalog** — the plugin models
the review *process*; a domain lens is only a list of `flag:` lines, each with a measurable
condition, plus `do not flag:` exclusions — generated from the target repo's own mined evidence
and the user's answers at setup time. All review policy lives in the contract and in the
`reviewing-prs` dispatch prompt, never in a lens. Lenses are pure
extension points.
