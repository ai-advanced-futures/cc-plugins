---
name: publish
description: Preview or publish an explicit Plan workspace to its configured GitHub Project through the named board writer. Preserve issue bindings and report partial publication.
argument-hint: "[preview|apply] --workspace PROFILE"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Publish Plan to GitHub Projects

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace and GitHub command forms |
| `${CLAUDE_PLUGIN_ROOT}/references/sharing.md` | Named publisher, shared results, and retry boundaries |

## Instructions

1. Produce one `github preview` from the selected workspace. Report the board, named writer, fingerprint, intended changes, and refusals. Missing board configuration is a setup decision, not permission to select another board.
2. For a requested or accepted apply, use the preview fingerprint and the configured writer through Plan's `github apply`. Report verified bindings and publication status, including partial effects or an uncertain result. Otherwise label the result as preview. Keep Product roadmap files unchanged and do not pull board state into Plan, because publication is one-way from Plan's work state.
