# Changelog

## 1.0.14

### Fixed
- The code, the tests and the verbatim templates have no old ruff F or E9 finding (STORY-431). 6 unused imports are removed, in `scripts/scaffold.py`, `tests/test_adr_py.py`, `tests/test_claude_md_router.py` and `templates/verbatim/tests/test_lifecycle.py`. The test `test_the_vendored_scripts_import_only_the_standard_library` in `templates/verbatim/tests/test_adr_lint.py` no longer builds the unused set `guarded`. No check of any test is weaker. The change to `templates/verbatim/` deletes 4 lines and adds none.
- A project with the deterministic gate (`--gate-deterministic`) gets this fix in its copy `tests/adr/test_adr_lint.py` only when `/architecture:setup --refresh` runs. No project has a copy of `test_lifecycle.py`, because `scaffold.py` does not copy it. The public export leaves out `templates/verbatim/tests/` until STORY-439.

## 1.0.13

### Changed
- The issue offer of `architecture:learn` shows the full issue body, asks a second question that says that `ai-advanced-futures/cc-plugins` is public, and opens the issue only after a yes to the second question (STORY-286). Before, it opened the issue after the first yes, which was to the offer and not to the text.

## 1.0.12

### Fixed
- `adr.py set` keeps a time as the text that you give. Before, it wrote `2026-11-09T19:00:00Z` as `2026-11-09 19:00:00+00:00` (STORY-276).

## 1.0.11

### Changed
- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 1.0.10

### Changed
- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 1.0.9

### Changed
- The text searches with `grep -n -E` through Bash, because Claude Code gives no Glob or Grep tool there. The macOS `grep` has no `-P`, so the patterns use `[[:blank:]]` for the tab of `links.tsv`. The text tells the model to write each `'` in a search term as `'\''`.

## 1.0.8

### Changed
- The tests and the docs name the job `architecture` of the CI workflow `.github/workflows/ci.yml`. One workflow replaces the workflow file of this plugin. The plugin behavior does not change.

## 1.0.7

### Fixed
- The hook runs its steps only when a Bash command runs `adr.py`. Before, a quoted text that held `(adr.py` (for example a page fact in a `knowledge.py walk` command) started the steps. The hook now removes each quoted span before it looks for the script. The hook also ignores a heredoc body and a `#` comment. The time of the check grows in line with the length of the command. A quoted script path, or a script path in a variable, does not start the hook.

## 1.0.6

### Changed
- The reference corpus is the synthetic corpus in `tests/parity/`. The README names no other repository.
- `scripts/parity.py` is gone. It compared the plugin with the TypeScript tool of one external repository. `tests/test_parity_fixture.py` checks the synthetic corpus on each test run.

## 1.0.5

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `architecture@cc-plugins`. The homepage and the repository fields point at the public repository, and the install line and the issue link name it. Install the plugins again from the new marketplace.

## 1.0.4

### Changed
- The schema `id` and prefix URLs name the public repository, `cc-plugins`.

## 1.0.3

### Changed
- The skill and command prompts are shorter. `/prompt:revise` measured them,
  and the instruction count went from 200 to 165. The findings went from 43
  to 0.
- Each "never" or "do not" rule that the prompt lint flagged now gives its
  reason in the same sentence.
- Fewer rules are stated in two files. For example, the `groom` and `index`
  commands no longer repeat the rules of their skills.
- The Grep patterns, the output sections, and the receipts are the same.

## 1.0.2

### Fixed
- The brain hook checks the session folder (the `cwd` of the hook input), not
  `CLAUDE_PROJECT_DIR`. A session in a worktree no longer gets a false error
  from the main checkout.
- The brain hook starts only for a Bash command that runs `adr.py`. A command
  that only names the script does nothing. A repository with no ADR graph
  does nothing, and no longer gets a false `K-registry` error.

## 1.0.1

### Changed
- The display name is now lowercase: `architecture`.

## 1.0.0

### Changed
- Moved to ai-advanced-futures/cc-plugins-library. Renamed from `adr` to
  `architecture`: the commands are now `/architecture:...`.
  They are `/architecture:check`, `/architecture:groom`, `/architecture:index`,
  and `/architecture:migrate`.
- Install the plugin with `claude plugin install architecture@cc-plugins-library`.
- The data names do not change: `.claude/adr.json`, `docs/adr/`, the graph
  `adr`, and the `<!-- adr:router start/end -->` markers stay.
