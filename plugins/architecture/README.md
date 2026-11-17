# Architecture

Discover architecture choices, record accepted decisions, and return when requirements change.
The plugin also creates an architecture-decision-record (ADR) corpus and answers questions about
past decisions. An ADR corpus here is a
flat directory of frontmatter files plus a generated register, kept structurally consistent by a
standard-library-only vendored toolchain and a pytest suite.

**The reference corpus is synthetic.** It is in `tests/parity/`. It holds each ADR graph and
register convention that the plugin supports, and the register and check output that it must make.

`ask` requires knowledge 2.0.0 or later. A single known read query, including
`regen --check`, leaves the brain hook without regeneration or checks. Writes
retain regeneration and both checks. Compound commands retain the write-check path.

## The bar

**Record a decision when it would be expensive to undo.** Cheap to change your mind, no ADR.
This one test governs capture, recall, grooming, and review alike.

| Earns an ADR | Does not |
|---|---|
| Chose Postgres over DynamoDB | Picked a retry count of 3 |
| Put auth at the gateway, not per service | Named a helper function |
| An event shape other services now consume | Chose a lodash utility |

## Commands and skills

Nine skills, four commands. Capture and recall can start during a session. Setup is user-invoked.
Explorer guides discovery; its `saving-deferred` helper runs only after approval to save a group
of open findings.

- **`/architecture:setup`** — bootstrap. Detects any prior corpus, offers greenfield, adopt, or migrate,
  confirms once, then writes the corpus, `.claude/adr.json`, and both CLAUDE.md rule blocks.
  Adoption writes only `.claude/adr.json` unless `--gate-deterministic` is requested. Ends only
  when the register indexes clean and the lint reports zero errors. Then it adds a short router
  block to the repo `CLAUDE.md` -- where the corpus is, which file to read first, and the two
  commands to use -- between `<!-- adr:router start/end -->` markers, on every path: fresh,
  adopt, and a corpus that is already configured. A migrate mode moves the lifecycle, re-copies
  the CI scripts, and deletes `docs/adr/CLAUDE.md`, each only after a yes. Backed by the `setup`
  skill (`disable-model-invocation: true`) and `scripts/scaffold.py`.
- **`/architecture:explore`** — guided discovery. Review evidence, choose architecture areas,
  record confirmed choices, check required-area coverage, and continue when requirements change.
- `saving-deferred` — internal forked skill. Saves only an approved group through `knowledge:learn`
  and reports saved paths or unsaved findings. It has no user command.
- **`/architecture:learn`** — capture. Writes one ADR with `lifecycle: accepted` and `status: stable` for a
  decision that is expensive to undo. Backed by the `architecture:learn` skill, which also fires on its own during a
  session, mid-flow, without stopping to ask. Applies the distillation standard from
  `skills/learn/distillation.md`.
- **`/architecture:ask`** — recall. Answers a question from the corpus with `path:line` citations. Backed
  by the read-only `architecture:ask` skill. Normal questions use `knowledge:ask` first, then source lifecycle and history checks. Exact sets and legacy corpora use the index or register path. Requires knowledge 2.0.0 or later.
- **`/architecture:index`** — regenerate the register and lint the corpus. Backed by the `indexing-adrs`
  skill, which never reports success on a red lint and never hand-edits between the generated
  markers.
- `amending-adrs` — no command of its own. Fires on its own, or from `architecture:learn`, when a
  recorded decision changes: rewrites in place, deprecates, or supersedes with both back-links set.
- **`/architecture:migrate`** — convert a legacy bold-key corpus to frontmatter with `adr_migrate.py`.
  `--frontmatter` (the default) folds bold keys and touches no filename; `--rename` also
  normalises `ADR-002-slug.md` to `0002-slug.md` and carries the register's hand-authored summary
  to the new key, because renaming changes every link that points at the file. A reference the
  converter cannot resolve to a real file is left for the lint to report, never guessed. Backed by
  `setup`'s migrate mode, which adopts first, then converts, and stages every
  change for review — it commits nothing.

  `--descriptions` is a third mode: it drafts the missing `description` values. It
  prints the plan and writes nothing; `--apply` writes. For each ADR with no
  `description`, it inserts one line below `title:` with the text that the generator
  would derive, and it marks the line `# draft`. The lint reports a `# draft` value as
  `description-missing`, so a person reviews each draft and removes the comment. The
  mode stops with exit 2 when the active schema has no `description` property.
