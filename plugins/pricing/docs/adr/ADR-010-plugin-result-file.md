# ADR-010: Adopt the plugin result file

**Status:** Accepted
**Date:** 2026-11-01. Rewritten for the marketplace port (2026-11-06).
**Adopts:** ADR-001 of the plugin result file standard (`tests/support/PLUGIN_RESULT_FILE.md`)

---

## Context

A reader of the producer plugins needs one shape. Until now, this plugin wrote `.pricing/pricing-recommendation.json` in its own shape, and a reader could not tell a price built on customer data from one built on the plugin's own constants. The plugin result file standard (`tests/support/PLUGIN_RESULT_FILE.md`) fixes one shape, the rules R1 to R7, and the invocation block a coach uses. One command of this plugin is on its list of adopting commands: `pricing:price`.

Four facts shaped the adoption:

1. The command's text is the price skill, `skills/price/SKILL.md` and `price.md`. A spike showed that `agents/new-offering-pricer.md`, dispatched directly, never read those files.
2. The price skill reads constants from `config/defaults.json` and falls back to built-in values when the person gives no answer.
3. Path A builds on a jtbd result. A change to the gate decided how the skill picks that result. This ADR records those decisions.
4. The price skill named `pricing_calculator.py` but gave no command to run it, and the script had no command line.

## Decision

1. **Adopt the standard.** `pricing:price` writes one result file to `.pricing/results/` at the end of every run, a partial or halted one too, and a person's run too (R1). `result-file.json` names the writer and the defaults registry. `questions/price.json` lists the inputs, and each AskUserQuestion line of the files the command reaches carries its `[q: <input>]` id.

2. **A thin runner is the route.** `agents/price-runner.md` reads the price skill and follows it, places the offering in the tiers with the package skill (as Step 6 of the pricer does), and writes the result file by the rules in the `## Result file` section of `agents/new-offering-pricer.md`. Run as itself, the pricer writes no result file. Each run keeps a copy of its files in its own folder, `.pricing/<run_id>/`, and a result's `detail` names that copy; the files at the `.pricing/` root stay as before.

3. **The Path A gate.** With a `plugin-run` block, the price skill reads only the jtbd result file that `inputs_from` names, and uses it only when its `run.run_id` and `run.case` match. A missing or unreadable file, a mismatch, or a file with no willingness to pay is refused: the run uses Path B, and the gate's gap goes into the result's `gaps` as written.

4. **The person-run confirmation.** With no block, the skill reads the newest jtbd result, and the old `.jtbd/` files only when there is none. It asks the person to confirm the run (`confirm_jtbd_run`, a boolean question). When it cannot ask, it names the file it chose in its output and in the result's `method`, and uses Path B.

5. **An automated run with no block is Path B and never validated.** Mode Detection skips the confirmation, so no jtbd result is accepted.

6. **The grade of a Path A price.** A Path A price is validated only when its willingness-to-pay result, and its customer-value result when it used one, has a `customer_data` or `published` source. Otherwise its confidence is `estimated`, and the result and the report call it "from jtbd" or "an estimate". The gate does not change: it accepts a matching result whatever its sources. A Path A price copies the sources and the defaults of each jtbd result it used and cites them, so a price built on estimated willingness to pay still says it rests on a default.

7. **Scripts run with `uv run` from a rooted path.** Every command the runner or the skill gives the model is `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py" ...`, never `python3 -c` or `python3 -` in the working directory, where a planted module could run. Each script has a PEP 723 block that names its Python version and its packages. `pricing_calculator.py` has a command line for this: `<function> '<JSON arguments>'`, printing the result as JSON.

8. **The registry.** Seventeen defaults are registered: the four constants of `config/defaults.json` (`target_margin`, `value_capture_rate`, `overhead_rate`, `value_share`); the price skill's fallbacks for production cost, the AI multiplier, the moat multiplier and the pricing unit; the five Path A fallbacks (AI value, moat value, EVC, reference price, and which willingness-to-pay number caps the price), each a row of the price skill's sourcing table; and the package skill's fallbacks for the feature list, the classes, the tier feedback and the freemium gate. An input the answers file does not give is a `default` source, never `model`. The other leaves of `config/defaults.json` are not defaults: two thresholds are rules of the method, and two ranges are documentation bounds that no code reads. `result-file.json` says why for each.

9. **A block run needs no confirmation.** A `plugin-run` block with a matching jtbd entry gives Path A without asking: the coach chose the run. `confirm_jtbd_run` set to `false` in the answers file gives Path B.

## Consequences

- A coach can run `pricing:price` with an answers file and read one checked result file. Each price says which defaults it rests on.
- A Path A price that rests on expert-estimated willingness to pay no longer reads as validated.
- Readers of `.pricing/pricing-recommendation.json` see no change.
- Path C asks more inputs than an automated run can guess. A coach run without them writes a gap, not a price.
