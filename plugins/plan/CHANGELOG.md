# Changelog

## 0.7.0

The final part of `github apply` ends in a time budget, makes 1 Dolt commit, and frees the lock (PLAN-STORY-674).

A new stop of a run that works today: a `--part` call that ended with `complete: true` on 0.6.2 can now end with `complete: false` and `stopped: part-limit`. So this is a minor step.

- The part budget: with `--part`, `apply` starts no write and no binding after 90 seconds from its start (`PART_SECONDS`). A binding starts only when the longest binding of the call can still end inside the budget. The first write or the first binding of a call always starts, so each part makes progress. The stop word is `part-limit`, so `sofa-publish` needs no change.
- The check read is not made again in a call with no GitHub write: that call uses its start read as the check read. A part that has only bindings left reads the board 1 time, not 2 times.
- On a large board, a part that sends a GitHub write leaves the check read to the next part, because the check read does not fit in the budget. Such a part returns `bindings_left: null`.
- 1 checkpoint for each binding of the check read, not 2. The recovery of a stopped binding is the same.
- 1 Dolt commit for each apply, not 1 commit for each store write. The writes stay in the Dolt working set until the lock ends. A call that ends with an error also commits. A stop (an interrupt) makes no commit, and the next commit of any Plan command records the writes. A failed commit is a warning: the output gets `store_commit` and stderr gets a warning, and the exit code does not change.
- The record `last` of a part that ends with `complete: false` has the key `complete: false`. The replay check reads only a complete record, so a record of 0.6.2 with no `complete` key replays as before.
- The result gets the new key `bindings_left`, and `progress` gets the key `bindings`. `items_left` now also counts the bindings that the check read found.
- Limit: on a large board, a part that sends a GitHub write makes no check read, so a write that GitHub takes and does not keep gives no verification error (issue 2971). The sign is `items_left` that does not fall across parts with writes.

## 0.6.2

The board read and the marker read count a marker only in an item that the configured writer made (issue 2901).

A patch step: it adds no stop to a run that works on 0.6.1, and it removes 3 stops that an item of another account gave.

- The 2 reads that match a marker are the board read (at the start of `preview` and `apply`) and the marker read (the read back after a failed reply, the retry after a rate limit, and the resolve of a prior create). Each now knows the account that made each issue and milestone: GraphQL `author { login __typename }` and REST `user.login` for an issue, and REST `creator.login` for a milestone. GraphQL gives the login of a GitHub App with no `[bot]` and the type `Bot`, so the code adds `[bot]` for a `Bot`. The compare with the configured writer is exact, as the viewer check of `apply`.
- An item of another account that holds the marker is skipped: apply does not bind it, does not count it for the 1-match rule, and does not stop for it. The check also covers the legacy marker `<!-- okf: <path> -->`. An account that GitHub does not give (a deleted account) is not the writer.
- A bound issue keeps its binding with no author check, because a binding is a saved Plan decision. So an imported issue that a person made keeps its binding.
- The 3 stops that go: "issue binding and markers are ambiguous" for a bound record and a foreign issue with its marker, "duplicate issue markers" for a foreign issue with the marker 2 times, and "a prior create has an unknown outcome" for a foreign issue and the own issue in the wait.
- Limit: a migration that changes the writer must bind each issue of the old writer first. The marker in an issue of the old writer with no binding no longer counts, so apply creates a new issue.
- A marker in an issue that a person made, with no binding, is no longer adopted. Apply creates an issue of the writer.
- Each issue and milestone of the snapshot has the new key `author`, so a preview of 0.6.1 has a fingerprint that 0.6.2 does not give. Apply of that fingerprint ends with "publication fingerprint changed; preview again before writing". `sofa-publish step` makes a new preview before each part, so it is not affected.

## 0.6.1

After a stopped create, the next apply resolves the unknown outcome with the marker read, so a stop by the caller does not need a person.

A patch step: it removes a case that ended the call, and adds none to a run that works on 0.6.0. A resolving apply waits at most 30 seconds, inside the time limit of the caller.

- A create can end with no reply: the caller stops Plan during the create, or GitHub gives a failed reply and the read back finds no issue. The next apply used to end with "a prior create has an unknown outcome; inspect GitHub before recovery". Now it settles the create. When the board read at the start of the call finds the issue with the marker, apply binds it. Else apply waits until 30 seconds have passed since the start of the call (GitHub ends each request after 10 seconds), and then makes the marker read. It binds the 1 issue (or milestone) that holds the marker, or it creates the issue 1 time when no issue holds it. The wait uses a clock that a change of the machine time does not move, so a machine clock that is set back does not make the wait longer (issue 2900).
- The cases that still end the call keep the old text, with the cause in parentheses after it: more than 1 issue holds the marker, the issue list has more than 100 pages, or the list is invalid. In these cases apply creates nothing, and a person must act. A rate limit of the marker read ends the call with `stopped: rate-limit` and `next_at`, and the next call reads again.
- A failed reply from GitHub still ends its own call with "create outcome is unknown; no duplicate create will be retried". A caller such as `sofa-publish` still sees `unknown-create` for that call, and a person is still told. The next apply then resolves the create. Only a stop by the caller needs no person.
- `recover` does not change: it does not read GitHub. After a stop, run `recover`, and then the next apply.

## 0.6.0

A Plan call that its caller stops leaves no `bd` write that can run beside a `recover`.

A minor step: after a stopped backup push, the next Plan call can be refused with `workspace is busy` where 0.5.1 ran it. A `git` process that `bd` started in flight at the stop holds the store lock until it ends. A call that waits `PLAN_LOCK_TIMEOUT` (120 seconds) for the lock is refused with `workspace is busy; no operation started` and changes nothing. Run it again. `lsof <Beads directory>/plan.lock` names the holder.

- The error `workspace is busy; no operation started` now ends with a fixed hint: the store lock is held by another process; run `lsof` on the file `plan.lock` in the Beads directory to find it. The first sentence is the same as before. The hint holds no path and no pid (issue 2890).
- The `bd` commands of the backup push (`dolt remote list`, `dolt remote add`, `diff`, `dolt commit` and `dolt push`) now stay in the process group of Plan. A stop of that group (the time limit of `sofa_plan.run`, or a Ctrl-C in a terminal) now also stops `bd`. The own time limit of these commands also stops each process below `bd`, also a `git` process that has its own session.
- Each `bd` child of a command that holds the store lock now holds the lock too. A `SIGKILL` to the group of Plan, or to the Plan process alone, no longer frees the lock while a `bd` or a `git` of that command still runs. A `recover` can then not write beside a push that was stopped.
- A normal end, and each unwind, still free the lock at once for each holder.
- A stopped backup push leaves no incomplete Plan write, because the push changes no record. The `recover` after it has nothing to finish.

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
