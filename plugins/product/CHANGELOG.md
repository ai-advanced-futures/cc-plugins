# Changelog

## 6.8.5

### Fixed
- The code and the tests of product have no old ruff F or E9 finding. `scripts/prdlib/runs.py` no longer imports `UsageError`, which it did not use, and the tests drop 9 unused imports. No behavior changes (STORY-430).

## 6.8.4

### Fixed
- `prd.py set`, `link` and `unlink` with `--actor agent:<id>` now write the page. Before, they exited 1, because the OKF stamp `generated.by` has no `agent:` form. Now `generated.by` is `prd/<version>`, and each such command adds 1 line to `log.md` that names the agent (`Set`, `Link` or `Unlink`). A person actor and no actor write the same stamp as before, and no line (STORY-24, D-024). Fixes #295.

## 6.8.3

### Fixed
- `check-plugin.sh`, which `check-relay.sh` and `check-superpowers.sh` call, finds a plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR/plugins` when the variable is set, else `~/.claude/plugins`. Before, `/product:specifying-stories` and `/product:work` reported relay or superpowers as missing in a session with another config folder. A relative value gives no candidate (STORY-295, the rule of STORY-281).

## 6.8.2

### Fixed
- `prd.py check` now fails with rule E2 for a `title`, `description`, `aliases` entry or `owner` that holds a line break or another control character. `prd.py new`, `set` and `link` refuse to write such a value. `generated.by` and `generated.at` follow the same rule. The body of a page keeps its line breaks.
- Before, a title with a line break passed `check`. `regen` then wrote its second line as a line of its own into the generated `index.md` and into the LINKS and STATUS blocks. A CR or NEL character also made `regen` unstable.
- The characters are each C0 control (LF, CR, VT, FF, ESC, tab), DEL, each C1 control (NEL, CSI), U+2028 and U+2029. The message names the first one as `U+XXXX`. To repair a page that now fails, replace the character with a space.
- `prd.py init` refuses a `--title` or `--description` with such a character. It writes nothing.
- `prd.py regen` and `regen --check` refuse a page that holds such a character in a value that `regen` copies into a generated file. They exit 1, print one line for each page with its path and the field, and write no generated file. Before, `regen` wrote the second line of a hand-edited title into the generated files, and no workflow runs `check`. The rule is the same function as E2, and it now holds each such value: `title`, `description`, `owner`, `state`, `blocked_by`, the `priority` of an `includes` or `traces` entry, `generated.by`, `generated.at`, each link of each field and the name of the field (these two go to `links.tsv`). The message says that the generated files are not updated and that a page change made before this step is kept: `set`, `link`, `unlink`, `remove`, `run-checks`, `init`, `upgrade` and `migrate --finish` write their own change first, then stop at this step on a hand-edited bad page. To repair, edit the field and run `prd.py regen`.
- A page whose file name, or the name of a folder above it, holds a line break or another control character is now refused. This is a visible change. `prd.py check` reports it as E2 ("the file name"), and `regen`, `regen --check`, `set`, `link`, `upgrade` and the other commands that call `regen` stop at the regen step. Before, `regen` copied the file name into each index, each STATUS row, each LINKS block and `links.tsv`, so a file named `FEATURE-02<LF>* [FORGED](x.md) - f.md` wrote a forged line into them, and `check` reported 0 errors. To repair, rename the file. The path in each message is still written with escapes. 5 tests of 6.8.1 (issue 1906) built such a file name and expected these commands to succeed; they now expect the refusal, with the path still escaped.
- `github pull --adopt` folds the title and the first line of an issue body into one line. Each such character becomes a space. A body with CR LF line ends no longer stops the adopt.
- `prd.py` now checks the `--actor` of each command that takes one: `set`, `link`, `unlink`, `remove`, `log`, `drift`, `state`, `claim`, `heartbeat`, `release`, `expire` and `run-checks`. It must be `human:<login>` or `agent:<id>` for the whole text. Before, `set`, `link`, `unlink`, `remove`, `log` and `drift --accept` took any text, and a line break in the actor wrote a second line into `log.md`. The pattern of the schema ends in `$`, which matches before a final line break. The new check does not.
- The change has three visible results. `process:<id>` is no longer an accepted `--actor` for those 6 commands. `drift --accept` with a `process:` actor or a malformed actor exits 2, not 1. An `agent:` actor still exits 1. An empty `--actor` exits 2.
- `prd.py log` still folds each run of whitespace in its text into one space, so a line break in the text never made a second line. It now also refuses a control character that the fold leaves, such as ESC.
- `log.md` has one writer, `logbook.append_entries`. It now writes each control character that is still in a line as an escape. A value from a file name or a snapshot cannot start a line of its own.
- `escape_controls` (6.8.1) now also writes U+2028 as `\u2028` and U+2029 as `\u2029`.

Fixes #1915 and #1928.

## 6.8.1

### Fixed
- A text of `prd.py` that prints a value that someone else wrote no longer lets that value forge a line or move the cursor. A line break, an ESC, another C0 control, DEL, or a C1 control (for example `0x9b`) in the value now prints as `\xNN`. Before, a page with a link value that held a line break gave an E4 finding of 2 lines, and the second line could read as a finding of another page. The same text came from `prd.py new`, `set` and `link` for a target that they refuse. The fix covers each text that prints a frontmatter value, a page name, a GitHub snapshot value, a YAML error, or a value that the caller gives: the findings of `check` (E1 to E6, E9, W8, and the page name of each finding), the errors of the commands, the lines of `prd.py github plan`, `apply` and `pull`, and the lists of `list`, `ready` and `stage`. One helper, `prdlib/textsafe.py`, writes the escape. A text that is a constant, a generated ID, or a member of a closed set is unchanged. The page body and the diff lines of `prd.py drift --show`, and the output of a declared check, are shown as they are, on purpose. A text with a clean value prints as before. Fixes #1906.

## 6.8.0

### Added
- `prd.py check` rule W9 (warning): a Story is in another milestone than its parent, or has no milestone while its parent has one. The parent can be a Feature or an Epic. A Task or a Feature gets no W9. A Story, a parent, or a parent `milestone` that is not a valid path gives no W9 and no note, because E2 reports that value and a line break in it would forge a line. The error of `prd.py new` for a parent milestone that cannot be copied writes each control character of the value as `\xNN`. With `--strict`, W9 gives exit 1, as each warning does. To clear it, run `prd.py set <STORY-ID> milestone=<the milestone of the parent>`, or give the Story a parent in its own milestone. The label of the whole-graph rule in a partial scan (`--bundle prd`) is now `W1-W9` (STORY-427).

### Changed
- `prd.py new Story` copies the `milestone` of its parent when the Story has a parent and no `milestone` (`--link milestone=` or `--set milestone=`). A parent with no milestone gives the Story none. A given `milestone` that differs from the milestone of the parent stays, and `new` writes 1 line `note: <ID>: ...` to stderr with the text of W9. The exit code is 0, and stdout holds the path only. When the milestone of the parent cannot be copied (its page does not exist, has another type, or has no valid path), `new` exits 1 and writes no page.
- `/product:stories-identify` no longer shows `--link milestone=` in its example command, and it tells that `prd.py new` copies the milestone of the feature. `skills/shared/roadmap-model.md` states the rule. A later change of the milestone of a parent does not change the milestone of its Stories.
- The Progress cell of a Milestone row counts each page whose `milestone` names it, so a new Story now counts there, as each Story on `main` already does.

## 6.7.1

### Fixed
- `prd.py github pull` no longer stops with `human:<app>[bot] is not an actor` when a GitHub App closed an issue or moved a card. A login that ends with `[bot]` is an agent, not a person: the Event line names `agent:<slug>-bot` (`example-app[bot]` gives `agent:example-app-bot`), and the issue (`#<n>`) is the approval of the change, as `product:roadmap-sync` already tells an agent. A cancel or a reopen by an App needs a hitl card or a D-id (DECISION-04), so the pull writes nothing for it and reports a conflict with the `prd.py state ... --approved-by` command. The same holds when the gh login of the session is the App.
- The GraphQL read of the closer asks for `__typename`. For an App, GraphQL gives `Bot` and the slug with no `[bot]`, so the reader adds `[bot]` (the form of REST). Before, an App closer reached the pull as a plain login.

