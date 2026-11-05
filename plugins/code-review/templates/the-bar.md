<!-- code-review generator template — the contract archetype. /code-review:setup (bootstrapping) fills the <PLACEHOLDER> spans from mined repo evidence and writes the result to .claude/code-review/contract.md. Not an active contract itself. -->

# PR review contract

The single source of truth for PR review in this repo. People can edit it. The executor skills
(`reviewing-prs` and the lifecycle skills) and every generated `reviewing-<concern>` lens read
this file. Four sections: **the Bar**, **Deterministic gates**, **Repo invariants**, and the
**Lens registry**.

---

## 1. The Bar — what a finding must clear, and which findings hold up approval

A finding is reportable only if it clears **both** tests:

1. **Real** — concretely true in *this* diff, with evidence. A guess, a "could be cleaner" remark, or a risk
   that needs a future change does not pass.

2. **Impactful if left unattended** — it causes one or more of:
   - broken or incorrect behavior that ships,
   - a security, data-exposure, or compliance breach,
   - a violated **repo invariant** from section 3, `[blocking]` or `[advisory]` (section 3 sets
     the highest label each marker can get),
   - a **costly-to-reverse** decision put into a layer that is hard to change,
   - a **broken contract** with existing consumers (API/schema/SDK surface),
   - a deterministic check defeated by a lie (e.g. mis-labeling a change to dodge a gate).

   <!-- The bullets above are generic. bootstrapping replaces the last four with this
        repo's real impact categories, mined from review history and docs. Example rows from a
        healthcare monorepo (drop or replace for your repo):
          - PHI / compliance exposure in any environment,
          - gateway-only-persistence invariant violated,
          - GraphQL breaking change to a published contract. -->

**Hard exclusion — drop what a deterministic gate already owns, because the gate already reports
it.** Section 2 lists the exact gate commands. Drop a style, formatting, or naming
preference that no repo invariant binds.

**The first decision is binary: report or drop.** The labels below sort only the findings you
report. "PR looks ok as is" is a valid result, and no reviewer has to find something.

**The default answer is silence.** Drop a finding when you cannot name the damage it causes. Drop
a preference. Drop what the author sees without you. Five small remarks hide the one remark that
matters.

### Three labels: must-fix, should-fix, note

Give each reported finding one label: must-fix, should-fix, or note. The label decides only
whether the finding holds up approval, and only must-fix holds it up.

#### The must-fix test

Write must-fix only when all four parts below are true.

1. **Name the wrong result.** Complete this sentence from the diff: "After this merge, <who or
   what> gets <the wrong result> at <file>:<symbol>." Fill every blank.
2. **Name a trigger that exists today.** Name a caller, a command, a user step, or a released
   artifact that reaches the defect now. A trigger that needs code nobody has written does not
   count.
3. **Name the line in this diff.** The line that causes the failure must sit inside this diff.
   Evidence outside the diff does not count.
4. **Match one of the six damage classes below.**

If any part fails, write should-fix or note. The size of the fix and your opinion of the code are
not parts of this test.

#### The six damage classes (closed list)

1. The software gives a wrong result, or it stops.
2. Private data escapes, or a security control breaks.
3. Data is destroyed, or made unrecoverable.
4. A published interface breaks for a caller you can name.
5. A check stops running, or a check passes when it must fail.
6. An invariant marked `[blocking]` in section 3 breaks.

The list is closed. Do not add a class, do not remove one, and do not reword one, because every
review in every repo must apply the same six.

#### Do not block on these

None of these reach must-fix on their own:

- Wording, tone, grammar, and voice.
- A missing test for code that already works.
- Naming, layout, duplication, and dead code.
- An input that no current caller sends.
- A risk that needs a future change to become real.
- Prose that no agent and no user follows to a wrong action.

Most pull requests get zero must-fix. When a report has more than two must-fix entries, read them
again.

#### Should-fix

The finding is real and names a defect, but it fails at least one part of the must-fix test.
Typical cases:

- The failure needs a caller that does not exist yet.
- The damage is latent.
- The evidence sits outside the diff.
- The failure is real, but it is not one of the six damage classes.

The author decides whether to fix it in this pull request.

#### Note

The finding is real. It clears the two report-or-drop tests above. It names no defect. Typical
cases:

- An invariant marked `[advisory]` is broken.
- The prose is unclear, but no agent or user acts wrongly on it.
- A test is missing for code that already works.

**The note cap.** Write a should-fix or a note in two sentences, maximum: one for what is wrong,
one for why it matters. Add no third sentence, no example block, and no patch. If a finding needs
more space, decide whether it is a must-fix, a should-fix, or not worth a report. Then write it in
that form, or drop it.

**Dropped stays dropped.** A label sorts what you report. It never turns a dropped remark into a
report, because a lower label is not a place for a remark that failed the report-or-drop tests.

#### When you are not sure, use the lower label

