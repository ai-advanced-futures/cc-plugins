# gtm

This plugin plans the go-to-market work of a product. It builds the brand identity, the marketing plans, the sales playbooks, and the revenue funnel. It starts from what the product really does, what customers need, and what the marketing masters say works. An integrity check scores each claim before the claim reaches an output file.

## What the plugin does

The plugin treats the go-to-market work of a company as one system, from brand identity to closed revenue. It uses three sources of truth at the same time:

1. **What the product does.** The plugin scans the codebase when you agree. It also reads the output of the optional `value-ip` plugin.
2. **What customers need.** The plugin reads the knowledge graphs of `jtbd-market-discovery` and `competitive-intelligence`.
3. **What the masters say works.** The plugin uses the work of Kotler, Moore, Sinek, Miller, Aaker, Rackham, Pine, and Cornell marketing science.

### Moral marketing

This plugin does not write false marketing, misleading claims, or hype that is larger than the product. The integrity agent reviews each artifact before delivery. It gives each claim a Truth Tier from 1 to 5:

- **Tier 1, Shipped:** The code is in production and customers use it. State it as fact.
- **Tier 2, In-Flight:** The code is in progress. Say "now in early access".
- **Tier 3, Committed:** The work is designed, budgeted, and scheduled. Say "coming in Q3".
- **Tier 4, Strategic Intent:** The direction is stated and not yet funded. Say "our vision is".
- **Tier 5, Speculation:** No evidence. The plugin blocks it. It never appears in an output file.

Run `/gtm:audit <path>` to audit any marketing or sales file, also a file that this plugin did not write. For example:

1. Write a draft with another tool, such as the `marketing:draft-content` skill.
2. Save the draft in a file, such as `draft-blog-post.md`.
3. Run `/gtm:audit draft-blog-post.md`.
4. Publish only the file that passes the audit.

### Frameworks in the plugin

- **Strategy:** Kotler STP, Ries and Trout, Moore Chasm, Ansoff Growth, Pine Experience Economy.
- **Brand:** Sinek Golden Circle, Miller StoryBrand, Aaker Brand Identity, Campbell Hero's Journey.
- **Demand:** AARRR Metrics, PLG Playbook, Sean Ellis PMF signal, Growth Loops.
- **Sales:** SPIN Selling, Challenger Sale, MEDDPICC.
- **Integrity:** the five-tier Truth Tier system and the moral marketing principles.

| Framework | Author | Book |
|---|---|---|
| Kotler STP | Philip Kotler | *Marketing Management* |
| Technology Adoption Lifecycle and Chasm | Geoffrey Moore | *Crossing the Chasm* |
| Positioning | Al Ries and Jack Trout | *Positioning: The Battle for the Mind* |
| Golden Circle | Simon Sinek | *Start With Why* |
| StoryBrand | Donald Miller | *Building a StoryBrand* |
| Brand Identity System | David Aaker | *Building Strong Brands* |
| Experience Economy | Pine and Gilmore | *The Experience Economy* |
| AARRR Metrics | Dave McClure | |
| SPIN Selling | Neil Rackham | *SPIN Selling* |
| Challenger Sale | Dixon and Adamson | *The Challenger Sale* |
| MEDDPICC | Jack Napoli | |

## Install

