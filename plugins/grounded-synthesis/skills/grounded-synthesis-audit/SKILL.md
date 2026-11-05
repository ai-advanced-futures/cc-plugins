---
name: grounded-synthesis-audit
description: Audit a synthesis draft against named primary source files (transcripts, briefs, raw artifacts) and find the facts that the sources hold and the draft does not. Use only when the user names a draft file path AND at least one source file path.
---

## Runtime Gate

Continue only when the request has a draft path and 1 or more source paths, and no path holds a quote, `$(`, or a backtick. If one is missing or unsafe, tell the user to run `/grounded-synthesis:audit <draft_path> <source_path> ...`.

Each input must be a file path. A description such as "my notes" is not a path.

## Accepted Source File Types

A source must be `.md`, `.markdown`, `.txt` or `.pdf`. Reject any other type with a clear error. PDF files use `pypdf`; an encrypted PDF or a PDF with bad OCR fails with a message.

## Options

- `--facts N`: facts for each source. Default 12, range [8, 20]. Pass it as `key_facts_per_source`.
- `--output <path>`: path of the gap report. Default: `<draft_path>.grounded-synthesis-report.md`. Pass it as `output_path`.

## Workflow

1. Check the Runtime Gate. Make each path absolute.
2. Use the Agent tool with `subagent_type: grounded-synthesis:grounded-synthesis-orchestrator`. Send `draft_path`, `source_paths`, and the optional `key_facts_per_source` and `output_path`.
3. Show the user the path of the gap report and the one-line coverage summary from the orchestrator.
