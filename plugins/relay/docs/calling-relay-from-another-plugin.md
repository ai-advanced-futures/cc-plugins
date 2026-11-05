# Calling relay from another plugin

This guide is for a plugin or a script that starts relay when no person is present. It
gives the launch line, the rules for the watcher, how to read the result, the engine
rules, and the duties of the caller. It applies to relay 5.0.0 and later.

## The launch line

Start a new root session in the caller's worktree:

```bash
cd "<worktree>"
claude -p "/relay:implement --non-interactive --worktree current --verify --spec <absolute spec path>" \
  --permission-mode bypassPermissions \
  --output-format stream-json --verbose \
  --max-turns 300
```

- `--non-interactive` tells relay that no person is present. Relay never waits for an
  answer. Where a normal run asks a question, this run uses a fixed answer. Where no safe
  answer exists, the run stops at once with a typed result.
- `--worktree current` keeps the run in this checkout. Relay does not make or enter a new
  worktree. Under `--non-interactive`, `current` is also the default.
- `--verify` adds the verify-until-clean loop after the build. An `ok` result then also
  means that the loop reported `clean`.
- `--spec <absolute spec path>` names the spec to build. When the spec frontmatter has
  `gh_issue: <n>`, the commit body gets `Closes #<n>`.
- `--output-format stream-json --verbose` writes one JSON event on each line. The final
  `result` event holds the last text of the run.
- `--max-turns 300` gives a long run enough turns.

The other five L3 commands (`verify`, `refine`, `execute`, `drive`, `diagnose`) also take
`--non-interactive`. They print no result block. When one of them stops, its last line is
`[relay] non-interactive: stop <blocked|error>: <reason>`.

## Why `claude -p` and not acpx

Measured on 2026-09-22 with acpx 0.16.0 and Claude Code 2.1.278:

- `acpx claude exec`: the turn ends before the Workflow ends, so the Workflow is killed
  (`wf_e327bc81-b13`, `status: killed`).
- An acpx named session: the Workflow completes (`wf_f78f2208-c93`), but the result goes
  only to the session history. The caller does not see it.
- `claude -p`: the session waits for the Workflow, and the final text holds the result
  (`wf_5993017e-4fc`, `status: completed`). The relay integration harness uses the same
  carrier (`tests/integration/conftest.py`).
- `claude -p` waits for background work only about 600 seconds after the turn ends
  (measured 2026-09-25: `wf_c36ba268-29d` and `wf_65b4f5c0-3f5` were killed at about 605 s).
  So under `--non-interactive` relay does not end its turn while the Workflow runs: it polls
  the run file with `scripts/wait-for-workflow.sh`. With that rule, a Workflow of 839 s
  completed under `claude -p` (`wf_2af734d9-2fa`). The caller does not need to do anything
  for this, but it must pass `--non-interactive`.
- At the end of a run under `--non-interactive`, relay closes every acpx session that is
  still open in the worktree (`scripts/close-run-sessions.sh`). So do not start two relay
  runs in one worktree at the same time.

Do not run relay in a sub-agent. A sub-agent does not have the `Workflow` tool, so the run
cannot start.

## Watch the child

Use the rules of `relay:delegate-and-watch`
([`skills/delegate-and-watch/SKILL.md`](../skills/delegate-and-watch/SKILL.md)):

1. Run the launch line with `run_in_background: true`, and send its output to a stream
   file.
2. In the same turn, poll the stream file. Never end the turn while the child runs. A turn
   that ends leaves the child with no watcher, and nobody reads its result.
3. The Bash tool stops a call after 10 minutes. A long run needs many polls. When a poll
   call returns and the child still runs, start the next poll call at once.
4. macOS has no `timeout` command. Use a bash loop on `$SECONDS`, and stop each poll call
   before the 10 minutes:

   ```bash
   start=$SECONDS
   until grep -Eq '"type": ?"result"' "<stream file>"; do
     if [ $((SECONDS - start)) -ge 540 ]; then
       echo "RELAY_CHILD=running"
       exit 0
     fi
     sleep 15
   done
   echo "RELAY_CHILD=exited"
   ```

5. When the child exits, read the result block (next section) and map it to one typed
   result: `ok`, `blocked` or `error`. When the child exits and the stream file has no
   `result` event, the run failed: treat it as `error`.

