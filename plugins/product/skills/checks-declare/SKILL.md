---
description: Record the check argv of each acceptance criterion of one story, with the person who declares it
argument-hint: "[story]"
model: sonnet
context: fork
allowed-tools: AskUserQuestion, Bash, Read, Edit, Grep
---

# Declare the checks of a story

A check is the argv list that `prd.py run-checks` runs for one acceptance
criterion. A check runs code on the machine of the user, so only a person
declares one. Rule E8 refuses a `check` that has no `check_declared_by:
human:<login>`.

Read these files before you write text:

- `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style.
- `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the page format, the IDs,
  and the write rule.

## Step 0: the bundle must exist

Run this command:

    ls docs/product/prd/index.md

If the file is absent and a v3 PRD file is present in `docs/product/`, stop.
Tell the user: "This repository holds a v3 PRD. Run `/product:migrate` first."
Leave the v3 PRD file as it is, because the migration reads it and a second
copy becomes a second source of truth.

If the file is absent and `docs/product/` holds no v3 PRD file, this
repository has no bundle. Tell the user to run `/product:explore` first, which
bootstraps the bundle. Then stop.

## The command

Run the script from the target repository:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py <subcommand>
```

If `uv` is not available, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py`
instead. The exit code is the verdict. Read the exit code, because the text alone can
look correct after a failure.

Exit code 0 is success. [inferred] Exit code 1 means the script refused the
data, such as an ID that names no page. [inferred] Exit code 2 means the
command was called wrong, such as a bad actor string or a missing argument.
[inferred] For code 1 and code 2 the script prints one `ERROR:` line on
stderr. [inferred]

Exit code 2 with "is held by another prd.py process" on stderr means that
another `prd.py` run holds the write lock. The command wrote nothing: wait,
then run the same command again. `run-checks` is the exception. It writes
its Run page and its `Run` line in a first lock, and then runs the regen in a
second lock. So after `run-checks` exits 2 with the lock message, list the Run
pages of the item first: `prd.py list Run --where item=/<directory>/<ID>.md`,
with the bundle path of the item (for example `/stories/STORY-12.md` or
`/tasks/TASK-07.md`). A Run ID holds its UTC time to the second
(`RUN-<date>-<time>-<token>`), so note the UTC time
(`date -u +%Y%m%d-%H%M%S`) before you run `run-checks`. If a Run page has a
time that is not before that noted time, run `prd.py regen` only, because the
checks already ran and a second run writes a second Run page. If no such page
is there, run `run-checks` again.

## Step 1: Find the story

If the user gave an ID, use it. If not, list the stories and ask which one:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Story --fields title,state
```

## Step 2: List the criteria of that story

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list AcceptanceCriterion \
  --where item=/stories/STORY-12.md --fields title,check,check_declared_by
```

A criterion that already has a `check` needs the approval of the user, not a
second declaration.

## Step 3: Get the login of the person

```bash
gh api user -q .login
```

If `gh` fails, ask the user for the login. The value must match
`^human:[A-Za-z0-9._-]+$`, such as `human:pilo`.

## Step 4: Ask for the argv of each criterion

Read the criterion page, propose one argv list, and ask the user to accept it
or give another one. Use `AskUserQuestion`. One criterion at a time.

Rules for an argv list:

- Each element is one word of the command. `["pytest", "tests/test_book.py"]`
  is correct. `["pytest tests/test_book.py"]` is not.
- No shell operator. The script starts no shell, so `|`, `>`, `&&`, `;`, and
  `$(...)` are text, not operators. Write a script in the repository and call
  that script instead.
- The command runs from the root of the repository.
- The command exits 0 when the criterion is met, and exits with another code
  when it is not.
- The command must end inside 600 seconds. A command that runs longer is
  stopped, and its result is exit code 124. [inferred]
- A criterion that no command can test gets no check. Its result is
  `not-checked`.

## Step 5: Write the two fields

Edit the criterion page. Add the two fields to the frontmatter:

```yaml
check:
  - pytest
  - tests/test_booking.py::test_books_a_free_slot
check_declared_by: human:pilo
```

Write `check_declared_by` in the same edit as `check`. A `check` alone is an
E8 error.

## Step 6: The write rule

After the last page write, run these two commands in this order:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check
```

If one of them exits with a code that is not 0, stop, show the output, and
report the failure. Do not report success, because the bundle is in a state
that the checks reject. Show each warning to the user, but
a warning does not stop the skill.

## Step 7: Tell the user what to run next

Name the command that runs the new checks:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py run-checks STORY-12 --actor human:pilo
```
