# cc-plugins

A Claude Code plugin marketplace from ai-advanced-futures. It holds plugins for architecture decisions, domain models, product planning, system design, code review, prompts, agent orchestration, a status bar, and a software factory. It also holds plain skills.

This repository is a release. A workflow writes each version from a private development repository. It takes no pull requests. To report a problem, use the private advisory form in [SECURITY.md](SECURITY.md).

## Add the marketplace

```bash
claude plugin marketplace add ai-advanced-futures/cc-plugins
```

## Install a plugin

```bash
claude plugin install <name>@cc-plugins
```

## Plugins

| Plugin | Description |
|---|---|
| `architecture` | The architecture decisions of a repository as an OKF graph on the brain standard: architecture:setup makes or migrates the corpus, architecture:learn writes one ADR, architecture:ask answers from past decisions, and /architecture:check reviews a diff against them. |
| `business-domain` | The domain model of a repository as one OKF graph on the brain standard: bounded contexts, terms, aggregates, events, and relationships, with business-domain:setup, business-domain:learn, and business-domain:ask, and a hook that runs regen and both checks |
| `product` | Product discovery and roadmap planning in two OKF graphs on the brain standard: one page for each requirement and each work item, typed links, product:setup, product:learn, product:ask, and a script that assigns IDs, checks the graph, and finds requirement drift |
| `system-design` | The architecture of a repository as one OKF graph on the brain standard, with system-design:setup, system-design:learn, and system-design:ask. It replaces the system-design skill of the product plugin. |
| `thinktank` | Structured multi-agent strategic analysis and Socratic deliberation for optimal implementation decisions |
| `relay` | Multi-agent orchestration toolkit — ACPX dispatch + adversarial refinement loops, layered on superpowers. |
| `code-review` | Bootstraps a repo-tailored PR review system (contract + per-concern lens skills) into any repo via /code-review:setup, executes it with a repo-agnostic reviewing-prs orchestrator plus lifecycle skills, guides engineers through a PR with the read-only /code-review:hitl walkthrough, and walks one PR chunk by chunk in a pane with /code-review:review-pane. |
| `knowledge` | The base of every brain: the brain standard, the generic OKF knowledge graph, the registry of graphs, the general check, and the generic skills knowledge:setup, knowledge:learn, knowledge:ask, and knowledge:forget. It was the wiki plugin. |
| `prompt` | Measures any prompt, skill, command, agent or plugin against the prompt engineering principles in its reference file, then shrinks it. Counts instructions rather than tokens, runs ten checks in code, cites a rule identifier per finding, and proves the revision moved the count. |
| `status` | A Nord status bar (below the prompt in a terminal, in a band above it in the desktop app): the model, the context, a prompt cache pill (cold, or warm with the time left and the hit percent), the 7-day limit, the folder, the worktree and the git branch. |
| `sofa` | Software factory: a team of Claude Code background sessions that build a product from the PRD and roadmap of a repository. |
| `grounded-synthesis` | Audit a draft against its primary source files. Find the facts that a source holds and the draft does not, and write a gap report. |
| `aiml` | Help a software engineer build an AI or ML feature, from the choice of approach (LLM, classical ML or hybrid) through design, plan, simulation, code scaffold, training guidance, evaluation and MLOps. |
| `competitive-intelligence` | Map the competitors of a market, gather public facts about them, and analyze one competitor through six lenses. Writes a SWOT, recommendations, and a result file for business-case. |
| `prose-authenticity` | Find the signs that a machine wrote a text, and rewrite the text so that it reads as human writing. Tiered detectors, voice profiles, and a humanize loop with a fact check. |
| `ux-hci-design` | Guide a person through UX design with the Design Thinking phases: research, personas, journey maps, design concepts, wireframes, and evaluation, with built-in accessibility (WCAG 2.2) and AI interaction guidelines. |
| `data-strategy` | Assess the data strategy of a software company: business alignment, the data platform, and the data product portfolio. Write a strategy report, a platform ADR, and a data roadmap. |
| `strategic-partnerships` | Find, design and decide on partnerships in a software ecosystem. Runs six phases: readiness, partner candidates, deal structure, technical integration, revenue model, and a go or no-go recommendation. |

## Skills

The `skills/` folder holds plain skills. They are not in a plugin. Install one with `npx skills add`:

```bash
npx skills add ai-advanced-futures/cc-plugins --skill <name>
```

| Skill | Description |
|---|---|
| [bg-watch](skills/bg-watch/SKILL.md) | Watch the background Claude Code sessions on this machine. Find a session that stopped on an API error, restart it, and send it `retry`. jag decides which sessions are stuck, and each jag decision goes into a log. Use "start" to run the check on a schedule, "check" to run it one time, and "stop" to cancel the schedule. |
| [dispatch](skills/dispatch/SKILL.md) | Use when the user wants to dispatch / spin up / launch / kick off a NEW background Claude Code session to work on ONE scoped item — "dispatch a new claude session", "dispatch this", "spin up a session for X", "start a background session to do Y", "kick this off in the background", "run this in another/separate session". Forks the CURRENT session into a new background session (`claude --bg --name <name> --resume <session-id> --fork-session`) so the new session starts with this conversation's full context and begins working immediately — no prompt file, no paste step. One work item per dispatch. |
| [doc-style](skills/doc-style/SKILL.md) | Writing style for all prose that a person reads: chat replies, documentation, README files, PR titles and descriptions, commit messages, code comments, error messages, release notes, and technical emails. Based on the Google developer documentation style guide. Load before you write or edit any of these. |
| [handoff](skills/handoff/SKILL.md) | Compact the current conversation into a handoff document for another agent to pick up. Optionally send it to a named Claude session. |
| [osaat](skills/osaat/SKILL.md) | Execute any series of steps one at a time with explicit confirmation between each step. Use when the user mentions "one at a time", "one by one", "step-by-step", "review one by one", or wants to review and approve each step individually before proceeding. |
| [rebase](skills/rebase/SKILL.md) | Rebase the current branch — onto the latest default branch, onto a branch you name, or resume a rebase in progress |
| [ship-it](skills/ship-it/SKILL.md) | Use when the user wants a change on the default branch now: "ship it", "get this to main", "commit, PR and merge this", "/ship-it". Moves the change into a worktree if it is not in one, commits it, pushes it, opens a pull request, waits for the checks, squash merges (with --admin when the plain merge is refused), runs the wrapup skill, and pulls the latest default branch. |
| [wrapup](skills/wrapup/SKILL.md) | Use when a session's work has LANDED — merged, or intentionally abandoned — and the workspace should be cleaned up: "wrap up this session", "tear down the worktree", "close this out". Confirms the work reached the default branch, then deletes the local branch and removes the worktree it runs in, then moves this session back to the main checkout (outside a worktree it returns to the default branch and pulls). Destructive — hard-stops on uncommitted work, unpushed commits, or an in-progress merge/rebase. If the PR is still open, drive it to green first with a PR-driving skill (e.g. relay:refining-prs). |

Sofa needs the skills `bg-watch`, `rebase`, and `wrapup`, and the skill `find-docs`. Run `/sofa:readiness` to see which skills are missing.

## License

Apache-2.0. See [LICENSE](LICENSE). Third-party notices are in [NOTICE](NOTICE).
