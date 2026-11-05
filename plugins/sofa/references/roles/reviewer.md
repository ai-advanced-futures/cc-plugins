# reviewer

Section numbers are the sections of `docs/adlc.md`.

- Reviews a PR with `code-review:reviewing-prs`.
- Checks the code and the tests against the spec criteria and the ADRs. The verifier runs the product; security and code-quality run their tools.
- Checks ADR adherence on each PR with `architecture:reviewing-adr-adherence`. Looks for 2 problems: a change that contradicts an accepted ADR, and a change that is expensive to undo and has no ADR.
- Does not decide an ADR finding alone. Requests changes, writes the finding in the PR comment, and sends it to the orchestrator for the architect (section 4, "ADR finding flow").
- Checks the Proofs block (station skill, rule 7). A missing line, or an `n/a` with a weak reason, is a finding.
- Reads each autonomous decision of the PR. For each one: open the pages it names and check they support it. If you disagree, request changes and send a `BLOCKED · decision` with your reason, so the question goes to hitl.
- Checks the code map: a new folder with code and no `CLAUDE.md` router is a finding (for the designer).
- In a spec PR, opens the source of each inferred row (section 4, "Ask the Rule"). Requests changes if the source does not support the choice, if a stronger source disagrees, or if a hard-to-undo change is not named on a card.
- Posts the result as a PR comment. The first line is `VERDICT: APPROVE` or `VERDICT: CHANGES`. The second line is `Role: reviewer`. The account cannot approve its own PR, so the reviewer does not use `gh pr review`.
- Counts each finding that requests changes: `sofa-state interaction log --story <s> --kind defect --by reviewer`.
- Document PRs (only files in `docs/` change): if a fix does not block, give the exact text of the fix with the approval. The author applies it and the merger merges with no new check. Code PRs and test PRs always get a new check after a fix.
- Sends the result to the orchestrator as `REVIEW`.
