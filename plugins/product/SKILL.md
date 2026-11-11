# PRD Analysis

Product-level PRD creation and roadmap planning through lens-driven Socratic
exploration, with full traceability from the PRD to the roadmap and to GitHub.

## Features

- **Two OKF bundles** — `docs/product/prd/` holds the PRD and
  `docs/product/roadmap/` holds the roadmap. One page holds one requirement or
  one work item. Each relationship is a typed field.
- **Lens-driven exploration** — an ordered lens spine: Problem → Personas →
  Journeys → Capabilities → Scope → Success metrics, and the satellites
  Business model, Go-to-market, Risks, and Experience.
- **The product hat** — each skill stays at the product level. An
  implementation ask becomes a product constraint.
- **Traceability** — a roadmap item holds a `traces` entry: the ID of a PRD
  page and the hash of its text.
- **Drift detection** — when a requirement changes, its hash changes, and
  `prd.py drift` lists each item that traces it.
- **One script** — `prd.py` writes each page, each ID, each index, each status
  table, and each log line. A skill never writes an ID or a table itself,
  because a hand-chosen ID can collide and `prd.py regen` overwrites a hand
  edit of a table.
- **The GitHub round trip** — `prd.py github plan`, `github apply`, and
  `github pull` sync the roadmap bundle with a GitHub Project.
- **The agent layer** — a lease holds one work item, a declared check tests one
  acceptance criterion, and one Run page records one agent execution.

## Skills

### PRD creation

### `/product:setup`
Makes the two bundles when they are absent and adds a router block to the
repo `CLAUDE.md` that points at them. Run it again to refresh the block.

**Use when**: You start the PRD in a repository, or the `CLAUDE.md` pointer is
missing.

### `/product:explore [lens]`
Lens-driven Socratic exploration. Give a lens (`problem`, `personas`,
`journeys`, `capabilities`, `scope`, `success-metrics`, `business-model`,
`go-to-market`, `risks-assumptions`, `experience`), or get a menu that recommends the next lens. It makes
the two bundles with `prd.py init` on the first run.

**Use when**: You find or deepen the product requirements.

### `/product:learn [lens]`
Write the findings of the session into the PRD bundle. It makes one page for
each finding with `prd.py new`, stores the relationships, updates the product
summary, runs the drift check, and adds the log line.

**Use when**: An exploration or a simulation gave findings to keep.

### `/product:simulate [capability | --all] [--decide autonomously|interactively]`
Simulate the implementation of one capability from the view of a developer. It
shows the gaps and the decisions that no page holds. By default, an assessor
agent picks the answer of each small gap, and you accept those picks in one
reply at the end. You answer only the gaps that need you.

**Use when**: The spine is explored and you want to test the PRD.

### `/product:migrate [map-file]`
Turn a v3 `docs/product/prd.md` and `roadmap.md` into the two bundles. It scans
the v3 files, takes a type map from you, builds the tree in a temporary
directory, tests five properties on it, and only then moves it. No ID and no
trace is lost. Run it one time, before any other skill.

**Use when**: The repository holds the v3 files.

### Roadmap planning

### `/product:plan [scope]`
Make the roadmap from the PRD. It asks how to slice the scope (MVP, one phase,
the full product), writes one Milestone page for each phase, drives the three
identify skills, and promotes the items of the chosen slice from `backlog`.

**Use when**: The PRD is ready and you want a roadmap.

### `/product:themes-identify [milestone]`
Group the features of a milestone into epics.

### `/product:features-identify [epic-or-milestone]`
Divide an epic or a milestone into features. Each feature traces its PRD pages.

### `/product:stories-identify [feature]`
Divide a feature into stories, each with its acceptance criteria.

### `/product:tasks-identify [story]`
Divide one story into engineering tasks, with an engineer persona.

### `/product:stories-estimate [feature]`
T-shirt sizing (S, M, L), one story at a time, with the team.

### `/product:roadmap-sync`
Three parts in one run: the GitHub round trip (`github pull`, `github plan`,
`github apply`), the requirement drift check, and the evidence scan for each
item that GitHub does not hold. It asks you before each apply. Its drift part
is `/product:review`.

### `/product:review [ID...]`
Review each roadmap item whose traced requirement changed. It shows the text of
the last accept from Git and a diff to now, groups the traces that one change
caused, and accepts a drift only when you say the item is still correct. It
needs no GitHub Project and no network.

### `/product:google-style`
The writing style for the text of a PRD page and a roadmap page, from the
Google developer documentation style guide. Each skill and each agent that
writes document text reads it first.

### The agent layer

### `/product:specifying-stories [FEATURE-ID]`
Turn one Feature and its Stories into one spec file or more in
`docs/superpowers/specs/` that `/relay:implement --spec` accepts. It writes the
path of the spec in the `spec` field of each covered Story and sets those
Stories to `ready`, on a `spec/<FEATURE-ID>` branch. Needs the superpowers
plugin. README.md holds the full entry.

**Use when**: A Feature has Stories and you want a person to decide how they
are built.

### `/product:checks-declare [story]`
Record the check of each acceptance criterion of one story. A check is an argv
list that `prd.py run-checks` runs. Only a person declares one, because a check
runs code on the machine of the user.

**Use when**: A story has criteria and you want a machine to test them.

### `/product:work [ID]`
The protocol for one agent and one roadmap item: claim it, read the item and
its links only, do the work, run the checks, and give the item back for review.
A person, or an agent with a recorded approval (`--approved-by`), sets `done`.

**Use when**: An agent takes one ready item off the roadmap.

## Conventions and specifications

The bundle layout, the page format, the IDs, the relationships, and the write
rule are in `skills/shared/bundle-schema.md`. The roadmap types, the states, the
relationships, and the status tables are in `skills/shared/roadmap-model.md`.
The product-level guardrail is in `skills/shared/product-hat.md`. The writing
style is `skills/google-style/SKILL.md`, and its application to bundle text is
in "Writing style" in `skills/shared/bundle-schema.md`. The schema
`schema/product.yaml` is the source of each type and each closed list. The full
workflow narrative is in `README.md`.
