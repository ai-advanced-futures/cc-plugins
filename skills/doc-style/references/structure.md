# Reference: Headings, lists, tables, procedures, links, and images

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, CC BY 4.0. Follow the source link for the full rule.

## Headings and anchors ([source](https://developers.google.com/style/headings), [source](https://developers.google.com/style/headings-targets))

| Rule | Do | Not |
| --- | --- | --- |
| Use sentence case for all titles and headings. | Set up a billing account | Set Up a Billing Account |
| Start a task heading with the base form of a verb. | Install the agent | Installing the agent |
| Write a concept heading as a noun phrase. | Agent architecture | Understanding the agent |
| Do not start a heading with an -ing word, because translators handle it badly. A gerund such as "Pricing" is acceptable when no better word exists. | Introduction to cache tuning | Tuning the cache |
| Put "Optional:" at the start of a heading for a section that only some readers need. | Optional: Add a custom domain | Add a custom domain (optional) |
| Use one h1 on each page, and make it unique in the doc set. | — | — |
| Do not repeat the exact page title as a section heading. | Page "Create and delete buckets"; sections "Create a bucket", "Delete a bucket" | Section "Create and delete buckets" |
| Do not number headings, because the heading levels and order already show the sequence. | Install the agent | 1. Install the agent |
| Do not put a link in a heading, because readers can think the link is a heading style. | — | — |
| Avoid code in a heading. If you must use it, add a noun after the code item. | The `retry` setting | `retry` |
| Use an abbreviation in a heading only when it is better known than the long form. | — | — |
| Do not skip a heading level. | `##` followed by `###` | `#` followed by `###` |
| Put text under each heading before the next subheading. | `## Migrate` + intro text + `### Plan` | `## Migrate` + `### Plan` |
| Introduce a group of subsections with "the following sections". | The following sections describe each mode. | This section describes each mode. |
| Write a custom anchor in lowercase, with hyphens between words. | `{: #rotate-keys }` | `{: #RotateKeys }` |
| When you rename a heading, keep the old anchor ID, so existing links still work. | `## Rotate all keys {: #rotate-keys }` | — |

## Lists ([source](https://developers.google.com/style/lists))

| Rule | Do | Not |
| --- | --- | --- |
| Use a list only for two or more items. Set off one item with other formatting. | — | A bulleted list with one item |
| Say clearly in a bulleted list if the reader must do all items or only some. | You can use any of the following formats: | — |
| Write the lead-in of a list as a full sentence. Do not let the items finish it. | Use the export for these tasks: | Use the export to: |
| End the lead-in with a colon when the list follows it. Use a period when other text comes between. | Do the following: | — |
| Capitalize the first word of each item, unless the case carries meaning. | - Read access | - read access |
| End each item with a period. Omit it when the item is one word, has no verb, is all code, or is all link text. | - Copy the file. / - Port number | - Port number. |
| If the end punctuation becomes mixed, rewrite the items in parallel form or put a period on all items. | — | — |
| Add an explanation to all items or to none. Use a description list for explanations. | — | Only one item has an explanation |
| End a run-in heading with a colon or a period, and use the same mark in the full list. | - **Port:** the port that the server uses. | — |
| After a colon, start the description in lowercase. After a period, start it with a capital letter. | - **Port:** the listening port / - **Port.** The listening port. | - **Port:** The listening port |
| After a colon, omit the end period for a phrase without a verb. Add a period when the description has a verb. | - **Logs:** errors, warnings | — |
| Separate a run-in heading from its description with a colon, not a dash. | - **Port:** the listening port | - **Port** — the listening port |
| Use the serial comma in an in-sentence list of three or more items. | logs, metrics, and traces | logs, metrics and traces |
| Do not end a list with "etc." or "and so on". Show in the lead-in that the list is not complete. | formats such as CSV, JSON, and XML | CSV, JSON, XML, etc. |

## Tables ([source](https://developers.google.com/style/tables))

