# Schema Validation Guide

This guide explains how to use the schema validator. The validator checks that each UX/HCI schema has the correct structure and all its parts.

Run each command in this guide from the folder `plugins/ux-hci-design`.

## Quick Start

### Validate All Schemas

```bash
cd plugins/ux-hci-design
python3 scripts/validate_schemas.py
```

**Output:**
```
Found 5 schema(s) to validate
================================================================================

Validating: schemas/heuristics/nielsen-usability-10.json
--------------------------------------------------------------------------------
  ✅ PASSED

...

================================================================================
SUMMARY:
  Total schemas:  5
  ✅ Passed:      5
  ❌ Failed:      0

🎉 All schemas validated successfully!
```

### Validate Specific Schema

```bash
python3 scripts/validate_schemas.py --schema schemas/heuristics/nielsen-usability-10.json
```

### Get Help

```bash
python3 scripts/validate_schemas.py --help
```

## Supported Schema Types

The validator finds the type of each schema by itself. It validates these types:

1. **Nielsen's 10 Usability Heuristics** (`nielsen-usability-10.json`)
2. **Rams' 10 Principles of Good Design** (`rams-good-design-10.json`)
3. **Norman's Interaction Design Principles** (`norman-interaction-principles.json`)
4. **WCAG 2.2 Accessibility Guidelines** (`wcag-2.2-criteria.json`)
5. **Microsoft's 18 AI-HCI Guidelines** (`microsoft-guidelines-18.json`)

## Validation Rules

### Nielsen Schema

**Required Fields:**
- `title`, `description`, `version`, `author`, `year`, `source`
- `severity_scale` with levels 0-4
- `heuristics` array with exactly 10 items

**Each Heuristic Must Have:**
- `number` (1-10, unique)
- `name`, `short_description`, `detailed_description`
- `key_principles` (array)
- `evaluation_criteria` with `questions` and `what_to_look_for`
- `common_violations` with `issue`, `example`, `severity`
- `best_practices` (array)
- `remediation_guidance` with `quick_fixes`, `comprehensive_solutions`, `testing_approach`

### Rams Schema

**Required Fields:**
- `title`, `description`, `version`, `author`, `year`
- `principles` array with exactly 10 items

**Each Principle Must Have:**
- `number` (1-10, unique)
- `name`, `original_german`, `short_description`, `detailed_description`
- `key_principles` (array)
- `evaluation_criteria` with `questions`
- `common_violations` with `issue`, `example`, `impact`
- `best_practices` (array)

### Norman Schema

**Required Fields:**
- `title`, `description`, `version`, `author`
- `principles` array (minimum 5)

**Each Principle Must Have:**
- `number` (unique)
- `name`, `short_description`, `detailed_description`
- `key_principles`, `evaluation_criteria`, `common_violations`, `best_practices`

**Optional Fields (the validator checks them if they exist):**
- `interaction_framework` with `seven_stages_of_action`

### WCAG Schema

**Required Fields:**
- `title`, `description`, `version`
- `conformance_levels` with `A` and `AA`
- `principles` array with 4 items

**Each Principle Must Have:**
- `code`, `name`, `description`
- `guidelines` array with `success_criteria`

**Each Success Criterion Must Have:**
- `number`, `name`, `level` (A, AA, or AAA)
- `description`, `techniques`, `test_procedures`

### AI-HCI Schema

**Required Fields:**
- `title`, `description`, `version`, `organization` (Microsoft Research)
- `guidelines` array with exactly 18 items

**Each Guideline Must Have:**
- `guideline_number` (1-18, unique)
- `guideline_name`, `category`, `interaction_phase`
- `description`, `evaluation_criteria`

**Valid Categories:**
- Initially
- During interaction
- When wrong
- Over time

## Running Tests

### Run All Tests

```bash
python3 -m pytest tests/
```

### Run Only Validation Framework Tests

```bash
python3 -m pytest tests/unit/test_schema_validation.py -v
```

### Run Test Suite Directly

Run pytest without the `python3 -m` prefix:

```bash
pytest tests/unit/test_schema_validation.py
```

## Error Messages

Each error message names the problem and its place:

### Example: Missing Required Field

```
ERROR: Heuristic at index 3: Missing required field 'remediation_guidance'
```

### Example: Invalid Data Type

```
ERROR: Heuristic at index 5: 'number' must be an integer
```

### Example: Structural Issue

```
ERROR: Expected 10 heuristics, found 8
```

### Example: Duplicate Detection

```
ERROR: Heuristic at index 7: Duplicate heuristic number 5
```

## Integration with Development Workflow

### Pre-Commit Validation

Add this script to your pre-commit hook:

```bash
#!/bin/bash
cd plugins/ux-hci-design
python3 scripts/validate_schemas.py || exit 1
```

### CI/CD Integration

Add this step to your CI pipeline:

```yaml
- name: Validate Schemas
  run: |
    cd plugins/ux-hci-design
    python3 scripts/validate_schemas.py
```

### Editor Integration

To validate while you edit, run this loop:

```bash
# Watch for changes and validate
while inotifywait -e modify schemas/**/*.json; do
  python3 scripts/validate_schemas.py
done
```

## Extending the Validator

### Adding New Validation Rules

1. Add a validation method to the `SchemaValidator` class:

```python
def _validate_new_field(self, data: Dict[str, Any], context: str) -> None:
    """Validate a new field."""
    if 'new_field' not in data:
        self.errors.append(f"{context}: Missing 'new_field'")
```

2. Call the method from the correct schema validator:

```python
self._validate_new_field(heuristic, f"Heuristic {idx}")
```

### Adding New Schema Type

1. Add a detection rule to `_detect_schema_type`:

```python
if 'unique_identifier' in schema:
    return "new_type"
```

2. Add a validation method:

```python
def validate_new_type_schema(self, schema_path: Path) -> Tuple[bool, List[str], List[str]]:
    # Validation logic here
    pass
```

3. Add a case to the `validate_schema` method:

```python
elif schema_type == "new_type":
    return self.validate_new_type_schema(schema_path)
```

## Best Practices

1. **Validate Early and Often**: Run the validator after each schema change.
2. **Fix Errors First**: Fix errors before you fix warnings.
3. **Read the Context**: Each error message names the place of the problem, for example "Heuristic at index 3".
4. **Test Changes**: Run the full test suite after each schema change.
5. **Version Control**: Commit only schemas that pass the validator.

## Troubleshooting

### Validator Not Found

```bash
# Ensure you're in the correct directory
cd plugins/ux-hci-design

# Or use absolute path
python3 /path/to/plugins/ux-hci-design/scripts/validate_schemas.py
```

### Import Errors

```bash
# Ensure Python 3 is installed
python3 --version

# Install pytest if running tests
pip3 install pytest
```

### Schema Type Not Detected

If the validator does not find the type of your schema:
1. Make sure the schema has the fields that identify its type.
2. Make sure the file name follows the naming rules.
3. If needed, add a detection rule for the type.

## Support

If you have a problem or a question:
1. Read this guide.
2. Read the error messages with care.
3. Run the tests to make sure the validator works: `pytest tests/unit/test_schema_validation.py`
4. Read the schema examples in the repository.

---

**Last Updated**: 2026-01-23
**Validator Version**: 1.0.0
**Tested With**: Python 3.9+
