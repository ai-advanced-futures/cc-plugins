---
name: delegate-and-watch
description: Use to background one acpx worker turn, block on it in the same turn with a bounded foreground poll, classify the outcome into one of five exit buckets (done/not-done/blocked/needs-decision/errored), and route via a router-loop — the watcher accumulates at each turn boundary, so context cost is O(turns).
user-invocable: false
---

<!-- EXECUTION PATH: run_in_background + blocking in-turn poll (never end the turn while waiting) -->

# delegate-and-watch

delegate-and-watch backgrounds one acpx worker turn, blocks on that turn inside the same
watcher turn with a bounded foreground poll, and routes through a five-bucket gate on each
turn boundary.

## TURN-LIFETIME RULE (non-negotiable)

- **Turn end IS termination.** An agent node has exactly one turn. When its final message is
  emitted the process is torn down; nothing resumes it, and no notification is delivered to a
  turn that has ended. Any child process still running is orphaned.
- **Never end a turn while waiting.** If the final message would say *"awaiting"*, *"parking
  until"*, *"I'll classify once it exits"*, or *"the harness will notify me"*, the node has
  already failed.
- **`park` is not available to an agent node.** It is a Workflow-graph control-flow primitive;
  a leaf has no resumable pause.
- **`Monitor` is not a wait mechanism here.** It arms an out-of-band watcher whose event is
  delivered to a future turn. There is no future turn.
- **Backgrounding is permitted; abandoning is not.** `run_in_background: true` is correct only
  when it is immediately followed, in the same turn, by a blocking in-turn poll.
- **On budget exhaustion, emit a typed failure, never park.** Surface `ROLE_RESULT=ERRORED`
  with `ERRORED_REASON=watcher_budget_exhausted`. A typed failure beats a null node.

The mandated wait primitive is one foreground `Bash` call on the session itself, re-issued
as many times as the worker needs:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/acpx-wait.sh" \
  --session "$ACPX_SESSION_NAME" --cwd "$ACPX_CWD" --engine "$ACPX_ENGINE" \
  --cursor-file "$ACPX_WATCH_CURSOR_FILE" --budget "${WATCH_BUDGET:-540}"
