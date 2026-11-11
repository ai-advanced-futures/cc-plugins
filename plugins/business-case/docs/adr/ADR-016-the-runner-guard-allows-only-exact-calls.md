# ADR-016 — The runner guard allows only exact calls

**Status:** Accepted · **Date:** 2026-11-09

## Context

The `build` command starts runners of 5 other plugins. Each runner calls the
scripts of its own plugin with `uv run`. The first version of the command
(STORY-168, ADR-006) gave a `Bash(uv run */<plugin>/*/scripts/*)` grant for
each plugin. Three problems showed in live runs and in a security review of
PR #697 (issue #703):

1. A `*` in a `Bash` pattern matches any text, with spaces. A `uv run` command
   with other words in front and a plugin script path at the end matched a
   grant. The 3 decoy commands of the issue ran with no question.
2. A grant of `allowed-tools` ends with the turn. A dispatch in the background
   ends the turn. In 1 of 3 runs, the next `bc.py` calls were refused and the
   run ended with `handoff blocked`.
3. A runner writes `.<plugin>/<run_id>/` and its session folder. No grant
   covered these writes, and an automated run refused them. The coach wrote its
   temporary files with fixed names in 1 folder, so 2 cases at the same time
   used the same files, and each `rm -f` of the text asked the person.

## Decision

### The hook

`hooks-handlers/runner_guard.py` has 5 modes. It is a new handler, not a new
mode of `judge_guard.py`: `judge_guard.py` blocks on a failure, and this
handler runs on each `Bash` call of each session, so an error must never stop
a call. Each error gives no decision and exit code 0.

- `post-bash` writes a mark file `$CLAUDE_PLUGIN_DATA/build-sessions/<session_id>`
  after a `bc.py session --id <this session id>` call that worked. A mark older
  than 30 days goes when the next mark is written.
- `pre-bash` gives an `allow` for a command only in a marked session, and only
  when the command is exactly 1 call: `uv run <absolute script path> <words>`
  with no shell feature. The script is `lib/bc.py` of this plugin with a
  subcommand of `bc.py` as first word, or a script of the table `RUNNER_CALLS`
  in the install folder that `install_check.check` gives for that plugin, with a
  first word that the table allows, or `scripts/bc_graph.py` of this plugin with
  the first word `publish`, and the option `--root <path>` before it. A judge in
  the background ends the turn before the `publish` call of `build.md`, and the
  grant of `bc_graph.py` ends with the turn (the verifier on PR 1034: 1 of 3
  automated builds wrote no page). `remove`, `set` and each other first word of
  `bc_graph.py` get no decision. Time stamps count as the first word `name`
  of `result_name.py`. A script sits in the `scripts/` folder of the install
  folder. Only `plugin_result_check.py` of `product-finance` sits in
  `scripts/plugin_result/` (a live run of its `discover-runner` showed this:
  its last step is a call of this script, and the guard refused it).
- `pre-write` gives an `allow` in a marked session for a write under
  `<project>/.<plugin>/` of the 5 plugins, and for a file directly in a
  temporary folder of `bc.py`. Paths are resolved, so a link out of the folder
  gets no `allow`.
- `pre-read` gives an `allow` in a marked session for a read of a file in the
  install folder of 1 of the 5 plugins, for a file in the `templates/`, `rubric/`
  or `agents/` folder of this plugin (`build.md` reads the case template and the
  rule of the figure extractor in a later turn), and for an answers file
  `business-cases/<case>/team/answers-*.json`. A live run showed the need: a
  runner reads its own plugin files (`plugin.json`, an agent file), these files
  are outside the project, and the default mode refused the read (2 refused
  reads in 1 run of `competitive-intelligence:discover`). Paths are resolved, so
  a link out of the plugin folder gets no `allow`. A plugin file is public text.
  A deny rule or an ask rule of the person still wins.
