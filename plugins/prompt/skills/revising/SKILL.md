---
name: revising
description: Applies the prompt engineering principles in its reference file to a prompt, skill, command, agent or plugin, deleting before rewriting, and proves the revision moved the instruction count or the finding count. Backs /prompt:revise.
---

# Revising prompts

Apply `${CLAUDE_PLUGIN_ROOT}/reference/principles.md` to a target, and measure
what the change did.

## The order of work

Apply the fixes in the order of this table. A deletion comes first because
additions degrade quality on current models, so the cheapest fix available in
2026 is a deletion (L2).

| Order | Kind of fix | Targets |
| --- | --- | --- |
| 1 | deletions | personas (L3), politeness and pressure (L4), anti-laziness scaffolding (L5), prescribed reasoning (L7), an instruction that repairs an older model's behaviour (L2) |
| 2 | rewrites | emphasis into plain words (L1), judgment words into numbers (P3), a bare prohibition into a prohibition with its reason (P7), a numbered method into the outcome it was aiming at (P1) |
| 3 | moves | hard content rules into a classifier or a code hook (P8), long reference material below the instructions (P5) or into its own file |

## Before editing

`resolve_target.py` gives the file list and the git state of each file. The
findings of `prompt_lint.py` are the work list, together with the rules that
have no check, such as L2 and P1, which a reader finds in the text. The
`--only <rules>` flag of `/prompt:revise` keeps the work of those rules, and
the script has no such flag:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_target.py" <target> --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/prompt_lint.py" <files>
```

Copy every target file into a new temporary folder before the first edit, at
the same relative path. A shared fixed path is not safe, because every skill
file has the name `SKILL.md` and one copy overwrites the next. A shell variable
does not survive from one tool call to the next, so write the folder path out
in full in each later command.

```bash
mktemp -d
mkdir -p "<folder>/$(dirname <file>)" && cp <file> "<folder>/<file>"
```

The git state decides where the revision is written:

| Git state | Revision goes to |
| --- | --- |
| tracked-clean | the file, in place |
| tracked-dirty, untracked, not-in-git | `<name>.revised.md`, beside the file |
| any state, with `--dry-run` | no file; the report shows the edit |

An in-place edit is safe on a clean tracked file because git can restore the
old file. On
any other state there is no undo, so the revision goes in a new file and the
report names it.

## While editing

Record every deletion as you make it: the text removed, and the behaviour it
was there to protect. A deletion with no record cannot be reversed by a reader
who later finds a regression.

Keep these, and say in the report that you kept them:

- an instruction that names an output contract, such as a format or a length;
- an instruction that a deterministic gate depends on;
- scaffolding on a prompt that runs on a small or unpinned model (U2).

## Proof

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/compare_prompts.py" "<folder>/<file>" <revision>
```

`<revision>` is the file itself on a tracked-clean target, and the
`<name>.revised.md` file on any other git state. The script takes one file on
each side, so a folder target needs one run for each changed file. Give the
all-rules estimate for each file, because a sum of percentages means nothing.

Exit code 1 says the revision moved no count down: the same instructions, and
the same findings. Report that file plainly as "no measurable change", even
when the other files moved. Say what was rewritten instead. A revision loop
that reports success on an unmoved measurement teaches the reader to trust a
number that means nothing.

Exit code 2 says one side could not be read, so there is no proof for that
file. The report then names the path and the error in place of the table.

## The report

Four parts, in this order:

1. The before-and-after table from `compare_prompts.py`.
2. The deletions, one line each: what went, and what it protected.
3. What was kept, and why.
4. A re-test note: the model this prompt is now tuned against, the sentence
   that a model swap is a breaking change (P9), and the evaluation the reader
   should run, because these numbers measure shape and not behaviour.

```
instructions        34 → 11   (-23)
reference lines    120 → 260  (+140)
all-rules estimate 50% → 80%  (+30pp)
findings             9 → 1    (-8)
```
