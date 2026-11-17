# Exploration question card

Use the Sofa HITL presentation for one question at a time. Keep Sofa routing, Slack posting, and judge metadata out of this interview, because Explore asks the person directly.

## Template

```markdown
from architecture:explore → "<plain topic>"

Context:
> <What the choice affects. Explain project terms in plain words.>
> - <Known fact with its source reference.>
> - <Remaining gap or conflict.>

<One question about the remaining choice or missing fact?>

- **<Option name>:** <Description.> [recommended]
  - **Pros:** ✅
    - <Advantage for this project.>
  - **Cons:** ❌
    - <Disadvantage for this project.>
- **<Option name>:** <Description.>
  - **Pros:** ✅
    - <Advantage for this project.>
  - **Cons:** ❌
    - <Disadvantage for this project.>

Defer or supply another answer if neither option fits.
```

Use two or three options with a short bold name and a colon. Give each option at least one pro and one con. Mark one option with `[recommended]` at the end of its description line; explain its basis in the context instead of adding another recommendation line. Use bullets rather than tables or numbered options. Omit unknown facts rather than inventing context.

Show the full card before using AskUserQuestion, with short option names as labels. If that tool is unavailable, ask the same question in the conversation and wait for the answer. Keep deferral available for source intake and later choices. An answer to an information question is not approval to save or replace a decision.