```

It reads `acpx sessions watch`, bounds itself with the shell's own `SECONDS` counter, and
saves a cursor so the next call resumes where this one stopped. A dead worker is now
reported by acpx, not inferred from a process list.

Give the `Bash` call the tool's maximum timeout, `600000` milliseconds. Write that number
into the call. The default, `120000`, is shorter than the wait's own budget, so the tool
ends the call before the budget does and every wait costs an extra turn.

Branch on the exit code:

- `0` (`WAIT_RESULT=settled` or `closed`): the turn is over. The driver still has to
  rebuild the text and write `<session>.turn.log`, which takes well under a second. Poll
  that file for the envelope for up to 30 seconds, then read its tail as before. An absent
  envelope after that routes to `errored` with `unparseable_envelope`.
- `75` (`running`): the worker is still working. Re-issue the same call. When the
  re-issues are spent, surface `ROLE_RESULT=ERRORED` with
  `ERRORED_REASON=watcher_budget_exhausted`.
- `2`: route to `errored` with `ERRORED_REASON=watch_usage`. The sidecar was incomplete.
- `1`: route to `errored` with `ERRORED_REASON=watch_<reason>`, taking `<reason>` from the
  `WAIT_ERROR=` line: `watch_outcome_unknown` when the owner disappeared before it
  recorded a result, `watch_owner_unsupported` when an older acpx owns the session,
  `watch_no_session` when the record is missing, and `watch_unknown` for every other
  reason.

Two exceptions, and only two.

`watch_no_session` within the window — `RELAY_WATCH_GRACE_SECONDS`
(default 10) of `ACPX_LAUNCHED_AT` — is treated as `running` and the wait is re-issued. The
session record is created inside the backgrounded dispatch, by `sessions ensure`, after
preamble assembly and the sidecar write, so a wait issued before that completes can see no
record yet. After the window, `watch_no_session` routes to `errored` as stated above.

A dispatch refused before its sidecar exists never reaches this wait: Step 2's sidecar
gate reads that refusal first. Before it routes `watch_no_session` to `errored`, read the
backgrounded dispatch output all the same, and apply the same `engine_error` rule, for a
refusal that comes after the sidecar write.

A `cursor_*` reason (`cursor_invalid`, `cursor_foreign`, `cursor_future`, `cursor_expired`)
is treated as `running` and the wait is re-issued. `acpx-wait.sh` deletes the rejected
cursor file before it returns, so the next call starts from the retained window and reads
the session. Routing the first one to `errored` throws away a dispatch the very next call
would have read. The re-issue budget bounds this, exactly as it bounds `running`.

A 30-minute dispatch costs about four of these calls. That is cheap; a null node is not.

## Watcher tier

The watcher's `agent()` node is generated with the pinned pair `scripts/resolve-tier.sh
watcher` prints — `model=sonnet effort=low` — not with a per-role tier and not with the
session model. This is a node-kind constant: the watcher does the same job (launch, wait,
classify, route) whatever role it delegates, and the real reasoning happens inside the
acpx worker session, whose model comes from the binding's `modalities.*`. Sonnet is the
floor rather than haiku because two duties carry judgment — composing the continuation
prompt each turn and routing `blocked`/`needs-decision` — and nothing downstream reviews
the prompts, only the artifacts. Effort stays low because the watcher is the long-lived
node: its context accumulates O(turns), so its per-token cost compounds. The pin honors
the same `in_session_tiers` gate as every role row — when tiers are off the watcher line
prints `inherit` and the node takes neither opt.

## Steps

This skill realizes the `multi-turn-dispatch` L1 shape: one WARM-session actor is driven
across multiple turns while the watcher maintains its own accumulated context. Drive it
as follows:

1. **Source the env sidecar, only after the gate.** The `${session}.env` sidecar written by
   `acpx-dispatch.sh` carries the 9-var (codex) or 10-var (claude/opencode) driver
   contract already resolved from the binding and turn protocol. Do not re-derive those
   values in the watcher body. Read it only after Step 2's sidecar gate accepts it, on
   every turn: each launch deletes the old sidecar first, and the dispatch writes a new
   one.
   A missing sidecar is never a reason to launch again: apply the sidecar gate to the output
   of the dispatch that already ran.

   **One Bash call is one shell.** A variable that a `source` sets, an `export`, and a
   `trap` last only until that Bash call ends. The watcher loop spans many calls (the
   launch, the gate, each wait, the close), so no shell lives for the whole loop. Read the
   sidecar values again after each gate pass, and write them into each later call of that
   turn, and into the close block, as literal values. Each launch writes a new `ACPX_LAUNCHED_AT`, and the
   `watch_no_session` window counts from the value of the current turn, never from turn
   1.

2. **Background the worker turn, then block on it in the same turn.** `delegate` one worker
   turn via `run_in_background=true` so the turn's stdout lands in a file rather than in the
   watcher's context. The entry command is
   `bash "${CLAUDE_PLUGIN_ROOT}/skills/dispatching-acpx-agents/acpx-dispatch.sh"`; it takes
   no positionals in the dispatch path — every input is env-passed, per its own usage
   header: `ACPX_ROLE_SLUG`, `ACPX_BINDING_PRESET` (or `ACPX_BINDING_JSON`),
   `ACPX_INPUTS_JSON`, `ACPX_RUN_ID`, `WORKTREE` are required, `ACPX_EXPECTED_MAJOR` and
   `ACPX_DRY_RUN` are optional, and its stdout is one line of JSON, the dispatch result. See
   `relay:dispatching-acpx-agents` for the wrapper contract this entry command implements.
   Launch it with an end marker, so the output shows when the dispatch has ended:
   `bash "${CLAUDE_PLUGIN_ROOT}/skills/dispatching-acpx-agents/acpx-dispatch.sh"; echo
   "RELAY_DISPATCH_EXIT=$?"`. The worker runs its session under the name given in the env
   sidecar (`ACPX_SESSION_NAME`).

   **Delete the old sidecar before every launch**, the first one and each re-entry from
   `not-done` or a later round: `rm -f "$SIDECAR"`. Every turn of one role in one run uses
   the same sidecar name, and nothing else deletes it. Without the delete, an old sidecar
   passes the gate below at once, even when the new dispatch was refused, and the watcher
   then waits on the previous session until its budget is spent.

   **Sidecar gate.** Immediately after the launch — same turn, no intervening final
   message — and before any `source` or wait step, wait for the sidecar
   (`~/.acpx/sessions/${ACPX_RUN_ID}-${ACPX_ROLE_SLUG}.env`, or the
   `ACPX_SESSION_NAME_OVERRIDE` name; the same path as `$SIDECAR`) or for the
   `RELAY_DISPATCH_EXIT=` line. The dispatcher writes the sidecar to a temporary file and
   moves it into place, so a sidecar that exists is complete. The
   dispatcher refuses some dispatches before it writes the sidecar or starts a session. It
   exits `68`. For a refused Codex home (relay 5.1.0) it also prints one JSON result line
   with `"status":"engine_error"` and `"error":"codex_home_refused"`; the other refusals
   print their reason to stderr only. Without this gate, the scaffold's `source` fails,
   `acpx-wait.sh` exits `2`, and the reason is lost as `watch_usage`. Give the `Bash` call
   the `600000` millisecond timeout.

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/acpx-dispatch-gate.sh" "$SIDECAR" "$DISPATCH_OUTPUT_FILE" "${WATCH_BUDGET:-540}"
   ```

   `$DISPATCH_OUTPUT_FILE` is the output file of the backgrounded launch. The script waits
   for the sidecar or the `RELAY_DISPATCH_EXIT=` line, then prints the route. Route on
   what it prints:

   - `GATE=sidecar` (exit `0`): read the sidecar, then go on to the wait below.
   - `GATE=errored` with `ERRORED_REASON=<error>` from a JSON line with
     `"status":"engine_error"` (exit `1`): route to `errored` with that
     `ERRORED_REASON`, for example `codex_home_refused`, and surface `ERRORED_DETAIL` as
     the detail. It holds the fix, for example "Unset CODEX_SQLITE_HOME for relay runs".
   - `GATE=errored` with `ERRORED_REASON=dispatch_no_sidecar` (exit `1`): any other end,
     or the budget is spent. Route to `errored` with that reason, and surface the
     `ERRORED_DETAIL` lines (the last lines of the dispatch output: the
     `RELAY_DISPATCH_EXIT=` code and the stderr reason) as the detail.

   Each `GATE=errored` route is a terminal result, so run the Step 6 close block: after a
   re-launch, the session of the earlier turn is still open.

   Never launch the dispatch again because the sidecar is missing.

   Then issue the mandated wait primitive from the turn-lifetime rule above, with the
   sidecar values written in as literals:
   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/acpx-wait.sh" --session "$ACPX_SESSION_NAME" --cwd
   "$ACPX_CWD" --engine "$ACPX_ENGINE" --cursor-file "$ACPX_WATCH_CURSOR_FILE" --budget
   "${WATCH_BUDGET:-540}"`. Re-issue that same call as many times as the worker needs; a
   30-minute dispatch costs about four of them. When the budget is spent and the worker has
   still produced no envelope, surface `ROLE_RESULT=ERRORED` with
   `ERRORED_REASON=watcher_budget_exhausted` rather than ending the turn on an outstanding
   dispatch.

3. **Read bounded output.** Once the wait returns, `read` the tail of the worker's turn
   content log (`~/.acpx/sessions/${session}.turn.log` — the dedicated turn-content
   channel written by the thinned driver). Bound to one `Read` tool-call pair per turn.
   Extract the envelope lines matching `^([A-Z][A-Z0-9_]*=.*|${terminal_token})$`.

4. **Classify into the five-bucket gate.** `classify` the captured envelope against this
   closed label set — reject any value outside it rather than guessing a route:

   > **Unparseable-envelope guard:** if `classify` produces no matching bucket because the
   > driver output contains neither the terminal token nor any `KEY=VALUE` envelope line (raw
   > prose only), the watcher routes to `errored` with `ROLE_RESULT=ERRORED` and
   > `ERRORED_REASON=unparseable_envelope`. It does not route to `not-done`, because a
   > re-dispatch hides the failure. [inferred]

   | bucket | condition |
   |--------|-----------|
   | `done` | terminal-token line present AND (no verify_artifact OR artifact freshness verified) AND (role is not writer-class OR landing-verify passed — edits present OR valid no-change signal with pre-flight pin confirmed) |
   | `not-done` | terminal-token absent, reply non-empty (rc=0 in-progress — or rc≠0 with partial output) — eligible for re-dispatch |
   | `blocked` | first content line matches `^BLOCKED:` |
   | `needs-decision` | first content line matches `^NEEDS_DECISION:` (terminal; session left open; PARKED=1; under `RELAY_NON_INTERACTIVE=1` the session is closed and PARKED stays 0) |
   | `errored` | non-zero rc AND empty reply, OR unrecoverable driver error, OR the envelope carries `ERRORED_REASON=config_replay_failed` |

   > **Session-config replay failure:** acpx >= 0.13.1 re-applies a reconnected session's
   > saved model and config options, and reports a failure instead of continuing on adapter
   > defaults. `acpx-envelope.sh` turns that report into `ERRORED_REASON=config_replay_failed`
   > and each session driver emits it as `ROLE_RESULT=ERRORED`. Route it to `errored`, never
   > to `not-done`, because re-dispatching would run the worker on a model it did not ask for, and
   > the turn's output would be attributed to the pinned model.

   > **Writer-role landing-verify in the done-gate:** When the dispatched role has
   > `role-class: writer`, run the landing-verify from `docs/dispatch-contract.md`
   > (Writer-Role Landing Contract) after the terminal token is confirmed. Run it in
   > `WORKTREE` or `WORKTREE_PATH`, the path the entry-point command set. Do not use
   > `ACPX_CWD`, because it is an internal session-driver env var, not the fixer's target path.
   > When the landing-verify fails, reclassify the turn as `errored` with
   > `ERRORED_REASON=landing_verify_failed`. This stops a
   > wrong-worktree dispatch (Variant B) from green-lighting a round that changed nothing.

5. **Route via the router-loop.** `branch` on the bucket:
   - `done`: exit the loop, surface the result envelope.
   - `not-done`: `loop-until` re-enters step 2 within the turn cap (value from
     `RELAY_MAX_TURNS`, default 10; set `ROLE_RESULT=MAX_TURNS_REACHED` when the
     cap is reached).
   - `blocked`: `abort` with the blocked reason; surface `ROLE_RESULT=BLOCKED`.
   - `needs-decision` without `RELAY_NON_INTERACTIVE=1`: set `PARKED=1`, surface
     `ROLE_RESULT=NEEDS_DECISION` and `QUESTION_TEXT=<text after the colon>`, and exit normally.
     Make no session call. Run the Step 6 close block with `PARKED=1` written in: its trap
     then leaves the session open, and no acpx version relay supports has a call that would
     leave it any other way.
   - `needs-decision` under `RELAY_NON_INTERACTIVE=1` (the watcher prompt carries this line when
     the caller passed `--non-interactive`): no person will answer the question. Leave
     `PARKED=0` and run the Step 6 close block: no other step closes the session. Still surface
     `ROLE_RESULT=NEEDS_DECISION` and `QUESTION_TEXT=<text after the colon>`, and exit
     normally. The bucket stays `needs-decision`; the caller maps it to a `blocked` result.
   - `errored`: `abort` with the error detail; surface `ROLE_RESULT=ERRORED`.

6. **Close step.** The watcher owns the `sessions close` cleanup. Run the close block (see
   Bash scaffolding below) once, as its own Bash call, when the router reaches a terminal
   result: `done`, `blocked`, `errored` (also `watcher_budget_exhausted` and a `GATE=errored` route),
   `MAX_TURNS_REACHED`, or `needs-decision`. Never run it before a wait, between waits, or
   on `not-done`: the `not-done` re-launch reuses the warm session. For an interactive
   `needs-decision`, run it with `PARKED=1`, so the session stays open; under
   `RELAY_NON_INTERACTIVE=1`, `PARKED` stays `0` and the session closes. The session
   drivers (thinned to single-turn invocations) never close the session.

## Refine critic roles

The dispatched role can be a refine critic: `roles/spec-simulator.md` or
`roles/plan-simulator.md`. Then the `done` bucket runs one more command before it surfaces
the result envelope:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/refine-node.sh" "<subject>" "<snapshot>" "<findings>"
```

