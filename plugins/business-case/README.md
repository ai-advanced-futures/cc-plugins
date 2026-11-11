# business-case

A person brings a thin business case. The plugin maps it against a versioned rubric and finds what a funder (the person who decides whether to put money in; for now, you play that part) would ask for and cannot find. It coaches the person to fill each gap. Code computes the numbers from the figures you confirm. An independent review checks the evidence, the completeness, the strategy and the investment. It reads only the case files, not the coaching conversation. The person, in the funder's role, records a decision for every gap. Code decides when the loop ends, and the run ends with a funding decision.

Use it when someone has to decide whether to fund an offering, and the business case for it is thin, has claims with no evidence, or is not finished. Bring the document you have: a proposal, a strategy, or both. The plugin checks the case against a versioned rubric, helps you fill each gap, works out the numbers from the figures you confirm, has an independent review in a fresh context check the case, and records each decision you make, in the proposer role and then in the funder role. Code decides when the case is done. The run ends with a decision to fund, not fund or defer.

## Install

```
claude plugin install business-case@cc-plugins
```

The plugin needs:

- **`uv`**, because the coach calls `uv run "${CLAUDE_PLUGIN_ROOT}/lib/bc.py"`. The script needs no package.
- **`python3` 3.9 or later**, for the 7 guard hooks (see "How it runs, and its limits").
- **The `knowledge` plugin**, for the case graph (see "The case graph"). The save code `scripts/bc_graph.py` also needs `uv`, because it runs with `pyyaml` and `jsonschema`.
- **Claude Code 2.1.295 or later**, because the hooks use `"onFailure": "block"`.
- **The evidence plugins**, when you want the evidence team to run them. Install each one with `claude plugin install <plugin>@cc-plugins`: `jtbd-market-discovery`, `competitive-intelligence`, `pricing`, `product-finance` and `gtm`. `value-ip` is optional and comes from outside this marketplace.

The analysts search the web (`WebSearch` and `WebFetch`). A search query can hold words of your case.

## How to run it

```
/business-case:build [path-to-proposal] [--strategy path] [--automated --offering <name> --market <market>]
```

The command runs in your own session and asks you each question it needs. It keeps the case in `business-cases/<slug>/` in your repository, and a later session picks the case up from those files.

Claude Code asks you to approve some of the coach's steps and plugin runs: about 200 times in one full test run before the hook of this plugin. The hook approves the steps of a plugin run, but a run still asks for each web search. The permission mode called auto asks far less; switching to it is your choice: in the CLI, press Shift+Tab or start with `--permission-mode auto`; in Desktop, use the mode picker.

The command gives the plugin runs it starts these grants, and no others. A runner gets no permission from its own
tools list: it uses the rules of the conversation that starts it. Each grant lets a runner write its run folder and
its session folder in the `.<plugin>/` folder, and read the answers file of the case. The hook of the next paragraph
approves its script calls:

<!-- runner-grants:start -->
```
Edit(/.competitive-intelligence/**)
Edit(/.gtm/**)
Edit(/.jtbd-market-discovery/**)
Edit(/.pricing/**)
Edit(/.product-finance/**)
Read(**/team/answers-*.json)
```
<!-- runner-grants:end -->

Seven runs are skills: `competitive-intelligence:discover`, `competitive-intelligence:analyze`,
`jtbd-market-discovery:discover`, `jtbd-market-discovery:wtp-check`, `gtm:marketing-launch-runner`,
`gtm:marketing-brand-runner` and `gtm:marketing-funnel-runner`. The command starts them with the `Skill`
tool, so it has one `Skill(<route>)` grant for each of the seven routes. It has one more, `Skill(business-case:learn)`,
for the question at the end of an interactive run, and no `Skill` grant for any other skill. The command also has
the grants for its own 2 scripts, `bc.py` and `bc_graph.py`.
The 3 routes of `gtm` are skills from version 1.11.0 of `gtm`, which is the floor of the plugin map.

