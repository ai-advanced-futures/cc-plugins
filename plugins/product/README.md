# PRD Analysis Plugin

Product-level PRD creation and roadmap planning through lens-driven Socratic
exploration, with full traceability from the PRD to the roadmap and to GitHub.

## Overview

The plugin writes two OKF v0.2 bundles for each repository:

| Bundle | Path | What it holds |
|------|------|---------------|
| PRD | `docs/product/prd/` | One page for each requirement: a problem, a persona, a need, a journey, a capability, an experience (a screen structure, a state rule, or an interaction rule), a scope item, a metric, a risk, a constraint, a decision, or a question |
| Roadmap | `docs/product/roadmap/` | One page for each work item: a project, a milestone, an epic, a feature, a story, a task, an acceptance criterion, or a run |

One page holds one thing. Each relationship is a typed field in the
frontmatter, and the script derives the other direction. An agent reads the
index of a directory, then one page, then the links of that page. It does not
read the full bundle.

Three principles run through each skill:

1. **The product hat.** Exploration and planning stay at the product level:
   problems, people, journeys, capabilities, scope, and metrics. An
   implementation ask (an architecture, a stack, an API) becomes a product
   constraint. The technology choice does not go in the PRD. See
   `skills/shared/product-hat.md`.
2. **Traceability.** A roadmap item records the requirements it satisfies:
   `- { to: prd:/capabilities/CAPABILITY-03.md, hash: a1b2c3 }`. When the
   requirement text changes, its hash changes, and the item is flagged.
3. **The script does the exact work.** `prd.py` assigns each ID, writes each
   page, each index, each status table, and each log line. A skill never
   chooses an ID and never edits a generated block.

## Quick start

```bash
# Make the two bundles and add the router block to CLAUDE.md
/product:setup

# Ask a question about the product
/product:ask "which capability covers single sign-on?"

# Find the requirements, lens by lens
/product:explore

# Keep the findings of the session
/product:learn

# Test the PRD from the view of a developer
/product:simulate

# Make the roadmap for the scope you choose
/product:plan
```

For a new repository, start with `/product:setup`, then `/product:explore`. For a repository that holds
the v3 file `docs/product/prd.md`, run `/product:migrate` first. Each other skill
stops when it finds a v3 file and no `docs/product/prd/index.md`.

## The script

