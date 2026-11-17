# Architecture area checklists

Load the selected area, not every checklist. Use the available evidence to find system-wide choices that remain open. Ask which building blocks must change if a choice changes. A choice confined to one building block is outside this interview.

These checklists guide investigation. Reviewing a topic does not accept a choice or establish area coverage. An accepted ADR can establish coverage without settling every topic in that area. The person can build with open topics and return during implementation.

Use each choice prompt as a starting point. Select two or three options that fit the evidence. Give their advantages and disadvantages, and recommend one based on the person's goals and limits. Treat examples as candidate choices until the person accepts them. Give explanations and examples on request.

## Quality

Map area: `quality`. Establish the quality goals that change system-wide choices.

- [ ] Review stated goals, quality requirements, service targets, incident findings, and known limits. Separate required behavior from how well that behavior must work.
- [ ] In code, inspect time limits, resource limits, failure handling, and tests for load or recovery. Distinguish a configured target from a measured result.
- [ ] Identify the conditions, expected response, and measure for each goal that can change a system-wide decision. Leave targets open when measurements or requirements are missing.
- [ ] Choice prompt: Which goal takes priority when they conflict? Lower delay can require more resources. Lower cost can permit slower responses. Recommend the priority that best supports the required product behavior, and state the cost to the other goal.

## Context

Map area: `context`. Establish what the system owns and what it depends on.

- [ ] Review product boundaries, user journeys, external systems, and organization responsibilities. Identify who owns each external dependency.
- [ ] In code, inspect entry points, external clients, scheduled work, and configuration for external services. Trace a request for required product behavior across the system boundary.
- [ ] Identify required external behavior, failure effects, and constraints that the project cannot change. Separate known boundaries from assumptions.
- [ ] Choice prompt: Does the system own a needed capability or use an external service? Ownership gives more control but adds maintenance. An external service reduces local work but adds dependency limits. Recommend from the required control and available support.

## Strategy

Map area: `strategy`. Include the technology stack here.

- [ ] Review accepted strategy decisions, organization technology guidance, team skills, licenses, budget, and delivery limits.
- [ ] In code, inspect package manifests, dependency locks, framework entry points, and build configuration. Check which technologies the application uses, not only which it declares.
- [ ] Compare the system structure and technology stack with quality goals. Identify choices that are costly to reverse and assumptions that need confirmation.
- [ ] Choice prompt: Keep one deployable application or use independently deployed services? One application reduces release and support work but couples releases. Separate services allow independent change but add communication and support work. Recommend the least separation that meets the known needs.

## Building blocks

Map area: `building-blocks`. Establish system-wide responsibility and dependency boundaries, not detailed component pages.

- [ ] Review existing component descriptions, ownership rules, and dependencies. Identify responsibilities that more than one building block claims.
- [ ] In code, inspect modules, imports, composition points, and calls between major parts. Compare stated boundaries with actual dependencies.
- [ ] Identify which changes cross boundaries and which responsibilities need a single owner. Leave choices internal to one building block outside this interview.
- [ ] Choice prompt: Organize major parts by business responsibility or by technical layer? Business grouping keeps related behavior together but can repeat technical code. Technical grouping shares mechanisms but can spread one product change across many parts. Recommend from the expected pattern of change.

## Data

Map area: `data`. Establish ownership, storage, and consistency choices across the system.

- [ ] Review data definitions, ownership, retention requirements, recovery needs, and accepted storage decisions.
- [ ] In code, inspect schemas, migrations, transactions, store clients, caches, and backup configuration. Trace who writes and reads important data.
- [ ] Identify shared writes, required consistency, deletion obligations, and recovery limits. Separate a backup setting from evidence that restoration works.
- [ ] Choice prompt: Use a shared store or stores owned by separate building blocks? A shared store supports joint transactions but couples schema changes. Separate stores clarify ownership but require coordination and can delay updates. Recommend from the required consistency and ownership boundaries.

## Contracts

Map area: `contracts`. Establish agreements that callers and producers depend on.

- [ ] Review interface definitions, event formats, published APIs, compatibility promises, and external consumer needs.
- [ ] In code, inspect handlers, clients, serializers, message producers, validators, and contract tests. Trace a request or event through its producer and consumer.
- [ ] Identify versioning, error, ordering, retry, and duplicate-handling rules that affect more than one building block.
- [ ] Choice prompt: Use a direct request or an event for this interaction? Direct requests give an immediate result but couple availability. Events reduce that coupling but add delayed results and duplicate handling. Recommend from the caller's required response and failure behavior.

## Conventions

Map area: `conventions`. Include security and identity here.

- [ ] Review organization rules for identity, access, sensitive data, audit records, errors, configuration, and shared coding practices.
- [ ] In code, inspect sign-in checks, permission checks, secret references, log filters, shared middleware, and enforcement tests. Report secret references and access checks without secret values.
- [ ] Identify trust boundaries and rules that need consistent enforcement across building blocks. Separate a written security rule from evidence of enforcement.
- [ ] Choice prompt: Enforce a shared access policy centrally or in each building block? Central enforcement improves consistency but adds a shared dependency. Local enforcement permits local control but risks different rules. Recommend from the trust boundaries and required availability.

## Deployment

Map area: `deployment`. Include cloud, network, and operations here.

- [ ] Review hosting limits, cloud guidance, network boundaries, release rules, availability needs, support duties, and operating cost limits.
- [ ] In code, inspect infrastructure definitions, containers, release jobs, network rules, health checks, alerts, and recovery procedures.
- [ ] Identify where processes and data run, what can communicate, how releases roll back, and who responds to failures. Distinguish configured recovery from tested recovery.
- [ ] Choice prompt: Use a managed service or operate the service directly? A managed service reduces maintenance but limits control and can increase dependency costs. Direct operation gives control but requires support and recovery skills. Recommend from the team's capacity and the required controls.
