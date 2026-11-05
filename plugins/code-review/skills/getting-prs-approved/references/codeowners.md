# CODEOWNERS parsing and matching

Answers one question for `getting-prs-approved` Step 1: **who can approve this PR**, so we can
request review from them.

## Parse

Read CODEOWNERS **from the PR's base branch** — that's the copy GitHub enforces, so a head-branch
copy (including one this very PR edits) would produce a list that doesn't match branch protection.
GitHub checks three locations and uses the first it finds:

```bash
for p in .github/CODEOWNERS CODEOWNERS docs/CODEOWNERS; do
  gh api "repos/$REPO/contents/$p?ref=$BASE_REF" --jq '.content' 2>/dev/null \
    | base64 -d && break
done
```

Each non-blank, non-`#` line is `PATTERN owner…`, where owners are teams (`@org/team`) or
individuals (`@login`).

- **No file in any of the three locations, or an empty one → empty owner set.** A normal repo
  shape, not an error. Continue with write-access collaborators only.
- **Keep the catch-all `*` rule.** Under *Require review from Code Owners*, only a code owner's approval flips
  `reviewDecision` to `APPROVED`, so for a repo whose CODEOWNERS is just `* @org/team`, that team
  is the **only** answer. Dropping it sends the request to collaborators who can't unblock the PR,
  and the loop then polls forever without ever reaching the dead-end escalation.

## Match

Test the PR's changed paths (`.files[].path` from the payload Step 1 already fetched) against
each pattern. `gh pr view --json files` returns at most 100 files; on a larger PR use
`gh api repos/$REPO/pulls/$N/files --paginate --jq '.[].filename'` rather than matching a
truncated list.

| Pattern shape | Meaning |
|---|---|
| Leading `/` (`/docs`) | anchored at the repo root |
| Trailing slash (`docs/adrs/`) | the directory and everything under it |
| No slash at all (`*.tf`, `build`) | matches at **any** directory depth |
| Otherwise (`src/**/api.ts`) | glob; `*` does not cross `/`, `**` does |

Last matching rule wins, per GitHub's own precedence.

## Using the result

Matched owners are eligible approvers. Step 1 owns the union with write-access collaborators,
the review request, and the escalation when nobody is left.

- **Drop the PR author and our own login.** GitHub rejects a review request naming the author, and
  self-review is pointless. An empty CODEOWNERS set is not an escalation here, because Step 1
  decides on the **union** with collaborators.
- **Team owners keep their `org/team` form, minus the `@`.** `gh pr edit --add-reviewer` takes
  `org/team` for a team and a bare `login` for a user. Passing `@org/team` verbatim fails and
  silently loses every team owner.
