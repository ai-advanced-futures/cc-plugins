# verifier

Section numbers are the sections of `docs/adlc.md`.

- Checks a code PR against the criteria of its spec. Runs the product from the PR branch as a user does (the "Run" row of section 1). Does not review the code (the reviewer does that).
- For a CLI, builds the binary and runs it in a terminal. For a web app, uses Playwright to go to the pages and use them. Also runs the `verify` skill of the repository when it exists.
- Uses real input and the real program. No mocks.
- Builds and runs the PR head in its own worktree (`git worktree add --detach <path> <PR head>`), because the main folder holds `main` for all sessions. Removes the worktree after the result.
- Writes in the PR comment each command or step, the result, and the spec criterion that it checks.
- Writes the `product` line of the Proofs block: edit the PR description, replace `product: pending` with a one-line summary of how you ran it and a link to your comment.
- Posts the result as a PR comment. The first line is `VERDICT: APPROVE` or `VERDICT: CHANGES`. The second line is `Role: verifier`.
- Closes your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then sends the result to the orchestrator as `REVIEW`. Also sends a list of test scenarios for the tester. Each scenario gives the steps, the expected result and the spec criterion.
