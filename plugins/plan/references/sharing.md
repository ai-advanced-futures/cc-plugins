# Shared Plan workspaces

A local workspace coordinates callers on one machine. A shared workspace coordinates compatible Plan callers on multiple machines. Each machine has its own profile, Beads directory, and source checkout. They share one workspace identity and one Git remote.

## Activate sharing

Installation does not publish work or start a factory. Before conversion, stop every existing writer and upgrade every Plan client. Review, apply, and verify one fixed roadmap migration in local mode before `share`. Migration apply refuses a shared target. Keep the source roadmap unchanged.

On the first machine, `share --remote origin --writers-paused --clients-upgraded` converts the selected workspace. These flags confirm actual operator checks; they are not a way to skip those checks. The remote must already hold a source branch. Sharing publishes Plan data and creates the coordination branch, so it needs explicit approval.

On each other machine, use Beads `bootstrap` to obtain the published data before Plan setup. Then use `setup --shared --remote origin --beads-dir DIR --source-root ROOT`. Do not initialize independent Plan controls and try to merge them. Verify the same workspace identity on every machine, then run `sync`, `list`, and `check`.

The profile stays machine-local. A worktree uses the main checkout's profile, not another store made inside the worktree. The read-only PRD and merged specification paths resolve against that machine's configured source root.

## Shared writes and claims

The Git branch `plan-coordination` grants one Plan operation access at a time. Acquisition and release use normal fast-forward pushes. A competing operation does not merge or rebase a rejected acquisition.

The holder verifies the shared baseline, reads the work, performs the checked operation, and publishes the complete result. Only then can the operation return shared success. A locally saved claim is not permission to start work. A failed or uncertain command gives no assumed owner, state, ID, or publication result.

The claim lease and the coordination gate are different. A claim lease limits how long a worker holds an item. The gate protects one shared store operation. No elapsed time transfers a retained gate to another caller.

An interrupted write, uncertain push, or unexpected local change stops shared operations. Keep its error and operation identity. A normal validation refusal releases the gate only when unchanged local and remote state is proved.

After the operator confirms that the prior writer stopped, use `recover --previous-writer-stopped --actor ACTOR` on the same machine. Recovery checks the saved attempt, gate identity, owned local checkpoint, and remote data before publication or release. It also covers a first share that stopped before the local profile changed to shared mode; only that machine's saved share attempt permits this conversion. It refuses missing journals, unknown local changes, remote divergence, and incomplete imports. It cannot take over another machine's gate. An uncertain unlock is cleared only after its exact published result is confirmed. Git history can prove that release after another machine has advanced the gate. This clears only the saved local attempt; it does not change the later gate or data. Read the current Plan record before resuming work, because an earlier completed operation does not prove current ownership.

An acquisition that never reached the remote can return `not_acquired: true` and `saved: unchanged`. Git history must include the proposal's original parent and exclude the proposal itself. Recovery also needs an unchanged local checkpoint and data that matches the current remote gate. Thus another machine can read or publish before recovery without losing its gate or data. An unknown history or unverified data retains the local attempt. For a first share, the coordination branch must still be absent. Recovery clears only the local attempt. It does not publish work, grant a claim, or complete the original command. Retry that command after recovery.

The confirmation flag is an operator statement, not a process-stop command. Do not clear a gate, overwrite local data, or force a ref to make a retry pass. Keep a refusal blocked and report its cause.

All writers use Plan. Raw `bd` mutations, synchronization, and independent database edits bypass the protocol. The gate coordinates cooperative clients; it is not an access-control boundary.

## Git transport

Beads 1.3.4 stores Dolt data under `refs/dolt/data`, separate from source branches. Its supported transport uses guarded data-ref replacement and can replace `refs/heads/__dolt_remote_info__`. The repository must explicitly permit those transport operations. This grants no permission to force a source branch or delete a ref.

## GitHub Projects

The board is a published view of Plan. One configured GitHub account publishes it through `gh`, including the factory's existing authentication wrapper. Another station can inspect a preview but cannot apply it as that writer.

Preview binds the source and intended changes to a fingerprint. Apply preserves existing bindings and records publication progress. GitHub and Beads do not share a transaction: a partial publication remains partial until a checked retry completes it. After an ordinary Plan edit during partial publication, obtain and accept a fresh preview. Apply keeps prior bindings and uncertain creates while publishing the current source. A binding intent from an older client without history evidence still needs its exact before or after state; later edits to that older intent remain blocked for inspection. Never create a second issue merely because an earlier response was lost.

Board publication does not pull issue state, assignees, or claims back into Plan. The tracker uses Plan for scheduling and the board for presentation. Human text outside a managed issue section remains unchanged.
