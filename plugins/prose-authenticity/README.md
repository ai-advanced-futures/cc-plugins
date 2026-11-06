# prose-authenticity

Find the signs that a machine wrote a text. Rewrite the text so that it reads
as human writing. The plugin has tiered detectors, voice profiles, and a
humanize loop with a fact check.

## Install

```
claude plugin install prose-authenticity@cc-plugins
```

The plugin needs `uv`. Each script of the plugin starts with `uv run`, and
`uv` installs the Python packages that the script needs.

## Commands

| Command | Purpose |
|---|---|
| `/prose-authenticity:check` | Score a text. Give a PASS, WARN, or FAIL report. |
| `/prose-authenticity:humanize` | Rewrite a text in a loop until it passes, or stop at a set limit. |
| `/prose-authenticity:profile` | Build a voice profile from 3 or more writing samples. |
| `/prose-authenticity:setup` | Turn on the detector tiers. Record the consent for the API tier. |

Use `check` for a request to score, check, or detect. Use `humanize` for a
request to transform a text, or to make it pass a detector. Use `profile` to
capture the voice of an author. Use `setup` to turn on a tier.

## Skills

| Skill | Purpose |
|---|---|
| `anti-ai-tells` | Write clean text the first time. It lists the signs that a machine wrote a text. |
| `prose-correctness` | Draft with no spelling fault, doubled word, or wrong article. |
| `simplified-technical-english` | Write in ASD-STE100 Simplified Technical English. |

## Inputs

- A markdown file, a text file, or pasted text.
- A source code file. The plugin reads only the comments and the docstrings.
- An optional voice profile. Without one, the plugin uses a neutral profile.
- Optional zone markers (see "Zone markers").

## Outputs

Each run writes into `.prose-authenticity/run-<UTC-timestamp>/` in the current
folder:

- a copy of the input,
- the zones, the scores, and each rewrite and candidate,
- the report,
- `prose-authenticity-handoff.json`, which holds the verdict, the path of the
  output, the path of the report, and the list of degradations.

The plugin never changes the input file, unless you give `--in-place`.

Voice profiles are in `.prose-authenticity/profiles/<name>.yaml`. The consent
for the API tier is in `.prose-authenticity/config.yaml`. This data belongs to
your project. The plugin does not delete old runs.

## Detector tiers

| Tier | Detectors | Availability |
|---|---|---|
| heuristics | Stylometric composite (burstiness, TTR, tells) | Always on |
| hf | Hello-SimpleAI/chatgpt-detector-roberta, andreas122001/roberta-mixed-detector, openai-community/roberta-base-openai-detector | Optional. Needs `torch` and `transformers`. |
| api | GPTZero, Originality.ai, Sapling | Optional. Needs keys and a recorded consent. |

Verdicts use composite points from 0 to 100. A lower number reads as more
human. The text passes at 50 or below, and within 10 points above the baseline
of the human zones. The heuristics tier fails above 70. The hf tier and the api
tier fail when 2 or more detectors score above 50. The report always names a
degradation. A degradation is never silent.

### Optional parts

- **hf tier.** Run `/prose-authenticity:setup`. The first run downloads `torch`,
  `transformers`, and 3 models. The scripts start with
  `uv run --with torch --with transformers`.
- **api tier.** Run `/prose-authenticity:setup`. The document text goes to 3
  outside services, so the plugin asks for your consent first. Export the keys
  `GPTZERO_API_KEY`, `ORIGINALITY_API_KEY`, and `SAPLING_API_KEY`. The keys stay
  in the environment, never in a file.
- **Fact check.** The humanize loop uses the `grounded-synthesis` plugin to check
  that a rewrite keeps each fact. Without that plugin, or when it fails, the loop
  runs at most 2 iterations. The report then shows UNVERIFIED FACTS.

## Zone markers

Mark sections with HTML comment markers. The markers tell the plugin which text a
human wrote, and which text it can rewrite:

```
<!-- ai-check:zone start name="intro" author="human" -->
Text that the author wrote and stands behind.
<!-- ai-check:zone end -->
```

The value of `author` is `human`, `ai`, or `mixed`. The plugin never rewrites a
human zone. Each candidate holds the human zones byte for byte. The human zones
also set the detector baseline: the loop must beat the writing of the author, not
an absolute score. The plugin treats `mixed` as `ai`. A document with no marker
is one `ai` zone.

Always show a marker inside a fenced block, as above. The parser reads a marker
in running text as a real marker, because nothing distinguishes an example from
the real thing.

A document with fences that do not pair can hide a real marker. The text is then
open to rewrite. ADR-009 records this and the other accepted limits.

## STE conformance checker

`ste_checker.py` checks a document for ASD-STE100 conformance. It applies 7
rules. It has no command of its own. It runs in two ways: as the script below,
and inside `/prose-authenticity:check`. The check reports its verdict as
`ste_verdict`, beside the tell score. The verdict never joins the detector
composite (ADR-006).

```
uv run ${CLAUDE_PLUGIN_ROOT}/lib/ste_checker.py <file> [--config config/ste.yaml] [--json]
```

In a Claude Code session, `${CLAUDE_PLUGIN_ROOT}` is the folder of the plugin.
The option `--config` is optional. The default path is relative to the script, so
it works from any folder.

