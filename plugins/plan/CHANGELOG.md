# Changelog

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
