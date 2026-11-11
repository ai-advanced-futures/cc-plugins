# ADR-006 — The judge writes its own report; a coach copy cannot end the loop

**Status:** Accepted · **Date:** 2026-10-27 · **Amended:** 2026-11-11 (v0.11.2, the plan pre-check of the analyst write allow); 2026-11-03 (v0.5.0, the analyst write allow)

Operator decision, 2026-10-27 (plan 1, resolution 6). Amended the same day by
the operator's decision that no file tool writes anywhere in a case folder
(plan 1, Task 7c).

## Context

In plan revision 2 the judge returned JSON, and the coach session wrote it to
a file for `bc.py save-report`. So the coaching side held the verdict text.
In a long transcription it could drop a finding or flip a status by a slip,
or on purpose. `validate_reply` checks shape and consistency, not authorship
(plan review finding M9). The wall guarded the judge's input. It did not
guard the judge's output.

Two limits of Claude Code shape the fix:

- A sub-agent's `tools:` list cannot limit its Write to one folder.
- Claude Code ignores `hooks:` in a plugin sub-agent's frontmatter.

So a guard on the judge's Write has to be a plugin hook, and a plugin hook
fires for every session with the plugin enabled.

## Decision

### The judge writes its reply once

The judge has `tools: Read, Write`. It writes its reply once, to the
`reply_path` its brief names, `business-cases/{slug}/judge/reply-NNN.json`.
When the Write succeeds, its final message is the reply path and nothing else.
When the Write is refused, its final message is the whole JSON and nothing else.

### Three hooks, one handler

`hooks/hooks.json` declares three guard hooks of the judge. All run
`hooks-handlers/judge_guard.py`, in a different mode each. It also declares the
5 hooks of the runner guard (`runner_guard.py`, ADR-016) and the brain hook of
the case graph (ADR-015): they are not part of the judge guard.

**The write guard** (`PreToolUse`, matcher `Write|Edit|MultiEdit|NotebookEdit`,
mode `pre-write`). Code writes every file in a case folder: `business-case.md`
through `bc.py change`, every other file through its own `bc.py` subcommand,
and the receipt through the hook below. So the guard refuses `Write`, `Edit`,
`MultiEdit` and `NotebookEdit` anywhere in a case folder, for every caller.
It allows two writes: the judge's own reply, here, and an analyst's reply
(below). The guard returns `permissionDecision: "allow"` for the judge's call
only when all of these hold:

- the call comes from `agent_type` `business-case:judge`;
- the tool is `Write`, not an edit;
- the path is exactly `judge/reply-NNN.json`, directly in a case's `judge/`
  folder;
- `judge/brief-NNN.txt` exists beside it;
- neither the reply nor its receipt exists yet.

That `allow` covers this one call, to this one path. The guard refuses the
judge every other write, inside a case or outside one. A write by any other
caller outside every case folder passes, and the guard says nothing. A call
with no readable path is refused when it comes from the judge or its input
mentions `judge` or `business-cases`.

A case folder is known by its names only: a folder whose name is a case slug
and whose parent is named `business-cases`. The names are also compared in
lower case, because macOS opens `Business-Cases/ACME/` as the same folder. For
any caller but the judge, the guard reads each path two ways: resolved, and
as plain text. The text reading is needed because resolving a symlinked
`business-cases` or slug folder loses those names. A path that is `~` or
starts with `~/` is also checked with the home folder put in. Only `~` and
`~/` are expanded; `~user` is not. The judge's allowed path is read only as
written and resolved.

`bc.py` refuses a case whose resolved path is not
`<anything>/business-cases/<slug>`. The guard decides by folder names, so a
case reached through a renamed symlink would be invisible to it.

This closes a forged decision line, and any other forged case file, written
with a file tool.

**The dispatch guard** (`PreToolUse`, matcher `Agent|Task`, mode
`pre-dispatch`). When `subagent_type` is `business-case:judge`, or the bare
`judge`, it refuses the dispatch unless the prompt is, byte for byte, the text
of the `judge/brief-NNN.txt` that the prompt's own `reply_path:` line points
at, and that brief has no reply or receipt yet. Any other dispatch passes.
`Agent` is the current tool name; `Task` is matched in case an older client
sends it.

