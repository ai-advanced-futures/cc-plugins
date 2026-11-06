# ADR-008 — Plugin rename and command names

**Status:** Accepted
**Date:** 2026-03-31
**Deciders:** The authors of the plugin

> **Note on the port.** This ADR first recorded the rename of `architect` to `architecture` and a short alias `arch:` for the skills. The plugin now has the name `architecture-assess`, because this marketplace already has a plugin `architecture` that stores decisions. The commands are `/architecture-assess:<folder>`, where `<folder>` is the folder name of the skill. The decision below keeps its reason and gives the current names.

---

## Context

The plugin was originally named `architect`, an action word that implied the plugin was a person
or a verb rather than a domain. This created two naming issues:

1. **Plugin-level naming:** `architect` reads as "someone who architects" — an agent role — not as
   a domain of knowledge. Plugin names should represent the domain while skills
   represent the action (`assess`, `design`).

2. **Command-surface verbosity:** All skills and commands used the full `architect:` prefix (13 chars).
   This cluttered the `/` autocomplete grouping and the `Skill("architect:...")` invocation surface.
   A shorter alias was unambiguous, but it was a second name for the same plugin.

---

## Decision

### 1. Plugin rename: `architect` → `architecture` → `architecture-assess`

- The first rename gave a domain name: `architect` → `architecture`.
- The port to this marketplace gives the final name: `architecture-assess`. The reason is that the plugin `architecture` of this marketplace stores decisions, and the two plugins must not share a name.
- `plugin.json` name field: `"architecture-assess"`
- All agent `name:` frontmatter fields are the file stem, with no colon. An agent is dispatched as `architecture-assess:<agent file stem>`.
- The agent returns a `DONE:` line, for example `DONE: orchestrator — adr_draft=<path>`.

### 2. Skill command surface: the folder name

Each skill has no `name:` key. The name of a skill is the name of its folder. Claude Code adds the
plugin name, so the command that a user types is `/architecture-assess:<folder>`.

| Surface | Value |
|---------|-------|
| `plugin.json` name | `architecture-assess` |
| Skill `name:` | none (the folder name) |
| Agent `name:` | the file stem |
| Install command | `claude plugin install architecture-assess@cc-plugins` |
| Invocation | `/architecture-assess:assess`, `/architecture-assess:review`, and so on |

The 12 commands are `assess`, `design`, `review`, `aiml`, `cicd`, `data-mesh`, `observability`,
`testing`, `infrastructure`, `agentic-plugin`, `sdlc`, and `cost-class-review`.

### 3. Router skill deleted

A redundant router skill, which duplicated the entry point, was deleted. The 12 skills
are the user-facing entry points.

---

## Consequences

**Positive:**
- Plugin name correctly describes a domain, not an action
- The plugin has one name, so there is no second alias to learn
- Removes the redundant router skill (one fewer SKILL.md to maintain)

**Negative / migration notes:**
- Any caller that dispatches `subagent_type: architect:orchestrator` must update to
  `subagent_type: architecture-assess:orchestrator`
- The `architecture-visualizer` plugin (a different plugin) is unaffected

---

## Related

- ADR-001 through ADR-007 — architectural decisions for the plugin's internal design
