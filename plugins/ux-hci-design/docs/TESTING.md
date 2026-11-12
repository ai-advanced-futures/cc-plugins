# Testing Guide

This guide shows how to run the tests of the UX/HCI Design plugin. It also shows how to add a test.

## Quick Start

Do these steps from the root of the repository.

```bash
# Go to the plugin folder
cd plugins/ux-hci-design

# Install the test tools (Python 3.9 or later)
pip install -r requirements-dev.txt

# Run all tests and show the reason for each skipped test
pytest tests/ -q -rs
```

The suite must show 0 skipped tests. A skipped test means that a test does not check anything. Find the cause and fix it.

---

## Test Structure

All tests are in `tests/unit/`. The folder `tests/` has no other test folder.

```
tests/
├── conftest.py                          # Shared fixtures
├── fixtures/                            # Sample data
│   ├── sample-persona.json
│   ├── sample-evaluation.json
│   ├── sample-jtbd-output.json
│   └── sample-research-findings.json
└── unit/
    ├── test_nielsen_schema.py           # Nielsen schema
    ├── test_rams_schema.py              # Rams schema
    ├── test_norman_schema.py            # Norman schema
    ├── test_wcag_schema.py              # WCAG schema
    ├── test_microsoft_aihci_schema.py   # Microsoft AI-HCI schema
    ├── test_schema_validation.py        # Validation framework
    ├── test_output_schemas.py           # Output schemas
    ├── test_output_schema_design_concept.py
    ├── test_output_schema_wireframe.py
    ├── test_context_detection.py        # Context detection
    ├── test_ux_score_calculation.py     # UX health score
    ├── test_orchestrator.py             # Skill ux-design
    ├── test_empathize_phase.py          # Phase skills
    ├── test_define_phase.py
    ├── test_ideate_phase.py
    ├── test_prototype_phase.py
    ├── test_evaluate_phase.py
    ├── test_phase_transitions.py        # Phase to phase flow
    ├── test_jtbd_bridge.py              # Bridge skills
    ├── test_prd_bridge.py
    ├── test_accessibility_reviewer.py   # Reviewer agents
    ├── test_ai_hci_reviewer.py
    ├── test_usability_reviewer.py
    ├── test_agent_structure.py          # Agent and skill structure
    ├── test_port_rules.py               # Rules of this marketplace
    ├── test_full_workflow.py            # Workflow across components
    ├── test_full_workflow_a11y.py
    ├── test_full_workflow_ai.py
    └── test_full_workflow_consumer.py
```

---

## Running Tests

Run each command from the folder `plugins/ux-hci-design`.

### All Tests

```bash
pytest tests/ -q -rs
```

### Specific Test File

```bash
pytest tests/unit/test_nielsen_schema.py -v
```

### Specific Test Class

```bash
pytest tests/unit/test_nielsen_schema.py::TestHeuristicStructure -v
```

### Specific Test Method

```bash
pytest tests/unit/test_nielsen_schema.py::TestHeuristicStructure::test_all_heuristics_have_names -v
```

### By Name

Use `-k` to select tests by a word in their name.

```bash
# Run only the tests with "wcag" in the name
pytest tests/ -v -k wcag
```

The file `pytest.ini` declares the markers `unit`, `integration`, `schema` and `slow`. No test uses a marker now. Do not select tests with `-m`, because it selects no test.

---

## Test Categories

### Schema Tests

These tests check the schema files in `schemas/`.

**Files:** `test_*_schema.py`, `test_output_schema*.py`, `test_schema_validation.py`

**Examples:**
- The Nielsen schema has 10 heuristics.
- The WCAG schema has the correct level for each criterion.
- The AI-HCI schema has 18 guidelines.

### Skill and Helper Tests

These tests read the files `skills/*/SKILL.md`. The 8 helpers are skills too. They check that the structure and the key rules are present.

**Files:** `test_orchestrator.py`, `test_*_phase.py`, `test_*_reviewer.py`, `test_*_bridge.py`, `test_agent_structure.py`, `test_helper_skills.py`, `test_no_agent_form.py`

**Examples:**
- Each helper has a name, a model, `allowed-tools` and `disallowed-tools`, and `context: fork`.
- Each helper denies the `Agent` tool.
- The skill `ux-design` gives each reviewer its `method_file`.
- Only `ux-prototype-builder` has the `Skill` tool.
- The name of each skill is the name of its folder.

