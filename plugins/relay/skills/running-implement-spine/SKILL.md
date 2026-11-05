---
name: running-implement-spine
user-invocable: false
description: "Use to generate and run the one dynamic Workflow for a classified implement run — resolves the per-leaf tiers, builds the §4.2.1 spine, records the run intent, runs the completeness gate, and returns one JSON block. Backs the /relay:implement command."
---

# running-implement-spine

This skill holds the part of `/relay:implement` that generates and runs the one dynamic
Workflow. `/relay:implement` runs Steps 0 through 2 — flags, the engine question, the
worktree gate, the branch guard, task-kind classification, and the §4.2.1 branch table —
then calls this skill. `/relay:implement` is its only caller. The skill holds no spine of
its own; the §4.2.1 branch table in `commands/implement.md` stays the one written authority.

## Inputs

- `kind` — the classified task kind (`feature | script | config-artifact | bugfix | docs`).
- `task` — the task description text.
- `spec_path` (optional) — the spec file path, when the caller has one.
- `engine` — the resolved dispatch engine.
- `agent` — the resolved dispatch agent.
- `verify` (boolean) — whether to append the verify-until-clean tail.
- `rounds` — the round value for every loop of this run: the ask point of `refine-spec`, the ask point of `refine-plan`, and the hard cap of the verify tail.
- `axis_source` — provenance of this run's dispatch axis (`flags`, `relay.json`,
  `default`, `prompt`, or a `<a>+<b>` combination — the same vocabulary
  `scripts/parse-engine-agent.sh` exports as `RELAY_AXIS_SOURCE`). `/relay:implement`
  forwards the source printed on its own last axis line.
- `command` — the name of the caller, recorded as this run's command. `/relay:implement`
  passes `implement`, which is today the only value. Step 3.5 writes this value, and
  `scripts/retro-run.sh` prints it back as `RELAY_RETRO_COMMAND`.
- `closes_issue` (optional) — an issue number to close in the commit body.
- `keep_sessions` (boolean, optional, default `false`) — when true, Step 4.5 keeps this
  run's background sessions instead of deleting them. `/relay:implement` forwards its
  `--keep-sessions` flag here.
- `non_interactive` (boolean, optional, default `false`) — true when `/relay:implement` got
  `--non-interactive`: no person is present, and the run must never wait for an answer.
  When it is true:
  - Write the literal line `RELAY_NON_INTERACTIVE=1` into the prompt of every generated
    node that can reach a question: each `relay:delegate-and-watch` watcher node, the
    `refine-spec` and `refine-plan` nodes, and the verify loop nodes. Next to it, write:
    "No person is present. Never ask a question. Choose from the evidence and write the
    assumption in your result."
  - Put `RELAY_NON_INTERACTIVE=1 AUTONOMY=fire-and-forget` in front of each acpx and bg
    dispatch command, after the `WORKTREE=<literal>` prefix. No script reads these two
    values. They are for the record only; the watcher prompt is the real control.
  - Use the fixed answers in Step 3, in the verify tail and in Step 4 below. Never call
    `AskUserQuestion`.
- `worktree` (optional) — the literal absolute path to this run's active worktree, from
  `RELAY_WT_ACTIVE`. Absent means the caller printed no active-worktree line: generate
  dispatches exactly as today. When present, write the literal absolute path into each
  generated dispatch:
  - `acpx`: prefix the dispatch command with `WORKTREE=<literal>` —
    `WORKTREE=<literal> bash skills/dispatching-acpx-agents/acpx-dispatch.sh …`.
  - `bg-sessions`: prefix the dispatch command the same way —
    `WORKTREE=<literal> bash skills/dispatching-bg-agents/bg-dispatch.sh …`.
  - `in-session`, writer roles (`role-class: writer`): pre-fill `WORKTREE_PATH` with the
    literal and `EXPECTED_HEAD` (captured via `git -C <literal> rev-parse HEAD`) in the
    generated `agent()` prompt slots.
  - `in-session`, non-writer roles: nothing.
  - Never emit the literal string `${WORKTREE:-$REPO_ROOT}` when a literal path is
    available; that fallback expression stays in the dispatch scripts themselves as the
    safety net for a caller that supplies nothing.

## Step 3 — Generate one Workflow
A `session-tree` run skips this step, because `session-tree` is a branch of Step 1 in
`commands/implement.md`, decided before this skill is ever called — that command's own
Step 3, the call into this skill, is itself skipped whenever Step 1 took it, so this
skill is never invoked at all on that path, and Step 3.5 below records no run intent
for it.

Call the `Workflow` tool now. Generate exactly one dynamic Workflow that runs the entire process beginning to end — from the first work-node through the final verify — in a single run. The roles named in Step 2 are leaf bodies: place each as an `agent()` node inside the generated Workflow. The only work that runs in this thread is the Step 1 classification. Running the spine inline forfeits the isolated runtime, native resume, and deterministic phasing that the Workflow substrate provides.

**Hold the turn under `--non-interactive`.** The `Workflow` tool starts the run in the
background and returns at once. Under `claude -p`, a run that still runs about 600 seconds
after this turn ends is killed (`wf_c36ba268-29d` and `wf_65b4f5c0-3f5`, `status: killed`).
So when the `non_interactive` input is true, do not end the turn while the Workflow runs, and
do not call `ScheduleWakeup`. Read the `wf_…` run id from the tool result, then run this
command with a Bash timeout of `600000`:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/wait-for-workflow.sh" "<runId>"
```

- Exit `3`: the run still runs. Run the same command again.
- Exit `0` and `RELAY_WF_STATUS=completed`: read the Workflow result from the task
  notification, or, when none has arrived, from the `result` key of the file that
  `RELAY_WF_RUN_FILE` names. When its `status` is `needs-decision`, go to Step 3.2 (no person:
  `blocked`). Otherwise continue with Step 3.5.
- Exit `0` with any other status: the run did not finish. Stop, and print the block with status
  `error` and the reason `workflow: <status>`.

**Close the run's sessions under `--non-interactive`.** When the wait exits `0` (any status),
and before you print the block, run this once. Pass the `worktree` input when it is present;
with no argument the script uses the top folder of the current checkout:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/close-run-sessions.sh" "<worktree>"
```

