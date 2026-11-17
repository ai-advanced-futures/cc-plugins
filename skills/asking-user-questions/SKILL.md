---
name: asking-user-questions
description: "Ask a user for a decision with the human-in-the-loop (HITL) question format: context, one question, alternatives, pros, cons, and one recommendation. Use when a user must choose between alternatives, clarify a requirement, or approve an action."
---

# Ask user questions

This skill formats a question. It does not set team roles, decision authority, or message delivery rules.

## Reference: question card

The text form has this order:

```markdown
from ROLE → "TOPIC"

Context:
> BACKGROUND IN PLAIN WORDS.
> - FACT THAT CHANGES THE DECISION.
> - VERIFIED SOURCE LINK, WHEN AVAILABLE.

ONE-SENTENCE QUESTION?

This answer decides:
THE RULE AND ITS SCOPE, FOR A RULE QUESTION ONLY.

- **SHORT OPTION NAME:** What this option does. [recommended]
  - **Pros:** ✅
    - One benefit
  - **Cons:** ❌
    - One cost or limit
- **SHORT OPTION NAME:** What this option does.
  - **Pros:** ✅
    - One benefit
  - **Cons:** ❌
    - One cost or limit
```

`ROLE` names the sender. `TOPIC` names the decision in a few plain words.
The other capitalized text marks the content to replace.
The optional `This answer decides:` block has at most 5 lines after its heading.
The recommendation appears only at the end of its option, as `[recommended]`.
Lists, rather than tables, keep the card readable on a small screen.
Question IDs and team review metadata stay outside the card.

For `AskUserQuestion`, the same content maps to these fields:

| Field | Content |
| --- | --- |
| `header` | Topic, at most 12 characters. |
| `question` | Context, factual bullets, the question, and the rule block when needed. The final line repeats the question and ends with `?`. |
| `options[].label` | Short option name, at most 5 words. The recommended option comes first and ends with `(Recommended)`. |
| `options[].description` | One sentence that states what the option does. |
| `options[].preview` | The option description and its pros and cons, as in the card. The label carries the recommendation. |
| `multiSelect` | `false` for a choice between alternatives. |

The tool supplies **Other** for a free-text answer.
Previews support single-select questions only.

## Instructions

1. Ask only when the answer changes the next action and belongs to the user. Use known facts and normal defaults otherwise.
2. Present 1 decision at a time. Use plain words for project ideas instead of internal IDs.
3. Put all facts needed to answer in the question itself, because the question tool can hide earlier messages.
4. Give 2 or 3 distinct alternatives. State what each does, with at least 1 pro and 1 con.
5. Link a named work item or pull request only when its URL is verified. State when a source link is missing.
6. Use `AskUserQuestion` when available, with the field mapping above. For a multiple-selection request, use `multiSelect: true` and put each option's pros and cons in its description instead of a preview.
7. If the tool is unavailable or refuses the call, present the text card in the conversation and wait for the answer. An unanswered question is not approval.