## 6.7.0

### Changed
- `/product:specifying-stories` reads the Experience pages of a Feature and its Stories (Step 1 item 2b): the pages that describe a Capability or a Journey that they trace, and the pages that they trace directly, with no deprecated page. Each kept page is a Decisions row with the source `EXPERIENCE-<NN>` and the treatment "Inherit", the "UI surface" area of the Design section names it with its `kind` and its title, and a spec choice against it is a conflict row. A product with no Experience page gets the same spec as before (STORY-243).

## 6.6.0

### Added
- The experience lens (`/product:explore experience`), a satellite lens for a product with a user interface. It opens when both Journeys and Capabilities are met. Its first question asks if the product has a user interface whose look and behavior matter to the outcome. On "no", the finding is one Decision page "The product needs no experience lens" and the lens is `complete`. The six spine lenses still make the PRD ready for planning (STORY-242).
- The lens guide "Experience (satellite)": one question set for each `kind` (`structure`, `state-rule`, `interaction-rule`), and the rule "1 fact, 1 page" that sends a flow to a Journey page, an unusual situation to a Capability page, and an accessibility level to a Constraint page.
- `/product:learn` writes an Experience page with its `kind` and one or more `describes` targets. A finding of the experience lens with no `describes` target is not written.

### Changed
- The product hat keeps design tokens and design-system component names out of the PRD. `/product:learn` takes them out of a finding and keeps the rest of the finding. They go to a `Convention` page of the system design.

