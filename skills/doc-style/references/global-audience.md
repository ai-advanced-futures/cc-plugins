# Reference: Accessible, inclusive, and global writing

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, CC BY 4.0. Follow the source link for the full rule.

## Accessibility ([source](https://developers.google.com/style/accessibility))

| Rule | Do | Not |
| --- | --- | --- |
| Write "and" in text, headings, and navigation. Keep `&` only when a UI label has it. | Install and configure | Install & configure |
| Keep `&` only for UI labels that show it, tight table headings, diagram labels, and code. | — | — |
| Use "preceding", "earlier", or "following" for positions, because a listener has no "above". | the preceding table | the table above |
| Name a control by its label, not by its shape or place. | Click **Settings**. | Click the gear icon on the right. |
| Give state a second cue, such as a text change, when color or an icon shows it. | Status: **Stopped** (red) | a red dot only |
| Use real text for code, commands, and terminal output, not images of them. | a code block | a screenshot of a shell |
| Give each image alt text that states its purpose; give decorative images empty alt text. | `alt=""` for a border graphic | no `alt` attribute |
| Put new information in the text too, not only in an image or a table symbol. | — | — |
| Prefer SVG to PNG, because SVG stays sharp when the reader zooms. | — | — |
| Write link text that makes sense alone, because screen reader users jump from link to link. | see the quota limits | click here |
| Tell the reader when a link downloads a file, opens a new tab, or jumps on the page. | Download the sample (ZIP file) | — |
| Go down one heading level at a time, and style headings with CSS, not with a wrong level. | h2, then h3 | h2, then h4 |
| Use one level-1 heading for the page title, and no empty headings. | — | — |
| Introduce a table in the text before it, because some screen readers do not announce tables. | The following table lists the regions: | — |
| Mark heading cells with `th`. Add `scope` when rows and columns both have headings. Add `headers`, with unique IDs, when more than one row has column headings. | — | — |
| Keep table cells unmerged, because `colspan` and `rowspan` confuse screen readers. | — | — |
| Introduce an expandable element in the text before it. | To see the limits, expand **Limits**. | — |
| Let text wrap freely, because hard line breaks fail in narrow windows and with large text. | — | — |
| Avoid all caps and camel case in prose, because some screen readers spell them letter by letter. | Save the file | SAVE THE FILE |
| Avoid exclamation marks, question marks, and semicolons when you can, because some screen readers skip them. | — | — |
| Put the full menu path in one bold span, and add an `aria-label` to `>` so that screen readers say "and then". | `**File <span aria-label="and then">></span> Save**` | **File** > **Save** |
| Keep text contrast at 4.5:1 or more in custom styles. | — | — |
| Show content with standard styles, because `visibility:hidden` and `display:none` hide it from screen readers. | — | — |
| Give each form field a `label` element outside the field. | — | placeholder text as the only label |
| State the problem and the fix in a form error. | Enter a project name. | Invalid input. |

## Inclusive language ([source](https://developers.google.com/style/inclusive-documentation))

| Rule | Do | Not |
| --- | --- | --- |
| Remove opinion words such as simple, easy, quick, careful, thorough, and proper, because the task is not easy for every reader. | Add the key to the file. | Simply add the key to the file. |
| Replace "properly" or "carefully" with a check that the reader can do. | Run `status` and confirm that it shows `running`. | Make sure that it runs properly. |
| Use neutral words in place of ableist words. | a final review | a sanity check |
| Use neutral words in place of violent or graphic words when a precise word exists. | stop responding | hang |
| Name the old term once in parentheses when the new term alone can confuse readers. | an allowlist (sometimes called a whitelist) | — |
| Prefer a rewrite to a direct word swap. | allow traffic from these IP addresses | allowlist these IP addresses |
| Show a non-inclusive keyword only in code font, and use the inclusive term after the first mention. | the parent node (named `master` in the file) | the master node |
| Use person-first terms unless the community prefers identity-first terms. | people with disabilities | the disabled |
| Describe disability in neutral words. | uses a wheelchair; lives with | wheelchair-bound; suffers from |
| Describe people without disabilities as nondisabled, sighted, or hearing. | nondisabled users | normal users |
| Write about age with neutral terms. | older adults | the elderly; seniors |