It closes every acpx session that is still open in that folder. A watcher closes its own
session with a trap, but the watcher writes that trap from text, and in the 5.0.0 acpx proof
row 10 sessions stayed open. A failed close or list (exit `1`) does not change the status of
the run: name each `RELAY_SESSION_CLOSE_FAILED` and `RELAY_SESSION_LIST_FAILED` line in the
final message.

**Tier note.** Resolve the per-leaf tier ladder deterministically — never hand-derive it from `bindings/presets.yaml`:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/resolve-tier.sh" --all
```

For every `agent()` role node this Workflow dispatches **in-session**, set `opts.model` and `opts.effort` from that role's printed row. A `model=inherit` row means OMIT `opts.model` so the node inherits the session model — still set that row's `opts.effort`. When in-session tiers are off, every row prints as `inherit` and you set neither opt. Delegated (`delegate-and-watch`) nodes: pin the **outer watcher** `agent()` node from the resolver's `watcher` line — it is a role-independent node-kind constant (the watcher only launches, waits, buckets the exit, and routes; when tiers are off its line prints `inherit` and you set neither opt). The inner worker is unaffected — its model comes from `modalities.*` at acpx dispatch time. A delegated node reaches its worker through `bash "${CLAUDE_PLUGIN_ROOT}/skills/dispatching-acpx-agents/acpx-dispatch.sh"` (see `relay:dispatching-acpx-agents`); do not substitute a single-turn prompt helper for it.

**The worker's mechanism.** Every delegated node maps the run's `agent` input to a mechanism and passes it to its dispatch as `ACPX_MECHANISM_OVERRIDE`: `claude` → `acpx-claude`; `codex` → `codex-session`; `opencode` → `acpx-opencode`; `hybrid` → that role's `modalities.hybrid.engine`, normalized through the same mapping. With no override, `skills/dispatching-acpx-agents/acpx-dispatch.sh` uses the role's static `binding.mechanism`, which can be codex, so a `--agent claude` run would quietly run a codex worker.

The printed rows already carry the two model overrides. `--fixes-model` and `--verification-model` replace the model of every role that carries the matching `category:` in `bindings/presets.yaml`, and the resolver's header names both values and where each one came from. Copy the rows as printed. Do not apply an override again by hand, because the rows already carry it. An override changes the model column only — `opts.effort` always comes from the row. With in-session tiers off, the header says both overrides reached no row.

**The `refine-spec` and `refine-plan` loops.** Each of these two steps is a loop, not one node. The rule: a fix is never the last act. After every fix a fresh review runs. The step ends when a review finds no critical and no important finding, or when a person decides. A missing review verdict is never `clean`.

Write the loop as plain JavaScript in the generated script — a `for` loop that builds each label from a template string, with `return` on a terminal state. Do not unroll a fixed number of rounds, because the verdicts decide when the loop ends.

- Critic labels: `` `${step}-critic-r${n}` ``. A retried review adds `-retry`: `` `${step}-critic-r${n}-retry` ``. The fresh review that opens a new block adds the block number: `` `${step}-critic-r${n}-b${block}` ``. A `no-answer` from that block-opening critic runs once more the same way: `` `${step}-critic-r${n}-b${block}-retry` ``.
- Fixer labels: `` `${step}-fix-r${n}` ``, and the retry `` `${step}-fix-r${n}-retry` ``. A fix label never takes a block suffix.

`step` is `refine-spec` or `refine-plan`. Every node stays in the phase of its own step, `Spec` or `Plan`. Each round carries a different label and a different prompt, so a resumed run replays the same branches. A node that never starts is not a dead node. The branch table in `commands/implement.md` keeps the bare names `refine-spec` and `refine-plan`; the round numbers exist only in the generated script.

The critic body is `roles/spec-simulator.md` or `roles/plan-simulator.md`. The fixer body is `roles/spec-fixer.md` or `roles/plan-fixer.md`. Fill every slot from the role file and write no prompt of your own in place of one. `roles/spec-reviewer.md` is a diff reviewer for built code and takes no part in these loops.

**Where the findings and the snapshots live.** Resolve the directory once, at generation time:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/refine-paths.sh" "<worktree>"
```

When the `worktree` input is absent, pass `.` in its place — the script then resolves the git directory of the checkout this skill runs in. Never pass an empty argument: the script reads that as a usage error and exits `1`, which would stop a healthy run before any node dispatches.

The script prints one absolute path, `<GIT_DIR>`. A non-zero exit is a fatal setup error: stop the run and report it. Build every findings path from that absolute path. Straight after the script prints the path, and still at generation time, create the findings directory with `mkdir -p "<GIT_DIR>/relay-refine/<slug>"`. `scripts/refine-node.sh` also creates this directory, with its own `mkdir -p`, when the snapshot copy needs it. A non-zero exit from `mkdir` is a fatal setup error too: stop the run and report the directory in the message.

Each pass writes `<GIT_DIR>/relay-refine/<slug>/<step>-<tail>.findings.md`, where `<tail>` is that pass's own round part — `r1`, `r2-retry`, `r3-b1`, `r3-b1-retry`. A pass's subject snapshot takes that pass's own findings-file name with `.findings.md` replaced by `.subject.md`. These paths sit outside the working tree, so no commit picks them up.

**The critic node.** One critic pass is one node. In-session the node is the `relay:leaf-reader` leaf with the role body and the standard preamble. Under `acpx` the node is the `relay:delegate-and-watch` watcher that launches `acpx-dispatch.sh` with the role. Fill the slots the role frontmatter already declares and add none.

