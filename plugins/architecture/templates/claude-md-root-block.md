## Architecture decisions

Decisions that are expensive to undo are recorded in `{{DIR}}/`.

Read `{{REGISTER}}` before you change an architectural boundary. Open only the ADRs that apply.
When you make a decision that is expensive to undo, write an ADR with `lifecycle: accepted`.
Do not stop to ask.

Rules for the ADRs in `{{DIR}}`:
- Write a new ADR only with `/architecture:learn`. Change a recorded decision only with the `amending-adrs` skill.
- `lifecycle` holds proposed, accepted, deprecated, or superseded. `status` holds the OKF value.
- Do not edit `index.md`, `archive/index.md`, `links.tsv`, the `LINKS` block of an ADR, or the register block.
