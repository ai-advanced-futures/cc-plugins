# The knowledge graph of {{REPO}}

The subject of this graph is {{SUBJECT}}. It follows the brain standard of the
`knowledge` plugin (`standard/brain-standard.md`).

## Where this lives

- `{{CONTAINER}}bundle/` is the OKF v0.2 bundle. `.claude/knowledge.json`
  names it as the graph `knowledge`.
- `{{CONTAINER}}raw/` holds the raw source files. Never edit a raw file.
  Name a raw file `raw/<date>-<slug>.<ext>`, with the publication date of the
  source.
- The bundle has five page folders: `sources/`, `entities/`, `concepts/`,
  `synthesis/`, and `open-questions/`. A page name is a lowercase slug.
- `manifest.md`, `log.md`, each `index.md`, each `LINKS` block, and
  `links.tsv` are generated. Do not edit them.

## Actors

- `{{HUMAN_ACTOR}}` is the person. Only a person writes `verified`.
- `{{AGENT_ACTOR}}` is the agent that writes pages.
- `process:<id>` is a script, for example `process:adversarial-verifier`.

## Operation: Setup

Run `/knowledge:setup`. It makes the bundle with
`knowledge_graph.py init`, or brings an old bundle to the standard with
`knowledge_graph.py upgrade`.

## Operation: Learn

Run `/knowledge:learn <path or URL>`. The skill reads the whole source,
writes each page with `knowledge_graph.py new`, `set`, `link`, and `body`, and runs
both checks. Each page has `type`, `title`, a one-line `description`,
`status`, and `generated`. A Source page has `resource`. A page that comes
from a source lists it in `sources` as `/sources/<file>.md`. `link` writes each
`sources` entry with `id`, `resource`, `title`, and `last_modified`. A Source page has
the base name of its raw file: `raw/2026-11-02-x.md` gives
`sources/2026-11-02-x.md`.

## Operation: Ask

Run `/knowledge:ask <question>`. It walks the graphs one step at a time with
`knowledge.py walk`, and cites each page that it used. It never writes.

## Operation: Forget

Run `/knowledge:forget <graph>:/<path>`. It shows the full plan
(`knowledge.py forget-plan`) and changes nothing before one yes.

## Operation: Check

The hook of the plugin runs both checks after each change of the bundle. To
run them yourself:

```bash
uv run <knowledge plugin>/scripts/knowledge_graph.py check --strict
uv run <knowledge plugin>/scripts/knowledge.py check --strict
```
