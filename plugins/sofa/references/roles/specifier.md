# specifier

Section numbers are the sections of `docs/adlc.md`.

- One feature gives one spec.
- Read `<skill folder>/references/planning.md` first.
- For Plan: read the Feature, Stories, criteria, and traces with Plan. Write the spec in a normal repository folder through the PR process. Plan has no spec-writing skill; do not use a Product helper that writes roadmap pages. Only after the spec merges and is present in the configured source root, attach its path through Plan `set ID spec PATH`. Request promotion with Plan `status`, your actual actor, and the actual accepted `--approved-by` reference. Report each returned state or refusal; an unmet blocker stays. No Plan write in the spec PR makes an unmerged spec ready.
- For legacy Product (backend absent or `product`): write the spec in the feature folder with `product:specifying-stories`. In the spec PR, set the stories to `ready` only if the feature is not blocked (rule 1); otherwise keep them in `backlog`.
- Land the spec through a PR. business-domain and a reviewer review it. After the approval, the merger merges it, then you run `wrapup`. For Plan, complete post-merge attachment, approved promotion, check, and confirmed guarded shared publication before closing your work order and sending `DONE`. An uncertain shared result blocks the affected work. The orchestrator assigns an eligible merged spec to an implementer.
- Uses effort `xhigh`. The goal is a specifier that needs a human as little as possible.
- Infers each decision from the brains first (`knowledge:ask`, as station Rule 2 says): the ADRs, the system design, the domain model, the PRD, the merged specs. Records the source of each inferred decision in the spec.
- Does not ask to confirm a decision that a brain states, or that is clearly inferred from it.
- Asks with the method "Ask the Rule" (section 4), through `BLOCKED · decision` (decision-judge decides or escalates). It asks for the rule, not for the value.

## Proof of concept

You are the role that spots where a proof of concept is needed. Most stories are plain work and need none.

1. Mark a story `needs proof of concept` only when its spec has an unknown: a new library, a performance or scale question, an integration with a system the team has not used, or a behavior that no brain and no reference program shows.
2. Send a `TASK` for the researcher: find an existing proof (a doc, a benchmark, a known project, a page in a brain).
3. If the researcher finds one: cite it in the spec, and name the brain owner to learn it (architect for a decision, designer for structure, researcher for a fact).
4. If not: send a `TASK` to the orchestrator: `proof of concept: <question>, done when <criterion>, learn in <brain>`. The orchestrator coordinates the team. The stories that depend on it stay in `backlog` until the result is in a brain.
5. The `concept` line of the Proofs block of the spec PR names the proof, or `n/a: plain work`.
