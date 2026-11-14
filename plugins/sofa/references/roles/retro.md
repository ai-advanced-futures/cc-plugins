# retro

Section numbers are the sections of `docs/adlc.md`.

- Starts when the orchestrator sends `RETRO`.
- Asks the user directly what to change and why.
- Lands each change with a short worktree, PR and merge loop (section 6). After the merge, runs `wrapup` (station skill, rule 3).
- Records each change in section 9.
- Closes your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then sends the orchestrator a `DONE` message with a summary of the changes.

## Where a change goes

Change only files in the repository, because the next install of the `sofa` plugin replaces the plugin files:

- A change to the rules, the flow, the message format, the card, the start commands, or a value in the roles table (model, effort, count): change `docs/adlc.md`. A role colour, also the colour of a new role: add a row with the role and the colour to `docs/adlc/colours.md` (the same table as `<skill folder>/references/colours.md`, only the rows that differ).
- A change to the work of 1 role: write it in `docs/adlc/roles/<role>.md`. Write only what is different from the skill role file (`<skill folder>/references/roles/<role>.md`). For each changed line, say which line of the skill role file it replaces. Where the two files differ, the repository file wins (section 3, "Role files").
- A new role: add its row to the roles table in `docs/adlc.md`, and write the full role in `docs/adlc/roles/<role>.md`.

## Offer the change to the skill

After the merge, ask the user with `AskUserQuestion` if the change must also go into the `sofa` plugin, for all repositories. The options are: open an issue in `ai-advanced-futures/cc-plugins`, or keep the change only in this repository.

If the user chooses the issue:

1. Write the issue text. Title: `sofa: <role or section>: <the change in a few words>`. Body:
   - The role or the section of the template that changes.
   - The new text, and the text that it replaces.
   - Why: the problem that the user saw.
2. Before you open the issue, remove all data that must not leave this repository, because the issue is public: secrets, private data, names of private repositories, paths, and all other data that a repository rule in section 1 protects (station skill, rule 3). Write the problem in general words.
3. Show the user the full text. Open the issue only after the user agrees: `gh issue create --repo ai-advanced-futures/cc-plugins --title "<title>" --body-file <file>`.
4. Put the issue link in the `DONE` message. Close your work order (`sofa-state item set --id <work order> --state done --session <your name>`) before the `DONE`.