Each skill calls one script, from the repository root:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py <subcommand>
```

If `uv` is not available, run `python3` with the same path.

| Subcommand | What it does |
|---|---|
| `init` | Writes the two empty bundles. |
| `upgrade` | Brings existing bundles to the brain standard: back-fills `generated`, adds `log.md`, runs `regen`, and writes the manifest and the registry entry. |
| `new` | Writes one page with the next ID. |
| `set` | Changes one or more fields of a page. It refuses `type`, `generated`, `protected`, and each field that only `state`, `regen`, or `drift` write. |
| `link` | Adds a typed link from one page to a target. |
| `unlink` | Removes a typed link from one page to a target. |
| `remove` | Deletes a page and retires its ID. It refuses a page with `protected: true`. |
| `log` | Writes one entry to the event log of a bundle. |
| `list` | Prints one line for each page of a type, from the frontmatter only. |
| `hash` | Prints the body hash of each page that you name. |
| `resolve` | Prints the path of an ID or an alias. |
| `stage` | Prints early or mature for each capability. A capability is mature when a `done` or `released` work item traces to it, directly or through its parent chain. |
| `regen` | Writes each generated block. `--check` writes nothing and names each stale file. |
| `check` | Tests the OKF rules, the schema, and the graph rules. |
| `drift` | Compares each stored trace hash with the page that it names. `--write` adds each drifted target to `drifted`. `--show` prints the text of the last accept, from Git, and a diff to now. `--accept` clears one flag. |
| `state` | Changes the state of one work item. It is the one write path for `state`. |
| `migrate` | Turns the v3 files into the two bundles. `--scan` reports and writes nothing, `--dry-run` builds the tree and deletes it, and `--finish` stores the hashes after the skill step. |
| `claim` | Takes one ready work item, or every Story of one spec, under a lease. A group claim is all or none. |
| `heartbeat` | Moves the lease of a claim forward. |
| `release` | Gives one claimed item back. |
| `expire` | Releases each lease that is over. |
| `ready` | Prints the work that an agent can take. |
| `run-checks` | Runs the declared checks of one item and writes one Run page. |
| `github` | The GitHub round trip: `github plan`, `github apply`, and `github pull`. See "Connect a GitHub Project". |

`set`, `link` and `unlink` take `--actor`. With `--actor human:<login>`, `generated.by` of the page names the person. With `--actor agent:<id>`, `generated.by` is `prd/<version>`, and the command adds 1 line to `log.md` of the bundle that names the agent, for example `* **Set**: [STORY-12](stories/STORY-12.md) size, parent, by agent:<id>, at <time>`. With no `--actor`, `generated.by` is `prd/<version>`, and no line is written. `remove` names its actor in its `Forget` line.

**The exit code is the verdict.** A skill gets the verdict from the exit code,
not from the output:

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | A finding or a data error. A finding is, for example, a drifted trace, a stale file, or a rule error of `check`. A data error prints one `ERROR:` line on stderr. |
| `2` | A usage error or an internal error, for example a wrong argument, a bundle that does not exist, or a write lock that another `prd.py` process holds. |

`/product:review` and `/product:roadmap-sync` do not stop on the code 1 of
`drift --all --write`, because that code is the drift that the skill resolves.
`drift --show` is text for a person, not a verdict, so it exits 0.

## The hook

`hooks/brain-hook.sh` runs after a Write or an Edit of a file inside the `prd` or `roadmap`
bundle, and after a Bash command that runs `prd.py`. A quoted text that names it is not a run. The hook runs three steps, in this order:
`prd.py regen`, `prd.py check`, then the general check of the `knowledge` plugin. A warning or a
skipped rule shows as added context, and the tool call still succeeds. An error, or a failed step,
stops the tool call and shows the finding.

## The lens system

`/product:explore` guides discovery through an ordered **spine**. Each lens builds
on the lenses before it:

```
Problem → Personas → Journeys → Capabilities → Scope → Success metrics
```

Four **satellite** lenses open when their prerequisites are met: Business
model, Go-to-market, Risks and assumptions, and Experience. The `experience`
lens is for a product with a user interface. It opens when both Journeys and
Capabilities are met.

- `/product:explore personas` goes straight to one lens.
- `/product:explore` with no argument asks what your goal is, and offers the lenses
  that make sense now.
- **Soft gate**: a lens whose prerequisite is missing (journeys with no
  personas) gives a recommendation to do the prerequisite first. You can
  override it, and the explorer captures a minimal bootstrap.

The bundle layout, the page format, the ID prefixes, and the write rule are in
`skills/shared/bundle-schema.md`.

## Skills

### `/product:setup`

Makes the two bundles with `prd.py init` when `docs/product/prd/index.md` is
absent, and adds a short router block to the repo `CLAUDE.md`: where the two
bundles are, which file to read first, and the three commands to use. The
block sits between `<!-- prd:router start -->` and `<!-- prd:router end -->`.
A second run keeps the bundles and replaces the block in place; it changes no
text outside the markers. A repository that holds the v3 file
`docs/product/prd.md` must run `/product:migrate` first.

**Output**: the two bundles, and one block in `CLAUDE.md`.

### `/product:ask <question>`

Answers a question about the product from the two bundles, with no write.
Four shortcuts cover a broad question (`prd/product.md`), a capability by
name (`prd/capabilities/index.md` and its `aliases`), a roadmap item's PRD
reason (its `traces`), and the work state (`prd.py list`). Any other
question goes to the `knowledge:ask` skill, which can also follow a link
into the system design or the ADRs.

### `/product:explore [lens]`

Socratic exploration of one lens at a time: one question at a time, 2 to 4
options for each question, and each question builds on the last. The question
guides come from standard product practice: jobs to be done, journey mapping,
Kano, MoSCoW, North Star metrics, and riskiest-assumption testing.

**Output**: the findings of the session, ready for `/product:learn`.

### `/product:learn [lens]`

Writes the findings into the PRD bundle:

- One page for each finding, through `prd.py new`. The script gives the ID.
- The relationships, stored one time on the page of the later lens.
- The summary in `prd/product.md`, and one Learn line in `prd/log.md`.
- The drift check for each requirement the session changed.

### `/product:simulate [capability | --all] [--decide autonomously|interactively]`

A senior-developer persona reads one capability and reports where the work
stops: an ambiguity, a missing error path, an unstated assumption, or an edge
case. The persona is technical. The captured decisions are not: each one lands
as product behavior or as a product constraint.

A gap counts only when a developer who builds the capability now must guess.
A gap that only matters later goes to a Later list, and you get no question
about it.

With `--decide autonomously`, the default, an assessor agent picks an option
for each gap and gives it a level (detail, middle, or direction), a
confidence, and a visibility (visible or hidden). A table sends the gap to you
now, or sets it aside. Detail gaps, and gaps that each user sees right away,
are set aside more often. A capability that a `done` roadmap item traces to is
mature (`prd.py stage`), and a mature capability sends more gaps to you. At
the end, you accept the set-aside picks with `all`, or with `all except 3, 7`.
`--decide interactively` asks you about each gap that counts. `--all` walks each
capability and does not ask whether to go on.

### `/product:migrate [map-file]`

Turns the v3 files into the two bundles. It scans the v3 files and reports the
shapes it finds, takes a type map from you, builds the tree in a temporary
directory, tests five properties on it, and only then moves it. No ID and no
trace is lost. `prd.py migrate --dry-run` builds the tree and deletes it. The
v3 files go to `docs/product/archive/`.

### `/product:plan [scope]`

The roadmap generator. It asks three things:

1. **What do we plan?** The MVP, the next phase, the full product in phases, or
   one phase.
2. **How do we slice?** It proposes strategies from the PRD content: a walking
   skeleton, persona first, journey first, or risk first, each with the phases
   it gives.
3. **How deep?** Milestones, epics, features, or stories. The default is
   stories.

Each phase becomes a Milestone page, so the full shape is visible. Only the
chosen slice is broken down, and only its items leave `backlog`. Run
`/product:plan` again for the next phase.

`/product:plan` drives the identify skills below. Each one also runs alone.

### `/product:themes-identify [milestone]` · `/product:features-identify [epic]` · `/product:stories-identify [feature]` · `/product:tasks-identify [story]`

The four steps of the tree: group the capabilities of a milestone into epics,
divide an epic into features, divide a feature into stories with their
acceptance criteria, and divide a story into engineering tasks. An epic and a
feature each hold one trace or more.

### `/product:stories-estimate [feature]`

T-shirt sizing (S, M, L), one story at a time, with the team present. The size
goes in the `size` field of the story.

### `/product:roadmap-sync`

Three parts in one run:

- **The GitHub round trip**: `prd.py github pull` reads GitHub back,
  `prd.py github plan` prints the change set, and `prd.py github apply` pushes
  it. The skill shows the change set and asks you before each apply.
- **Drift**: `prd.py drift --all --write` recomputes each trace hash. An item
  whose requirement changed gets that target in `drifted`, and the issue gets
  the label `needs-review` on the next apply. You accept the new text, or you
  change the item. This part is `/product:review`.
- **The evidence scan**: for each work item that GitHub does not hold, the
  skill looks for the ID and each alias in the last 50 commit subjects and in
  the branch names. An Explore agent looks in the code and in GitHub. A match
  is evidence, not a verdict: you confirm the state of each item. With no git
  repository, the skill tells you that the scan did not run.

### `/product:review [ID...]`

The drift part of `/product:roadmap-sync`, as a command of its own. Use it when the
repository has no GitHub Project, or when you want to review drift and nothing
else. It reads and writes only the bundles.

- `prd.py drift --all --write` flags each drifted trace. With IDs of PRD pages,
  it checks only the traces to those pages.
- `prd.py drift --show <ITEM> <TARGET>` finds the text of the last accept in
  the Git history of the requirement, and prints the commits that changed it
  and a diff to now. The trace stores only a short hash, so Git is the source
  of the old text. With no matching commit, it prints the current text.
- The skill groups the traces that one change caused, for example one wording
  change to many requirements. You answer one time for a group, or for each
  item.
- Only you accept. The skill runs `prd.py drift --accept` only for a trace that
  you accepted, with your `human:<login>`, and it lists each accept. It
  dispatches no agent.

`/system-design:learn` of the `system-design` plugin replaces the old
`/product:system-design` command.

### `/product:specifying-stories [FEATURE-ID]`

Turn one Feature and its Stories into one spec file or more in
`docs/superpowers/specs/` that `/relay:implement --spec` accepts. The skill
infers each technical decision from an accepted ADR, a PRD Decision page, an
Experience page of a Story, or a built spec, and asks the person only the rows
that no source answers. An Experience page counts when it describes a
Capability or a Journey that the Feature or a Story traces, or when a page
traces it directly. A product with no Experience page gets the same spec as
before. It records each cross-cutting decision as an ADR with
`lifecycle: accepted`, writes the path of the spec in the `spec` field of each
covered Story, and sets each of those Stories to `ready`. The work goes on a
`spec/<FEATURE-ID>` branch and
in one draft pull request, apart from the build. The skill needs the
superpowers plugin, and it uses the relay plugin for the code summary when
relay is present.

**Use when**: A Feature has Stories and you want a person to decide how they
are built.

### `/product:checks-declare [story]`

Records the check argv of each acceptance criterion of one story, with the
login of the person who declares it. Rule E8 refuses a check that no person
declared, because a check runs code on the machine of the user.

### `/product:work [ID]`

The agent protocol for one roadmap item: claim it under a lease, read the item
and its links only, do the work, run the checks, and give the item back for
review. A person, or an agent with a recorded approval (`--approved-by`), sets `done`.

## Connect a GitHub Project

1. Make the Project in GitHub. One roadmap bundle is one Project.
2. Add its owner and number to `docs/product/roadmap/projects/PROJECT-01.md`:

   ```yaml
   github:
     owner: acme
     number: 7
   ```

3. Give the token the `project` scope: `gh auth refresh -s project`.
4. Run `/product:roadmap-sync`. It shows the change set and asks before it pushes.

The three commands behind it:

| Command | What it does |
|---|---|
| `prd.py github plan` | Prints the change set and writes nothing. It is a pure function of the roadmap pages and one snapshot of the GitHub API. |
| `prd.py github apply` | Runs the change set, then writes the number, the node ID, the URL, the `pushed_hash`, and the `synced` pair back on each page. `--dry-run` prints each change and calls nothing. `--keep <ID>` (on `plan` too) sends the values of a page over an edit that a person made in GitHub. It is also the only way to send the title and the body of a bound issue (a `BOUND:` line of `github pull`). |
| `prd.py github pull` | Reads GitHub back. A push-only field that differs is reported, never taken. A page with an issue number and no `pushed_hash`, whose issue holds text that a person wrote, is reported in a `BOUND:` line, and the sync sends no title or body to it. A state that a person changed in the Project goes through `prd.py state`, so the log stays complete. `--adopt` makes a page for an issue on the Project that has none. An issue that is not on the Project is not roadmap work, and the pull ignores it. |

Each of the three takes `--snapshot <file>`, which reads a recorded API
snapshot instead of calling GitHub. The whole test suite runs on recorded
snapshots.

Each plan line names its subject: `create_issue_type Epic`,
`create_field Planned start`, `create_issue STORY-12`. A `create_issue_type`
line adds that name to every repository of the organization, not to this one,
so the skill names it in the question before the apply.

A repository that a user owns has no issue types. The push then gives each
issue the label `type:epic`, `type:feature`, `type:story`, or `type:task`.
An organization repository takes the same labels when the token has no
`admin:org` scope, because GitHub makes an issue type only with that scope.

## Traceability model

```
docs/product/prd/capabilities/      docs/product/roadmap/features/
──────────────────────────────      ──────────────────────────────
CAPABILITY-03.md                    FEATURE-04.md
  title: Book a slot       ◄──────    traces:
  in under a minute                     - { to: prd:/capabilities/CAPABILITY-03.md,
                                            hash: a1b2c3 }