## 6.5.0

### Added
- The page type `Experience` in the PRD bundle (`prd/experiences/`, prefix `EXPERIENCE`). It holds a screen structure, a state rule, or an interaction rule, with a `kind` of `structure`, `state-rule` or `interaction-rule`. The required link `describes` (inverse "described by") points to a Capability or a Journey. A Story can trace an Experience page, and drift covers it (STORY-241).
- The optional key `hash` of a `sources` entry: 6 hex characters, the form of `Trace.hash`.
- `tests/fixtures/ui_product.py`: a builder of a made-up product with a user interface, for the tests of later stories.

### Changed
- `prd.py new`, `set` and `link` refuse a link target that does not exist or that has a type that the field refuses, before they write a file or take an ID. Before, only `prd.py check` found it, after the write. Each type has this rule.
- The first page of a new folder in a bundle with a `manifest.md` writes the manifest again with the new `id_folders`, and `regen --check` and `check` name a manifest that lacks a folder that holds a page (rule E10). Before, only `prd.py upgrade` did it.

## 6.4.7

### Changed
- The issue offer of `product:learn` shows the full issue body, asks a second question that says that `ai-advanced-futures/cc-plugins` is public, and opens the issue only after a yes to the second question (STORY-286). Before, it opened the issue after the first yes, which was to the offer and not to the text.

## 6.4.6

### Fixed
- `set` and `new --set` keep a date or a time as the text that you give. Before, `set` refused each date, also in a date field such as `target_date`, and `new --set` wrote a time such as `2026-11-09T19:00:00Z` as `2026-11-09T19:00:00+00:00` (STORY-276).

## 6.4.5

### Changed
- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 6.4.4

### Changed
- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).
- The same holds for the finder of `relay` and `superpowers` in `check-plugin.sh`.

## 6.4.3

### Changed
- The text lists files with `find` and searches with `grep` through Bash, because Claude Code gives no Glob or Grep tool there.

## 6.4.2

### Changed
- The tests and the docs name the job `product` of the CI workflow `.github/workflows/ci.yml`. One workflow replaces the workflow file of this plugin. The plugin behavior does not change.

## 6.4.1

### Fixed
- The hook runs its steps only when a Bash command runs `prd.py`. Before, a quoted page fact that held `(prd.py github pull` (in a `knowledge.py walk` command) started `prd.py regen`, and `regen` changed the field order of some roadmap pages. The hook now removes each quoted span before it looks for the script. The hook also ignores a heredoc body and a `#` comment. The time of the check grows in line with the length of the command. A quoted script path, or a script path in a variable, does not start the hook.

## 6.4.0

### Added
- The `released` state. It follows `done` and it is a closed state. `prd.py check`
  accepts it on each work item, and `prd.py state <ID> released` sets it. The
  schema and the roadmap model list it. A bundle with a `released` page needs
  product 6.4.0 or later, because an older `prd.py check` gives E2 for it.
- A `released` item counts as delivered: a blocker that is `released` does not
  block, a `released` child counts in the Progress cell, a `released` item makes
  its capability mature, and W4 also warns on a `released` parent with an open
  child. `actual_end_date` is set at the change from an open state to `done` or
  `released`, and a change between the two keeps it.
- The GitHub sync: a `released` item closes its issue as completed, and the
  Status field has a `Released` option (nine options, one for each state). A
  closed issue keeps a `released` page `released`, and a card in `Released`
  gives `released`.

## 6.3.0

