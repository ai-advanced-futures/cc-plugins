# business-domain

The domain model of a repository as one OKF v0.2 bundle. Each bounded context, term,
aggregate, event, relationship, open question, and source is one page. Typed edges join the
pages. A script assigns the IDs, writes the indexes and the reverse links, and checks the
graph. An agent reads the bundle as it reads the `adr`, `wiki`, and `prd` bundles: the
`CLAUDE.md` router, the root index, one context, one page, then the links of that page.

The domain knowledge comes from `ddd-design` 0.2.0 (MIT). See `NOTICE`.

The bundle is a graph on the brain standard of the `knowledge` plugin, a dependency of this
plugin: it has a manifest, a registry entry, and the same output contract as each other brain.

## Commands

| Command | Does |
|---|---|
| `/business-domain:setup [dir]` | Makes the bundle at `docs/domain/`, or at `dir`, and adds the router block to `CLAUDE.md`. On an existing bundle, it runs `upgrade` in place of `init`. A second run changes no byte. |
| `/business-domain:learn [what to learn]` | Saves one page, or a change to one, through `ddd.py`, then runs both checks. |
| `/business-domain:ask <question>` | Answers from the bundle, and cites each page. It runs the drift check first, then hands over to `knowledge:ask` when its own shortcuts do not answer the question. |

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

After each Write or Edit of a file inside the bundle, and after each Bash command that runs
`ddd.py` (a quoted text that names it is not a run), the plugin hook runs `ddd.py regen`, `ddd.py check`, then the general check of the
`knowledge` plugin. An error goes back to the agent with exit code 2. The hook does not see a
`sed` command or an editor outside Claude Code: `/business-domain:ask` runs `ddd.py regen --check` first for
that reason.

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