### Script Tests

These tests run the code in `scripts/`.

**Files:** `test_context_detection.py`, `test_ux_score_calculation.py`

**Examples:**
- Context detection finds the project type.
- The score calculation uses the weights of the chosen profile.

### Workflow Tests

These tests use several components together. They are in `tests/unit/` like all other tests.

**Files:** `test_full_workflow*.py`, `test_phase_transitions.py`

**Examples:**
- Schema loading and validation as one chain
- Context detection and configuration generation
- A phase output that the next phase accepts

### Port Rule Tests

The file `test_port_rules.py` holds one test for each rule of this marketplace. For example, the version in `plugin.json` must match the first heading of `CHANGELOG.md`. The example projects must keep their `.ux-config.json` file.

---

## Test Fixtures

### Shared Fixtures (`conftest.py`)

The file `tests/conftest.py` gives these fixtures:

```python
# Folders
plugin_dir, schemas_dir, skills_dir, fixtures_dir

# Loaders
load_schema("heuristics/nielsen-usability-10.json")
load_json(path)
load_skill("ux-design")

# One fixture for each schema
nielsen_schema, rams_schema, norman_schema, wcag_schema, ai_hci_schema
persona_schema, journey_map_schema, evaluation_report_schema, mental_model_schema

# Sample data
sample_persona, sample_evaluation_finding
```

### Sample Data Files

The folder `tests/fixtures/` holds sample data.

**sample-persona.json:**
```json
{
  "schema_version": "1.0",
  "persona": {
    "id": "persona-001",
    "name": "Alex Chen",
    "goals": [...],
    "pain_points": [...],
    "accessibility_needs": {...},
    "ai_interaction_preferences": {...}
  }
}
```

**sample-evaluation.json:**
```json
{
  "schema_version": "1.0",
  "evaluation": {...},
  "summary": {...},
  "findings": [...],
  "framework_scores": {...}
}
```

---

## Writing Tests

### Test Naming Convention

Name each test for what it checks and for the condition.

```python
def test_<what>_<condition>():
    """Test that <what> <does expected behavior> when <condition>."""
    pass

# Examples:
def test_schema_loads_valid_json():
def test_heuristic_has_required_fields():
def test_validation_fails_on_missing_field():
```

### Test Structure (Arrange-Act-Assert)

Write each test in three parts: set up, act, check.

```python
def test_validation_fails_for_invalid_json():
    """Test that validator reports errors for invalid JSON."""
    # Arrange
    validator = SchemaValidator()
    invalid_json_path = Path("tests/fixtures/invalid.json")

    # Act
    is_valid, errors, warnings = validator.validate_schema(invalid_json_path)

    # Assert
    assert not is_valid
    assert len(errors) > 0
    assert "JSON" in errors[0]
```

### Make Each Test Able to Fail

A test must fail when the code is wrong. Follow these rules:

- Do not skip a test. A skipped test counts as a failure of the suite.
- Do not check an empty list. Check first that the list has items.
- Compare with the value in the source file, not with a copy of the wrong value.

---

## Schema Validation Tests

### Testing Knowledge Schemas

```python
class TestNielsenSchema:
    """Tests for Nielsen's 10 Usability Heuristics schema."""

    def test_has_exactly_10_heuristics(self, nielsen_schema):
        """Test that schema contains exactly 10 heuristics."""
        assert len(nielsen_schema["heuristics"]) == 10

    def test_heuristics_numbered_1_to_10(self, nielsen_schema):
        """Test that heuristics are numbered 1-10."""
        numbers = [h["number"] for h in nielsen_schema["heuristics"]]
        assert numbers == list(range(1, 11))

    def test_severity_scale_has_5_levels(self, nielsen_schema):
        """Test that severity scale has levels 0-4."""
        levels = nielsen_schema["severity_scale"]["levels"]
        assert len(levels) == 5
```

### Testing Output Schemas

