---
description: Use for a standalone Testing at Design Time and Runtime deep-dive. Applies Kent Beck (TDD, tests as design tools), Michael Feathers (legacy code, seams, characterization tests), Dave Farley (FIRST principles, test pyramid, contract testing, architecture fitness functions), and Chaos Engineering (controlled production failure injection) to assess your testing architecture.
---

# /architecture-assess:testing

Standalone deep-dive into your testing architecture at design time and runtime.

## When to Use

- "Review our testing architecture"
- "How do we improve our test pyramid?"
- "We have legacy code with no tests — where do we start?"
- "How do we implement architecture fitness functions?"
- "Should we adopt chaos engineering?"
- "How do we test our AI/ML features for bias?"

## Steps

1. Scan the codebase for testing infrastructure (test directories, coverage configs, chaos tool configs).
2. Ask with `AskUserQuestion` for your biggest testing pain point and your language and framework. Skip a question that the text after the command already answers.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py new`. The command prints the temp folder `.architect-tmp/<id>/`. Keep the path as `output_dir`, and `<id>` as `session_id`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: architecture-assess:testing-assessor`. The prompt gives these fields: `session_id`, `output_dir`, and `business_context` (the answers of step 2).
5. Read the last line of the agent reply.
   - `DONE: testing`: read `<output_dir>/testing.md` and show the assessment (domain ADR section with TDD evidence, FIRST compliance, legacy risk, fitness functions status). Show the `constitution_check` value of the YAML header. When it is `indeterminate`, say that the assessor could not decide it from the code, and show its reason.
   - Any other ending: show the last lines of the reply and say that the run failed. Keep the temp folder, and stop.
6. Clean up: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session.py remove <session_id>`.

> **For a complete architecture assessment (all domains):** Use `/architecture-assess:assess`
>
> **To assess Testing as part of a full design:** Use `/architecture-assess:design`
