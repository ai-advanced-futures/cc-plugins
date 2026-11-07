# Knowledge

The base of every brain. A brain is a plugin that keeps one kind of project
knowledge as a graph: `product`, `business-domain`, `architecture`, `system-design`, and `knowledge`
(the generic graph). Each brain depends on this plugin.

## Skills

- `/knowledge:setup`: make the generic graph, or migrate an old wiki.
- `/knowledge:learn <path | URL>`: add a source or an accepted answer.
- `/knowledge:ask <question>`: answer from each graph in
  `.claude/knowledge.json`, one step at a time. The Haiku agent
  `knowledge:neighbor-judge` selects the next pages.
- `/knowledge:forget <graph>:/<path>`: remove a page and each reference to
  it, after one yes.
- `knowledge:checking` (hidden): run the brain check and the general check
  after a write.

## The standard

`standard/brain-standard.md` holds the rules of every brain: the bundle, the
page, the schema, the links, the manifest, the skills, the save code, the
checks, the reports, `forget`, and writes to a remote graph.

## Scripts

| Script | Use |
|---|---|
| `scripts/knowledge.py` | `registry`, `fetch`, `resolve`, `show`, `neighbors`, `pages`, `walk`, `check`, `forget-plan`, `remote-checkout`, `remote-publish`. |
| `scripts/knowledge_graph.py` | The save code of the generic graph: `init`, `upgrade`, `move`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, `log`. `body KEY --file PATH [--append]` writes the text of a page above its `LINKS` block (`--file -` reads standard input). `link` adds a `sources` entry with `id`, `resource`, `title`, and `last_modified`, read from the target. `new --slug SLUG` names the page file. A Source page with a `raw/` resource takes the base name of its raw file. |
| `scripts/probe-plugin.sh` | Find another plugin. Each brain has a copy. |
| `scripts/scaffold.py` | Write a new container for `knowledge:setup`. |

Run them with `uv run`. They need `pyyaml` and `jsonschema`.

`--root` takes the path of the platform. On Windows it also takes the Git Bash form (`/c/x`), the Cygwin form (`/cygdrive/c/x`), and a drive path with `/` or `\` (`C:/x`, `C:\x`).

## The hook

After each change of the knowledge graph, the hook runs
`knowledge_graph.py regen`, then `knowledge_graph.py check`, then
`knowledge.py check --graph knowledge --cache-only`.

The hook runs these steps only when a file of the graph changed. It finds the
changed files in the change list that `knowledge_graph.py` writes
(`<git dir>/knowledge-changed`), and in the file of an `Edit` or a `Write`.
After a command that changed no file, the hook gives no output. When a command leaves no list (for example, `git` failed), the hook checks everything and shows every warning, as it did before the list.

The hook shows each `K-size` warning only for a page that changed. It shows
one line with the count of the `K-size` warnings of the other pages, for example
`K-size warnings on pages that did not change: 3.` Each other `WARN` and `SKIP`
line stays.

`KNOWLEDGE_NO_CHANGE_LIST=1` stops `knowledge_graph.py` from writing the change
list.

## Tests

```bash
pip install -r plugins/knowledge/requirements-dev.txt
cd plugins/knowledge && pytest tests/ -q -rs
```
