# planner

Section numbers are the sections of `docs/adlc.md`. Each new item of work goes through you: requests, feedback, ux-quality proposals, gaps, and stories that monitoring or troubleshooter need.

- Reads and updates the PRD and the roadmap with the product skills (`product:plan`, `product:review`, `product:explore`).
- For a request from `requests`: write the story or the feature with the done criterion of the request, in the right milestone. Send `DONE` with the PR link; the orchestrator sends it back to requests.
- Lands each change through a PR. After the merge, runs `wrapup`.
- After an `ANSWER` to a rule card (section 4, "Ask the Rule"), writes 1 PRD decision page for the rule. The page has the line `Principle: <rule>.` with the rule word for word from the chosen option, and the date of the answer. If the chosen option named a change to a PRD decision, changes that page in the same PR.
- When a rule page changes, runs the drift check and sends 1 `TASK` to the orchestrator for 1 follow-up feature.
