# ADR-014 — The plugin map and the install check

**Status:** Accepted · **Date:** 2026-11-04

## Context

The evidence team (ADR-013) plans runs of other plugins' commands. Before it
can plan one, code must know two things. First, which command serves which
rubric item, and which version of each plugin writes results the team can
trust. Second, whether this session can run that plugin at all.

Code answers the second question from the files Claude Code 2.1.316 writes
for its installs and its settings. ADR-000 listed both parts as Plan 4 work. This record states what
v0.5.0 does and why.

## Decision

### The map is one versioned file in the plugin

The map is `plugin-map/plugin-map-1.0.0.json`. `lib/plugin_map.py` reads it
and holds no map data of its own. It refuses a file whose `schema` or
`version` is not the one it expects.

The map holds:

- each plugin's `min_version` and its commands. A command has its `route`,
  the agent the coach dispatches, `coach_runs`, `reads_from`, the result
  `kinds` it writes, and the inputs the coach never sets;
- the grade ceilings that are lower than a result's sources give;
- each result kind, with the rubric items it serves;
- each item's owner, its contributors, the items it comes `after`, and
  `owns_inputs`. In 1.0.0 every `owns_inputs` is empty.

`coach_runs` is false for `product-finance:cost-coverage` and
`value-ip:analyze`. The person runs those two (ADR-013). `reads_from` and
`after` give the order of work: a brief for an item waits until each item it
comes after is settled.

### A result below `min_version` is refused

`bc.py evidence --from-result` refuses a result file from a map plugin whose
`plugin_version` is older than its plugin's `min_version`, and names the
oldest version the map accepts. A page is never built from a result that an
older plugin wrote, because the result shape and its sources are what the
grade ceiling rests on. The install check uses the same minimum: an
installed plugin below it is `too_old`. The version compare is numeric, part
by part.

### The install check reads Claude Code's own files

`lib/install_check.py` reads the files as Claude Code 2.1.316 writes them:

- `<config>/plugins/installed_plugins.json`, version 2, for each install's
  scope, path and version;
- each scope's settings file, for `enabledPlugins`: managed, then local, then
  project, then user. The first file that holds a plugin's key decides it;
- the marketplace entry's `defaultEnabled`, then the installed plugin's, for
  a key no settings file holds.

The local settings file is `.claude/settings.local.json` at the main
checkout's root. The project settings file is `.claude/settings.json` in the
session's working folder. A worktree's own local settings file is not read.

A local install counts for this project when its `projectPath` equals the
main checkout's root or the worktree's own root. The 2026-11-03 probe
measured why both count: a local install run from a linked worktree records
the worktree's own root, while Claude Code writes the line that turns it on to
the main checkout's `settings.local.json`. Each match is exact. A parent
folder never counts.

### Each plugin gets one state

The check gives each map plugin one state: `available`, `too_old`,
`ambiguous`, `disabled`, `not_installed` or `not_checked`. Only an
`available` plugin's commands are planned. A plan brief names the questions
list of each command of each `available` plugin.

- `too_old` also covers an install that lacks a questions list for a command
  the coach runs.
- `ambiguous` is two keys of one name that are both on, even when only one is
  new enough: both copies load, so the dispatch name does not settle which
  one runs.
- `not_checked` is anything the check cannot read: a file that exists and
  cannot be read, an `installed_plugins.json` of another version, an entry of
  an unknown shape, or a git that fails. It is never read as
  `not_installed`. When the managed settings cannot be read, the result also
  holds the key `managed scope` as `not_checked`.

From Python 3.14, `Path.is_file()`, `is_dir()` and `exists()` read a folder
that cannot be read as absent. That turned an unreadable install into
`too_old`. Every check that must stop on an unreadable path now calls
`os.stat` through `lib/paths.py`, which treats only "not found" as absent and
raises on any other error.

## Alternatives considered

- **Treat an unreadable file as "not installed".** Rejected. The person would
  be told to install a plugin they have, and nothing would name the real
  cause.
- **Read only the working folder's local settings file.** Rejected. The probe
  showed that a local install from a worktree is turned on in the main
  checkout's file.

## Consequences

- A Claude Code release that changes these files can turn every plugin
  `not_checked`. The team then plans no plugin runs, and the coach tells the
  person which plugins it could not check. Nothing is run on a guess.
- A new plugin version that changes its result shape needs a new map file and
  a new `min_version`.
- The person sees `installs` before the first brief, so a missing plugin is
  named before any plan relies on it.