```python
class TestPersonaSchema:
    """Tests for persona output schema."""

    def test_persona_has_required_fields(self, sample_persona):
        """Test that persona has all required fields."""
        persona = sample_persona["persona"]
        required = ["id", "name", "goals", "pain_points"]
        for field in required:
            assert field in persona

    def test_persona_has_accessibility_needs(self, sample_persona):
        """Test that persona includes accessibility considerations."""
        a11y = sample_persona["persona"]["accessibility_needs"]
        assert "vision" in a11y
        assert "hearing" in a11y
```

---

## Workflow Tests

### Full Workflow Test

```python
class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_evaluation_workflow_simulation(self, fixtures_dir, load_json):
        """Simulate an evaluation workflow end-to-end."""
        # 1. Load evaluation data
        sample_evaluation = load_json(fixtures_dir / "sample-evaluation.json")
        assert sample_evaluation["schema_version"] == "1.0"

        # 2. Extract findings
        findings = sample_evaluation["findings"]
        assert len(findings) > 0

        # 3. Categorize by severity
        critical = [f for f in findings if f["severity"] == 4]
        major = [f for f in findings if f["severity"] == 3]

        # 4. Verify summary matches
        summary = sample_evaluation["summary"]
        assert summary["critical_findings"] == len(critical)
        assert summary["major_findings"] == len(major)
```

### Context Detection Tests

```python
def test_detect_react_project(self, tmp_path):
    """Test detection of React project type."""
    package_json = {
        "name": "react-app",
        "dependencies": {"react": "^18.0.0"}
    }
    (tmp_path / "package.json").write_text(json.dumps(package_json))

    detector = ContextDetector(tmp_path)
    context = detector.detect()

    assert context.type in ["web-app", "enterprise"]
    assert "react" in context.tech_stack
```

---

## Running the Scripts

Run each script with `python3` from the folder `plugins/ux-hci-design`.

### Schema Validation

```bash
# Validate all schemas
python3 scripts/validate_schemas.py

# Validate one schema
python3 scripts/validate_schemas.py --schema schemas/heuristics/nielsen-usability-10.json
```

### Context Detection

```bash
# Detect the context of the current folder
python3 scripts/detect_context.py

# Detect the context of another folder
python3 scripts/detect_context.py --project /path/to/project

# Save the result in .ux-config.json
python3 scripts/detect_context.py --save
```

---

## Before You Open a Pull Request

The CI file of the repository has no job for this plugin. Run the tests on your machine.

```bash
cd plugins/ux-hci-design
pytest tests/ -q -rs
python3 scripts/validate_schemas.py
```

Check that the summary shows 0 skipped tests.

---

## Coverage

The file `requirements-dev.txt` does not include a coverage tool. To measure coverage, install `pytest-cov` first.

```bash
pip install pytest-cov

# Terminal report
pytest tests/ --cov=scripts --cov-report=term-missing

# HTML report
pytest tests/ --cov=scripts --cov-report=html
open htmlcov/index.html
```

---

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -v --tb=long
```

### Print Statements

```bash
pytest tests/ -v -s
```

### Drop into Debugger

```bash
pytest tests/unit/test_file.py::test_name --pdb
```

### Show Locals on Failure

```bash
pytest tests/ -v --tb=short --showlocals
```

---

## Common Issues

### ModuleNotFoundError

If the module is `jsonschema` or `pytest`, install the test tools:

```bash
pip install -r requirements-dev.txt
```

If the module is one of the plugin scripts, go to the plugin folder:

```bash
cd plugins/ux-hci-design
```

### Fixture Not Found

```python
# Put the fixture in tests/conftest.py,
# or import it into the test file.
```

### Tests Not Discovered

```bash
# Check the naming rules:
# Files: test_*.py
# Classes: Test*
# Functions: test_*
```

---

## Adding New Tests

### 1. Create Test File

Put the new file in `tests/unit/`.

```python
# tests/unit/test_new_feature.py
import pytest
from pathlib import Path

class TestNewFeature:
    """Tests for new feature."""

    def test_basic_functionality(self):
        """Test basic functionality works."""
        assert True
```

### 2. Add Fixtures if Needed

```python
# tests/conftest.py
@pytest.fixture
def new_feature_data():
    """Fixture for new feature tests."""
    return {"key": "value"}
```

### 3. Run and Verify

```bash
pytest tests/unit/test_new_feature.py -v
```

Then run the full suite and check that it shows 0 skipped tests.

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite)

---

**Python Version:** 3.9 or later