Order: must-fix, then should-fix, then note. When you are not sure which label fits, use the lower
one, because an approval that a human must chase costs more than a note that a human ignores.
"Not sure" means you cannot complete the four-part test. It does not mean you completed it and
think the fix is small.

### Voice — ASD-STE100

Write every finding, digest, and receipt in ASD-STE100 Simplified Technical English:

- Write one idea in one sentence. Use a maximum of 20 words.
- Use the active voice and the present tense.
- Use one word for one meaning, because a reader takes a new word for a new thing.
- Use plain words, because a reader takes an idiom, a metaphor, humor, or jargon literally.
- Name the file, the symbol, and the damage. Write no hedge word such as "might" or "possibly",
  because a hedged claim gives the author nothing to act on.

This applies to all review text, local and posted. Paths, identifiers, commands, and quoted
source keep their exact spelling.

---

## 2. Deterministic gates (never re-flag)

The repo's own mechanical checks. A lens does not report what one of these gates owns, because
the gate already reports it. `reviewing-prs` uses this list as its hard-exclusion set. The
lifecycle skills (`getting-prs-approved`, `getting-prs-merged`) run these commands as the
CI-equivalent gate before they call a PR green.

<!-- bootstrapping records the exact commands found at setup time, one per line, each
     with a scope note. At review time the executor uses the scope note to decide whether a
     finding is gate-owned, because a command string does not show what it covers. -->

- `<GATE_COMMAND_1>` — <what it owns>   <!-- e.g. `npm run lint` — formatting, style, unused vars, import order -->
- `<GATE_COMMAND_2>` — <what it owns>   <!-- e.g. `npm run typecheck` — type errors, incompatible signatures -->
- `<GATE_COMMAND_3>` — <what it owns>   <!-- e.g. `npm test` — failing/missing assertions in existing suites -->
- `<GATE_COMMAND_N>` — <what it owns>   <!-- e.g. secret-scan — committed credentials; schema-validate — schema syntax -->

---

## 3. Repo invariants

The mined, repo-specific rules that must always hold. The lenses turn them into `flag:` lines.
Write each one so that a reader can point to the diff line that breaks it.

Each invariant bullet starts with `[blocking]` or `[advisory]`. A `[blocking]` invariant is
damage class 6 in section 1: a diff that breaks it can be a must-fix. An `[advisory]` invariant
can reach should-fix at most. An invariant with no marker reads as `[advisory]`.

<!-- bootstrapping fills these from CLAUDE.md, CONTRIBUTING.md, ADRs, and recurring
     review objections. One short rule per bullet, with a pointer to the authoritative doc.
     Write the `[blocking]` or `[advisory]` marker first on every bullet — see Step 4 of
     bootstrapping/SKILL.md. -->

- `[blocking]` `<INVARIANT_1>`   <!-- e.g. "All persistence goes through the gateway; no browser-direct data access." -->
- `[blocking]` `<INVARIANT_2>`   <!-- e.g. "No PHI in any environment, including dev." -->
- `[advisory]` `<INVARIANT_N>`   <!-- e.g. "Use canonical component names everywhere; never invent an alias." -->

---

## 4. Lens registry

The authoritative list of this repo's active lenses. `reviewing-prs` reads this table to decide
which lenses to run on a diff. Two built-in lenses, `code-review` (Claude Code's `/code-review`
skill) and `code-review:reviewing-goal-achievement`, run on every review. They need no row, and
`reviewing-prs` selects them whether this table lists them or not. Each row:

| name | when | skill path |
|------|------|------------|

- **name** — the lens identifier. It must equal `basename(skill path)` and the Skill-tool
  invocation token, i.e. `reviewing-<concern>`.
- **when** — a comma-separated list. An entry is a **file glob** if it contains `*`, `/`, or a
  file extension, and it matches against the diff's changed paths. Any other entry is a
  **change-type keyword** (e.g. `touches-data-model`, `renames-component`, `adds-endpoint`).
  `reviewing-prs` selects by path match for a glob. It always considers a change-type keyword,
  because paths alone do not show a change type, and the lens filters itself against its own
  list. So a glob miss does not drop a concern-driven lens (PHI, naming).
- **skill path** — `.claude/skills/reviewing-<concern>` (a bare-name repo skill in the target
  repo, human-editable, discovered by Claude Code).

<!-- bootstrapping writes one row per confirmed concern. Example rows (replace with
     this repo's concerns; note name == basename(skill path)): -->

| name | when | skill path |
|------|------|------------|
| reviewing-naming   | `touches-data-model`, `renames-component`   | `.claude/skills/reviewing-naming` |
| reviewing-security | `auth/**`, `gateway/**`                      | `.claude/skills/reviewing-security` |
| reviewing-graphql-contract | `**/*.graphql`, `**/schema.ts`      | `.claude/skills/reviewing-graphql-contract` |
