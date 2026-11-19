# Reference: Plan commands

The Plan skills use the Python command line that ships with Plan. The Beads store is the write backend. Product PRD files are read-only input.

## User-facing text

This rule covers all Plan questions, replies, reports, item views, saved prose, and published GitHub issue and board text.

Only Milestones, Features, and Stories appear with IDs. Each mention includes both its exact returned ID and its English title. Unsaved proposals have titles but no invented IDs.

Describe all PRD concepts and other Plan types in plain English: the relevant behavior, need, or constraint. Their IDs, aliases, and source paths stay out of visible text, source links, and quoted output so the explanation makes sense without a lookup. External links keep their destinations; their visible labels follow this rule. Code examples with commands or other literal content keep their text and arguments. A standalone source reference in inline code follows the display rule. Explain the code's purpose in nearby prose; do not use code blocks for reference lists. A missing source that Plan data or the PRD names (a trace, a link, a path with a PRD prefix) is a reported gap, not an invented description: publication stops and the error names the record and the reference. An ID or a path that no Plan record, PRD page or alias holds (a made-up example) stays as written.

Stored references, command arguments, and internal helper handoffs keep the actual source IDs, canonical paths, relationships, and code-written hashes. Resolve aliases to the source identity, such as `CAPABILITY-10`, rather than shortening IDs or changing stored references. Full helper records and CLI JSON are internal evidence; present their meaning under this rule. Reports retain each refusal's cause and each warning. Operational values, such as actors, claim tokens, and publication fingerprints, retain their exact form.

## Invocation and workspace

Every command runs from the target repository. The command prefix is:

```text
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE
```

`PROFILE` is an explicit workspace profile file path configured by setup, such as `.claude/plan/local.json`; it is not a discovered store name. `DIR` is an existing initialized Beads directory, usually the selected workspace's `.beads` directory. `ROOT` is the source repository root, which holds `docs/product/prd/`. Setup checks the selected store rather than initializing another one. `PLAN_WORKSPACE` can supply the profile when `--workspace` is absent. An explicit profile takes priority. A skill keeps the same profile for its whole run. A missing or unclear profile is a setup decision, not a reason to choose an unrelated store.

The command's `--help` is the source for exact arguments. Output is structured JSON; `--json` makes that output compact. `--actor ACTOR` or `PLAN_ACTOR` identifies the executing actor. State and claim changes require an explicit actor. Shell examples for the user have a `$ ` prefix; the prefix is not part of the executed command.

A workspace is local to one machine. With the automatic push on, the result of a content write has a `backup` block: `pushed: true`, or `pushed: false` with `error`. A failed push does not change the exit code of the write. A write and its automatic push hold the store lock for at most the lock budget, `PLAN_LOCK_TIMEOUT` minus 20 seconds (100 by default). The push gets the time that is left, at most `PLAN_BACKUP_TIMEOUT`; with less than 10 seconds left, it is skipped and the data stays pending. The `backup` block of a failed or skipped push also has `pending` and `last_push_at`. The error text of a push has no credentials, no token and no absolute path. A command that cannot get the store lock in `PLAN_LOCK_TIMEOUT` seconds (120 by default) stops with `workspace is busy; no operation started`, then a fixed hint: run `lsof` on the file `plan.lock` in the Beads directory to find the holder. [One factory on one machine](single-factory.md) gives the rules for sessions, claims, backup, restore, and the migration from shared mode.

## Commands

The following table gives the command forms after the prefix:

| Command | Purpose | Result used by skills |
| --- | --- | --- |
| `setup --beads-dir DIR --source-root ROOT` | Configure the selected profile file | Configured source and Beads paths |
| `unshare` | Convert a profile and a store from the removed shared mode to local, one time | `unshared: true` and the list `changed`; a second run gives an empty list |
| `backup` or `backup --remote NAME` `[--timeout SECONDS]` | Commit pending Dolt changes and push the Plan data one time to `refs/dolt/data` of the backup remote of the profile, or of `NAME`. `--timeout` is the limit of this push, from 1 to 3600 seconds; default `PLAN_BACKUP_TIMEOUT`; no lock budget | `backed_up: true`, the remote address (with no user and password), and the pushed commit in `data_commit` |
| `backup --remote NAME --auto on` or `backup --auto off` | Save the backup remote and the automatic push after each content write in the profile; no push | `configured: true` and the block `backup` |
| `describe` | Read selected store identity and supported operations | `workspace_id`, paths, `import_state`, the list `operations`, and `backup` with `remote`, `auto`, `pending`, `last_push_at`, and `last_error` |
| `prd` | Read PRD summary rows | IDs, paths, types, titles, descriptions, and hashes |
| `prd ID` | Read one full PRD page | Requirement fields, body, relationships, and hash |
| `new TYPE --title TEXT` | Create an item | Assigned ID in `record.id` |
| `list` or `list --type TYPE` | List Plan items | Candidate IDs and existing children; `--milestone ID` filters the phase |
| `show ID` or `show TYPE NUMBER` | Read an item | Stored fields, links, criteria, and body |
| `link ID REL TARGET` | Add a supported relationship | Stored relationship |
| `unlink ID REL TARGET` | Remove a supported relationship | Remaining relationships |
| `accept-drift ID TARGET --actor ACTOR [--approved-by REF]` | Accept a reviewed change of 1 traced PRD page | The new hash in the trace; the history event keeps the approval and both hashes |
| `set ID FIELD VALUE` | Change a supported non-work-state field | Stored value; `lifecycle` maps to page `status` |
| `body ID --file PATH` | Store agreed body text | Stored body |
| `check` | Check the Plan model and source links | Errors, warnings, and completion result |
| `ready` | List available work | Eligible items with no live claim; `--type TYPE` and `--milestone ID` filter the result |
| `assign TYPE NUMBER OWNER` | Set responsibility | Stored owner |
| `status TYPE NUMBER STATE --actor ACTOR` | Request a work state | Actual state after blocker rules. With no STATE and a profile with a `backup` block, the result also has the `backup` block of `describe` |
| `claim TYPE NUMBER --actor ACTOR` | Take work with a lease | Claim and actual state |
| `heartbeat TYPE NUMBER --actor ACTOR --claim-token TOKEN` | Renew the holder's lease | Updated claim |
| `release TYPE NUMBER --actor ACTOR --claim-token TOKEN` | Return held work | Cleared claim; claimed or in-progress work becomes ready or blocked, while other work states stay unchanged |
| `expire TYPE NUMBER --actor ACTOR` | End an expired claim | Cleared claim; live claims are refused |
| `history ID` | Read saved operation events | Actors, times, requests, and changes |
| `recover` | Complete each recorded incomplete write of a stopped command | The repaired IDs in `recovered`; not a fresh import |
| `migrate` | Preview a copy from a Product roadmap | Proposed items and source mapping |
| `migrate --apply` | Apply the previewed copy | Stable mapping to Beads IDs |
| `github configure --repo OWNER/REPO --owner OWNER --number NUMBER --writer LOGIN --actor ACTOR` | Check and save an existing Project and its publisher | Verified board settings; imported bindings stay intact |
| `github preview` | Compare a fixed Plan view with its GitHub Project | Fingerprint, source revision, intended changes, and warnings |
| `github apply --fingerprint HASH --writer LOGIN --actor ACTOR [--part [--max-writes N]]` | Publish the accepted preview as the configured writer, all at once or in parts | Verified bindings and publication result (`complete`), a partial result with `next_at`, or a refusal with its cause |

The creation options are `--description TEXT`, `--body-file PATH`, `--parent ID`, `--milestone ID`, repeatable `--trace PRD_REF`, `--item ID`, `--target-date DATE`, `--spec PATH`, and `--size SIZE`. Repeatable `--set FIELD=YAML` sets accepted fields, and `--link FIELD=TARGET` adds accepted relationships. Each option is used only for a type that accepts it. Parent, Milestone, and Criterion item references use IDs returned by Plan, not Product roadmap paths. `Criterion` and `AcceptanceCriterion` both name the criterion type. New execution Run records are outside planning; migration preserves existing Run evidence.

`status` accepts `--approved-by REF` for a transition that requires approval. `claim` and `heartbeat` accept `--lease 30m` to request a lease. A claim returns a `claim_token`. That exact token is required for heartbeat, release, and changes to held work through `status`, `set`, `body`, `link`, `unlink`, and `accept-drift`. A stale token is refused. `in-progress` and `in-review` map to stored `in_progress` and `in_review`.