- **`/architecture:check`** — the gate's model tier. Reads the diff between the current branch and its
  default branch, reports whether it contradicts an accepted ADR or ships a hard-to-reverse change
  with no ADR, and **always exits 0** — findings are advisory, and the deterministic tier is what
  the gate blocks on. Backed by the read-only `reviewing-adr-adherence` skill.
- **`/architecture:groom`** — merge overlapping ADRs, retire what reality outgrew, compress prose in place,
  or archive the dead. **Always proposes a plan and shows a diff first; never rewrites silently.**
  Archiving sets `archive_dir` in `.claude/adr.json` and repairs every inbound link, including the
  register's own keys, before the next regeneration. Backed by the `grooming-adrs` skill, invoked
  by a human — it rewrites a corpus, so it does not fire on its own.

**Commands carry `disable-model-invocation: true`. Skills do not, with one exception: `setup`.**
Commands are what a human types. Most skills are what a session reaches for on its own — this
split is the mechanism that makes the plugin engage without being asked. `setup` is user-typed
only, so it carries `disable-model-invocation: true` too, even though it has no command of its own.

## Architecture discovery

Use `/architecture:explore` to start from scratch, organization guidance, or an existing
application. No prior architecture or product requirements document (PRD) is required.
Explorer reviews available sources first, then asks one question at a time with options,
advantages, disadvantages, and a recommendation. You choose the next area. Ask for an
explanation or an example when you need one.

Explorer covers eight areas: `quality`, `context`, `strategy`, `building-blocks`, `data`,
`contracts`, `conventions`, and `deployment`. It uses an existing assessment report or
examines application code. It asks you to confirm each inferred choice. Permission to
adopt external ADRs without individual questions applies only to those ADRs, not to
choices inferred from code or documents.

Accepted choices go to `architecture:learn`. Rejected choices create no ADR. Deferred
or uncertain choices stay open, and existing proposed ADRs stay unchanged. Explorer
shows grouped deferred findings before it asks to save them through `knowledge:learn`.
Without that support, it continues and lists unsaved findings; it writes no substitute
file.

Select the areas required for the first build. Coverage counts only accepted ADRs with
an explicit `map_area`; the free-text `area` remains unchanged. Proposed, deprecated,
superseded, and deferred decisions do not count. Accepted decisions in every required
area establish the stopping point, not a claim that the entire architecture or every
checklist topic is complete. You can build or continue discovery while other areas stay
open.

The map refuses an unfinished accepted record instead of reporting coverage. A mapped
record needs written Decision content. Each other standard section present must also
contain content. Older records need not add missing standard headings. Comments and
empty headings or code blocks do not complete a section. The error names the record
and sections to complete; the map changes no file.

When a schema requires model facts or evidence, supply them in the same `new` call.
Use `--model-status`, optional `--model-element` and `--model-reason`, and repeated
`--evidence` options for dated measurements. Model details require a model status.
The complete candidate is checked before a mapped record is written.

The knowledge plugin is required to load Architecture. A missing knowledge graph or failed
save support does not stop the interview; Explorer reports setup steps and unsaved findings.
A missing knowledge plugin prevents the host from loading Architecture.

With a PRD, Explorer compares decisions with functional requirements after source review
and again at the end. Conflicts and unsupported requirements become questions; the PRD
stays unchanged. Without a PRD, Explorer says that this comparison did not run.

On return, Explorer uses accepted coverage and open choices. It reviews only accepted
decisions affected by changed evidence or requirements and asks before replacing them.
Unrelated decisions stay unchanged. If open choices were not saved, supply them again;
Explorer does not claim to recover missing session history.

## The optional gate

`templates/gate/adr-gate.yml` is a GitHub Actions workflow, offered at `/architecture:setup` and written by
`scaffold.py` only when asked for (`--gate-deterministic`, `--gate-model`). Two tiers:

- **Deterministic** — `adr_lint.py` and `adr_index.py --check`. Plain `python3`, standard library
  only, no install step, runs in any CI with no key. Scopes the "still `proposed`" check to the
  files the pull request actually changed, via `--changed`, so capturing a new decision never fails
  every PR on its own.
- **Model** — `claude -p "/architecture:check"`, run only when `secrets.ANTHROPIC_API_KEY` is present, with
  `continue-on-error: true` so a finding never fails the check.

## Format and graph

```
docs/adr/0007-order-state-machine.md
```

