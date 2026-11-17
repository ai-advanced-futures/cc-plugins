# Changelog

## 0.5.1

A Plan call that its caller stops leaves no `gh` process that can still write to the board.

- The `gh` child of a GitHub call now stays in the process group of Plan. A stop of that group (the time limit of `sofa_plan.run`, or a Ctrl-C in a terminal) now also stops `gh`. A `SIGINT` to the Plan process alone also stops `gh`. A `SIGTERM` or a `SIGKILL` to the Plan process alone does not: this is a stated limit.
- The own time limit of a `gh` call now also stops a process below `gh` that left the group.
- `bd` and `git` do not change: they keep their own session.

## 0.5.0

A refused issue create finds the issue that GitHub made when the machine clock differs from GitHub time.

A minor step: in a call with no valid `Date`, a repository with more than 10,000 issues and pull requests makes the marker read reach the limit of 100 pages. The create then stops with "create outcome is unknown; no duplicate create will be retried" where 0.4.0 created it again.

- The pending mark of a create now uses the `Date` header of the GitHub replies, plus the seconds that passed on this machine since that reply. A machine clock that is more than 120 seconds ahead of GitHub time or behind it no longer gives a second issue and the stop "issue binding and markers are ambiguous".
- With no valid `Date` in the call, the marker read has no time stop. It reads the whole issue list, at most 100 pages.
- The saved field `pending_at` keeps its name. It holds GitHub epoch seconds, or `null`.

## 0.4.0

`plan github apply` paces its writes, reads the board once, and reports the real GitHub error.

A minor step: a run with no `--part` now exits 1 when it stops at the hour budget (400 writes in 60 minutes), at a second rate-limit refusal, or at a rate-limit wait of more than 60 seconds. It prints the result JSON with `complete: false`. Run apply again with the same fingerprint, or pass `--part`.

- Each GitHub error now has a kind: `rate-limit`, `secondary-rate-limit`, `timeout`, `http`, `graphql`, `network` or `other`. The message holds the kind, the HTTP status and the `retry-after` seconds. It holds no text of GitHub.
- Apply keeps 1 second between 2 writes and sends at most 400 writes in 3,600 seconds. The start times are saved in the workspace between calls.
- A rate-limit refusal waits up to 60 seconds and runs the call 1 more time. A create that is refused is checked by its marker before apply creates it again.
- A paged GraphQL read gives the cards of the board. It replaces `gh project item-list`, so the date values now match the board and the cap of 1,000 cards is gone.
- A new card is filled with the item ID that the add returns. Apply reads the full board at most 4 times in 1 call, and 1 more time when a create fails and apply checks for the issue.
- New options `--part` and `--max-writes N` (1 to 400, default 40) send 1 part of the writes and save a checkpoint. The result has `complete`, `items_left`, `stopped` and `next_at`.

## 0.3.1

The default time limit of one backup push (`PLAN_BACKUP_TIMEOUT`) is 45 seconds, not 15.

A patch step: the change sets 1 default value.

- A push of a 762-record store to GitHub took about 10 seconds (measured on 2026-11-16). A limit of 15 seconds left too small a margin, and a push that reaches the limit is a failed push.
- The limit stays below the 120-second wait for the store lock.

## 0.3.0

A repository has one factory on one machine. This release removes shared mode. It is a breaking change.

### Removed
- Shared mode: the `plan-coordination` Git gate, the journal `plan-shared-attempt.json`, the baseline file `plan-shared-baseline.json`, and the shared recovery.
- The commands `share` and `sync`, the options `setup --shared` and `setup --remote`, and the option `recover --previous-writer-stopped`.
- The skill `/plan:sync`.
- The keys `shared`, `distributed_claims`, and `automatic_publish` of `describe`.
- The reference `references/sharing.md`. `references/single-factory.md` replaces it.

### Added
- `unshare`: the migration from shared mode. It converts a shared profile and its store to local, with no network call. It keeps `workspace_id`, `control_id`, and each record. Each other command on a shared profile stops with an error that names `unshare`. Run it one time.
- `backup` and `backup --remote NAME`: one push. It commits pending Dolt changes and pushes the Plan data to `refs/dolt/data` of one Git remote. To restore, run `bd bootstrap` and then `setup`.
- `backup --remote NAME --auto on|off`: it saves the block `backup` (`remote`, `auto`) in the profile. With `auto` on, Plan pushes after each content write: `new`, `set`, `body`, `link`, `unlink`, `assign`, `status`, `migrate --apply`, `github configure`, `github apply`, and a `recover` that repairs a record. No push follows a claim command or a read.
- A failed push does not fail the write. The result gets `backup: {pushed: false, error}`, stderr gets one warning line, and the state file beside the profile records `pending` and `last_error`. The next push sends all the data. `PLAN_BACKUP_TIMEOUT` sets the time limit of one push (default 15 seconds).
- `describe` shows `backup`: `remote`, `auto`, `pending`, `last_push_at`, `last_error`.
- `PLAN_LOCK_TIMEOUT` sets the wait of a command for the store lock in seconds.
- After a failed push, Plan makes no automatic push for 60 seconds (`PLAN_BACKUP_RETRY`). A write in that time is saved and gets `pushed: false` with `push skipped`. With a remote that did not answer and no pause, 11 of 21 parallel commands stopped with `workspace is busy`.
- `unshare` makes the remote of the shared block the backup remote, with `auto` on.

### Changed
- `recover` repairs only a record with an incomplete write or a changed native field or link. Before, it wrote each record again. `recovered` lists only the repaired IDs.
- `check` reads the store one time, not two times. A write that does not change the links of a record reads those links one time, not two times.
- Each result keeps the key `saved` with the value `local`.
- A command waits 120 seconds for the store lock, not 20 seconds. With 20 seconds, 3 of 8 parallel writes on a store of 762 records stopped with `workspace is busy`.

### Not changed
- Claims, `github configure`, `github preview`, and `github apply` work as before. `github apply` still refuses a `gh` login that is not the configured writer.
- An actor name can be `agent:<station>` or `agent:<instance>.<station>`.
