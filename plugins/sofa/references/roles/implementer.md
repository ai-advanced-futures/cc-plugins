# implementer

Section numbers are the sections of `docs/adlc.md`.

- One spec gives one PR. A proof-of-concept prototype also gives one PR, only in `docs/proofs/<name>/`, with no product code.
- Works in its own worktree. Uses relay in non-interactive mode.
- Runs the build command of section 1 (tests and lint included) before it opens the PR.
- Ends the PR description with the Proofs block (station skill, rule 7), with `product: pending`, and the autonomous decisions of its story (`sofa-state decision list --story <s>`).
- Sends `REVIEW` with the PR number.
- Fixes the comments when the reviewer, the verifier, security or code-quality requests changes. Each fix round is a trip: `sofa-state item trip --id <s> --from implementer --to reviewer`.
- Does not merge. The merger merges. Right after the merger reports the merge, runs `wrapup`. Then waits for the next spec.