- `roles/spec-simulator.md`: `SPEC_FILE_PATH`, `SPEC_CONTENT`, `FINDINGS_OUTPUT_PATH`, `ROLE_PROFILE`, `ITERATION_CONTEXT`.
- `roles/plan-simulator.md`: `PLAN_PATH`, `PLAN_CONTENT`, `SPEC_FILE_PATH`, `SPEC_CONTENT`, `SLUG`, `FINDINGS_OUTPUT_PATH`, `ROLE_PROFILE`, `ITERATION_CONTEXT`.
- `SPEC_CONTENT` and `PLAN_CONTENT` are the sentence `Read the file at <path> first.` The subject changes between rounds and the script reads no file. Both roles declare `requires: [read_files, run_bash]`, so they read it themselves, and the acpx dispatch passes the sentence to an external worker unchanged.
- `FINDINGS_OUTPUT_PATH` is this pass's own literal path from the rule above.
- `ROLE_PROFILE` is unchanged from today's dispatch.

After the role body has written the findings file, the node runs one command. It is the
same command on both engines, so neither engine needs a written-file exception to the role
contract — the script writes the snapshot, the role never does:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/refine-node.sh" "<subject>" "<snapshot>" "<FINDINGS_OUTPUT_PATH>"
```

The script copies the subject to this pass's own snapshot path, then runs
`scripts/refine-verdict.sh` on the findings file and prints the one verdict line, unchanged,
on stdout and nothing else. A non-zero exit means the snapshot could not be written; the
reason is on stderr and the node reports `outcome: errored` — never a verdict it did not get.
Each engine runs this line where it already runs its own shell work. In-session, the fenced
line above is appended to the critic node prompt, below the role body. It is the one
allowed write for that node. The role text itself writes nothing but the findings file.
Under `acpx` the `relay:delegate-and-watch` watcher runs the same line after the role's
`ROLE_DONE` reaches the `done` bucket and before it surfaces the result envelope.

The node returns this typed result. All three fields are required:

```json
{ "outcome": "done | blocked | errored",
  "verdict_line": "<the one line the script printed, unchanged>",
  "findings_path": "<FINDINGS_OUTPUT_PATH>" }
