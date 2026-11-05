# System design

The architecture of a repository as one OKF graph on the brain standard of the
`knowledge` plugin (a dependency). The default folder is `docs/system-design/`.

## Skills

- `/system-design:setup`: make the graph, the manifest, the registry entry,
  and the router block.
- `/system-design:learn [area]`: decide the open areas with the person, in
  blocking order. It writes an accepted ADR for each decision that is
  expensive to undo, and migrates `docs/product/system-design.md` after a yes.
- `/system-design:ask <question>`: answer from the design and follow links
  into the PRD, ADR, and domain graphs.

## The save code

`scripts/system_design.py --root <project>`:

| Subcommand | Does |
|---|---|
| `init [--dir D] [--title T]` | Make the bundle, `system.md`, the eight areas, the manifest, the log, and the registry entry. |
| `upgrade [--dir D]` | Bring an existing bundle to the standard. |
| `migrate-file PATH` | Write one page for each item of the old `system-design.md`. |
| `new TYPE --title T --description D` | Make a page with the next ID. |
| `set KEY KEY=YAML...` | Change fields of a page. |
| `link KEY FIELD TARGET [--with K=V]` | Add a typed link. |
| `unlink KEY FIELD TARGET` | Remove a typed link. |
| `remove KEY` | Delete a page and retire its ID. |
| `resolve KEY` | Print the path of a page. |
| `regen [--check]` | Write the indexes, the LINKS blocks, `links.tsv`, and the blocks of `system.md`. |
| `check [--strict]` | Run the brain check: E1 to E17, W1 to W8, and X1 to X7. |
| `log OPERATION TEXT` | Write one `log.md` entry. |

## Tests

```bash
pip install -r plugins/system-design/requirements-dev.txt -r plugins/knowledge/requirements-dev.txt
cd plugins/system-design && pytest tests/ -q -rs
```