**The receipt** (`PostToolUse`, matcher `Write`, mode `post-write`). Claude
Code runs it only after a Write succeeded. When the Write came from
`business-case:judge`, wrote a `judge/reply-NNN.json` beside its brief, and
the bytes on disk equal the Write's content, it hashes those bytes. It then
creates `judge/reply-NNN.receipt.json` with `O_CREAT | O_EXCL`, so a receipt
is never overwritten. The receipt holds the brief, the reply, the sha256, the
byte count, the agent ID, the agent type, the session ID and the tool name.

### The analyst write allow (v0.5.0)

The evidence team (ADR-013) adds one more exception to the write guard: the
analyst write allow. An analyst type is `business-case:<name>`, where the name
is the frontmatter `name:` of an `agents/case-*-analyst.md` file. The guard
returns `allow` for one call only when all of these hold:

- the call comes from an analyst type, or its bare name when no other agent
  the guard can see has that name;
- the tool is `Write`, and the path is exactly `team/reply-NNN.json` in a
  case's `team/` folder;
- `team/brief-NNN.txt` exists beside it, names that analyst type, and is not
  cancelled or expired, and no other brief of that type is open;
- neither the reply nor its receipt exists yet;
- the reply's `brief_sha256` equals the `sha256:` line of that brief, the
  digest of the brief's other lines, not of the file;
- for a plan brief, the reply's own text passes the plan rules of
  `team-reply --check`: the schema and the rules on the cards, the card ids,
  `follow_up` and `runs`. An error in that check allows the Write, and
  `team-reply --check` then decides (STORY-387).

The guard refuses an analyst every other write, anywhere. The dispatch guard
refuses an analyst dispatch whose prompt is not, byte for byte, the text of
an open brief, or whose `subagent_type` is not the type that brief names. The
receipt hook writes `team/reply-NNN.receipt.json` for a completed analyst
reply, as it does for the judge, and `bc.py team-reply --check` refuses a
reply with no receipt.

### Saving the report

`bc.py save-report --brief PATH` reads only the reply path the brief names. It
checks the receipt: its `agent_type` is `business-case:judge`, its session is
the case's current session, and its sha256 and byte count equal the reply
file's. It then validates the reply as ADR-002 describes, and saves the
report marked `"written_by": "judge"`.

When it refuses, the message tells the coach which branch it is on:

- No reply file and no receipt: the message starts `no judge reply` and names
  `--coach-copy`. The coach goes to the fallback.
- A receipt from a session that is not the case's current one: the message
  starts `the judge's reply is from another session` and tells the coach to
  make its own session current with `bc.py session`, then save again. It
  does not ask for a new judge run (ADR-002).
- A strategy file that cannot be read: the message starts `a strategy file
  cannot be read`, names the problem, and ends `repair the file,
  then write a new brief`. It does not ask for a new judge run until the file
  is repaired, since no run can pass before then.
- Any other refusal: the message names each problem and ends with "run the
  judge again with a new brief". It does not name `--coach-copy`.

### The fallback: a coach copy

If the judge's write is refused, the coach copies the JSON the judge returned
to a file outside the case and runs `bc.py save-report --brief PATH
--coach-copy FILE`. Code refuses a copy anywhere in a case folder, and refuses
any copy while a judge reply or receipt exists for that brief. The saved report
is always `"written_by": "coach-copy"`. No CLI flag sets `written_by`.

A coach copy can be read, but it cannot end the loop. Loop-end code never
counts a report that the judge did not write. A funding decision waits for
the loop to end, so it stays refused until a judge-written report is current.

### Loop end re-checks the saved report

A saved report is not a judge input, so an edit to it does not make it stale.
So loop end does not trust its `written_by` field (rulings FR-I2, FR-I2b).
Loop end reads every saved report once, through one check. A report counts
as the judge's only when:

- it is marked `"written_by": "judge"`;
- its receipt verifies, with a session the case recorded, since a report may
  be saved in an earlier session than the one that reads it; and
- it equals the report that the judge's reply yields now, by `save-report`'s
  own checks (`judge_report.rederive`). Every field but `saved_at` is
  compared. The one check left out is that the brief's inputs are
  unchanged, so a stale report is re-derived too. The re-derived `brief`
  and `manifest` come from the code-written brief, so a report whose
  manifest is not its brief's never counts (ruling S-11). No separate brief
  check is needed.

Loop end uses findings only from a report that counts: to close an item, to
list undecided findings and to bind a decision to its finding's item. The
checks read the case's files as they are now. When an edit moves a
paragraph that a claim finding points at, a stale report no longer equals
what its reply yields. Its findings then count as empty, and it closes
nothing. A latest report that fails is named in `bc.py status` with the
field or the receipt problem.