```

Read the label from `verdict_line` only, with this expression — a literal copy of the master copy in `scripts/refine-verdict.sh`:

```
^REFINE_VERDICT=(clean|findings|stalled|no-answer) critical=([0-9]+) important=([0-9]+) minor=([0-9]+) reason=([^ ]+) fingerprints=(.*)$
```

Group 6, `fingerprints`, is a list of tokens joined with `;`, and `;` is the only separator. Split group 6 on `;` to get the list. Do not split on a comma or on a space: a token holds neither, but it does hold `-` and `:`. An empty group 6 is an empty list.

```js
const fingerprints = m[6] ? m[6].split(';') : []
```

Keep the three cases apart. A null result, a missing line, or a line that does not match is `no-answer`:

```js
if (!res || !parse(res.verdict_line)) label = 'no-answer'
else label = parse(res.verdict_line).verdict
```

**What a critic receives from round 2.** Round 1 scans the full subject and leaves `ITERATION_CONTEXT` empty. From round 2 `ITERATION_CONTEXT` holds:

```
Iteration <N>.
Earlier findings: <the findings_path of the last critic entry in history>.
Fixer result: ROUND_RESULT=<addressed=A skipped=S>.
Snapshot before the fix: <that same path with .findings.md replaced by .subject.md>.
Run: diff <snapshot> <subject>
Trend: bash <plugin root>/scripts/refine-trend.sh <the findings_path of the last critic entry in history> <subject>
```

`ITERATION_CONTEXT` carries these paths, this fixer line and this trend line, and nothing else. `<plugin root>` is the absolute path, written as a literal at generation time. The trend line reports the rounds up to and not including the current round, because the findings file of the current round does not exist yet. For a `-b<B>` pass the last critic entry is round `N`'s own critic, so the table ends at round `N` and the look-back gives `progress`. The three-round window of the look-back counts from the last row of that table. The two-part review rule and the look-back rule are in the role body already — `roles/spec-simulator.md` names a section, `roles/plan-simulator.md` names a task. Never restate those rules in the prompt: a restatement drifts from the role that the critic obeys.

Take both paths from the last `critic` entry in `history`. Skip an entry labeled `no-answer`; it never had a findings file. A `-b<B>` critic runs in round `N`, so the last critic entry before it is round `N`'s own critic — the one that fired the ask point — not round `N-1`'s. When no fixer ran since that critic entry, leave the `Fixer result:` line out and print `No fix since the last review.` in its place. A retry pass gets the same inputs the failed pass got.

Each critic pass is a fresh context. No critic sees another critic's reasoning, only the files.

**The fixer node.** One fix is one node. `spec-fixer` always runs in-session as the `relay:leaf-worker` leaf. `plan-fixer` follows the engine like every other writer role. Fill these slots. `SPEC_FILE_PATH` or `PLAN_PATH`. `FINDINGS_PATH` is the `findings_path` of the last `critic` entry in `history`. `FINDINGS` and `SPEC_TEXT` or `PLAN_TEXT` each use the sentence `Read the file at <path> first.` `ORIGINAL_SNAPSHOT` uses the same sentence, with the path `<GIT_DIR>/relay-refine/<slug>/<step>-r1.subject.md`. Also fill `EXPECTED_HEAD` and `WORKTREE_PATH`.

The node returns `{ "outcome", "round_result", "detail" }`, all three required. `round_result` is the role's `ROUND_RESULT=<addressed=N skipped=M>` line. A null result, a `BLOCKED:` line, or `errored` gets one retry with the `-retry` label. A second failure ends the step as `error` and stops the run. A fixer that fails is never a reason to skip the next review; it is a reason to stop.

**The end states of a step.** Map each label:

- `clean` — the step ends `clean` and the run continues.
- `findings` with rounds left — the fixer runs, then the next critic.
- `no-answer` — the same critic runs once more with the `-retry` label. This applies to a block-opening critic too: a `no-answer` from `<step>-critic-r<N>-b<B>` runs once more as `<step>-critic-r<N>-b<B>-retry`, which writes `<step>-r<N>-b<B>-retry.findings.md` and its matching `.subject.md`. A second `no-answer` ends the step `unverified` and stops the run with that reason. Run `wf_a7545ff4-1ee` continued on a null result; this guard exists to stop that silent pass.
- `findings` at the ask point — Step 3.2 below.
- `findings` with `reason=no-trend` — the trend script failed, so the stall floor did not run on this pass. The loop treats the pass as `findings`. The final report names each such pass with its `findings_path`, so a floor that is off is visible to the person.
- `stalled` — an ask point, now, in the block the loop is in. Step 3.2 runs with the cause `stalled`. A continue here raises `block`; Step 3.4 states what that does to the next scheduled ask point. When the same pass is also a scheduled ask point, the loop asks one time, with the cause `stalled`.
- any other label — the step ends `unverified` and the run stops with that reason. A generated script that carries the new expression and no `stalled` branch is safe because of this default.

A step's result object is `{ state, rounds, fix_rounds, history, findings_path }`. `state` is one of `clean`, `accepted`, `needs-decision`, `unverified`, `error`, `skipped`. `history` holds one entry per pass with the node kind (`critic` or `fixer`), the parsed counts, the fingerprints, the `round_result`, and, for a critic entry, its own `findings_path` and `verdict_line`. A step the run gates off never starts, and its result is `{ state: 'skipped', rounds: 0, fix_rounds: 0, history: [], findings_path: null }`. The step-level `findings_path` is the `findings_path` of the last `critic` entry in `history`. Return `refine: { spec: <result>, plan: <result> }` in the Workflow's final object.

**No node inside a refine loop runs `git commit`.** The fixer's `EXPECTED_HEAD` is a literal from generation time, so a commit inside the loop makes every later fixer report a base mismatch and stop. One coordinator node, label `commit:docs`, runs after `refine-plan` and records the spec and the plan together with the message `docs(<slug>): refine spec and plan`. When neither file changed, `commit:docs` makes no commit and says so. The existing `commit` node for the code stays as it is. The loops write no inline refinement marker into the subject: the findings files and the snapshots under `<GIT_DIR>/relay-refine/<slug>/` are the record.

**The `write-plan` node.** The node dispatches through `relay:delegate-leaf` using the node label `write-plan`, the same way the branch table resolves every other kind's role from a label. It runs after `refine-spec` and before `refine-plan`.

- Run the node only when no file under `docs/plans/` matches the spec slug. If a plan is present, skip the node.
- When the run has no spec file at all, skip `refine-spec`, `write-plan` **and** `refine-plan`, and go straight to `implement`.
- Fill all six role slots: `SPEC_FILE_PATH`, `SPEC_CONTENT`, `SLUG`, `PLAN_PATH`, `REPO_ROOT`, `TASK_DESCRIPTION`. `SLUG` is the spec filename stem. `PLAN_PATH` is `<REPO_ROOT>/docs/plans/<SLUG>.md`. `SPEC_CONTENT` is the full text of `SPEC_FILE_PATH`.
- The role prints `PLAN_PATH=<path>`. The plan adapter reads a lower-case `plan_path`. Bind them with the literal line `plan_path = PLAN_PATH` before `refine-plan` runs. The case is different, and nothing bound them before.
- If `refine-plan` finds no subject, the adapter returns `SUBJECT_MISSING` and the run stops. An empty plan is not an acceptable plan.

**The `commit` node.** The node runs in the coordinator, not in a leaf. The implementer leaf stays read-only on git: it never runs a git mutation, because recording commits is the parent coordinator's job.

- Message: `<type>(<scope>): <summary>`. The type comes from the kind: `feature` gives `feat`, `bugfix` gives `fix`, `docs` gives `docs`, `script` and `config-artifact` give `chore`.
- Scope: the spec slug. With no spec, use the top directory the diff touches.
- Body: add `Closes #<n>` when the caller supplied `closes_issue`.
- If `git status --short` prints nothing, the node fails and the run reports `error`. A run that changed no file is not a clean run.

**Under `--non-interactive`.** When the `non_interactive` input is true, no node waits for a
person:

- A watcher node that returns the `needs-decision` bucket (`ROLE_RESULT=NEEDS_DECISION` with
  `QUESTION_TEXT`) has already closed its worker session (`relay:delegate-and-watch`). Do not
  re-dispatch the node. Stop the spine and return `blocked` with the reason
  `needs-decision: <node>: <question>`: the node label, then the `QUESTION_TEXT`.
  This includes a delegated refine critic or fixer.
- A refine loop that reaches its ask point (Step 3.2) gets no answer. Never choose **accept**
  and never choose **continue**: return `blocked` with the reason
  `<step>: needs-decision after <N> fix rounds; findings at <path>`.

**Verify-node guard.** A verify node must separate three cases — no verdict, a verdict that is clean, and a verdict that carries findings. Write the guard so the absent case stays reachable:

> `if (!verdict) { /* unverified — retry or fail */ } else if (!verdict.blocking) { /* clean */ }`
>
> Collapsing them into `if (!verdict || !verdict.blocking) break` reports an unverified run as verified. Likewise, a `try/catch` around `agent()` that returns `null` on a schema miss converts a hard harness failure into a false success — if you catch, re-raise or record the miss as a failure in the returned result, never as an absent field.
>
> Both anti-patterns come from a real failing generated script. It carried a prose output contract *and* a `safeAgent` wrapper added to survive that contract's misses; the wrapper is what made the failure silent. The mitigation caused the silent failure it was added to survive.

