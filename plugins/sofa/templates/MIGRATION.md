# Migration of docs/adlc.md

The `sofa:start` skill reads this file when `docs/adlc.md` has a lower `sofa-template-version` than `templates/ADLC.md`. Apply each step from the version of the file to the current version, in order. Keep each value and each repository rule of the file. Ask the user only for the values that a step marks `ask`.

## 10 → 11

1. Section 2: add the template rules "Mention the operator" and "The App identity for git and gh" at the end of the list, with the next free numbers. Skip a rule if section 2 already has a rule whose text, after its number, starts with the title of the template rule (the words in quotes above): keep that rule as it is, because its text can hold the details of this repository. Each file cites these 2 rules by their title, not by their number, so the numbers can differ from the template.
2. Section 8: add the paragraph "Exception, a fresh restart" of the template after the paragraph about the session names. Skip it if section 8 already has a paragraph that starts with `Exception, a fresh restart`.
3. Section 1, machine values: if the list has no bullet that starts with `- GitHub person:`, add the `GitHub person` bullet of the template after the `GitHub account` bullet. If the `GitHub account` bullet is ``- GitHub account: the active `gh` account on this machine. Sessions commit, push and open PRs as this account.`` (the text of version 10 before the App), replace it with the `GitHub account` bullet of the template. If it has another text that does not name `<slug>[bot]`, keep that text and add the sentence ``With a team App (`sofa-github check` exits 0), it is `<slug>[bot]`.`` at its end. The template got these 2 bullets after version 10 with no step, and the 2 new rules use them.
4. Section 8, start prompt: if the `Machine values:` line has no `GitHub person <gh person>`, add `, GitHub person <gh person>` before its final full stop. The template got this value after version 10 with no step, and the rule "Mention the operator" needs it.
5. Section 9: add the row `Migrated to sofa template version 11`.
6. Set `<!-- sofa-template-version: 11 -->`.

## 9 → 10

1. Section 3: replace the `Tier:` text with the `Tier:` text of the template. Keep a `Tier:` text that differs from the template 9 text, because that difference is a choice of this repository.
2. Section 8: remove the sentence "A session that the orchestrator deleted (`claude rm`) is not in that list, so its number is free again." In the last paragraph, replace the resume prompt with the template text (the added sentence about the worktree).
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
11. Machine: `.sofa.state.json` → the state store. If `.sofa.state.json` exists in the main folder, run `sofa-state init`, copy its sessions and items with `sofa-state session upsert` and `sofa-state item set`, then delete the JSON file. Replace the `.sofa.state.json` line of `.git/info/exclude` with `.sofa/`.
12. Machine: run `/sofa:setup` for the new items (scheduler cron line, tools per role, human team).
