# ADR-005: Adopt the plugin result file

**Status:** Accepted
**Date:** 2026-11-01
**Updated:** 2026-11-05 (port to this marketplace)
**Updated:** 2026-11-07 (STORY-146: the 3 routes are skills, and "publishes nothing" holds by the skill text and `disallowed-tools`)
**Plugin:** gtm

---

## Context

A coach plugin, such as business-case, reads what the producer plugins found. Before this decision, the gtm commands wrote plans in their own shapes, to the project root and to `.gtm/working/`. No file told a reader which part the person gave and which part the plugin filled in.

A result file has one shape. It marks each default, and it has a block that a coach uses to start a command. Three gtm commands adopt it: `gtm:marketing:launch`, `gtm:marketing:brand`, and `gtm:marketing:funnel`.

Four facts shaped the decision:

1. A test run dispatched the agents that the commands name. `marketing-agent` wrote a stub `gtm-context.json`. `brand-agent` wrote `brand-identity.draft.json`. `funnel-agent` wrote only to `gtm-context.json`. None of them ran the steps of its command. A thin runner that read the command file wrote the real output of each command. The runner was an agent then; since STORY-146 it is a skill.
2. The commands read the shared `gtm-context.json` and the brand files at the project root. Another run can leave or overwrite these files.
3. The commands publish. Launch posts to Slack and creates a Notion page. Launch and brand can make Canva designs.
4. A gtm plan is the intention of the person. It is not a finding. Only a figure read from channel results or pipeline records is evidence about customers.

## Decision

1. **Write one result file for each run.** Each of the three commands writes one result file to `.gtm/results/` at the end of every run. This includes a halt, a partial run, and a run by a person. The file `result-file.json` names the writer of each command and holds the defaults. The file `questions/<command part>.json` lists the inputs. Each command file has an `## Inputs` section. Its `AskUserQuestion` lines carry the ids `[q: <input>]`. The defaults are four: the funnel window is the constant `30d`. The target customer and the channels of launch, and the target customer of brand, are rules. The run chooses them, so their questions have no default value.

2. **The writer is the agent. A thin runner skill is the route.** The `## Result file` section of each command is in the agent that `result-file.json` names for the command: `marketing-agent` for launch, `brand-agent` for brand, and `funnel-agent` for funnel. A person's run of `/gtm:marketing:*` reaches the section, because the last step of each command says to follow it in every run. The section applies only to its command. When `/gtm:run` dispatches the agent, or for `gtm:marketing:content`, the agent writes no result file. A coach calls the skill `marketing-launch-runner`, `marketing-brand-runner`, or `marketing-funnel-runner` with the `plugin-run` block. The runner skill reads the start time and `plugin.json` first, also for a halt. It reads the command file and follows its body. It dispatches no agent. It then follows the `## Result file` section of the agent, and no other step of the agent. Where a command passes work to the integrity agent, the runner checks each claim of a result against `definitions/truth-tiers.md` itself. A runner never asks the person a question, also when the session has the `AskUserQuestion` tool. It accepts `automated` and takes each value from the answers file. The `## Plugin-run block` is the first `##` heading of its body, and it holds the sentence `Ask the person nothing.`

3. **A plugin run uses only what it was given.** It reads the files of an earlier run only through `inputs_from`. It reads and writes no `gtm-context.json`, no file in `gtm-output/`, and no file that the command names at the project root. It writes each file of the command into its own folder, `.gtm/<run_id>/`. The `detail` of a result names that copy. Where a step needs a value that the answers and the defaults do not give, the run leaves out what needs it and records a gap. With no `self_serve` answer, launch names no growth motion. With no `product_capabilities` answer, brand states no proof point. A plugin run with no `product_description` halts and writes the halt gap.

4. **A plan is never customer data.** What the person gave is a `person` source. A `customer_data` source is only a figure that the run read through an MCP connection. The `method` of that result then says `read through the <name> MCP connection`. A funnel channel whose visitors and MQLs the run read through the `google-analytics` connection is a `channel` result with a `customer_data` source. When the answer and the connection both give a channel, the figures from the connection win. No result is called validated, measured, or actual unless a source is `customer_data` or `published`. No result holds a figure that the model computed. The funnel bottleneck stays in `funnel-health.md`, and the command states its one formula.

5. **A runner publishes nothing.** The `allowed-tools` of a runner skill hold no Canva, Notion and Slack tool that creates or posts, and its `disallowed-tools` name the 4 publishing tools. Each runner skips those steps. The text of the skill and the live check of STORY-146 back this up, because a skill that runs in the session of a coach cannot be sure that the removal of a tool lasts. The read-only tools stay: `ahrefs` for launch, and `google-analytics` and `hubspot` for funnel. A server is optional. When it is missing, the step uses its fallback.

6. **The scripts run with `uv`.** A runner skill and a command call `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py` for the file name and the time. The `allowed-tools` of a runner skill name that one script. The text of each file says to run only the scripts of this plugin, one for each `Bash` call, with no inline code. No agent has `Bash`: the runner skill, in the main conversation, follows the shell steps of the `## Result file` section.

## Consequences

- A coach can run any of the three commands with an answers file. It reads one result file that marks each default. Launch gives `channel` and `growth_motion` results. Brand gives `message` and `proof_point` results. Funnel gives `channel` results.
- A person's own run of the slash command writes the result file too, with no `run_id` part, and keeps the publishing steps of the command. A run through a runner publishes nothing.
- Known limit: a runner chooses channels and a target customer when the answers give none. The result marks that it rests on a default, and its `method` says the run chose them.
- ADR-001 lists the agent roster. The three writer agents are in it; the three runners are skills.
- Three agents write a result file for one command each. The context diagram counts them.
- The plugin keeps the names of the three runners, the `plugin-run` block, the `command` values, and the folder `.gtm/results/`, because business-case depends on them.
