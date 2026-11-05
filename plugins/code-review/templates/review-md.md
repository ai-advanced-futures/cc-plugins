<!-- code-review generator template: the REVIEW.md block. /code-review:setup (bootstrapping, Step 5d) fills the <PLACEHOLDER> spans and writes the result between `<!-- code-review:router start -->` and `<!-- code-review:router end -->` in the repo-root REVIEW.md. Anthropic's Code Review service on GitHub reads that file. Keep the output short: 60 lines or fewer. Delete this comment line from the output. -->
## Rules from the review contract

Generated from `.claude/code-review/contract.md` by `/code-review:setup`. Write your own rules
outside this block. A re-run replaces only this block.

### What failure looks like here

Mark a finding Important only when this change makes the repo fail in one of these ways:

- <FAILURE: one plain statement of how this repo fails, with the paths it applies to, e.g. "Docs under `docs/` lie: they state a command, flag, or path that the code does not have.">
- <FAILURE: e.g. "Config under `deploy/` misroutes: a request reaches the wrong service or tenant.">
- A rule marked blocking under "Always check" breaks.

All other findings are Nit at most. When you are not sure, use Nit.

### Evidence

Give a `file:line` in this diff for each finding. Read the code before you state what it does,
because a name can be wrong. Report a finding only when you can point to its line.

### Cap the nits

Report at most <NIT LIMIT> Nits per review.

### Do not report

- Anything these CI commands check: <GATE COMMANDS, comma-separated>
- <SKIP PATH, e.g. "Generated files under `src/gen/`, and any `*.lock` file">

### Always check

- [blocking] <INVARIANT from contract §3 that is marked [blocking]>
- <FLAG LINE from a lens, without the "flag:" prefix>

### Summary

Start the summary with the count: "<n> Important, <n> Nit". When there is nothing to fix, say
"Nothing to fix." and stop.
