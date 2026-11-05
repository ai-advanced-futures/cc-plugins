# Reference: Code, commands, UI elements, and text formatting

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, CC BY 4.0. Follow the source link for the full rule.

## Code in text ([source](https://developers.google.com/style/code-in-text))

| Rule | Do | Not |
| --- | --- | --- |
| Use code font (backticks) for code items in a sentence: classes, methods, attributes, data types, keywords, and enum values. | Call the `refresh` method. | Call the refresh method. |
| Use code font for file names, paths, folders, and environment variables. | Open the `/etc/hosts` file. | Open the /etc/hosts file. |
| Use code font for HTTP verbs, IAM roles, port numbers, DNS record types, and query parameters. | Send a `PATCH` request to port `8443`. | Send a PATCH request to port 8443. |
| Use code font for text that the reader types and for command output. | In the **Zone** field, enter `eu-west-2a`. | In the **Zone** field, enter "eu-west-2a". |
| Use plain font for product names, domain names, and URLs to open in a browser. | Go to example.com. | Go to `example.com`. |
| Write an element name without angle brackets. | the `footer` element | the `<footer>` element |
| Leave out quotation marks around code, unless the marks are part of the code. | Set `mode` to `strict`. | Set `mode` to "`strict`". |
| Use code font for a literal Boolean value, and plain font for the result of a condition. | Returns `false` on error. If the test is true, … | If the test is `true`, … |
| Use code font for a command, and plain font for the project or product with that name. | Run `docker` to start the Docker engine. | Run Docker to start the `Docker` engine. |
| Use code font for an email address only when it is input or output; link a contact address instead. | Enter `ana@example.com`. | Write to `help@example.com`. |
| Omit the class name from a method name, unless the short name is ambiguous. | Call its `delete` method. | Call its `bucket.delete` method. |
| Call an HTTP code a "status code", and put the number and name in code font. | an HTTP `404 Not Found` status code | a 404 error code |
| Show a range of status codes as `Nxx` in code font. | an HTTP `5xx` status code | a 500-series code |
| Put a noun after a code element; do not make the element a verb, plural, or possessive. | the `PORT` constant's value; send a `DELETE` request | `PORT`'s value; `DELETE` the record |
| Add a noun to make a class name plural. | two `Bucket` objects | two `Bucket`s |
| Use code font and bold together when a UI item is also code. | In the **Network** list, select **`dev-net-3`**. | In the **Network** list, select `dev-net-3`. |

## Code blocks ([source](https://developers.google.com/style/code-samples))

| Rule | Do | Not |
| --- | --- | --- |
| In Markdown, put a code block in a code fence, or indent each line by four spaces. | `` ``` `` fence | code in a normal paragraph |
| Indent with spaces, usually two for each level, as the language style guide tells you. | two spaces | tab characters |
| Mark omitted code with a comment, not dots, and do not make that block click-to-copy. | `# Other settings omitted.` | `...` or `…` |
| Put a sentence before each code sample to introduce it. | The following sample creates a queue: | — |
| End the introduction with a colon only when the sample comes directly after it; else use a period. | …uses the `get` method. For details, see [Methods]. | …see [Methods]: (then the sample) |

## Command-line syntax ([source](https://developers.google.com/style/code-syntax))

| Rule | Do | Not |
| --- | --- | --- |
| Link to the command reference in the text that introduces the command. | Use the [`kubectl apply`](…) command: | — |
| Give a copyable command that needs no change other than placeholders. | `kubectl apply -f FILE_NAME` | `kubectl apply [-f FILE] [--dry-run]` |
| Give each command variant its own block, because brackets, braces, pipes, and dots break copied commands. | A second block that adds `--force` | `deploy APP [--force]` |
| Show each optional argument in its own pair of square brackets. | `sync SRC [--quiet] [--verbose]` | `sync SRC [--quiet --verbose]` |
| Show a one-of-many choice in braces, with a pipe between the choices. | `{--zip\|--tar}` | `(--zip or --tar)` |
| Show a repeatable argument with three dots after it. | `[TAG ...]` | `[TAG …]` |
| End each line of a split command, except the last, with a space and the continuation character. | `--zone=ZONE \` (Linux), `--zone=ZONE ^` (Windows) | `--zone=ZONE` with no `\` |
| Start each input line with `$` in a block that has more than one input line. | `$ cd app` then `$ make` | `~/app$ make` |
| Put input and output in separate code blocks. | — | — |
| Show output only when the reader must copy or check a value in it. | — | — |
| Introduce output with a standard phrase. | The output is similar to the following: | Here's what you'll see: |
| Show omitted output lines with three dots alone on a line. | `...` | `…` |

## Placeholders ([source](https://developers.google.com/style/placeholders))

| Rule | Do | Not |
| --- | --- | --- |
| Write placeholders in uppercase, with underscores between words. | `BUCKET_NAME` | `bucketName`, `bucket-name`, `Bucket_Name` |
| Give the placeholder a descriptive name; use x characters only where they are the norm. | `ORDER_ID`; `4xx` status codes | `xxxx` |
| Leave possessive words out of placeholders. | `API_KEY` | `YOUR_API_KEY`, `MY_API_KEY` |
| In Markdown text, write an inline placeholder as italic code. | `` *`TOPIC_ID`* `` | `` `<topic-id>` `` |
| In a code fence, write the placeholder in uppercase only, because a fence ignores italics. | `gsutil ls gs://BUCKET_NAME` | — |
| Explain each placeholder at its first use. | — | — |
| For one placeholder, write "Replace X with" and a description. | Replace `TOPIC_ID` with the ID of your topic. | — |
| For two or more, write "Replace the following:" and list them in command order. | Replace the following: | Where: |
| Write each list item as placeholder, colon, then a description with a lowercase first letter. | `REGION`: the region of the cluster | `REGION` - The region of the cluster |
| Start an example in a description with an em dash or "such as". | `ZONE`: the zone—for example, `asia-east1-b` | `ZONE`: the zone (e.g. `asia-east1-b`) |
| Introduce a placeholder list after output with a standard phrase. | This output includes the following values: | — |

