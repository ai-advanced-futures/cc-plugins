# ADR-008: The shared standard-library input checker

**Status:** Accepted
**Date:** 2026-11-09
**Builds on:** ADR-007, `ADR-007-assumptions-input-contract.md`
**Plugin:** product-finance v0.13.5, amended in v0.13.6, v0.13.7 and v0.14.0

---

## Context

`ai_roi_calculator.py` checked its input with `pydantic`, so `uv run` had to get that package before the script could start. A machine that could not get it stopped the script, and the model worked out the figures by hand. A bad value also printed the multi-line text of `pydantic`, which a person could not act on.

ADR-007 moved `market_sizing_calculator.py` to `scripts/input_check.py`, a checker that needs only the standard library of Python. This ADR records the checker as the one tool that both scripts share, so the next script uses it again. The amendment in v0.13.6 moved `unit_economics.py` and `rule_of_40.py` to it, and made it refuse a number that is not finite. The amendment in v0.13.7 moved the input read and the refusal that the 3 calculator scripts shared into the checker, and made a `null` in a field with a default take the default. The amendment in v0.14.0 gave the `null` of a required field its own reason, and rewrote the known limit for a figure above the float range.

## Decision

1. **`scripts/input_check.py` is the shared standard-library input checker of the plugin.** It checks a dict in the shape of JSON against a dataclass. It gives back the object, or each problem that it found. It needs no installed package. It also holds the read and the refusal that the 3 calculator scripts share: `read_json_input` reads the JSON from `--input` or stdin and exits with code 1 on a read or JSON error; `checked_input` checks it and exits with code 3 on a refused input; `EXIT_INPUTS` is that 3. `market_sizing_calculator.py` uses only `EXIT_INPUTS`.
2. **Five limits, set with `limits(...)`.** They are `gt` (above), `ge` (at least), `le` (at most), `one_of` (a fixed list of text values) and `each` (a limit on each value of a dictionary field). A limit runs after the type check, on the stored value. A field cannot have both `ge` and `gt`. For one value the checker reads `le` first, then `ge`, then `gt`. Text, `true` and `false` fail the type check first and get `not a number`. A `NaN`, `Infinity` or `-Infinity` in a number field fails next and gets `not a finite number`, so no limit sees it. This holds also for each value of a dictionary field and each item of a list.
3. **The go-together rule.** A class can name pairs of fields that go together. When a person gives one field of a pair and leaves out the other, the other field gets the reason `needed with <field>`. A pair adds nothing when one of its fields already has a problem. A `null` counts as not given: a field with a default takes its default, a required field gets `null, a value is required`, and the go-together rule counts it as not given.
4. **Plain reasons.** Each problem has one reason: `missing`, `null, a value is required`, `not a number`, `not a finite number`, `not a whole number`, `not above N`, `above N`, `below N`, `not one of <values>`, `not text`, `not an object`, `not a list` or `needed with <field>`. The docstring of the module lists them.
5. **Stricter values.** A number written as text is refused. So are `true` and `false` in a number field. `pydantic` accepted both. A script that needs a number reads a JSON number only.
6. **One way to print a problem.** The checker holds `show`, which writes a value as JSON text, and `format_problem`, which writes one line: `<location>: <reason>`, or `<location> = <value>: <reason>` when the problem has a value. `market_sizing_calculator.py` uses `show` and builds its own lines; `ai_roi_calculator.py`, `unit_economics.py` and `rule_of_40.py` print their lines through `format_problem`.
7. **Exit code 3 for a refused input.** Each script that uses it exits with code 3. `ai_roi_calculator.py`, `unit_economics.py` and `rule_of_40.py` print `Error: Invalid input data:` and one line for each problem; `market_sizing_calculator.py` prints `Missing or invalid inputs in <path>:` and its lines. Code 3 is not 0 (success), 1 (other errors) or 2 (usage). A command file reads code 3 as "the inputs were wrong", and writes the input again or records a gap. It does not read code 3 as a crash.
8. **Who uses it.** `market_sizing_calculator.py`, `ai_roi_calculator.py`, `unit_economics.py` and `rule_of_40.py`. `instrumentation_analyzer.py` still uses `pydantic`, and so does `cost_coverage_readout.py`, because it checks the Charter schema.

## Consequences

- The next script that needs input checks uses the module and its tests again. It adds no package.
- `ai-economics` runs its script with `uv run`, with no extra package. A refused input gives a short list of named problems.
- `unit_economics.py` and `rule_of_40.py` run with `uv run`, with no extra package. No command runs them. A person can run them by hand.
- A person who gave a number as text, or `true`, now gets a refusal where `pydantic` gave a figure. This is intentional.
- A `null` in a field with a default, such as `period_months`, now runs with the default and exits 0. Before, it exited with code 3. This is intentional.
- Known limit: an input that is finite can still produce a figure above the float range. AI ROI, unit economics and Rule of 40 compute exactly and print `Infinity` or `-Infinity` in the JSON for such a figure, never `NaN`. Market sizing computes in floats and can still print `NaN`, `Infinity` or `-Infinity`.
