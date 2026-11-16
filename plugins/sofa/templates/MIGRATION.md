# Migration of docs/adlc.md

The `sofa:start` skill reads this file when `docs/adlc.md` has a lower `sofa-template-version` than `templates/ADLC.md`. Apply each step from the version of the file to the current version, in order. Keep each value and each repository rule of the file. Ask the user only for the values that a step marks `ask`.

## 13 → 14

A repository has 1 factory on 1 machine. This step removes the text for several machines and teams. It is a template update: do not import a roadmap or change the selected backend.

1. Section 1, the table: add the row ``| Factory | `<app slug>` |`` after `Repository` (ask). The value is the slug of the GitHub App of the factory (the output of `<skill folder>/scripts/sofa-state kv get machine.github-app.slug` on the factory machine), or `none` for a team with no App.
2. Section 1: remove the sentence `They are the same on each machine that starts the team.`
3. Section 1, `Board publisher`: set it to the GitHub account of the factory (`<slug>[bot]`, or the `gh` account of a team with no App). Keep a value that already names that account.
4. Section 1: replace the subsection "Plan workspace and activation" with the paragraph about the `Factory` row and the subsection "Plan workspace" of the template. Remove each repository line there about an activation state, a workspace or control identity, a gate, or a machine that joins. Keep each other repository line.
5. Section 1, machine values: replace the first sentence with the template sentence, replace the 3 bullets `Main folder`, `Skill folder` and `GitHub account` with the template bullets when they have the template 13 text, and remove the `GitHub person` bullet.
6. Section 2: replace the rule whose text starts with `Mention the operator` with the template rule "Mention the human team". Keep its number, because other files cite the rules of this section. Keep each sentence that is a rule of this repository and names no operator and no machine.
7. Section 2 and "Repository rules": show the user each rule that exists only for several machines or teams, and remove it after the user agrees. These are: a rule that 2 teams or 2 machines work on 1 repository, a team part in a branch name, a bot for each machine, a floor publication, a block of decision ids, and each allowed special ref other than `refs/dolt/data`. Do not give a new number to a rule that stays: leave the number of a removed rule free, and say so in its place.
8. Section 3: in the tracker row, remove `plan:sync` from the skills. Replace the `Input` and `Output` cells of the tracker row, and the publisher row of "Who writes which file", with the template cells when they have the template 13 text.
9. Section 4: in the feature flow, replace the first 4 lines of the block (from `shared Plan workspace/control` to `guarded shared publication`) and its last line with the template lines. Replace the sentence above the block, and the `Gap in PRD or roadmap` line of the side flows, with the template text. Skip each one that does not have the template 13 text.
10. Section 5: replace the text of the `SYNC` row with the template text when it has the template 13 text.
11. Section 8: remove `of this machine` after `from the main folder`. In the start prompt, remove `, GitHub person <gh person>` from the `Machine values:` line.
12. Machine: when `sofa:readiness` shows `roadmap-backend` as `wrong` with "the Plan profile is still shared", the Plan profile needs `sofa-plan unshare` while the team is stopped. Do "One-time unshare" of `<skill folder>/references/planning.md` before the start of the team.
13. Machine, with the backend `plan`: run `<skill folder>/scripts/sofa-plan --repo <main folder> describe --json`. The automatic backup is on when `backup.auto` is `true`. Else run `/sofa:setup` (step 2.4).
14. Section 9: add the row `Migrated to sofa template version 14; 1 factory on 1 machine`.
15. Set `<!-- sofa-template-version: 14 -->`.

## 12 → 13

This is a template update, not a roadmap import or Plan activation. Do not run `migrate --apply`, create a store, change the selected backend, or start Plan writers as part of this step.