## File names and file types ([source](https://developers.google.com/style/filenames))

| Rule | Do | Not |
| --- | --- | --- |
| Name files and folders in lowercase, with hyphens between words. | `error-codes.md` | `Error_Codes.md`, `errorcodes.md` |
| Use only ASCII letters and numbers, and a specific name. | `set-up-billing.md` | `page2.md`, `café-setup.md` |
| Use underscores only to match a folder where all files already use them. | `step_4.md` next to `step_3.md` | — |
| Refer to a file with code font and the word "file". | Edit the `app.yaml` file. | Edit app.yaml. |
| Spell a file name exactly as it is, even if it breaks the naming rules. | — | — |
| Name a file type by its formal name, not by its extension. | a JSON file, a Bash file | a .json file, an .sh file |
| Use a real verb for an action on a file, not the file type as a verb. | Extract the zip file. | Unzip the zip file. |

## UI elements ([source](https://developers.google.com/style/ui-elements))

| Rule | Do | Not |
| --- | --- | --- |
| Put the name of a UI element in bold (`**`). | Click **Save**. | Click "Save". Click `Save`. |
| Refer to a button by its label only. | Click **Apply**. | Click the "Apply" button. |
| Copy the capitalization of the label; use sentence case if labels are all caps or mixed. | Click **Delete**. | Click **DELETE**. |
| Name the element and give the action; do not use a label as a verb. | For **Display name**, enter a name. | Specify a **Display name**. |
| Write "the NAME menu", and call each item in it a "command". | In the **Edit** menu, click **Paste**. | Click the **Paste** menu item. |
| Use `>` only for a path through menus, and bold the full path once. | **File > Export > PDF** | **File** > **Export** > **PDF** |
| Wrap each `>` in a span with `aria-label="and then"`, because screen readers say "greater than". | `<span aria-label="and then">></span>` | a bare `>` |
| Use `>` for menus only; describe other element types in a separate step. | Select **Tools > Options**, and then click the **Fonts** tab. | Select **Tools > Options > Fonts > Add**. |
| Call a web or console screen a "page", and a small front window a "dialog". | the **Billing** page; the **Confirm** dialog | the Billing window; the Confirm pop-up |
| Call a separate region of a window a "pane", not a section, area, or column. | In the **Details** pane, click **Edit**. | In the Details area, click **Edit**. |
| Call a list of links to app pages a "navigation menu". | In the navigation menu, click **Logs**. | In the nav bar, click **Logs**. |
| Call a text entry box "the NAME field" in Google Cloud and Workspace docs, else "the NAME box". | In the **Owner** field, enter a name. | In the **Owner** text box, enter a name. |
| Use "select", "clear", and "selected" for checkboxes, because "check" and "uncheck" are ambiguous. | Select the **Send alerts** checkbox. | Check **Send alerts**. |
| Say "expander arrow" and "expandable section", because slang names confuse readers. | Click the expander arrow. | Click the zippy. Click the hamburger. |
| Tell the reader the position for a toggle, and do not use "toggle" as a verb. | Click the **Dark mode** toggle to the on position. | Toggle **Dark mode**. |
| For an icon button, show the icon and then the tooltip name. | Click ⋮ **More actions**. | Click ⋮. Click the icon. |
| Remove a trailing ellipsis from a label. | Click **Import**. | Click **Import...**. |
| Locate elements by name or toolbar, because "above" and "left side" fail for accessibility and translation. | On the **Jobs** toolbar, click **Refresh**. | Click the button at the top right. |
| Use "in" for dialogs, fields, lists, menus, panes, and windows; use "on" for pages, tabs, and toolbars. | On the **Users** page; in the **Share** dialog | In the **Users** page |

## Keyboard keys ([source](https://developers.google.com/style/ui-elements#press-and-type-keyboard-keys))

