# Troubleshooting Guide

This guide lists common problems of the UX/HCI Design plugin and their solutions.

---

## Installation Issues

### Plugin Not Found

**Symptom:** `claude plugin install ux-hci-design@cc-plugins` fails with "plugin not found"

**Solutions:**

1. Add the marketplace:
   ```bash
   claude plugin marketplace add ai-advanced-futures/cc-plugins
   ```

2. Install the plugin again. Write the name in lowercase:
   ```bash
   claude plugin install ux-hci-design@cc-plugins
   ```

3. Update the marketplace cache:
   ```bash
   claude plugin marketplace update
   ```

---

### Python Version Issues

**Symptom:** Scripts fail with syntax errors or import failures

**Solutions:**

1. Check the Python version. The plugin needs Python 3.9 or later:
   ```bash
   python3 --version
   ```

2. Use `python3` and not `python`. Run the script from the plugin folder:
   ```bash
   cd plugins/ux-hci-design
   python3 scripts/validate_schemas.py
   # Not: python scripts/validate_schemas.py
   ```

3. Make a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

---

### Missing Dependencies

**Symptom:** `ModuleNotFoundError: No module named 'pytest'` or `No module named 'jsonschema'`

**Solution:** Install the test tools from the plugin folder.

```bash
cd plugins/ux-hci-design
pip install -r requirements-dev.txt
```

---

## Schema Validation Issues

### Unknown Schema Type

**Symptom:** The validator reports "Unknown schema type"

**Cause:** The schema has none of the fields that the validator uses to find the type.

**Solutions:**

1. Check that the schema has the identifying fields of its type:
   - Nielsen: `heuristics` array and `severity_scale`
   - Rams: `principles` array with `original_german`
   - Norman: `principles` array with a principle named `Affordances`
   - WCAG: `conformance_levels`, or a title that starts with `WCAG`
   - AI-HCI: `guidelines` array and `organization` set to `Microsoft Research`
   - AI paradigm: `paradigm_shift` or `thought_leader`
   - Output: `$schema` field with a JSON Schema URL

2. The validator uses the file name only when no field matches. The folder of the file does not matter.

3. For an output schema, add the `$schema` field:
   ```json
   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "title": "My Output Schema",
     ...
   }
   ```

---

### Invalid JSON Syntax

**Symptom:** `JSONDecodeError: Expecting property name`

**Solutions:**

1. Remove each trailing comma. JSON does not allow it:
   ```json
   // Wrong
   {
     "key": "value",  // <-- trailing comma
   }

   // Correct
   {
     "key": "value"
   }
   ```

2. Use double quotes. JSON does not allow single quotes:
   ```json
   // Wrong
   {'key': 'value'}

   // Correct
   {"key": "value"}
   ```

3. Find the line of the error:
   ```bash
   python3 -m json.tool file.json
   ```

---

### Missing Required Fields

**Symptom:** Validation error "Missing required field 'X'"

**Solutions:**

1. Read the schema for the list of required fields.
2. Compare the file with an existing valid file.
3. Use a sample fixture as a template:
   ```bash
   cat tests/fixtures/sample-persona.json
   ```

---

## Test Failures

### Tests Not Found

**Symptom:** `collected 0 items`

**Solutions:**

1. Check the file names. They must be `test_*.py`, in `tests/unit/`:
   ```bash
   ls tests/unit/test_*.py
   ```

2. Check the function names. They must start with `test_`:
   ```python
   def test_something():  # Correct
   def something_test():  # Not discovered
   ```

3. Check the class names. They must start with `Test`:
   ```python
   class TestFeature:  # Correct
   class FeatureTests:  # Not discovered
   ```

4. Do not select tests with `-m`. No test has a marker, so `-m` selects nothing.

---

### Skipped Tests

**Symptom:** The summary shows skipped tests

**Solutions:**

1. Show the reason for each skip:
   ```bash
   pytest tests/ -q -rs
   ```

2. Fix the cause. The suite must show 0 skipped tests.

---

### Import Errors in Tests

**Symptom:** `ModuleNotFoundError: No module named 'validate_schemas'`

**Solutions:**

1. Run the tests from the plugin folder:
   ```bash
   cd plugins/ux-hci-design
   pytest tests/ -q -rs
   ```

2. Add the scripts folder to the path in the test file:
   ```python
   # In test file
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
   ```

---

### Fixture Not Found

**Symptom:** `fixture 'sample_persona' not found`

**Solutions:**

1. Check that the fixture is in `tests/conftest.py`.
2. Check that `conftest.py` is in the `tests/` folder.
3. Check the spelling of the fixture name.

---

### Assertion Errors

**Symptom:** A test fails with `AssertionError`

**Solutions:**

1. Run the test with more detail:
   ```bash
   pytest tests/ -v --tb=long
   ```

2. Show the values of the local variables:
   ```bash
   pytest tests/ -v --showlocals
   ```

3. Start the debugger at the failure:
   ```bash
   pytest tests/unit/test_file.py::test_name --pdb
   ```

---

## Context Detection Issues

### Wrong Project Type Detected

**Symptom:** The script detects the wrong project type (for example "enterprise" and not "web-app")

**Cause:** The script weighs several signals, and they point to different types.

**Solutions:**