### The verify-until-clean loop — only when `--verify` was passed

Generate this tail only when the `verify` input is true. (`/relay:implement` sets that input
from `--verify`. Gate on the `verify` input itself, never on Step 0 output read again here.)
Invoke `relay:verifying-until-clean` to
generate the round nodes and the terminal report node. The skill appends its nodes to this same
Workflow, right after the branch's `verify` node — this skill generates no second `Workflow`,
so exactly one Workflow still runs.

Declare no loop identity here. `relay:verifying-until-clean` takes the engine and nothing else,
and this skill must not rename a node, a session, or the state directory. `/relay:implement --verify` has to produce exactly
what `/relay:implement` followed by `/relay:verify` produces, down to the session names, and a
per-caller name would break that.

**Pass this run's engine to the loop.** `/relay:verify` resolves the same axis with the same
script, so the two paths stay equal only when this tail uses the engine this run resolved. Take
that engine from this skill's own `engine` input. Do not read `$RELAY_ENGINE`, because it is not
set here. `/relay:implement`'s own Step 0 exports it in a different Bash call.
Set it from the input before branching:

```bash
RELAY_ENGINE="<this run's engine input>"
case "$RELAY_ENGINE" in
  in-session|acpx) RELAY_VERIFY_ENGINE="$RELAY_ENGINE" ;;
  *)
    echo "[relay] verify: engine=$RELAY_ENGINE has no verify-loop substrate — the loop runs in-session"
    RELAY_VERIFY_ENGINE="in-session"
    ;;
esac
export RELAY_VERIFY_ENGINE
export RELAY_VERIFY_ROUNDS="<this run's rounds input>"
echo "[relay] verify: loop engine=$RELAY_VERIFY_ENGINE rounds=$RELAY_VERIFY_ROUNDS"
```

Set `RELAY_VERIFY_ROUNDS` from the `rounds` **input**, for the same reason the engine comes
from the `engine` input. `relay:verifying-until-clean` reads that variable and nothing else for
its round count, and Step 0 prints it empty on a run with no `--verify`. Writing it here is
what makes `rounds` one value for all three loops of the run.

The substitution is printed, never silent. A hard rejection here would throw away a finished
build over its last step, and the loop is a tail, not the work.

**When the loop engine is `acpx`,** the skill asks the user one question before it generates any
node, because the loop then runs headless child sessions with the approval gate off. Ask it
here too, for the same reason and with the same words: `/relay:verify` asks it under acpx, so a
`--verify` tail that did not ask would make the two paths differ. Without `--non-interactive`, do
not skip that question, and do not answer it for the user. When the user does not agree, generate
no loop node and report
the run as unverified. The spine keeps whatever result it already earned.

**Under `--non-interactive`,** the flag is the consent: the caller got the operator's consent
before it passed the flag. Pass `non_interactive` to `relay:verifying-until-clean`. That skill
then does not ask. It prints the three-point notice as text, then the line
`[relay] verify: consent given by --non-interactive`, then generates the nodes.

**When the loop engine is `in-session`,** ask nothing. No child process starts, so no approval
gate is turned off. `/relay:verify` asks nothing there either, so the two paths still match.

The report node ends in one of the three terminal states `relay:verifying-until-clean` defines
for `RELAY_VERIFY_RESULT`: `clean`, `findings`, or `unverified`. Before the command reports
completion, name the reason plainly:

- `unverified (acpx unavailable)` — the helper exited `69`. The acpx engine only.
- `unverified (no reply)` — a step recorded `failed:no-reply`, so it invoked nothing or
  answered with an empty file. The in-session engine only.
- `unverified (loop blocked)` — the loop ran and could not reach a verdict.
- `findings` — the loop ran and the branch still carries problems.

A run is reported clean only when the loop's own result reads `clean`.

A bare run produces no `RELAY_VERIFY_RESULT` at all, because no loop ran. Report that the loop
did not run. Never read the absence of the loop as a clean result.

Cite only `relay:delegate-leaf`, `relay:delegate-and-watch`, `relay:improve-loop`, `relay:panel`, `relay:parallel-gather`, `relay:verifying-until-clean`, and the language-reference doc.

## Step 3.2 — The ask point

Runs between `Workflow` returns: after a return whose `status` is `needs-decision`, and before Step 3.5. A `session-tree` run skips this step, for the same reason as Step 3 above.

`ROUNDS` is the `rounds` input. Each refine loop counts its own fix rounds. When the critic of a round reports `findings` and `fix_rounds` equals `ROUNDS × (block + 1)`, that loop is at an ask point. `block` starts at `0`. There is no ceiling on the number of rounds except the person's answers here, the Workflow's own agent backstop, and the token budget.

The generated script declares one literal near its top:

```js
const DECISIONS = { 'refine-spec': {}, 'refine-plan': {} }
```

The script reads `DECISIONS[<step>][ask]` only at the ask point. `ask` is the number of ask points that the step has reached before this one, from `0`. `block` stays for the `-b` label and the scheduled test.

- absent — the script returns at once:

```js
return { status: 'needs-decision', step, cause, ask, block, rounds, fix_rounds,
         summary, findings_path, subject_path, refine }
```

The object carries `cause`, with the value `rounds` or `stalled`. `cause` is `rounds` for a scheduled ask point and `stalled` for a `stalled` pass. On resume the script reads the answer stored for the same `ask`. `ask` becomes `ask + 1` when the loop goes on, at the same place where `block` changes.

