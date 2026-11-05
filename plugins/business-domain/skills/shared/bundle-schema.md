# Bundle schema

This document gives the format of the domain bundle. Each business-domain skill obeys it. The LinkML
schema `schema/domain.yaml` is the one source of the types, the fields, the closed lists, and
the permitted edge targets. If this document and the schema do not agree, the schema is
correct.

## Location

`.claude/ddd.json` names the bundle directory. The default is `docs/domain/`:

```json
{ "dir": "docs/domain", "okf_version": "0.2", "plugin_version": "0.1.0" }
```

Each skill reads `.claude/ddd.json` first. When the file does not exist, the skill tells the
user to run `/business-domain:setup` and stops.

## Layout

| Path | Type |
|---|---|
| `index.md` | the bundle index. Its frontmatter holds `okf_version` only |
| `log.md` | the log. Setup, Apply, and Merge entries, newest date first |
| `links.tsv` | the full edge list |
| `contexts/` | Context |
| `relationships/` | Relationship |
| `terms/` | Term |
| `aggregates/` | Aggregate |
| `events/` | Event |
| `questions/` | Question |
| `sources/` | Source |

Each type directory has a generated `index.md`. A directory with no pages does not exist.

## IDs

- An ID is `<PREFIX>-<NN>`: `CONTEXT-01`, `RELATIONSHIP-03`, `TERM-14`, `AGGREGATE-02`,
  `EVENT-07`, `QUESTION-05`, `SOURCE-04`.
- The file name is the ID plus `.md`. The name, the `type`, and the directory must agree.
- An ID is permanent. A rename changes the `title` only. A removed page gets
  `status: deprecated`, and the file stays.
- `aliases` holds each old title and each merged ID. `ddd.py resolve` accepts an ID or an alias.
- The script assigns each ID. Never choose an ID yourself. Run `ddd.py new`.

## Page format

1. The frontmatter holds the OKF fields first: `type`, `title`, `description`, `status`,
   `tags`. Then the type fields. Then the edges. Then the provenance fields `sources`,
   `confidence`, `generated`, and `verified`. The frontmatter has no comments.
2. `status` is the page lifecycle only: `draft`, `stable`, or `deprecated`. `draft` means that
   a person accepted the page, but it is not settled. `stable` means that a person confirmed
   it. A Question uses `state` for `open` or `resolved`.
3. An actor is `human:<login>` for a person, `ddd/<version>` for the plugin, or
   `process:regen` for the script. Each timestamp has an explicit UTC offset, as in
   `2026-10-20T09:30:00Z`. `generated` is `{ by, at }`. `verified` is a list of `{ by, at }`.
4. The body starts with `# <ID>: <title>`.
5. The script writes the `LINKS` block at the end of the body. It shows each stored edge and
   each derived reverse edge. Never edit the block, because the next `regen` writes it again.
6. A link in the frontmatter is bundle-relative and starts with `/`, as in
   `/contexts/CONTEXT-01.md`. A link in the body is relative to its own file, as in
   `../contexts/CONTEXT-01.md`.
7. The title of a Term, Aggregate, or Event is its name in the ubiquitous language, in the form
   that the code uses: `Order`, `ShippingAddress`, `PlaceOrder`, `OrderPlaced`. A Term of kind
   `role` or `concept` can use plain words.
8. The description is the router: an agent sees only the index line before it opens a page.
   Write it in the words of the domain, and make it specific.
9. A page has fewer than 100 lines and fewer than 600 words. The `LINKS` block does not count.

## Page types and fields

| Type | Type fields | Body |
|---|---|---|
| Context | `subdomain` (`core`, `supporting`, `generic`), `external`, `big_ball_of_mud`, `owner` | Purpose. For a core context, the domain vision statement |
| Relationship | `patterns` (one or more of `shared-kernel`, `customer-supplier`, `conformist`, `anti-corruption-layer`, `open-host-service`, `published-language`, `separate-ways`) | Rationale, translation mechanism, integration test commitments |
| Term | `kind` (`entity`, `value-object`, `domain-service`, `role`, `command`, `policy`, `concept`), `avoid` | Definition, examples, notes |
| Aggregate | `avoid` | Root entity, a `## Invariants` section with one list item for each invariant, lifecycle, operations |
| Event | `initial`, `avoid` | Meaning, payload, the condition that makes it happen |
| Question | `state` (`open`, `resolved`), `kind` (`conflict`, `hotspot`, `gap`) | The question, the evidence on each side, and the answer when resolved |
| Source | `resource`, `source_kind`, `content_hash`, `cursor`, `analyzed_at` | What the source is, and what the model took from it |

Each type also has `aliases`. The language of a context is the set of its Term, Aggregate,
and Event pages.

## Edges

