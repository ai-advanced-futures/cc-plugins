---
description: Saves knowledge into the ux-hci-design graph - it confirms the pages of a run after the person accepts them and saves the behavior results into the PRD and the design tokens into the system design, or it saves a fact that the person gives - through ux_graph.py, then runs both checks and reports. Use for "/ux-hci-design:learn" and the "Learn these results?" offer of the ux-design skill.
argument-hint: "[RUN ID | a fact]"
allowed-tools: Read, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(gh api user --jq .login)
---

# Learn into the ux-hci-design graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails.
`U` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ux_graph.py --root <git root>`.

## Step 0: the guard

Run `$U resolve RUN-01`. When it exits 2, stop with: "This repository has no ux-hci-design graph. Run `/ux-hci-design:setup` first."

## Step 1: the person and the time

Run `gh api user --jq .login`. The output is `<login>`. When the command fails, ask the person for the login. The save code writes the time.

## Step 2: a run

When the argument is a RUN ID:

1. Run `$U verify-run <argument> --by "human:<login>"`. It gives the run page and each page of the run `status: stable` and one more `verified` entry, in one process. A second confirmation adds an entry. It does not replace the first.
2. When the command exits 1 or 2, stop and show its output. Do not report success, because no page is confirmed.

## Step 2b: the PRD and the system design

Do this step only when the argument is a RUN ID and Step 2 exited 0. A person started this skill, with a yes to "Learn these results?" or with the command `/ux-hci-design:learn <RUN ID>`, so the person asked for the save. This is the only place where `ux-hci-design` saves into the PRD and into the system design. A `ux-design` run with no answer to "Learn these results?" saves only the UX brain.

1. Read `<git root>/.claude/knowledge.json` with the Read tool. A missing file is the same as a file with no entry. With no `prd` entry and no `system-design` entry, go to item 4.
2. With a `prd` entry:
   - When the `ux-hci-design` entry has `"git": false`, say "The behavior results go into the PRD, and git keeps the PRD."
   - Run `$U behavior --run <RUN ID> --check-prd`. Its first line is `today <YYYY-MM-DD>`, the UTC date that the save writes.
   - On exit 0, say "The PRD holds each behavior result of this run."
   - On exit 1, when 1 line or more is `missing` or `different`, run the save of "The behavior save" below. Then run `--check-prd` again with the same command. When that run exits 1, show each line that is not `present` or `rejected`, and say "Run /product:explore experience to place these results in the PRD." When no line is `missing` or `different`, show each `error` and `extra` line, and say "Repair or remove the PRD pages that these lines name." Run no save.
   - On exit 2, show the output.
3. With a `system-design` entry: run `$U tokens --run <RUN ID> --save`. Show its output. When its output is the line `The run has no design tokens.`, it wrote no page, so Step 4 does not check the `system-design` graph.
4. Say the line of the case:
   - No `prd` entry and no `system-design` entry: "The behavior results are in the UX brain. To add them to the PRD, run /product:setup and /system-design:setup first."
   - No `prd` entry and a `system-design` entry: "The behavior results are in the UX brain. To add them to the PRD, run /product:setup first."
   - A `prd` entry and no `system-design` entry: "The design tokens are in the UX brain. To add them to the system design, run /system-design:setup first."
   - Both entries: no line.

   Then go on to Step 4, because Step 3 is only for a fact.

### The behavior save

Run this save when the first `--check-prd` run exits 1. A line that is `present` or `rejected` is not in the save, because a person rejected a `rejected` result, and the PRD already holds a `present` result. `ux-hci-design` writes no PRD page itself. The skill `product:learn` writes each page.

- Run `$U behavior --run <RUN ID>`. It prints the behavior results of the run as a list. Each item has `prd_type`, `kind`, `path`, `title`, `description`, `brain_type`, `pattern_kind` and `hash`.
- The check prints the `today` line, then 1 line for each item, in the order of `$U behavior --run <RUN ID>`. A `present` line holds only the PRD ID, so match it to its item by its place in that order. A `missing`, `different` or `rejected` line also holds the brain path. An `extra` line and an `error <path>: <reason>` line come after the items. They are not items. Show them to the person, because the save does not change the PRD page that they name.
- Find the brain page of each item that has a `missing` or `different` line: run `$U pages <brain_type> --run <RUN ID>`. The brain page is the entry whose `path` is the `path` of the `ux-hci-design` entry of `knowledge.json` followed by the `path` of the item.
- Invoke the skill `product:learn` 1 time with the `Skill` tool and the argument `experience`. The message holds the date of the `today` line, only the items of the lines that are `missing` or `different` (each with its line and its brain page), and the 8 rules below.
- For a state rule or a screen interaction, add its Screen page and, when that screen is `present`, the PRD ID and the `describes` of its PRD page.
- For a pattern (`pattern_kind: pattern`), add the PRD ID and the `describes` of each Screen result of the run that is `present`.
- When the `Skill` call fails because the skill `product:learn` is not there, say "Install the product plugin to add the behavior results to the PRD: claude plugin install product@cc-plugins".

The 8 rules of the message:

1. 1 PRD page for each item. The type is `prd_type`. An `Experience` page gets `--set kind=<kind>`.
2. A new page gets `--set 'sources=[{resource: "ux-hci-design:<path>", id: "<ID of the brain page>", hash: "<hash>", last_modified: "<the date of the today line>"}]'`. The `<path>` is the `path` of the item, and it starts with `/`.
3. An `Experience` page gets 1 or more `--link describes=<target>`: the Capability or the Journey of the PRD that the screen, the state or the rule belongs to. For a state rule or a screen interaction, use the `describes` of its screen when the message gives it; else read the `concept` and `journey` links of its Screen page. A pattern (`pattern_kind: pattern`) is a rule for each screen, so it gets the `describes` targets of each Screen result of the run: the targets that the message gives for a `present` screen, and the targets that this save gives to a new screen. When no target fits, write no page, and name the item in the report.
4. A user flow (`prd_type: Journey`) is a Journey page with `serves` a Persona of the PRD. When a Journey page of the PRD already holds the same flow, change that page: add the `sources` entry to its list, and keep the other entries.
5. When an Experience page of the PRD already holds the same screen, state or rule (the experience lens wrote it, or an earlier run saved it), change that page: add the `sources` entry to its list, and keep the other entries. 1 fact, 1 page.
6. A `different` line names the PRD page. Change that page, and write the new `hash` and `last_modified` in its `sources` entry; the `id` stays. Make no second page, because a second page splits 1 result in two. For the line "2 PRD pages hold this result", keep the page with the lower ID, and remove the `sources` entry of this result from the other page.
7. Write no design token and no component name of the brain page into the PRD page. Copy no persona name, no quote and no research fact. Write the behavior only.
8. When the lens `experience` of `product.md` is `not-started` or absent, set it to `in-progress`. Keep a lens that is `in-progress` or `complete`, because a person or an earlier run set it. When a Decision page says that the product needs no experience lens, tell the person that the UX brain holds screens of the product, and ask if that Decision page still holds. On "no", set it to `status: deprecated`. With no answer, keep it and save.

`product:learn` then runs its own steps: the product hat, `regen` and `check`, `knowledge:checking`, `drift --write`, and the log line. Leave these steps to `product:learn`, because a second run repeats each check and each log line.

## Step 3: a fact

When the argument is a fact:

1. For each name in the fact (a persona, a screen), run `$U resolve <name>`. A hit through `aliases` is the same page. Change that page, because a second page splits one thing in two.
2. A new page: `$U new <Type> --title "<title>" --description "<one line>" --set KEY=YAML`. A changed field: `$U set <ID> KEY=YAML`. A new link: `$U link <ID> <field> /<folder>/<ID>.md`. A page of each type except `Run` belongs to 1 run: add `--set run=[/runs/RUN-NN.md]`. With no run, `new` writes no page and exits 1.
3. Run `$U verify <ID> --by "human:<login>"` for each page that you made or changed, because the person gave the fact.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `ux-hci-design`. Also call it with the graph `system-design` when item 3 of Step 2b wrote a page. Never report success while it returns `CHECKS: FAILED`, because the person must see the failure.

## Step 5: report

Report each page that you made or changed, and each ERROR, WARN, and SKIP line of the checks. For a RUN ID, also report each line that Step 2b showed, and say if the `product:learn` call ran.