1. Section 1: if `Roadmap backend` is absent, add `| Roadmap backend | product |`. This preserves the existing factory as explicitly legacy Product. Keep an existing `product` or `plan` choice. An unknown value needs a setup decision; do not infer a choice from installed plugins or profile files.
2. Section 1: if `Plan workspace` is absent, add `| Plan workspace | .claude/plan/local.json |`. This is an inactive path for a legacy Product factory, not permission to create or import a store. Keep an existing profile choice. Its path is relative to the main checkout, never a worktree.
3. Add the template's "Plan workspace and activation" subsection if absent (from template version 14, its name is "Plan workspace"). Keep the existing board, Product docs, tools, role skill rows, and legacy Product flows when the selected backend is `product`. Do not replace these rows with the Plan-default rows. Add a note before the flows that the selected backend's instructions in `<skill folder>/references/planning.md` and the shipped role files apply. For an already explicit Plan choice, check the workspace and repository role overrides before a start; the template update itself supplies no activation evidence.
4. Keep each repository rule and ownership boundary. Add the planning-contract source distinction: code, specs, and PRD come from `main`; selected Plan work comes from the Plan store of the factory; legacy Product work comes from roadmap pages on `main`. Retain the GitHub Project, its bindings, and its board publisher. Product Proofs lines still mean that the verifier ran the product as a user. Metrics remain in Sofa.
5. Section 9: add `Migrated to sofa template version 13; roadmap backend preserved`.
6. Set `<!-- sofa-template-version: 13 -->`.

A later request to use Plan is a separate change that the user approves. Follow `references/planning.md`, "Conversion of a legacy Product factory". A preview or an empty store is not a conversion. Do not run both roadmap backends.

## 11 → 12

1. Section 3, the paragraph that starts with `Tier:`: if it has the words `, and it resumes a session that Claude Code stopped`, replace them with `. It gives a session that Claude Code stopped a fresh restart`. Skip it if the paragraph does not have these words.
2. Section 8, the line of the dispatch script: if it has the option `--resume`, remove that option and its value. In the template 11 text, that is the part ` [--resume <session id>]` at the end of the line. Skip it if the line does not have `--resume`.
3. Section 8, the paragraph that starts with `Exception, a fresh restart`. Replace the sentence `The same holds for the new session that the orchestrator starts when a resume fails.` with the 2 sentences of the template from `This holds for each restart`. Replace the sentence `Why: a store row with the old id makes the orchestrator resume a session that can lack the App env.` with the `Why:` sentence of the template. Skip each sentence that the paragraph does not have, because the paragraph can hold the words of the repository.
4. Section 8, the paragraph that starts with `If a session stops before its item is done`: find the sentence that has `--resume <session id>`. Replace that sentence with the text of the template paragraph after its first sentence. Remove each other sentence of the paragraph that has `You were resumed` or `If the resume fails`. Keep each other sentence of the paragraph, because it can be a rule of the repository. Skip this item if the paragraph does not have `--resume <session id>`, because then the repository already gives a stopped session a fresh restart.
5. Section 5, the row of `RESUME`: if its text is `From the orchestrator: continue the open item from the branch`, replace that text with the text of the template row. Skip this item if the row has other text, because it can be a rule of the repository.
6. Section 9: add the row `Migrated to sofa template version 12`.
7. Set `<!-- sofa-template-version: 12 -->`.

## 10 → 11

