# UX/HCI Design Schemas

This folder holds the schemas for UX/HCI design heuristics, guidelines, and evaluation frameworks.

## Directory Structure

```
schemas/
├── heuristics/
│   └── nielsen-usability-10.json    # Nielsen's 10 Usability Heuristics (1994)
└── README.md
```

## Nielsen's 10 Usability Heuristics

### Overview

The `nielsen-usability-10.json` schema holds the full text of Jakob Nielsen's 10 Usability Heuristics for User Interface Design (1994).

### Schema Structure

Each heuristic has these parts:

- **Metadata**: The number, the name, and two descriptions (short and detailed).
- **Key Principles**: The core ideas of the heuristic.
- **Evaluation Criteria**:
  - The questions to ask during the evaluation.
  - What to look for in the interface.
- **Common Violations**: Real examples with severity ratings (0-4).
- **Best Practices**: Actions that make the interface comply.
- **Remediation Guidance**:
  - Quick fixes that help at once.
  - Complete solutions that fix the cause.
  - Test methods that check the fixes.

### Severity Scale

The schema uses the 0-4 severity rating of the Nielsen Norman Group:

| Level | Label | Description |
|-------|-------|-------------|
| 0 | No Problem | Not a usability problem at all |
| 1 | Cosmetic | Need not be fixed unless extra time is available |
| 2 | Minor | Fixing this should be given low priority |
| 3 | Major | Important to fix, should be given high priority |
| 4 | Catastrophic | Imperative to fix before product can be released |

### The 10 Heuristics

1. **Visibility of System Status** - Tell users what the system does.
2. **Match Between System and the Real World** - Use the language of the users.
3. **User Control and Freedom** - Let users undo and redo.
4. **Consistency and Standards** - Follow the rules of the platform.
5. **Error Prevention** - Stop problems before they occur.
6. **Recognition Rather Than Recall** - Do not make users remember things.
7. **Flexibility and Efficiency of Use** - Make the interface fast for expert users.
8. **Aesthetic and Minimalist Design** - Remove parts that users do not need.
9. **Help Users Recognize, Diagnose, and Recover from Errors** - Write error messages that help.
10. **Help and Documentation** - Give help that is about the task.

## Validation

### Running the Schema Validator

Run the validator from the folder `plugins/ux-hci-design`:

```bash
python3 scripts/validate_schemas.py
```

The validator checks these things:
- The JSON syntax is valid.
- All required fields exist.
- Each field has the correct type.
- Each severity rating is in the range 0-4.
- The structure is complete.
- The content has good quality.

### Running Unit Tests

```bash
pytest tests/unit/test_nielsen_schema.py -v
```

Run this command from the folder `plugins/ux-hci-design`. The tests check these things:
- The structure of the schema.
- The metadata is complete.
- The severity scale is correct.
- All 10 heuristics exist.
- The field types and the content quality are correct.
- The data is consistent.

## Usage

### Loading the Schema

```python
import json

with open('schemas/heuristics/nielsen-usability-10.json', 'r') as f:
    nielsen_heuristics = json.load(f)

# Access a specific heuristic
heuristic_1 = nielsen_heuristics['heuristics'][0]
print(heuristic_1['name'])  # "Visibility of System Status"

# Access severity scale
severity_levels = nielsen_heuristics['severity_scale']['levels']
```

### Example: Evaluating an Interface

```python
# Iterate through all heuristics
for heuristic in nielsen_heuristics['heuristics']:
    print(f"\n{heuristic['number']}. {heuristic['name']}")

    # Show evaluation questions
    print("\nEvaluation Questions:")
    for question in heuristic['evaluation_criteria']['questions']:
        print(f"  - {question}")

    # Show common violations to look for
    print("\nCommon Violations:")
    for violation in heuristic['common_violations']:
        print(f"  - {violation['issue']} (Severity: {violation['severity']})")
```

## Contributing

When you add or change a schema:

1. Make sure the JSON is valid and has the correct format.
2. Run the validator: `python3 scripts/validate_schemas.py`
3. Run the unit tests: `pytest tests/unit/test_nielsen_schema.py`
4. Describe each new field and structure.
5. If you add a schema, update this README.

## References

- Nielsen, J. (1994). "10 Usability Heuristics for User Interface Design"
- Nielsen Norman Group: https://www.nngroup.com/articles/ten-usability-heuristics/
- Severity Ratings: https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/

## License

This schema is based on the public usability heuristics of Jakob Nielsen. The structure and the detailed content are part of the UX/HCI Design Plugin.
