# ADR-007: The assumptions input contract

**Status:** Accepted
**Date:** 2026-11-04
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Builds on:** ADR-006, `ADR-006-plugin-result-file.md`
**Plugin:** product-finance v0.10.0

---

## Context

ADR-006 fixed what the plugin writes. This ADR fixes what the market sizing script reads.

`setup` writes `.product-finance/assumptions.json` in the nested shape of `templates/assumptions.json`: `pricing`, `costs`, `market`, `retention` and more. The script `market_sizing_calculator.py` loaded the file straight into its input model, which needs a flat shape. A file that `setup` wrote stopped the script with a wall of validation errors. And `discover` never wrote its own answers into the file before it ran the script. It also never asked for three inputs the script needs: `average_acv`, `gross_margin_pct` and `monthly_churn_pct`. So no person's run got figures from the script. The model worked them out and said so in the `method` text.

## Decision

1. **One loader, two shapes.** The script loads `--assumptions` through one function. It accepts the nested shape, the flat shape, or both in one file. A top-level key wins over a value mapped from the nested shape. A top-level segment wins field by field. A list item that is `null` is dropped.
2. **A nested value is mapped only where it is the same quantity.** The table holds the renamed fields; same-name segment fields pass through: `segment_name`, `acquisition_difficulty`, `willingness_to_pay`, `wtp_source`, `target_acv` and `conversion_rate_pct`.

| Script input | Nested source |
|---|---|
| `tam` | method `stated`, with `total_market_size` set to `market.tam` |
| `sam_filters` | `geographic` set to `market.sam / market.tam` times 100, when both are present and above zero |
| `som_market_share_pct` | `market.som / market.sam` times 100 when both are present and above zero, else `market.competitive_landscape.market_share_target_pct` |
| `monthly_churn_pct` | `retention.monthly_churn_rate_pct` |
| `segments` | `market.target_segments`, merged by segment name with the top-level `segments` |
| segment `potential_customers` | the segment's `size` |

   When a top-level `tam` differs from the one mapped from `market.tam`, neither share is taken from setup: both are shares of setup's TAM. Segment names match when trimmed and with case ignored. When two top-level segments match one setup segment, the later one wins. A dotted name in a message is a key inside a top-level object.
3. **`stated` is a new TAM method.** The TAM is `total_market_size` as written, and the report says it was stated, not worked out. A value mapped from setup is used only when it is a JSON number, not a boolean. This covers `market.tam`, `market.sam`, `market.som`, `market_share_target_pct`, `retention.monthly_churn_rate_pct`, and the size, willingness to pay, ACV and conversion rate of each setup segment. Any other value, a numeric string or a boolean for example, is never used as a figure. Unless a top-level key gives the same input, the script exits with code 3 and names it once, with its source, as in `tam.total_market_size = "5000000000" (market.tam): not a number`. A bad `market.tam` is one line, with no extra `sam_filters` line. A top-level value follows the same rule: a number field takes only a JSON number, and a whole-number field takes only a whole number, so `"10"` or `true` there exits with code 3 and is named.
4. **No invented values.** `average_acv`, `gross_margin_pct`, `som_timeframe_years` and a segment's `target_acv` and `conversion_rate_pct` are taken only when given. `targets.gross_margin_target_pct` is a target, not an actual, so it is not mapped. A `null` counts as not given.
5. **Missing and bad inputs stop the script with exit code 3.** One message lists every problem, each by its input name. A missing input reads `<name>: missing`. A bad value reads `<name> = <value> (<nested source>): <reason>`, with the value as the person wrote it in JSON: a string is in quotes. A bad setup value is named once, with its source. The loader never returns nothing: it returns the inputs or raises one problem list. Code 3 differs from 0 (success), 1 (other errors) and 2 (usage). The reason is one of `missing`, `not a number`, `not a whole number`, `not above 0`, `above <limit>`, `not one of <values>`, `not text`, `not an object` and `not a list`.
6. **`discover` writes before it runs.** In a person's run, `discover` writes the answers of the run into `assumptions.json` as top-level keys, then runs the script. When the person gave no `sam_percent`, Phase 2b's three filter shares are asked as numbers in one call, with the model's estimate as the recommended option, and are written to `sam_filters`. An object the run asked about is written whole; when the run asked `channels`, the channel objects it did not pick are removed. If no file exists, the file holds only flat keys. Other commands then report a missing `pricing` section instead of "not found".
7. **`Calculator run` asks for what the script lists.** On exit code 3, `discover` asks the person for each listed input, writes each answer under the name the script lists, and runs the script once more. An automated run asks nothing and treats the first exit code 3 as a second one. These ask lines carry `[q: none]`: a plugin run reads no `assumptions.json`, so an answer there would have no step that takes it, and `questions/discover.json` stays as it is. A second exit code 3 is not looped. The model works out the figures whose inputs are all present and records each figure it could not work out as a gap, with the inputs still missing in `why`.
8. **Sources.** A value answered in this run is a `person` source, even though it travels through the file. An answer picked from an option labelled as the default or as recommended stays a `default` source. A person source has the ref `asked in this run: <input>`.
9. **The fallback is narrow.** A script exit other than 0 and 3 keeps the model fallback, with the same `method` text as before.

## Consequences

- Flat keys next to nested ones break no other reader. `setup`, `templates/assumptions.json` and `simulator.py` do not change.
- A file that `discover` creates holds only flat keys. Other commands report a missing `pricing` section, not "not found".
- A person who declines `gross_margin_pct` still gets TAM, SAM and SOM.
- `market_sizing_calculator.py` needs only Python's standard library, so `discover` runs it with `uv run` on any machine that has `uv`.
- The script checks its inputs with `scripts/input_check.py`, a standard-library module.
- Known limit: the jtbd integration counts setup segments. This was true before this change.