| Rule | Do | Not |
| --- | --- | --- |
| Use a list for single items, a description list for pairs, and a table for three or more facts for each item. | Parameter, type, description → table | — |
| Change a one-column table to a list. | — | A table with one column |
| Use a table only for data with rows and columns. Do not use it for page layout, code, or a long list split into columns. | — | Function names split into two columns |
| Avoid a table in the middle of a numbered procedure. | — | — |
| Introduce a table with a complete sentence, because some screen readers do not announce tables. | The following table lists the limits: | — |
| Add a caption only when several tables are near each other. Use "Table N." and sentence case, with no end period. | **Table 2.** Supported regions | Table 2: Supported Regions. |
| Refer to a table by its number in lowercase. Do not link to a table. | as shown in table 2 | as shown in Table 2 |
| Do not merge cells. | — | A cell that spans two columns |
| Sort rows in a logical order. If no order is logical, sort them alphabetically. | — | — |
| Write column headings in sentence case, short, with no end punctuation. | Default value | Default Value: |
| Do not show new data with only an icon or symbol. Give each one alt text. | ✓ with alt text "Supported" | ✓ alone |

## Procedures ([source](https://developers.google.com/style/procedures))

| Rule | Do | Not |
| --- | --- | --- |
| Introduce a procedure with a complete sentence or an imperative, not a fragment. | To rotate the key, follow these steps: / Rotate the key: | To rotate the key: |
| Write a single-step procedure as one sentence in a bulleted list. | - To reset the counter, click **Reset**. | To reset the counter, follow this step: 1. Click **Reset**. |
| Label sub-steps with lowercase letters, and sub-sub-steps with lowercase Roman numerals. | 1. a. i. | 1. 1.1 1.1.1 |
| End a step that has sub-steps with a colon or a period, as for a lead-in. | 2. Configure the server: | — |
| Order a complex step as: action, command, placeholders, more detail, output, then the result in a new paragraph. | — | — |
| Join menu choices in one step with the `>` sign. | Click **File > Export**. | — |
| State where the action happens before the action. | In the Admin console, open **Users**. | Open **Users** in the Admin console. |
| Restate the location in the first step of each procedure under a different heading. | In Cloud Shell, … | — |
| State the goal before the action. | To export logs, click **Export**. | Click **Export** to export logs. |
| Use the colon form when "To …" makes a required step look optional. | Sort the rows by date: click **Sort**. | To sort the rows by date, click **Sort**. |
| Give the action first and the result second, in the same paragraph. | Click **Save**. A confirmation appears. | — |
| Do not state a result that the next step names again. | 1. Click **Add**. 2. In the **New user** dialog that opens, click **Next**. | 1. Click **Add**. The **New user** dialog opens. 2. In the **New user** dialog, click **Next**. |
| Give the action first and the reason second. | Copy the token. You need it in step 5. | — |
| Start an optional step with "Optional:". | Optional: Add a label. | (Optional) Add a label. |
| Start each step with an imperative verb. | Note the bucket name. | You need the bucket name later. Note it. |
| Use one verb form in a step. | Click **More**, and then click **Save**. | Save it by clicking **More** and then clicking **Save**. |
| Avoid direction words, because they fail with screen readers and translation. Add a screenshot for a hard-to-find control. | in the following diagram | in the diagram below; the button on the right |
| Name an icon by its label, not by its shape. | Click **Menu**. | Click the button with three lines. |
| Do not write "please". | Click **Open**. | Please click **Open**. |
| Say what a command does, not "run the following command". | Create the bucket: | Run the following command: |
| Put "press Enter" in the same step as the typing. | Type `quota`, and then press Enter. | 3. Type `quota`. 4. Press Enter. |
| Do not give keyboard shortcuts. | Copy the value and paste it into the field. | Press Ctrl+C, then Ctrl+V. |
| Document only the best method: keyboard-only first, then the shortest. Put any other method under its own heading or tab. | — | — |
| Link to a repeated procedure. Do not copy it again. | Add a user as in step 2. | — |
| Tell the reader what to prepare before the procedure starts. | You need the following tools: | — |

## Notices and footnotes ([source](https://developers.google.com/style/notices), [source](https://developers.google.com/style/footnotes))

| Rule | Do | Not |
| --- | --- | --- |
| Write the text in the body first, and add a notice only when you must, because readers often skip notices. | — | — |
| Do not put two or more notices together. Reorganize the content. | — | A note followed by a caution |
| Use **Note** for useful data that the reader can skip and still succeed. | **Note:** Each project has a default network. | — |
| Use **Caution** to tell the reader to continue carefully. | **Caution:** Wide address ranges allow all traffic. | — |
| Use **Warning** for a risk of lost data, money, or security, or for a step that you cannot undo. | **Warning:** Do not put a token in a shell command. | — |
| Use **Success** only in interactive content. | — | **Success** on a static page |
| Do not use a note for a cross-reference, a prerequisite, a full step, required data, or an expected result. | — | **Note:** For more information, see … |
| Avoid footnotes, because they hurt accessibility and translation. Use a link, a note, or parentheses. | — | — |
| If you must use a footnote, mark it with a superscript number. | text¹ | text* |

