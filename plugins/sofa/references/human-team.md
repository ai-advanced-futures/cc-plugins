# The human team

The `knowledge` brain holds 1 person page for each person of the human team. `scripts/sofa-people` writes and reads the pages. The `setup` skill (step 6), `requests`, `scribe`, `hitl` and `decision-judge` use this file.

## The person page

An `Entity` page in `entities/<slug>.md`, with `entity_kind: person`. The knowledge schema permits no other keys on an `Entity`, so the data of the person is in `tags`:

| Tag | Value |
|---|---|
| `person` | always |
| `role:<role>` | the role, in the words of the person, for example `role:owner` |
| `owns:<area>` | 1 tag for each decision area of `decision-areas.md` that the person decides |
| `escalates-to:<slug>` | the slug of the person who decides when this person cannot, or `none` |
| `slack:<handle>` | the Slack display name, for example `slack:@Pilo` |
| `slack-id:<id>` | the Slack user ID, for example `slack-id:U01ABC`. A mention in a message is `<@U01ABC>`, because a display name does not notify the person. |
| `github:<login>` | the GitHub login |

The GitHub login and the Slack handle are also `aliases`, so `knowledge:ask` finds the person by either one. Each person page cites the hub page `synthesis/the-human-team.md`, and the hub cites each person page.

## The commands

```
sofa-people draft [--json]                 # gather people from GitHub, CODEOWNERS, git log, Slack
sofa-people add --batch <file> --by <actor> [--confirmed-by human:<login>] # write a confirmed batch
sofa-people list [--owns <area>] [--json]   # read the person pages
```

`draft` reads the repository and the Slack channel from `docs/adlc.md`, and the Slack token from `SLACK_BOT_TOKEN` or from `.claude/settings.local.json`. It writes nothing. A source that fails shows as `unavailable` with its cause, and the other sources still run. It joins rows only when the GitHub login, the email or the lowercase name is equal, so a person with 2 names shows as 2 rows. The human joins them.

`add` finds the knowledge save code from `--kg`, then `$SOFA_KNOWLEDGE_GRAPH`, then the knowledge plugin in `~/.claude/plugins/installed_plugins.json`. It stops with exit code 1 when it finds none.

## The batch file

A JSON list. 1 item for each person:

```json
[{"name": "Pilo", "role": "owner", "owns": ["product-direction", "technical-direction"],
  "escalates_to": "none", "slack": "@Pilo", "slack_id": "U01ABC", "github": "404pilo"}]
```

`name`, `role`, `owns` and `escalates_to` are necessary. `add` checks them before it writes a file. Each batch gets its own raw file, because a raw file does not change after a Source page cites it. A person who has a page already gets an update of that page, not a second page. `add` finds that page by the optional `slug` field, then by an alias (the GitHub login or the Slack handle), then by the slug of `name`. An update keeps the handles that the batch does not give. `escalates_to` must be the name or slug of a person in the batch or the brain, or `none`; else `add` stops before it writes a file. `slug` must be the slug of a page that exists in the brain; else `add` stops with 1 line before it writes a file. Give `slug` when the name differs from the title of the page, for example `"name": "Ana B. Example", "slug": "ana-b-example"`. A new person gets no `slug`: `add` makes the slug of the new page from `name`.

## The actor

- An agent session gives `--by agent:<session name>` and `--confirmed-by human:<login>`, the login of the person who confirmed the batch. `add` refuses `--by human:<login>` in an agent session, and `--by agent:<id>` with no `--confirmed-by`, with 1 line.
- A person who runs `add` in a terminal gives `--by human:<login>`. `--confirmed-by` is optional then, and the default is the same login.
- The login of the person goes into the raw file and the Source page: `Confirmed by <login> on <date>.` For an agent session, they add `Written by agent:<id>.`
- `generated.by` of each page that an agent session saves holds `sofa/<version>`, the plugin code that writes the page, because the brain standard permits only `human:<login>`, `<plugin>/<version>` and `process:<id>`.
- An agent never writes a `human:` actor (DECISION-03), in `generated.by` or in `verified[].by`.
- The limit: `add` knows that an agent runs it only from the variable `CLAUDE_CODE_CHILD_SESSION`, so a shell that does not have the variable can give `--by human:<login>`. `--confirmed-by` is a claim, not a proof, because `add` cannot check that the person confirmed. So each new Source page needs a link to the card or the `ANSWER` that shows the confirmation, in its PR.

## The interview

1. Show the draft as 1 table. Ask which rows are on the human team, and which person is missing.
2. For each person, ask 3 questions in 1 `AskUserQuestion`: the role; the decision areas (`multiSelect`, from `decision-areas.md`); and who the person escalates to (the other people, and `none`). The first option is the most likely answer, from the draft and the earlier answers.
   - Then ask for the GitHub login of the person in its own `AskUserQuestion`, not in the `AskUserQuestion` of the 3 questions.
   - For the GitHub login, the first option is the login of the draft row.
   - With no login in the draft row, the first option is the GitHub person of this machine (item 4), but only while no item of the batch and no person page has that login.
   - The last option is "no GitHub login". For that answer, leave out the key `github` of the item.
   - The user types another login with "Other".
   - When "no GitHub login" is the only option left, ask for the login as text, not in an `AskUserQuestion`.
3. Ask for the Slack handle only when the draft has none.
4. Check the operator before you write the batch.
   - Find the GitHub person of this machine. In a team session, it is the GitHub person of the machine values of your start prompt. Else it is the active account of `gh auth status`. Else it is the value of `<skill folder>/scripts/sofa-state kv get machine.instance`, run from the main folder. When no source gives a login, stop step 6 and say which source failed.
   - Run `sofa-people list --json`. 1 item of the batch, or 1 page of that list, must have that login as `github` (the case of the letters does not count).
   - Else ask the user which person has that login. Give at most 4 options: the people of the batch or of that list who most likely have it, and "a new person". When the batch and that list have no person, do not ask this question, because "a new person" is the only answer.
   - For a person of the batch, set `github` of that item. For a person who has a page but is not in the batch, add the object of that page from `sofa-people list --json` to the batch, and set its `github`. That object has each field of the page, so `add` keeps the role, the decision areas and the escalation of the page. For "a new person", ask the 3 questions of item 2 for the operator, set `github` to that login, and add the operator to the batch.
   - The user can skip this check. Then the readiness item `operator-page` blocks the start of the team, and the report of step 7 names the skip.
5. Run `add` with `--by agent:<your session name>` and `--confirmed-by human:<login of the person who answered>`.
