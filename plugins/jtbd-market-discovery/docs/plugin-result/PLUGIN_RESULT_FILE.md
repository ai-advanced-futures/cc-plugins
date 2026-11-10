# Plugin Result File

**Version:** 1.1 (`plugin-result/1`). **Decision record:** `docs/adr/ADR-003-plugin-result-file.md`.

## What the file is

A plugin writes one JSON file when a run ends, beside its other outputs. Every plugin uses the same shape. Seven plugins depend on it: six plugins write result files in it, and business-case reads them. So the standard lives at repo level, and no plugin owns it.

business-case's analysts also write the shape, each in its own reply to a brief: `plugin` is `business-case`, and the file is the case's `team/reply-NNN.json`. That reply is not a run's result file, so the name rule (R-NAME) and the results folder do not apply to it. business-case checks it with `check_result()`.

The machine form is in `docs/plugin-result/schemas/`. That folder holds exactly five files:

| File | What it holds |
|---|---|
| `plugin-result.schema.json` | The shape of a result file. |
| `kinds.json` | The kind list. |
| `questions.schema.json` | The shape of a questions list. |
| `answers.schema.json` | The shape of an answers file. |
| `plugin_result_check.py` | The checker: one Python file, standard library only, safe on Python 3.9. |

A rule that a schema cannot state is written once, in the checker. The schema names the rule by its id.

## Where it goes

The file goes to `.<plugin>/results/<UTC timestamp>-<command>-<subject slug>-<run_id>.json`.

- The folder is under the git root of the run's working directory. When there is no git root, it is under the working directory. `git rev-parse --show-toplevel` gives the git root. It prints nothing and exits non-zero outside a repository.
- `<plugin>` is the plugin's full name, for example `.jtbd-market-discovery/results/`.
- `<UTC timestamp>` is `YYYYMMDDTHHMMSSZ`, taken from `run.finished_at`.
- `<command>` is the canonical command name without `<plugin>:`. Each further `:` becomes `-`. `gtm:marketing:launch` gives `marketing-launch`.
- `<subject slug>` is `run.subject` in lower case. Each run of other characters becomes one `-`. The slug has at most 40 characters and does not start or end with `-`. A subject with no letter or digit in a-z or 0-9 gives `subject`.
- A run with no `run_id` leaves out that part and its `-`.

A run never overwrites an earlier file. When the name is taken and the run has no `run_id`, add `-2` before `.json`, then `-3`, and so on. When the name is taken and the run has a `run_id`, stop: two runs never share a `run_id`.

The checker builds the name with `result_file_name()` and checks it with rule R-NAME.

## The shape

Top level:

- `schema`: the string `"plugin-result/1"`.
- `plugin`, `plugin_version` and `command`. `command` is the canonical `plugin:command` name the session lists, for example `jtbd-market-discovery:discover`. Every table and example in this standard uses that one spelling.
- `run`: `started_at` and `finished_at` (UTC, ISO 8601, ending in `Z`), `mode` (`interactive` or `automated`), `subject` (what was analysed, in plain words), and three optional keys: `case` (R7), `run_id` (R5) and `answers` (the answers file the run used, R5).
- `results`: a list. Each result has:
  - `id`: unique in the file.
  - `kind`: one name from the kind list.
  - `label`: plain words, for example "Willingness to pay, mid-market controllers".
  - `value`: a number, a string or an object, in the shape its kind sets. `unit` and `period` are present where the kind needs them.
  - `sources`: a list of `{type, ref, date}`. Every result has at least one source. `type` is one of:
    - `customer_data`: interviews, surveys, usage, sales records. A file the person hands over, such as a CRM export, is this type, and `ref` is the file.
    - `published`: a third-party page or report.
    - `person`: something the person said in this run, with no record behind it.
    - `model`: the model's own knowledge or inference.
    - `default`: a built-in constant or setting that nobody confirmed.

    `ref` is a URL, a file path or a plain description. `date` is when the source is from (`YYYY`, `YYYY-MM` or `YYYY-MM-DD`), or `null`.
  - `method`: how the value was found, in one or two sentences.
  - `rests_on_default` and `defaults`. `defaults` names each unconfirmed default the value used, for example `"discount_rate = 0.15"`. `rests_on_default` is true when a source has type `default`. It is also true when the `defaults` list of marker strings is not empty; otherwise it is false.
  - `confidence`: optional. The plugin's own label, kept as written.
  - `detail`: optional. The path to the plugin's fuller file for this result.
  - `cites`: optional. The results this result rests on, each as `{file, result_id}`.
