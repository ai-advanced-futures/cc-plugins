---
name: google-style
description: Writing style for the text of PRD and roadmap documents that the product skills write - requirement text, titles, descriptions, milestones, features, stories, acceptance criteria, decisions, and migrated text. Based on the Google developer documentation style guide (https://developers.google.com/style). Every product skill and agent reads it before it writes document text.
---

# Google developer documentation style

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), with changes.

Follow the Google developer documentation style guide for everything you write: docs, PR descriptions, commit messages, emails, chat messages, release notes, and conversational replies. The full guide lives at https://developers.google.com/style; these are the rules that matter most in practice.

## Voice and tone

- Be conversational and friendly without being frivolous. Write like a knowledgeable colleague, not a marketer or a lawyer.
- Use second person: "you", not "we" or "the user".
- Use active voice. Make it clear who performs each action ("The server sends a response", not "A response is sent").
- Use present tense. Do not use "will" for a thing that happens as a normal consequence, because the reader reads a promise, not a fact ("The command prints the version", not "The command will print the version").
- Contractions are fine ("don't", "it's").
- Write instructions without "please" ("Click **Save**", not "Please click **Save**").
- Cut filler and hype: "simply", "easily", "just", "obviously", "of course", "very", "quite". If a step were simple, you wouldn't need to say so.
- Describe only the features that exist now, because a future feature can change or never ship.

## Grammar and language

- Use standard American spelling and punctuation.
- Put the condition before the instruction: "If you want to save the file, click **Save**" — not "Click **Save** if you want to save the file". The reader decides whether the instruction applies before reading it.
- Use "can" for ability, "might" for possibility, and "must" for requirements, not the ambiguous "should" and "may".
- Prefer "for example" over "e.g." and "that is" over "i.e.".
- Write "email", "sign in" (verb) / "sign-in" (noun or adjective), "set up" (verb) / "setup" (noun). When unsure about a term, check the word list at https://developers.google.com/style/word-list.

## Formatting and structure

- Use sentence case for titles and headings ("Configure the database", not "Configure The Database").
- Use numbered lists for sequential steps, one action per step. Use bulleted lists for non-sequential items.
- Use the serial (Oxford) comma.
- Use code font for code, commands, filenames, paths, API names, and literal values.
- Bold UI element names: "Click **Save**".
- Use descriptive link text that says where the link goes, not "click here" or "this link".
- Write dates unambiguously: "August 18, 2026" or "2026-08-18", not "8/18/26".
- Spell out numbers zero through nine in prose; use numerals for 10 and above, and always for measurements, versions, and technical values.

## Global audience and accessibility

- Keep sentences short and direct. Break up long sentences rather than stacking clauses.
- Use plain words in place of idioms, slang, humor that depends on culture, and phrasal verbs with non-obvious meanings ("determine", not "figure out").
- Provide alt text for images. Convey meaning with names, not with color, position, or direction alone ("the **Delete** button", not "the red button on the right").
- Use inclusive language: neutral terms ("validation check", not "sanity check") and gender-neutral generics.

## Applying this to specific formats

- **PR descriptions and commit messages**: Lead with what the change does and why, in active voice and present tense ("Add retry logic to the upload client"). Keep the summary line under about 70 characters.
- **Technical emails**: State the point in the first sentence. Use short paragraphs and lists. Same voice rules apply — direct, friendly, no filler.
- **Chat and conversational replies**: The formatting rules relax (headings, lists as needed), but voice, clarity, and word-choice rules still apply.
- **Code comments**: Active voice, present tense, sentence case. Explain why, not what.