### Added
- `prd.py state` takes `--approved-by <text>`. An `agent:` actor can now make
  each state change of an Epic, a Feature, a Story or a Task when the call gives
  an approval: a PR URL or `#<n>`, a D-id, an `ANSWER:<id>`, a hitl card link, or
  another URL. The script checks the shape of the text. The Event line names the
  approval: `by agent:x, approved by #12, at <time>`.
- A change to `cancelled`, and a reopen from `done` or `released`, need a hitl
  card link or a D-id.
- An agent sets a Story from `backlog` to `ready` or `blocked` only when the
  `spec` file of the Story is in the tree, below the root folder.

### Changed
- Five agent changes need no approval: `ready -> claimed`,
  `claimed -> in_progress`, `in_progress -> in_review`, `claimed -> ready` and
  `in_progress -> ready`. Each other agent change with no `--approved-by` exits
  with code 1. The list `AGENT_TRANSITIONS` is now `FREE_AGENT_MOVES`.
- `/product:work`, `/product:plan`, `/product:specifying-stories`,
  `/product:roadmap-sync` and the roadmap model describe the agent changes.

## 6.2.3

### Changed
- The schema names the Apache-2.0 license, the license of the repository. It named MIT before. The google-style skill states that it paraphrases the Google developer documentation style guide under CC BY 4.0, with changes.

## 6.2.2

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `product@cc-plugins`. The homepage and the repository fields point at the public repository, and the install line and the issue link name it. Install the plugins again from the new marketplace.

## 6.2.1

### Changed
- The README provenance of `google-style`, the CHANGELOG, and the README license line name no private repository. The license is Apache-2.0, as the root LICENSE says.

## 6.2.0

### Fixed
- The roadmap sync keeps the title and the body of an issue that a person
  wrote. A bound page has `github.number`, no `pushed_hash`, and an issue with
  no OKF marker. `github plan` sends nothing to it until you give
  `--keep <ID>`. An edit of the page sends nothing.
- `github apply` stores no hash when an update sends no title or body.

### Added
- `github pull` reports each bound page in a `BOUND:` line (JSON key `bound`).
  `/product:roadmap-sync` asks which bound issues get the bundle text. The
  default is none.
- `github pull --adopt` stores the hash of the values that the issue holds, so
  a person's edit after the adopt gives a `DIFFERENT:` line.

## 6.1.1

### Changed
- The skills, agents, and shared references of the product plugin have fewer
  and clearer instructions. `/prompt:revise` measured them against the prompt
  engineering principles of the prompt plugin. Each prohibition now gives its
  reason, and repeated or deletable text is removed.
- `/product:explore` and the prd-analyst agent stop a lens when the "done when"
  of the lens guide is met, when the last 2 answers gave no new finding, or
  when the user says to stop. "Diminishing returns" is now that test. The
  roadmap-analyst agent stops when each decision that the active skill needs
  has an answer, when the last 2 answers gave no new item, or when the user
  says to stop.
- The prd-simulator agent gives one pro and one con for each option, and marks
  a recommended option in `--decide interactively` mode only.
- "The write rule" in `shared/bundle-schema.md` holds the rule for a warning, a
  status table, and a hash one time. Six roadmap skills point to it in place of
  a copy.

## 6.1.0

### Changed
- `/product:simulate` asks fewer questions. By default (`--decide autonomously`),
  an assessor agent picks an option for each gap and gives it a level, a
  confidence, and a visibility. A table for the stage of the capability sends
  the gap to the owner now, or sets it aside. The owner accepts the set-aside
  picks in one reply at the end: `all`, or `all except 3, 7`.
  `--decide interactively` asks the owner about each gap that counts, as in
  6.0.1.
- `/product:simulate`: a gap counts only when a developer who builds the
  capability now must guess. A gap that only matters later goes to a Later
  list of the summary, and does not go to `/product:learn`.

### Added
- `/product:simulate --all` walks each capability and does not ask whether to
  go on.
- `prd.py stage [ID...]`: early or mature for each capability. A capability is
  mature when a work item in state `done` traces to it, directly or through
  its parent chain.

Ported from the private predecessor repository, pull request 207 (prd 5.1.0).

## 6.0.1

### Fixed
- The brain hook checks the session folder (the `cwd` of the hook input), not
  `CLAUDE_PROJECT_DIR`. A session in a worktree no longer gets a false
  "regen failed" error from the main checkout.
- The brain hook starts only for a Bash command that runs `prd.py`. A `grep`,
  a `sed`, or a PR text that names `prd.py` does nothing. A repository with no
  bundle does nothing.
