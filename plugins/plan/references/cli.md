# Reference: Plan commands

The Plan skills use the Python command line that ships with Plan. The Beads store is the write backend. Product PRD files are read-only input.

## Invocation and workspace

Every command runs from the target repository. The command prefix is:

```text
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE
```

`PROFILE` is an explicit workspace profile file path configured by setup, such as `.claude/plan/local.json`; it is not a discovered store name. `DIR` is an existing initialized Beads directory, usually the selected workspace's `.beads` directory. `ROOT` is the source repository root, which holds `docs/product/prd/`. Setup checks the selected store rather than initializing another one. `PLAN_WORKSPACE` can supply the profile when `--workspace` is absent. An explicit profile takes priority. A skill keeps the same profile for its whole run. A missing or unclear profile is a setup decision, not a reason to choose an unrelated store.

The command's `--help` is the source for exact arguments. Output is structured JSON; `--json` makes that output compact. `--actor ACTOR` or `PLAN_ACTOR` identifies the executing actor. State and claim changes require an explicit actor. Shell examples for the user have a `$ ` prefix; the prefix is not part of the executed command.

A workspace is local to one machine. With the automatic push on, the result of a content write has a `backup` block: `pushed: true`, or `pushed: false` with `error`. A failed push does not change the exit code of the write. [One factory on one machine](single-factory.md) gives the rules for sessions, claims, backup, restore, and the migration from shared mode.

## Commands

The following table gives the command forms after the prefix:

| Command | Purpose | Result used by skills |
| --- | --- | --- |
| `setup --beads-dir DIR --source-root ROOT` | Configure the selected profile file | Configured source and Beads paths |
| `unshare` | Convert a profile and a store from the removed shared mode to local, one time | `unshared: true` and the list `changed`; a second run gives an empty list |
| `backup` or `backup --remote NAME` | Commit pending Dolt changes and push the Plan data one time to `refs/dolt/data` of the backup remote of the profile, or of `NAME` | `backed_up: true`, the remote address, and the pushed commit in `data_commit` |
| `backup --remote NAME --auto on` or `backup --auto off` | Save the backup remote and the automatic push after each content write in the profile; no push | `configured: true` and the block `backup` |
| `describe` | Read selected store identity and supported operations | `workspace_id`, paths, `import_state`, the list `operations`, and `backup` with `remote`, `auto`, `pending`, `last_push_at`, and `last_error` |
| `prd` | Read PRD summary rows | IDs, paths, types, titles, descriptions, and hashes |
| `prd ID` | Read one full PRD page | Requirement fields, body, relationships, and hash |
| `new TYPE --title TEXT` | Create an item | Assigned ID in `record.id` |
| `list` or `list --type TYPE` | List Plan items | Candidate IDs and existing children; `--milestone ID` filters the phase |
| `show ID` or `show TYPE NUMBER` | Read an item | Stored fields, links, criteria, and body |
| `link ID REL TARGET` | Add a supported relationship | Stored relationship |
| `unlink ID REL TARGET` | Remove a supported relationship | Remaining relationships |
| `set ID FIELD VALUE` | Change a supported non-work-state field | Stored value; `lifecycle` maps to page `status` |
| `body ID --file PATH` | Store agreed body text | Stored body |
| `check` | Check the Plan model and source links | Errors, warnings, and completion result |
| `ready` | List available work | Eligible items with no live claim; `--type TYPE` and `--milestone ID` filter the result |
| `assign TYPE NUMBER OWNER` | Set responsibility | Stored owner |
| `status TYPE NUMBER STATE --actor ACTOR` | Request a work state | Actual state after blocker rules |
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
| `github apply --fingerprint HASH --writer LOGIN --actor ACTOR [--part [--max-writes N]]` | Publish the accepted preview as the configured writer, all at once or in parts | Verified bindings and publication result (`complete`), a partial result with `next_at`, or an exact refusal |

The creation options are `--description TEXT`, `--body-file PATH`, `--parent ID`, `--milestone ID`, repeatable `--trace PRD_REF`, `--item ID`, `--target-date DATE`, `--spec PATH`, and `--size SIZE`. Repeatable `--set FIELD=YAML` sets accepted fields, and `--link FIELD=TARGET` adds accepted relationships. Each option is used only for a type that accepts it. Parent, Milestone, and Criterion item references use IDs returned by Plan, not Product roadmap paths. `Criterion` and `AcceptanceCriterion` both name the criterion type. New execution Run records are outside planning; migration preserves existing Run evidence.

`status` accepts `--approved-by REF` for a transition that requires approval. `claim` and `heartbeat` accept `--lease 30m` to request a lease. A claim returns a `claim_token`. That exact token is required for heartbeat, release, and changes to held work through `status`, `set`, `body`, `link`, and `unlink`. A stale token is refused. `in-progress` and `in-review` map to stored `in_progress` and `in_review`.

