# Reference: Punctuation, capitalization, and abbreviations

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, CC BY 4.0. Follow the source link for the full rule.

## Commas ([source](https://developers.google.com/style/commas))

| Rule | Do | Not |
| --- | --- | --- |
| Use the serial comma before the last item of a list of three or more. | disks, images, and snapshots | disks, images and snapshots |
| Put a comma before *and*, *but*, or *so* when it joins two full clauses. | The job stops, and the log shows the cause. | The job stops and the log shows the cause. |
| Join two very short clauses with no comma. | Select the file and click **Open**. | Select the file, and click **Open**. |
| Omit the comma when the second part has no subject, unless the sentence becomes unclear. | The cache is local and clears on restart. | The cache is local, and clears on restart. |
| Put a comma before *which* when it starts a nonessential clause. | Enter the zone name, which can have 63 characters. | Enter the zone name which can have 63 characters. |
| Put a semicolon or a period before *however*, *otherwise*, or *therefore*, and a comma after it. | Save the file; otherwise, you lose the edits. | Save the file otherwise you lose the edits. |
| Put a comma before *because* only when the clause after it is nonessential. | The build fails because the path is wrong. | The build fails, because the path is wrong. |

## Colons and semicolons ([source](https://developers.google.com/style/colons), [source](https://developers.google.com/style/semicolons))

| Rule | Do | Not |
| --- | --- | --- |
| Make the text before a list colon a complete sentence. | The tool supports the following formats: | The supported formats are: |
| Start the text after a colon in lowercase, except for a proper noun, a heading, a quotation, or text after a label such as **Note**. | Check three things: the name, the zone, and the size. | Check three things: The name, the zone, and the size. |
| Prefer a period or a comma to a semicolon in most sentences. | The disk is full. Delete old logs. | — |
| Use semicolons to split a list when its items contain commas. | Check the names; the dates, times, and zones; and the labels. | Check the names, the dates, times, and zones, and the labels. |

## Dashes and hyphens ([source](https://developers.google.com/style/dashes), [source](https://developers.google.com/style/hyphens))

| Rule | Do | Not |
| --- | --- | --- |
| Use an em dash with no space on each side for a break in a sentence, and never type it as `--`. | The update—if it succeeds—restarts the VM. | The update — if it succeeds — restarts the VM. |
| Use a hyphen or the word *to* where other writers use an en dash. | pages 4-9 | pages 4–9 |
| Use a colon or a period between a term and its description, not a dash. | Region: a geographic area. | Region - a geographic area. |
| Use a hyphen or *from ... to* for a range of numbers, and keep the two forms apart. | 3-6 nodes; from 3 to 6 nodes | from 3-6 nodes |
| Write most prefixes closed, with no hyphen. | metadata, preload, subnet | meta-data, pre-load |
| Hyphenate after *self* or *cross*, before a capital or a number, and where the closed form misleads. | self-signed, non-Linux, pre-2020, re-sign | selfsigned, nonLinux |
| Write compound nouns closed when that form is common in the field. | filename, timestamp | file-name, time stamp |
| Hyphenate a compound modifier before a noun when the hyphen makes it clearer. | a long-running job | — |
| Leave a compound open after a verb, unless the word list always hyphenates it. | The page is well organized. | The page is well-organized. |
| Leave an *-ly* adverb open before a noun. | a newly created disk | a newly-created disk |
| Move words after the noun when a modifier has more than two words. | tests that run only on ARM | ARM-only-run tests |
| Put a hyphen between a number and a unit written as a word when they come before a noun. | a 32-bit key, a 10-second delay | — |
| Put a nonbreaking space between a number and a unit abbreviation, not a hyphen. | `500&nbsp;MB` disk | 500-MB disk |
| Use a suspended hyphen to share one base, with a space after the hyphen only. | two- or four-core machines | two - or four-core machines |

## Periods, parentheses, and ellipses ([source](https://developers.google.com/style/periods), [source](https://developers.google.com/style/parentheses), [source](https://developers.google.com/style/ellipses))

| Rule | Do | Not |
| --- | --- | --- |
| Move a URL away from the end of a sentence, or put it on its own line, because readers can think the period is part of it. | Open https://example.com/terms and read the terms. | Read the terms at https://example.com/terms. |
| End titles and headings with no period. | Create a bucket | Create a bucket. |
| Use periods, not exclamation points, in concept, reference, and task docs, because exclamation points can alarm readers and translate badly. | The VM is ready. | The VM is ready! |
| Keep important information out of parentheses, because some readers skip text in parentheses. | Type a label—for example, `prod-eu`. | Type a label (for example, `prod-eu`). |
| Put the period inside the parentheses only when they hold a full sentence. | The tool is free. (Support costs extra.) | The tool is free. (Support costs extra). |
| Write the full content, not an ellipsis for a pause or for cut text. | The answer is no. | The answer is ... no. |
| Leave out an ellipsis that a UI label shows, unless that causes confusion. | Click **Export**. | Click **Export...**. |
| In a quotation, use an ellipsis only for text cut from the middle, and type three periods with a space on each side. | "Back up ... before you upgrade." | "...back up your data." |

## Quotation marks ([source](https://developers.google.com/style/quotation-marks))

| Rule | Do | Not |
| --- | --- | --- |
| Put commas and periods inside the closing quotation mark. | See the page "Set up billing." | See the page "Set up billing". |
| Put a literal string in code font with no quotation marks; if you quote it, put other punctuation outside the marks. | Type `yes`, and press Enter. | Type "yes," and press Enter. |
| Use straight quotation marks and apostrophes, because code needs them and curly marks cause errors. | "Don't stop" | “Don’t stop” |
| Use single quotation marks only in code that needs them or for a quotation inside a quotation. | He said, "The log shows 'disk full' twice." | He said, 'The log shows "disk full" twice.' |
| Use quotation marks for short work titles and for section names that you cannot link to. | the section "Before you begin" | — |
| Put quotation marks on a metaphor only when the field does not already use the term. | The cache is a "waiting room" for requests. | — |