```

- An ID is `<PREFIX>-<NN>` and is permanent. A removed page gets
  `status: deprecated`, and the file stays. `aliases` holds each old ID.
- `a1b2c3` is the first 6 hex characters of the SHA-256 of the page body. The
  generated `LINKS` block and the generated `STATUS` block are removed first.
- A hash that does not match is a drift: the requirement changed and the item
  needs a person to read it.
- `prd.py drift --all --write` adds the target of each drifted trace to the
  `drifted` field of the item. Only a person clears a flag:
  `prd.py drift --accept <ITEM> <TARGET> --actor human:<login>` stores the new
  hash and removes the target from `drifted`.

The full rules are in `skills/shared/bundle-schema.md` and
`skills/shared/roadmap-model.md`.

## Status tables

`prd.py regen` writes one status table on each container page, between
`<!-- STATUS:START (generated, do not edit) -->` and `<!-- STATUS:END -->`. No
page holds the full tree, so each page stays under 100 lines.

```markdown
<!-- STATUS:START (generated, do not edit) -->
| Item | State | Progress | Owner | Blocked by | Drift |
|---|---|---|---|---|---|
| [MILESTONE-01: Foundation](../milestones/MILESTONE-01.md) | - | 3/5 (60%) | - | - | - |
| [EPIC-02: Booking](EPIC-02.md) | in_progress | 1/4 (25%) | human:ana | - | CAPABILITY-03 |
<!-- STATUS:END -->
```

States: `backlog`, `ready`, `claimed`, `in_progress`, `in_review`, `blocked`,
`done`, `released`, and `cancelled`. `ready` and `blocked` are computed from `blocked_by`.
Only `prd.py state` changes a state, and each change adds one line to
`roadmap/log.md`.

## Workflow

```
1. /product:migrate          → The v3 files to the two bundles (one time)
2. /product:explore          → Lens-by-lens discovery (makes the bundles)
   └─→ /product:learn         → Keep each session
