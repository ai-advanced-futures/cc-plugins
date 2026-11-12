# Changelog

## 1.7.0

### Added
- The general check has a new rule, `K-cite` (WARN; `--strict` gives exit 1). It reads the pages of the folders in the new optional manifest key `cite_folders`, and it warns on 2 classes of text: a line citation with no commit in its sentence (a path and a line such as `file.py:12`, prose such as `line 12` or `lines 3-5`, and a backticked `:12`), and a PR or issue state next to a number (for example `open`, `not on main`, `not merged`, a draft PR) with no date and no commit in its sentence. A graph with no `cite_folders` key, a `null` value, or an empty list gets no `K-cite` warning. A `cite_folders` value that is not a list of strings, or a folder that is not in `id_folders`, gives a `K-manifest` error. The save code keeps the key and never writes it. Sections 6 and 9 of the brain standard say this (STORY-426).
- The hook keeps each `K-cite` warning only for a changed page, as it does for `K-size`, and it adds the line `K-cite warnings on pages that did not change: <N>.` for the others.

## 1.6.1

### Fixed
- `knowledge.py brain-check` ended with a traceback (`TypeError: unhashable type`) and no `SKIP` line when the `plugin` or the `save_code` of a manifest was a list or a map, and the check of each later graph did not run. Now it tests that each of the 2 values is text before it puts the pair in the set. A value that is not text (a list, a map, `null`, a number) gives the line `SKIP: brain-check (<graph>: the <field> of manifest.md is not text: <value>)` and exit 1, and the run goes on with the next graph. The general check keeps its `K-manifest` error for the same manifest (STORY-318).

## 1.6.0

### Added
- A local registry entry can have `"git": false`: git does not keep its folder, so a new clone has no folder until the person runs the setup skill of that brain. `knowledge.py check` gives a `WARN` `K-registry` for such an entry with an absent folder (before, an `ERROR`), and the text gives the steps to fix it. A link into such a graph that does not resolve in that clone gives a `SKIP` `K-link` (before, an `ERROR`). An entry with no `git` key acts as before. A `git` value that is not `true` or `false` is a usage error (exit 2). Sections 5 and 9 of the brain standard say this (STORY-257).
- `ux-hci-design` is a known brain: `knowledgelib/probe.py` has the pair `("ux-hci-design", "scripts/ux_graph.py")`.

## 1.5.4

### Changed
- The issue offer of `knowledge:learn` and `knowledge:forget` shows the full issue body, asks a second question that says that `ai-advanced-futures/cc-plugins` is public, and opens the issue only after a yes to the second question (STORY-286). Before, it opened the issue after the first yes, which was to the offer and not to the text. Section 10 of the brain standard says the two steps, and `knowledge:learn` says that the report file holds only the body that the person accepted.

## 1.5.3

### Changed
- The hidden skill `knowledge:checking` grants only its 2 check commands and `git rev-parse`. Before, it granted the whole shell, and each skill that called it kept the whole shell after the check.
- New: `knowledge.py brain-check --graph <graph>` runs the check of the save code of each named graph. `brain-check` and `check` take `--root` after the command name too (STORY-282).

## 1.5.2

### Changed
- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).
- `install_place` reads the same folder.

## 1.5.1

### Changed
- `BRAINS` of `knowledgelib/probe.py` has the pair `business-case` with `scripts/bc_graph.py`, so the manifest check, `K-fresh`, `forget` and the remote save code accept the graph `business-case` (STORY-89). Before, `knowledge.py check` of that graph gave the `K-manifest` ERROR "is not the pair of a known brain".

## 1.5.0

### Changed
- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).
- New: `knowledge.py brain-root --graph <graph>` prints the root of the brain of a graph. The skills `checking` and `forget` use it.
- The manifest, the check `K-fresh`, `forget` and the remote save code refuse a plugin name or a `save_code` path that is not the pair of a known brain.

## 1.4.11

