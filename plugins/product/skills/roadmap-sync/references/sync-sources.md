# Roadmap sync sources

The evidence scan reads these sources for each work item that has no `github`
field. A state in the tables below is a `WorkState` value of
`../../shared/roadmap-model.md`. Set it with
`prd.py state <ID> <state> --actor human:<login>`, never with an edit tool,
because `prd.py state` is the one write path and logs each change.

## GitHub issues and pull requests

### Search patterns

Match the full ID, such as `STORY-12`, and each alias of the page. Do not match
a prefix, because `STORY-1` also matches `STORY-12`.

1. **Title**: the ID in the title of an issue or a pull request
2. **Body**: the ID in the body of an issue or a pull request
3. **Label**: a label that carries the ID
4. **Branch**: a branch named with the ID, such as `feature/STORY-12-booking`

### GitHub CLI commands

```bash
# The issues that name one item
gh issue list --search "STORY-12" --state all --json number,title,state,labels

# The pull requests that name one item
gh pr list --search "STORY-12" --state all --json number,title,state,mergedAt

# One issue in full
gh issue view <number> --json title,state,labels,body
```

### The state that a GitHub signal proposes

| GitHub signal | Proposed state |
|---|---|
| A merged pull request names the item | `done` |
| An open pull request names the item | `in_review` |
| A draft pull request names the item | `in_progress` |
| An open issue with an assignee | `in_progress` |
| An open issue with no assignee | `ready` (a weak signal) |
| An issue closed as completed | `done` |
| An issue closed as not planned | `cancelled` |

No evidence gives `released`. Only `prd.py state` sets it.

### Two signals that do not agree

- A merged pull request beats an open issue.
- An open pull request beats the state of an issue.
- The most recent signal wins when the two are of one type.

### The states that this scan never sets

- `blocked` comes from `blocked_by`. The checker computes it.
- `claimed` belongs to the claim commands.
- A drifted item is the work of `prd.py drift`, not of this scan. The `drifted`
  field holds the targets, and `state` keeps its value.
- A milestone has no state. Skip each `MILESTONE-01` page in this scan.

## Code evidence

### What to look for

For each `EPIC-01`, `FEATURE-04`, `STORY-12`, and `TASK-31` page:

1. **Source files**: a file or a directory whose name matches the title of the
   item, or a comment that names the ID
2. **Test files**: a test whose name matches the title of the item

### Commands

```bash
# The files that name one item
grep -rn "STORY-12" --include="*.ts" --include="*.py" -l .

# The files that match the title of an item
find . -name "*booking*" -not -path "*/node_modules/*" -not -path "*/.git/*"

# The tests of one item
find . -path "*test*" -name "*booking*"
```

### The state that a code signal proposes

| Code signal | Proposed state |
|---|---|
| Source files and tests are present | Supports `done` |
| Source files are present, tests are absent | Supports `in_progress` |
| No source file is present | Supports `ready` |

A code signal supports a GitHub signal. It does not beat one.
