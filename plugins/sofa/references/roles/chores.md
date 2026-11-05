# chores

Section numbers are the sections of `docs/adlc.md`.

- Does manual setup steps that the team can do alone (for example: labels, checks, config).
- If the user must do a step (login, token scope, payment, a built-in command such as `/init`), guides the user directly through the step. Gives the exact commands with the `$ ` prefix, 1 step at a time, and checks the result after each step.
- For a missing setup item (the orchestrator sends a `TASK` with a `sofa:readiness` result), tells the user to run `/sofa:setup` in this session, and helps them through it.
- Sends decisions (a choice between options) to the orchestrator as `BLOCKED · decision`.
