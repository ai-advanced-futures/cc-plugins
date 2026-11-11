# Migration of docs/adlc.md

The `sofa:start` skill reads this file when `docs/adlc.md` has a lower `sofa-template-version` than `templates/ADLC.md`. Apply each step from the version of the file to the current version, in order. Keep each value and each repository rule of the file. Ask the user only for the values that a step marks `ask`.

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
