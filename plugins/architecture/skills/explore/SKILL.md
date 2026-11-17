---
description: Guides architecture discovery from scratch, organization guidance, or an existing application. Reviews evidence, asks one question at a time, records accepted decisions through architecture:learn, and keeps deferred choices separate. Use for "/architecture:explore", "discover the architecture", "help me choose the architecture", or "resume architecture discovery".
argument-hint: "[area | source | changed requirement]"
allowed-tools: Read, AskUserQuestion, WebFetch, Skill(knowledge:ask), Skill(architecture:learn), Skill(architecture:amending-adrs), Skill(architecture:saving-deferred), Bash(find *), Bash(grep *), Bash(git rev-parse *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_migrate.py *)
---

# Explore architecture

Help the person make system-wide choices from evidence. The input is **$ARGUMENTS**.
A product requirements document (PRD), design graph, and assessment are optional.

Explore asks; `architecture:learn` writes accepted architecture decision records (ADRs).
Leave ADR bodies to Learn and deferred knowledge to its helper, because each graph has
one writer. Leave detailed system-design pages and product requirements unchanged.
Call no skill of `system-design`, `architecture-assess`, or `sofa`, because their
interviews are outside this discovery. Use `knowledge:ask` for available registered graphs.

## Review evidence first

Read [the evidence review](resources/evidence.md) at intake. Read the request, available
accepted ADRs, PRD, organization guidance, supplied sources, and an existing assessment.
With application code but no assessment, inspect code with the relevant area checklist.
Name missing or unreadable sources without inventing evidence, then continue discovery.
Ask which additional information sources the person wants considered, unless already
answered. Gather context before each question as described in the evidence review.

Replace `ROOT` in each command with the literal absolute target repository path. Use the
expanded plugin path too, because the permission and read-only hook checks need literal
commands, not shell variables or substitutions. Read `.claude/adr.json` and its configured
rules. Use the configured ADR register to find accepted records for this session's
areas and sources. Find unknown paths with `find` and search with `grep -n -E` through
Bash, using POSIX patterns. Read known paths with Read. Read the map:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root ROOT map
```

`map` returns JSON without a `--json` flag. A failed read gives no usable coverage;
report the cause, not an empty or successful map. If setup is absent, name
`/architecture:setup` and continue the interview without claiming saved coverage.

Keep accepted local ADRs, external ADRs, and choices inferred from documents or code
separate. An accepted local ADR settles its recorded choice. Review each inferred choice
individually before the remaining discovery questions. Review each external ADR
individually unless the person explicitly permits adoption of the named external ADRs
without individual questions. Keep that permission limited to those external ADRs;
inferred choices still need individual confirmation. Record each adopted external source.
Existence is not acceptance.

For a source conflict that no accepted ADR settles, show each source, the conflicting
claims, their effect, and what remains uncertain. Recommend a choice and ask whether to
decide or defer. Leave source priority for the person to confirm, because conflicting
evidence does not authorize a choice. For a conflict with an accepted ADR, use the
return-session change procedure before any replacement.

After initial source review, load [requirements and return-session review](resources/review.md).
Compare available functional PRD requirements with decisions: ask a separate question for
each impossible required behavior and each unsupported requirement in an already decided
area. Leave the PRD unchanged. Without a PRD, say that this comparison cannot run and
continue. Repeat the comparison at discovery end, using the resulting accepted choices.

## Establish direction and ask

Establish current goals, quality goals, and limits with the person. Use the same area
coverage for every experience level, with extra explanations and examples on request.
Start from goals, not an initial experience-level question.

For each unmapped existing ADR, propose one `map_area` and ask for confirmation before
saving it. Preserve its free-text `area` and lifecycle, including an existing proposed
lifecycle. `parent_spec` can inform a suggestion, not set a mapping. For a body-only
legacy ADR, show its state and keep it unmapped until the person approves conversion.
The `/architecture:migrate` route updates lifecycle metadata; use this preview for
body-header conversion instead:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_migrate.py --repo-root ROOT --frontmatter --dry-run
```

Show the preview: it can include multiple legacy records. Only after the person approves
that conversion, run the same command without `--dry-run`, check its result, and retry
the confirmed mapping. Leave conversion out of a map read, because a read must preserve
the records. Save a confirmed mapping through the save code:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root ROOT set ADR_FILE map_area=AREA
```

Replace `ADR_FILE` with the existing record and `AREA` with the confirmed area. If the
active schema rejects the mapping, report `/architecture:setup --refresh` or a custom
schema update. Leave the refused record unchanged, because silently refreshing the schema,
omitting the mapping, or hand-editing around refusal defeats the save guard.

Ask which areas are required for the first build. Show the eight areas from the map:
`quality`, `context`, `strategy`, `building-blocks`, `data`, `contracts`, `conventions`,
and `deployment`. Persist only an explicit selection. Use `--set` with one or more areas,
`--none` for a confirmed empty selection, or `--clear` only to remove a selection at the
person's request:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root ROOT required-areas --set quality data
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root ROOT required-areas --none
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root ROOT required-areas --clear
```

