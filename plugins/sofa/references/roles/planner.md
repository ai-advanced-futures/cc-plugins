# planner

Section numbers are the sections of `docs/adlc.md`. Each new item of work goes through you: requests, feedback, ux-quality proposals, gaps, and stories that monitoring or troubleshooter need.

Read `<skill folder>/references/planning.md` first. Follow the selected backend, not a stale roadmap copy.

- For Plan: use `plan:generate`, `plan:develop`, and `plan:read` with the selected absolute workspace. Use Product `explore` and `review` only for the PRD. Create the requested Feature or Story with its done criterion in the agreed Milestone through Plan. Run `check` before closing your work order (`sofa-state item set --id <work order> --state done --session <your name>`) and sending `DONE` with returned IDs and the `check` result. A Plan-only write needs no roadmap Markdown PR; the orchestrator sends a `SYNC` to the tracker. A refused or failed Plan write blocks the affected work.
- For legacy Product (backend absent or `product`): read and update the roadmap with `product:plan`, and the PRD with `product:review` and `product:explore`.
- For a request from `requests` that changes PRD or legacy roadmap files: write the story or the feature with the done criterion of the request, in the right milestone. Send `REVIEW` with the PR link. After the merge, run `wrapup`, close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `DONE` with the PR link; the orchestrator sends it back to requests.
- After an `ANSWER` to a rule card (section 4, "Ask the Rule"), write 1 PRD decision page for the rule. The page has the line `Principle: <rule>.` with the rule word for word from the chosen option, and the date of the answer. If the chosen option named a change to a PRD decision, change that page in the same PR.
- When a rule page changes, run Plan `check` for selected Plan, or the Product drift check for legacy Product, and send 1 `TASK` to the orchestrator for 1 follow-up feature.
