# Reference: Voice, tone, and wording

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, CC BY 4.0. Follow the source link for the full rule.

## Tone ([source](https://developers.google.com/style/tone))

| Rule | Do | Not |
| --- | --- | --- |
| Write like a helpful, informed peer: friendly and plain, not stiff and not jokey. | This method returns the cart total. | Whoa, this method is seriously cool! |
| Leave out "please" in instructions and links, because it adds words and no meaning. | To save the draft, click **Save**. | Please click **Save** to save the draft. |
| Leave out "simply", "easy", and "quickly" in steps, because the task can be hard for the reader. | Run the setup script. | Simply run the setup script. |
| Leave out filler openers such as "please note" and "at this time". | The export runs once a day. | Please note that at this time the export runs once a day. |
| Use a direct instruction instead of "let's". | Open the config file. | Let's open the config file. |
| Use a period instead of an exclamation mark in most text. | Your build is complete. | Your build is complete! |
| Leave out pop-culture references, slang, and web abbreviations such as "tl;dr", because many readers do not know them. | In short, | tl;dr |
| Vary how sentences start, because many "You can" openers in a row read badly. | — | — |

## Person and voice ([source](https://developers.google.com/style/person), [source](https://developers.google.com/style/voice))

| Rule | Do | Not |
| --- | --- | --- |
| Address the reader as "you". | This page shows you how to add a webhook. | This page shows how we can add a webhook. |
| Use "user" only for the person who uses the reader's app, not for the reader. | Your users see the banner after sign-in. | The user (you) configures the banner. |
| Use the imperative to tell the reader to do a task. | Click **Deploy**. | You will want to click **Deploy**. |
| Use the third person to describe actions of the program or of its end users. | The method returns `null` when the key is missing. | — |
| Use "we" only for the organization, after you name it, so the reader knows who "we" is. | Example Bank stores the logs. We delete them after 30 days. | We delete the logs after 30 days. |
| Use active voice, so the reader knows who does the action. | Send the request. The API returns a token. | The request is sent and a token is returned. |
| Use passive voice only when the actor is unknown or not important. | The cache was cleared at midnight. | — |

## Tense ([source](https://developers.google.com/style/tense))

| Rule | Do | Not |
| --- | --- | --- |
| Use present tense for general behavior. | The server sends a reply. | The server will send a reply. |
| Use "will" only for an action that truly happens later, such as an async or scheduled event. | The job will run at the next hourly sync. | — |
| Leave out the hypothetical "would". | If you close the port, the agent stops. | You can close the port. The agent would then stop. |

## Contractions ([source](https://developers.google.com/style/contractions))

| Rule | Do | Not |
| --- | --- | --- |
| Use common two-word contractions. | you're, it's, there's | — |
| Use negative contractions, because a reader who scans can miss a separate "not". | The field isn't required. | The field is not required. |
| Use only standard two-word contractions, because made-up ones confuse readers. | — | logs're, mightn't've |

## Anthropomorphism ([source](https://developers.google.com/style/anthropomorphism))

| Rule | Do | Not |
| --- | --- | --- |
| Describe software and hardware without human traits, because figurative text is hard to translate. | The parser detects a syntax error. | The parser sees a syntax error. |

## Claims ([source](https://developers.google.com/style/excessive-claims))

| Rule | Do | Not |
| --- | --- | --- |
| Describe products with facts, not superlatives such as "best", "fastest", "never", or "always". | The index is stored in memory. | This is the fastest index on the market. |
| Use "ensure" and "guarantee" only when the result is certain. | — | This setting guarantees zero data loss. |
| Give a source for each specific speed, size, or cost claim. | Reads take 4 ms on average (see the benchmark page). | Reads are lightning fast. |
| Say a feature helps with security, because a breach makes an absolute claim false. | Two-step sign-in helps protect your account. | Two-step sign-in makes your account secure. |
| Compare with other products only with facts that stay true after their next release. | Our tool runs the queries in parallel, so it can be faster for large joins. | Our tool is faster than Acme DB. |