```yaml
---
type: adr
title: Order state machine
description: Orders move through a fixed state machine, not free-form flags.
area: orders
map_area: data             # optional shared coverage area
status: stable             # the OKF value: draft | stable | deprecated
lifecycle: accepted        # proposed | accepted | deprecated | superseded
date: 2026-08-13
supersedes: null
superseded_by: null
amends: []
amended_by: []
refines: []
deviates_from: []
related: []               # documentation links; not deterministic graph edges
parent_spec: null
evidence: []
model:
  status: modeled
  element: system.orders
generated:
  by: adr/0.5.0
  at: 2026-08-13T00:00:00Z
---
```

Required: `type`, `title`, `area`, `lifecycle`, and `date`. **The filename is the identity — there
is no `id` field.** `lifecycle` carries the ADR lifecycle value; `status` is the OKF value that
`lifecycle` maps to (`proposed` → `draft`, `accepted` → `stable`, `superseded` and `deprecated` →
`deprecated`). The two fields are always written together; only `lifecycle` is ever hand-edited.
The deterministic graph reads `supersedes` ⇔ `superseded_by` and `amends` ⇔
`amended_by`; both pairs are reciprocal and case-exact. A partial supersession keeps the old
record's status and uses a matching `# partial` inline comment on both relationship entries.
`refines`, `deviates_from`, and `related` are schema-valid context, not deterministic graph
edges.

The parser is read-tolerant: it also reads legacy bold-key metadata (`**Status:** Accepted`) so an
existing corpus adopts unmodified and lints clean on day one, flagged only as a warning. Writers
emit frontmatter only. Existing frontmatter is edited textually: changes preserve untouched keys,
their ordering, and inline comments.

## The save code and the hook

`scripts/adr.py` is the one script that writes a change to the corpus: `init`, `upgrade`, `new`,
`set`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, and `log`.
`map` reads coverage without writing files; `required-areas` saves an explicit required-area selection. It imports `adr_lib.py`,
`adr_index.py`, `adr_lint.py`, and `adr_migrate.py` from `templates/verbatim/scripts`, so it runs
the same code as the CI copy and the hook below. `upgrade` brings an old corpus to the brain
standard: it moves `status` to `lifecycle`, adds a `generated` stamp to each ADR that has none,
writes `log.md`, and writes `manifest.md`.

`hooks/brain-hook.sh` runs after a tool call that writes to the corpus. It runs three steps, in
this order: `adr.py regen`, `adr.py check`, then the general check of the `knowledge` plugin. A
warning shows as added context, and the tool call still succeeds. An error, or a failed step,
stops the tool call and shows the finding.

## Config — `.claude/adr.json`

```json
{
  "dir": "docs/adr",
  "register": {
    "path": "docs/adr/README.md",
    "exclude": []
  },
  "id_scheme": "sequential",
  "gate": {
    "deterministic": false,
    "model": false,
    "proposed_verdict": "error"
  },
  "archive_dir": "archive",
  "schema": null,
  "rules": null,
  "extra_corpora": []
}
```

`id_scheme` accepts `sequential` (four-digit zero-padded prefixes) or `date`
(`YYYY-MM-DD-slug.md`, for corpora that already use date names). The legacy string
form of `register` remains accepted, but canonical config uses `register.path` and
`register.exclude`. Excluded basenames stay in the graph but do not receive register rows.
`schema` can point to a repository-relative adopter schema; `rules` points to optional corpus
instructions; `extra_corpora` lists additional read-only decision corpora.

The optional `required_areas` list stores the areas selected for the first build. An absent
key means no selection has been made; `[]` means the person explicitly selected no required
areas. The list accepts only the eight area names, without duplicates. Coverage is computed,
not stored. No checklist state or deferred-choice pointers are added to this configuration.

The save-code commands use the plugin-owned script. Replace `PLUGIN_ROOT` and `REPO` with
the plugin and target repository folders:

```bash
$ uv run PLUGIN_ROOT/scripts/adr.py --root REPO map
$ uv run PLUGIN_ROOT/scripts/adr.py --root REPO required-areas --set quality data
$ uv run PLUGIN_ROOT/scripts/adr.py --root REPO required-areas --none
$ uv run PLUGIN_ROOT/scripts/adr.py --root REPO required-areas --clear
```

`map` returns JSON with `version`, `required_areas`, `ready`, `areas`, and `unmapped`.
`ready` means only that the selected required-area rule is met. It is false before selection
and true for an explicit empty selection. Each area lists the accepted ADRs that cover it.

