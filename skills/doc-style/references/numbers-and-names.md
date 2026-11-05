# Reference: Numbers, dates, units, and product names

Paraphrased from the Google developer documentation style guide (https://developers.google.com/style), snapshot 2026-10-09, CC BY 4.0. Follow the source link for the full rule.

## Numbers ([source](https://developers.google.com/style/numbers))

| Rule | Do | Not |
| --- | --- | --- |
| Write zero to nine as words and 10 or more as numerals. | three nodes; 12 nodes | 3 nodes; twelve nodes |
| Use numerals for versions, technical quantities, prices, steps, and pages, also below 10. | version 2; 4 GB; 8 queries per second | version two; four GB |
| Use numerals for all numbers in a sentence that also has a number above 9. | 14 jobs ran and 3 failed | 14 jobs ran and three failed |
| Use numerals for negative numbers, decimals, percentages, dimensions, measurements, and ranges. | 6 pixels; -2 | six pixels |
| Spell out a number at the start of a sentence, or move the number later in the sentence. | Twenty tasks finished. | 20 tasks finished. |
| Spell out the first of two numbers that come together. | creates twelve 500-byte files | creates 12 500-byte files |
| Use words for vague, approximate amounts and numerals for exact amounts. | millions of rows; 2,048,000 rows | — |
| Spell out ordinal numbers. | third; twenty-first | 3rd; 21st |
| Use Arabic numerals, because readers scan them faster; keep Roman numerals for sub-steps only. | Part 4 | Part IV |
| Write fractions as decimals when you can; hyphenate fractions in words. | 0.5; three-eighths | 1/2 |
| Put a zero before the decimal point when the value is less than one. | 0.25 seconds | .25 seconds |
| Treat decimal values as plural, also 1.0 or less. | 1.0 meters; 0.5 seconds | 1.0 meter |
| Put a comma in numbers of four or more digits, counting from the decimal point. | 4,096; 2,500,000 | 4096; 2 500 000 |
| Use a period as the decimal point and no separators after it. | $0.004218 | $0.004,218 |
| Put no space between a number and the percent sign. | 25% | 25 %; 25 percent |
| Spell out the number and "percent" when a percentage starts a sentence. | Thirty percent of jobs failed. | 30% of jobs failed. |
| Use a hyphen with no spaces for a range, not an en dash. | 2019-2023 | 2019–2023; 2019 - 2023 |
| Use suspended hyphens when number compounds share one noun. | 10-, 20-, or 30-second timeouts | 10-second, 20-second, or 30-second timeouts |
| Write dimensions with a lowercase x and no spaces. | 640x480 | 640 x 480; 640X480 |
| Put the dollar sign first, and use commas, not spaces, for thousands. | $25,000 | $25 000; 25,000$ |
| Put a nonbreaking space between a number and its noun when they must stay on one line. | `5&nbsp;files` | — |

## Units of measure ([source](https://developers.google.com/style/units-of-measure))

| Rule | Do | Not |
| --- | --- | --- |
| Put a nonbreaking space between a number and its unit. | `32&nbsp;GB` (32 GB) | 32GB |
| Put no space before currency, percent, or angle symbols. | €40; 15%; 90° | € 40; 90 ° |
| For temperature, put a space before the degree sign and none between the sign and the scale. | 20 °C | 20°C; 20° C |
| For kelvin, omit the degree sign and keep the space. | 273 K | 273°K |
| Do not hyphenate a number and unit before a noun unless the hyphen prevents confusion. | a 500 GB disk | a 500-GB disk |
| In a range, repeat the unit and use "to", because a hyphen can look like a minus sign. | -10 °C to 40 °C | -10-40 °C |
| Hyphenate units that multiply together. | 12 node-hours | 12 node hours |
| When you use k for thousands, add no space and name the thing you count. | 30k reads per day | 30 k; 30k per day |
| State the currency when the symbol can mean more than one currency. | CA$15; US$15 | $15 (when unclear) |
| Write "per" for rates; use a slash only in tight spaces such as narrow tables. | writes per second | writes/second |
| Shorten "per" to "p" only in well-known rate units. | Mbps | Mb/s |
| Use the same byte system as the product, because decimal and binary units differ. | 8 GiB (when the product uses GiB) | 8 GB (when it means GiB) |

## Dates and times ([source](https://developers.google.com/style/dates-times))

| Rule | Do | Not |
| --- | --- | --- |
| Write dates as month name, day, and four-digit year. | March 14, 2024 | 3/14/24; 14 March 2024 |
| Do not use numeric dates with slashes or periods, because regions read the day and month order differently. | June 8, 2025 | 06/08/2025; 08.06.2025 |
| If you must use numbers only, use the ISO 8601 form YYYY-MM-DD. | 2025-06-08 | 06-08-2025 |
| In a made-up example date, pick a day above 12 so that readers cannot mix it up with the month. | 2024-03-21 | 2024-03-05 |
| Put the weekday first, before the month. | Friday, March 15, 2024 | March 15, 2024, Friday |
| Put no comma between a month and a year alone. | in March 2024 | in March, 2024 |
| Put a comma after the year when a full date is in mid-sentence. | The May 2, 2023, update fixed it. | The May 2, 2023 update fixed it. |
| Abbreviate to three letters only in tight space, with no period, and abbreviate the whole date. | Thu, Feb 6, 2025 | Thu, February 6, 2025; Feb. 6 |
| Use the 12-hour clock, unless the product, UI, or code uses 24-hour time. | 9:30 AM | 09:30 (in general text) |
| Write AM and PM in capitals with a space before them. | 4:15 PM | 4:15pm; 4:15 p.m. |
| Drop the minutes for a time on the hour. | 2 PM | 2:00 PM |
| Use a hyphen with no spaces in a time range. | 15-20 minutes | 15 - 20 minutes |
| Put the date first and the time second. | 2025-06-08 at 11 AM | 11 AM on 2025-06-08 |
| Avoid time zones; if you need one, spell out the region and add the UTC offset. | US and Canadian Eastern Standard Time (UTC-5) | EST |
| Tell readers when a time is in their own time zone. | 8 AM your local time | — |
| Use months or quarters, not seasons, because seasons differ between hemispheres. | in July; in Q3 | in summer |

## Phone numbers ([source](https://developers.google.com/style/phone-numbers))

| Rule | Do | Not |
| --- | --- | --- |
| Use only 800-555-0100 to 800-555-0199 for example numbers, because that range is reserved for fiction. | 800-555-0142 | a real phone number |
| Separate the parts of a North American number with nonbreaking hyphens. | `650&#8209;555&#8209;0177` | (650) 555 0177 |
| For other countries, add a plus sign and the country code with no space. | +44‑20‑5550‑1234 | 0044 20 5550 1234 |
| Write the word "extension" after the number to show an extension. | 800‑555‑0142, extension 31 | 800‑555‑0142 x31 |

## Mathematical notation ([source](https://developers.google.com/style/mathematical-notation))

| Rule | Do | Not |
| --- | --- | --- |
| Use HTML entities for math symbols; keyboard characters are fine only for +, =, and /. | `&minus;`, `&times;`, `&le;` | `-`, `x`, `<=` |
| Use the multiplication sign, not an asterisk, in text, unless you match the UI. | 4 × 6 | 4 * 6 |
| Write exponents with superscript and subscripts with `<sub>`, not with a caret. | `2<sup>10</sup>` | 2^10 |
| Italicize variables, but not operators. | *m* + *n* | *m + n* |
| Put nonbreaking spaces around operators so that the expression stays on one line. | `_p_&nbsp;+&nbsp;_q_` | — |
| Use words instead of notation when notation makes the sentence hard to read. | Multiply the rows by the columns. | Multiply r × c. |

## Product names and trademarks ([source](https://developers.google.com/style/product-names), [source](https://developers.google.com/style/trademarks))

| Rule | Do | Not |
| --- | --- | --- |
| Use the official capitalization of each product, brand, and community term. | Pub/Sub; a Kubernetes Pod | PubSub; a kubernetes pod |
| Keep a name that starts in lowercase in lowercase; rewrite the sentence so it does not come first. | Install the app on iOS. | IOS supports the app. |
| Write feature names in lowercase unless the name is officially capitalized or you match a UI label. | the autoscaling feature | the Autoscaling feature |
| Use the full trademarked product name; shorten it only to match a UI label. | Google Sheets | Sheets (outside a UI label) |
| Do not put "the" before a product name unless the name modifies a noun. | Use Cloud Storage with BigQuery. | Use the Cloud Storage with the BigQuery. |
| Put "the" before tool names and API names. | the gcloud CLI; the Vision API | gcloud CLI supports this. |
| Use "service" for products only when the meaning stays clear. | the Compute Engine service | — |
| Do not use a product, feature, or trademark name as a verb. | Search for it with Google Search. | Google it. |
| Use a trademark as a modifier of a noun, not as a noun alone. | a Pixel phone | a Pixel |
| Do not make a trademark plural or possessive, or change its form. | the features of Chrome browsers | Chrome's features; two Chromes |
| Follow the mark owner's rules for trademark symbols and attribution. | — | — |