## Alternatives considered

- **The coach saves the judge's JSON** (plan revision 2). Rejected for the
  reason in Context: the coaching side would hold the verdict text.
- **An HMAC-signed receipt**, with its key under `${CLAUDE_PLUGIN_DATA}`.
  Rejected. The unguarded shell route that could forge a receipt can read the
  key too. It adds machinery and closes no route.
- **A `PreToolUse` guard on `Bash`.** Rejected. No decidable rule tells a shell
  command that writes into `judge/` apart from `bc.py save-report --brief
  judge/brief-001.txt`.

## Consequences

- On the normal path the coaching side never handles the report text.
- A refused judge write costs one more judge run from the session budget. It
  leaves no reply and no receipt, so the judge may retry.
- Both `PreToolUse` hooks carry `"onFailure": "block"`, so the plugin needs
  Claude Code 2.1.295 or later. The Claude Code docs do not say how an older
  client treats that key, so below 2.1.295 the guard makes no promise to fail
  closed.
- With `"onFailure": "block"`, a missing `python3`, a timeout or a crash blocks
  the call. In a session with the plugin enabled and no working `python3`,
  every file-tool write and every sub-agent dispatch is blocked. Inside the
  handler, an error, an import error included, refuses any call of a tool the
  guard covers. The `PostToolUse` hook has no `onFailure`: if it fails, no
  receipt exists, and `save-report` refuses the reply.
- The hooks run under the `python3` on `PATH`, which may be macOS's 3.9. The
  handler and every `lib` module it imports keep to 3.9 syntax, and a test
  enforces this.
- The case-folder rule has a false positive. A working tree under a
  `business-cases/<slug>/` path cannot be written with file tools while the
  plugin is enabled. The rule is by name only, by the operator's choice.
- Claude Code's sensitive-path rule overrides a hook's `allow`. The judge
  cannot write its reply for a case under `~/.claude/`: in the live check,
  Claude Code 2.1.312 denied it as "a sensitive file". Whether a case under
  `.claude/worktrees/` meets the same denial is not tested.
- A judge reply written into another case's `judge/` folder is refused by
  that case's `save-report`. The reply's manifest digest does not equal that
  case's brief. The session ID does not help here: one coach session working
  two cases has one session ID.

### What the live check recorded

Task 12 Step 5, 2026-10-27, `claude -p` runs only; the interactive run was not
done.

| Value | Seen |
|---|---|
| Claude Code version | `2.1.312` |
| `python3` the hooks ran | `/opt/homebrew/bin/python3`, 3.14.7 |
| the judge's `agent_type` in the hook input | `business-case:judge` |
| the `Agent` tool's input keys | `subagent_type`, `description`, `prompt`, `run_in_background` |
| `subagent_type` for the judge | `business-case:judge` |
| receipt `session_id` | equal to the session ID the run was given, and to the case's session |
| the judge's Write after the hook's `allow` | accepted, decision source `hook`, no prompt |
| dispatch with one extra line | refused, exit 2 |
| main-session Write into `judge/` | refused, exit 2 |
| `python3` that exits 127 | Write blocked, because `onFailure` is `block` |

## Residual risk

The receipt proves two things. The reply bytes are the bytes on disk after a
completed Write that Claude Code labelled as coming from `business-case:judge`
in this case's session. And each `Agent` dispatch of the judge carried
exactly a brief's text.

It does not prove that no model in the coach session forged the reply and a
matching receipt by a route the hooks do not see. A receipt is not
authenticated. A shell write, or an MCP file tool, that creates both a reply
and a receipt with a correct sha256 passes `save-report`. The operator
accepted this (resolution 6(a)). The command body forbids it. No hook sees it.

A shell edit of a saved report alone does not count: loop end re-derives the
report from the receipted reply and refuses a report that differs. A shell
append of a well-formed line to `decisions.jsonl` forges a decision, not a
report. It is the same shell-write residual (ruling S-9).

These routes are unguarded:

- **Shell writes** through `Bash`, `PowerShell` or `Monitor`: `cat >`,
  `python3 -c`, `cp`. No decidable rule tells such a command apart from `bc.py
  save-report --brief judge/...`. The shell can also make links the guard does
  not see:
  - a hard link to a case file, made from outside the case. A file-tool write
    to the link's outside path changes the case file.
  - a file inside a real case replaced by a symlink to an outside file. A
    file-tool write to that outside target is not seen by the guard.
