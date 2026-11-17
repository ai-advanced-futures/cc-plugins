# Requirements and return-session review

Use this reference for product fit, affected decisions, and the meaning of coverage. It does not replace the discovery interview.

## Product requirement comparison

When a PRD is available, compare architecture decisions with its functional requirements twice: after initial source review and at the end of discovery. The end comparison must include decisions accepted during the session. Run both comparisons even when required-area coverage remains incomplete.

Check for both types of finding:

- Conflict: a decision makes required product behavior impossible. Name the requirement, the decision, the evidence, and the behavior that cannot work.
- Gap: a functional requirement has no support from the decided architecture areas. Name the requirement and the missing support. Lack of evidence is not proof that the behavior is impossible.

Turn each finding into a separate question, one at a time. Give the context, two or three options with advantages and disadvantages, and one recommendation. Include deferral when the choice cannot yet be settled. If the choice changes an accepted ADR, obtain confirmation before replacement.

Do not change product requirements or edit the PRD. If the person wants a requirement change, leave that change for the product requirements process. State any unresolved conflict or gap rather than reporting that the architecture supports it.

Without a PRD, continue discovery and explicitly report: “The product requirements comparison did not run because no PRD was available.” Do not invent requirements or report a successful comparison.

## Return sessions

Resume from accepted-decision coverage and explicitly open choices. Review changed requirements and evidence first. Do not repeat the whole interview.

For each affected accepted ADR, show the record, the changed requirement or evidence, and the effect on its decision. Ask whether to keep the decision, confirm a replacement, or defer further work. Confirmation of a concern is not confirmation to replace the decision. Keep the accepted record unchanged until the person confirms the replacement.

After explicit replacement confirmation, route the change through `architecture:amending-adrs`. That process uses `architecture:learn` when a replacement needs a new accepted ADR. Keep the relationship to the prior record. Leave unrelated accepted ADRs unchanged and outside the interview. Proposed records and open findings do not become accepted merely because the session resumes.

Use the product comparison when a PRD is available. The person can choose the next affected area or another open area, including during implementation or after the previous stopping point.

## Coverage is not checklist completion

Use the computed map across `quality`, `context`, `strategy`, `building-blocks`, `data`, `contracts`, `conventions`, and `deployment`. Count only accepted ADRs with a confirmed map area. For an existing ADR without a map area, propose a mapping and obtain the person's confirmation. Use explicit confirmation for acceptance and map assignments rather than deriving them from source content.

One accepted mapped ADR establishes area coverage. Deferred choices and proposed, deprecated, or superseded ADRs are outside accepted coverage. Reading a checklist, reviewing code, discussing an option, or approving a deferred knowledge save does not establish coverage.

The person selects the areas required for the first build. Reach the discovery stopping point only when every selected required area has accepted decisions. An area selection that has not happened is not an empty selection. Establish an explicit area selection before reporting completion.

Other areas and topics can remain open. Reaching the stopping point does not mean that the entire architecture or every topic within a covered area is complete. Further discovery remains available. Keep the coverage map computed from ADRs and checklist progress outside persistent storage.

## End-of-session checks

Before reporting the result, check the following:

- Accepted choices have saved accepted ADRs. Report failed writes as failures, not saved decisions.
- Rejected choices have no ADR. Deferred choices remain open, and any unsaved findings are listed.
- The coverage statement follows accepted ADRs and the person's required areas, not checklist review.
- The final PRD comparison ran, or the response explicitly says why it did not run. List unresolved conflicts and unsupported requirements.
- Any changed accepted decision has explicit replacement confirmation. Unrelated records remain unchanged.