- `{ action: 'continue' }` — `block` becomes `block + 1`. Let `N` be the round number of the critic pass that fired the ask point; a `-retry` pass and a `-b` pass never advance `n`. A fresh critic pass runs first, labeled `<step>-critic-r<N>-b<block>` — a new label the cache does not hold, so a hand edit made during the pause is reviewed before any fixer runs. If that pass is `clean`, the step ends `clean` with no fixer. Otherwise the fixer runs with the first unused fix label, `<step>-fix-r<N>`, and the loop goes on with the next unused critic label, `<step>-critic-r<N+1>`. The next ask point is `ROUNDS` fix rounds later.
- `{ action: 'accept' }` — the step ends `accepted` with its open findings in `history`, and the run continues to the next step.

`summary` is built by plain code from `history`. For each round it holds the counts, the fixer's `addressed` and `skipped`, and each critical and important fingerprint bucketed as one of three. Each round's fingerprints are group 6 of its `verdict_line` split on `;`, the one separator — a round with three findings gives three tokens, never one. Compare the rounds token by token:

- `fixed` — present in round N-1, absent in round N.
- `recurring` — present in both. The fixer said addressed; the critic still flags it.
- `new` — absent in round N-1, present in round N. A fix introduced it.

This is the answer to "why does it not converge". Three counts alone do not answer it.

**Ask the person.** MAIN runs `refine-trend.sh <findings_path> <subject_path>` and prints its output before the summary table. For the cause `stalled`, the question starts with one sentence: the count of critical and important findings set no new low in the last 5 reviews. The three answers do not change. Print the summary as a table. Read the findings file at `findings_path` and show the section and the concern of each open critical and important finding, at most ten. Then ask one question with three answers:

1. **Continue** — another `ROUNDS` fix rounds, opening with the fresh critic pass described above. That pass resets the count of the trend script, so the next `stalled` is 5 rounds later at the earliest.
2. **Accept the open findings and continue** — the run goes on to the next step with the findings listed in the report. This builds on a subject that a review still rejects. The person takes that decision, never the script.
3. **Stop** — print the output block with `status: blocked` and the reason `<step>: stopped after <N> rounds; findings at <path>`. For the cause `stalled` the reason is `<step>: stalled after <N> rounds; findings at <path>`. The spec and the plan edits stay on disk.

**Resume.** On a **continue** or an **accept** answer, first capture the head:

```bash
git -C "<worktree>" rev-parse HEAD
```

Then edit the saved script at the path the `Workflow` result gives, writing the answer into the `DECISIONS` literal under the `ask` value that the `needs-decision` object printed — for example `'refine-spec': { 0: { action: 'continue', expected_head: '<sha>' } }` — and call:

```js
Workflow({ scriptPath, resumeFromRunId })
```

Every completed `agent()` call whose prompt and opts are unchanged returns its cached result. So a **continue** resumes at the fresh critic pass of the new block and repeats no earlier round, and an **accept** goes straight to the next step with no new critic pass.

Two rules keep the cache intact:

- No prompt of a node that ran before the ask point may hold a value the decision changes. The `DECISIONS` literal is read only after the ask point.
- `expected_head` reaches only the fixers of blocks after the decision.

A person may commit during a pause, so the head captured at the most recent decision is the `EXPECTED_HEAD` of every writer node that runs after it — the later-block `refine-spec` fixers, `write-plan`, and every `refine-plan` fixer. The generation-time literal applies only to writer nodes that ran before the first decision, and those nodes are already cached.

Resume is same-session only. A run that reached an ask point in one session cannot be resumed from another; it is restarted, and the edits stay on disk.

**No person, no guess.** When the `non_interactive` input is true, no person can answer. Do not
ask, and do not guess: never choose **accept** or **continue**. Print the summary, then print
the output block with `scripts/result-block.sh`, status `blocked`, and the reason
`<step>: needs-decision after <N> fix rounds; findings at <path>`. For example:

```json
{"schema": "relay.implement-result/1", "status": "blocked", "run_id": "wf_…", "branch": "…", "commit": null, "reason": "refine-spec: needs-decision after 3 fix rounds; findings at <path>"}
```

The caller decides. A restart reviews from round 1.

Under `--non-interactive`, and in a headless session, a `stalled` pass gets no answer. The run returns `blocked` with the reason `<step>: stalled after <N> rounds; findings at <path>`.

**A person who tells the run not to ask.** The generated script declares one more literal near its top:

```js
const AUTO_CONTINUE = false
```

Set it to `true` only when the person told this run, in the command text, not to ask at the ask points. With `true`, a scheduled ask point (cause `rounds`) does not return: the loop goes on with the next fixer, and `block` does not change. `true` removes the scheduled ask point for the rest of the step, at every occurrence and not one time only. The one brake left in that mode is the `stalled` pass, with the agent backstop and the token budget. A `stalled` pass always returns `needs-decision`, with `true` and with `false`.

The skill states one rule in plain words: no instruction of the person and no stored note removes the ask-point branch or the `stalled` branch from the generated script. The literal is the one way to run without the scheduled question.

A continue at a `stalled` ask point raises `block`, as a continue at a scheduled ask point does, so the next scheduled ask point is the one at `fix_rounds` equal to `ROUNDS × (block + 1)` with the new `block`. The scheduled test does not change.

## Step 3.5 — Record run intent
This step never runs for a `session-tree` run, for the same reason as Step 3 above: that
branch is decided by `commands/implement.md`'s own Step 1, before this skill is ever
called. `session-tree` allocates its own runid through `scripts/bg-manifest.sh` instead,
and this bookkeeping step's script never runs for a session-tree run (spec §Deliverable 3,
Bookkeeping).

Runs **immediately after the `Workflow` tool returns** for the last time — a
`needs-decision` return is not the last one, see Step 3.2 — `run_id` exists only then, and
it is returned in the tool *result*, never echoed back from the input.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/record-run-intent.sh" \
  --run-id "<runId>" --command "<this run's command input>" --task-kind "<kind>" \
  --spine "<the Step 2 branch row for this kind, as the agent() node LABELS, comma-separated>" \
  --gates "<verify-loop=false unless the verify input is true; add write-plan=false when the write-plan node was skipped; add refine-spec=false and refine-plan=false when the run has no spec file>" \
  --axis-source "<this run's axis_source input>"
