# The brain standard

Version 1. The `knowledge` plugin owns this standard. Every brain follows it.
The general check (`knowledge.py check`) checks each rule that code can check.

A brain is a plugin that keeps one kind of project knowledge as a graph:
`product` (PRD and roadmap), `business-domain` (domain), `architecture`
(decisions), `system-design` (system design), and `knowledge` (the generic
graph). An agent that can read
one brain can read every brain. An agent finds facts one step at a time. It
never loads a full graph.

## 1. A brain

- A brain is a Claude Code plugin with one or more OKF v0.2 bundles.
  `product` has two bundles, `prd` and `roadmap`. Each other brain has one bundle.
- A brain declares `knowledge` as a dependency in `plugin.json` by name only:
  `"dependencies": ["knowledge"]`. Do not add a version range. A range needs
  release tags, and this repository has none.
- The minimum Claude Code version is 2.1.110.

## 2. The bundle

- Each Markdown file has YAML frontmatter with a `type` that is not empty.
- The root `index.md` has frontmatter with `okf_version` only. A directory
  `index.md` has no frontmatter. The save code writes each `index.md`.
- `log.md` is at the bundle root. It has no frontmatter. It has
  `## YYYY-MM-DD` headings, newest first. One entry is one line:
  `* **<Operation>**: <text>, by <actor>, at <time>`.
- The save code writes a `LINKS` block at the end of each page that has
  links. The block starts with `<!-- LINKS:START (generated, do not edit) -->`
  and ends with `<!-- LINKS:END -->`.
- The save code writes `links.tsv` at the bundle root. Its first three
  columns are `source`, `relation`, and `target`. A brain can add columns.
- `manifest.md` is at the bundle root (section 6).
- A page has fewer than 100 lines and fewer than 600 words. The `LINKS`
  block does not count. A longer page gets a warning.

## 3. The page

- The OKF fields come first: `type`, `title`, `description`, `status`,
  `tags`.
- `description` is one line, and each page must have it. The `ask` judge
  reads the description before it opens the page. Write it in the words of
  the brain, and make it specific.
- `status` has the OKF values only: `draft`, `stable`, `deprecated`. A brain
  keeps its own lifecycle in a different field: `product` uses `state`, and
  `architecture` uses `lifecycle`.
- Provenance is on each page. `generated: {by, at}` records the last
  meaningful change. `verified: [{by, at}]` records each confirmation by a
  person. `sources` and `confidence` are optional.
- An actor has one of three forms: `human:<login>` for a person,
  `<plugin>/<version>` for the plugin code, and `process:<id>` for a script.
- `protected: true` stops `forget`. Only a person sets or removes it. The
  save code never changes it.
- Each brain declares its ID scheme in its manifest. `product`,
  `business-domain`, and `system-design` use `<TYPE>-<NN>`: the file name is
  the ID plus `.md`, and the type, the folder, and the ID prefix agree.
  `architecture` keeps its `id_scheme`.
  The generic graph keeps its slug names.
- An ID is unique in its graph. A reference in body text to a page of another
  graph names the graph: `prd:CAPABILITY-12`, or a `<graph>:/<path>` link.
- The save code gives each ID. An ID is never used again, also after
  `forget`. `aliases` holds old titles, merged IDs, and old ID forms.
- A page with a fixed name and no ID is allowed only where the manifest lists
  it in `fixed_pages`.

## 4. The schema

- Each brain has a LinkML schema. A pinned generator (`linkml==1.11.1`)
  writes a JSON Schema from it. The generated file is in git.
- `knowledge/schema/base.yaml` holds the shared slots: the OKF fields,
  provenance, `aliases`, `protected`, and the actor forms. Each brain schema
  imports it with `../../knowledge/schema/base`. A brain schema never
  defines a name that the base defines. It narrows a base slot only with
  `slot_usage`.
- The generated JSON Schema of each brain is complete. No plugin reads a
  file of another plugin when it runs.
- A test of each brain fails when its generated schema is not fresh, or when
  its schema does not import the base.

## 5. Links

- In a bundle, a frontmatter link starts with `/` and is relative to the
  bundle root. A link in the body is relative to its file.
- Between graphs, the link form is `<graph>:/<path>`, for example
  `prd:/capabilities/CAPABILITY-03.md`. `<graph>` is a name in the registry.
- The registry is `.claude/knowledge.json` in the project:

  ```json
  {"graphs": {"prd": {"path": "docs/product/prd"},
              "platform-adr": {"repo": "github.com/<owner>/<repo>", "path": "docs/adr"}}}
  ```

  `path` is the bundle root: the folder that holds the root `index.md`. Each
  brain's `setup` writes its own entries. A person adds the remote entries.
  A brain with its own config file (`.claude/ddd.json`, `.claude/adr.json`)
  keeps it. When the two differ, the brain config is correct, and the next
  `setup` writes the registry entry again.