- `prd.py init` prints each file that it writes, also the manifests,
  `links.tsv`, and `.claude/knowledge.json`.
- `prd.py check` ends with the summary line `N errors, M warnings`, as the
  brain standard says.
- `/product:setup` gives `--repo-root .` to the router script.

## 6.0.0

### Changed
- Moved to ai-advanced-futures/cc-plugins-library. Renamed from `prd` to
  `product`: the commands are now `/product:...`. Install the plugin with
  `claude plugin install product@cc-plugins-library`. The skills install names
  are now `product-<skill>` (for example `product-ask`). The data names do not
  change: `docs/product/prd/`, the graph `prd`, and the `<!-- prd:router -->`
  markers stay.

## 5.0.0

### Removed
- `prd:save`: use `prd:learn`. `prd:system-design` and `design_lint.py`: use
  the `system-design` plugin (`/system-design:learn`).

### Changed
- The two bundles are on the brain standard of the `knowledge` plugin: a
  manifest for each bundle, the registry entries `prd` and `roadmap`,
  `links.tsv`, `generated` on each page, and the OKF actor forms
  (`process:regen`, `process:github`). `prd.py state` still refuses a
  `process:` actor.
- `prd:specifying-stories` reads the `system-design` graph, and writes each
  new ADR with `lifecycle: accepted`: the review of the pull request is the
  acceptance.
- The page-size rule W1 moved to the general check (`K-size`).

### Added
- `prd:ask`, `prd:learn`, `prd.py set`, `link`, `unlink`, `remove`, `log`,
  and `upgrade`, and the hook that runs regen and both checks.

### skills/prd/ (the skills install)
- `prd-system-design` leaves the install, with no replacement there.
- `prd-learn` replaces `prd-save`. It saves through `prd-runtime`.
- The skills install now also has the knowledge skills (`skills/knowledge/`).
  `prd-learn` and `prd-setup` run both checks through `knowledge-checking`,
  and `prd-ask` uses `knowledge-ask`. The three skills stop with an install
  message when `knowledge-runtime` is missing.

## 4.5.5

### Fixed