This is the same line the in-session critic node runs. It writes the subject snapshot
and prints the one verdict line `refine-verdict.sh` returns; the watcher relays that
line unchanged as the node's `verdict_line`. The worker role writes no snapshot itself.
A non-zero exit from `refine-node.sh` is an `errored` outcome, the same as any other
failed shell step in this skill.

## Bash scaffolding

This is the close block of Step 6. Run it once, as its own Bash call, at a terminal
result, also when the last gate routed to `errored`. Write into it the literal
`ACPX_CWD`, `ACPX_ENGINE` and `ACPX_SESSION_NAME` values that this watcher read at its
own last accepted gate pass. The block reads no file: other runs and worktrees share
`~/.acpx/sessions/`, and a session name does not always hold a unique run id, so a file
there can belong to another run's session that is still open. When this watcher never passed
a gate, it started no session: do not run the block. Never run it as a step
before the wait: a `trap` fires when its Bash call ends, so a trap set before the wait
closes the session just after the launch. The `PARKED`-conditional trap stays the one
place that closes the session. This is the Phase D2 gate criterion: the trap must be
present in the delegate-and-watch SKILL.md bash scaffolding, not merely in hypothetical
generated code.

A trap lives only for the Bash call that set it, so it cannot close the session when the
watcher node dies in the middle of the loop. Under `--non-interactive`, the run calls
`scripts/close-run-sessions.sh` once after its Workflow ends, and that script is the close
for this case. In an interactive run, such a session stays open until you close it.

