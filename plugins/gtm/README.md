# gtm

This plugin plans the go-to-market work of a product. It builds the brand identity, the marketing plans, the sales playbooks, and the revenue funnel. It starts from what the product really does, what customers need, and what the marketing masters say works. An integrity check scores each claim before the claim reaches an output file.

## What the plugin does

The plugin treats the go-to-market work of a company as one system, from brand identity to closed revenue. It uses three sources of truth at the same time:

1. **What the product does.** The plugin scans the codebase when you agree. It also reads the output of the optional `value-ip` plugin.
2. **What customers need.** The plugin reads the output files of `jtbd-market-discovery` and `competitive-intelligence`.
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
| `/gtm:run` | Builds the full GTM package. It starts the orchestrator, and the orchestrator runs the agents in four waves. | Your role, the business stage, and the primary goal. For an idea or pre-PMF stage, it shows the Sean Ellis test and asks if you want to continue. Then it asks if it may scan the codebase, and which files to read. When a score is from 0.60 to 0.84, it asks you to rerun the agent or to override the score. |
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

The plugin has 30 skills. A skill gives a framework or a rule to an agent or to you.

- **Frameworks (16):** `frameworks-aaker-brand-equity`, `frameworks-aarrr-metrics`, `frameworks-ansoff-growth`, `frameworks-campbell-hero`, `frameworks-challenger-sale`, `frameworks-growth-loops`, `frameworks-kotler-stp`, `frameworks-meddpicc`, `frameworks-miller-storybrand`, `frameworks-moore-chasm`, `frameworks-pine-experience`, `frameworks-plg-playbook`, `frameworks-pmf-signal`, `frameworks-ries-trout`, `frameworks-sinek-why`, `frameworks-spin-selling`.
- **Integrity (3):** `integrity-audit`, `integrity-moral-marketing-principles`, `integrity-truth-tier-system`.
- **Marketing (5):** `marketing-brand-identity`, `marketing-content`, `marketing-gtm-funnel`, `marketing-launch`, `marketing-unified-funnel`.
- **Sales (4):** `sales-pe-portfolio-prospecting`, `sales-pipeline`, `sales-pitch`, `sales-prospecting`.
- **Sales compensation (2):** `sales-comp-gate-review` runs the sales-comp precondition gate. It asks you the five preconditions, then writes a deterministic `proceed`, `pause`, or `re_pause` recommendation. `agentic-pricing-comms` holds six stakeholder message templates for a change to agentic pricing.

## Inputs

- Your answers to the questions of each command.
- Files that you name for `/gtm:learn` and `/gtm:audit`.
- The codebase, only when you agree to the scan. The scan is read-only.
- The output files of other plugins, when they are in the project:
  - `competitive-intelligence`: the files in `.competitive-intelligence/`.
  - `jtbd-market-discovery`: the files in `.jtbd-market-discovery/`.
  - `pricing`: the pricing files that the plugin finds, such as `evc-analysis.json`.
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
2. **A script or a `claude mcp add` line.** Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup_mcp.sh" <name>` in your own terminal. `<name>` is `all`, `hubspot`, `apollo`, `ahrefs`, `ga4`, `notion`, `slack`, or `canva`. The script asks for each token in your terminal, and it gives the token to `claude mcp add-json`. Or copy the `claude mcp add` line that the command shows.

A server that you add has tools named `mcp__<server>__<tool>`. To check the names in your session, run `/mcp`.

When a server is missing, the step uses a fallback:

- No `ahrefs`: web research, marked as approximate.
- No `hubspot`: you give the funnel numbers by hand.
- No `apollo`: the plugin writes the ICP criteria for a manual search.

### Plugins from outside this marketplace

An agent calls a skill of these plugins with the `Skill` tool, only when the plugin is in the session. Without the plugin, the agent runs its own short path, and its output names the plugin as an option.

| Plugin | Used for |
|---|---|
| `enterprise-search` | Searching the knowledge base (knowledge agent). |
| `customer-support` | Churn signals and ticket summaries (knowledge agent). |
| `sales` | Call prep, battlecards, and prospect research (sales agent). |
| `marketing` | Content drafts and performance reports (marketing agent). |
| `data` | SQL queries and data exploration (funnel agent). |
| `value-ip` | Survived IP claims that anchor the positioning (brand agent and integrity agent). |
| `tech-contracts` | The review and the negotiation of a redlined vendor contract (sales agent). Without it, the sales agent reviews the redlines itself and says that no `tech-contracts` review ran. |

Two of these plugins, `value-ip` and `tech-contracts`, are optional plugins from outside this marketplace. The plugin works without them. This README gives no install line for `value-ip`.

### Plugins of this marketplace

`competitive-intelligence`, `jtbd-market-discovery`, and `pricing` write files that this plugin reads. `aiml` writes the `p15-trigger-event` file. Run them before `/gtm:run`.

## Privacy

- The plugin reads the files that you name, the codebase only when you agree, and web pages with `WebSearch` and `WebFetch`.
- An MCP server that you add can give CRM and prospect data. That data can hold personal data of contacts. The plugin writes it only into the project files in the table above.
- The publishing steps (a Slack post, a Notion page) run only in a command that you run, and only when the server is added. A runner for a coach plugin never publishes.
- An optional plugin that an agent calls with `Skill` reads the data that the agent gives it, for example the account and deal data of the sales agent.
- The plugin writes no credential. `/gtm:setup` asks for no token. The script `setup_mcp.sh` reads each token in your terminal with `read -rsp` and gives it to `claude mcp add-json`.

## Tests

Run the tests from the folder `plugins/gtm`:

```
pip install -r requirements-dev.txt
python3 -m pytest tests -q -rs
```

The tests run with no skipped test. They do not start `uv` and they do not call an outside service.

## More documents

See [docs/INDEX.md](docs/INDEX.md) for the architecture decisions and the context diagram. See [CHANGELOG.md](CHANGELOG.md) for the changes. See [NOTICE](NOTICE) for the origin of the plugin.
