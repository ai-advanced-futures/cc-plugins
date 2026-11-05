# Changelog

## 1.1.1

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `prompt@cc-plugins`. The homepage and the repository fields point at the public repository. Install the plugins again from the new marketplace.

## 1.1.0

### Changed
- The skills have new names that do not repeat the plugin name. `prompt:reviewing-prompts` is now `prompt:reviewing`, `prompt:revising-prompts` is now `prompt:revising`, and `prompt:writing-prompts` is now `prompt:writing`. The commands `/prompt:review`, `/prompt:revise`, and `/prompt:new` keep their names.
- The three skills hold fewer instructions: 31 before, 20 after. `/prompt:revise` measured the change.
- The skills do not tell the model to announce itself. Claude Code already shows the skill name.
- `writing` leaves the markup-scheme rule (P6) and the reason-beside-a-prohibition rule (P7) to the lint run, which checks both. The `/prompt:revise` help names the `--dry-run` row.

### Fixed
- `revising` saves the before-copies in a new `mktemp -d` folder, at the same relative path. The old fixed `/tmp` path lost copies, because every skill file has the same file name.
- `revising` compares each before-copy with the real revision: the file itself, or the new "revised" file beside it. It runs the compare script one time for each changed file, and it reports "no measurable change" for each file that did not move. It says what the report holds when the compare script cannot read a file.
- `revising` names the rules that have no check, such as L2 and P1, as part of the work list, and it says where a `--dry-run` revision goes: to no file.
- The lint script does not count a hyphenated label such as "must-fix" or "should-fix" as an instruction or as a bare prohibition. Before, each label made its sentence an instruction, so the counts were too high. A modal after a dash still counts, and a label before a colon, such as "Must-fix: run the tests", still opens an instruction.

## 1.0.1

### Changed
- The display name is now lowercase: `prompt`.

## 1.0.0

- Moved to ai-advanced-futures/cc-plugins-library. Renamed from `prompt-fit` to
  `prompt`: the commands are now `/prompt:...`.

## 0.1.1

- The skill, command, and manifest descriptions name the principles in
  `reference/principles.md`, not a month. The reference file keeps its date.

## 0.1.0

First release.

- `/prompt-fit:review` measures a file, a skill, a command, an agent, a plugin,
  or a whole project against the August 2026 prompt engineering principles, and
  reports findings that cite a rule identifier. It edits nothing.
- `/prompt-fit:revise` applies the findings in the order delete, rewrite, move,
  and proves that the instruction count or the finding count went down.
- `/prompt-fit:new` drafts a prompt in the 2026 shape: few outcome-shaped
  instructions, reference material held apart, hard rules left to code.
- `scripts/prompt_lint.py` counts instructions and reference lines separately,
  and raises ten checks. It reports the all-rules estimate over three bands,
  from the 0.98 per-rule figure that `--per-rule` can change.
- `scripts/compare_prompts.py` exits 1 when a revision moved no count down, so
  a revision loop cannot report success on a rewrite that measures the same.
- `scripts/resolve_target.py` prints the scope of a review, with each file's
  role and git state. It ends the run on a target that holds no prompt file, or
  that holds more than 100, rather than reviewing a part of it in silence.
- `reference/principles.md` holds all 19 rules, each with its check or a note
  that it is judgement only, its confidence label, and a broken-and-fixed pair.
  A finding cites one of them, so a reader can find what it means.
