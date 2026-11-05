---
description: Audit a draft against primary source files. Extracts facts from each source, checks the draft, and writes a gap report of PRESENT and MISSING facts.
argument-hint: "<draft_path> <source_path> [source_path ...] [--facts N] [--output <path>]"
---

Run the `grounded-synthesis:grounded-synthesis-audit` skill with these arguments: $ARGUMENTS

- `draft_path` (required): the draft file (`.md`, `.markdown`, `.txt` or `.pdf`).
- `source_path` (required, 1 or more): the primary source files (`.md`, `.markdown`, `.txt` or `.pdf`).
- `--facts N` (optional): facts for each source. Default 12, range [8, 20].
- `--output <path>` (optional): path of the gap report. Default: `<draft_path>.grounded-synthesis-report.md`.