The same gap applies when the sidecar gate spends its budget and routes
`dispatch_no_sidecar`: the backgrounded `acpx-dispatch.sh` can still be running, and it can
then start a session that no watcher waits on or closes. The same is still true after the
`watch_no_session` window, as on main: the dispatch writes the sidecar before `sessions
ensure`, so an ensure that takes more than 10 s routes `errored` while the dispatch keeps
running. Only `close-run-sessions.sh`, under
`--non-interactive`, closes such a session.

```bash
#!/usr/bin/env bash
# delegate-and-watch close block. One Bash call, at a terminal result only.
# Write in the values this watcher read at its own last accepted gate pass. Read no file
# from ~/.acpx/sessions: other runs share that folder and can use the same session name.
ACPX_CWD='<ACPX_CWD from the last accepted gate pass>'
ACPX_ENGINE='<ACPX_ENGINE from the last accepted gate pass>'
ACPX_SESSION_NAME='<ACPX_SESSION_NAME from the last accepted gate pass>'

# No CODEX_HOME here (relay 5.1.0): in acpx 0.19.3 `sessions close` signals the queue
# owner, which keeps its own environment, and edits the record under ~/.acpx. It never
# starts the adapter.

LOG_DIR="${HOME}/.acpx/sessions"
LOG_FILE="${LOG_DIR}/${ACPX_SESSION_NAME}.driver.log"

# PARKED=0 closes the session. Write PARKED=1 here instead for an interactive
# needs-decision, to prevent the trap from closing a deliberately parked session
# (S1 spike outcome: close + re-ensure silently forks a blank session under the same
# name, losing all accumulated context).
PARKED=0

# Close trap: close the session when this call exits (normal, error, signal),
# UNLESS the session was intentionally parked for a needs-decision gate.
# The trap fires in the watcher only — thin session drivers are single-turn and
# do NOT register this trap.
trap 'if [[ "$PARKED" != "1" ]]; then
  acpx --cwd "$ACPX_CWD" "$ACPX_ENGINE" sessions close "$ACPX_SESSION_NAME" >>"$LOG_FILE" 2>&1 || true
fi' EXIT SIGTERM SIGINT
```