Read [the selected area checklist](resources/areas.md) when recommending or exploring an
area. Recommend the next area from required gaps, goals, and evidence. Let the person
choose another area, defer, stop, or build with areas still open. Ask which building blocks
must change if a choice changes. Keep choices confined to one building block outside this
interview, because this discovery covers system-wide choices.

Ask one question at a time, using [the question card](resources/questions.md).
Give context, two or three options with advantages and disadvantages, and one recommendation.
Include a way to defer. Keep checklist topics reviewed in session context only.
Reading a checklist does not accept a decision.

## Save the person's choices

Use the following routes for each answer:

- Accepted firm choice: invoke `architecture:learn` with one decision sentence and facts
  for Context, Decision, Why, Alternatives considered, and Consequences. Add the optional
  labeled facts `map_area: AREA`, `Parent spec: PATH`, and `Source: PATH_OR_URL` when known.
  Confirm the map area with the choice. Learn writes `lifecycle: accepted`; only its saved
  path and check result count as a save. A failed save remains unsaved.
- Rejected choice: create no ADR.
- Deferred or “not sure” choice: keep the question, context, options, reason it remains
  open, source, and external-ADR identity when present. Create neither an accepted nor a
  proposed ADR. Do not change or remove existing proposed ADRs because of deferral.

To save deferred findings, show the exact group, including deferred external decisions,
and ask for approval. A changed group needs fresh approval. Only after approval, invoke
`architecture:saving-deferred` through `Skill`, not `Agent`. Pass that plain-text group
and state that the person approved this exact group. The helper calls `knowledge:learn`; it must not ask questions or expand the group. Use
its saved paths, unsaved findings with causes, and check notes to update the report.

The knowledge plugin is required to load Architecture. If its graph is absent or unusable,
name `/knowledge:setup` or the reported graph repair and continue discovery. If save support
is absent, name the missing `knowledge:learn` support and its installation or update step,
and continue discovery. List every unsaved finding in the final response. Write no fallback
file. Unsaved choices stay in this session only; a fresh session needs the person to
supply them again.

## Check coverage and finish

Read the map again after each accepted save, confirmed mapping, or amendment that changes
acceptance or coverage. Count only active accepted ADRs with a valid `map_area`. Exclude
deferred knowledge, proposed, deprecated, superseded, and archived ADRs, and generated or
non-ADR pages. `register.exclude` hides register rows, not accepted records from coverage.
Show all eight areas, selected required areas, accepted ADR paths, and remaining gaps.
A covered area can still have open checklist topics. If a failed save left a partial
accepted file, identify that path separately and keep the stopping result unverified
until the failed save is repaired; a partial file is not a verified save.

An absent `required_areas` selection is unset, not empty, and cannot meet the stopping
rule. An explicit empty selection meets only the selected required-area stopping rule.
For a nonempty selection, every required area needs accepted coverage. Other areas can
remain open. State only that the selected required-area stopping rule is met, because
coverage proves neither a complete architecture nor checklist completion. Allow discovery
during building and after the stopping point.

At discovery end, repeat the functional PRD comparison. Ask each conflict or unsupported
requirement as a separate question; if the person stops, list those questions as unresolved.
If no PRD was available, explicitly state that neither PRD comparison ran. Finish with
saved ADR and knowledge paths, coverage, open and unsaved choices, failed saves and check
notes, unresolved product conflicts and gaps, and one recommended next step. Report only
verified saves, not promised records.

## Resume without a restart

On return, load the review resource for affected-decision review. Read accepted coverage
and accessible saved open choices through `knowledge:ask`. If durable open choices are
unavailable, state that limit rather than claiming to remember them. Compare changed
requirements and supplied evidence with existing ADRs. Show only affected accepted ADRs
and why they are affected. Leave unrelated accepted ADRs unchanged and skip their
interview, because unchanged records still settle their choices.

Before replacing an accepted decision, show the record and proposed change and obtain
explicit replacement confirmation. Confirmation of a concern is not replacement approval.
Include the confirmed `map_area: AREA` in the replacement choice.
Then invoke `architecture:amending-adrs` with the confirmed change and mapping fact.
That skill forwards the mapping to Learn. A silent `new` replacement loses the recorded change relationship. New accepted choices still
go through Learn. Refresh the map after
changes. Continue from open choices and missing required coverage, not the first question.
