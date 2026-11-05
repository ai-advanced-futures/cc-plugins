# Decision areas

A person page of the human team has 1 `owns:<area>` tag for each area that the person decides. `sofa-people list --owns <area>` finds the owners of an area. The `setup` skill (step 6), `requests`, `decision-judge` and `hitl` use the names below, so the same question always finds the same person.

| Area | The person decides |
|---|---|
| `product-direction` | what the product does next: the PRD, the roadmap order, the scope of a milestone |
| `technical-direction` | the architecture, the ADRs, the stack, the code conventions |
| `content` | the text that users read: docs, skill text, examples, names |
| `releases` | when a change ships, and a version bump that is not a patch |
| `destructive-actions` | a delete of data, a branch or a plugin, a force push, a revert of a release |
| `money` | a paid service, a plan change, a spend limit |
| `security` | secrets, access rights, a security finding |
| `people` | who joins the human team, and the role of each person |

An area that is not in this table is permitted. Write it in lowercase, with `-` between the words, for example `business-strategy`.

## Which area a question has

Find the area of a card from what the answer changes. Use the first row that matches:

1. The answer deletes, force-pushes or reverts something: `destructive-actions`.
2. The answer spends money: `money`.
3. The answer changes a secret or an access right: `security`.
4. The answer changes an ADR or the structure of the code: `technical-direction`.
5. The answer changes the PRD, the roadmap or the scope: `product-direction`.
6. The answer changes text that users read: `content`.
7. The answer changes when something ships: `releases`.

When no row matches, or when the area has no owner, the card goes to each person whose tag is `escalates-to:none`.