The sidecar write must append `RELAY_MAX_TURNS=${RELAY_MAX_TURNS:-10}` so the
sidecar carries the turn cap for the watcher. No session driver reads it.

## Two-log contract

The watcher reads from and writes to two log files:

- `~/.acpx/sessions/${session}.driver.log` — forensic turn log: one entry per worker turn
  with timestamp, turn number, rc, and reply byte count. Written by the watcher after each
  turn boundary.
- `~/.acpx/sessions/${session}.turn.log` — turn-content channel: the thinned driver runs
  exactly one turn and captures the full turn stdout into this dedicated file. The watcher
  reads the tail of this file at each turn boundary (one bounded `Read` per turn).

The `${session}.turn.log` file is the documented turn-content channel (Phase D2 gate
criterion). The watcher samples it once per turn boundary. Rotation deferred (spec §7
open issue 3).

## Env sidecar contract

`acpx-dispatch.sh` writes `~/.acpx/sessions/${session}.env` before spawning the watcher.
The sidecar carries the fully-resolved per-mechanism driver vars plus the sidecar-only vars.
The canonical table is in `docs/dispatch-contract.md` (Driver env-var table). The watcher
sources the sidecar at entry (`source "${session}.env"`) so it never re-derives
`ACPX_ENGINE`, `ACPX_SESSION_NAME`, `ACPX_CWD`, the model, or the effort from the binding.