## Slashes ([source](https://developers.google.com/style/slashes))

| Rule | Do | Not |
| --- | --- | --- |
| Use *or* or *and* between alternatives, not a slash. | Run the test two or three times. | Run the test 2/3 times. |
| Write *and*, *or*, or *A, B, or both* in place of *and/or*, except where space is tight, such as a table. | You can read and write the file. | You can read and/or write the file. |
| Write dates with no slashes, because the order of day and month changes by country. | October 9, 2026 | 10/9/2026 |
| Write a fraction as a decimal or a percentage, because a slash can also mean "or". | 0.5, 50% | 1/2 |
| Spell out short forms that use a slash. | with, care of | w/, c/o |
| Break a long URL right after a slash, and never add a hyphen to break it. | — | — |

## Possessives and plurals ([source](https://developers.google.com/style/possessives), [source](https://developers.google.com/style/pluralization))

| Rule | Do | Not |
| --- | --- | --- |
| Add *'s* to a singular noun, also when it ends in *s*. | the class's fields | the class' fields |
| Add only an apostrophe to a plural noun that ends in *s*. | the users' roles | the users's roles |
| Use a product or feature name as a modifier, or use *of*, in place of a possessive. | Cloud Run performance; the limits of Cloud Run | Cloud Run's performance |
| Put the possessive on the noun after a code item, or rewrite the sentence. | the `parse` method's output; the output of `parse` | `parse`'s output |
| Add *s* with no apostrophe to make an abbreviation plural, because *'s* looks like a possessive. | URLs, VMs | URL's, VM's |
| Add *es* to an abbreviation that ends in *s*, *sh*, *ch*, or *x*. | OSes | OS's |
| Make the long form and its abbreviation agree in number. | service accounts (SAs) | service accounts (SA) |
| Keep a unit abbreviation singular after a number. | 16 GB | 16 GBs |
| Use the plural of a spelled-out unit for all numbers except 1, including 0 and decimals. | 0 seconds, 1.5 seconds, 1 second | 0 second |
| Pick singular, plural, or *one or more* in place of an optional plural in parentheses. | one or more files | file(s) |
| Keep a class name singular and add a plural noun after it, because a changed class name can confuse translators. | `Task` objects | `Tasks` |
| Use a plural after *one or more* and a singular after *more than one*. | More than one job is in the queue. | More than one jobs are in the queue. |

## Abbreviations ([source](https://developers.google.com/style/abbreviations))

| Rule | Do | Not |
| --- | --- | --- |
| Spell out an unfamiliar abbreviation at first mention, then put the abbreviation in parentheses and use it alone after that. | Identity and Access Management (IAM) | IAM (Identity and Access Management) |
| Leave out the abbreviation when the term occurs only once, unless the short form is equally common. | — | — |
| Use well-known abbreviations such as API, URL, HTML, PDF, and GB with no long form. | Download the PDF. | Download the portable document format (PDF) file. |
| Capitalize the long form only when it is a proper noun, not because the abbreviation is in capitals. | access control list (ACL) | Access Control List (ACL) |
| Italicize the long form and the abbreviation when you introduce them together. | *Domain Name System (DNS)* | — |
| Use the abbreviation in a heading if necessary, and spell it out in the first paragraph after the heading. | — | — |
| Write *for example* and *that is* in place of *e.g.* and *i.e.* | for example, Go | e.g., Go |
| Write the full word in place of slang, rare short forms, or symbols that stand for words. | approximately; 5 times faster | approx.; 5x faster; tl;dr |
| Write acronyms and initialisms with no periods. | CPU | C.P.U. |
| Put a period after a shortened word, but not after date or time short forms, country or state codes, or words you say aloud (app, sync). | etc.; Mon; CA; app | app.; C.A. |
| Use an abbreviation as a noun or a modifier, not as a verb. | Use SSH to connect to the VM. | SSH into the VM. |
| Pick *a* or *an* from the most common way to say the abbreviation. | a SQL query, an HTTP request | an SQL query |

## Capitalization ([source](https://developers.google.com/style/capitalization))

| Rule | Do | Not |
| --- | --- | --- |
| Use sentence case in titles and headings: capitalize the first word, proper nouns, and the first word after a colon. | Set up logging: First steps | Set Up Logging: First Steps |
| Use sentence case when you refer to a heading in docs that follow this guide; keep the original case for outside works. | see "Manage user roles" | see "Manage User Roles" |
| Use sentence case in captions, image labels, list items, and all table text. | Table 1. Supported regions | Table 1. Supported Regions |
| Write glossary and index terms in lowercase, unless they are proper nouns. | load balancer | Load Balancer |
| Use words, not only a capital letter, to show a difference in meaning, because many readers miss it. | the Kubernetes `Service` object | the Service (not a service) |
| Use all capitals only in official names, abbreviations, and code that uses them. | `MAX_RETRIES`, NASA | Do NOT delete the file. |
| Use camel case only in official names and in code. | YouTube, `getUser` | the ClickStream data |
| Capitalize only the first part of a hyphenated word at the start of a sentence or heading, unless a later part is a proper noun. | Built-in roles | Built-In roles |
| Describe a casing format and give an example, not a name such as *camel case*, because these names do not translate well. | Capitalize each word and use no spaces, for example `OrderTotal`. | Use Pascal case. |