1. Section 2: add the template rules "Mention the operator" and "The App identity for git and gh" at the end of the list, with the next free numbers. From template version 14, the first rule has the title "Mention the human team": add that rule in its place. Skip a rule if section 2 already has a rule whose text, after its number, starts with the title of the template rule (the words in quotes above): keep that rule as it is, because its text can hold the details of this repository. Each file cites these 2 rules by their title, not by their number, so the numbers can differ from the template.
2. Section 8: add the paragraph "Exception, a fresh restart" of the template after the paragraph about the session names. Skip it if section 8 already has a paragraph that starts with `Exception, a fresh restart`.
3. Section 1, machine values: skip the `GitHub person` bullet when the template has none (template version 14 or later). Else, if the list has no bullet that starts with `- GitHub person:`, add the `GitHub person` bullet of the template after the `GitHub account` bullet. If the `GitHub account` bullet is ``- GitHub account: the active `gh` account on this machine. Sessions commit, push and open PRs as this account.`` (the text of version 10 before the App), replace it with the `GitHub account` bullet of the template. If it has another text that does not name `<slug>[bot]`, keep that text and add the sentence ``With a team App (`sofa-github check` exits 0), it is `<slug>[bot]`.`` at its end. The template got these 2 bullets after version 10 with no step, and the 2 new rules use them.
4. Section 8, start prompt: skip this item when the template line has no `GitHub person` (template version 14 or later). Else, if the `Machine values:` line has no `GitHub person <gh person>`, add `, GitHub person <gh person>` before its final full stop. The template got this value after version 10 with no step, and the rule "Mention the operator" needs it.
5. Section 9: add the row `Migrated to sofa template version 11`.
6. Set `<!-- sofa-template-version: 11 -->`.

## 9 → 10

1. Section 3: replace the `Tier:` text with the `Tier:` text of the template. Keep a `Tier:` text that differs from the template 9 text, because that difference is a choice of this repository.
2. Section 8: remove the sentence "A session that the orchestrator deleted (`claude rm`) is not in that list, so its number is free again." In the last paragraph, replace the resume prompt with the template text (the added sentence about the worktree). If the template has no resume prompt (template version 12 or later), skip this sentence. The step 11 → 12, item 4, then replaces the resume text of that paragraph.
3. Section 9: add the row `Migrated to sofa template version 10`.
4. Set `<!-- sofa-template-version: 10 -->`.

## 8 → 9

1. Section 3: for each of decision-judge, scribe, tracker, plan-auditor, merger and monitoring, set the tier to `on demand` if the row has `always`. Set the `Starts when` cell if the row has the template 8 text: decision-judge `Always running` becomes ``A `BLOCKED · decision`, or an `ASK` for hitl``, scribe `Always running` becomes ``A `learn:`, `validate` or `lower` task``, and monitoring `An environment exists` becomes ``An environment with logs or metrics exists, or a feature is `done` ``. Keep the `Starts when` cells of tracker, plan-auditor and merger, because template 9 has the template 8 text in them. Keep a tier or a `Starts when` cell that differs from template 8: that difference is a choice of this repository.
2. Section 3: add the `Tiers:` paragraph of the template below the roles table, above the `Compact at:` note.
3. Section 4, decision flow: replace `knowledge:ask in a fork` with `knowledge:ask (station Rule 2)`, as in the template line.
4. Section 9: add the row `Migrated to sofa template version 9`.
5. Set `<!-- sofa-template-version: 9 -->`.

## 7 → 8

1. Header: in the sentence that names the retro session as the only owner of this file, add `docs/adlc/colours.md`.
2. Section 3, "Who writes which file": in the retro row, add `docs/adlc/colours.md`.
3. Section 6, step 2: add `docs/adlc/colours.md` to the files that the fast path can change.
4. Section 9: add the row `Migrated to sofa template version 8`.
5. Set `<!-- sofa-template-version: 8 -->`.

## 6 → 7

1. Section 3: remove the `Colour` column from the roles table, and remove the `Colour:` note below the table. The colours are now in `<skill folder>/references/colours.md`. The v6 template differs from that file in 2 rows only: `tracker` was `yellow`, and `scheduler` had no colour. Do not keep these 2 old values, because they are not a choice of this repository. For each other role whose old colour differs from that file, or that is not in that file, add a row with the role and the old colour to `docs/adlc/colours.md` (a table with the header `| Role | Colour |`), so the repository keeps its colour.
2. Below the `Output style:` note, add the `Colour:` line of the template.
3. Replace the sentence about a live session after `RELOAD` with the template sentence.
4. Section 9: add the row `Migrated to sofa template version 7`.
5. Set `<!-- sofa-template-version: 7 -->`.