A run of `value-ip:analyze` or `product-finance:cost-coverage` is yours: the command starts neither, so it gives
no grant for them.

The source of each runner list is the `caller-grants.json` of each runner plugin, with the same list in the README of that plugin
under "Grants that a caller must give". A test of this plugin compares the scripts of each file with the table of the hook, and
the `Edit` grant of each file with the line above. The web tools and the MCP tools of a runner are not in the command or in the hook:
in a session with a person, Claude Code asks for each web call, and in a headless run the call is refused and the run goes on with a gap in its result file.

Claude Code applies a grant only during the turn of the command, so each grant ends when the command ends. A grant ends with the turn, and a run in the background ends the turn. So the hook `hooks-handlers/runner_guard.py` approves, in a session that started a build, only 1 exact call of `bc.py`, of `bc_graph.py publish` or of a listed runner script, a write in a runner folder or in the temporary folder of a case, a read of a file of a runner plugin or of an answers file, and, in the conversation of the coach, the `Skill` call of a route whose `args` are the `plugin-run` block that `team-answers` printed for an open run of that route in a case of the session.

Two limits of these grants:

- A `*` in a `Bash` grant matches any text, with spaces, so the command has no such grant for a runner script. The hook checks the words of the call. It does not check the value of an argument, and `uv run` reads a `pyproject.toml` of the project. A command with other words in front gets no approval from the hook, so it asks you. See ADR-016.
- The folder grants are `Edit` rules, because Claude Code checks a file write against the `Edit` rules. A `Write` rule with a path does not match a write. Each grant names the whole `.<plugin>/` folder, because the run folder (`.<plugin>/<run_id>/`) has a name that is not known when the command starts, and the folder also holds files at its root.

A run goes like this:

1. **Intake.** You give the proposal, the strategy, or both. Each one is kept as given and never edited.
2. **Map.** The coach maps the case against its rubric and proposes, for each item, whether it is present and factual, present but weak, or missing. A proposal is not a verdict. Only the independent review makes an item met. A new case opens on the newest rubric, which asks for the numbers code computes. The coach offers to move a case opened on an older rubric; the move is the funder's decision.
3. **The evidence team.** For the items that need evidence, the coach asks the analysts that own them, each in its own sub-agent, what to run and what to ask you. The team has eight analysts; one that owns no such item is not asked. The coach asks you their questions on cards, then runs the commands they plan from jtbd-market-discovery, product-finance, pricing, competitive-intelligence and gtm. Those plugins must be installed and on: before the first plan, the coach tells you each one it cannot use. You run `product-finance:cost-coverage` yourself, when the coach asks. `value-ip` is an optional plugin from outside this marketplace; the coach asks you to run `value-ip:analyze` only when `value-ip` is installed, and this README gives no install line for it. Each analyst then drafts results from what the runs wrote, and each result becomes an evidence page only after you confirm its grade.
4. **Fill the gaps.** You and the coach improve the case one section at a time. Each piece of evidence becomes an evidence page, and you confirm its grade: from your own source, from a published source, or an estimate. Each money amount in the case becomes a figure in the financial figures file, and you confirm each one (see "The numbers and the verdict").
5. **Strategy.** You and the coach fill the strategic decisions register, the conditions list and the notes list. Each choice about the offering goes in one of eight categories. Code shows the result in `strategy-view.md`.
6. **Independent review.** A reviewer in a fresh context is given only a code-written brief that names its input files. It reads only the case files, not the coaching conversation. Claude Code cannot stop a sub-agent from reading other files, so a report counts only while its manifest equals the current file set. The review checks the evidence, the completeness and the strategy files, checks the plan as a whole, and writes its reply. A change to the register, the conditions or the notes makes the report stale.
7. **Funder decisions.** You switch to the funder role and decide each finding. Each decision records your reason in your own words, your role and your name.
8. **Loop.** Code decides when the loop ends. Every item that applies must be met, accepted as a risk or waived. The latest review report must be current, and you must decide every finding, including each empty category and each orphaned condition. Until then, the coach goes back to the step each open reason needs. Each session has 5 independent reviews; when they are spent, the case resumes from its files in a new session.
9. **Funding decision.** The coach shows you the numbers first. You decide to fund, not fund or defer, with a reason.

