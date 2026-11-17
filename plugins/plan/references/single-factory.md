# One factory on one machine

A repository has one Plan workspace on one machine. Many sessions on that machine can use the workspace at the same time. Plan has no mode for writers on two or more machines.

## Sessions and claims

Each Plan command takes the file lock `plan.lock` in the Beads directory. The lock lets one command read or write the store at a time. A command waits for the lock for 120 seconds at most. `PLAN_LOCK_TIMEOUT` sets another wait in seconds. A command that cannot get the lock in that time stops with `workspace is busy` and changes nothing. Run the command again.

On a store of some hundred records, one command holds the lock for 3 to 5 seconds. Thus parallel commands of 8 sessions wait in a line for about 30 seconds.

A claim gives one session the right to work on one item. `claim` returns a `claim_token`. The session renews the lease with `heartbeat` and gives the item back with `release`. A second session cannot claim an item that has a live claim. After the lease ends, `expire` removes the claim.

The profile stays on the machine. A worktree uses the profile of the main checkout, not a second store in the worktree.

All writers use Plan. A raw `bd` write does not do the checks of Plan.

## A command that stopped

If a write command stops before it completes, the record keeps the mark `pending`, and each other command on the workspace stops with an error that names `recover`. Run `recover`. It completes each incomplete write and restores each native field or link that differs from the Plan data. The result lists the IDs that it repaired in `recovered`.

## Backup

The backup is a push of the Plan data to the ref `refs/dolt/data` of one Git remote. Plan has no backup on a schedule. It pushes after each content write.

### Set the backup remote

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE backup --remote NAME --auto on
```

This command saves the block `"backup": {"remote": "NAME", "auto": true}` in the profile. It makes no push. `--auto off` stops the automatic push and keeps the remote. If Beads has no remote with that name, Plan adds it with the address of the Git remote `NAME` of the source root.

### Automatic push

With `auto` on, Plan commits and pushes after each successful write of one of these commands:

- `new`, `set`, `body`, `link`, `unlink`, `assign`, and `status` with a new state
- `migrate --apply`
- `github configure` and `github apply`
- `recover`, when it repairs a record

No push follows `claim`, `heartbeat`, `release`, `expire`, a read command, or a replay of an earlier request. The push runs inside the store lock, so the pushes of parallel sessions go in order. The result of the write gets `"backup": {"pushed": true, "remote": "NAME"}`.

With `auto` off, or with no backup remote, Plan makes no push and gives no warning.

### A push that fails

A failed push does not fail, block, or undo the write. The exit code and the result are those of the write. Plan adds `"backup": {"pushed": false, "remote": "NAME", "error": "TEXT"}` to the result and prints one warning line on stderr. The state file beside the profile (`local.backup.json` for the profile `local.json`) records `pending: true` and `last_error`.

After a failed push, Plan makes no automatic push for 60 seconds. `PLAN_BACKUP_RETRY` sets another pause in seconds, and `0` sets no pause. A content write in the pause is saved and gets `pushed: false` with an error that starts with `push skipped`. The pause is necessary because the store lock is held during a push: without the pause, a remote that does not answer makes each write wait for the full time limit, and the sessions behind it stop with `workspace is busy`. A manual push has no pause.

The next push, automatic after the pause or manual, sends all the data and clears `pending`. Thus no retry is necessary for the failed push. `describe` shows the state in `backup`: `remote`, `auto`, `pending`, `last_push_at`, and `last_error`.

One push has a time limit of 45 seconds, which is below the 120-second wait of another session for the store lock. `PLAN_BACKUP_TIMEOUT` sets another limit in seconds. Keep it below the value of `PLAN_LOCK_TIMEOUT`. A push that reaches the limit is a failed push. The store lock is held during the push.

### Manual push

`backup` pushes one time to the backup remote of the profile. `backup --remote NAME` pushes one time to that remote and does not change the profile. The manual push also reads `refs/dolt/data` from the remote and returns that commit in `data_commit`. A failed manual push gives exit code 1.

### Transport

Plan does not force a push. It ignores the session rules `url.<base>.insteadOf` and `url.<base>.pushInsteadOf`, so the address that Beads saved stays valid. It keeps the session credentials. Beads 1.3.4 can replace `refs/heads/__dolt_remote_info__` on the remote during a push. The repository must permit the two refs. A push changes no source branch.

Do not use `bd backup` for this: it writes to a folder or to DoltHub, not to the Git remote.

## Restore

Restore puts the data of the last backup on a machine that has no Beads directory. Records that were written after the last backup are lost.

1. Clone the source repository from the remote that holds `refs/dolt/data`, so that this remote is `origin` of the clone.
2. In the root of the clone, run `bd bootstrap --yes`. Beads clones the data from `origin` into `.beads`.
3. Run `setup --beads-dir DIR --source-root ROOT` with a new profile path. Setup finds the workspace control in the restored data and keeps its `workspace_id`.
4. Run `list` and `check`.
5. Run `backup --remote NAME --auto on`, because a new profile has no `backup` block and the automatic push is off.

`bd bootstrap` reads only `origin`, or the address in the Beads setting `sync.remote`. Thus a backup to a remote with another name needs that remote as `origin` of the clone for the restore.

If step 3 or step 4 gives an error that names `unshare`, the backup holds data from shared mode. Run `unshare`, then run step 4 again.

## Migrate from shared mode with `unshare`

Plan 0.2 had a shared mode for two or more machines. Plan 0.3.0 removed it. Each command on a shared profile stops with an error that names `unshare`.

Run `unshare` one time on the machine that keeps the factory:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE unshare
```

`unshare` does these steps and makes no network call:

1. It sets the workspace control in the store to schema 1 and removes its `sharing` block.
2. It writes the profile as schema 1, without the `sharing` block. The remote of the `sharing` block becomes the backup remote, with the automatic push on (`backup` in `changed`).
3. It deletes `plan-shared-attempt.json` and `plan-shared-baseline.json` from the Beads directory.

It keeps `workspace_id`, `control_id`, and each Plan record. The result lists the changed parts in `changed`. A second run changes nothing and gives an empty `changed` list. If a run stops between steps, run it again.

`unshare` does not delete the branch `plan-coordination` on the Git remote. Plan does not read that branch. An operator can delete it.

After `unshare`, run `describe`, `list`, and `check`. The first content write then pushes the data to the backup remote. To prevent that push, run `backup --auto off` first. Stop Plan on each other machine and delete the profile there.

## GitHub Projects

The board is a published view of Plan. One configured GitHub account, the writer, publishes it through `gh`. Apply compares the login that `gh` uses with the configured writer and refuses a different login. Thus a session with the credentials of a person cannot publish in place of the factory account.

Preview binds the source and the intended changes to a fingerprint. Apply keeps the existing bindings and records its progress. GitHub and Beads do not share a transaction: a partial publication stays partial until a checked retry completes it. After an ordinary Plan edit during a partial publication, get and accept a new preview. Apply keeps the earlier bindings and the uncertain creates while it publishes the current source. A binding intent from an older client without history evidence needs its exact before or after state; later edits to that intent stay blocked for inspection. Do not create a second issue because an earlier response was lost. A large publication runs in parts: `github apply --part` sends at most 40 writes (`--max-writes N` changes the limit), and the result says `complete: false` and `next_at` while work is left. Run it again with the same fingerprint, after `next_at`.

Publication does not pull issue state, assignees, or claims into Plan. Text that a person wrote outside a managed issue section stays unchanged.