- `pre-skill` gives an `allow` in a marked session for a `Skill` call of the
  main conversation only for a route of `SKILL_ROUTES` (the 7 skill routes of
  `build.md`), and only for a planned run: its `args` must be the `plugin-run`
  block that `team-answers` printed (fenced, or the JSON line alone), the case
  of the block must be a case of a session call of the session (a line of the
  mark), and `team/runs.json` of that case must hold an open run with the same
  `run_id` and `command`, whose `block_sha256` is the SHA-256 of the JSON line
  of `args`, and whose route in the plugin map is the skill.
  `business-case:learn` gets no `allow`: in a later turn, Claude Code asks the
  person once before the skill loads (D-1065). Each `Skill(<name>)` grant of
  `build.md` ends with the turn, so a route that starts after the notice of a
  background dispatch was refused in a headless run (the STORY-251 probes). A
  call with `agent_id` in the hook input comes from a subagent, and it gets no
  decision. A test compares `SKILL_ROUTES` and the 1 exception
  `business-case:learn` with the 8 `Skill` grants of `build.md` (STORY-251,
  D-1049, D-1062, D-1065).

Each of the 5 runner plugins names the grants that its caller must give in its
own `caller-grants.json` (STORY-168). A test of this plugin compares the scripts
of each file with `RUNNER_CALLS`, so a new script in a runner fails the test
until the file names it. The guard gives no `allow` for a web tool or an MCP
tool, and neither does `build.md`: a web call stays the approval of the person,
because an `allow` for `WebFetch` would let an agent send data of the case to
any address.

A session with no mark gets no decision, so a plugin that is only enabled
changes no permission. A deny rule or an ask rule of the person still wins over
an `allow` of a hook.

`words_of` reads the command like a small shell parser and refuses each
feature that it does not model: `;`, `&`, `|`, redirects, `$`, backticks,
globs, braces, a backslash outside a quote, and a newline in a quote. The test
`test_a_call_with_an_extra_word_or_a_shell_feature_gets_no_allow` holds the
forms. A test compares the table `RUNNER_CALLS` with the text of each route, so
a new script in a runner fails a test.

### The grants of the command

The 10 `Bash` grants for the runner scripts are removed. The 2 `bc.py` grants
stay, because the first `bc.py` calls run before the mark exists. The folder
grant of each plugin is `Edit(/.<plugin>/**)`, because Claude Code checks a
file write against the `Edit` rules (ADR-006), the `<run_id>` is not known when
the command starts, and the root of the folder holds files too.

### The temporary folder of a case

`bc.py temp-dir --case <case>` makes and prints
`<gettempdir>/bc-<slug>-<8 hex of the sha256 of the case path>/` with mode 700.
It refuses a link and a folder of another user. `main()` deletes, in a
`finally`, each file that an option of `TEMP_FILE_OPTIONS` names, when the file
is in the temporary folder of `--case`, whatever the exit code. A file in
another place is the person's, and it stays. A call that the parser refuses
leaves its file, because `main()` has no parsed `--case` then; the next step
corrects the command and uses the same file. The command text holds no
`rm -f`.

## What the hook does not cover

- The `allowed-tools` of a route that `pre-skill` allows, and of each skill that
  the route loads with a bare `Skill` grant. Claude Code applies them in that
  turn, as it does for the `Skill(<name>)` grant of `build.md` in the first
  turn. A route that runs can also add an open run: with its own bare `Write` to
  `team/runs.json`, or with a `bc.py team-answers` call that `pre-bash` allows
  (#1598).
- The value of an argument: `uv run <script> <any text>` is allowed when the
  words match the table.
- A `pyproject.toml` of the project that `uv run` reads.
- A plugin that loads with `--plugin-dir` and has no install entry: its script
  calls ask, because the install check does not list it.
- A plugin that comes from a marketplace with a directory source: Claude Code
  loads it in place, and not from the install folder. The hook gives no
  decision for a read of its files, so each read asks. This fails closed.
  To test such a plugin, load the install folder with `--plugin-dir`.
- A call in a session that `bc.py session` never marked.

## Consequences

- A reply that a person types in the chat does not end the approval of the
  hook, and a dispatch in the background does not end it.
- The warning of the command says that a hook approves the own steps and the
  listed script calls.
- Each new script call in a runner needs a row in `RUNNER_CALLS`.
- Each new option of `bc.py` that takes a temporary file needs a name in
  `TEMP_FILE_OPTIONS`; a test checks the names in `build.md`.
- The hook costs about 0.45 s on a `uv run` call in a marked session. A call
  that does not start with `uv run` returns before the imports.