| Use | Instead of |
| --- | --- |
| allowlist, blocklist | whitelist, blacklist |
| primary, replica; parent, child; controller | master, slave |
| placeholder | dummy |
| person-hours; humanity | man-hours; mankind |
| point to; click | hover over; hit |
| fence (a node) | STONITH |
| built-in | native (feature) |
| nondisabled; neurotypical | normal; healthy |
| a plain rewrite of the sentence | first-class citizen; pets versus cattle |
| people with disabilities | physically challenged; differently abled; special |

## Writing for translation ([source](https://developers.google.com/style/translation))

| Rule | Do | Not |
| --- | --- | --- |
| Use the plain verb, but keep a special sense when you need it. | use; start; so | utilize; commence; consequently |
| Use one word in place of a phrase. | some | a number of |
| Use a single verb in place of a phrasal verb, except set up, log in, and sign in. | uses | makes use of |
| Use two nouns or fewer before a noun. | a build pipeline for mobile apps | a mobile app CI build pipeline |
| Put "only" directly before the word it limits. | Send only one request. | Only send one request. |
| Write "how to" plus a verb, not a gerund. | how to rotate keys | rotating keys |
| Use "by using" or "that uses" in place of a bare "using". | Connect by using SSH. | Connect using SSH. |
| Keep "that" after verbs and before relative clauses. | the keys that you created | the keys you created |
| Keep small linking words like "then", "that", and "of", because translation tools need them. | If the file is missing, then the job stops. | If the file is missing, the job stops. |
| Write "all of the", not "all the". | all of the logs | all the logs |
| Write "and then" between two steps. | Stop the agent, and then delete it. | Stop the agent, then delete it. |
| Repeat a word when it removes doubt. | both disk encryption and network encryption | both disk and network encryption |
| Give one meaning to words such as once, while, as, and since. | after the job ends | once the job ends |
| Add a noun after a file or code name. | the `app.yaml` file | `app.yaml` |
| Replace an unclear pronoun with its noun, because translators often see one string alone. | make sure that the bucket is private | make sure that it is private |
| State the condition first, and then the instruction. | To delete the key, click **Delete**. | Click **Delete** to delete the key. |
| Use one term for one concept, with the same capitalization each time. | — | VM, then instance, then server |
| Form plurals without an apostrophe, and give no possessive or plural to a trademark. | APIs | API's |
| Use months or quarters, not seasons, because seasons differ by hemisphere. | in Q3 | this summer |
| Leave out idioms, slang, and humor, because they do not translate. | an estimate | a ballpark figure |

## Example values ([source](https://developers.google.com/style/examples))

| Rule | Do | Not |
| --- | --- | --- |
| Use reserved or fake values, or placeholders, because real data can expose people. | `PROJECT_ID` | a real project ID |
| Make project names meaningful, with numbers when you need many. | `web-prod-1`, `web-prod-2` | `foo`, `bar` |
| Use they, their, and theirs for example people, and give jobs to no fixed gender or ethnicity. | — | — |
| Use the Alice and Bob names only for a specification that uses them. | — | — |

| Item | Safe values |
| --- | --- |
| Domains | `example.com`, `example.org`, `example.net` (reserved for examples). See the source page for more fictional domains. |
| Email | a listed name at a listed domain, such as `kai@example.com`; role addresses such as `support@example.net` are OK |
| Given names | Names from the source list, such as Kai, Dana, or Noam. Check that a name does not suggest a gender that you do not intend. |
| Surnames | an initial after the given name: Hao L., Nur B. |
| Company | Example Organization; add a word to tell two apart: Startup Example Organization |
| Phone | 800-555-0100 to 800-555-0199 |
| IPv4 | `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` |
| IPv6 | `2001:db8::/32`, for example `2001:db8:1:1:1:1:1:1` |
| Street | A fictional address. See the source page for safe addresses. |
| Service account ID | `123456789012345678901` |