A `feature` run with `--verify` can take hours. The relay harness gives each run two hours.

## Read the result

The run prints one `relay.implement-result/1` block on one line, in a fenced `json` code
block:

```json
{"schema": "relay.implement-result/1", "status": "ok", "run_id": "wf_abc123", "branch": "feature/x", "commit": "abc1234"}
```

- Take the **last** fenced `json` block that has `"schema": "relay.implement-result/1"`.
  With `--output-format stream-json`, the final text is the `result` field of the final `result` event.
- No block means that the run failed. Treat it as `error`.
- The exit code does not tell the status. Relay cannot set the exit code of `claude -p`.
  Read the block.
- Ignore the keys that you do not know. A later relay can add keys.
- For a strong receipt, also check git:
  `git merge-base --is-ancestor <commit> <branch>`.
- The run record `~/.claude/relay/runs.jsonl` is advisory. It records the intent of a run,
  not its outcome. Do not use it to decide the status.

The keys:

| Key | Value |
|---|---|
| `schema` | Always `relay.implement-result/1`. |
| `status` | `ok`, `blocked` or `error`. No other value. |
| `run_id` | The Workflow run id (`wf_…`), or `null` when the run stopped before the Workflow started. |
| `branch` | The branch of the run, or `null` for a detached HEAD. |
| `commit` | The short hash of the commit that the spine `commit` node made, or `null` when that node made no commit. |
| `reason` | Present when `status` is not `ok`. Absent when `status` is `ok`. |

`ok` means that the run finished, the `commit` node made a commit, the completeness check
passed and, with `--verify`, the loop reported `clean`.

Some `reason` values that a caller can see:

| Status | Reason | Cause |
|---|---|---|
| `blocked` | `worktree-missing: <value>` | The `--worktree` value is not a worktree or a checked-out branch of the repository. |
| `blocked` | `branch-guard: <main\|detached HEAD>` | The run would build on `main` or on a detached HEAD. |
| `blocked` | `needs-decision: <node>: <question>` | A worker asked a question that no fixed answer covers. |
| `blocked` | `refine-spec: needs-decision` | A refine critic asked a question. `refine-plan` is the same for the plan. |
| `blocked` | `non-interactive: engine session-tree needs a person to answer escalations; pin in-session or acpx` | The engine is `session-tree` (see Engines). |
| `error` | `spec-missing: <path>` | The `--spec` file does not exist. |
| `error` | `completeness: incomplete: <node names>` | Nodes of the Workflow did not finish, also after one more run. |
| `error` | `completeness: indeterminate: <reason>` | The completeness check could not read the run. |
| `error` | `findings` | The verify loop ended and the branch still has problems. |
| `error` | `preflight: <first error line>` | A check before the Workflow failed, for example a missing dependency. |

## Engines

- **No pin.** `/relay:implement` runs with `--engine acpx --agent claude`. The machine
  needs acpx 0.21.1 or later on `PATH`, with a Claude agent that is logged in. Under
  `--non-interactive`, the flag is the consent that the verify loop asks for before its
  approvals-off acpx sessions.
- **In-session pin.** Put `{"engine": "in-session", "agent": "claude"}` in
  `.claude/relay.json` of the repository. This needs no acpx. A flag on the launch line
  (`--engine in-session --agent claude`) does the same for one run.
- **`session-tree`.** Under `--non-interactive`, this engine stops at once with `blocked`.
  It needs a person to answer escalations. Remove a `session-tree` pin before you call
  relay.

A flag beats a pin, and a pin beats the default.

## The caller's duties

- Get the operator's consent before you start relay with `--permission-mode
  bypassPermissions`. The run then asks for no approval.
- Get the operator's consent before you pass `--non-interactive`. The flag gives the
  consent for the approvals-off acpx sessions of the verify loop. Relay cannot check that
  the operator agreed.
- Use `bypassPermissions`. Under `--permission-mode auto`, the auto-mode rule
  `Create Unsafe Agents` can still stop a verify node. This is not measured under `auto`.
- Check the spec before you call relay. Relay does not read `lifecycle_state`. A caller that
  uses `lifecycle_state: specified` as its gate must check it itself.