| Exit code | Verdict |
|---|---|
| 0 | PASS |
| 1 | WARN |
| 2 | FAIL |
| 3 | Usage or operation error (bad config, file not readable, zone parse failure) |

A bad config is a missing key or a value of the wrong type. An unquoted `yes`,
`no`, `on`, or `off` in a word list is also a bad config. The script stops when
it loads the config, and the message names the key.

The report shows a truncated scan. When a code fence opens and never closes, the
script skips each line from the fence to the end of the file. It then prints a
second line:

```
PASS: 0 findings, 4 sentences, mean 9.0 words, stdev 1.4, 0 exempt zones
WARNING: scan truncated — a code fence opened and never closed, so every line from it to the end of the file was skipped.
```

The verdict and the exit code do not change. Close the fence and run the script
again. The `--json` output holds the same state in `metrics.truncated_scan`.

## Prose correctness checker

`correctness_checker.py` checks a document for spelling faults and mechanical
grammar faults. It applies 3 rules:

- C1 flags a token that is on a curated list of misspellings.
- C2 flags the same word twice in a row on one line.
- C3 flags an article that does not agree with the word after it.

The checker has no command of its own. `/prose-authenticity:check` runs it and
reports its verdict beside the tell score. The two results stay apart, because
`check` measures the chance that a machine wrote the text, and this checker does
not (ADR-010). The correctness verdict never joins the composite.

On a `/prose-authenticity:humanize` run, the report gives the **delta** against
your original. The delta is the list of faults that the rewrite introduced. All 3
rules catch editing faults more than writing faults, so the humanizer prompt names
them (ADR-012). The report lists the faults that your document already had
separately. Neither check gates the loop.

```
uv run ${CLAUDE_PLUGIN_ROOT}/lib/correctness_checker.py <file> [--config config/correctness.yaml] [--json]
```

The exit codes are the same as for the STE checker. The code 1 (WARN) is defined,
but no rule gives it now.

`config/correctness.yaml` holds each threshold, each severity, and each word list
of the project: the misspellings, the table of initialisms, and the words whose
spelling gives a false idea of their sound. Three short lists are in
`lib/correctness_checker.py`, because they are facts about English and not choices
of this project. They name the letters whose names start with a vowel sound, the
conjunctions that can never be the noun after an article, and the ordinary words
that spell an initialism of the table. Edit the config. Do not edit the alphabet.

A bad config is a missing key, a value of the wrong type, a severity that names
no real verdict, or a `severities` map that leaves out a rule. The script stops at
load, and the message names the key.

The check reads the same prose as the STE checker, through `lib/prose_spans.py`.
It skips code fences, inline code, block quotes, YAML frontmatter, and zones with
`author="human"`. It reports a truncated scan on a second line, and in
`metrics.truncated_scan` of the `--json` output.

The limits are mechanical, and the plugin states them. The check does not look a
word up in a dictionary. It catches only the misspellings that someone wrote on
the list. A correct word that is wrong in the sentence, such as `form` for `from`,
passes unless that exact pair is on the list. A general dictionary gave 413
findings and 0 true faults over the prose of the source project. ADR-010 records
that measurement, the release gate of the 3 rules, and the reason why C4, C5, and
C6 do not exist.

C3 has the same kind of limit. English picks the article by sound, and the
checker sees spelling. Three closed lists decide `a` and `an` before the vowel
test runs. An initialism that is not in the lists goes to the vowel test, which
reads only the first letter. The result is wrong when a word does not sound like
its spelling. **The fix for a wrong C3 report is a new row in a list, not a new
rule.** ADR-011 records why a rule that reads capitals as initialisms costs more
than the gap that it closes.

**A PASS does not prove that the checker read the whole document.** An inline
code span that wraps a line break makes `prose_spans` blank the next line and show
its code. That line reaches no rule, so its faults stay hidden, and the document
can score PASS. ADR-011 records the defect and the decision to defer the fix. Do
not use this check as a gate that reads exit code 0 as proof.

The skill `prose-correctness` gives the same discipline for drafting time. It also
states the rule for a new entry in the list.

## Architecture

Agents give judgment only. Each number, each parse, each verdict, and each loop
decision is in a tested script in `lib/`. The agents start the scripts with Bash.
This keeps the context small: the arithmetic goes to Python, and the narrative
goes to the agents.

The humanize flow has these parts:

- The command `humanize` starts the agent `orchestrator`.
- The orchestrator starts `extraction-agent`, `question-adjudicator`,
  `humanizer`, and `detection-analyst` with full names, such as
  `prose-authenticity:humanizer`.
- `loop_controller.py` decides the next action. The orchestrator does not.
- The fact check is a handoff file contract with the `grounded-synthesis` plugin
  (ADR-002).

Read `docs/diagrams/prose-authenticity-context.md` and
`docs/diagrams/prose-authenticity-container.md` for the system views. Read
`docs/INDEX.md` for the 12 decisions.

## Ethics and position

The plugin is for self-checks. It keeps a professional document that a human
directed from being flagged as machine output by mistake. Do not use it to
misrepresent authorship where the rules require AI disclosure, such as in
academic work and regulated filings. The plugin never changes a human zone.

## Tests

```
pip install -r requirements-dev.txt
python3 -m pytest tests/ -q -rs
```

The tests need no model and no network. The live test of the hf tier downloads
models. Run it on your machine with `make itest TIER=hf`.

## Changelog

See `CHANGELOG.md`.
