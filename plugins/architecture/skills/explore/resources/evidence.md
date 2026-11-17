# Evidence review

Use this reference during source intake and when evidence conflicts. Review available project records and provided sources before discovery questions. A source shows evidence, not acceptance or permission to replace a decision.

## Three starting situations

Use the evidence that exists for the starting situation:

- No prior architecture: identify available product information and limits. Name missing sources and continue from scratch. A PRD, design graph, or assessment is not a prerequisite. Establish goals, quality goals, and limits with the person after source review.
- Organization guidance: review provided standards, reference architectures, policies, and external ADRs. Identify which guidance applies to this project and which choices still need confirmation.
- Existing application: use an available architecture assessment report. If no report exists, inspect application code with the selected area checklist. Keep observed behavior separate from the intended design.

These situations can overlap. Keep missing evidence explicit rather than filling gaps with invented sources, measurements, requirements, or decisions. A source that cannot be read is unavailable, not evidence that no decision exists.

## Source review cues

Use the available sources that can answer the current question:

- Project ADRs: check lifecycle, scope, rationale, and links to replacement records. An existing accepted ADR settles its recorded choice unless the person confirms a change.
- Product records: identify required behavior, current goals, quality goals, and limits. Keep product requirements separate from architecture preferences.
- Local graphs: use `knowledge:ask` for relevant graph evidence. Keep the returned source references and state any limits in the answer.
- Organization guidance: distinguish mandatory rules from recommendations and examples. Identify the scope of each rule. If applicability or authority is unclear, ask rather than assign source priority.
- External ADRs: retain the source and original decision context. Check whether its assumptions apply here before recommending adoption.
- Assessment report: identify its scope, date, findings, and cited code. Do not treat a report recommendation as an accepted choice.
- Application code: inspect relevant files and call paths, not only filenames or dependency lists. Use [the area checklists](areas.md) to focus the investigation. Cite the files that support each inferred choice.

A document can state intent while code shows different behavior. Describe the difference without assuming that either source authorizes a change.

## Candidate choices and acceptance

For each choice found in documents or code, retain its source, the observed fact, the inferred choice, and any uncertainty. Review each inferred choice individually before the remaining discovery questions. A recommendation, existing implementation, or source reference does not make the choice accepted.

External ADRs also require individual review unless the person explicitly permits adoption without individual questions. Keep this permission limited to the external ADRs that the person authorizes. Choices inferred from guidance, other documents, reports, or code still require individual confirmation. Each adopted ADR must name its source.

Route accepted choices to `architecture:learn` as accepted ADRs. A rejected choice creates no ADR. Deferred choices, including external decisions and “not sure” answers, remain outside the ADR set. Leave existing proposed ADRs unchanged and deferred choices outside both accepted and proposed ADRs.

Before the deferred-findings helper saves knowledge, show the grouped findings and obtain the person's approval. Include deferred external decisions when applicable. Architecture requires the knowledge plugin to load. If the graph or save support is missing or unusable, continue discovery and name the missing part and setup step. List unsaved findings only in the final response, with failed saves marked as failures.

## Conflicting evidence

If an accepted ADR settles the choice, show that record and explain the conflicting evidence. If the person wants to change the decision, use [the affected-decision review](review.md#return-sessions). Keep that accepted record unchanged until the person confirms its replacement.

If no accepted ADR settles the conflict, show the sources, the conflicting claims, and the effect on the architecture or required behavior. State what remains uncertain. Recommend a choice from the known goals and limits, and ask one question that permits a decision or deferral. Ask the person to settle source priority, and keep uncertain choices open.
