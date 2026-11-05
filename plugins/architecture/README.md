# Architecture

Scaffolds an architecture-decision-record (ADR) corpus into any repository, captures a decision
the moment it is made, and answers questions about past decisions from it. An ADR corpus here is a
flat directory of frontmatter files plus a generated register, kept structurally consistent by a
standard-library-only vendored toolchain and a pytest suite.

**The reference corpus is synthetic.** It is in `tests/parity/`. It holds each ADR graph and
register convention that the plugin supports, and the register and check output that it must make.

## The bar

**Record a decision when it would be expensive to undo.** Cheap to change your mind, no ADR.
This one test governs capture, recall, grooming, and review alike.

| Earns an ADR | Does not |
|---|---|
| Chose Postgres over DynamoDB | Picked a retry count of 3 |
| Put auth at the gateway, not per service | Named a helper function |
| An event shape other services now consume | Chose a lodash utility |

## Commands and skills

Seven skills, four commands. Capture and recall fire on their own, mid-session; setup is typed but
never fires on its own either; the rest are invoked by a human.

- **`/architecture:setup`** — bootstrap. Detects any prior corpus, offers greenfield, adopt, or migrate,
  confirms once, then writes the corpus, `.claude/adr.json`, and both CLAUDE.md rule blocks.
  Adoption writes only `.claude/adr.json` unless `--gate-deterministic` is requested. Ends only
  when the register indexes clean and the lint reports zero errors. Then it adds a short router
  block to the repo `CLAUDE.md` -- where the corpus is, which file to read first, and the two
  commands to use -- between `<!-- adr:router start/end -->` markers, on every path: fresh,
  adopt, and a corpus that is already configured. A migrate mode moves the lifecycle, re-copies
  the CI scripts, and deletes `docs/adr/CLAUDE.md`, each only after a yes. Backed by the `setup`
  skill (`disable-model-invocation: true`) and `scripts/scaffold.py`.
- **`/architecture:learn`** — capture. Writes one ADR with `lifecycle: accepted` and `status: stable` for a
  decision that is expensive to undo. Backed by the `architecture:learn` skill, which also fires on its own during a
  session, mid-flow, without stopping to ask. Applies the distillation standard from
  `skills/learn/distillation.md`.
- **`/architecture:ask`** — recall. Answers a question from the corpus with `path:line` citations. Backed
  by the `architecture:ask` skill, which is read-only by construction — its tool list holds only
  `Read, Grep, Glob, AskUserQuestion, Skill`, and none of them can change a file — and reads `index.md` first, or the register when that file does not
  exist, before it opens any single ADR.
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
`set`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, and `log`. It imports `adr_lib.py`,
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

`/architecture:ask` reads `index.md` first when the file exists, and the register when it does
not. To stop navigation, delete the 3 files.

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
8. `architecture:ask` is read-only. It reads the generated index before any ADR, or the register when no index exists.
9. **Commands set `disable-model-invocation: true`. Skills never do, except `setup`.** Commands
   are user-typed; most skills are what a session reaches for on its own, but `setup` is
   user-typed only.
10. Setup never rewrites an existing ADR unless migration was chosen explicitly. `/architecture:setup`
    writes nothing if any manifest target already exists, with four idempotent exceptions: the
    repo `CLAUDE.md` append, `<dir>/CLAUDE.md`, the vendored tree, and the register.