Watcher-relevant notes:

- `ACPX_EFFORT` carries the effort on every engine: the codex driver applies it with
  `set reasoning_effort`, the claude and opencode drivers with `set effort`. claude/opencode
  also carry `ACPX_PERMISSIONS`. The session record re-applies model and effort per turn,
  so the watcher passes neither on the turn command. `CODEX_CONFIG` is gone (4.53.0).
- `RELAY_MAX_TURNS` — turn cap for this loop (default 10); the sidecar appends
  `RELAY_MAX_TURNS=${RELAY_MAX_TURNS:-10}` so the watcher receives it. It is a
  sidecar value read here, not a driver env var — no driver reads it.
- `ACPX_WATCH_CURSOR_FILE` — `~/.acpx/sessions/${session}.cursor`, the cursor file
  `scripts/acpx-wait.sh` reads and writes. It lives for the life of the session. No
  driver reads it.
- `ACPX_LAUNCHED_AT` — epoch seconds at the sidecar write, before `sessions ensure`
  runs. The `RELAY_WATCH_GRACE_SECONDS` window for `watch_no_session` subtracts from
  this value. No driver reads it.

## The bg-sessions leg

When `$RELAY_ENGINE` is `bg-sessions`, the watcher runs the same five-bucket router
loop above with two substitutions and one new first step. See
`docs/bg-dispatch-contract.md` for the shared mechanism this leg defers to, and
`skills/dispatching-bg-agents/SKILL.md` for the sidecar and handoff file this leg
reads.

- **Step 1 substitution.** Source `~/.claude/relay/bg/${runid}/${role_slug}.env`
  instead of the acpx `~/.acpx/sessions/${session}.env`. Branch the poll target on
  which sidecar was found — the acpx sidecar carries `ACPX_SESSION_NAME`; the bg
  sidecar carries `RELAY_BG_HANDOFF`.
- **Poll target substitution.** Search `$RELAY_BG_HANDOFF` with `grep` instead of the acpx turn
  log.
- **Liveness escape substitution.** The escape is `bg-liveness.sh --short-id
  "$RELAY_BG_SHORT_ID"` reporting `stopped` (exit `1`), instead of polling a process
  list. The bg leg has no acpx session to watch, so it keeps a poll, bounded by the
  shell's own `SECONDS` counter:

  ```bash
  bash -c 'SECONDS=0
    until grep -qE "^(ROLE_RESULT=|ROLE_DONE$)" "'"$RELAY_BG_HANDOFF"'" 2>/dev/null \
       || { bash "'"$CLAUDE_PLUGIN_ROOT"'/scripts/bg-liveness.sh" --short-id "'"$RELAY_BG_SHORT_ID"'" >/dev/null 2>&1; [ $? -eq 1 ]; } \
       || [ "$SECONDS" -ge "'"${WATCH_BUDGET:-540}"'" ]; do
      sleep 10
    done'
  ```

  The escape fires on rc `1` only. rc `3` (`stale` or `unknown`, per
  `docs/bg-dispatch-contract.md` §Liveness and truth) does not fire the escape, because
  `unknown` does not prove that the child stopped.
- **TURN discipline.** The watcher discards an envelope whose `TURN=` does not match
  the turn it just sent, and keeps polling — the same rule
  `skills/dispatching-bg-agents/SKILL.md` states for the handoff file's writer side.
- **Stop on a terminal bucket.** `done` and `errored` end with the stop instruction
  and a `stopped` confirmation, via `bg-liveness.sh` (§Spawn authority,
  `docs/bg-dispatch-contract.md`). `needs-decision` leaves the child alive and
  records its name. Under `RELAY_NON_INTERACTIVE=1`, `needs-decision` also ends with the stop
  instruction and a `stopped` confirmation: no person will answer, so no child stays alive.

## Vocabulary

```relay-vocab
l1-shape: multi-turn-dispatch
l0-deps: delegate, session-grounding, loop-until, marker, branch, classify, typed-output
acpx-leg-required: true
```