## Links ([source](https://developers.google.com/style/cross-references))

| Rule | Do | Not |
| --- | --- | --- |
| Give a short definition or a few steps on the page. Link only for longer content. | — | — |
| Link to each destination one time on a page. Repeat only for far-apart text, a link to a section, or separate entry points. | — | — |
| Use the exact page title or a short descriptive phrase as link text. | see [Manage quotas] | see [this page] |
| Put the important words first in descriptive link text. | [Quota limits for exports] | [Learn more about what the limits are] |
| Do not use the same link text for different targets. | — | — |
| Write link text that makes sense alone. | [Manage quotas] | [click here], [this document] |
| Do not use a URL as link text. Legal documents are an exception. | see [HTTP semantics] | see [https://example.com/rfc] |
| Put the full name and its abbreviation inside the link. | [Identity and Access Management (IAM)] | [Identity and Access Management] (IAM) |
| Include the noun after a code item in the link text. | the [`--port` flag] | the [`--port`] flag |
| Introduce a link in its own sentence with "For more information, see". | For more information, see [Manage quotas]. | Want more? Go to [Manage quotas]. |
| Add "about" and the topic when the link text does not show why it helps. Use "about", not "on". | For more information about quotas, see … | For more information on quotas, see … |
| Use "see" to refer to a link. | see [Manage quotas] | check out [Manage quotas] |
| For a link to a section on the same page, say so. | see the [Limits] section of this document | see [Limits] |
| When a section title on another page matches one on this page, add the page name. | see [Install] in "Deploy the agent" | see [Install] |
| Say in the link text when a link downloads a file or opens email, and give the file type. | [download the pricing PDF] | [pricing] |
| Open links in the same tab. If a link must open a new tab, say so. | [Accessibility (opens in a new tab)] | [Accessibility] that opens a new tab |

## Images ([source](https://developers.google.com/style/images))

| Rule | Do | Not |
| --- | --- | --- |
| Use text for code, terminal output, and prose. Do not use images of text. | A code block | A screenshot of a code block |
| Save diagrams as SVG. If you cannot, use PNG. Do not use a transparent background. | — | — |
| Use MP4 for animation, because animated GIF files use more resources. | — | animated GIF |
| Crop a screenshot to the part that matters. | Only the **Save** button area | The full window |
| Use the same operating system and look for all screenshots in a doc set. | — | — |
| Hide personal data with a solid box at full opacity, because people can reverse a blur. Flatten layered files. | — | Blur or mosaic |
| Do not use image maps. Put a list of text references after the image. | — | — |
| Introduce an image with a complete sentence. A screenshot right after UI steps needs no lead-in. | The following diagram shows the request path: | — |
| Always include the alt attribute. Use `alt=""` for a decorative image, because without the attribute screen readers may read the filename. | `alt=""` | No alt attribute |
| Do not start alt text with "Image of" or "Photo of". | `alt="Request path from client to proxy."` | `alt="Image of request path"` |
| Keep alt text to 155 characters or fewer, and use punctuation, because screen readers pause at it. | — | — |
| Avoid all caps in alt text, because some screen readers spell out each letter. | — | `alt="WARNING ICON"` |
| Use the same alt text for each copy of a repeated icon. | — | — |
| Introduce a diagram in the body, not in the alt text. Do not use a caption as alt text. | — | — |
| Put a long description in the body when the image holds more than the alt text can say. | — | — |
| Write a caption as a complete sentence with end punctuation. Use "Figure N." when you number figures. | **Figure 2.** The proxy sends each request to a backend. | Proxy routing |
| Refer to a numbered figure in lowercase, and never by position. | as figure 2 shows | the image above; Figure 2 |
| Keep text in an image short and in sentence case. Do not add new abbreviations. Use full trademark names. | — | — |
| Put captions and descriptions in text after the image, not inside it. | — | — |
| Use the site CSS for image layout. Do not center an image. | — | — |
