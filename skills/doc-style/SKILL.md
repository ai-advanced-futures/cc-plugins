---
name: doc-style
description: 'Writing style for all prose that a person reads: chat replies, documentation, README files, PR titles and descriptions, commit messages, code comments, error messages, release notes, and technical emails. Based on the Google developer documentation style guide. Load before you write or edit any of these.'
---

# Doc style

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, licensed CC BY 4.0. Tuned against Claude Opus 5.5 and other Claude 5 models. Test again after a model change.

## Reference files

| File | Load when the text has |
| --- | --- |
| `references/voice-and-tone.md` | prose longer than a short chat reply: person, tense, claims, "must" and "should", pronouns |
| `references/structure.md` | headings, lists, tables, steps, notes and warnings, links, images |
| `references/code-and-ui.md` | code, commands, file names, placeholders, UI names, API reference comments |
| `references/punctuation.md` | a question about a comma, dash, colon, quotation mark, capital letter, or abbreviation |
| `references/numbers-and-names.md` | numbers, dates, times, units, phone numbers, product or trademark names |
| `references/global-audience.md` | content for a wide or global audience: accessibility, inclusive terms, translation, example values |
| `references/word-list.md` | a term whose form you are not sure of, such as "sign in", "setup", "e.g.", or "allowlist" |
| `references/vale.md` | a request to check style, or a repository with a `.vale.ini` file |

## Instructions

1. Before you write, read each reference file whose row matches the text. For a short chat reply, read none.
2. When the user, the project, or a `CONTRIBUTING` file gives a different style rule, follow that rule, because local rules take priority over this guide.
3. Address the reader as "you", and use active voice and present tense.
4. Put the goal or the condition first in a sentence, then the instruction: "To delete the file, click **Delete**."
5. Use "must" for a required action, "can" for an optional action, and "might" for a possible result.
6. Leave out "please", "simply", "just", and "easy", because these words add no facts. Leave out "new", "now", and "currently" when they describe a feature, because the text becomes wrong after the next release.
7. Use sentence case in every title and heading.
8. Use a numbered list for steps in sequence, and a bulleted list for other lists of three or more items.
9. Put code, commands, file names, and values in code font, and put UI element names in bold.
10. Use the serial comma, and write link text that names the target page, because a screen reader can read the links alone.
11. When Vale is installed and you changed a Markdown file, run Vale on the file with `references/vale.md`, and fix each error.