## The case folder

One case per folder, `business-cases/<slug>/`. Code writes every file in it: `bc.py`, and the hook for the receipt. The two exceptions are the independent review's reply and each analyst's reply.

| File | What it holds |
|---|---|
| `case.json` | slug, offering, market, rubric version, session budget, sessions |
| `scope.json` | market, rubric version and applicable item IDs; written by `init` and by `move-rubric` |
| `rubric.json` | a copy of the pinned rubric version |
| `inputs/proposal.original`, `inputs/strategy.original` | each input as given, never edited |
| `inputs/proposal.text.md`, `inputs/strategy.text.md` | only when that original is not UTF-8: the session's text extraction |
| `changelog.jsonl` | one entry per change to the case; append-only |
| `business-case.md` | the case; created by `init` from the template, then written only through `bc.py change` |
| `evidence/EV-NNN.json` | evidence pages |
| `ledger.json` | the item ledger: the coach's proposal for each item |
| `decisions.jsonl` | the decision record; append-only; created empty by `init` |
| `register.jsonl` | the strategic decisions register; append-only, and an edit to an earlier line is refused; written only by `bc.py register` |
| `conditions.jsonl` | the conditions list; append-only, and an edit to an earlier line is refused; written only by `bc.py condition` and `bc.py mark` |
| `notes.jsonl` | the notes list; append-only, and an edit to an earlier line is refused; written only by `bc.py note` |
| `strategy-view.md` | the register as one page; written by `bc.py view`, never by hand |
| `judge/brief-NNN.txt` | the brief code writes for one independent review; names the reply path |
| `judge/reply-NNN.json` | the independent review's reply, written by the review only |
| `judge/reply-NNN.receipt.json` | the receipt the hook writes after the review's Write completed |
| `judge/report-NNN.json` | the validated report, `"written_by": "judge"` or `"coach-copy"` |
| `figures.jsonl` | the financial figures file: each figure and your confirmation of it; append-only, and an edit to an earlier line is refused; written only by `bc.py figure` and `bc.py mark` |
| `figure-refusals.json` | the proposals the latest `bc.py figure` run refused, or the refusal of the whole run, with the reasons, and the amounts it left uncovered; replaced on each run |
| `finance.json` | the numbers and the highest verdict they allow; written only by `bc.py brief`, for the independent review |
| `finance-view.md` | the numbers in plain words, for you and the funder; written only by `bc.py compute`, never by hand |
| `funding/finance-report-NNN.json` | a copy of the numbers a funding decision rests on; never rewritten |
| `team/brief-NNN.txt` | the brief code writes for one analyst round; names the reply path |
| `team/brief-NNN.cancelled.json` | marks a brief the coach cancelled; written by `bc.py team-brief --cancel` |
| `team/reply-NNN.json` | the analyst's reply, a plan or results, written by that analyst only |
| `team/reply-NNN.receipt.json` | the receipt the hook writes after the analyst's Write completed |
| `team/reply-NNN.check.json` | written by `bc.py team-reply --check` when a reply passes: the sha256 of the reply and of each file it cites |
| `team/cards-NNN.json` | the card record: every card of the merged plans, and its answer |
| `team/answers-NNN.json` | the answers file the plugin runs read |
| `team/runs.json` | the run list: each plugin run, the person's runs and their results or gaps |
| `team/upstream/<name>.json` | a snapshot: the results of one run of `jtbd-market-discovery` or `competitive-intelligence`, as `bc.py team-run` read them from the graph of that plugin; written 1 time |
| `team/.lock` | the lock each team command holds while it writes |
| `business-case-handoff.json` | what a run hands to you and to a later session; an interactive run writes it too |