Existing-record mutations accept `--expected-revision NUMBER` to refuse a stale item view. Creation and existing-record mutations accept `--request-id TEXT` to identify one exact operation. Creation has no expected revision because the record does not exist yet. A retry with the same request ID and unchanged payload returns the original `operation` and `operation.result`, plus the current `record` view. `operation.result` holds the revision, state, owner, and claim token at that operation; the current record can have changed. This is not a full historical record snapshot. Reusing the ID for another operation is refused. Actor, workspace, payload, and any claim token stay part of the same work attempt.

Before you continue work from a replay, compare `operation.result.revision` with `record.revision`. If they differ, get a fresh view and the current claim needed for that work. An earlier claim token does not prove current ownership.

`migrate --source PATH` selects a source roadmap when the default is not intended. Preview is the default. A Git source is read from a committed snapshot, with `HEAD` as the default, rather than concurrent uncommitted edits. An explicit non-Git source folder is read as files. Apply copies the roadmap into Beads with a stable source mapping; it leaves the Product roadmap files unchanged. A repeated apply of the same snapshot uses that mapping rather than creating duplicate items. `--revision COMMIT` selects a fixed Git snapshot, and `--fingerprint HASH` on apply refuses a source different from the accepted preview. Apply needs a target that is empty or holds an incomplete import of that same snapshot. Migration is not an ongoing source sync.

Preview returns a `mappings` row for each record with `source_id`, `source_path`, and the preserved `plan_id`. Apply and repeat apply also return each `beads_id`. Preview reads no Beads data. A failed Git check stops the copy; it does not select uncommitted files.

Import keeps each Product claim and gives it a Plan `claim_token`. A resumed copy keeps the token already saved in Beads. The holder reads that token through `show ID` before a change or heartbeat. A tokenless claim from an older import permits no held-work changes or renewal; after its lease ends, use `expire`, then claim eligible work again.

The Project summary uses its title, description, and body. `prd:/product.md` is a summary, not a trace target. Traces name typed requirement pages, such as a Capability or Scope. A full PRD path must match that exact path. Bare IDs and aliases can find a page at its current path. Moving a page leaves a broken stored trace until you remove that trace and add its current target.

## GitHub Project publication

`github configure` requires one Project record and an existing GitHub Project. It preserves imported `github` values. `--type-mode labels` or `--type-mode issue_types` selects an explicit representation; an existing choice is not silently replaced.

`github preview` makes no board change. Apply requires its fingerprint, the configured writer, and the same actual GitHub login. A caller-provided writer alone grants nothing, so a session that `gh` authenticates as a person cannot publish as the factory account. The command uses `gh` from the current `PATH`, so Sofa's authentication wrapper remains in use.

Publication records stable issue and Project item bindings. A human owner maps to a GitHub assignee. An agent owner appears as `Plan owner` in the managed issue text and has no GitHub assignee; the Plan claim stays unchanged. Missing board fields, status options, labels, or issue types are reported rather than silently omitted. A partial or uncertain result must not be reported as a complete board update. Reuse the recorded attempt; do not create replacement issues or modify Product roadmap files. The publisher does not pull issue state or assignees into Plan.

### Pace, parts and errors

- Pace: apply waits 1 second between the starts of 2 writes, and sends at most 400 writes in each 3,600 seconds. The start times are saved in the workspace, so the limit holds across calls, parts and fingerprints. A read has no wait.
- Why 400: GitHub allows 500 content writes an hour, and the sessions of 1 team share 1 App installation. The 100 writes that remain stay for the other sessions.
- What counts as a write: each `gh api` call with the method `POST`, `PATCH`, `PUT` or `DELETE`, except a GraphQL query, and each GraphQL call whose text starts with `mutation`. A read of the board or of the issues is not a write.
- Checkpoint: apply saves its progress after each 10 writes (a batch of 10 writes), and when the call ends.
- Board reads: apply reads the whole board 1 time at its start, 1 time after it made an issue or a milestone, 1 time after a card add failed, and 1 time to check the result. A card add returns the item ID, and apply writes the fields of the card from it.
- `--part [--max-writes N]`: send at most N writes (1 to 400; default 40 writes), save a checkpoint, and exit 0. `--max-writes` without `--part` is refused before any GitHub call.
- A call that has work left returns `complete: false`, `items_left`, `stopped` (`part-limit`, `hour-budget` or `rate-limit`) and `next_at` (a UTC time, or `null` when the next call can start now). With `rate-limit` it also returns `github_error` (`kind`, `status`, `retry_after`). Without `--part`, such a call exits 1 with the error "publication is partial; run apply again with the same fingerprint". Run apply again with the same fingerprint after `next_at`. A result with `complete: false` is not a published board.
- A Plan edit between 2 calls changes the fingerprint, and apply refuses the old one. A claim, a heartbeat and a release are Plan edits for this rule, because they save the record. After such an edit, get and accept a new preview, then run apply with the new fingerprint. The new preview keeps the checkpoint, so the work that is done stays done. A caller that claims or renews a lease between 2 parts (for example the publication loop of PLAN-STORY-619) needs a new preview each time.
- Rate limit: when GitHub refuses a call with a rate limit, apply waits at most 60 seconds, then runs the call 1 more time. If the wait is longer, or the second run is refused, the call ends. A refused create is checked by its marker before apply creates it again.
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
