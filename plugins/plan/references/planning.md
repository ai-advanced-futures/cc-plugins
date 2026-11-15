# Plan planning reference

This reference adapts Product's scope, theme, feature, and story workflows for a Beads store. It describes the same product decisions. The Plan command line replaces Product's roadmap file writers.

## Source and write boundaries

| Area | Plan behavior | Reason |
| --- | --- | --- |
| PRD | Reads the Product PRD files from the configured source root | Requirements remain in their existing bundle. |
| Roadmap | Reads and writes through Plan's `plan.py` command line | Beads is the work-item store. |
| Product installation | Not needed | Plan includes its own skills, agent, model reference, and PRD reader. |
| Product roadmap writers and analyst | Not called | They write Markdown roadmap pages rather than Beads items. |
| Specification | An existing spec can be attached through Plan | Product's specifying skill targets Product roadmap pages, not Beads items. |
| Follow-up work | Plan develop and Plan item commands | Product task, estimate, check-declaration, and sync skills target another store. |
| Activation | Explicit Plan setup and commands | Installation does not start a factory or replace a knowledge graph entry. |

The PRD read path starts at `index.md`, then `product.md`, then the type index needed for the question, then the relevant pages and their links. A whole-graph question uses Plan's `prd` view. This keeps a large PRD out of the active context. A legacy PRD or an absent bundle is a source problem, not permission to make a second source copy. The report names the missing bundle or its required conversion; an installed Product plugin is not a prerequisite for Plan.

The capabilities and scope lenses support planning. A lens below `in-progress` is a warning: the user can continue with the existing requirements, with the missing evidence named in the summary.

## Overall scope and phases

The scope choice has 3 forms:

| Choice | Detailed work in this run | Other phases |
| --- | --- | --- |
| MVP | First shippable phase | Empty milestones |
| One phase | The named phase | Empty milestones |
| Full product | Every agreed phase | Every phase is developed |

An explicit scope argument answers the scope question. Its meaning is confirmed rather than asked again. With no argument, one question presents these 3 choices.

A phase proposal names its capabilities, its scope entries, its boundary, and the reason for the split. Two to 4 phase proposals give the user a choice. One proposal has a recommendation and a reason. The agreed phase set covers the visible product shape, including future phases outside the selected slice.

The workspace has 1 Project from the PRD product summary. Every agreed phase has 1 Milestone. A future phase outside the selected slice has 0 epics, features, and stories. An existing milestone is reused when it represents the same agreed phase. Dates come from the user or the PRD; an absent target date remains visible as a warning rather than an invented commitment.

`generate` owns scope and milestones, then passes the selected milestone IDs and the scope decision to `develop`. `develop` continues an existing Milestone, Epic, or Feature. The existing children, criteria, links, and traces are the starting point, so continuing a phase adds missing work rather than a second copy.

## Conversation contract

The active decision has 1 question at a time, with 2 to 4 distinct choices and the effect of each choice. A missing fact, an unclear answer, or an answer that conflicts with an earlier decision is a reason for a question. Answers already in the PRD or the current session remain evidence, not repeated questions.

The user owns scope and order. Each set is confirmed before it becomes stored items. Questions end when the active skill has its answers, when the last 2 answers add no item or change, or when the user stops. A partial plan keeps the confirmed items and names the remaining decisions.

Every feature has a separate stop point before story work. Agreement to develop a whole milestone is not agreement to run every feature's story questions without a pause.

## Themes: milestones to epics

A theme groups capabilities that give value together. It becomes 1 Epic attached to the selected Milestone, with 1 or more PRD traces.

| Question area | Evidence for the proposed set |
| --- | --- |
| Value groups | Capabilities that deliver value together |
| Dependencies | Work that must exist before other work can start |
| Risk | Unclear or difficult parts |
| Small gains | Value that needs little work |

Three to 6 theme proposals name their capabilities and scope entries and explain why each group belongs together. Challenges test whether an epic is too large, its smallest useful scope, the effect of delay, and outside constraints. A theme describes user value rather than a system component.

The result names every Epic ID, its Milestone, its PRD traces, untraced epics, and milestone capabilities outside the set. The next Plan helper is `features-identify`.

## Features: epics or milestones to features

A Feature can belong to an Epic or directly to a Milestone. A milestone with no epics is valid input. Each Feature has 1 or more PRD traces, usually Capability pages, and 1 or more agreed criteria.