## The review report and the coach copy

The independent review writes its own reply to the path its brief names. A hook records a receipt of that write. `bc.py save-report` checks the receipt and the reply, and saves the report marked `"written_by": "judge"`. On this path the coach never handles the report text.

If the review's write is refused, the coach copies the JSON the review returned to a file outside the case and runs `bc.py save-report --coach-copy`. That report is marked `"written_by": "coach-copy"`. A coach copy can be read, but it cannot end the loop. A funding decision needs the loop to be done, and a coach copy never ends it.

## The numbers and the verdict

Every money amount in the case goes into the financial figures file, `figures.jsonl`. A second sub-agent reads the case and proposes each figure. Nothing enforces what it reads, so code checks every proposal against the case's own sentences and its evidence pages, and you confirm each figure. A proposal code refuses is shown to you with the reason.

Each figure takes the grade of its evidence page: from your own source, from a published source, or an estimate. A value of the business beyond the horizon, and a number whose evidence names the case's own text, count as an estimate. An estimate counts only after the funder approves it.

Code computes NPV, payback and ROI for each scenario from the figures that count, and sets the highest verdict the numbers allow. The verdict reads "supported", "not yet determined" or "not supported". It reads "not yet determined" while a figure waits for you or the funder, while an amount in the case has no figure, or while too much of a total rests on estimates. It reads "not supported" when the numbers do not pay: NPV below zero, or cash that never pays back within the horizon, with the business's value at the end not covering what is still owed. Code applies this test first, counting every recorded cost and only the income that counts, so figures still waiting for an answer cannot rescue a case whose own numbers say no.

The independent review reads the figures and the numbers and computes nothing. It may give a lower verdict, and names the finding it rests on. When it says "not supported" because an evidence page contradicts the case's largest revenue figure, the coach shows you that first. You can correct the figure, bring newer evidence, or answer it in the case.

`finance-view.md` shows the numbers in plain words, for you and the funder. `finance.json` holds the numbers the review reads. When the funder records a funding decision, to fund, not to fund or to defer, code keeps a copy of those numbers in `funding/`.

## Automated mode

Automated mode covers intake, mapping and the independent review only. In mapping it also has the figures proposed and records each one code accepts, but it never confirms one. An automated re-run on an existing case copies the proposal only into the sections that still matched the template before it began. It records only the strategy's claims the case does not already hold, then skips the rest of intake. It records no decision. It ends with `DONE: business-case` and writes `business-case-handoff.json`, which names the open items. A run that stops short prints `FAILED: business-case — <cause>` in place of the DONE line; ADR-003 lists each stop. The run takes its values from the arguments: `/business-case:build <proposal> --automated --offering <name> --market <market> [--strategy <path>]`. When an argument is missing, the run makes no case. Code refuses each decision in an automated run, because every decision needs a person, so a run with no person (`claude -p`) works.

## The case graph

The plugin keeps a knowledge graph of its cases: the graph `business-case`, in the folder `docs/business-case/`. It follows the brain standard of the `knowledge` plugin. The case folder stays the record of a case: the coach writes only the case folder, and the independent review reads only the case folder. The pages are a copy of the case for a reader: you, a later session, or another plugin that links to a part of a case (ADR-015).

The graph needs the `knowledge` plugin and `uv`.

| Skill | What it does |
| --- | --- |
| `/business-case:setup [bundle folder]` | Makes the graph, writes a block in `CLAUDE.md` that says where the graph is, and writes the pages of each case folder of the repository. With no argument, the folder is `docs/business-case/` (the `--dir` of `init`). |
| `/business-case:learn [case page or correction]` | Confirms the pages of a case after you accept them: each page gets `status: stable` and one `verified` entry with your GitHub login. It can also add your note to the page of a case. It changes no value of a case: correct a value with `/business-case:build`. |
| `/business-case:ask <question>` | Answers a question from the pages, and writes nothing. It follows a link into the graphs of `jtbd-market-discovery` and `competitive-intelligence`, and it writes `(draft)` after each page that no person confirmed. |