- `gaps`: a list of what the run could not produce, each with `kind`, `label` and `why`. For example: a framework that failed and was skipped.

No other key is allowed, at any level.

A complete example:

```json result
{
  "schema": "plugin-result/1",
  "plugin": "pricing",
  "plugin_version": "1.10.4",
  "command": "pricing:price",
  "run": {
    "started_at": "2026-10-31T10:00:00Z",
    "finished_at": "2026-10-31T10:15:00Z",
    "mode": "automated",
    "subject": "Mid-market controllers",
    "case": "business-cases/acme",
    "run_id": "acme-0007",
    "answers": "/abs/business-cases/acme/team/answers-002.json"
  },
  "results": [
    {
      "id": "price-1",
      "kind": "launch_price",
      "label": "Launch price, mid-market controllers",
      "value": {"price": 49.0, "pricing_unit": "per seat per month", "path": "A"},
      "unit": "USD",
      "period": "month",
      "sources": [
        {"type": "customer_data", "ref": "interviews.csv", "date": "2026-09-14"},
        {"type": "person", "ref": "answers:target_margin", "date": null}
      ],
      "method": "Path A: the price sits inside the willingness-to-pay range from the jtbd run, at the margin the person gave.",
      "rests_on_default": false,
      "defaults": [],
      "confidence": "medium",
      "detail": ".pricing/acme-0007/price.md",
      "cites": [
        {"file": ".jtbd-market-discovery/results/20261031T091500Z-wtp-check-mid-market-controllers-acme-0006.json", "result_id": "wtp-1"}
      ]
    },
    {
      "id": "motion-1",
      "kind": "growth_motion",
      "label": "Growth motion",
      "value": "product-led",
      "sources": [
        {"type": "model", "ref": "inference from the package list", "date": null},
        {"type": "default", "ref": "config/defaults.json", "date": null}
      ],
      "method": "Chose the motion that fits a self-serve entry package.",
      "rests_on_default": true,
      "defaults": ["entry_package = self_serve"]
    }
  ],
  "gaps": [
    {"kind": "competitor", "label": "Competitor prices", "why": "The search returned no pricing pages."}
  ]
}
```

## The kind list

`kinds.json` holds the kinds, version 1.1.0. Each entry has a `definition`, a `value` shape, and whether `unit` and `period` are `required`, `optional` or `none`. A new kind is a change to that file and to this standard's version.

## Rules every producing plugin follows

**R1.** Write the file at the end of every run, interactive or automated, success or partial. A run that produced nothing still writes the file, with its `gaps`.

**R2.** Mark every default. Each plugin keeps a registry of the inputs that can take a default in its adopting commands. The registry is derived by a search of those commands' agent texts (for `or <value>`, "default", "fallback", "estimate" and "skip"), not typed from memory. Each entry has a doc test that the writer marks it, a rot test that its text still exists, and a check that the registry is not empty. The search is a review aid; see "The default search".

**R3.** Never put a default in `sources` as anything but `type: default`.