- `prd.py github plan`, `apply`, and `pull`, and `github_probe.py`: a String
  or ID value goes to `gh api graphql` with `-f`, not `-F`. `gh` turns an
  all-digit value sent with `-F` into a number, so a Status option id such as
  `98236657` failed with
  "Variable $option of type String! was provided invalid value" and the
  apply stopped with the board partly written. The same fault broke an issue
  title of digits, a body that starts with `@` (`gh` reads a file for it),
  and a repository or owner name of digits. `-F` stays for the Int and
  Boolean values only (#197).

## 4.5.4

### Fixed

- `prd.py github pull`, `plan`, and `apply`: a short read of the Project
  items is refused. `gh project item-list` can exit 0 with fewer items than
  `totalCount`, for example under a GitHub rate limit, and the plan then
  added each issue to the Project a second time. The read now stops when it
  gets fewer items than the count, reads again when it gets 0 items, and
  stops when the Project holds more items than one read takes (#182).

## 4.5.3

### Fixed

- `prd.py github apply`: an issue that is already on the Project is done.
  A board workflow can put an issue on the Project before the run, and
  GitHub then refuses the add with "Content already exists in this
  project". The run stopped there and left the rest of the plan unpushed.
  It now reads the card the issue has and goes on (#188).

## 4.5.2

### Fixed

- `prd.py github pull`, `plan`, and `apply`: a repository of more than 100
  issues works. The issue read pages on `pageInfo { hasNextPage endCursor }`
  and joins the pages. A read with fewer issues than the count is refused.
  The labels, the issue types, and the milestones still refuse a full list
  (#175).

## 4.5.1

### Fixed

- `prd.py github pull`: the read of the milestone list failed with HTTP 422.
  `gh api` sends a POST when a call has a `-f` field and no method, and a POST
  to the milestone list makes a milestone. The call now names `--method GET`.
  No other `gh api` read in the plugin has this fault: the writes that use `-f`
  are meant to be POST requests.

## 4.5.0

### Changed

- `/prd:review` and `/prd:roadmap-sync`: the model can start them. They no
  longer set `disable-model-invocation`. Only the person accepts a drift, in an
  answer to `AskUserQuestion`, as before.

## 4.4.0

### Added

- `/prd:setup`: makes the two bundles with `prd.py init` when they are absent,
  and adds a router block to the repo `CLAUDE.md` between
  `<!-- prd:router start -->` and `<!-- prd:router end -->`: where the bundles
  are, which file to read first, and the commands to use. A second run keeps
  the bundles and replaces the block in place.
- `scripts/claude_md_router.py`: the script that writes the block. It changes
  no text outside its markers. The same file ships in the adr, wiki, and
  pr-flow plugins.

### Changed

- `/prd:explore` and `/prd:migrate` point at `/prd:setup` for the `CLAUDE.md`
  block. They do not write `CLAUDE.md`.

## 4.3.0

### Added

- `/prd:system-design`, the skill that turns the PRD bundle and the ADRs into
  one system design. It walks eight areas in their blocking order: quality,
  context, strategy, building blocks, data, contracts, conventions, and
  deployment. It writes `docs/product/system-design.md` with stable IDs that
  a spec can cite, records each significant decision as an ADR with
  `status: proposed`, and keeps each settled area across sessions. Every run
  works on the `design/system` branch and in one draft pull request. A
  quality target that no PRD page holds becomes a Constraint page.
- `skills/system-design/references/document-format.md`, the template of the
  document: the fifteen headings, the frontmatter keys, the component
  catalogue, and the ID rules.
- `scripts/design_lint.py`, the well-formedness check of the document. It
  tests the area statuses, the shape of each Decision index row, each ID
  reference, each ADR file name, the one `C-<slug>` ID and the `areas` key of
  each catalogue entry, each `realizes` item, and the rule that
  `status: accepted` needs no open area. It prints one line for
  each finding and exits 1. A draft with no component catalogue yet names
  components freely, and a superseded ADR needs no Decision index line.

### Changed

- `/prd:specifying-stories` reads `docs/product/system-design.md` as one more
  source. A `decided` area with an accepted ADR is inherited; an `open` or
  `fog` area is asked. A missing design, or an open area that the Feature
  touches, gives one warning and an offer to run `/prd:system-design` first.
  It does not refuse. Each spec lists the IDs that it inherits in an
  `inherits` frontmatter key, and a spec choice that contradicts an inherited
  entry is a conflict that the skill shows and asks about.

## 4.2.0

### Added

- `/prd:specifying-stories`, the skill that turns one Feature and its Stories
  into one spec file or more that `/relay:implement --spec` accepts. It infers
  each technical decision from an accepted ADR, a PRD Decision page, or a
  built spec, asks the person only the open rows, writes each cross-cutting
  decision as a proposed ADR, and sets each covered Story to `ready`. It asks
  which Stories need no build, and gives each one `spec: none`. Each spec
  records the session that wrote it in a `session` key. Each ADR names its
  spec in `parent_spec`. A failed state call stops the skill before the
  commit, and the report names each Story that is `blocked`. The spec pull
  request refers to each Story issue with `Refs #n`, so the build pull
  request closes it.
- The `spec` slot on the `Story` class: a path from the repository root, or
  the word `none` when the Story needs no build. `schema/product.schema.json`
  is regenerated.
- `scripts/check-plugin.sh`, which finds an installed plugin root by a probe
  file and an optional version floor. It holds the candidate search of the two
  probes below: the project root, the home root, then the plugin cache. A
  direct root that passes ends the search, so the common case does not walk the
  cache.
- `scripts/check-superpowers.sh`, the presence probe of the superpowers
  plugin. `/prd:specifying-stories` copies the spec shape and the self-review
  list of its `brainstorming` skill, so the skill stops when the plugin is
  absent.
- `scripts/check-relay.sh`, the presence and version probe of the relay
  plugin, with a floor of 5.0.0. `/prd:work` stops when relay is absent and
  the spec is `kind: build`. `/prd:specifying-stories` keeps relay optional,
  for the code summary of the `relay:scout` agent only.
- Warning W7: a Story in `ready` with no `spec` field. Warning W8: two files
  in `docs/superpowers/specs/` that list the same Story.

### Changed

- `prd.py claim` takes one ID or every ID of one spec, and it is all or none:
  the group is refused when one Story is held or is not ready, and nothing is
  written. `release` and `expire` keep one ID.
- `prd.py ready` offers no Story that has no `spec` field and no Story with
  `spec: none`. Items of the other types are listed as before.
- `/prd:work` refuses a Story with no `spec`, a Story with `spec: none`, a
  `spec` path to a missing file, a spec whose `stories` list does not hold the
  Story, and a spec whose `lifecycle_state` is not `specified`. It claims
  every Story of one spec in one call. After the consent, it sets every
  Story of the group to `in_progress`, and it calls
  `/relay:implement --spec` for a `kind: build` spec. When `prd.py ready` prints no line, it runs
  `prd.py check` and names each `W7` Story, with the advice to run
  `/prd:specifying-stories`.
- The two shared documents name the `spec` field of a Story.

## 4.1.0

### Added

- `/prd:review`, the drift part of `/prd:roadmap-sync` as a command of
  its own. It needs no GitHub Project and no network. It shows each drifted
  trace, groups the traces that one change caused, and runs `drift --accept`
  only for a trace that the person accepted. It has no `Agent` grant, and a
  person must start it.
- `prd.py drift --show <ITEM> <TARGET>`. It finds the text of the last accept
  in the Git history of the requirement, the newest commit whose body has the
  stored hash, and prints the commits after it and a diff to now. It writes
  nothing and exits 0.

### Changed

- `/prd:roadmap-sync` Part 2 follows `/prd:review`, so the review has one
  home.
- `/prd:save` tells the user to run `/prd:review` after it flags drift.

### Fixed

- A Milestone can hold `drifted`. A Milestone holds `traces`, so
  `drift --write` flagged it, and `check` then failed with rule E2 on each
  flagged milestone.

## 4.0.0

The prd plugin writes two OKF v0.2 bundles: `docs/product/prd/` for the PRD and
`docs/product/roadmap/` for the roadmap. One page holds one requirement or one
work item, each relationship is a typed field, and a Python command does the
exact work. The design is
`docs/superpowers/specs/2026-09-20-prd-okf-graph-design.md`.

### Breaking

- The PRD and the roadmap are directories, not files. `docs/product/prd.md` and
  `docs/product/roadmap.md` become `docs/product/archive/prd-v3.md` and
  `roadmap-v3.md`.
- `/prd:migrate` does the change. It scans the v3 files, takes a type map from
  the user, builds the new tree in a temporary directory, asserts five
  properties on it, and only then moves it. No ID and no trace is lost.
- Each skill stops when it finds `docs/product/prd.md` and no
  `docs/product/prd/index.md`. It recommends `/prd:migrate`.
- The arc plugin reads the v3 paths. It stops reading the PRD of a repository
  that migrates, until its own change lands. arc is in another repository.

### Added

- `schema/product.yaml`, one LinkML schema for the PRD bundle and the roadmap
  bundle, and the generated `schema/product.schema.json`, written by
  linkml 1.11.1. `requirements-dev.txt` holds that pin, and both
  `scripts/gen-schema.sh` and the CI workflow read it from there.
- `scripts/prd.py` with `init`, `new`, `resolve`, `list`, `check`, `regen`,
  `hash`, `drift`, and `state`.
- `check --bundle <name>` answers rules E1 to E3 only, and prints one
  `SKIP: <rule>` line for each rule it does not run. A rule that cannot run
  must not read as a rule that passed.
- Warning W1 comes at 100 lines or at 600 words. A long block on one line
  does not pass the line count (D34).
- A pytest suite in `tests/` and the CI workflow `.github/workflows/prd.yml`.
- The `google-style` skill, vendored from a private repository of the author at `e799832`. Its
  description is limited to PRD and roadmap text. Every skill and agent that
  writes document text reads it first, and "Writing style" in
  `skills/shared/bundle-schema.md` tells how it applies to a PRD and a roadmap.
  The legacy migration writes merged text in this style. A skill restyles only
  the text it writes or changes, so a style edit gives no false drift.
  `tests/test_writing_style.py` fails if a skill or agent stops loading it.
- `prd.py migrate` with `--scan`, `--map`, `--dry-run`, the main run, and
  `--finish`. `--scan` reports the shapes it finds and the recipe vote,
  `--map` takes the type map, `--dry-run` builds the tree and throws it away,
  the main run asserts the five properties, moves the tree, and archives
  the v3 files, and `--finish` stores the hashes after the skill step.
- The skills `/prd:tasks-identify` and `/prd:migrate`.
- `skills/shared/bundle-schema.md` and `skills/shared/roadmap-model.md`, the
  two documents that hold the page format, the node types, the relationships,
  the states, and the status tables.
- The static skill tests: each skill names the pages it writes, holds the Bash
  grants it needs, and carries the v3 guard.
- The migration golden manifest and the three shape fixtures.
- The GitHub round trip: `prd.py github plan`, `github apply`, and
  `github pull`. `plan` is a pure function of the roadmap pages and one
  snapshot of the GitHub API, so it prints a change set and writes nothing.
  `apply` runs the change set and writes the number, the node ID, the URL, and
  the `pushed_hash` back on each page. It writes a value into `synced` only
  after it sent that value. `pull` reads GitHub back: a push-only field that
  differs is reported, never taken, and a state that a person changed in the
  Project goes through `prd.py state`, so the Event log stays complete.
- `apply` sends each of the nine values that the `pushed_hash` covers: the
  title, the body, the type, the parent, the blockers, the milestone, the two
  planned dates, and the labels. A new issue goes onto the Project with the
  Status of its page and the person who owns it.
- An issue that a person closed reads as `done`, or as `cancelled` when it
  closed as not planned, in `plan` and in `pull` alike.
- `github plan --keep <ID>` and `github apply --keep <ID>` send the values of
  a page over an edit that a person made in GitHub.
- `github pull --adopt` makes a page in `backlog` for an issue on the Project
  that no page names. An issue that is not on the Project is not roadmap work.
- An organization repository gets issue types when the token has the
  `admin:org` scope. Other repositories, and other tokens, get the labels
  `type:epic`, `type:feature`, `type:story`, and `type:task`.
- `github plan`, `github apply --dry-run`, and `github pull` take `--snapshot
  <file>`, which reads a recorded API snapshot. The whole test suite runs on
  recorded snapshots, so no test calls GitHub.
- `scripts/github_probe.py` answers the five GitHub questions that no source
  tested: the Status option IDs, a `blockedBy` cycle, the sub-issue limits, the
  login of the person who moved a card, and the login of the person who closed
  an issue. Until the probe runs, the code takes the safe path for each one
  (D37). The probe refuses to run without `--confirm`. It also prints the
  calls that no test sent to GitHub, as a list to run by hand on a test
  Project.
- `/prd:roadmap-sync` drives three parts: the round trip, `drift --all`, and the
  evidence scan for an item that GitHub does not hold. It asks the user before
  every apply.

- The agent layer: phase 4 of the design spec. `prd.py claim`, `heartbeat`,
  `release`, and `expire` hold one work item under a lease. The lock covers
  one working tree, so between clones git is the check: two claims change the
  same lines and the second push gets a conflict.
- `prd.py ready` lists the items in `ready` that no live claim holds, in the
  order of the milestone date and then the ID. An item with no milestone, or
  with a milestone that has no date, comes last.
- `prd.py run-checks` runs the declared check of each acceptance criterion and
  writes one Run page. A check is an argv list and the script starts no shell.
  A criterion with no check gets the result `not-checked`, which is an entry
  with no `exit_code`. The exit code of the command is the verdict: 0 when
  no check failed, 1 when one failed. A run in which no check ran gets the
  outcome `not-checked`, not `passed`.
- `prd.py new --discovered-from <ID>` writes the `discovered_from` path from
  an ID, for the work that an agent finds.
- `/prd:checks-declare` records the check of each criterion of one story, with
  the login of the person who declares it. Rule E8 refuses a check that has no
  `check_declared_by: human:<login>`, because a check runs code on the machine
  of the user.
- `/prd:work` gives the protocol for one agent and one item: claim, read the
  item and its links only, work, run the checks, review, release. A person
  sets `done`.

- A page with frontmatter that does not parse gives the `E1` finding in
  `check`, and an exit-1 message in `regen` and `drift`, never a traceback.
  `new` refuses a `--set` of `state`, `drifted`, or an actual date, refuses
  `--link includes=` and `--link traces=`, and checks the new page against
  the schema before it writes anything. A usage mistake (an unknown type, a
  bad actor string, a missing `--actor`) exits 2. A lock file that is still
  being written does not read as stale.
- Rule E10 and `regen --check` read the same comparison, so they give the same
  answer for a table.
- A page that does not read and a trace target that is deleted both exit 1.
- `list --where` needs a key and a value. A `--where` with no `=` exits 2.
- A state that leaves `done` clears the actual end date.
- The Event line takes the shape of the spec.
- The hash drops the `# <id>` heading only. It keeps every other heading.
- The limit of the page writer is written down: it rewrites the frontmatter,
  and it does not rewrite the body.

### Removed

- `skills/shared/prd-schema.md` and `skills/shared/roadmap-table-schema.md`.
  The two documents above replace them.
