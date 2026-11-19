---
name: migrate
description: Preview or copy a Product roadmap into a Beads Plan workspace with stable source identity. Keeps the Product source files unchanged.
argument-hint: "[--source PATH] [--revision COMMIT] [--apply] [--workspace PROFILE]"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Copy a roadmap to Plan

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Preview-first migration and stable source mapping |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Plan item, Criterion, trace, and lifecycle model |

Migration is a copy to the selected Beads store, not a source conversion or a factory switch. A repeated apply reuses source identity. The default command previews the proposed copy.

## Instructions

1. Produce 1 migration preview through Plan using the 2 references, selected workspace, and requested source, with the fixed source revision, fingerprint, proposed mappings, and warnings.
2. For a requested or accepted apply, return 1 verified copy from Plan's `migrate --apply` and `check` commands, bound to the preview's revision and fingerprint, with copied items, criteria, and reused mappings presented under the command reference's user-facing text rule, warnings, errors, and source preservation; otherwise, label the result as preview.