**R4.** The file passes this standard's checker, in each plugin's tests. The tests load the checker by path from `docs/plugin-result/schemas/`. They import nothing from business-case and need nothing beyond what CI installs (`pytest pyyaml` and each plugin's requirements files). Only the checker holds the rules the schema cannot state, so `jsonschema` alone is not enough.

**R5.** Accept answers and run for the coach. The coach runs an adopting command from the main session: with the `Agent` tool when the route is an agent, and with the `Skill` tool when the route is a skill. The prompt (or the arguments of the skill) carries the invocation block (see "The invocation contract").

- The route of each adopting command is the agent or the skill that the coach starts with the block (see "Adopting commands").
- The answers file is keyed by the canonical command name. Each plugin reads only its own section.
- A value the answers file gives is used in place of the plugin's default. A value marked `settled_by: person` gets a source of type `person`. A value marked `settled_by: recommended` is recorded as a default: a source of type `default`, and `rests_on_default: true`. A value neither the answers file nor the run supplies stays a default and is marked as one (R2).
- A value taken from the answers file is the source `{"type": "person", "ref": "answers:<input>", "date": null}` for `settled_by: person`, and `{"type": "default", "ref": "answers:<input>", "date": null}` for `settled_by: recommended`.
- Each adopting command publishes the questions it would ask in an interactive run (see "The questions list").
- The person's answers set plugin inputs and are `person` sources. A result is more than an estimate only when its sources also include `customer_data` or `published`. This is the intended honesty, not a defect.

**R6.** Scope. R1 to R5 apply to the adopting commands this standard lists. A plugin's other commands stay as they are, and may adopt the file later.

**R7.** Tie a result to a case. `run.case` is the `case` of the invocation block, when there is one. When it is absent, business-case uses the result only after a case card.

The checker adds these rules to the schema. Each error message starts with the rule id.

| Id | Rule | Checked by |
|---|---|---|
| R-DEFAULT | `rests_on_default` is true when a source has type `default`. It is also true when the `defaults` list of marker strings is not empty; otherwise it is false. | `check_result` |
| R-IDS | The `id` of each result is unique in the file. | `check_result` |
| R-KIND | The `kind` of each result and each gap is in `kinds.json`. | `check_result` |
| R-VALUE | `value`, `unit` and `period` match the kind's entry. | `check_result` |
| R-EMPTY | A file with no results lists at least one gap. | `check_result` |
| R-TIME | `finished_at` is not before `started_at`. | `check_result` |
| R-NAME | The file name is the one `result_file_name()` builds from the file's fields. | `check_result_file` |
| R-INPUTS | The `input` of each question is unique in the questions list. | `check_questions` |
| R-OPTIONS | A `choice` question lists its `options`. | `check_questions` |

In a schema pattern, `$` is allowed only as the last character, where it means the end of the string. The checker refuses a schema that uses `$` anywhere else.

## The invocation contract

The coach dispatches the route with a prompt that holds one fenced block with the info string `plugin-run`. The block is one JSON object:

```plugin-run
{"command": "pricing:price", "automated": true,
 "answers_path": "/abs/business-cases/acme/team/answers-002.json",
 "case": "business-cases/acme", "run_id": "acme-0007",
 "inputs_from": [{"plugin": "jtbd-market-discovery", "run_id": "acme-0006",
                  "result_file": ".jtbd-market-discovery/results/20261031T101500Z-wtp-check-acme-controllers-acme-0006.json"}]}
```

- All six keys are present. No other key is allowed.
- `command` is the canonical name of an adopting command. `check_invocation(block, commands)` checks the name against `commands` when it is given. `tests/plugin_result_conformance.py` `check_invocation(block)` gives it this standard's list.
- `automated` is `true`. The invocation block wins over any config file's automation setting.
- `run_id` matches `^[a-z0-9][a-z0-9-]{2,62}[a-z0-9]$`. Code assigns it. The plugin puts it in `run.run_id` and in the file name.
- `inputs_from` lists each earlier run this run builds on, as `{plugin, run_id, result_file}`. It may be `[]`. A run reads an earlier run's files only through this list.

`check_invocation()` checks a block, and `parse_invocation_block()` reads the first `plugin-run` fence of a text.

## The route rule

The standard records one route for each adopting command (see "Adopting commands"). Where the plugin's own agent did not run the command's instructions, the route is a thin runner, `agents/<command part>-runner.md`. A runner reads the command file and follows its body.

- A route cannot ask the person: Claude Code removes `AskUserQuestion` from every subagent. Its frontmatter `tools:` line does not name `AskUserQuestion`. The first `## ` heading of the route is `## Plugin-run block`, so no block about the mode of the run comes before it.
- A route under `skills/` has no `tools:` line. It cannot ask when the first `## ` heading of its `SKILL.md` is `## Plugin-run block` and that section holds the sentence `Ask the person nothing.` The checker then applies the checks of a route that cannot ask, and reads no `tools:` line. The section names the 2 input forms: the arguments of the skill hold a fenced block with the info string `plugin-run`, or they are 1 line that is the path of a file that holds the block.
- The `## Plugin-run block` section names each of these in backticks, as a whole span: the command (`` `pricing:price` ``), `` `answers_path` ``, `` `case` ``, `` `inputs_from` ``, `` `run_id` ``, `` `settled_by` `` and the folder (`` `.pricing/results/` ``). When another agent writes the result file, the section names that agent's path in backticks (`` `agents/new-offering-pricer.md` ``). The section also holds the precedence rule: "the invocation block wins over any config file's automation setting".
- `${CLAUDE_PLUGIN_ROOT}` is substituted in an agent's own text, and it is never a shell variable: never write it as `$CLAUDE_PLUGIN_ROOT`, and never rely on it being set in the shell. A file loaded with Read keeps the token, and the route maps it to the plugin's root.

The block, as a route holds it:

```markdown
## Plugin-run block

When the dispatch context holds a fenced block with the info string `plugin-run`, this run is a plugin run of `pricing:price`. The block holds `command`, `automated`, `answers_path`, `case`, `run_id` and `inputs_from`.

- Read the answers file at `answers_path` and use its `pricing:price` section. A value it gives replaces the default for that input. Each answer has `settled_by`. A value with `settled_by: person` is a source of type `person`; a value with `settled_by: recommended` is a source of type `default`.
- `automated: true` in the invocation block wins over any config file's automation setting. Ask the person nothing.
- Read an earlier run's files only through `inputs_from`. Put `case` in `run.case` and `run_id` in `run.run_id` and in the file name.
- End the run with the result file written to `.pricing/results/` by `agents/new-offering-pricer.md`.
```

## Running code and permissions

Every file a person's run follows carries this sentence, word for word: the adopting command body, each agent the body follows, and the `## Result file` section of each writer the body follows.

> Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command.

- Every adopting command body also says: Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
- A figure that no script computed is worked out from the formula the command states, with no code at all, and its `method` says so.
- Every writer runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py` for the result file name and uses its output as printed. Every producer ships the same `scripts/result_name.py`.
- Every adopting command's `allowed-tools`, and every reader body's that runs a script, holds the grant line `Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)`. The grant covers a call written without quotes, as the prompt text writes it. It does not cover `python3 -c` or any other inline code, which still needs approval.
- What a permission does (measured on Claude Code 2.1.316): A command's or skill's `allowed-tools` grants a matching call with no prompt. It restricts nothing: a call it does not name falls to the person's session rules. The grant also reaches a subagent that the command's run dispatches. The grant holds only in the turn that ran the command: when a background agent's notice starts a new turn, the same call needs approval. A subagent's own `tools:` Bash pattern neither grants nor restricts. The person's own session rules govern.
- An agent's `tools:` line names the shell it may run, such as `Bash(uv run *)`, never `Bash(*)` or a bare `Bash`. It states intent; it is not a control.

`docs/adr/ADR-003-plugin-result-file.md` records why.

## The questions list

Each adopting command publishes the questions it would ask in an interactive run, at `questions/<command part>.json` in the plugin's folder. `gtm:marketing:launch` gives `questions/marketing-launch.json`. The file passes `check_questions()`.

- `input` is a snake_case name. It is unique in the file (R-INPUTS).
- `question` is one sentence.
- `type` is `choice`, `number`, `text`, `path` or `boolean`. A `choice` question lists its `options` (R-OPTIONS).
- `default` is the value the plugin uses when nobody answers. `unit` is optional.

A person can skip a question. Design every question for no answer.

```json questions
{
  "schema": "plugin-questions/1",
  "command": "pricing:price",
  "questions": [
    {"input": "target_margin", "question": "What gross margin should the price keep?", "type": "number", "default": 0.7, "unit": "share of price"},
    {"input": "pricing_model", "question": "Which pricing model fits the offering?", "type": "choice",
     "options": [{"value": "per_seat", "label": "Per seat"}, {"value": "usage", "label": "By usage"}],
     "default": "per_seat"}
  ]
}
```

## The answers file

The coach writes one answers file and passes its path as `answers_path`. Each key is a canonical command name. Each value maps an input name from that command's questions list to `{value, settled_by, round}`. `settled_by` is `person` or `recommended`. `round` is optional, an integer of 1 or more. The file passes `check_answers()`.

```json answers
{
  "pricing:price": {
    "target_margin": {"value": 0.7, "settled_by": "person", "round": 1},
    "pricing_model": {"value": "per_seat", "settled_by": "recommended"}
  },
  "jtbd-market-discovery:discover": {
    "market_area": {"value": "invoice automation for mid-size finance teams", "settled_by": "person"}
  }
}
```

## Adopting commands

R1 to R7 apply to these 2 commands and to no other. `route` is relative to the plugin folder. `runner` is `yes` when the route is a thin runner. `depth` is the deepest agent layer the route uses, route agent included.

<!-- adopting-commands:start -->
| command | route | runner | depth |
|---|---|---|---|
| `jtbd-market-discovery:discover` | `skills/discover/SKILL.md` | no | 1 |
| `jtbd-market-discovery:wtp-check` | `skills/wtp-check/SKILL.md` | no | 1 |
<!-- adopting-commands:end -->

## The adoption manifest

Each producer has `plugins/<plugin>/result-file.json`. It names the writer of each adopting command, the defaults registry, the config leaves ruled not to be defaults, and any extra files to scan. `tests/plugin_result_conformance.py` checks it with `check_manifest()`.

```json adoption
{"schema": "plugin-result-adoption/1", "plugin": "product-finance",
 "commands": {"product-finance:feature-roi": {"writer": "agents/roi-calculator.md"}},
 "defaults": [{"command": ["product-finance:feature-roi"], "input": "discount_rate",
               "marker": "discount_rate = 0.15", "file": "agents/roi-calculator.md",
               "anchor": "discount_rate = user_selection or 0.15"}],
 "not_defaults": [{"file": "templates/auto-config.template.json", "anchor": "<dotted key path>", "why": "a label, not an input"}],
 "scan_also": [{"file": "commands/setup.md", "why": "writes the assumptions the adopting commands read"}]}
