# business-domain

The domain model of a repository as one OKF v0.2 bundle. Each bounded context, term,
aggregate, event, relationship, open question, and source is one page. Typed edges join the
pages. A script assigns the IDs, writes the indexes and the reverse links, and checks the
graph. Normal ask questions use the shared evidence reader after a read-only drift check.
Exact relations and unresolved names use the indexes, context pages, source fields, and edge file.

The domain knowledge comes from `ddd-design` 0.2.0 (MIT). See `NOTICE`.

The bundle is a graph on the brain standard of the `knowledge` plugin, a dependency of this
plugin: it has a manifest, a registry entry, and the same output contract as each other brain.

`ask` requires knowledge 2.0.0 or later. A single known read query, including
`regen --check`, leaves the brain hook without extra checks. Other Bash calls run
checks only, including compound and unrecognized commands. The Bash hook never
repairs generated files. Commands that change the graph regenerate their own
output; direct Write/Edit events retain automatic regeneration and both checks.

## Commands

| Command | Does |
|---|---|
| `/business-domain:setup [dir]` | Makes the bundle at `docs/domain/`, or at `dir`, and adds the router block to `CLAUDE.md`. On an existing bundle, it runs `upgrade` in place of `init`. A second run changes no byte. |
| `/business-domain:learn [what to learn]` | Saves one page, or a change to one, through `ddd.py`, then runs both checks. |
| `/business-domain:ask <question>` | Answers from the bundle, and cites each page. It checks drift, then uses `knowledge:ask` first for normal questions. Stale generated files stop the lookup; repair is a separate approved write. Requires knowledge 2.0.0 or later. |

## The script

Run it from the repository root. The skills run it for you.

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py <subcommand>

| Subcommand | Does |
|---|---|
| `init [--dir <dir>]` | Writes `.claude/ddd.json`, `log.md`, the generated parts, `manifest.md`, and the registry entry. |
| `upgrade` | Brings an old bundle to the brain standard: a `generated` stamp on each page that has none, `log.md`, `manifest.md`, and the registry entry. |
| `new <Type> --title <t> --description <d> [--set key=value]` | Writes a page with the next ID. |
| `regen [--check]` | Writes the indexes, the `LINKS` blocks, and `links.tsv`. `--check` writes nothing and names each stale part. |
| `check [--strict]` | The domain linter: rules E1 to E12 and W1 to W6, W8, and W9. |
| `merge <FROM> <INTO> [--by <actor>]` | Points each edge to FROM at INTO, and deprecates FROM. |
| `resolve <ID or alias>` | Prints the path of a page. |
| `log <Setup\|Apply\|Merge> <text> [--by <actor>]` | Adds one line to `log.md`. |
| `set <ID or alias> <key=value>... [--by <actor>]` | Changes fields of a page. It does not change `type`, `generated`, or `protected`. |
| `link <ID or alias> <field> <target> [--by <actor>]` | Adds a typed edge to a page. |
| `unlink <ID or alias> <field> <target> [--by <actor>]` | Removes a typed edge from a page. |
| `remove <ID or alias> [--by <actor>]` | Deletes a page and retires its ID. A protected page stays. Use `merge` to rename a page or to join two pages. |

Exit codes: 0 success, 1 an error in the bundle, 2 wrong input (no bundle, a bad argument).

## The hook

After a direct Write or Edit of a bundle file, the hook runs `ddd.py regen`,
`ddd.py check`, then the general check of the `knowledge` plugin.

For a Bash command that runs `ddd.py`, the hook runs the read-only `regen --check`
and the two checks instead. A known single read can exit before these steps.
Compound and unrecognized calls cannot select the writing regeneration path.
On stale generated files, the hook reports each `STALE:` line, prints a repair
command that requires separate approval, and exits 2 without changing files.
A failed brain check stops before the general check, as with direct file events.

The CLI operations `init`, `upgrade`, `new`, `set`, `link`, `unlink`, `remove`,
`merge`, and writing `regen` already regenerate their output. `log` only appends
to the log and does not repair existing drift. This keeps write checks without
making a read command repair the graph.

The hook does not detect a quoted script path, a script path held in a variable,
or changes made by an external editor. `/business-domain:ask` keeps its initial
`ddd.py regen --check` for changes that the hook does not detect.

## Requirements

- `uv`, or `python3` 3.11 or later with `pyyaml` and `jsonschema`.
- `git`. The hook finds the repository root with it.
- `jq` is optional. The hook uses `python3` when `jq` is absent.

## Development

    cd plugins/business-domain
    pip install -r requirements-dev.txt
    pytest tests/ -q
    bash scripts/gen-schema.sh    # after a change to schema/domain.yaml

The format is in `skills/shared/bundle-schema.md`. The design is in
`docs/superpowers/specs/2026-10-20-ddd-okf-plugin-design.md`.
