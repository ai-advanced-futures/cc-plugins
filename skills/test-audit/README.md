# Test audit

This skill derives from OpenClaw `test-audit` at commit
`4cbd215af463775faa6807aea90621292b28af15`, with changes.

The revised files are `SKILL.md`, `CAMPAIGN.md`, and `references/audit.md`.
The revision removes repeated criteria and replaces fixed steps with required
results. The source is the
[OpenClaw test-audit folder](https://github.com/openclaw/openclaw/tree/4cbd215af463775faa6807aea90621292b28af15/.agents/skills/test-audit).
The MIT license notice remains in [NOTICE](NOTICE).

## Source-specific requirements

The skill retains OpenClaw's validation commands. It is not adapted to this
repository or to another test framework. The source guides remain outside this
folder; use their pinned copies:

- [Test boundary and cost guide](https://github.com/openclaw/openclaw/blob/4cbd215af463775faa6807aea90621292b28af15/docs/help/testing/writing-tests.md).
- [OpenClaw testing proof policy](https://github.com/openclaw/openclaw/blob/4cbd215af463775faa6807aea90621292b28af15/.agents/skills/openclaw-testing/SKILL.md#proof-policy).

This folder does not include OpenClaw's Vitest setup, `pnpm` commands,
`scripts/check-changed.mjs`, or maintainer review tools. Those commands require
the OpenClaw repository.

## Re-test requirement

The revision targets Claude Fable 5, but no behavior evaluation has run. The
skill has no model pin; its evidence fields, decision marks, independent review,
and validation requirements remain applicable to other models.

Treat a model swap as a breaking change. Before release, compare the original
and revised skill on tests with weak assertions, duplicate coverage, independent
static contracts, baseline product defects, missing deletion evidence, and
unreachable negative controls. Include a subsystem audit with a retained-contract
check and a deliberate mutation that its retained test detects. Shape measures
and their all-rules estimates do not measure task accuracy.