```

- A `defaults` entry's `command` is always a list of one or more canonical names. `marker` is the text the writer puts in a result's `defaults` list. `anchor` is the text in `file` that holds the default.
- `not_defaults` holds JSON leaves only. `why` says why the leaf is not a default.
- `scan_also` names a file outside the derived scan set that the commands depend on, with `why`.
- `"no_ask_sites": "<why>"` is set when the plugin's routes ask nothing.
- The writer of each command has a `## Result file` section. That section names `` `.<plugin>/results/` ``, `` `run_id` ``, `` `rests_on_default` `` and `` `gaps` `` in backticks, and says the run "never overwrites" an earlier file. Each of its `json` fences is a result example that passes `check_result()`.

### The scan set

The scan set of a command is derived, never typed:

1. Its command or skill file, and its route.
2. Then, until nothing new is added: every `agents/<name>.md` of the same plugin whose stem is named in a file already in the set; and every skill folder a file in the set names, by `<plugin>:<name>` (when `skills/<name>/` exists), by a `skills/<name>/...` path, or by "Run `<name>` Skill". A reached skill folder adds every `.md` file in it. When the command file is a `SKILL.md`, its own folder is reached.
3. Every file under the plugin's `config/`, and each `scan_also` file.

### The default search

The default search is a review aid, not a test. It runs these patterns, without regard to case, on each line of a scan set that is not JSON: `\bor\s+(["'`][^"'`]+["'`]|-?\d[\d.,%]*|None|null)`, `\bdefault`, `\bfall ?back`, `\bestimat` and `\bskip`.

```bash
uv run python3 tests/plugin_result_conformance.py hits <plugin>
```

prints every hit for each adopting command. The adopting task lists every hit with a ruling: a registered default, or not a default with the reason. The task's reviewer checks the rulings. A default worded so the search misses it is caught by review, not by a test.

The tests hold each registry entry to these facts: its anchor is in its file; its anchor is on exactly one line of that file; its marker is in the `defaults` list of a writer example and of a written result fixture of each of its commands; and the registry is not empty.

### Config leaves

This check is total. Every leaf of every JSON file under `config/` and of every JSON `scan_also` file is covered by exactly one `defaults` or `not_defaults` entry. The entry has that `file`, and its `anchor` is the leaf's dotted key path, for example `formulas.path_b.target_margin`. A leaf is a scalar, an array or an empty object.

### Ask sites

The ask files of a command are its command file, its route (an agent file or a skill file), the skill files it reaches, and the agents it reaches by a dispatch line. A dispatch line names the agent together with "dispatch" (any case), `Task(`, `subagent_type` or `Agent`.

- Each line of an ask file that names `AskUserQuestion` carries an id on the same line. Frontmatter is left out. The words around the token do not matter.
- An ask site carries `[q: <input>]`. `<input>` is a question of an adopting command whose scan set holds the file. Only the first id on a line counts, so ask one question per line.
- A line that names the tool and asks nothing carries `[q: none]`, for example "Do not call AskUserQuestion in automated mode [q: none]."
- Each question is named by an ask id or by a `defaults` entry of that command.
- Control: the plugin has at least one ask site. A manifest with `no_ask_sites` has none.

### Written result fixtures

Each producer keeps real result files from harness runs in `plugins/<plugin>/tests/fixtures/plugin-result/`:

- `<command part>-defaults.json`, from a run whose answers file answers no input. Where a command's defaults split by branch, keep one `<command part>-defaults-<branch>.json` for each branch. Together they list the marker of every registered default of the command.
- `<command part>-answered.json`, from a run whose answers file gives one registered input with `settled_by: person`. It sets `run.answers`, has the source `{"type": "person", "ref": "answers:<input>"}`, and lists that input's marker in no `defaults` list.

### The checks

A producer's contract test calls each check with `CONF.adopting_commands("<plugin>")` and expects an empty list.

| Check | What it holds |
|---|---|
| `check_route` | The route exists, does not ask the person, and holds the Plugin-run block as "The route rule" says. |
| `check_questions_file` | The questions list exists, passes `check_questions()`, names the command, and each question is asked or defaulted. |
| `check_asks` | Each ask site has an id that names a question. The control holds. |
| `check_writer` | The writer's `## Result file` section and its examples. Each served command has an example, and each registered default's marker is shown. |
| `check_answer_example` | For each command with a registered default, one example shows an answer in place of that default. |
| `check_written` | The written result fixtures. |
| `check_defaults` | The manifest's shape and commands, rot, one line per anchor, the cover of config leaves, and the controls. |

## Folder names

- A new run of jtbd-market-discovery or competitive-intelligence writes only to its new folder, `.jtbd-market-discovery/` or `.competitive-intelligence/`. Old folders (`.jtbd/`, `.competitive-intel/`) are never moved, renamed or deleted.
- Every reader of an old path reads the new folder first. It falls back to the old folder only when the new one has no match. This holds for jtbd-market-discovery, and for every other reader a search finds: pricing and product-finance.
- competitive-intelligence reads both folders, newest file first, so its history in `.competitive-intel/` stays in view.
- A test finds the readers by search and fails when a reader names an old path without the new one before it. A control checks that the list of readers is not empty.

## The checker

```bash
python3 docs/plugin-result/schemas/plugin_result_check.py result <result file>
python3 docs/plugin-result/schemas/plugin_result_check.py questions <questions file>
python3 docs/plugin-result/schemas/plugin_result_check.py answers <answers file>
python3 docs/plugin-result/schemas/plugin_result_check.py invocation <text file holding the block>
```

Exit 0 when the file is valid. Exit 1 when it is not, with one error per line on stderr. Exit 2 on bad use. `result` runs `check_result()` and `check_result_file()`.

A test loads the checker and the helper by path, with `importlib.util.spec_from_file_location` and a module name unique to the test file. It never runs `import scripts`.