A requirement drift is a trace whose PRD page changed after Plan stored the trace. `check` gives a drift warning for it. Review the change, then run `accept-drift ID TARGET`: it stores the hash of now, and the history keeps the actor, the approval and both hashes. A `human:` actor needs no approval. An `agent:` actor needs `--approved-by` with a hitl card link or a D-id. Plan checks the form of the approval, not who made it. The next change of the page gives a new drift. `link` refuses a page that the item already traces with another hash, and its message names `accept-drift`. To move a trace to a new page, unlink it, then link it. Limit: an agent can still clear a drift in 2 calls, `unlink` and then `link`, with no approval. Plan does not stop this path. Its history has 2 events and no hashes, so a review can see it. Use `accept-drift`, because it keeps the approval and both hashes (D-9293, D-9300). `check` gives no drift warning for an item whose state is `cancelled`. An item that leaves `cancelled` shows its drift again. A missing page is an error in each state. `check` compares the resolved milestone records, so a bare ID and a `/milestones/` path of the same milestone are 1 milestone.

Existing-record mutations accept `--expected-revision NUMBER` to refuse a stale item view. Creation and existing-record mutations accept `--request-id TEXT` to identify one exact operation. Creation has no expected revision because the record does not exist yet. A retry with the same request ID and unchanged payload returns the original `operation` and `operation.result`, plus the current `record` view. `operation.result` holds the revision, state, owner, and claim token at that operation; the current record can have changed. This is not a full historical record snapshot. Reusing the ID for another operation is refused. Actor, workspace, payload, and any claim token stay part of the same work attempt.

Before you continue work from a replay, compare `operation.result.revision` with `record.revision`. If they differ, get a fresh view and the current claim needed for that work. An earlier claim token does not prove current ownership.

`migrate --source PATH` selects a source roadmap when the default is not intended. Preview is the default. A Git source is read from a committed snapshot, with `HEAD` as the default, rather than concurrent uncommitted edits. An explicit non-Git source folder is read as files. Apply copies the roadmap into Beads with a stable source mapping; it leaves the Product roadmap files unchanged. A repeated apply of the same snapshot uses that mapping rather than creating duplicate items. `--revision COMMIT` selects a fixed Git snapshot, and `--fingerprint HASH` on apply refuses a source different from the accepted preview. Apply needs a target that is empty or holds an incomplete import of that same snapshot. Migration is not an ongoing source sync.

Preview returns a `mappings` row for each record with `source_id`, `source_path`, and the preserved `plan_id`. Apply and repeat apply also return each `beads_id`. Preview reads no Beads data. A failed Git check stops the copy; it does not select uncommitted files.

Import keeps each Product claim and gives it a Plan `claim_token`. A resumed copy keeps the token already saved in Beads. The holder reads that token through `show ID` before a change or heartbeat. A tokenless claim from an older import permits no held-work changes or renewal; after its lease ends, use `expire`, then claim eligible work again.

The Project summary uses its title, description, and body. `prd:/product.md` is a summary, not a trace target. Traces name typed requirement pages, such as a Capability or Scope. A full PRD path must match that exact path. Bare IDs and aliases can find a page at its current path. Moving a page leaves a broken stored trace until you remove that trace and add its current target.

## GitHub Project publication

`github configure` requires one Project record and an existing GitHub Project. It preserves imported `github` values. `--type-mode labels` or `--type-mode issue_types` selects an explicit representation; an existing choice is not silently replaced.

`github preview` makes no board change. Apply requires its fingerprint, the configured writer, and the same actual GitHub login. A caller-provided writer alone grants nothing, so a session that `gh` authenticates as a person cannot publish as the factory account. The command uses `gh` from the current `PATH`, so Sofa's authentication wrapper remains in use. The `gh` child stays in the process group of Plan, so a caller that stops the Plan group also stops `gh`. At its own time limit, Plan stops `gh` and each process below it.

Publication reads Markdown and the PRD to turn source references into English titles. Paths that start with `../` and enter a PRD folder identify PRD sources. Use repository paths for other files. A bare source filename must match one page. Markdown formatting can change. Code commands and external link destinations stay unchanged. A missing bundle, missing or ambiguous reference, or a title that cannot be resolved without a cycle stops publication rather than exposing an ID. The preview fingerprint includes the PRD evidence, so a source change needs a fresh accepted preview even after a partial publication. Hidden identity markers and existing user-written text outside the managed section stay unchanged.

