# ADR-009: Exact figures, rounded half away from zero at output only

**Status:** Accepted
**Date:** 2026-11-09
**Plugin:** product-finance v0.14.0

---

## Context

The unit economics, Rule of 40 and AI ROI scripts computed in binary floats, and rounded with `round()` or a format spec. Two faults followed.

1. **A band could be wrong at its edge.** A value that is exactly on a band edge could land just below it in float. A Rule of 40 score of exactly 40 (growth 64.1, margin -24.1) got `good`, with the line "Improve score by 0 points".
2. **A printed figure could be one cent short.** A probe over 300 inputs with cents found that CAC printed `4,170.81` for an exact 4,170.815 in 17 of them. The weighted Rule of 40 printed `63.1` for an exact 63.15. `round()` rounds half to even on each version of Python, and a float such as 4170.815 is stored just below the half.

Decision D-544 chose exact math until output for each printed figure of these 3 scripts.

## Decision

1. **Read each input as written.** `scripts/utils/exact.py` has `as_written`: a float becomes the `Fraction` of its shortest decimal text, so `0.1` reads as 1 tenth. An int stays exact. A NaN or an infinity raises `ValueError`. A `-0.0` reads as 0.
2. **Compute in `Fraction`.** Each formula and each comparison of the 3 scripts works on `Fraction` values and exact literals, such as `Fraction("1.33")`. Result fields hold the `Fraction`.
3. **Round half away from zero, only at output.** `shown(x, places)` rounds in integers and returns a `Decimal` with exactly `places` digits. JSON gets `float(shown(x, places))`. Markdown formats the `Decimal`. Each figure keeps the places that it printed before. No code rounds a figure before a band compares it.
4. **Above the float range.** `as_float` is `float()` that gives `Infinity` or `-Infinity` with the sign of the value, where `float()` of a large `Fraction` raises. JSON prints `Infinity` or `-Infinity` for such a figure, never `NaN`. Markdown prints its full digits.
5. **The format rule.** No output site formats a `Fraction` or calls `round()`, because `round()` rounds half to even and a format spec such as `:.2f` raises `TypeError` on a `Fraction` on some versions of Python. Tests hold this rule:
   - a source guard reads the syntax trees of the scripts. It refuses `round()`, a numeric format spec that `shown` does not feed at the same places, and a `float()` that does not wrap `shown`, outside a listed set of raw sites;
   - an in-process test replaces the `fractions.Fraction` class with a class whose formatting raises, and runs each script path;
   - a type test checks that result fields hold `Fraction` values;
   - a table pins the places of each JSON figure to what it printed before.
6. **Out of scope.** The market sizing script still computes in floats and can still print `NaN`, `Infinity` or `-Infinity`.

## Consequences

- A value on a band edge gets the band that the edge belongs to, and a printed figure is its exact value rounded half away from zero. In 0.14.0 this changed CAC, the weighted Rule of 40 in 11 sample cases, LTV:CAC in 1 case, and a Magic Number tie at 0.125, which now prints `0.13`.
- Each changed sample file was set by hand, from the formula, before the script ran on it.
- A new figure must go through `as_written` and `shown`, or the source guard fails. A new JSON figure must also have a row in the places table.

## Amendment in v0.15.0

The new JSON keys of 0.15.0 take 2 places by decision, and no new key prints `-0.0`.
