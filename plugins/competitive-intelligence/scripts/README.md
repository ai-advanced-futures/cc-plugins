# Scripts

This folder holds the Python scripts of the competitive-intelligence plugin.

## Scripts that a prompt runs

Two scripts have a command line. A skill or an agent runs them with `uv`. Each script starts with a PEP 723 block, so `uv` installs its packages when the script starts.

| Script | What it does | Packages |
|---|---|---|
| `result_name.py` | Prints the file name of a result file, or the time of now. | none |
| `vendor_archetype_emitter.py` | Classifies one vendor and writes the artifact and the handoff file. | `jsonschema` |

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vendor_archetype_emitter.py --input .competitive-intelligence/vendor-archetype-input.json --output-dir .
```

## Library modules

The other modules are a library with tests. No prompt runs them. The agents hold the rules that these modules also hold, such as the confidence thresholds (2.5 or more is HIGH, 1.5 or more is MEDIUM, 0.5 or more is LOW, and less is SPECULATIVE).

| Module | What it does |
|---|---|
| `confidence_scoring.py` | Scores and propagates confidence. |
| `triangulation.py` | Compares findings from several sources. |
| `web_research.py` | Helpers for search and fetch results. |
| `workflow_engine.py` | Phase sequence and state. |
| `phase_01_context_discovery.py` to `phase_06_deliverables.py` | Reference models of the phases. |
| `lens_*.py` | Reference models of the six lenses. |
| `plugin_integration.py` | Builds the output schemas for other plugins. |
| `io_manager.py` | Writes the output files. |
| `schema_validator.py` | Checks output files against `schemas/`. |
| `script_generator.py` | Writes the Python scripts of a deliverable. The plugin does not run them. |
| `vendor_archetype_classifier.py` | Classifies the pricing signals of a vendor. |
| `vendor_archetype_input_loader.py` | Loads and checks the input of the classifier. |
| `_jsonschema_formats.py` | Format checks, and the path of `schemas/`. |

## Tests

Install the packages with `pip install -r requirements-dev.txt` in the plugin folder. Then run `pytest tests/ -q -rs`.
