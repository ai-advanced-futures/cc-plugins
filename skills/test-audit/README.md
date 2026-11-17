# Test audit

This folder contains a verbatim copy of the OpenClaw `test-audit` skill at
commit `4cbd215af463775faa6807aea90621292b28af15`.

The copied files are `SKILL.md`, `CAMPAIGN.md`, and `references/audit.md`.
Their content is unchanged. The source is the
[OpenClaw test-audit folder](https://github.com/openclaw/openclaw/tree/4cbd215af463775faa6807aea90621292b28af15/.agents/skills/test-audit).
The MIT license notice is in [NOTICE](NOTICE).

## Source-specific requirements

The skill retains the commands, examples, and relative links of OpenClaw.
It is not adapted to this repository or to another test framework.

Two required guides are outside the copied skill folder. Their relative links
do not resolve here. Read the pinned source copies:

- [Test boundary and cost guide](https://github.com/openclaw/openclaw/blob/4cbd215af463775faa6807aea90621292b28af15/docs/help/testing/writing-tests.md).
- [OpenClaw testing proof policy](https://github.com/openclaw/openclaw/blob/4cbd215af463775faa6807aea90621292b28af15/.agents/skills/openclaw-testing/SKILL.md#proof-policy).

The copy does not include OpenClaw's Vitest setup, `pnpm` commands,
`scripts/check-changed.mjs`, or maintainer review tools. The referenced
commands require the OpenClaw repository. The import does not verify an audit
run against this repository's tests.