**When the pages are written.** At the end of each run, after the handoff, the coach runs `bc_graph.py publish` for the case. `publish` makes the graph when the repository has none, and prints `INIT: docs/business-case/`. A new page and a changed page have `status: draft`. When `publish` fails, the coach shows `GRAPH: FAILED <exit code> <first error line>` and ends as usual: the case folder is complete, and the next run writes the pages. At the end of an interactive run, the coach asks "Learn these results?", and on yes it starts `/business-case:learn`. An automated run, and a run that stopped on its budget of reviews, ask nothing, and their pages stay `draft`.

**The hook.** The brain hook, `hooks/brain-hook.sh`, runs after a write to the folder of the graph and after a command that runs `bc_graph.py`. It runs `regen`, the brain check and the check of the `knowledge` plugin, and it blocks no write. It works with no `uv` on the `PATH`: it then uses `python3`, which must be version 3.11 or later, with `pyyaml` and `jsonschema`.

**The graphs of other plugins.** The evidence team reads a run of `jtbd-market-discovery` (version 1.9.2 or later) and of `competitive-intelligence` (version 1.10.8 or later) from the graph of that plugin, and not from a result file. `bc.py team-run` keeps a copy of each run that the case uses, a snapshot, in `team/upstream/` of the case folder. The snapshot is written 1 time, because an evidence page and a decision pin the bytes that you graded, and a page of another graph can change later. When the other graph gives no run, the run is recorded as a gap.

**Privacy.** The pages hold what the case folder holds: the text of each section, the name that you gave the coach, the reason of each decision, the money figures and the review reports. Git tracks the folder of the graph by default. When git ignores the case folder and does not ignore the folder of the graph, `publish` writes no page and prints a `PRIVATE:` line. The save code and the read of the other graphs make no network call.

The graph has 14 page types. The schema is `schema/business-case.yaml`. `scripts/gen-schema.sh` writes the JSON files next to it.

| Type | Prefix | Folder | Holds |
| --- | --- | --- | --- |
| Case | `CASE` | `cases` | one business case: the case folder and its status |
| Run | `RUN` | `runs` | one session of the coach on a case |
| Part | `PART` | `parts` | one section of the business case, or one page of a long section |
| Evidence | `EV` | `evidence` | one piece of evidence of a case |
| Decision | `DECISION` | `decisions` | one decision record of a case |
| StrategyEntry | `SD` | `strategy` | one entry of the strategy register, with its confirm records |
| Condition | `CONDITION` | `conditions` | one condition of the plan, with its marks |
| Note | `NOTE` | `notes` | one note of the strategy |
| Figure | `FIGURE` | `figures` | one money figure, with its confirm records |
| Finance | `FINANCE` | `finance` | the numbers that code computed from the figures of a case |
| Review | `REVIEW` | `reviews` | one saved report of the independent review |
| OpenItem | `OPEN` | `open-items` | one rubric item that the loop has not closed, with its state |
| ItemVerdict | `VERDICT` | `verdicts` | the verdict of one report on one rubric item |
| Finding | `FINDING` | `findings` | one finding of one report |