Publication records stable issue and Project item bindings. A marker counts only in an issue or milestone that the configured writer made: REST `user.login` (an issue) or `creator.login` (a milestone), or GraphQL `author.login`, where GraphQL names an App with no `[bot]`. The board read and the marker read skip an item of another account: they do not bind it, do not count it for the 1-match rule, and do not stop. A bound issue keeps its binding with no author check. Limit: a migration that changes the writer must bind each issue of the old writer first, because the marker in an issue of the old writer with no binding no longer counts, and apply then creates a new issue. A human owner maps to a GitHub assignee. An agent owner appears as `Plan owner` in the managed issue text and has no GitHub assignee; the Plan claim stays unchanged. Missing board fields, status options, labels, or issue types are reported rather than silently omitted. A partial or uncertain result must not be reported as a complete board update. Reuse the recorded attempt; do not create replacement issues or modify Product roadmap files. The publisher does not pull issue state or assignees into Plan.

### Pace, parts and errors

- Pace: apply waits 1 second between the starts of 2 writes, and sends at most 400 writes in each 3,600 seconds. The start times are saved in the workspace, so the limit holds across calls, parts and fingerprints. A read has no wait.
- Why 400: GitHub allows 500 content writes an hour, and the sessions of 1 team share 1 App installation. The 100 writes that remain stay for the other sessions.
- What counts as a write: each `gh api` call with the method `POST`, `PATCH`, `PUT` or `DELETE`, except a GraphQL query, and each GraphQL call whose text starts with `mutation`. A read of the board or of the issues is not a write.
- Checkpoint: apply saves its progress after each 10 writes (a batch of 10 writes), and when the call ends.
- Board reads: apply reads the whole board 1 time at its start, 1 time after it made an issue or a milestone, and 1 time after a card add failed. A call that sent a GitHub write reads the whole board 1 more time to check the result (the check read). A call that sent no GitHub write uses its start read as the check read. A card add returns the item ID, and apply writes the fields of the card from it.
- `--part [--max-writes N]`: send at most N writes (1 to 400; default 40 writes), save a checkpoint, and exit 0. `--max-writes` without `--part` is refused before any GitHub call.
- Part budget: with `--part`, apply also stops on time. On a large board, a part that sends a GitHub write leaves the check read to the next part. It starts no write and no binding after 90 seconds from its start (`PART_SECONDS`). It starts a binding only when the longest binding of the call can still end inside the 90 seconds, and it starts the check read (the board read that checks the result) only when a read as long as its start read can end inside the 90 seconds. The first write or the first binding of a call always starts, so each part makes progress. A call that stops on time returns `stopped: part-limit`, the same word as the write limit.
- Lock time of 1 part: the start read, the work, and the end are inside the lock. The work ends inside the 90 seconds, then 1 binding at most, the end checkpoint, the 1 Dolt commit and the backup push follow. The backup push gets only the time that is left of the lock budget (100 seconds by default); a part that held the lock for about 96 seconds skips its push, and the data stays pending until a later push.
- Bindings: after the check read, apply saves the binding of each item whose saved binding is different (the card ID, the managed labels and dates, and the hash of the published values). A call that sent no GitHub write uses its start read as the check read, so a part that has only bindings left reads the board 1 time.
- The check of the earlier part: a call that ends before its check read (a stop on time, `hour-budget` or `rate-limit`) saves in its checkpoint, under `unverified`, each item whose writes it sent completely. For each changed key of the item it saves the digest of the board value before the write and the digest of the written value, not the text. The start read of the next call checks each saved key 1 time, before any write, and then removes it:
  - The written value is on the board, or Plan has a new value for the key: no error.
  - The board shows the value from before the write: GitHub took the write and did not keep it. The call ends with the error of the check read (for example `GitHub title verification failed; no publication success checkpoint`) and sends no write. The next call writes the item again, and the call after it gives the error again when GitHub again does not keep the write: each try is 1 write and 1 error.
  - The board shows another value (a person's edit on GitHub, or a value that GitHub changed, for example a cut body): no error. The call writes the Plan value over it and saves the key again, so a value that GitHub changes in the same way each time gives the error at the next check.
  An item that a call wrote only in part is not saved: the next call writes its keys that are still different, and then saves it. A call that starts its own check read clears `unverified`, because that read checks the same writes, and a complete publication removes the checkpoint. A new preview and `recover` do not change it. A limit: when a person sets a key back to the value from before the write between 2 calls, the next call gives the error 1 time, because the values do not show who made the change.
- Store commits: apply keeps its store writes in the Dolt working set and makes 1 Dolt commit when the lock ends, also when the call ends with an error. A stop (an interrupt) makes no commit. Each write is saved before the commit, and each later Plan command reads it. A failed commit does not fail the apply: the output gets `store_commit` with the error and stderr gets a warning, and the next commit of any Plan command records the writes.
- A call that has work left returns `complete: false`, `items_left`, `bindings_left`, `stopped` (`part-limit`, `hour-budget` or `rate-limit`) and `next_at` (a UTC time on the clock of this machine, or `null` when the next call can start now). `items_left` counts the items with GitHub work left and the bindings that the check read found. `bindings_left` counts only those bindings; it is `null` when the call stopped before the check, so `items_left` can be 0 while the check is still due. With `rate-limit` it also returns `github_error` (`kind`, `status`, `retry_after`). Without `--part`, such a call exits 1 with the error "publication is partial; run apply again with the same fingerprint". Run apply again with the same fingerprint after `next_at`. With `rate-limit`, `next_at` is the time of this machine when the call ended plus the wait in GitHub time, so a caller on the same machine compares it with its own clock. With `hour-budget`, it is 1 hour after the oldest write of the last hour, on the clock of this machine. A result with `complete: false` is not a published board.
- The record of a part: a call that ends with `complete: false` and no error writes the publication record `last` with `complete: false`, the fingerprint, the progress and the time. Only a record with `complete: true` (or a record of Plan 0.6.2 or earlier, which has no `complete` key) lets apply accept the fingerprint of an earlier preview with no write.
- A Plan edit between 2 calls changes the fingerprint, and apply refuses the old one. A claim, a heartbeat and a release are Plan edits for this rule, because they save the record. After such an edit, get and accept a new preview, then run apply with the new fingerprint. The new preview keeps the checkpoint, so the work that is done stays done. A caller that claims or renews a lease between 2 parts (for example the publication loop of PLAN-STORY-619) needs a new preview each time.
- Rate limit: when GitHub refuses a call with a rate limit, apply waits at most 60 seconds, then runs the call 1 more time. The wait is in GitHub time: the `retry-after` seconds, else `x-ratelimit-reset` (a GitHub time) minus GitHub time now, plus 30 seconds, else 60 seconds. GitHub time now is the `Date` of the newest GitHub reply of the call plus the seconds that passed on this machine since that reply, as for the pending mark below. So a machine clock that is ahead of GitHub time or behind it does not change the wait, and the call ends only when the wait of GitHub is more than 60 seconds. Limit: the wait can be longer by the time of 1 reply and by less than 1 second, never shorter. When no reply of the call has a valid `Date`, apply uses the machine clock in place of GitHub time, so a machine clock that is ahead of GitHub or behind it makes that wait shorter or longer. If the wait is longer, or the second run is refused, the call ends. A refused create is checked by its marker before apply creates it again. The marker read looks back to 120 seconds before the pending mark. The mark is in GitHub time: apply takes the `Date` header of the newest GitHub reply of the call (only the form `Tue, 17 Nov 2026 13:06:08 GMT`, and only when it is within 1 day, 86,400 seconds, of the machine clock), and adds the seconds that passed on this machine since that reply. A `Date` that is more than 1 day ahead of the machine clock or behind it is not GitHub time: apply uses it as a reply with no valid `Date`. So a machine clock that is ahead of GitHub time or behind it by at most 1 day does not move the mark, and a machine clock that is more than 1 day off gets the read with no time stop. Limit: when the `Date` comes from the clock of GitHub, the mark can be early by the time of 1 reply (at most 60 seconds) and by less than 1 second, never late. A `Date` that does not come from that clock (a proxy, a wrong `GH_HOST` server) and that is more than 120 seconds ahead of it, but within the bound, makes the mark late: the marker read can then miss the issue, and apply creates it 1 more time; the call then ends with "issue binding and markers are ambiguous", and a person must act. A change of the machine clock of more than 120 seconds during the call can move it. When no reply of the call has a valid `Date`, the marker read has no time stop: it reads each page of the issue list, at most 100 pages. Apply then binds the issue of the writer with the marker, or creates it 1 more time. When the list has more than 100 pages, the call ends with "create outcome is unknown; no duplicate create will be retried" or binds the issue that a full read finds.
- Prior create: apply marks a create as pending before it sends it. When a call ends with no reply to the create (the caller stopped it, or GitHub gave a failed reply and the read back found no issue), the next apply resolves it. When the board read at the start of the call finds the issue of the writer with the marker, apply binds it. Else apply waits until 30 seconds have passed since the start of the call, because GitHub ends each request after 10 seconds, and then makes the marker read of the rate-limit retry (back to 120 seconds before the pending mark; each page, at most 100, when the mark is null or more than 1 day ahead of the machine clock, because an earlier version saved such a mark from a far `Date`). It binds the 1 issue of the writer that holds the marker, or it creates the issue 1 time when no issue of the writer holds it. When more than 1 issue of the writer holds the marker, or the read cannot complete (more than 100 pages, an invalid list), the call ends with "a prior create has an unknown outcome; inspect GitHub before recovery" and the cause in parentheses, and it creates nothing. A rate limit of the read ends the call with `stopped: rate-limit`, and the next call reads again. The wait is inside the time limit of the caller. `recover` does not read GitHub. Limit: a `gh` that outlives a stop of the Plan process alone can send the create after the wait; the next read then finds 2 issues and stops.
- Error kinds: the message names 1 kind and no text of GitHub. The kinds are `rate-limit`, `secondary-rate-limit`, `timeout`, `http`, `graphql`, `network` and `other`. The message also gives the HTTP status and the `retry-after` seconds when GitHub sent them. Apply tests a failed call in this order, and the first match gives the kind: (1) `rate-limit`, when the header `x-ratelimit-remaining` is 0 or a GraphQL error has the type `RATE_LIMITED`; (2) `secondary-rate-limit`, when the status is 403 or 429 and the reply has a `retry-after` header, or the message says "secondary rate limit"; (3) `rate-limit`, when the message says "API rate limit exceeded"; (4) `timeout`, when GitHub says it could not respond in time; (5) `http`, for another status of 400 or more; (6) `graphql`, for a status 200 reply with errors; (7) `network`, when there is no status and the text names a connection failure; (8) `other`. The message patterns are a second sign only, because the headers are the signs that GitHub documents.

## Creation examples

The following examples show the shape of Plan writes. `PROFILE` is the selected workspace. `MILESTONE_ID`, `EPIC_ID`, `FEATURE_ID`, and `STORY_ID` are IDs returned by earlier Plan commands. Each PRD reference must exist in the configured source.

Create a Milestone, including a future phase with no children:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE new Milestone --title "First release" --description "Customers can book an available slot." --trace prd:/scope/SCOPE-01.md
```

Create an Epic in that Milestone:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE new Epic --title "Booking" --description "Customers find and book available slots." --milestone MILESTONE_ID --trace prd:/capabilities/CAPABILITY-03.md
```

Create a Feature under that Epic:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE new Feature --title "Slot search" --description "Customers see the available slots for a day." --parent EPIC_ID --milestone MILESTONE_ID --trace prd:/capabilities/CAPABILITY-03.md
```

Create a Story under that Feature:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE new Story --title "Pick a day" --description "As a customer, I want to pick a day, so that I can see its available slots." --parent FEATURE_ID
```

Create a separate Criterion for the Story:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE new Criterion --title "A full day has no available slots" --description "The day view states that no slot is available when every slot is taken." --item STORY_ID
```

A Feature criterion uses `--item FEATURE_ID` in the same way. Every criterion gets its own returned ID.

## Result handling

A successful command returns the value that the summary uses. Mutations return a `record` and an `operation`; creation's assigned ID is `record.id`. `show` returns the record directly. Stored fields are under `fields`, and `effective_state` is the current blocker-derived state. A nonzero exit means the requested operation did not complete; the command's error is the next action. A failed creation has no assumed ID. A failed status request has no assumed state. A failed check leaves the run partial. A warning is shown even when the command exits with 0.

Trace hashes, actual dates, derived progress, and claim times come from Plan code. The Plan interface supplies the model checks that direct `bd` writes bypass.