- A new register region tells the reader to run `/architecture:index`.
  An existing region keeps its own text, so `/adr:index` stays in it.

## 0.5.0

### Changed
- The ADR corpus is an OKF bundle on the brain standard of the `knowledge`
  plugin: the register has frontmatter, the archive index has none,
  `docs/adr/CLAUDE.md` goes, and each ADR gets a `LINKS` block.
- The ADR lifecycle moves from `status` to `lifecycle`. `status` holds the
  OKF value. Run `/adr:migrate` on an existing corpus.
- `/adr:setup` and `scaffolding-adr-corpora` are now `adr:setup`.
  `/adr:new` and `authoring-adrs` are now `adr:learn`.
  `/adr:ask` and `consulting-decisions` are now `adr:ask`.
- `adr:learn` and `adr.py new` write a new ADR with `lifecycle: accepted`
  and `status: stable`. The review of the pull request is the acceptance.
  Pass `--lifecycle proposed` for a decision that a person keeps open.
- The hook reads the corpus folder from `.claude/adr.json` first, and from
  the registry only when `adr.json` has no `dir`.
- `adr_lint.py` uses the standard output contract and takes `--strict`.
  A `<graph>:/` target in `parent_spec` gives no warning.

### Added
- `scripts/adr.py`, the save code. The hook runs it, then the brain check,
  then the general check.

## 0.4.0

`/adr:setup` adds a router block to the repo `CLAUDE.md` on every path.

### Added

- `scripts/claude_md_router.py`: writes one block between `<!-- adr:router start -->` and
  `<!-- adr:router end -->` in `CLAUDE.md`. It replaces a marked block in place, appends when
  there is none, creates the file when it is absent, keeps a block that 0.3.0 wrote without
  markers, and changes no text outside the markers. A file with CRLF line endings keeps them.
- `scaffold.py --router-only`: writes only the router block, from `.claude/adr.json`. Step 7 runs
  this one command. When `<dir>/CLAUDE.md` does not exist (an adopted corpus), the block leaves out
  the line that links to it.
- `/adr:setup` Step 7: after both gates are green, it writes the block for an adopted corpus and
  for a corpus that is already configured. Before, only a fresh or `--refresh` run wrote it. The
  Step 4 confirmation says so and gives one way to decline; the receipt reports `written`,
  `unchanged`, `skipped (declined)`, `skipped (gate red)`, or `FAILED exit <n>`.

### Changed

- `scaffold.py` writes the root block between the same markers. The block text is the same as
  in 0.3.0. A broken marker pair in `CLAUDE.md` stops a fresh or `--refresh` run before it writes
  any file. `/adr:new`, `/adr:ask`, `/adr:index`, `/adr:check`, `/adr:groom`, and `/adr:migrate`
  are unchanged.

## 0.3.0

Graph navigation for the corpus, a generated schema, and one new front matter key.
Run `/adr:index --nav` one time to turn navigation on. A corpus that does not run it
behaves as it did in 0.2.0.

### Added

- `description`: one optional line of 30 words or fewer, below `title`. Write it in the
  words of the task. `/adr:new --description` writes it, and the authoring and amending
  skills ask for it. `adr_new.py --description` stops with exit 2 when the active schema
  does not have the property.
- `/adr:index --nav` writes 3 generated files: `<dir>/index.md`,
  `<dir>/<archive_dir>/index.md` and `<dir>/links.tsv`. A plain `/adr:index` then
  keeps them current. Delete the 3 files to stop navigation.
- `index.md` gives one line for each live ADR, grouped by area and by status, with the
  area list, the successor text, and the `description` or a text that the generator
  derives from the `## Decision` section and marks `(derived)`. The archive `index.md`
  gives one line for each archived ADR, with its successor text.
- `links.tsv` gives one row for each stored edge, with the resolved target, the target
  state, the target status, the two area columns and the `note` list. `/adr:ask` walks
  the graph from this file.
- `adr_index.py` reads a generated `index.md` as a generated file, not as an ADR. An
  `index.md` that the owner wrote has no `okf_version` key, so it stays an ADR.
- `adr_index.py` stops with exit 2 when an `index.md` is not a generated file, when the
  vendored scripts are older than the plugin, when an area slug is a reserved word, or
  when a file name holds a comma or a semicolon. It stops with exit 1 on a
  `superseded_by` cycle.