| Field | From → To | Number |
|---|---|---|
| `context` | Term, Aggregate, Event → Context | 0 or 1 |
| `between` | Relationship → Context | exactly 2, different |
| `upstream` | Relationship → Context, one of the two in `between` | 0 or 1 |
| `contains` | Aggregate → Term of kind `entity` or `value-object` | 0 or more. No cycles |
| `references` | Aggregate → Aggregate | 0 or more |
| `emits` | Aggregate → Event | 0 or more |
| `triggered_by` | Event → Term of kind `command` or `policy`, Event | 0 or more |
| `translates_to` | Term, Aggregate, Event → Term, Aggregate, Event in a different context | 0 or more |
| `about` | Question → any page | 1 or more |
| `sources` | any page except Source → Source, as `{ id: SOURCE-01, resource: <the resource> }` | 0 or more |

**One rule for the direction.** Store each edge one time, in the frontmatter of one page.
`ddd.py regen` writes the reverse direction into the `LINKS` block of the target page. A
Context page stores no list of its terms: its `LINKS` block lists them.

## The read order

1. The router block in `CLAUDE.md` names the bundle and this order.
2. Read the bundle-root `index.md`. It lists each Context with one line, and links to each
   type index.
3. Open one Context page. Its `LINKS` block lists the terms, aggregates, events, and
   relationships of the context.
4. Open one page. The frontmatter gives each typed edge, and the `LINKS` block gives each
   reverse edge.
5. For a question about the full graph, grep `links.tsv`. Do not read each page, because
   `links.tsv` holds each edge in one file.

## Generated parts

`ddd.py regen` writes these parts from the frontmatter only. Never edit them, because the next
`regen` writes them again and E10 reports the difference.

- Each type `index.md`: one line for each page, `* [<ID>: <title>](<file>) - <description>`.
  The Term, Aggregate, and Event indexes group the lines under one heading for each context.
  Deprecated pages go under `## Deprecated`.
- The bundle-root `index.md`: the list of contexts and one link for each type directory,
  between `<!-- DDD:INDEX START (generated, do not edit) -->` and `<!-- DDD:INDEX END -->`.
  The text around the markers belongs to the user.
- The `LINKS` block of each page.
- `links.tsv`, with the columns `source`, `relation`, `target`, `source_type`, `target_type`,
  `source_context`, `target_context`, `target_status`. A missing value is `-`.

`regen` writes a file only when its bytes change. Two runs in a row change no byte.

## The checker

`ddd.py check` gives one line for each finding: `<LEVEL>: <path>:<line> [<code>] <message>`,
then `<n> errors, <m> warnings`. The exit code is 0 with no error, 1 with an error, and 2 when
the input is wrong. `--strict` makes each warning an error.

| Code | Rule |
|---|---|
| E1 | The frontmatter does not parse, or `type` is missing. |
| E2 | The frontmatter does not agree with `schema/domain.schema.json`, or `between` names one context two times. |
| E3 | The file name, the `type`, and the directory do not agree, two pages have one ID, or two live Source pages have one `resource`. |
| E4 | An edge points to a page that does not exist. |
| E5 | An edge points to a page of a type, or a Term of a `kind`, that the schema does not permit. |
| E6 | A `contains` cycle. |
| E7 | In one context, two live pages have the same title or alias, or a title is in the `avoid` list of another page. |
| E8 | A Relationship to a Context with `big_ball_of_mud: true` has no `anti-corruption-layer` or `conformist` pattern. |
| E9 | A `translates_to` edge joins two pages of the same context. |
| E10 | A generated part does not agree with what `regen` writes now. |
| E11 | The root `index.md` has keys other than `okf_version`, a type `index.md` has frontmatter, or the `log.md` dates are not newest first. |
| E12 | A directional pattern has no `upstream`, `shared-kernel` or `separate-ways` alone has an `upstream`, or `upstream` is not in `between`. |
| W1 | A Term, Aggregate, or Event has no `context`. |
| W2 | An Aggregate is in a Context that has no `subdomain`. Do the strategic work first. |
| W3 | A live Aggregate has no list item under `## Invariants`. |
| W4 | An Event title is not in the past tense. |
| W5 | More than one Context has `subdomain: core`. |
| W6 | A live edge points to a deprecated page. |
| W8 | A page has no inbound edge and no outbound edge. Source and Question pages are exempt. |
| W9 | An open Question is older than 30 days, by `generated.at`. |

## The write rule

After the last page write, each skill that writes runs:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py check

If `uv` is not installed, the skill runs `python3` with the same path. If a command gives an
exit code that is not 0, the skill stops, shows the output, and does not report success. The
skill shows each warning.

## Edits outside a skill

A person can edit a page in an editor, and an agent can edit a page with the Write or Edit
tool. Two mechanisms keep the generated parts correct.

- **The hook.** After each Write or Edit of a file inside the bundle, the plugin hook runs
  `ddd.py regen` and `ddd.py check`. An error from `check` comes back to the agent with exit
  code 2: correct the page. Warnings come back as context. The hook does not undo the edit.
  The hook does not see a `sed` command, a script, or an editor.
- **The check at skill start.** Each business-domain skill that reads the bundle runs
  `ddd.py regen --check` first. Exit 1 means drift: each `STALE:` line names one generated
  part. The skill then runs `ddd.py regen` and `ddd.py check`, and tells the user which parts
  it rewrote.

The hook and the check change only the generated parts. They never change the frontmatter or
the text of a page.