Only `scripts/bc_graph.py` writes the graph. Do not edit a page by hand. The coach and the 3 skills call it; you can also run it with `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py" <operation>`. The operations are `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `verify`, `verify-case`, `regen`, `check`, `log` and `publish`. An operation exits with 0 when it succeeds, with 1 when the data is wrong, and with 2 when the input is wrong.

- `publish --case DIR` writes the case folder `DIR` into pages. It works on a copy, runs `regen` and `check`, and moves the pages only when the check finds no ERROR. It leaves the case folder unchanged. When the project has no graph, it makes one and prints `INIT: docs/business-case/`. When git ignores the case folder, it writes no page and prints a `PRIVATE:` line that says what to add to the ignore file of git. The graph would show a private case otherwise.
- `check` runs the brain check. Its rules are `BC-schema`, `BC-id`, `BC-link`, `BC-required`, `BC-case`, `BC-run`, `BC-alias`, `BC-part`, `BC-source`, `BC-fresh`, `BC-upstream` and `BC-stale`. `BC-fresh` and `BC-upstream` give a WARN. `BC-upstream` gives a SKIP when the `knowledge` plugin is not there.
- `verify PAGE --by human:<login>` and `verify-case CASE --by human:<login>` record that a person confirmed a page, or a case and each page of it. `verify-case CASE --run RUN --by human:<login>` confirms the Case page, that Run page, and each `draft` page of that run only.
- An Evidence page links to the Result page of the graph of `jtbd-market-discovery` or of `competitive-intelligence` (`source_results`) when the run entry of the case names that page.

## How it runs, and its limits

Three plugin hooks guard the independent review and the analysts' replies (ADR-006). Five more hooks, `hooks-handlers/runner_guard.py`, approve the exact runner calls (ADR-016), and the brain hook (`hooks/brain-hook.sh`) is the ninth. All of them run in every session with the plugin enabled, not only during a business-case run.

- **Claude Code 2.1.295 or later.** The write guard and the dispatch guard declare `"onFailure": "block"`, which needs 2.1.295. Below that version, the guard makes no promise to fail closed.
- **A working `python3`, version 3.9 or later.** The hooks run under the `python3` on your `PATH`. The handler and the `lib` modules it imports keep to Python 3.9 syntax, so macOS's `/usr/bin/python3` works.

  In a session with the plugin enabled and no working `python3`, every file-tool write (`Write`, `Edit`, `MultiEdit`, `NotebookEdit`) and every sub-agent dispatch is blocked. A timeout or a crash in the hook blocks the call the same way.
- **No file tool writes in a case folder.** The write guard refuses `Write`, `Edit`, `MultiEdit` and `NotebookEdit` anywhere in a `business-cases/<slug>/` folder, for every caller. The review's own `judge/reply-NNN.json` and each analyst's own `team/reply-NNN.json`, while its brief is open, are the two exceptions. The guard knows a case folder by its names only. So a repository that itself sits under a `business-cases/<slug>/` path cannot be written with file tools while the plugin is enabled.
- **A case must resolve to `business-cases/<slug>`.** `bc.py` refuses a case folder whose resolved path is not `<anything>/business-cases/<slug>`. A case behind a renamed symlink is refused, because the guard would not see it.
- **Not under `~/.claude/`.** In a `claude -p` run of the live check, Claude Code 2.1.312's sensitive-path rule overrode the hook's allow for a case under `~/.claude/`. It refused the review's write as "a sensitive file". Treat a case under `~/.claude/` as unsupported. A case under `.claude/worktrees/` was not tested.
- **Routes the hooks do not see.** A shell write, a file-writing MCP tool, or a review started outside the `Agent` tool is not guarded. The command body forbids each of them. ADR-006 names them under "Residual risk".

## What it does not do

- **Later:** IRR, the sensitivity test, unit economics arithmetic, a verdict on any scenario but the base one, currency conversion, and a view of what changed since funding.
- Also not here: nested cases, and a coach run of `value-ip:analyze` and cost coverage (you run those two yourself).

## Documentation

Start with [docs/INDEX.md](docs/INDEX.md). ADR-000 is the overview, and ADR-006 records the guard on the independent review and what it does not prove. ADR-009 to ADR-011 record the financial figures file, the numbers and the verdict, and the move to a newer rubric.

## Tests

Run these commands from `plugins/business-case`:

```
pip install -r requirements-dev.txt
pytest tests/ -q -rs
```

The tests run with no skip.
