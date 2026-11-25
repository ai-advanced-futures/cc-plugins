# The Brain Studio

The Brain Studio is the set of plugins that people use to build and shape the
brains of a project. This page names the members, shows who uses each one, and
shows how the work of one member reaches the next. It states what code does
and what a person does.

Facts on this page come from the plugin code and the plugin READMEs. When a
plugin changes, check the page again.

## Words

| Word | Meaning |
|---|---|
| Brain | One graph of project knowledge. It follows the [brain standard](../standard/brain-standard.md) of the `knowledge` plugin: one plugin, one graph, OKF pages with typed edges. Only the save script of the plugin writes it. A person confirms every write. |
| Brain Studio | The plugins that people use to build and shape brains, step by step. The agent leads and the person confirms. The agent asks the person for expertise: this is mostly the "consultant" style of work. The name is permanent. It does not depend on how much the agent does on its own. |
| Consultant | The third of five levels of autonomy (operator, collaborator, consultant, approver, observer; [Feng, McDonald and Zhang, 2025](https://arxiv.org/abs/2506.12469)): the agent leads the work and asks the person for expertise or preferences. |
| Software factory | The `sofa` plugin: a set of stations that read the brains and a roadmap, then build, review, and merge. A decision judge and Slack cards bring in a person when one is needed. |

The Brain Studio and `sofa` work together. `sofa` reads the brains and writes
decisions, ADRs, and roadmap status back. No station of `sofa` replaces a
Brain Studio plugin today. Discovery, business case, and PRD creation stay
with people. More automation is a later step, after the gains from the brains
are measured.

## Members

A member is one of two types.

- A brain-writer writes one brain. Its save script is a pair in `BRAINS` of
  `plugins/knowledge/scripts/knowledgelib/probe.py`, and the plugin depends on
  `knowledge`.
- A feeder makes reports or results that feed a brain or another member. It
  writes no brain of its own.

### Brain-writers

| Plugin | Version | Used by | Brain (page types) |
|---|---|---|---|
| `knowledge` | 2.1.1 | Everyone on the team | Generic graph: Concept, Entity, Synthesis, Source, OpenQuestion. It also owns the standard, the registry, and the general check. |
| `product` | 6.11.1 | Product managers, owners | The PRD: Capability, Journey, Persona, Problem, Need, Constraint, Decision, Experience, Risk, Metric, and more. It has a second graph for the roadmap. That graph is legacy: the live roadmap is the `plan` plugin. |
| `architecture` | 1.2.1 | Architects | ADRs, with a `lifecycle` field. |
| `system-design` | 0.3.0 | Architects | System design: Component, Interface, QualityScenario, Convention, DataEntity, DeploymentNode, and more. |
| `business-domain` | 2.0.0 | Owners, architects | Domain model: Context, Term, Aggregate, Event, Relationship, Subdomain. |
| `competitive-intelligence` | 1.12.0 | Strategy leads | Competitors: Competitor, Offer, SwotItem, Moat, Threat, Recommendation, Gap, Run. |
| `jtbd-market-discovery` | 1.12.0 | Product managers, strategy leads | Jobs To Be Done: Job, JobStep, Outcome, Segment, WtpValidation, Run. |
| `business-case` | 0.12.0 | Owners, strategy leads | The case: Case, Part, Evidence, Figure, Finding, Review, Decision, Verdict. |
| `ux-hci-design` | 1.9.0 | UX designers | UX: Persona, Journey, MentalModel, Concept, Screen, StateRule, InteractionRule, Evaluation, EvalFinding. |
| `value-ip` | 1.4.0 | Strategy leads, owners | Value and IP: Run, Differentiator, Verdict, Gap. |

### Feeders

| Plugin | Version | Used by | What it makes, and where it goes |
|---|---|---|---|
| `pricing` | 1.13.9 | Product managers, pricing leads | Price and package files in `.pricing/`. It reads the jtbd and competitive-intelligence graphs. |
| `gtm` | 1.12.6 | Marketing and sales leads | Brand, marketing, and sales files. It reads the jtbd, competitive-intelligence, and value-ip graphs. |
| `product-finance` | 0.16.0 | Product managers, finance partners | Financial analysis in `.product-finance/`. It reads the jtbd graph. |
| `strategic-partnerships` | 2.2.1 | Business development leads | A partnership strategy and a go or no-go result. It reads no graph. |
| `corporate-development` | 0.20.4 | Corporate development leads | An M&A pipeline on one target. It reads the pages of the value-ip graph. |
| `data-strategy` | 0.3.4 | Data and engineering leaders | A strategy report, a platform ADR file, and a data roadmap. It reads no graph and does not save the ADR with `architecture`. |
| `aiml` | 0.8.1 | Engineers, engineering leaders | Design and plan files for an AI or ML feature in `.aiml/`. It reads no graph. |
| `grounded-synthesis` | 0.4.7 | Anyone who checks a draft | A gap report on a draft against its source files. It reads no graph. |
| `architecture-assess` | 1.0.3 | Architects | Assessments and designs. It is a feeder that writes into two brains, but only through their plugins: `architecture:learn` for each ADR and `system_design.py` for each design page. Each save needs a yes from the person. |

### Not members

| Plugin | What it is |
|---|---|
| `plan` | The roadmap store. It turns the PRD into work items. It is not a brain. |
| `sofa` | The software factory. |
| `relay` | Runs many agents with dispatch and refinement loops. |
| `code-review` | Makes and runs a PR review system for a repository. |
| `prompt` | Measures and shortens prompts, skills, and agents. |
| `thinktank` | Runs a debate of many agents to find the best implementation approach. |
| `status` | Shows a status bar below the prompt. |
| `prose-authenticity` | Finds the signs that a machine wrote a text, and rewrites it. |

## Journey: from a market question to merged code

Each hand-off has one status.

- `code`: a script of one plugin reads the output of another plugin.
- `partial`: a skill or an agent reads it, or a script checks only a part.
- `manual`: a person carries the result. No code reads it.

| # | From | To | Status | What happens, and where |
|---|---|---|---|---|
| 1 | `jtbd-market-discovery` | `pricing` | `code` | `plugins/pricing/scripts/brain_read.py` reads willingness to pay and outcomes through `jtbd_graph.py`. |
| 2 | `competitive-intelligence` | `pricing` | `code` | The same script reads the moats through `ci_graph.py`. |
| 3 | `jtbd-market-discovery`, `competitive-intelligence`, `value-ip` | `gtm` | `code` | `plugins/gtm/scripts/brain_read.py` reads the three graphs. The `value-ip` read is optional. |
| 4 | `jtbd-market-discovery` | `product-finance` | `code` | `plugins/product-finance/scripts/jtbd_read.py`. No script of `product-finance` reads the competitive-intelligence graph. |
| 5 | `jtbd-market-discovery`, `competitive-intelligence` | `business-case` | `code` | When the evidence team runs a plugin that has a `graph` key in `plugins/business-case/plugin-map/plugin-map-1.0.0.json`, `lib/brain_read.py` reads the run from the graph. A person can also skip the evidence team. |
| 6 | `value-ip` | `business-case` | `partial` | The plugin map has no `graph` key for `value-ip`, so the case reads a result file, not the graph. The coach does not run `value-ip:analyze`: a person runs it. |
| 7 | `value-ip` | `corporate-development` | `partial` | `agents/deal-advisor.md` tells the agent to find the Run pages of the target and read them. No script does it. |
| 8 | `business-case` | `product` | `manual` | No code in `business-case` or `product` reads the case into the PRD. A person carries it. |
| 9 | `ux-hci-design` | `product` | `partial` | `/ux-hci-design:learn` calls the skill `product:learn` with the argument `experience`. A script option, `--check-prd`, checks which results the PRD already holds. |
| 10 | `ux-hci-design` | `system-design` | `code` | `ux_graph.py tokens --save` writes one `Convention` page, with the tag `design-tokens`, through `system_design.py`. |
| 11 | `architecture-assess` | `architecture`, `system-design` | `partial` | The skills ask the person, then call `architecture:learn` for an ADR. For a design, `scripts/design_to_graph.py` runs `system_design.py`. |
| 12 | `product` | `plan` | `code` | `plugins/plan/scripts/planlib/sources.py` reads the PRD bundle and records source hashes. `plan:generate` makes the work items. |
| 13 | The brains and `plan` | `sofa` | `code` | `plugins/sofa/scripts/readiness.py` checks the registry. See the next section. |

Step 0 is the person with a market question. Steps with no row, such as
`strategic-partnerships`, `data-strategy`, `aiml`, and `grounded-synthesis`,
have no hand-off in code. A person carries their reports into other work.

## `value-ip`

`value-ip` asks if an artifact (a plan, a PRD, code, an analysis, or due
diligence) holds a real differentiating value and an IP claim. Four framework
agents (7 Powers, Blue Ocean ERRC, disruption, core and context) analyze it and
debate. The run writes a result file in `.value-ip/results/`.

- Page types: `Run`, `Differentiator`, `Verdict`, and `Gap`. Each page links to
  its Run page. `/value-ip:learn` makes the pages, after the person answers
  "Learn these results?" with yes.
- The grade is always `model`. The schema has this one value
  (`plugins/value-ip/schema/value-ip.yaml`). No page is called validated.
- Pages start as `draft`. A person must verify a run
  (`vip_graph.py verify-run`) before its pages become `stable`.
- Readers: `gtm` reads the graph by script (step 3). `corporate-development`
  reads the pages by agent (step 7). `business-case` reads a result file
  (step 6).
- Open item: the plugin map of `business-case` still names `value-ip` as an
  optional plugin and sets no `graph` key. A decision to add the key is open.

## How `sofa` uses the brains

At the start, `/sofa:readiness` runs `scripts/readiness.py`. It checks that
`.claude/knowledge.json` lists these graphs: `knowledge`, `adr`,
`system-design`, `ddd`, and `prd`. It checks the roadmap too. It also checks
that the `knowledge` graph has a page for each person of the team. As a
brain check, only the PRD (and the legacy `roadmap` graph when the roadmap
backend is `product`) blocks the start. A missing ADR, domain, or system-design
graph is an item to fix, and it does not block the start.

At run time, the roles read the brains and write to the brains they own. The
factory file `docs/adlc.md` of a repository (made by `/sofa:setup`) lists the
writer of each brain:

| Brain | Writer in `sofa` |
|---|---|
| PRD | planner |
| `adr` | architect |
| `system-design` | designer |
| `ddd` | business-domain |
| `knowledge` | scribe |

The roadmap status comes from `plan`. A decision judge answers a question of a
station from the brains. When the judge is not sure, a Slack card asks a
person.

Trust scores. The role text of `sofa` says that a `knowledge` page has a
veracity from 1 to 100. The decision judge reads it, and the scribe raises or
lowers it after a person answers. The `knowledge` schema has no field for
veracity, and no skill `knowledge:validate` exists in the plugin. The loop is
described, and the brain does not hold it yet.

## Not yet

- No hand-off from `business-case` to the PRD in code.
- The feeders write no brain of their own. Their reports stay in files.
- No design-system brain. `ux-hci-design` saves design tokens into one
  `Convention` page of `system-design`.
- No measure of how much the brains improve the output of an agent.
- The trust score loop of `sofa` has no field in the `knowledge` schema.