- `consulting-decisions` reads `index.md` first when it exists, walks one hop of the
  graph with 2 Grep patterns on `links.tsv`, follows a supersede chain to its end, and
  opens an ADR by section. It reads the register first only when no index exists.
  `resources/graph-walk.md` holds the `partial` rule, the `now=` rule and the
  set-question procedure.
- The answer names how it reached each record, gives each chain end, and states the
  status of each cited ADR. It never gives a proposed ADR as a decision in force.
- 8 lint rules: `description-length`, `description-repeats-title`,
  `description-missing`, `index-drift`, `links-drift`, `graph-cycle`,
  `target-missing` and `yaml-shape`. 6 of them run only when navigation is on.
  `description-missing` asks for a `description` on each ADR that the `--changed` list
  names. `yaml-shape` reports a list item that has the form of a mapping, and a flow
  list that holds a quote mark; the parser reads the two forms wrongly.
- The LinkML schema pipeline: `schema/adr.yaml` is the source, `scripts/gen-schema.sh`
  and `scripts/flatten_schema.py` generate `templates/verbatim/schemas/adr.schema.json`,
  and `requirements-dev.txt` pins `linkml==1.11.1`. Run `scripts/gen-schema.sh` after
  you change the source, and commit both outputs. LinkML is a build and test
  dependency; every vendored runtime script keeps to the standard library.
- `schema/adr.slots.json`, the slot vocabulary. A test keeps `KEY_ORDER`, `STATUSES`,
  `MODEL_STATUSES`, `LIST_KEYS`, `GRAPH_KEYS`, `RELATIONSHIP_KEYS`, `OBJECT_KEYS` and
  the new `RELATIONS` constant in agreement with it.
- `/adr:migrate --descriptions` drafts the missing `description` values. It prints the
  plan, and `--apply` writes one line marked `# draft` in each ADR.
- `scripts/measure_navigation.py`, a read-only measurement. It asks 10 deterministic
  questions on the `tests/nav` fixture and prints one Markdown table of byte counts.
- `.github/workflows/adr.yml` runs both pytest suites and the schema tests with
  `ADR_REQUIRE_LINKML=1`.
- Tests for each of the three `--changed` input forms: a path with the corpus prefix, a
  bare file name, and a file outside the corpus that has the file name of an ADR. The
  third form reports the ADR. This is a known limit: `--changed` compares file names
  only.
- The OKF profile record: the generated corpus passes the OKF checker when the
  register, the corpus rules file and the archive index are out. The 2 files that stay
  are recorded breaks.

### Changed

- `adr_index.py --check` also compares the 3 generated files with the generator output
  when navigation is on. It reports `navigation files up to date`.
- Greenfield setup and migrate setup run the generator, so the first lint reports no
  drift. The register seed is now the generator output.
- The shipped schema is generated. It gains `description`, and it loses the date-only
  patterns, `minLength` and `format`. A code check keeps the `evidence` finding.
- A schema with a keyword outside the supported subset stops the lint with exit 2 and
  the message `schema-unsupported: <keyword> at <path>`.
- `/adr:index` and `indexing-adrs` take `[--nav] [config path]`. `--nav` writes the
  navigation files one time, and a plain `/adr:index` keeps them current.
- The corpus rules say that `index.md`, `links.tsv` and the archive `index.md` are
  generated, and they ask for a `description` on each new ADR.
- The README gives the navigation surface, the schema pipeline and the measurement.

### Fixed

- A reciprocal pair between two sequential ADRs no longer reports `schema-type`: the
  5 relation keys lost their date-only pattern (DEF-1).
- The register round trip keeps a row whose status cell reads `unknown` (DEF-2). Before
  this release the row grew by one more cell on each `/adr:index` run, and the stale
  report never cleared.
- `adr_index.py --write` prints each dropped row and each unparsed row before the
  receipt line, and a `rows removed:` count, so a lost row is visible (DEF-3). The
  receipt line and the exit code do not change.
- The PyYAML sentence of the README says that the vendored scripts never import PyYAML.
  The old words said that PyYAML is optional, and no vendored script read it (DEF-5).
- The frontmatter writer keeps an unknown scalar key and an unknown list key. It writes
  them after the known keys, in source order. Before this release it dropped them. Only
  `id` is still dropped, because the file name is the identity.