| Rule | Do | Not |
| --- | --- | --- |
| In Markdown, show keys in code font, because this matches how the HTML key element renders. | Press `Enter`. | Press **Enter**. |
| Spell out modifier keys, join keys with a plus sign, and put Shift after the other modifier. | `Control+Shift+T` | `Ctrl+Z`, `⌘Z`, `Shift+Control+T` |
| Write letter keys in uppercase. | `Control+P` | `Control+p` |
| Write the Windows and Linux key combination first, then add the Mac one in parentheses. | `Control+C` (or `Command+C` on macOS) | `Ctrl+C` (`⌘+C`) |
| Spell out keys that are easy to confuse in a shortcut, such as comma, period, hyphen, and plus. | `Control+Comma` | `Control+,` |
| Use "press" for a key that starts an action; use "enter" or "type" for text input. | Press `Esc`. Type `y`. | Hit `Esc`. |

## Text formatting ([source](https://developers.google.com/style/text-formatting), [source](https://developers.google.com/style/italics-terms))

| Rule | Do | Not |
| --- | --- | --- |
| Keep bold for the names of UI controls and for a label that starts a paragraph, such as a note label. | **Note:** The key expires. | The key **expires** in an hour. |
| Write bold as `**` in Markdown, because `__` is hard to see in the source. | `**Save**` | `__Save__` |
| Write italics as `_` in Markdown, because `*` is easy to confuse with bold. | `_shard_` | `*shard*` |
| Use italics for a new term at its definition and for words as words; do not use bold or quotes. | A _shard_ is one part of a table. | A "shard" is one part of a table. |
| Use italics for emphasis, and use it rarely. | You _must_ restart. | You **must** restart. |
| Italicize titles of full works, and put titles of short works in quotes, unless the title is a link. | _The Pragmatic Programmer_; "Scaling Reads" | — |
| Italicize math variables and version variables, but not operators. | _a_ + _b_ = 5; version 2.3._x_ | _a + b_ = 5 |
| Use underline only for links. | — | — |
| Write "and" in text, headings, and navigation; use `&` only when a UI label has it. | Tips and tricks | Tips & tricks |
| Put end punctuation and closing quotes outside link text. | See [Quotas]. | See [Quotas.] |

## How to introduce an example in a sentence ([source](https://developers.google.com/style/format-examples))

| Rule | Do | Not |
| --- | --- | --- |
| When a sentence ends with an example, put "such as" or an em dash before it. | Add a label—for example, `env:test`. | Add a label; for example, `env:test`. Add a label (for example, `env:test`). |
| Keep a mid-sentence example short, and set it off with parentheses, commas, or dashes. | Enter a port (for example, `8080`), and then click **Save**. | Enter a port (for example, if you use TLS, enter `8443`), and then click **Save**. |
| Put a long example in a separate sentence that starts with "For example". | You can group VMs with tags. For example, tag each VM with `tier:web` or `tier:db`. | — |

## API reference comments ([source](https://developers.google.com/style/api-reference-comments), [source](https://developers.google.com/style/reference-verbs))

| Rule | Do | Not |
| --- | --- | --- |
| Start a method description with a verb that tells what the method does, in present tense. | Creates a bucket. | Create a bucket. |
| Start a getter that returns a Boolean with "Checks whether". | Checks whether the cache is full. | Returns if the cache is full. |
| Start other getters with "Gets the", and other methods with a verb such as "Sets", "Deletes", or "Called by". | Gets the owner of the file. | Get the owner of the file. |
| State the purpose of a class in the first sentence, without the class name or "This class". | Stores the settings for one upload. | This class will store the settings. |
| Write "for example" in a first sentence, because some tools end the summary at the first period. | …types, for example, images. | …types, e.g. images. |
| Start a parameter description with a capital letter and end it with a period. | The ID of the user to remove. | the user id |
| Start a non-Boolean parameter with "The" or "A". | A label for the new disk. | Label for disk |
| For a Boolean that controls an action, give the result of true and of false. | If true, retries failed uploads. If false, stops at the first failure. | Retry flag. |
| For a Boolean state or Boolean return, write "True if …; false otherwise." without code font. | True if the job is done; false otherwise. | `true` if the job is done. |
| Give the behavior for each value, then the default value after "Default:". | Default: 30 seconds. | — |
| Start a non-Boolean return value with "The", and keep it short. | The user that matches the ID. | Returns the user that matches the ID. |
| Start an exception with "If" when the tool adds "Throws"; else start with "Thrown when". | If the key is missing. / Thrown when the key is missing. | — |
| Put string literals in code font, inside double quotation marks. | `"auto"` | auto |
| In a deprecation, name the replacement in the first sentence. | Deprecated. Use `fetchAll` instead. | Deprecated. |
| Use a common English word in lowercase plain font when a class name is also a general term. | Each activity has a lifecycle. | Each `Activity` has a lifecycle. |