| Question area | Evidence for the proposed feature |
| --- | --- |
| Discovery | Capabilities needed for the goal, smallest useful version, effect of omission, and overlapping features |
| Scope | The smallest version that still gives value |
| User value | Who benefits and how |
| Dependencies | Features needed first and features this one enables |
| Difficulty | Known, partly known, or unknown work; unknown work calls for a separate investigation |
| Priority | Must have, should have, or nice to have within the epic |
| Challenge | Simpler scope, excess scope, failure cases, and how the user finds and learns the feature |
| Set confirmation | Missing, unnecessary, or overlapping features |

One acceptance criterion is 1 sentence that states an observable completion result. Each confirmed criterion becomes a distinct Criterion item linked to exactly 1 Feature. Criterion text describes the result for the user. Check commands and declarations are separate work, not invented during feature discovery.

The result names every Feature ID, parent if any, Milestone, criterion count, PRD traces, and uncovered capabilities. The next Plan helper is `stories-identify`, after the user's stop point for that feature.

## Stories: features to stories

Story discovery follows the user's first action, later actions, failure cases, and success feedback. Each Story has this form in its description and body:

    As a PERSONA, I want to ACTION, so that BENEFIT.

`PERSONA` names the PRD Persona and its ID when one exists. `ACTION` is the user's action. `BENEFIT` is the value of that action.

| Test | Question the story answers |
| --- | --- |
| Independent | Can this story be built without another story first? |
| Negotiable | Can scope change as the team learns? |
| Valuable | Who benefits and how? |
| Estimable | Is enough known to estimate the work later? |
| Small | Does the story fit in 1 sprint? |
| Testable | Does each criterion state completion? |

A story that fails a test needs a smaller scope or a missing fact. Useful split choices are workflow steps, persona, simple then complex data, create/read/change/remove operations, and basic then faster behavior. Challenges test whether the proposal is 2 stories, its smallest useful form, and failure coverage. The user confirms that the ordered stories cover the full feature without overlap or work outside the feature.

Each Story has its Feature as parent. A new Story inherits the parent's Milestone unless the user chooses another. If the Feature has no Milestone, the user can choose one or leave it absent. A later milestone change on a Feature does not silently move its Stories.

Each agreed Story criterion becomes a distinct Criterion item linked to exactly 1 Story. Feature criteria stay separate from Story criteria. Their IDs remain visible in reports and item views rather than becoming body checkboxes.

A Story carries a direct PRD trace only when it narrows its Feature's traces, such as one step of a journey. Otherwise, the Feature supplies the requirement link. The result names every Story ID, parent, Milestone, criterion count, and the reason for each narrower trace.

## Product-level text

Milestone, Epic, Feature, Story, and Criterion text describes user value and product outcomes. Architecture, services, APIs, storage, hosting, libraries, and visual component choices belong to design work. A technical request can reveal a product constraint: offline work is a user need, while a local cache is a design choice. An existing requirement can be traced; a missing requirement is reported for the source owner rather than written into the PRD by Plan.

Tasks, execution records, and an attached spec can hold engineering detail. Planning does not imply that implementation has started.

Titles and headings use sentence case. Text uses active voice, present tense, and short sentences. Literal IDs, links, hashes, and field values retain their exact form.

## Trace and slice completion

Each Milestone, Epic, and Feature carries at least 1 existing PRD reference. Each reference has a hash from Plan code. Hashes are code output, not authored text. A missing trace target is an error. An untraced item needs the user's requirement or an explicit unresolved gap.

The final coverage view compares every scope entry of the selected slice with item traces. The user classifies each uncovered entry as a gap or an intentional omission. Out-of-slice entries stay outside promotion.

New work starts in `backlog`. A confirmed selected slice can be promoted through Plan's status command with the real actor and the approval reference required by the lifecycle model. A Story without the spec evidence required for agent promotion remains in backlog, with the refusal reported. Attaching or writing an agreed spec is separate work; Product's specifying skill is not a Plan backend.

The CLI decides whether a requested `ready` state is `ready` or `blocked`. The final report uses the returned state and blocker evidence. A refused transition is a partial result, not a completed promotion.

The caller runs 1 final Plan check after the helper group. A standalone helper runs its own check. A nonzero command result stops dependent writes and is shown to the user. Warnings remain in the summary. There is no Product `regen` step for a Beads plan.

## Summary fields

A complete summary names all Milestones, the selected slice, counts of Epics, Features, Stories, and Criteria in that slice, stored states, blockers, spec or approval refusals, untraced items, uncovered scope entries, intentional omissions, and the final check result. A partial run names its stop point and remaining decisions. The follow-up is the next Plan helper or another `plan:develop` run for a future phase.