1. Make a config file and set the correct type in it:
   ```bash
   python3 scripts/detect_context.py --save
   # Edit .ux-config.json to set correct type
   ```

2. Show the signals that the script found:
   ```bash
   python3 scripts/detect_context.py --verbose
   ```

---

### Context Detection Is Slow

**Symptom:** `detect_context.py` takes a long time

**Cause:** The project folder is large or has a deep folder structure.

**Solutions:**

1. Point the script at the smaller source folder:
   ```bash
   python3 scripts/detect_context.py --project path/to/src
   ```
2. Check the project for symbolic link loops.
3. Set a time limit:
   ```bash
   timeout 30 python3 scripts/detect_context.py
   ```

---

## Runtime Issues

### Skill Not Invoked

**Symptom:** `/ux-hci-design:ux-design` does not start the skill

**Solutions:**

1. Check that the plugin is installed:
   ```bash
   claude plugin list
   ```

2. Check that the file `skills/ux-design/SKILL.md` exists.
3. Install the plugin again:
   ```bash
   claude plugin uninstall ux-hci-design
   claude plugin install ux-hci-design@cc-plugins
   ```

4. Write the full name. A command without the plugin name does not work. The plugin has 13 skills for a person. Each one is `/ux-hci-design:<skill>`.

---

### Helper Not Found

**Symptom:** The start of a helper fails because the skill does not exist, or an `Agent` call with `ux-hci-design:<name>` finds no agent

**Solution:** Start a helper only with the `Skill` tool, and use the full name `ux-hci-design:<helper>`. A bare name finds no skill. The plugin has no agent files since version 1.8.0. The 8 helpers are `ux-researcher`, `ux-artifact-generator`, `ux-concept-designer`, `ux-prototype-builder`, `ux-evaluator`, `accessibility-reviewer`, `usability-reviewer`, and `ai-hci-reviewer`.

---

### A Helper Wants an Answer

**Symptom:** A phase ends with the file `<output_dir>/open-questions.md`

**Cause:** A helper cannot ask the person a question. When it needs an answer, it writes its open questions to this file and returns.

**Solution:** Let the skill `ux-design` ask these questions. It removes the file with `ux_graph.py remove-questions`, and starts the same helper again with your answers. If you started the helper from another skill, answer the questions, remove the file, and start the helper again. An old file starts the same questions again.

---

### The Skill Asks for the Project Context Each Time

**Symptom:** The skill `ux-design` asks the context questions in every session

**Cause:** The project folder has no `.ux-config.json` file.

**Solution:** Make the file. When it exists, the skill reads it and asks no context question.

```bash
python3 scripts/detect_context.py --project path/to/project --save
```

---

### Slow Performance

**Symptom:** Operations take too long

**Solutions:**

1. Validate one schema and not all schemas:
   ```bash
   python3 scripts/validate_schemas.py --schema schemas/heuristics/nielsen-usability-10.json
   ```

2. Run the performance tests to get a baseline:
   ```bash
   pytest tests/ -v -k "performance"
   ```

---

## Output Issues

### Malformed JSON Output

**Symptom:** The generated JSON is not valid

**Solutions:**

1. Validate the output against the schema:
   ```python
   import jsonschema
   import json

   with open('schemas/outputs/persona-schema.json') as f:
       schema = json.load(f)
   with open('output.json') as f:
       data = json.load(f)

   jsonschema.validate(data, schema)
   ```

2. Compare the output with the sample fixtures.

---

### Missing Schema Version

**Symptom:** The output has no `schema_version` field

**Solution:** Always include the schema version:
```json
{
  "schema_version": "1.0",
  "persona": {...}
}
```

---

## Platform-Specific Issues

### macOS

**Symptom:** The `python` command is not found

**Solution:** Use `python3`:
```bash
pytest tests/
```

### Windows

**Symptom:** Path separators cause errors

**Solution:** Use `pathlib.Path` for paths that work on all systems:
```python
from pathlib import Path
schema_path = Path("schemas") / "heuristics" / "nielsen.json"
```

### Linux

**Symptom:** The system refuses to run a script (error "denied")

**Solution:** Make the scripts executable:
```bash
chmod +x scripts/validate_schemas.py
chmod +x scripts/detect_context.py
```

---

## Getting Help

### Diagnostic Information

When you report a problem, include this information:

1. **Python version:**
   ```bash
   python3 --version
   ```

2. **Plugin version:**
   ```bash
   grep version plugins/ux-hci-design/.claude-plugin/plugin.json
   ```

3. **Test output:**
   ```bash
   pytest tests/ -q -rs 2>&1 | head -50
   ```

4. **Schema validation:**
   ```bash
   python3 scripts/validate_schemas.py --verbose
   ```

### Reporting Issues

Open an issue at: https://github.com/ai-advanced-futures/cc-plugins/issues

Include this information:
- A clear description of the problem
- The steps to repeat it
- The expected result and the actual result
- The diagnostic information above
- The error messages

---

## Quick Reference

| Problem | First Try |
|---------|-----------|
| Import error | `cd plugins/ux-hci-design` first |
| Tests not found | Check the `test_` prefix |
| Skipped tests | `pytest tests/ -q -rs` |
| Schema invalid | Run `validate_schemas.py` |
| Wrong project type | Make `.ux-config.json` with `--save` |
| Skill not working | `claude plugin list` |
