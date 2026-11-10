# ADR-008: The shared standard-library input checker

**Status:** Accepted
**Date:** 2026-11-09
**Builds on:** ADR-007, `ADR-007-assumptions-input-contract.md`
**Plugin:** product-finance v0.13.5

---

## Context

`ai_roi_calculator.py` checked its input with `pydantic`, so `uv run` had to get that package before the script could start. A machine that could not get it stopped the script, and the model worked out the figures by hand. A bad value also printed the multi-line text of `pydantic`, which a person could not act on.

ADR-007 moved `market_sizing_calculator.py` to `scripts/input_check.py`, a checker that needs only the standard library of Python. This ADR records the checker as the one tool that both scripts share, so the next script uses it again.

## Decision

1. **`scripts/input_check.py` is the shared standard-library input checker of the plugin.** It checks a dict in the shape of JSON against a dataclass. It gives back the object, or each problem that it found. It needs no installed package.
2. **Five limits, set with `limits(...)`.** They are `gt` (above), `ge` (at least), `le` (at most), `one_of` (a fixed list of text values) and `each` (a limit on each value of a dictionary field). A limit runs after the type check, on the stored value. A field cannot have both `ge` and `gt`. For one value the checker reads `le` first, then `ge`, then `gt`. A `NaN` fails the first limit that the field has; text, `true` and `false` fail the type check first and get `not a number`.
3. **The go-together rule.** A class can name pairs of fields that go together. When a person gives one field of a pair and leaves out the other, the other field gets the reason `needed with <field>`. A pair adds nothing when one of its fields already has a problem. A `null` counts as not given.
4. **Plain reasons.** Each problem has one reason: `missing`, `not a number`, `not a whole number`, `not above N`, `above N`, `below N`, `not one of <values>`, `not text`, `not an object`, `not a list` or `needed with <field>`. The docstring of the module lists them.
5. **Stricter values.** A number written as text is refused. So are `true` and `false` in a number field. `pydantic` accepted both. A script that needs a number reads a JSON number only.
6. **One way to print a problem.** The checker holds `show`, which writes a value as JSON text, and `format_problem`, which writes one line: `<location>: <reason>`, or `<location> = <value>: <reason>` when the problem has a value. `market_sizing_calculator.py` uses `show` and builds its own lines; `ai_roi_calculator.py` prints its lines through `format_problem`.
7. **Exit code 3 for a refused input.** Both scripts exit with code 3. `ai_roi_calculator.py` prints `Error: Invalid input data:` and one line for each problem; `market_sizing_calculator.py` prints `Missing or invalid inputs in <path>:` and its lines. Code 3 is not 0 (success), 1 (other errors) or 2 (usage). A command file reads code 3 as "the inputs were wrong", and writes the input again or records a gap. It does not read code 3 as a crash.
8. **Who uses it.** `market_sizing_calculator.py` and `ai_roi_calculator.py`. `cost_coverage_readout.py` still uses `pydantic`, because it checks the Charter schema.

## Consequences

- The next script that needs input checks uses the module and its tests again. It adds no package.
- `ai-economics` runs its script with `uv run`, with no extra package. A refused input gives a short list of named problems.
- A person who gave a number as text, or `true`, now gets a refusal where `pydantic` gave a figure. This is intentional.
- Known limit: a float field that has no `le` limit passes `Infinity`, as it did under `pydantic`, and a finite value near `1e308` overflows, so the JSON output can hold `NaN`, `Infinity` or `-Infinity`.