## 0.2.0

- Ports the deterministic ADR graph and register contract of a reference corpus, including partial
  supersession, amendment reciprocity, case-exact reference resolution, exclusions, and
  content-detected status cells.
- Expands the adopter schema and preserves existing frontmatter text and inline comments.
- Carries an existing register's own warning blockquote through verbatim, so adopting a corpus
  never rewrites the line naming the command that regenerates its register.
- Runs skills from `${CLAUDE_PLUGIN_ROOT}` and vendors only an explicitly requested
  deterministic gate.
- Adds the synthetic parity corpus and a release check against a reference checkout.

## 0.1.0

- Deterministic spine: `adr_lib.py` (read-tolerant frontmatter and legacy bold-key parser,
  write-strict frontmatter writer, filename-derived identity, config plus Discovery), `adr_new.py`
  (sequential/date ID allocation, collision refusal), `adr_index.py` (register generation grouped
  by area, hand-authored-summary preservation across regeneration, `--write`/`--check`), and
  `adr_lint.py` (required fields, status enum, date parse, duplicate identity, cross-reference
  resolution, supersede pairing, register staleness, scoped `--changed proposed` check).
- `/adr:setup` and the `scaffolding-adr-corpora` skill: detect or create a corpus, offer
  greenfield/adopt/migrate, write the corpus, `.claude/adr.json`, the vendored tooling, and both
  CLAUDE.md rule blocks. Ends only when the register and lint gates are green.
- `plugins/adr/scripts/scaffold.py`, the deterministic write step behind setup, plus `--refresh`
  and `--adopt` modes.
- `plugins/adr/templates/`: both CLAUDE.md blocks, the ADR template bound to `adr_new.py`'s writer,
  and the register seed bound to `adr_index.py`'s markers.
- `/adr:new` and the `authoring-adrs` skill: writes one ADR with `status: proposed` for a decision
  that is expensive to undo, then keeps working -- it never stops to ask. Carries the bar's
  IN/OUT examples and the distillation standard (`skills/authoring-adrs/distillation.md`) with its
  four append tells.
- `/adr:ask` and the `consulting-decisions` skill: read-only recall (`Read, Grep, Glob` only) that
  reads the register first, cites `path:line`, and states plainly what the corpus does not cover.
- `amending-adrs`: rewrites a changed ADR in place, deprecates, or supersedes with both back-links
  set on a supersede, never a one-sided link.
- `/adr:index` and the `indexing-adrs` skill: regenerates the register, reports dropped and
  unparsed rows from the receipt, and never reports success on a red lint.
- `adr_migrate.py` and `/adr:migrate`: folds legacy bold-key headers into frontmatter
  (`--frontmatter`, the default), leaving every filename untouched, or additionally normalises
  `ADR-002-slug.md` to `0002-slug.md` (`--rename`) and carries the register's hand-authored
  summary to the new key. A supersede reference it cannot resolve to a real file is left for the
  lint to report, never guessed. Stages every change for review; commits nothing. Vendored through
  `scaffold.py`, and wired into `scaffolding-adr-corpora`'s migrate path (adopt, then convert).
- `reviewing-adr-adherence` and `/adr:check`: the gate's model tier. Reads the diff between the
  current branch and its default branch, reports whether it contradicts an accepted ADR or ships a
  hard-to-reverse change with no ADR, and always exits 0 -- findings are advisory, and the
  deterministic tier is what the gate blocks on.
- `templates/gate/adr-gate.yml`: an optional two-tier GitHub Actions gate, offered at `/adr:setup`
  and written by `scaffold.py` only when asked for. The deterministic job (`adr_lint.py`,
  `adr_index.py --check`) runs with no install step and no key, scoping the "still `proposed`"
  check to the pull request's own changed files. The model job runs `claude -p "/adr:check"` only
  when `secrets.ANTHROPIC_API_KEY` is present, and never fails the check on its own.
- `grooming-adrs` and `/adr:groom`: merges overlapping ADRs, retires what reality outgrew,
  compresses prose in place to the distillation standard, and archives the dead into
  `{{DIR}}/archive/`, setting `archive_dir` and repairing every inbound link -- including the
  register's own keys -- before the next regeneration. Always proposes a plan and shows a diff
  first; never rewrites silently.
- Registered in the marketplace.
