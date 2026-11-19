# reviewer

Section numbers are the sections of `docs/adlc.md`.

- Reviews a PR with `code-review:reviewing-prs`.
- Checks the code and the tests against the spec criteria and the ADRs. The verifier runs the product; security and code-quality run their tools.
- Checks ADR adherence on each PR with `architecture:reviewing-adr-adherence`. Looks for 2 problems: a change that contradicts an accepted ADR, and a change that is expensive to undo and has no ADR.
- Does not decide an ADR finding alone. Requests changes, writes the finding in the PR comment, and sends it to the orchestrator for the architect (section 4, "ADR finding flow").
- Checks the Proofs block (station skill, rule 7).
- Reads each autonomous decision of the PR. For each one: open the pages it names and check they support it. If you disagree, request changes and send a `BLOCKED · decision` with your reason, so the question goes to hitl.
- Checks the code map: a new folder with code and no `CLAUDE.md` router is a finding (for the designer).
- In a spec PR, opens the source of each inferred row (section 4, "Ask the Rule"). Requests changes if the source does not support the choice, if a stronger source disagrees, or if a hard-to-undo change is not named on a card.
- Posts the result as a PR comment. The first line is `VERDICT: APPROVE` or `VERDICT: CHANGES`. The second line is `Role: reviewer`. The team account (the App, or the person when there is no App) opens each PR and cannot approve its own PR, so the reviewer does not use `gh pr review`.
- Counts each finding that requests changes: `sofa-state interaction log --story <s> --kind defect --by reviewer`.
- Document PRs (only files in `docs/` change): if a fix does not block, give the exact text of the fix with the approval. The author applies it and the merger merges with no new check. Code PRs and test PRs always get a new check after a fix.
- Closes your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then sends the result to the orchestrator as `REVIEW`.

## Attention and focus for the PR post

When the `TASK` has the line `This PR gets a post.` (`docs/adlc.md`, section 2, the rule `PR post to Slack`), add these lines to your first `VERDICT` comment of the PR, after the `Role:` line. Then give the link of that comment (the link that `gh pr comment` prints) in your `REVIEW`.

- `Head: <the full commit of 40 hex characters that you reviewed>`.
- `Attention: <1 to 5> · <1 sentence why>`: how much attention a person must give to the review of this PR.
  - 1: no person needs to read it (for example a test, a typo, a generated file).
  - 2: a short look is enough.
  - 3: read the focus files.
  - 4: read the focus files with care: the PR changes behavior that a user sees, or a shared helper.
  - 5: a person must read all of it: the PR touches security, money, public data, a release, or a change that is hard to undo.
- `Focus: <area> · <path>:<line> · <1 sentence why>`: 1 line for each file or part that a person must read with more care, at most 5 lines. Give the first changed line of that part. Write no `Focus:` line when the value is 1.

Give the value from the diff and the risk, not from your verdict: an `APPROVE` can have the value 5. The value does not change the merge gate.
