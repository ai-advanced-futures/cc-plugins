---
name: osaat
description: Execute any series of steps one at a time with explicit confirmation between each step. Use when the user mentions "one at a time", "one by one", "step-by-step", "review one by one", or wants to review and approve each step individually before proceeding.
---

# OSAAT (One Step At A Time)

## How It Works

Divide the task into small steps. Do no step until the user approves it, and show the result of each step before you ask about the next one. The user can stop, change, or skip any step.

Ask each question with the AskUserQuestion tool, in the format below.

## How to Write a Question

The AskUserQuestion tool can hide the text that you write before the call. The user sees only the header, the question body, the options, and the preview of the selected option. Thus, these fields must hold all of the context.

### Rule 1: Put all of the context in the question body

Write the `question` field in this format:

```text
Step <N> of <total> (<ID>). I recommend Option <K>, at <low|medium|high> confidence. <Why this step needs a decision from the user.>

THE QUESTION: <The question, in 1 sentence.>

WHAT THIS IS ABOUT: <The facts that the user needs to answer: what the step does, why it is necessary, the result of the last step if it changes this decision, and the files, commands, or values that the step touches. Give the ID of each source, for example DECISION-234.>

Select an alternative to see its pros and cons. <The question again, as the last line, with a question mark.>
```

Set `header` to the ID of the step, for example "QUESTION-43" or "Step 2".

Example:

```text
Step 10 of 10 (QUESTION-43). I recommend Option 1, at medium confidence. I ask because each option breaks one of your rules.

THE QUESTION: What does a search give when one part is larger than one tool result?

WHAT THIS IS ABOUT: A page of results never cuts a part (DECISION-234). But a page must fit in one tool result (CONSTRAINT-21). A schema can set no size limit for its parts (DECISION-171), so one part can be larger than one tool result. No page says which rule gives way.

Select an alternative to see its pros and cons. Which rule gives way for a part that is larger than one tool result?
```

### Rule 2: Put the pros and cons of each alternative in its preview

When you give the user 2 or more alternatives, write the pros and cons in the `preview` field of each option, not in the question body. Use this format:

```text
<NAME OF THE ALTERNATIVE, IN CAPITAL LETTERS>

<What it does, in 2 to 5 short sentences.>

✅ <One pro>
✅ <One more pro>
❌ <One con>
```

Example:

```text
CUT IT ACROSS PAGES

Only a part that is larger than the
largest page size comes in pieces. Each
piece comes alone on its own page. Each
piece says "piece 2 of 3".

✅ The full text comes through
✅ Each page fits one tool result
❌ Breaks "it never cuts a part"
   (DECISION-234) for this case
```

Obey these rules for the format:

- Make the `label` a short form of the name in the preview, 5 words maximum.
- In the `description` of each option, write 1 short sentence.
- Give each alternative 1 pro and 1 con at minimum. Keep each line of the preview to 40 characters maximum. Break a longer line, and indent the next line by 3 spaces after a ✅ or a ❌.
- If a step has only 1 action, ask "Do this step?" with the options "Yes (Recommended)", "Skip this step", and "Stop". Do not add previews, because there is no alternative to compare. The user can select "Other" to change the step.
