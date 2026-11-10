# grounded-synthesis

Audit a draft against its primary source files. The plugin extracts the key facts of each source, finds the facts that the draft does not cover, and writes a gap report.

## Install

```
claude plugin install grounded-synthesis@cc-plugins
```

The plugin needs [`uv`](https://docs.astral.sh/uv/). The agents run the library scripts with `uv run`, and `uv` installs the Python packages that each script needs (`pypdf`, `jsonschema`).

## Use

```
/grounded-synthesis:audit <draft_path> <source_path> [source_path ...] [--facts N] [--output <path>]
```

You can also ask for the audit in plain words. The skill `grounded-synthesis-audit` runs only when your request names a draft file and at least one source file.

### Inputs

- `draft_path` (required): the draft.
- `source_path` (required, 1 or more): the primary source files. A path must not hold a quote, `$(`, or a backtick. A source must be `.md`, `.markdown`, `.txt` or `.pdf`. Other types are rejected. A PDF that is encrypted or has bad OCR fails with a message.
- `--facts N` (optional): the most key facts for each source. Default 12, range [8, 20]. A source that holds fewer facts gives fewer.
- `--output <path>` (optional): the path of the gap report. Default: `<draft_path>.grounded-synthesis-report.md`, next to the draft.

### How it works

1. The orchestrator checks each source.
2. Wave 1: one `fact-extractor` agent for each source extracts the facts (at most 12 by default, fewer when the source holds fewer) with a place in the source for each fact.
3. The orchestrator checks the fact files.
4. Wave 2: one `coverage-checker` agent for each source judges each fact as `PRESENT` or `MISSING` in the draft. The judgment is about meaning, not about words.
5. `lib/gap_report.py` reads all JSON files and writes the gap report and `handoff.json`.

### Outputs

- The gap report: a Markdown file with a summary, a section for each source, the top missing facts, the facts with no verdict, and the sources that were not analyzed.
- `handoff.json`: the result for a caller (`schema_version: "1"`). It has the status (`ok`, `partial` or `failed`), the fact count that the run used (`invocation.key_facts_per_source`), the path of the gap report, the path of the session folder, and a `warnings` array. The array names each source that the plugin skipped, each source with no fact file or no coverage file, and each fact with no verdict. When the array names a source or a fact, the status is `partial`.
- The session folder: `${GROUNDED_SYNTHESIS_HOME:-$HOME/.cache/grounded-synthesis-sessions}/<session_id>/`. It holds the fact files and the coverage files. It holds facts from your source files. Each run deletes the session folders that are older than 30 days. It deletes only folders with a uuid4 name, and it skips symbolic links.
- A headless run (`claude -p`, default mode) needs the grants `Bash(uv run:*)`, `Write` and `Read`, because the session folder is outside the project. With fewer grants, the audit writes no report.

## Start the audit from an agent

An agent starts `grounded-synthesis:grounded-synthesis-orchestrator` with the `Agent` tool. The agent sends these fields (the full contract is in [ADR-007](docs/adr/ADR-007-caller-contract.md)):

| Field | Required | Meaning |
|---|---|---|
| `draft_path` | yes | Absolute path of the draft. |
| `source_paths` | yes | List of absolute paths of 1 or more source files. |
| `key_facts_per_source` | no | Default 12. The orchestrator clamps it to [8, 20]. |
| `output_dir_override` | no | Absolute path. `gap-report.md` and `handoff.json` go to this folder (`--output-dir-override` of `lib/gap_report.py`). |
| `output_path` | no | Path of the gap report. |

If `draft_path` or `source_paths` is missing, the orchestrator writes no file and ends with `DONE: grounded-synthesis FAILED: draft_path and source_paths are required`. On success it ends with `DONE: grounded-synthesis`.

## Verdicts

The only verdicts are `PRESENT` and `MISSING`.

## Develop

Run the tests from this folder:

```
pip install -r requirements-dev.txt
pytest tests/ -q -rs
```

All tests must pass with no skip. The job `grounded-synthesis` of `.github/workflows/ci.yml` runs the same steps. More documents are in [docs/INDEX.md](docs/INDEX.md). The changes are in [CHANGELOG.md](CHANGELOG.md).

## License

The Apache License of the repository applies (see the root `LICENSE`). The MIT notice of the source plugin is in [NOTICE](NOTICE).