Use `new --map-area AREA` for a confirmed new mapping, or `set ADR_FILE map_area=AREA`
for an existing frontmatter ADR. `map_area=null` clears a mapping. These writes refuse a
schema that does not support the field. Update a custom schema explicitly, or refresh an
opted-in shipped schema with `/architecture:setup --refresh`; no map read upgrades a corpus.

## Register contract

`/architecture:index` owns the marker-bounded region. It starts with the register's own warning
blockquote, carried through verbatim — including its absence — because that line names the
command a reader runs to regenerate the region, and that command belongs to whichever tool
owns the register. A register with no region yet gets this plugin's default. The region then
preserves existing `### <area> — <description>` headers and hand-authored summaries. Rows are sorted by date
then filename within each area; existing area order is retained and new areas are appended
alphabetically. The generator indexes **live ADRs only**; archive contents never receive a live
register row.

Rows have this shape:

```markdown
- [2026-08-13 — Order state machine](./2026-08-13-order-state-machine.md) — proposed — Hand summary
```

The status cell is content-detected, never configured. An empty register seed, or any existing
row with a status cell, emits cells; a non-empty cell-less register stays cell-less so existing
corpora round-trip byte-for-byte. A `superseded` record displays `superseded by` followed by file
links; a partial supersession displays its frontmatter status instead.

## Navigation files

`/architecture:index --nav` turns navigation on. Run it one time. It writes 3 generated files
beside the corpus, and a plain `/architecture:index` then keeps them current:

| File | Holds |
|---|---|
| `<dir>/index.md` | one line for each live ADR, grouped by area and by status |
| `<dir>/<archive_dir>/index.md` | the same form, for the archived ADRs |
| `<dir>/links.tsv` | one row for each relation, with 8 columns |

Each file starts from the generator. **Do not edit them.** `index.md` carries the key
`okf_version: "0.2"`, which is how every tool knows that the generator wrote the file.
An `index.md` that a person wrote, with no such key, stops `--nav` with exit 2 and
stays an ADR for the reader.

Each index line shows the ADR `description`. An ADR that has no `description` gets a
text that the generator derives from the first block of the `## Decision` section,
marked `(derived)`. The generator writes the `LINKS` block at the end of each ADR. Do not
edit it.

`/architecture:ask` uses the shared reader first for normal registered corpora. It uses the index
or register for exact sets and legacy corpora, and checks each selected ADR source and history.
To stop navigation, delete the 3 files.

## The schema pipeline

The shipped schema is generated, not hand-written:

```bash
cd plugins/architecture && ./scripts/gen-schema.sh
```

| File | Role |
|---|---|
| `schema/adr.yaml` | the LinkML source; edit this one |
| `scripts/gen-schema.sh` | runs LinkML and the flatten step |
| `scripts/flatten_schema.py` | reduces the LinkML output to the subset that the lint reads |
| `templates/verbatim/schemas/adr.schema.json` | generated, committed, vendored |
| `schema/adr.slots.json` | generated, committed, the slot vocabulary of the tests |
| `requirements-dev.txt` | the build and test pins: `linkml==1.11.1` and `pytest` |

LinkML is a build and test dependency only. Every vendored runtime script keeps to the
Python 3 standard library. A schema with a keyword outside the subset stops the lint
with exit 2 and the message `schema-unsupported: <keyword> at <path>`.

## New lint rules

8 rules join the rules of 0.2.0. A rule marked "gated" runs only when navigation is on.

| Rule | Level | Gated | Fires when |
|---|---|---|---|
| `description-length` | error | no | the `description` has more than 30 words, or a line break |
| `description-repeats-title` | warning | no | the `description` says the title again |
| `description-missing` | warning | yes | a changed ADR has no `description`, or its value is a draft |
| `index-drift` | error | yes | a generated index is not the generator output |
| `links-drift` | error | yes | `links.tsv` is stale or absent |
| `graph-cycle` | error | yes | a `superseded_by` chain comes back to itself |
| `target-missing` | warning | yes | a stored relation target does not exist |
| `yaml-shape` | error | yes | a list value has a YAML form that the parser reads wrongly |

## Runtime and optional gate

Every plugin skill executes the plugin-owned scripts from
`${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/`. Installing an updated plugin therefore updates
skill behavior immediately. Vendoring is opt-in: `/architecture:setup --gate-deterministic` copies a
standalone deterministic CI gate, while ordinary setup and adoption do not copy runtime tools.