You need [`uv`](https://docs.astral.sh/uv/). The plugin runs its scripts with `uv run`.

```
claude plugin install gtm@cc-plugins
```

## Commands

The plugin has 13 commands. Each command runs in the main conversation and asks you its questions there. No agent of the plugin asks you a question. Start with `/gtm:run`.

| Command | What it does | What it asks |
|---|---|---|
| `/gtm:run` | Builds the full GTM package. It starts the orchestrator to prepare the session, then it starts the agents in four waves itself. | Your role, the business stage, and the primary goal. For an idea or pre-PMF stage, it shows the Sean Ellis test and asks if you want to continue. Then it asks if it may scan the codebase, and which files to read. When a score is from 0.60 to 0.84, it asks you to rerun the agent or to override the score. |
| `/gtm:setup` | Shows how to add each optional MCP server, then writes `.gtm-mcp-status.json`. | Which servers to set up, one by one. It skips a server that is connected. It asks for no token. |
| `/gtm:learn [path]` | Reads call transcripts, win and loss notes, and playbooks, and extracts GTM intelligence. | The place of the knowledge files, when you give no path. The option `--notion` reads from Notion. |
| `/gtm:audit [path]` | Gives each claim of one file a Truth Tier, and writes a cleaned copy. | Which file to audit, when you give no path. The option `--all` audits all files in `gtm-output/`. |
| `/gtm:funnel` | Reads the unified revenue funnel: the MQL, SAL, and SQL handoff, the bottleneck, and the revenue math. | The MQL and SQL definitions, when `mql-criteria.json` or `sql-criteria.json` is missing. |
| `/gtm:marketing:brand` | Builds the brand identity, the voice, the positioning, and the StoryBrand script. | The product, the target customer, the capabilities, and the differentiators. |
| `/gtm:marketing:launch` | Builds the launch plan, the campaigns, and the MQL criteria. | The product, the target customer, whether a customer can sign up alone, the channels, and the year-one target of each channel. |
| `/gtm:marketing:content` | Builds the content strategy and the content calendar. | A short product description, when `voice-guide.md` or `brand-identity.json` is missing. The options are `--horizon`, `--focus`, and `--keywords-only`. |
| `/gtm:marketing:funnel` | Reads the top of the funnel: the acquisition channels and the entry health. | The product, the time window, and the counts: visitors, signups, activated users, and MQLs. |
| `/gtm:sales:pitch` | Builds the pitch outline and the pitch narrative with Challenger Sale and StoryBrand. The option `--format` is `slides`, `narrative`, or `both`. The plugin makes no slide file. | Nothing. The options are `--audience`, `--deal`, and `--format`. |
| `/gtm:sales:prospecting` | Builds the ICP-driven prospecting plan and the outreach sequences. | Nothing. The command builds the ICP when it is missing. The options are `--icp-segment`, `--quota`, and `--intent-signals`. |
| `/gtm:sales:pipeline` | Builds the MEDDPICC pipeline playbooks. | The stage names and the usual deal length, when `hubspot` is not added. |
| `/gtm:sales:pe-prospecting` | Researches the portfolio companies of private equity firms, scores them, and ranks the leads. | The name of the private equity firm, when you give no `--firm`. |

The three commands `/gtm:marketing:brand`, `/gtm:marketing:launch`, and `/gtm:marketing:funnel` also write a result file. A coach plugin, such as business-case, can run them. The file is in `.gtm/results/`.

## Skills

The plugin has 33 skills. A skill gives a framework or a rule to an agent or to you.

- **Frameworks (16):** `frameworks-aaker-brand-equity`, `frameworks-aarrr-metrics`, `frameworks-ansoff-growth`, `frameworks-campbell-hero`, `frameworks-challenger-sale`, `frameworks-growth-loops`, `frameworks-kotler-stp`, `frameworks-meddpicc`, `frameworks-miller-storybrand`, `frameworks-moore-chasm`, `frameworks-pine-experience`, `frameworks-plg-playbook`, `frameworks-pmf-signal`, `frameworks-ries-trout`, `frameworks-sinek-why`, `frameworks-spin-selling`.
- **Integrity (3):** `integrity-audit`, `integrity-moral-marketing-principles`, `integrity-truth-tier-system`.
- **Marketing (5):** `marketing-brand-identity`, `marketing-content`, `marketing-gtm-funnel`, `marketing-launch`, `marketing-unified-funnel`.
- **Sales (4):** `sales-pe-portfolio-prospecting`, `sales-pipeline`, `sales-pitch`, `sales-prospecting`.
- **Runners for a coach plugin (3):** `marketing-launch-runner`, `marketing-brand-runner`, `marketing-funnel-runner`. Each one runs the matching command for a coach plugin, asks you nothing, and publishes nothing.
- **Sales compensation (2):** `sales-comp-gate-review` runs the sales-comp precondition gate. It asks you the five preconditions, then writes a deterministic `proceed`, `pause`, or `re_pause` recommendation. `agentic-pricing-comms` holds six stakeholder message templates for a change to agentic pricing.

## Inputs

- Your answers to the questions of each command.
- Files that you name for `/gtm:learn` and `/gtm:audit`.
- The codebase, only when you agree to the scan. The scan is read-only.
- The knowledge graphs of two plugins, when the project has them. Step 3 of `/gtm:run` runs `scripts/plugin_integrator.py`. It reads each graph through the save code of the plugin that wrote it. It does not read the files of that plugin.
  - `competitive-intelligence`: the `Competitor`, `Offer`, and `SwotItem` pages of all runs, and the `LensResult` pages of the `jtbd-performance` lens. Make the graph with `/competitive-intelligence:discover` or `/competitive-intelligence:analyze`.
  - `jtbd-market-discovery`: the `Run`, `Outcome`, `Segment`, and result pages of the newest finished `discover` run. Make the graph with `/jtbd-market-discovery:discover`.
  - The plugin writes a copy of each page list to `.gtm/upstream/<graph>/`. Each run of step 3 writes the copies again. The agents read the copies.
  - If a graph is absent, the run goes on with no input from it. The plugin writes one line that starts with `NO-GRAPH:` or `GRAPH-READ-FAILED:` to `.gtm-graph-notes.txt` in the project folder (outside `.gtm/`, so the lines reach you also when `.gtm` is a link), and `/gtm:run` shows each line of that file.
  - The plugin reads no old output file of these two plugins. If you have such a file, run the discover command again to make the graph.
  - `pricing`: the file `right-price` that the plugin finds in the project.
  - `value-ip`: the scorecard at `.value-ip/<run>/output/value-ip-scorecard.md`. This plugin is optional. The GTM steps work without it.
  - `aiml`: the `p15-trigger-event` file that `agentic-pricing-comms` reads.

## Outputs

The plugin does not change the file names of the source plugin. All files are in the project.

| Path | Content |
|---|---|
| `gtm-context.json` (at the git root) | The session state: the product, the learned knowledge, the brand, the ICP, the plugin inputs, and the completion flags. |
| `gtm-output/` | The final files that passed the integrity gate, such as `brand-identity.json`, `launch-plan.json`, `pitch-deck.json`, `pipeline-playbook.json`, `funnel-metrics.json`, `consolidated-audit.json`, and `truth-tier-audit.json`. |
| `.gtm/working/` | The drafts of the agents. |
| `.gtm/audit/` | The integrity reports. |
| `.gtm/open-questions.json` | The choices that `/gtm:run` asks you. The run ends with `OPEN: .gtm/open-questions.json` until you answer. |
| `.gtm/results/` and `.gtm/<run_id>/` | The result file and the files of a run that a coach plugin starts. |
| `.gtm/sales-comp-gate-input.json`, `.gtm/sales-comp-precondition-gate.json`, `.gtm/sales-comp-gate-handoff.json` | The input, the result, and the handoff of the sales-comp gate. |
| `.gtm-mcp-status.json` | The status of the MCP servers that `/gtm:setup` checked. |

A finished run ends with the line `DONE: gtm`.

## Optional tools

All of these tools are optional. The plugin starts no outside service by itself, and it has no `.mcp.json` file. A step uses a tool when you have it. It works without the tool when you do not.

### MCP servers

Run `/gtm:setup` to add the servers. The fixed server names are `hubspot`, `apollo`, `ahrefs`, `canva`, `google-analytics`, `notion`, and `slack`.

| Server | What it gives | Used by |
|---|---|---|
| `hubspot` | Contacts, deals, pipeline data, and email campaign data. | funnel, prospecting, pipeline |
| `apollo` | Prospect search and contact enrichment. | prospecting, PE prospecting |
| `ahrefs` | Keyword research and backlink data. | launch, content |
| `canva` | Brand kits, launch assets, content templates, and visual asset briefs. The plugin does not make a slide deck. | brand, launch, content |
| `google-analytics` | Real conversion data, channel attribution, and funnel metrics. | funnel |
| `notion` | Reading and writing documents, and publishing launch plans. | launch, learn |
| `slack` | Campaign announcements. | launch |

`/gtm:setup` shows the setup in two ways:

1. **Docker MCP Toolkit.** Use this way when you have the toolkit.
2. **A script or a `claude mcp add` line.** Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup_mcp.sh" <name>` in your own terminal. `<name>` is `all`, `hubspot`, `apollo`, `ahrefs`, `ga4`, `notion`, or `canva`. The script asks for each token in your terminal, and it gives the token to `claude mcp add-json`. Or copy the `claude mcp add` line that the command shows.

A server that you add has tools named `mcp__<server>__<tool>`. To check the names in your session, run `/mcp`.

The script `setup_mcp.sh` starts each server at a pinned version:

| Server | Package | Version | Maintainer |
|---|---|---|---|
| `hubspot` | `@hubspot/mcp-server` | 0.4.0 | HubSpot |
| `apollo` | `@thevgergroup/apollo-io-mcp` | 3.0.0 | 1 person, not Apollo.io (third party) |
| `notion` | `@notionhq/notion-mcp-server` | 2.6.1 | Notion |
| `canva` | `@canva/cli` | 2.17.0 | Canva |
| `google-analytics` | `analytics-mcp` | 0.8.0 | Google (from PyPI, started with `uvx`) |

`ahrefs` is the hosted server of Ahrefs. A pin holds the version of the package, not of the packages that it needs. A server that you added before this version keeps its old package: the script warns you, and you run `claude mcp remove <server>` and then the script again.

Slack has no step in the script. The package `@modelcontextprotocol/server-slack` is deprecated, and the hosted server of Slack (`https://mcp.slack.com/mcp`) takes only a registered Slack app, and has no tool named `slack_post_message`. To post from `/gtm:marketing:launch`, add your own server with the name `slack` that gives this tool. Without it, the command writes no Slack post. The official Slack plugin gives other tool names, so the command does not use them.

The scopes and rights that the script asks for:

| Scope or right | Who needs it |
|---|---|
| `crm.objects.contacts.read` | `sales-agent` |
| `crm.objects.companies.read` | `sales-agent` |
| `crm.objects.deals.read` | `funnel-agent` |
| Google Analytics role Viewer | `funnel-agent`, `marketing-agent` |
| Notion capability Read content | `/gtm:learn` |

The Notion step asks for Read content only. `/gtm:marketing:launch` step 10 names a Notion tool that this server does not give, so the step writes no Notion page with it.

The script asks for no HubSpot write scope. HubSpot has no read-only scope for marketing emails, so the script asks for no scope for them.

`claude mcp add-json` reads its JSON only from its argument, not from standard input. So while the script runs, another user of the machine can read the token with `ps`: the machine must be single-user while the script runs. Claude Code then keeps the token in its configuration file. To keep a token out of both, put a reference in the JSON in place of the token, between single quotes (`"PRIVATE_APP_ACCESS_TOKEN":"${GTM_HUBSPOT_TOKEN}"`), and set that variable in the shell that starts Claude Code. Claude Code reads it when the server starts.

When a server is missing, the step uses a fallback:

- No `ahrefs`: web research, marked as approximate.
- No `hubspot`: you give the funnel numbers by hand.
- No `apollo`: the plugin writes the ICP criteria for a manual search.

### Plugins from outside this marketplace

The command `/gtm:run` calls the skills `enterprise-search` and `customer-support` with the `Skill` tool, only when the plugin is in the session. No agent calls a skill. Without the plugin, the agent runs its own short path, and its output names the plugin as an option.

| Plugin | How this plugin uses it |
|---|---|
| `enterprise-search` | `/gtm:run` calls its skill to search the knowledge base, and gives the answer to the knowledge agent. |
| `customer-support` | `/gtm:run` calls its skill for churn signals and ticket summaries, and gives the answer to the knowledge agent. |
| `value-ip` | No call. The plugin reads its output files: the survived IP claims that anchor the positioning (brand agent and integrity agent). |
| `sales` | No call. The sales agent does the account research and the prospecting itself, and its output names `sales:call-prep` and `sales:prospect-research` as options. |
| `marketing` | No call. The marketing agent writes the content drafts and the performance summary itself, and its output names `marketing:draft-content` and `marketing:performance-report` as options. |
| `data` | No call. The funnel agent estimates the conversion rates itself, and its output names the `data` plugin as an option for SQL queries. |
| `tech-contracts` | No call. The sales agent reviews the redlines of a vendor contract itself, says that no `tech-contracts` review ran, and names `tech-contracts:review` and `tech-contracts:negotiate` as options. |

Two of these plugins, `value-ip` and `tech-contracts`, are optional plugins from outside this marketplace. The plugin works without them. This README gives no install line for `value-ip`.

### Plugins of this marketplace

`competitive-intelligence` and `jtbd-market-discovery` save a knowledge graph that this plugin reads. `pricing` writes a file that this plugin reads. `aiml` writes the `p15-trigger-event` file. Run them before `/gtm:run`. To read a graph, this plugin needs the plugin that wrote it, and its Python dependencies (`uv` gives them). Set `GTM_GRAPH_PYTHON` to the Python that runs the save code when you do not use `uv`.

## Grants that a caller must give

A plugin run of this plugin gets no permission from its own tools list. The session that starts it must give these grants, or a run in the default mode refuses the calls and writes no result. `<plugin root>` is the absolute path of the install folder of this plugin. `<answers path>` is the file that the `plugin-run` block names, and it needs a grant only when it is outside the project. Each is an absolute path, so a rule has 2 slashes, for example `Read(//srv/plugins/pricing/**)`. `caller-grants.json` holds the same list.

<!-- caller-grants:start -->
```
Bash(uv run <plugin root>/scripts/result_name.py*)
Bash(uv run "<plugin root>/scripts/result_name.py*)
Edit(/.gtm/**)
Read(/<plugin root>/**)
Read(/<answers path>)
WebSearch
mcp__ahrefs__get_keyword_ideas
mcp__ahrefs__get_search_volume
mcp__google-analytics__run_report
mcp__google-analytics__get_realtime_data
mcp__hubspot__hubspot_get_marketing_emails
```
<!-- caller-grants:end -->

- `WebSearch`: With no `WebSearch` grant, the run uses only the answers, and records a gap for each input that it lacks. Give this grant only in a session whose input you trust, because it lets the run send words of the case to the search provider in a query.
- `mcp__ahrefs__get_keyword_ideas` and `mcp__ahrefs__get_search_volume`: With no `ahrefs` server, or no grant for it, the run uses `WebSearch`, and marks the data as approximate. Give this grant only in a session whose input you trust, because it lets the run send data of the case to the `ahrefs` server.
- `mcp__google-analytics__run_report`, `mcp__google-analytics__get_realtime_data` and `mcp__hubspot__hubspot_get_marketing_emails`: With no `google-analytics` or `hubspot` server, or no grant for it, the run uses the numbers of the answers, and records a gap for each number that it lacks. Give this grant only in a session whose input you trust, because it lets the run send data of the case to the `google-analytics` or `hubspot` server.

`business-case` does not give these grants. Each runner skill holds `WebSearch` and its MCP read tools in its own `allowed-tools`, so in the turn of the skill these calls do not ask.

A person's command can write any path in the project, because its grant is `Write`.

## Privacy

- The plugin reads the files that you name, the codebase only when you agree, and web pages with `WebSearch` and `WebFetch`.
- An MCP server that you add can give CRM and prospect data. That data can hold personal data of contacts. The plugin writes it only into the project files in the table above.
- The publishing steps (a Slack post, a Notion page) run only in a command that you run, and only when the server is added. A runner for a coach plugin never publishes.
- An optional plugin that `/gtm:run` calls with `Skill` (`enterprise-search`, `customer-support`) reads the request that the command gives it.
- The plugin writes no credential. `/gtm:setup` asks for no token. The script `setup_mcp.sh` reads each token in your terminal with `read -rsp` and gives it to `claude mcp add-json` (see "MCP servers" for the limit of this).

## Tests

Run the tests from the folder `plugins/gtm`:

```
pip install -r requirements-dev.txt
python3 -m pytest tests -q -rs
```

The tests run with no skipped test. They do not start `uv` and they do not call an outside service.

## More documents

See [docs/INDEX.md](docs/INDEX.md) for the architecture decisions and the context diagram. See [CHANGELOG.md](CHANGELOG.md) for the changes. See [NOTICE](NOTICE) for the origin of the plugin.