### Fixed
- `knowledge.py` and `knowledge_graph.py` accept the Git Bash form of `--root` on Windows (`/c/x`, also `/cygdrive/c/x`), and a drive path with `/` or `\`. Windows Python read `/c/x` as the folder `c` on the current drive, so `resolve /index.md` said that the graph is not in `.claude/knowledge.json`.
- When `.claude/knowledge.json` does not exist at the root, the message says `the root does not match a path in .claude/knowledge.json`, and names the file and the `--root` as given. It does not say that the graph is missing.

## 1.4.10

### Fixed
- The save code tries a read or a write of a file again when a short file lock stops it, as an antivirus or an indexer does on Windows (errno 13 or 22, or Windows error 32 or 33): 5 tries in 1.5 seconds. Before, `link` could lose its write, and `body` stopped in regen with a traceback (public issues 1 and 2).
- A write goes to a temporary file in the same folder first, and then takes the place of the file. So a write that fails keeps the old file.
- When the last try fails, the command exits 1 with 1 line. A page write says that the page was not saved. A failed regen says which page is saved, which file failed, and gives the command `knowledge_graph.py --root "<root>" regen`.

## 1.4.9

### Changed
- `knowledge:ask` allows only its own commands. A run of `uv run` is allowed only for `${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py`, so `uv run python -c ...` and `uv run --with <package> ...` ask for approval. `mktemp` is allowed only with `-u`, so it makes no file. The walk state file is named by its path: the skill runs `printenv KNOWLEDGE_WALK_STATE` and writes the path it prints in each call, not the variable, because a command with a variable asks for approval. Tests of the skill check that each command of the skill text runs with no prompt, and that the commands above ask for one.

## 1.4.8

### Changed
- `knowledge:ask` writes each command in full in each Bash call, so it runs in zsh and in bash, and it writes no wrapper file and no helper file. The walk state template is `/tmp/knowledge-walk.XXXXXX`, so it works with the `mktemp` of macOS.

## 1.4.7

### Changed
- `knowledge:ask` reads each page and each manifest with the Read tool. Step 1, Step 2, and Step 3 get the path with `$K resolve`, then read that file with the Read tool, not with `cat`, `grep` or another shell command. A test of the skill fails when a step does not name the Read tool.

## 1.4.6

### Changed
- The tests and the docs name the job `knowledge` of the CI workflow `.github/workflows/ci.yml`. One workflow replaces the workflow file of this plugin. The plugin behavior does not change.

## 1.4.5

### Fixed
- The hook runs its steps only when a Bash command runs `knowledge_graph.py`. Before, any command that held the file name, even in a quoted text, started the steps. The hook now looks for the script in command position, and it removes each quoted span first. The hook also ignores a heredoc body and a `#` comment. The time of the check grows in line with the length of the command. A quoted script path, or a script path in a variable, does not start the hook.

## 1.4.4

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `knowledge@cc-plugins`. The homepage and the repository fields point at the public repository, and the install lines and the issue links name it. Install the plugins again from the new marketplace.

## 1.4.3

### Changed
- The schema `id` and prefix URLs of `base.yaml` and `knowledge.yaml` name the public repository, `cc-plugins`.

## 1.4.2

### Changed
- `knowledge:ask`: an answer that does not come from the walk, for example from a
  grep of the files, starts with the exact first line `not a graph walk: grep fallback`.
- `knowledge:neighbor-judge` has the tool `Read` only. Its steps read the current
  node and never search, so `Grep` and `Glob` are removed.

## 1.4.1

### Changed
- The hook runs its steps only when a file of the graph changed. A Bash command
  that runs `knowledge_graph.py` and changes no file (for example `check` or
  `resolve`) now gives no output and starts no step.
- The hook shows each `K-size` warning only for a page that changed in this
  call. It adds one line, `K-size warnings on pages that did not change: <N>.`,
  for the others. Each other `WARN` and `SKIP` line stays.
- `knowledge_graph.py` writes the change list `<git dir>/knowledge-changed`:
  the paths (relative to the git root) of each file that `new`, `set`, `body`,
  `link`, `unlink`, `remove`, `regen`, `log`, and `upgrade` write or delete.
  The hook takes the list with one `mv`. `KNOWLEDGE_NO_CHANGE_LIST=1` turns the
  list off. Outside a git repository there is no list and no error.
- When a Bash command leaves no change list (for example, `git` failed), the
  hook checks everything and shows every warning, as before 1.4.1. A run that
  changed no file leaves an empty list, and the hook then ends with no output.
- When `knowledge_graph.py` cannot write the change list, it prints one `WARN`
  line on stderr. The exit code does not change.
- A write that does not use the save code (for example `sed -i`) is not in the
  list. The hook still checks the file of an `Edit` or a `Write`.

## 1.4.0

### Added
- `knowledge_graph.py body KEY --file PATH [--append] [--by ACTOR]` writes the
  text of a page above its `LINKS` block. `--file -` reads standard input.
  With no `--append`, the text replaces the text above the block. With
  `--append`, the text goes after the current text, after one empty line.
  `body` keeps the frontmatter, writes `generated`, and lets `regen` write the
  block again. It exits 2 for empty text, a missing file, and text that holds a
  `LINKS` marker. It exits 1 when the key has no page. It changes a protected
  page, as `set` does.

### Fixed
- A key of `set`, `body`, `link`, `unlink`, `remove`, and `resolve` that leaves
  the bundle (`..`), or a page that is a symbolic link out of the bundle, now
  gives no page (exit 1). Before, `remove` could delete a file outside the
  bundle and `set` could change one.

### Changed
- The `learn` skill writes each page text with `body`. A direct edit, with its
  Report entry, is only for a change that no command of the save code can make.

## 1.3.1

### Changed
- `knowledge_graph.py link` now adds a full `sources` entry: `id` (the file
  name of the target with no `.md`), `resource`, `title`, and `last_modified`
  (the date of `generated.at` of the target). Before, the entry had only
  `resource`, so a footnote such as `[^2026-11-02-x]` did not match a source.
- `link` reads the target, as the `K-link` check does. When it cannot read the
  target (no file, no cache of a remote graph, or no `title` or `generated.at`),
  it exits 1 and writes nothing. Before, it wrote the entry anyway.
- A link path that leaves the bundle (`..`) or a symbolic link that leaves it
  is not a file of the graph. `link`, `resolve`, and the checks do not read it.
- `regen` escapes `\`, `[`, `]`, `<`, `>`, and the backtick in a title that it
  writes as the label of a markdown link (the `LINKS` blocks and the indexes).
- An entry with the same `resource` stays as it is. To repair an old entry that
  has only `resource`, run `unlink`, then `link`.

## 1.3.0

### Added
- `knowledge_graph.py new` has the option `--slug SLUG`. It names the page
  file. A slug that is not lowercase letters, digits, and single hyphens
  makes `new` exit with 2 and write nothing.

### Changed
- A Source page with a `resource` that starts with `raw/` now has the base
  name of its raw file. `raw/2026-11-02-x.pdf` gives `sources/2026-11-02-x.md`.
  Before, the slug came from the title. `--slug` wins over the base name.
- When the slug is taken or retired, `new` says to give `--slug` or another
  title.
- The `learn` skill links each page to the Source file name that `new` printed.
- A slug with a final newline is not valid. `new` refuses it, and the general
  check reports a page file with such a name.
- `new` refuses a page path that is a symbolic link (also a dangling one), and
  a type folder that is a symbolic link. Before, `new` could write through a
  dangling link to a file outside the repository.

## 1.2.1

### Changed
- The notes of 1.2.0 did not say this about `move`: when `AGENTS.md`, `raw/`,
  or `bundle/` of the graph is a symbolic link, or a folder in the path of the
  new folder is one, `move` refuses and changes nothing. `move` has done this
  since 1.2.0.

## 1.2.0

### Changed
- The default folder of the generic graph is now `docs/knowledge/`. It was
  `docs/wiki/`. A new graph is written to `docs/knowledge/bundle/`.
- A graph that is in `docs/wiki/` continues to work, because each command reads
  the path from `.claude/knowledge.json`.

### Added
- `knowledge_graph.py move --to <container>` moves `AGENTS.md`, `raw/`, and
  `bundle/` to a new folder, with no data loss, and undoes the move on an
  error.
- `/knowledge:setup` finds a graph in the old default folder `docs/wiki/` and
  offers to move it to `docs/knowledge/`.

## 1.1.3

### Changed
- The skill prompts and the `neighbor-judge` agent prompt are shorter. Each
  prohibition that stays now gives its reason. Duplicate rules are removed.
  The steps and the outputs of each skill stay the same.

## 1.1.2

### Fixed
- `knowledge:checking` runs one brain check for each pair of plugin and save
  code, not one for each graph. `prd` and `roadmap` share one check.
- Brain standard section 9: the hook starts for a Bash command that runs the
  save script, and uses the git root of the session folder.

## 1.1.1

### Changed
- The display name is now lowercase: `knowledge`.

## 1.1.0

### Changed
- Moved to ai-advanced-futures/cc-plugins-library. Install the plugin with
  `claude plugin install knowledge@cc-plugins-library`.

## 1.0.0

### Changed
- The `wiki` plugin is now `knowledge`. Remove `wiki` and install `knowledge`.
- `/wiki:setup` and `scaffolding-okf-wikis` are now `knowledge:setup`.
  `/wiki:ask` and `answering-from-okf-wikis` are now `knowledge:ask`.
  `/wiki:ingest` is now `knowledge:learn`.
- The plugin no longer copies `check_okf.py`, `check_links.py`,
  `regen_indexes.py`, and their tests into a project. The general check
  (`knowledge.py check`) replaces them.
- The registry entry `knowledge` in `.claude/knowledge.json` replaces
  `.claude/wiki.json`. `knowledge:setup` migrates an old wiki.

### Added
- The brain standard: `standard/brain-standard.md`.
- The base LinkML schema (`schema/base.yaml`) and the schema of the generic
  graph (`schema/knowledge.yaml`).
- `knowledge.py`: the registry, link resolution, the remote cache,
  navigation, the walk state of an ask, the general check, the forget plan,
  and writes to a remote graph.
- `knowledge_graph.py`: the save code of the generic graph.
- `knowledge:forget`, the hidden `knowledge:checking`, the Haiku agent
  `knowledge:neighbor-judge`, and the PostToolUse hook.
- The skills install: `skills/knowledge/`, built by
  `scripts/build-knowledge-skills.py`, with `knowledge-runtime` and one
  `knowledge-<skill>` for each skill. `probe-plugin.sh` also finds the
  `<brain>-runtime` skill of a skills install.