3. /product:simulate         → Developer-view stress test
   └─→ /product:learn         → Keep the decisions
4. /product:plan             → Slice the scope, write the roadmap with traces
5. /product:stories-estimate → Size the stories with the team
6. /product:checks-declare   → Declare the check of each criterion
7. /product:specifying-stories → One Feature becomes relay-ready spec files
8. /product:work             → One agent takes one ready item
9. /product:roadmap-sync     → GitHub, drift, and evidence
    └─→ /product:review        → Drift only, with no GitHub Project
```

## File structure

```
plugins/product/
├── agents/
│   ├── prd-analyst.md             # Product-hat Socratic agent (Opus)
│   ├── prd-simulator.md           # Developer-view gap analysis
│   └── roadmap-analyst.md         # Roadmap planning agent (trace-aware)
├── schema/
│   ├── product.yaml               # The LinkML schema of both bundles
│   └── product.schema.json        # Generated from it by linkml 1.11.1
├── scripts/
│   ├── prd.py                     # The one command
│   ├── prdlib/                    # Its modules, github* for the round trip
│   ├── github_probe.py            # Answers the five GitHub questions (D37)
│   └── gen-schema.sh              # Writes product.schema.json
├── skills/
│   ├── shared/
│   │   ├── bundle-schema.md       # Layout, page format, IDs, links, write rule
│   │   ├── product-hat.md         # Product-level guardrail and deflection
│   │   └── roadmap-model.md       # Types, states, status tables
│   ├── google-style/SKILL.md      # Writing style (vendored)
│   ├── explore/SKILL.md           # Lens-driven exploration
│   ├── save/SKILL.md              # PRD bundle writer
│   ├── simulate/SKILL.md          # Implementation simulation
│   ├── simulate/assessor.md       # The assessor role of simulate
│   ├── migrate/SKILL.md           # v3 files to the two bundles
│   ├── plan/SKILL.md              # Roadmap generator
│   ├── themes-identify/SKILL.md   # Capabilities into epics
│   ├── features-identify/SKILL.md # Epic into features
│   ├── stories-identify/SKILL.md  # Feature into stories
│   ├── tasks-identify/SKILL.md    # Story into tasks
│   ├── stories-estimate/SKILL.md  # T-shirt sizing
│   ├── checks-declare/SKILL.md    # The check of each criterion
│   ├── work/SKILL.md              # The agent protocol for one item
│   ├── review/SKILL.md            # A person reviews each drifted trace
│   ├── specifying-stories/SKILL.md # One Feature into relay-ready specs
│   └── roadmap-sync/
│       ├── SKILL.md               # GitHub, drift, evidence
│       └── references/sync-sources.md
├── tests/                         # The pytest suite, run by the job product in CI
├── .claude-plugin/plugin.json     # Plugin metadata
├── SKILL.md                       # Plugin manifest
└── README.md                      # This file
```

## Writing style

Each skill and each agent that writes PRD or roadmap text reads
`skills/google-style/SKILL.md` first, and follows the
[Google developer documentation style guide](https://developers.google.com/style).
The rules for page text are in "Writing style" in
`skills/shared/bundle-schema.md`. They cover the text that a migration writes.
An ID, a link, a hash, a frontmatter key, a frontmatter value, and a generated
block never change for style. A skill restyles only the text it writes or
changes, because a restyled requirement gets a new hash and flags each item
that traces it.

**Provenance**: `skills/google-style/SKILL.md` is vendored from
a private repository of the author, commit `e799832`
(2026-09-01). The body is a verbatim copy. The `description` is adapted: it
limits the skill to PRD and roadmap text, so the skill does not load for all
prose in a repository that installs this plugin. The source repository is
private, so `.claude/upstreams.json` does not list it. To refresh the copy,
compare both files by hand.

## Breaking changes in v4.0.0

- **The PRD and the roadmap are directories.**
  `/product:migrate` turns `docs/product/prd.md` into the bundle `docs/product/prd/`,
  and `docs/product/roadmap.md` into `docs/product/roadmap/`. The v3 files move
  to `docs/product/archive/`. Each other skill stops when it finds a v3 file
  and no `docs/product/prd/index.md`, and recommends `/product:migrate`.
- **One status per item becomes two fields.** `status` is the page lifecycle
  (`draft`, `stable`, `deprecated`). `state` is the work status. The v3
  statuses map as: `Not Started` → `ready` or `blocked`, `In Progress` →
  `in_progress`, `Completed` → `done`, and `Needs Review` → a `drifted` field
  that is not empty.
- **`prd.py` does each write.** A skill calls `new`, `state`, `regen`, and
  `check`. It does not choose an ID, and it does not write an index or a status
  table.
- **New skills**: `/product:migrate`, `/product:tasks-identify`, `/product:checks-declare`,
  and `/product:work`.
- **`/product:roadmap-sync` is the GitHub round trip.** It drives
  `prd.py github pull`, `plan`, and `apply` against a GitHub Project, and it
  asks you before each apply. The v3 skill read issues and PRs only.
- **The arc plugin reads the v3 paths.** It stops reading the PRD of a
  repository that migrates, until its own change lands. arc is in another
  repository.

## Plugin dependencies

Two skills of this plugin call another plugin:

- `/product:specifying-stories` needs the **superpowers** plugin. It copies the
  design-doc shape and the self-review list of the `brainstorming` skill.
  `scripts/check-superpowers.sh` is the probe, and the skill stops when the
  plugin is absent.
- `/product:work` needs the **relay** plugin at version 5.0.0 or later for a spec
  with `kind: build`. It calls `/relay:implement --spec`.
  `scripts/check-relay.sh` is the probe, and it holds the version floor.

Both probes call `scripts/check-plugin.sh`, which holds the candidate search:
the home root, then the plugin cache. A candidate passes only when its
`plugin.json` names the plugin. Each probe holds its own probe file, its
version floor, and its install message.

`/product:specifying-stories` also uses other plugins that do not stop it:

- The **architecture** plugin, for `architecture:ask` to read the ADR register and `architecture:learn`
  to record a decision. Without an ADR corpus, the skill notes "no ADR
  corpus" and goes on.
- The `relay:scout` agent, for a summary of the code. Without relay, the
  skill runs a short sweep with `find` and `grep` instead.

Every other skill of this plugin needs no other plugin.

## Limits of the script

- `prd.py` writes a page again from its values. It does not keep a comment in
  the frontmatter, and it does not keep the original quoting. Each value stays
  the same. The page format has no comment in the frontmatter, so no valid page
  loses text.
- `prd.py` rewrites the frontmatter of a page. It does not rewrite the body.
- The write lock covers one working tree. Between clones, git is the check: two
  writers change the same lines, so the second push gets a conflict.
- The GitHub probe has not run (D37). Until it does, each of the five open
  answers takes the safe path.

## License

Apache-2.0. See the LICENSE file at the root of the repository.

---

**Ready to make your PRD?** Start with `/product:explore`