```

`--command` takes the `command` **input**, never a literal word. Today the input is always
`implement`, but the record must name the caller that ran, so a new caller gets a correct
record without an edit here.

`--gates` keys on **node labels** — the same strings recorded in `--spine`. The retro
suppresses a role by looking that role up in `gates`, so a key naming anything else
matches no role and suppresses nothing. Record a gate only for a spine role this run
deliberately did not dispatch. A setting that changes *how* a node runs rather than
*whether* it runs is not a gate: with delegation off every spine role still dispatches
(`relay:delegate-leaf` stands in for `relay:delegate-and-watch`), and C4 AXIS already
reports on delegation wiring from the script's own consts.

`verify-loop` is the one skippable role in this spine. Key the gate on the `verify` **input**
this skill received, never on a flag: `/relay:implement` sets that input from `--verify`. When
`verify` is true the loop dispatches, so the value is `""`. When `verify` is false it does not,
so the value is `verify-loop=false`.

Record that gate. It is not optional bookkeeping. `scripts/retro-run.sh` matches an intended role
against the joined node labels as a **substring**, and a bare run produces no label containing
`verify-loop`. Omit the gate and every bare run reports a `SPINE` deviation that describes a
healthy run. The gate makes the retro drop the role from its expected set instead.

`--spine` takes **node labels, not skill names.** The retro compares each recorded role
against the labels of the agent nodes that actually ran, so recording the branch row
verbatim — `relay:delegate-leaf(implement)` — matches nothing and makes a perfectly healthy
run report a SPINE deviation. For `feature` the correct value is
`refine-spec,write-plan,refine-plan,implement,commit,verify,verify-loop` for both a bare run and a `--verify`
run: the recorded spine is the same, and only the `--gates` value differs — a bare run gates
`verify-loop` off, a `--verify` run leaves it empty. Recording `verify-loop` here is what makes
the gate above load-bearing: `retro-run.sh` suppresses a role only when it is in the recorded
spine, so a bare run that dropped `verify-loop` from the spine would make `verify-loop=false`
suppress nothing. The other kinds drop the leading refine roles the same way. Whatever label you
gave the node is what goes in.

Record `write-plan` in `--spine` on every `feature` run, whether the node ran or not, because
`retro-run.sh` suppresses a role only when that role is in the recorded spine.

Record the bare step names `refine-spec` and `refine-plan` in `--spine`, never a round label.
The nodes themselves carry `-critic-r<N>` and `-fix-r<N>` labels, and `scripts/retro-run.sh`
matches a recorded role against the joined labels as a substring, so the bare name matches
every round of its own loop. Step 3.5 runs after the **final** `Workflow` return. A resume
keeps the same run id, so record that one id.

Record only what no artifact preserves. The runId is the join key; `kind` and the command
identity appear nowhere else (`workflowName` is free text); `intended_spine` snapshots the
§4.2.1 row **at run time**, so a later retro of this run does not diff it against a table
that has since changed. Do **not** add the axis values or the task text — both are already
persisted as `const ENGINE` / `const AGENT` / `const TASK` in the script, and a second copy
can disagree with the first.

This is advisory bookkeeping. If it fails, report the reason and continue — the run already
succeeded, and a later retro simply degrades its spine-coverage check to "unknown".

## Step 4 — Verify run completeness
This step never runs for a `session-tree` run, for the same reason as Step 3 above: that
branch is decided by `commands/implement.md`'s own Step 1, before this skill is ever
called, so this step's "exactly one `Workflow` run was launched" check does not run and
must not fire its "stop and re-issue the work as a single Workflow" branch against a run
that generated no Workflow by design.

Before reporting completion, confirm: exactly one `Workflow` run was launched, and no spine role (`relay:delegate-leaf`, `relay:improve-loop`, `relay:panel`) was invoked directly in this thread. Count runs by run id: exactly one `Workflow` run id was launched. A second `Workflow` call that carries `resumeFromRunId` for that same run id is a resume of the one run, not a second run, and does not fail this check. A `Workflow` call with no `resumeFromRunId`, or one that names a different run, still fails this check. If any spine role ran inline, stop and re-issue the work as a single Workflow.

**The refine verdict check.** For each of `refine-spec` and `refine-plan` in the returned
`refine` object, take that step result's own `findings_path` and the `verdict_line` of the
last `critic` entry in its `history`, then run:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/refine-verdict.sh" "<findings_path>"
```

Compare the label the script prints with the label in that `verdict_line`. A mismatch makes
the run `error` with the reason `refine verdict mismatch`: a node relayed a line its own
findings file does not support. A result whose `state` is `skipped` has an empty `history`
and is not checked. Never scan the findings directory for a last-written file; read the step
result's own field. The check keeps its rule: it runs `scripts/refine-verdict.sh` (not `--single`) on the `findings_path` of the step and compares the line with the `verdict_line` of the last critic entry.

**The refine report.** Next to the refine verdict check, MAIN runs `refine-trend.sh <findings_path> <subject_path>` for each of `refine-spec` and `refine-plan` that ran. The final report prints, for each step, the state, the rounds, the two word counts of the last trend line, the minor count of the last verdict line with the path of that findings file, and each section that the last look-back named as churn. It also names each critic pass whose `verdict_line` holds `reason=no-trend`, with its `findings_path`: the stall floor did not run on that pass. The minor count is there because the fixer skips minor findings, so they are open when the step ends. A step that ended `clean` after a look-back verdict of `churn` shows those sections, so the person can read what the loop made shorter or left to judgment.

