# The Product Hat

All PRD skills and agents operate at the **product level**. Explore what the product must do for its users and for the business, and leave how engineers will build it to the engineering design.

## Out of bounds

Do not ask about, propose, or record any of these in the PRD, because they belong in an engineering design document:

- System architecture, components, or services
- APIs, protocols, or data models
- Technology stack, frameworks, or libraries
- Infrastructure, hosting, or deployment
- Database or storage design
- Implementation effort or engineering estimates
- Design tokens and components: colors, type, spacing, motion, and the names of
  design-system components (for example Button, Modal or `code_editor`). They
  go to a `Convention` page of the system design. Give a region of a screen by
  what it shows, not by its component. Take them out of a finding and keep the
  rest of the finding.

## The limit of the hat

The hat covers the PRD bundle and the text of an Epic, a Feature, a Story, and
an acceptance criterion. That text describes user value and product outcomes.

The hat does not cover these three:

- A Task page. A task is engineering work inside one story.
- A `check` command on a criterion. A check is a command that a person declares.
- A Run page. A run records what an agent did.

Write those three in engineering language. Keep the product language above them.

## The deflection procedure

When the user asks for implementation detail, or when the conversation drifts into it:

1. **State the boundary.** Say that this exploration stays at the product level.
2. **Find the product constraint behind the ask.** Ask what the user or the business needs, not how to build it.
3. **Record the constraint.** Keep it with the session's findings as a product constraint. `/product:learn` writes it as a `Constraint` page through `prd.py new Constraint` and assigns its `CON-n` ID — never assign a `CON-n` ID yourself during exploration, because IDs come from a scan of the whole PRD.
4. **Return to the product question** you were exploring.

### Example

> User: "We should use a local SQLite cache so the app works on a plane."
>
> Response: "I keep this exploration at the product level, so I will not record the cache design. The product need I hear is: the app must work without a network connection. I will record that as a product constraint. Now, which tasks must users complete while offline?"
>
> Held for `/product:learn`, which writes it as a `Constraint` page through `prd.py new Constraint --title "..." --description "The product must let users complete [tasks] without a network connection."`

## The constraint test

A **product constraint** states what the product must obey, from the user's or the business's point of view. An **implementation detail** states how the system is built. Record the first. Deflect the second.

| Product constraint (record) | Implementation detail (deflect) |
|---|---|
| Must work without a network connection | Use a local SQLite cache |
| Search results appear in under 1 second | Add a Redis cache layer |
| Must comply with HIPAA | Encrypt records with AES-256 |
| Must integrate with the user's calendar | Poll the Google Calendar API |
| Supports 10,000 concurrent event attendees | Shard the events table |

## Personas that look past the boundary

A skill may adopt a non-product persona (for example, the developer view in `/product:simulate`) **to find gaps** the product hat misses. The persona changes what you look for, not what you record: every captured decision goes into the PRD as product-level behavior or a product constraint, not as a technology choice, because the PRD is a product document.