## Timeless documentation ([source](https://developers.google.com/style/timeless-documentation), [source](https://developers.google.com/style/future))

| Rule | Do | Not |
| --- | --- | --- |
| Describe the product as it is, without words such as "now", "new", "currently", "soon", or "latest". | The CLI supports these flags: | The CLI now supports these new flags: |
| Give a version or date when you must say a feature is new. | Version 3.2 adds the `--dry-run` flag. | The new `--dry-run` flag |
| Do not announce future features or products unless your legal team approves. | — | Windows support comes in a later release. |
| Use time words only in dated content, such as release notes, or for a state change in a step. | The service restarts soon after you save. | — |

## Jargon ([source](https://developers.google.com/style/jargon))

| Rule | Do | Not |
| --- | --- | --- |
| Write around jargon when readers do not search for the term. | After launch, discuss what went well and what did not. | Hold a retro after launch. |
| Replace jargon and vague terms such as "solution" with a specific plain word. | load the files | ingest the files |
| Explain a needed jargon term in plain words when it first appears, or link to a reliable definition. | a warm standby (a backup system that runs and stays in sync) | a warm standby |
| Use an unwanted term only when code requires it, and format it as code. | Add the host to the denylist (blacklist) with `blacklist add HOST`. | Add the host to the blacklist with `blacklist add HOST`. |

## Sentence order ([source](https://developers.google.com/style/sentence-structure))

| Rule | Do | Not |
| --- | --- | --- |
| Put the goal or condition before the instruction, so readers can skip steps that do not apply. | To rename the file, click **Rename**. | Click **Rename** if you want to rename the file. |
| Put "For more information" before the link. | For more information, see [Quotas]. | See [Quotas] for more information. |

## Must, can, might ([source](https://developers.google.com/style/prescriptive-documentation))

| Rule | Do | Not |
| --- | --- | --- |
| Use "must" or a plain imperative for a required action. | You must set a region first. | You should set a region first. |
| Use "we recommend" for a recommended action. | We recommend a separate project for tests. | You should use a separate project for tests. |
| Use "can" for an optional action. | You can also export the report as CSV. | — |
| Use "might" or "can" for a possible outcome. | The import might take an hour. | The import should take an hour. |
| State an expected outcome as a fact. | The query returns 20 rows. | The query should return 20 rows. |
| Replace "should" when you describe a state, and say who sets the value. | The agent sets `ready` to `true`. | The `ready` value should be `true`. |
| Use "should" only for a widely accepted practice. | You should use a strong password. | — |

## Pronouns ([source](https://developers.google.com/style/pronouns))

| Rule | Do | Not |
| --- | --- | --- |
| Repeat the noun when "it" could refer to two things. | If you edit the row, the row stays locked. | If you edit the row, it stays locked. |
| Put a noun after "this" or "these". | Set this flag to `false`. | Set this to `false`. |
| Use singular "they" for a person of unknown gender. | Each admin sees their own key. | his or her, he/she, (s)he |
| Keep optional "that" and "which" for clarity. | Select the file that you want to share. | Select the file you want to share. |
| Use "that" with no comma for a restrictive clause. | The key that expired is blocked. | The key, that expired, is blocked. |
| Use "which" after a comma for a nonrestrictive clause. | The key, which expires daily, is blocked. | The key which expires daily is blocked. |

## Articles ([source](https://developers.google.com/style/articles))

| Rule | Do | Not |
| --- | --- | --- |
| Keep "a", "an", and "the", also in headings, because translation needs them. | Create a service account | Create service account |

## Prepositions ([source](https://developers.google.com/style/prepositions))

| Rule | Do | Not |
| --- | --- | --- |
| End a sentence with a preposition when that reads more naturally. | Pick the region you deploy to. | Pick the region to which you deploy. |
