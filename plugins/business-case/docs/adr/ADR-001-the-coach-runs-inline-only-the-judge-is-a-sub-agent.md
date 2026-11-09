# ADR-001 — The coach runs inline; the sub-agents only read and reply

**Status:** Accepted · **Date:** 2026-10-27 · **Amended:** 2026-10-29 (v0.3.0, the figure extractor); 2026-11-03 (v0.5.0, the analysts and the coach's plugin runs); 2026-11-09 (v0.7.1, the 3 routes of `gtm` are skills)

## Context

The coach asks the user questions all through a run: what a missing item is,
whether a fact is right, which grade an evidence page has. Every funder
decision needs an explicit answer from the person, with the reason in their
own words (spec §4, §6).

Claude Code removes `AskUserQuestion` from every sub-agent, even one that
declares it (Claude Code, "Available tools" of the sub-agent document).
A coach that ran as a sub-agent could not ask anything, and every decision
would rest on a default.

The command has no `agent:` key, and the plugin has no skill named `build`,
so no skill hides the command.

## Decision

The coach and every funder decision run in the user's own session. The
judge is a sub-agent. From v0.3.0 the figure extractor is a second one.

`commands/build.md` has no `agent:` key and no `context: fork`, so the command
body runs inline and the coach keeps `AskUserQuestion`.

The judge (`agents/judge.md`) needs no questions. It reads files and writes
one reply. A fresh context is what the wall needs.

### The second sub-agent, the figure extractor

The figure extractor, `agents/figure-extractor.md`, reads the case and returns
its proposed figures as JSON in its reply, and judges nothing: it decides no
verdict, no grade and no confirmation. Its only tool is Read, so it writes no
file. The coach saves its reply outside the case folder and passes it to
`bc.py figure`, which checks each proposal (ADR-009). The extractor asks no
question, so it loses nothing by running as a sub-agent, and a fresh context
reads the case with less pull from the coaching conversation. Nothing
enforces that isolation: the coach writes its prompt and handles its reply.

### The analysts and the coach's plugin runs (v0.5.0)

From v0.5.0 the evidence team adds the analysts, `agents/case-*-analyst.md`
(ADR-013). Each analyst is a sub-agent that may plan, draft and write one
reply, to its own reply file in the case's `team/` folder. It asks no question:
its plan lists the cards, and the coach asks them. So the analysts lose
nothing by running as sub-agents, and the coach keeps every question.

From the main session, the coach dispatches the route of each command a plan
names with the `Agent` tool and the map's `subagent_type`, and waits for it to
end. It runs one command at a time, and starts the next run or asks the next
card only after that. A route ran in the
background in every spike run, so the coach ends its turn after a dispatch,
and the completion notice starts its next turn. The coach uses the `Skill` tool only for the seven routes of
`competitive-intelligence`, `jtbd-market-discovery` and `gtm`, which are skills: the `Agent` tool cannot start a skill. At the end of an interactive run, the coach also loads the skill `business-case:learn` with the `Skill` tool (ADR-015). A skill runs in the main
conversation. The four routes of `competitive-intelligence` and `jtbd-market-discovery` dispatch their
own agents from there, and the three routes of `gtm` dispatch no agent. For any other map command it uses the
`Agent` tool: told only to dispatch an agent, Desktop's model ran the skill in
the main session instead.

`## Workflow` holds both the automated and the interactive branch. The
automated branch starts when the arguments hold `--automated`.

## Consequences

- The coach shares the user's context. That is the point: the user sees each
  question and answers it.
- The coach and the judge still never share a context. The judge is given
  only the brief's text. A reply counts only against the files and digests
  the brief names (ADR-002).
- A test pins that the command has no `agent:` key, no `name:` key and no
  `context: fork` (`tests/unit/test_plugin_layout.py`).
- An analyst's prompt is its brief alone. Its agent file says which files it
  may read, and, as with the figure extractor, nothing enforces that. Code
  checks every file its reply cites (ADR-013).
- If Claude Code ever starts to honour `agent:` without `context: fork`, a
  command with that key would become a sub-agent and lose `AskUserQuestion`.