- **A file-writing MCP tool.** No matcher here names one.
- **A judge started outside `Agent`:** a `Workflow` script's sub-agents, or
  `SendMessage` that resumes an earlier judge with new text. Such a judge's
  Write still passes the write guard, because the guard checks who writes,
  not how the judge was started.

The cheapest route the review found, extra text in the judge's dispatch
prompt, is closed by the dispatch guard.

The command body's own shell commands are pinned.
`test_coach_bash_writes_only_to_tmp_or_dev_null` in
`tests/unit/test_doc_contracts.py` checks that no bash fence in
`commands/build.md` writes anywhere but the temporary directory `temp-dir`
prints, `/dev/null`, `/dev/stdout` or `/dev/stderr`.

Every route above needs a deliberate act: a shell write of two files with a
correct sha256, or a second way to reach the judge. A transcription slip,
the risk M9 named, cannot produce one.

The guard also does not prove that the judge's verdicts are right.

### The analysts (v0.5.0)

The routes above reach an analyst's reply too. Three more are the analysts'
own.

Each round is a fresh analyst, and the coach sends no resume. A `SendMessage`
call that resumes an analyst is not seen by the dispatch guard. So neither
the brief check nor the budget holds for it. The resumed analyst's Write
still meets the write guard.

The reply's `brief_sha256` binds a reply to its brief. A run that reads
another open brief and copies its digest into `brief_sha256` can still write
that brief's reply file. It takes a deliberate act: a run whose brief expired, was cancelled or
was answered cannot do it by accident. The read-scope rule in each analyst
file narrows this: an analyst reads only the brief files its brief names in
`team/`. Nothing enforces that rule.

The guard accepts an analyst's bare name only when no other agent has it.
The bare-name scan reads project agents, user agents, `CLAUDE_CONFIG_DIR`
agents and `CLAUDE_PROJECT_DIR` agents. For the project, it reads the
`.claude/agents` folder of `CLAUDE_PROJECT_DIR` and of the working folder,
and of each parent up to the git root or the home folder. Agents from
`--agents`, settings and managed sources stay out of reach. The guard treats
such an agent with an analyst's bare name as the analyst.

A person's own `python3` rule can let a plugin route run any `python3`
command, `-c` included (the plugin-result standard in `schemas/`,
Decision 8). The analysts have no shell. So the rule widens only the routes
and the coach's own steps. The coach's warning before its first dispatch
names that choice.

The `build` command holds two grant lines in its `allowed-tools`:
`Bash(uv run "${CLAUDE_PLUGIN_ROOT}/lib/bc.py*)` and `Bash(uv run
${CLAUDE_PLUGIN_ROOT}/lib/bc.py*)`. The probe measured that the grant covered
every `bc.py` call shape on the CLI. The grant lasts only the command's turn:
a background agent loses it. A reply the person types in the chat ends the
grant too, and a later card answer does not bring it back: in the 2026-11-04
live run, every `bc.py` call after the first typed reply asked. It allows any
`bc.py` subcommand while the command runs, not only the ones the command's
steps name. The probe also measured that a call with a shell default value in
it asks every time, grant or no grant. ADR-016 (2026-11-09) adds a hook that
approves the exact `bc.py` and runner script calls in a session that runs a
build: that approval does not end with the turn.

The same line holds a second group of grants for the runners the command
starts (STORY-168, 2026-11-06; changed by STORY-188 and STORY-190, 2026-11-09).
The verifier measured in a live run (2026-11-06) that a `Write` rule with a path
does not match a write, because Claude Code checks a file write against the
`Edit` rules. So the folder grant of each of the five plugins whose runners the
coach starts is `Edit(/.<plugin>/**)`: it covers the result files, the run
folder and the session folder of the runner. The answers file of the case has
the grant `Read(**/team/answers-*.json)`.

The first version of this group also held a `Bash` grant for each script of
each plugin. A `*` in a `Bash` pattern matches any text, with spaces, so a
`uv run` command with other words in front and a plugin script path at the end
could match such a grant. The grant also ends with the turn. The `Bash` grants
are therefore removed. The hook `hooks-handlers/runner_guard.py` approves the
exact script calls of the runners instead, in a session that runs a build,
and it does not end with the turn. ADR-016 records that decision, its limits
and its checks.