- For a remote graph, the code makes a shallow clone of the default branch
  into a cache outside the project. A private repository needs `gh`
  authentication (`gh auth setup-git`). A remote link that does not resolve
  is a warning.
- In the `LINKS` block, a link to a local graph also gets a relative path, so
  a generic OKF reader can follow it. A graph that is not in the registry
  gets no relative path.
- When a `<graph>:/<path>` target is not at its path, the resolver looks for
  the same file name in each folder of the manifest `id_folders`.
- A graph never stores the links that come into it from another graph. The
  `knowledge` code computes them on request.

## 6. The manifest

`manifest.md` is at the bundle root, with `type: Manifest`. Its fields:

- `brain`: the graph name, for example `adr`.
- `plugin` and `plugin_version`: the plugin and the version that wrote the
  bundle.
- `ask_skill`: the skill that answers from this brain, as `plugin` (for
  example `architecture:ask`) and `skills` (for example `architecture-ask`).
- `install`: the command that installs the plugin.
- `save_code`: the save script, relative to the plugin root: a path that is not absolute and has no empty, `.` or `..` part. `plugin` holds a name of the form a-z, 0-9 and -, with a letter or a digit first. The 2 values are a pair of `BRAINS` in `knowledgelib/probe.py`; a new brain plugin adds its pair there.
- `id_pattern` and `id_folders`: a regular expression for the file name of a
  page with an ID, and the folders that hold those pages (`.` is the root).
- `answers`: the kinds of question that the brain answers, as short lines.
- `required_links`: for each page type, the link fields whose target the page
  cannot exist without. `forget` reads it.
- `fixed_pages`: the names or name patterns of the pages with no ID.
- `retired_ids`: the IDs that `remove` retired. `new` never gives them again.

Each brain's `setup` writes the brain's router block in `CLAUDE.md` with
its copy of `claude_md_router.py`.

## 7. Skills

- Each brain has `setup`, `learn`, and `ask`. The plugin form is
  `<brain>:<skill>`.
- A brain can have more skills. A skill that makes knowledge ends with the
  question "Learn these results?" and calls `learn` on yes.
- `check` is not a command. The hook of the brain runs the checks, and
  `learn` runs them itself.

## 8. The save code

Each brain has one save script. `learn` and `forget` write pages only
through it. Each operation writes `generated` with the actor. Each script
takes `--root <project root>` before the operation:

| Operation | What it does |
|---|---|
| `init [--dir D]` | Makes a new bundle with the manifest, the log, and the registry entry. |
| `upgrade [--dir D]` | Brings an existing bundle to the standard: adds `generated` with a `process:` actor, adds `log.md`, runs `regen`, and then writes the manifest and the registry entry. |
| `new TYPE --title T --description D [--set KEY=YAML]` | Makes a page with the next ID and valid frontmatter. |
| `set KEY KEY=YAML...` | Changes fields of a page. It refuses `protected`. |
| `link KEY FIELD TARGET` | Adds a typed link. |
| `unlink KEY FIELD TARGET` | Removes a typed link. |
| `remove KEY` | Deletes a page and adds its ID to `retired_ids`. It refuses a protected page. |
| `resolve KEY` | Prints the path of a page from an ID, an alias, or a bundle path. |
| `regen [--check]` | Writes the indexes, the `LINKS` blocks, and `links.tsv`. With `--check`, it writes nothing, prints `STALE: <root-relative path>` for each stale file, and exits 1. |
| `check [--strict]` | Runs the semantic rules of the brain. |
| `log OPERATION TEXT` | Writes one `log.md` entry. |

When the code cannot do the change, the agent edits the page directly. Then
it reports the problem and the reason (section 10).

## 9. The checks

- The brain check runs the semantic rules of the brain, in its own code.
- The general check runs the rules of this standard, in `knowledge`:

| Rule | Level | What it checks |
|---|---|---|
| `K-registry` | ERROR | The project has `.claude/knowledge.json`, and each local path is a folder. |
| `K-manifest` | WARN, ERROR | WARN when the bundle has no `manifest.md` ("not on the standard yet"). Then no other rule runs on it. ERROR when a manifest field is missing or wrong. |
| `K-root-index` | ERROR | The root `index.md` exists and its frontmatter holds `okf_version` only. |
| `K-dir-index` | ERROR | A directory `index.md` has no frontmatter. |
| `K-log` | ERROR | `log.md` exists, has no frontmatter, and has `## YYYY-MM-DD` headings, newest first. |
| `K-links-tsv` | ERROR | `links.tsv` exists and starts with `source`, `relation`, `target`. |
| `K-okf` | ERROR | Each page has frontmatter that parses as a mapping with a `type`. |
| `K-fields` | ERROR | Each page has `title`, a one-line `description`, an OKF `status` when present, and a boolean `protected` when present. |
| `K-provenance` | ERROR | `generated` and each `verified` entry hold `by` (an actor form) and `at` (a time with an offset). |
| `K-id` | ERROR | Each page in `id_folders` matches `id_pattern`, or `fixed_pages` names it. |
| `K-links-block` | ERROR | A page with frontmatter links has a `LINKS` block. |
| `K-fresh` | ERROR, SKIP | The `regen --check` of the brain finds no stale file. SKIP when the plugin is not found. |
| `K-link` | ERROR | A `/` link or a link into a local graph resolves. |
| `K-remote-link` | WARN, SKIP | A link into a remote graph resolves. SKIP when the hook finds no cache. |
| `K-unknown-graph` | WARN | A `<graph>:/<path>` link names a graph that is in the registry. |
| `K-size` | WARN | A page has fewer than 100 lines and fewer than 600 words. |

- Each linter has one output contract: one line for each finding,
  `<LEVEL>: <file>:<line> [<rule>] <message>`, with the levels `ERROR`,
  `WARN`, and `SKIP`. A SKIP line is `SKIP: <rule> (<message>)`, with no file
  and no line. The last line is the summary `N errors, M warnings`. It is not
  a finding. The exit codes are `0` (clean, or warnings only without
  `--strict`), `1` (an error, or a warning with `--strict`), and `2` (a usage
  or a configuration error).
- Each brain has one PostToolUse hook on `Write|Edit|Bash`. For a file in its
  bundle, or for a Bash command that runs its save script, the hook runs
  `regen`, then the brain check, then the general check on that bundle with
  `--cache-only`. A command that only names the save script, for example a
  `grep`, does not start the steps. For a Bash command, the root is the git
  root of the `cwd` of the hook input, so a session in a worktree checks that
  worktree. When that root has no bundle of the brain, the hook does nothing. Claude Code runs the hooks of one event in parallel, so one
  hook does the three steps in this order. A hook can skip its steps when no
  file of its bundle changed, and it can print the `K-size` warnings of the
  changed files only, with a count of the others.
- Code that needs another plugin finds it with its copy of
  `probe-plugin.sh <name> <probe-path>`. The probe tries the sibling folder
  first (`<own root>/../<name>`), and uses it only when its `plugin.json`
  names the plugin. Then it tries the installed places. In a check, a probe
  miss gives one SKIP line for each rule that needs the other plugin. It never
  tries a folder of the project, because Claude Code installs no plugin there.
  It refuses a plugin name that is not a-z, 0-9 and - (a letter or a digit
  first), and a probe path that is absolute or has an empty, `.` or `..` part.
  A caller runs a save code only when its resolved path is in the resolved
  plugin root, and the root is an install place.
- `learn` and `forget` run both checks after each write, through the hidden
  skill `knowledge:checking`. They never report success while a check exits 1.

## 10. Reports

`learn` and `forget` write a `log.md` entry (`* **Report**: ...`) for each
direct edit: the failed operation, the edit, and the reason. They also write
an entry for each recommendation to improve the skill or the save code. They
show the report at the end of the run, with each SKIP line of the checks.
They offer to open a GitHub issue with the report in
`ai-advanced-futures/cc-plugins`. After a yes, they show the full issue body
and ask a second question, which says that the repository is public. They open
the issue only after a yes to the second question.

## 11. Forget

`knowledge:forget` removes a page from any brain and each reference to it.
`knowledge.py forget-plan <graph>:/<path>` finds the references (frontmatter
links, `<graph>:/` links, and IDs in body text) and the tree of pages that
cannot exist without the target (`required_links`). The plan stops, and
nothing changes, when a page of the tree is protected, when the plugin of a
graph that it touches is not installed, or when such a graph has no manifest.
The person gives one yes for the whole tree. Each brain's save code removes
the pages and the links. The agent edits the body mentions and reports each
edit. A remote reference goes through a pull request, after a separate yes.

## 12. Writes to a remote graph

- A write uses a full clone of the default branch in a work folder.
- The code pushes a branch when the person can push. If not, `gh` makes a
  fork, and the pull request comes from the fork.
- The save code of the plugin that is installed here writes the change. The
  write stops when the brain of the remote graph is not installed here, or
  when the remote manifest has a higher major `plugin_version`.
- Both checks run in the clone before the push. A failed check stops the
  write, and nothing is pushed.
- One pull request for each remote repository in one run, after a separate
  yes.