That check proves shape only — one run, nothing inline. It never proves that every node produced output. Then run the completeness gate, passing the `runId` from the `Workflow` tool result:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/verify-run-completeness.sh" <runId>
```

Branch on the exit code:

- `0` COMPLETE — proceed.
- `1` INCOMPLETE — do not report success. Name each dead node and the phase output it was to produce, then re-run those nodes or escalate.
- `2` INDETERMINATE — report that completeness could not be verified. Never treat it as a pass.

**Fixed answers.** Under `--non-interactive`, exit `1` has one fixed answer: re-run the dead nodes
once. If a node is still dead, do not wait and do not escalate to a person, because no person answers
under `--non-interactive`. Return `error` with the
reason `completeness: incomplete: <dead node names, comma-separated>`. Exit `2` gives `error` with
the reason `completeness: indeterminate: <RELAY_COMPLETENESS_REASON>`, with or without the flag.
The gate prints that value on its `RELAY_COMPLETENESS_REASON=` line.

A `0` here proves shape only. It does not turn a non-clean `verify-loop` result into a success.
Report the loop's own result (`clean`, `findings`, or `unverified`) as the run's outcome. On a bare run there is no loop result to report, and a `0` here says
nothing about whether the branch verifies. Say that the loop did not run.


## Step 4.5 — Clean up the run's background sessions

Runs only when the `engine` input is `bg-sessions`. `session-tree` never reaches this
skill — that branch is terminal in `commands/implement.md` Step 1 — and every other
engine launched no background session, so there is nothing to clean up.

Resolve the run's status **before** running the cleanup, so a failed run keeps its
sessions readable for debugging: `--outcome clean` when the run is about to report
`status: ok`, `--outcome failed` otherwise. `--runid` is the Workflow `run_id`
(`wf_...`) from Step 3.5 — `scripts/bg-cleanup.sh` normalizes it itself. Pass `--keep`
when the `keep_sessions` input is true.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/bg-cleanup.sh" --runid "<run_id>" --outcome "<clean|failed>" [--keep]
```

The cleanup is advisory. It does not change the JSON `status` this skill prints in
`## Output`. Branch on the exit code and always print something from this table:

| Exit | Spine behavior |
|---|---|
| `0` | Report the final `RELAY_BG_CLEANUP=` line. Done. |
| `1` | At least one session did not stop. Send the pinned finish-and-stop message (`docs/bg-dispatch-contract.md` §Spawn authority) via `SendMessage` to each printed `RELAY_BG_STOP_REQUIRED=` name, then re-run the identical `scripts/bg-cleanup.sh` command. At most two re-runs. If a session still does not read `stopped`, name it in the run's report and continue. If `SendMessage` is unavailable in this session, say so in the report and name the sessions as not stopped. |
| `2` | A usage error here is a relay bug, not a run failure. Report the stderr line verbatim and continue. Do not retry, because the arguments do not change on a retry. |
| `3` | Zero sessions were recorded for this runid. Say so (`no background session was recorded for this run`) and continue. This is legal for a `bg-sessions` run whose leaves all fell through to in-session dispatch — it is not a failure and not a clean deletion. |

## Output

The last thing this skill prints is one `relay.implement-result/1` block, and nothing after it.
Never write the JSON by hand. Print the block with the script, and copy its output verbatim:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/result-block.sh" --status <ok|blocked|error> --run-id "<runId>" --commit "<sha>" [--reason "<reason>"]
```

The script prints one fenced JSON block, for example:

```json
{"schema": "relay.implement-result/1", "status": "ok", "run_id": "wf_...", "branch": "...", "commit": "abc1234"}
```

`status` is `ok`, `blocked`, or `error`. `--commit` takes the short hash of the commit that the
`commit` node made. Leave out `--commit` when that node made no commit, and leave out `--run-id`
when no Workflow run started. The script reads the branch itself.

Print `ok` only when the run finished, the `commit` node made a commit, the completeness gate
exited `0`, and — when the caller asked for `verify` — the loop reported `clean`. An `accepted`
step is not an error; the report lists its open findings. On any other outcome, pass
`--reason` with the cause in plain words:

- `findings` — status `error`: the loop ran and the branch still carries problems.
- `unverified (acpx unavailable)`, `unverified (no reply)`, `unverified (loop blocked)` — status
  `error`: the loop could not reach a verdict.
- `completeness: incomplete: <node names>` — status `error`: Step 4 exit `1`, still dead after
  the one re-run.
- `completeness: indeterminate: <RELAY_COMPLETENESS_REASON>` — status `error`: Step 4 exit `2`.
- `workflow: <status>` — status `error`: under the flag, `wait-for-workflow.sh` read a status
  other than `completed` (for example `killed`).
- `needs-decision: <node>: <question>` — status `blocked`: a worker asked a question under
  `--non-interactive`.
- `refine-spec: needs-decision after <N> fix rounds; findings at <path>` — status `blocked`: a
  refine loop reached its ask point (Step 3.2) and no person can answer.
- `refine-spec: stalled after <N> rounds; findings at <path>` — status `blocked`: the count of
  critical and important findings set no new low in 5 reviews and no person can answer.
- `refine-spec: stopped after <N> rounds; findings at <path>` — status `blocked`: a person
  answered **Stop** at the ask point.
- `refine-spec: unverified (no critic answer)`, `refine-spec: fixer failed`,
  `refine verdict mismatch` — status `error`.
- The same refine forms exist for `refine-plan`.
- the failing node's name — status `error`: any other node failure.

Never print `ok` for a run that made no commit. The script refuses `ok` without `--run-id` and
`--commit`, and it refuses `blocked` or `error` without `--reason`. When it exits `2`, correct
the call.

Return this block to `commands/implement.md` Step 3. That command runs its retro and its reason
report, then prints the same block again, unchanged, as the last text of the run (its Step 6).
