# Optional GitHub publication

Plan is the work store. GitHub Issues and an organization Project are a view of that store. This release supports GitHub only, with no incoming updates. A factory with no publication approval can work locally. Legacy Product factories keep their existing board rules.

## Setup

Use this prefix for each command below:

```text
<skill folder>/scripts/sofa-plan --repo <main folder>
```

1. Read `publication status`. Offer to keep the current setting, configure GitHub publication, or disable it. Do this even when readiness passes. An absent approval means disabled; installation and a template update grant no write permission.
2. For GitHub publication, ask for the issue repository, organization Project owner and number (or its URL), and type mode (`labels` or `issue_types`). Read existing values from the Plan Project first. Confirm them instead of asking the user to enter them again. Keep existing issue, Project, card, and field links. A target or writer change needs a separately agreed migration; this setup does not perform one. Do not create a new Project or duplicate issues to avoid a failed check.
3. Reuse the factory GitHub App, or complete setup step 5.5. The App needs Issues and Organization projects read and write permissions, and installation access to the issue repository. Repository projects permission is not a substitute for Organization projects. The writer must be the App bot. Never request a private key or token in chat. The user saves the key outside the repository, with mode 600, and enters its location locally. Do not print settings output, key locations, or tokens. If App setup changes, existing sessions need a fresh start as step 5.5 specifies.
4. Confirm that the former publisher will no longer write the target. A new Project containing the same issues does not isolate issue writes. The local publication lock cannot stop another program or machine. Resolve conflicting identities, unexplained board edits, or missing evidence from a prior publication before continuing. For a first publication, explicitly review the existing target and proposed adoption. Ask the user when the evidence is insufficient; do not infer approval from a matching title.
5. After agreement, use `github configure --repo OWNER/REPO --owner ORGANIZATION --number NUMBER --writer APP-BOT --type-mode MODE --actor ACTOR`. Use the actual setup actor and App login. This saves checked links in Plan and performs no GitHub write. It can trigger Plan's configured data backup. Do not alter the profile schema or write raw Beads data.
6. Run `publication preview`. Show its target, writer, proposed creates and updates, and `approval_fingerprint`. This checks App permissions and reads Plan's live preview. It changes no GitHub issue or Project item. Resolve refusals before asking for approval.
7. Ask whether to enable routine publication to that target. Explain that all supported Epic, Feature, Story, Task, and Milestone records are in scope, including work not ready for implementation. Routine writes include creating missing issues and milestones and updating the fields that Plan manages. Acceptance criteria appear in issue text. This approval does not authorize deletion, changing the target, importing GitHub edits, or replacing saved links.
8. On approval, run `publication enable --fingerprint HASH` with the `approval_fingerprint` from step 6. The command checks a fresh preview. If its fingerprint changed, show the new preview and ask again. Setup ends with publication ready, not verified. It does not run `github apply`; the first publication waits for an orchestrator `SYNC`.

For a disable request, run `publication disable`. It stops future publication through the wrapper, preserves Plan links and the last verified result, and deletes no remote work. It works with a missing Plan profile or unavailable App. If publication is busy, wait for that operation to finish and retry; do not remove its lock. Keep local Plan work running.

## Tracker operation

Read `publication status` through `sofa-plan` before a board round. When disabled, report that publication is off and do no board work. Assignment and claim coordination remain available. Inspect a blocked or failed result before retrying. A partial result does not advance verification, but a planned part limit permits the next step as the tracker table specifies. `ready` means configured but not yet verified. `verified` names the last successful attempt, not a claim that GitHub is still unchanged.

On an orchestrator `SYNC`, use `<skill folder>/scripts/sofa-publish --repo <main folder>` with the planning contract and the outcome table in `references/roles/tracker.md`. Run `base --sync <subject>` once to save the round's first preview. Run `step --writer <Board publisher> --actor agent:<your name>` for each part, with a shell time limit of 600 seconds. Each step makes a fresh preview, compares it with the saved preview, and applies only its own fingerprint for at most 1 part of 10 writes. Follow the table for differences, waits, failures, and recovery. A `published` closes the `SYNC`; the next round needs a new `base`. Keep the table's stop when stderr says `the SYNC stays open after its apply`.

Setup approval authorizes routine publication to the saved target; the `SYNC` approves the round. Neither authorizes overwriting unexplained human edits. Inspect the preview against the repository's update boundaries and any evidence from the last verified result. Preserve the publication frequency limit. Do not bypass a refusal through a direct Plan script, raw Beads sync, or a personal login.

Both `sofa-plan` and `sofa-publish` use the same execution checks. Before each apply, they check enablement, the approved workspace, Project and repository identities, type mode, App installation, and writer. They supply the factory App environment for GitHub commands. Disabling and applying share a non-waiting local lock, so a disable between parts stops the next apply. These are consistency controls, not a security boundary against a process that can edit local files or call GitHub directly.

Plan verifies affected remote values before it returns `published: true` and `complete: true`. Only that result advances the local `last_verified` record. A failed command or `complete: false` leaves the prior result unchanged. Report partial effects, remaining work, and any retry time. A command exit of zero alone is not success.

For `unknown-create`, follow the tracker table exactly. Run one further `step` in the same turn only when the outcome line has `"retry": true` and stderr has no line `a file operation failed`. The script waits up to 31 seconds before that step's preview. With `"retry": false`, no `retry` key, or that stderr line, send `BLOCKED · team` with the error text. Do not run `recover` for `unknown-create`, because it repairs local records rather than an uncertain GitHub create. The table also gives the Plan version requirement and the action for each of the two unknown-create error texts.

Publication failures stop publication only. Report that the GitHub view is out of date; keep local factory work running. Access failures, changed targets, conflicting links, and unexplained board edits require correction, not repeated automatic attempts. A temporary service failure can wait for a later `SYNC`.

## Local state and recovery

Plan Project metadata remains the connection record; individual Plan records keep the issue and card links. Machine App values remain in the Sofa state store. The ignored `.sofa/github-publication.json` file stores versioned enablement, the approved target and App identifiers, approval time and fingerprint, and the last attempt and verified result. It contains no credentials and is written with mode 600. Do not copy its approval to another machine or commit it. Setup must obtain approval on the receiving factory machine.

`publication status` reads local evidence and the selected Plan identity, not live GitHub access. Readiness reports publication separately and does not block local factory work on this optional check. App access and the live target are checked during preview and publication.

After an upgrade from a release with no approval file, publication is disabled until setup completes. Existing Plan and GitHub links are retained. Restart the tracker on the updated plugin before enabling publication. An older session or another publisher does not acquire the new wrapper controls merely because the plugin was installed.

## GitHub references

- [Automating Projects with a GitHub App](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions)
- [Authenticating as an App installation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)
