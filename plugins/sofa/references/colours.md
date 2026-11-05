# Role colours

The session colour of each role. The sofa mod (`hooks/register.tsx`) reads this file and `docs/adlc/colours.md` when a session starts. It finds the role in the session name (`<prefix>-<role>[-n]`) and runs the built-in `/color` with the colour of the role. When `/color` is done, the mod records the colour in the state store (`sofa-state session colour`). The orchestrator compares the store with the two files in its status check (orchestrator role file, "Status check").

The names that `/color` takes are `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink` and `cyan`. 8 names are available for 29 roles, thus a colour shows a group of roles:

- `purple`: the roles that decide and route.
- `yellow`: only the roles that talk directly to a human. Give a role that does not talk to a human a different colour.
- `orange`: the roles that keep the records (knowledge, board, roadmap, versions).
- `green`: the roles that build and land code.
- `blue`: the roles that test, run and watch the environments.
- `cyan`: the roles that plan, design and study.
- `red`: the roles that find problems.
- `pink`: the retro.

A repository can change a colour, or give a colour to a role that is only in that repository, in `docs/adlc/colours.md`: the same table, with only the rows that differ. For each role in it, the repository file wins (as for role files). The retro writes it. A live session keeps its colour until the orchestrator restarts it.

| Role | Colour |
|---|---|
| orchestrator | `purple` |
| hitl | `yellow` |
| requests | `yellow` |
| decision-judge | `purple` |
| scribe | `orange` |
| tracker | `orange` |
| plan-auditor | `orange` |
| merger | `green` |
| monitoring | `blue` |
| scheduler | `orange` |
| retro | `pink` |
| planner | `cyan` |
| architect | `cyan` |
| designer | `cyan` |
| business-domain | `cyan` |
| specifier | `cyan` |
| implementer | `green` |
| reviewer | `green` |
| verifier | `green` |
| tester | `blue` |
| security | `red` |
| code-quality | `red` |
| researcher | `cyan` |
| troubleshooter | `red` |
| operator | `blue` |
| feedback | `blue` |
| ux-quality | `blue` |
| updater | `orange` |
| chores | `yellow` |