| Destination | Origin |
|---|---|
| `scripts/adr/adr_lib.py`, `adr_new.py`, `adr_index.py`, `adr_lint.py`, `adr_migrate.py` | copied |
| `scripts/adr/requirements.txt` | copied (dev-only — `pytest`, never installed at runtime) |
| `schemas/adr/adr.schema.json` | copied |
| `tests/adr/conftest.py`, `test_adr_lib.py`, `test_adr_new.py`, `test_adr_index.py`, `test_adr_lint.py`, `test_adr_migrate.py` | copied |
| `<dir>/CLAUDE.md` | rendered (the corpus rule file) |
| `<dir>/README.md` | rendered (the register seed, empty markers) |
| `.claude/adr.json` | generated |
| `CLAUDE.md` (repo-root) | appended, never overwritten |

The table applies only to `--gate-deterministic`. Re-running `/architecture:setup --refresh` refreshes an
existing opted-in gate and its corpus `CLAUDE.md`, skips the root `CLAUDE.md` append when its
marker is already present, and touches no existing ADR.

## Parity check

`tests/test_parity_fixture.py` runs the deterministic checks on the synthetic corpus in
`tests/parity/repo`. It compares the generated register region with `tests/parity/expected-region.md`
and the check output with `tests/parity/expected-check.txt`. The plugin-side suite runs it, so each
test run is also the parity check.

## Testing

Plugin-side and vendored tests are two separate suites, run with two separate commands, because
both trees ship a `conftest.py` with the same basename — running pytest across both roots in one
invocation raises `ImportError` on the second `conftest.py` collected. Run them separately:

```bash
python3 -m pytest plugins/architecture/tests -q
cd plugins/architecture && python3 -m pytest templates/verbatim/tests -q
```

The vendored suite also runs, unmodified, inside a repo after `/architecture:setup`:

```bash
pip install -r scripts/adr/requirements.txt && python3 -m pytest tests/adr
```

### Live Explorer checks

Ordinary pytest runs exclude the `integration` marker. Live checks use separate fixture
projects and require an explicit opt-in.

Before you run the live commands, you must set `CLAUDE_JOB_DIR` to a fresh absolute local
directory. The fixture writes logs under `CLAUDE_JOB_DIR/tmp`. Keep these logs local; do not
commit them. Create the directory and run the checks in the same shell.

```bash
$ export CLAUDE_JOB_DIR="$(mktemp -d /tmp/architecture-explore.XXXXXX)"
$ ARCHITECTURE_ITEST=1 make -C plugins/architecture itest TIER=registration
$ ARCHITECTURE_ITEST=1 make -C plugins/architecture itest TIER=acceptance
$ ARCHITECTURE_ITEST=1 ARCHITECTURE_INTERACTIVE_BASH=1 make -C plugins/architecture itest TIER=interactive
```

Use `TIER=all` for all three groups, with both opt-ins. Registration runs before a behavior
series. Test sessions exclude inherited settings and refuse API-key use and overage.
Headless runs require actual rate events. The interactive group requires separate permission
to preapprove Bash in its synthetic fixture, while retaining `acceptEdits`. It uses its own
tmux server and checks the subscription and disabled extra usage before and after the save.
A missing or unclear billing observation stops the run. No user settings or shipped skill
permissions change. Offline helper tests check the harness without starting Claude.

## Invariants

1. The bar is the cost of undoing the decision. Every skill applies the same test.
2. **The filename is an ADR's identity.** No `id` field is ever written.
3. Writers emit YAML frontmatter only. Readers accept legacy bold-key as well.
4. **Vendored scripts import only the standard library.** The vendored scripts never import
   PyYAML.
5. **Hand-authored register summaries survive every regeneration.** The row key is the link href.
6. **Nothing moves on disk unless `/architecture:groom` is invoked.** On-disk layout is flat by default.
7. **Autonomous capture writes `lifecycle: accepted` and never interrupts.** The review of the pull
   request is the acceptance. Asking mid-session was rejected: it breaks flow, and in an unattended
   session nobody is there to answer. `proposed` is only for a decision that a person keeps open.
8. `architecture:ask` is read-only. It uses shared evidence first for normal questions, and keeps exact index or register queries and source history checks.
9. **Commands set `disable-model-invocation: true`. Skills never do, except `setup`.** Commands
   are user-typed; most skills are what a session reaches for on its own, but `setup` is
   user-typed only.
10. Setup never rewrites an existing ADR unless migration was chosen explicitly. `/architecture:setup`
    writes nothing if any manifest target already exists, with four idempotent exceptions: the
    repo `CLAUDE.md` append, `<dir>/CLAUDE.md`, the vendored tree, and the register.