## 5 → 6

1. Section 1:
   - Add the rows `Risk appetite` (ask), `Domain model` (`docs/domain` if the `ddd` brain exists, else `none`), `Proofs folder` (`docs/proofs`), `Environments` (ask), `Healthy window` (`24h`), `Slack` (`none`; `/sofa:setup` adds it later).
   - Add the table "Tools per role". Take `tracker` from the old `Board tool` value (GitHub Projects → `gh`). Ask the others, or set `built-in` and `none`.
   - `System design`: keep the value.
2. Section 2: replace the 15 rules with the new short section. The old rules 1–10 and 12–15 are now in the `sofa:station` skill. The old rule 11 (story `ready`) is the new rule 1. Add the new rules 2 (states, `released`) and 3 (who writes which file). Keep each repository-specific rule that the retro added: move it to section 1, "Repository rules".
3. Section 3: replace the roles table with the template table. For each row of the old table whose model, effort, colour or count differs from the v5 template, keep the old value (it is a choice of this repository). Add the columns `Tier` and `Output style`. Add the rows `requests`, `decision-judge`, `scribe`, `plan-auditor`, `merger`, `monitoring`, `scheduler`, `designer`, `business-domain`, `security`, `code-quality`, `troubleshooter`, `operator`, `feedback`, `ux-quality`, `updater`. Add the table "Who writes which file".
4. Skill names in the table and in `docs/adlc/roles/*.md`: `prd:` → `product:`, `adr:` → `architecture:`, `adr:scaffolding-adr-corpora` → `architecture:setup`, `pr-flow:reviewing-prs` → `code-review:reviewing-prs`, `ui-judge:*` → `playwright`.
5. The architect no longer owns the system design: if `docs/adlc/roles/architect.md` has lines about the system design, move them to `docs/adlc/roles/designer.md`.
6. Section 4: replace with the template section 4 (flows, release flow, decision flow, decision tables). Keep any repository change of the old "Ask the Rule" text.
7. Section 5: add the types `PAUSE` and `RESUME`.
8. Section 8: replace with the template section 8 (dispatch script, new start prompt).
9. Section 9: add the row `Migrated to sofa template version 6`.
10. Set `<!-- sofa-template-version: 6 -->`.
11. Machine: `.sofa.state.json` → the state store. If `.sofa.state.json` exists in the main folder, run `sofa-state init`. Then copy its sessions and its items, as the next sentences say. Run each copy command with `env -u CLAUDE_CODE_SESSION_ID`, because a migration writes the rows of other sessions and is not the write of 1 session of the team. Copy each session with `--id ""` in the command `sofa-state session upsert`: a name that has a row keeps its live id, and a new name gets `NULL`, so an old id does not count as a restart of a live session. Copy each item with `sofa-state item set`. `item set` accepts only these states: `backlog`, `ready`, `in progress`, `in review`, `fix round`, `waiting`, `blocked`, `done`, `merged`, `released`, `cancelled` and `superseded`. Copy each item with a state of this list. When the state of an old item is not in the list, the exit-2 message of `item set` names the word: use the nearest state of the list. When an old item has no state, use `--state backlog`. Skip an item whose id is not in the form `[A-Za-z0-9][A-Za-z0-9._:-]{0,79}`, and list it in the report of the migration. An id of the form `STORY-<n>`, `FEATURE-<n>` or `MILESTONE-<n>` is a roadmap row. Each other id is a work order. Copy each work order with `--session` and the session of the old item. When the old item has no session, give the name of the orchestrator of the team, because the orchestrator holds the work that no other session holds, and list the row in the report of the migration. Then delete the JSON file. Replace the `.sofa.state.json` line of `.git/info/exclude` with `.sofa/`.
12. Machine: run `/sofa:setup` for the new items (scheduler cron line, tools per role, human team).
